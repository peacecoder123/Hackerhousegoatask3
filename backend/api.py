"""
backend/api.py
--------------
Flask REST API that exposes the FaceChain Verify pipeline to the frontend.

Endpoints:
  POST /api/run   — Upload a face image, run full pipeline, return live results
  GET  /api/health — Health check

Usage:
    cd backend/
    python api.py
    # Runs on http://localhost:5050
"""
import os
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

# Load backend/.env
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

# Set UTF-8 for Windows console logging
os.environ.setdefault("PYTHONUTF8", "1")

from PIL import Image as PILImage
from face_detection import FaceDetector
from web_search import search_by_image
from blockchain import compute_fingerprint, upload_to_chain, verify_on_chain_full, FACECHAIN_VERIFY_ABI

app = Flask(__name__)
CORS(app)   # Allow Next.js dev server (localhost:3000) to call this API

# Global lazy/singleton detector instance for fast inference
_detector_instance = None

def get_detector() -> FaceDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = FaceDetector()
    return _detector_instance


@app.get("/")
def root():
    return jsonify({
        "service": "FaceChain Verify API",
        "status": "online",
        "frontend_url": "http://localhost:3000",
        "endpoints": {
            "health": "/api/health",
            "scan_face": "/api/scan-face",
            "run_pipeline": "/api/run",
            "verify": "/api/verify",
            "tamper": "/api/tamper"
        },
        "message": "API is active. Open the web interface at http://localhost:3000"
    })


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "FaceChain Verify API",
        "contract_address": os.getenv("CONTRACT_ADDRESS", "")
    })


@app.post("/api/scan-face")
def scan_face():
    """
    Step 1: Real-time face detection on an uploaded image.
    Returns real bounding box, confidence, and facial landmarks/area.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    suffix = Path(file.filename).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        file.save(tmp.name)
        image_path = tmp.name

    try:
        # Get image dimensions
        try:
            with PILImage.open(image_path) as img:
                width, height = img.size
        except Exception:
            return jsonify({
                "success": False,
                "error": "Uploaded file is not a valid or readable image. Please provide a JPG, PNG, or WEBP.",
                "faces_found": 0,
            }), 400

        detector = get_detector()
        face_result = detector.detect_and_encode(image_path)

        if not face_result.get("success"):
            return jsonify({
                "success": False,
                "error": face_result.get("error", "No face detected in the provided image."),
                "faces_found": 0,
            }), 422

        return jsonify({
            "success": True,
            "faces_found": face_result["faces_found"],
            "confidence": round(face_result["confidence"] * 100, 1),
            "bbox": face_result["bbox"],              # [x1, y1, w, h]
            "facial_area": face_result["facial_area"],  # {x, y, w, h}
            "image_size": [width, height],
            "embedding_dimension": len(face_result.get("primary_encoding", [])),
        })

    except Exception as exc:
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500

    finally:
        try:
            os.unlink(image_path)
        except OSError:
            pass


@app.post("/api/run")
def run_pipeline():
    """
    Run the full pipeline on an uploaded face image.

    Request:  multipart/form-data  { image: <file>, skip_upload?: "true"|"false" }
    Response: JSON with all pipeline stage results
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    skip_upload = request.form.get("skip_upload", "").lower() in ("true", "1")

    # Save uploaded image to a temp file
    suffix = Path(file.filename).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        file.save(tmp.name)
        image_path = tmp.name

    try:
        result = {}

        # ── STEP 1: Face Detection ─────────────────────────────────────
        detector = get_detector()
        face_result = detector.detect_and_encode(image_path)

        if not face_result.get("success"):
            return jsonify({
                "error": f"Face detection failed: {face_result.get('error', 'No face detected')}",
                "step": "face_detection",
            }), 422

        result["face"] = {
            "confidence": round(face_result["confidence"] * 100, 1),
            "bbox": face_result["bbox"],
            "faces_found": face_result["faces_found"],
        }

        # ── STEP 2: Web / Social Media Search ────────────────────────
        matches = search_by_image(image_path)

        if not matches:
            return jsonify({
                "error": "No matching content found on the web.",
                "step": "web_search",
                "face": result["face"],
            }), 404

        best = matches[0]
        result["match"] = {
            "url": best.get("url", ""),
            "platform": best.get("platform", "Web"),
            "title": best.get("title", ""),
            "score": round(best.get("score", 0) * 100, 1),
            "local_path": best.get("local_path", ""),
        }
        result["candidates"] = [
            {
                "url": m.get("url", ""),
                "platform": m.get("platform", "Web"),
                "title": m.get("title", ""),
                "score": round(m.get("score", 0) * 100, 1),
            }
            for m in matches[:5]
        ]

        # ── STEP 3a: Fingerprint ──────────────────────────────────────
        fingerprint = compute_fingerprint(image_path, best)
        result["fingerprint"] = fingerprint
        result["contract_address"] = os.getenv("CONTRACT_ADDRESS", "")
        result["abi"] = FACECHAIN_VERIFY_ABI

        if not skip_upload:
            # ── STEP 3b: Blockchain Upload via Custodial Backend ──────────
            upload = upload_to_chain(fingerprint)
            result["upload"] = {
                "success": upload.get("success", False),
                "already_exists": upload.get("already_exists", False),
                "transaction_hash": upload.get("transaction_hash"),
                "block_number": upload.get("block_number"),
                "network": upload.get("network", "Ethereum Sepolia"),
            }

            # ── STEP 3c: Verification ─────────────────────────────────────
            verify = verify_on_chain_full(fingerprint)
            ts = verify.get("timestamp", 0)
            human_ts = (
                datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%d %b %Y, %H:%M UTC")
                if ts else "unknown"
            )
            result["verification"] = {
                "verified": verify.get("verified", False),
                "timestamp": ts,
                "human_timestamp": human_ts,
                "message": verify.get("message", ""),
            }
        else:
            result["upload"] = None
            result["verification"] = None

        result["success"] = True
        return jsonify(result)

    except Exception as exc:
        traceback.print_exc()
        return jsonify({
            "error": str(exc),
            "step": "pipeline",
        }), 500

    finally:
        try:
            os.unlink(image_path)
        except OSError:
            pass


