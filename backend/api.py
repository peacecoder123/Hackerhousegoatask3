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
load_dotenv(BACKEND_DIR / ".env")

# Set UTF-8 for Windows console logging
os.environ.setdefault("PYTHONUTF8", "1")

from face_detection import FaceDetector
from web_search import search_by_image
from blockchain import compute_fingerprint, upload_to_chain, verify_on_chain_full

app = Flask(__name__)
CORS(app)   # Allow Next.js dev server (localhost:3000) to call this API


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "FaceChain Verify API"})


@app.post("/api/run")
def run_pipeline():
    """
    Run the full pipeline on an uploaded face image.

    Request:  multipart/form-data  { image: <file> }
    Response: JSON with all pipeline stage results
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    # Save uploaded image to a temp file
    suffix = Path(file.filename).suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        file.save(tmp.name)
        image_path = tmp.name

    try:
        result = {}

        # ── STEP 1: Face Detection ─────────────────────────────────────
        detector = FaceDetector()
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

        # ── STEP 3a: Fingerprint ──────────────────────────────────────
        fingerprint = compute_fingerprint(image_path, best)
        result["fingerprint"] = fingerprint

        # ── STEP 3b: Blockchain Upload ────────────────────────────────
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

        result["success"] = True
        return jsonify(result)

    except Exception as exc:
        traceback.print_exc()
        return jsonify({
            "error": str(exc),
            "step": "pipeline",
        }), 500

    finally:
        # Clean up temp file
        try:
            os.unlink(image_path)
        except OSError:
            pass


if __name__ == "__main__":
    print("FaceChain Verify API — http://localhost:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)
