"""
pipeline.py
-----------
FaceChain Verify — Main Pipeline Entry Point

Runs the full end-to-end pipeline:
  1. Face detection & embedding (Member 1)
  2. Web / social media search (Member 2)
  3. Blockchain fingerprint, upload & verification (Member 3)

Usage:
    python pipeline.py --image path/to/face.jpg
    python pipeline.py --verify-only <64-char-fingerprint>
"""

from __future__ import annotations
import argparse
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

from utils.logger import get_logger
from face_detection import FaceDetector
from web_search import search_by_image
from blockchain import compute_fingerprint, upload_to_chain, verify_on_chain_full

load_dotenv()
log = get_logger("pipeline")


def run_pipeline(image_path: str) -> None:
    """Run the full FaceChain Verify pipeline on the given face image."""

    log.info("=" * 60)
    log.info("FaceChain Verify Pipeline — Starting")
    log.info("=" * 60)

    # ── Step 1: Face Detection ─────────────────────────────────────
    log.info("[STEP 1] Detecting and encoding face...")
    face_result = FaceDetector().detect_and_encode(image_path)
    log.info(
        "  ✓ Face detected — confidence: %.1f%%, bbox: %s",
        face_result["confidence"] * 100,
        face_result["bbox"],
    )

    # ── Step 2: Web / Social Media Search ─────────────────────────
    log.info("[STEP 2] Searching for matching content on the web...")
    matches = search_by_image(image_path)

    if not matches:
        log.error("  ✗ No matching content found. Aborting.")
        sys.exit(1)

    best = matches[0]
    log.info(
        "  ✓ Best match: %s — '%s' (score: %.1f%%)",
        best["platform"],
        best["title"],
        best["score"] * 100,
    )
    log.info("  ✓ URL: %s", best["url"])

    # ── Step 3a: Fingerprint ───────────────────────────────────────
    log.info("[STEP 3a] Computing SHA-256 content fingerprint...")
    fingerprint = compute_fingerprint(image_path, best)
    log.info("  ✓ Fingerprint: %s...%s", fingerprint[:22], fingerprint[-5:])

    # ── Step 3b: Blockchain Upload ─────────────────────────────────
    log.info("[STEP 3b] Uploading fingerprint to Ethereum Sepolia...")
    upload_result = upload_to_chain(fingerprint)

    if upload_result.get("already_exists"):
        log.info("  ⚠ Fingerprint already on-chain — skipping new transaction.")
    else:
        log.info(
            "  ✓ Transaction confirmed: %s (block #%s)",
            upload_result.get("transaction_hash"),
            upload_result.get("block_number"),
        )

    # ── Step 3c: Verification ──────────────────────────────────────
    log.info("[STEP 3c] Verifying fingerprint on-chain...")
    verify_result = verify_on_chain_full(fingerprint)

    if verify_result["verified"]:
        ts = verify_result["timestamp"]
        human_ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else "unknown"
        log.info("  ✓ VERIFIED — on-chain since %s", human_ts)
        log.info("  %s", verify_result["message"])
    else:
        log.error("  ✗ VERIFICATION FAILED — %s", verify_result["message"])
        sys.exit(1)

    log.info("=" * 60)
    log.info("Pipeline complete — integrity verified ✓")
    log.info("=" * 60)


def run_verify_only(fingerprint: str) -> None:
    """Re-verify an existing fingerprint against the on-chain record."""
    log.info("Re-verifying fingerprint: %s...%s", fingerprint[:22], fingerprint[-5:])
    result = verify_on_chain_full(fingerprint)

    if result["verified"]:
        ts = result["timestamp"]
        human_ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else "unknown"
        log.info("✓ VERIFIED — on-chain since %s", human_ts)
        log.info("  %s", result["message"])
    else:
        log.error("✗ MISMATCH — %s", result["message"])
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FaceChain Verify Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python pipeline.py --image face.jpg\n"
            "  python pipeline.py --verify-only <64-char-hex-fingerprint>\n"
        ),
    )
    parser.add_argument("--image", type=str, help="Path to the face image to process")
    parser.add_argument(
        "--verify-only",
        type=str,
        metavar="FINGERPRINT",
        help="Skip detection/search; only verify an existing fingerprint on-chain",
    )
    args = parser.parse_args()

    if args.verify_only:
        run_verify_only(args.verify_only)
    elif args.image:
        run_pipeline(args.image)
    else:
        parser.print_help()
        sys.exit(1)