@app.post("/api/verify")
def verify_hash():
    """
    On-demand verification of an existing fingerprint on Ethereum Sepolia.
    """
    data = request.get_json(silent=True) or {}
    fingerprint = data.get("fingerprint")
    if not fingerprint:
        return jsonify({"error": "Missing fingerprint"}), 400

    try:
        verify = verify_on_chain_full(fingerprint)
        ts = verify.get("timestamp", 0)
        human_ts = (
            datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%d %b %Y, %H:%M UTC")
            if ts else "unknown"
        )
        return jsonify({
            "success": True,
            "verified": verify.get("verified", False),
            "timestamp": ts,
            "human_timestamp": human_ts,
            "message": verify.get("message", ""),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/tamper")
def simulate_tamper():
    """
    Simulate tampered content by altering the fingerprint and running
    actual on-chain verification against Sepolia to prove tampering is detected.
    """
    data = request.get_json(silent=True) or {}
    fingerprint = data.get("fingerprint")
    if not fingerprint or len(fingerprint) != 64:
        return jsonify({"error": "Invalid fingerprint"}), 400

    # Flip characters to create a deterministically modified fingerprint
    # that simulates altered image pixels or metadata
    tampered_fp = ("deadbeef" if not fingerprint.startswith("deadbeef") else "cafebabe") + fingerprint[8:]

    try:
        verify = verify_on_chain_full(tampered_fp)
        return jsonify({
            "success": True,
            "original_fingerprint": fingerprint,
            "tampered_fingerprint": tampered_fp,
            "verified": verify.get("verified", False),
            "timestamp": verify.get("timestamp", 0),
            "message": verify.get("message", "Tamper detected: No on-chain record for modified fingerprint"),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    print("FaceChain Verify API — http://localhost:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)
