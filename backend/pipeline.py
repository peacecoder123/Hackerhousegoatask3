"""
pipeline.py
-----------
FaceChain Verify — Main Pipeline Entry Point

Runs the full end-to-end pipeline:
  1. Face detection & embedding (Member 1)
  2. Web / social media search (Member 2)
  3. Blockchain fingerprint, upload & verification (Member 3)

Usage:
    python pipeline.py --image path/to/face.jpg [--verify-only <fingerprint>]
"""

from __future__ import annotations
import argparse
import sys

from dotenv import load_dotenv

from utils.logger import get_logger
from face_detection import encode_face
from web_search import search_by_image
from blockchain import compute_fingerprint, upload_to_chain, verify_on_chain

load_dotenv()
log = get_logger("pipeline")


def run_pipeline(image_path: str) -> None:
    """Run the full FaceChain Verify pipeline on the given face image."""

    log.info("=" * 60)
    log.info("FaceChain Verify Pipeline — Starting")
    log.info("=" * 60)

    # ── Step 1: Face Detection ─────────────────────────────────────
    log.info("[STEP 1] Detecting and encoding face...")
    face_result = encode_face(image_path)
    log.info(
        f"  ✓ Face detected — confidence: {face_result['confidence']:.1%}, "
        f"bbox: {face_result['bbox']}"
    )

    # ── Step 2: Web / Social Media Search ─────────────────────────
    log.info("[STEP 2] Searching for matching content on the web...")
    matches = search_by_image(image_path)

    if not matches:
        log.error("  ✗ No matching content found. Aborting.")
        sys.exit(1)

    best = matches[0]
    log.info(
        f"  ✓ Best match: {best['platform']} — '{best['title']}' "
        f"(score: {best['score']:.1%})"
    )
    log.info(f"  ✓ URL: {best['url']}")

    # ── Step 3a: Fingerprint ───────────────────────────────────────
    log.info("[STEP 3a] Computing SHA-256 content fingerprint...")
    fingerprint = compute_fingerprint(image_path, best)
    log.info(f"  ✓ Fingerprint: {fingerprint[:22]}...{fingerprint[-5:]}")

    # ── Step 3b: Blockchain Upload ─────────────────────────────────
    log.info("[STEP 3b] Uploading fingerprint to Ethereum Sepolia...")
    tx_hash = upload_to_chain(fingerprint)
    log.info(f"  ✓ Transaction submitted: {tx_hash}")

    # ── Step 3c: Verification ──────────────────────────────────────
    log.info("[STEP 3c] Verifying fingerprint on-chain...")
    is_valid, timestamp = verify_on_chain(fingerprint)

    if is_valid:
        log.info(f"  ✓ VERIFIED — fingerprint matches on-chain record (timestamp: {timestamp})")
    else:
        log.error("  ✗ VERIFICATION FAILED — fingerprint not found on-chain!")
        sys.exit(1)

    log.info("=" * 60)
    log.info("Pipeline complete — integrity verified ✓")
    log.info("=" * 60)


def run_verify_only(fingerprint: str) -> None:
    """Re-verify an existing fingerprint against the on-chain record."""
    log.info(f"Re-verifying fingerprint: {fingerprint[:22]}...{fingerprint[-5:]}")
    is_valid, timestamp = verify_on_chain(fingerprint)

    if is_valid:
        log.info(f"✓ VERIFIED — recorded at timestamp {timestamp}")
    else:
        log.error("✗ MISMATCH — fingerprint not found or content has been tampered with")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FaceChain Verify Pipeline")
    parser.add_argument("--image", type=str, help="Path to the face image to process")
    parser.add_argument(
        "--verify-only",
        type=str,
        metavar="FINGERPRINT",
        help="Skip detection/search and only verify an existing fingerprint",
    )
    args = parser.parse_args()

    if args.verify_only:
        run_verify_only(args.verify_only)
    elif args.image:
        run_pipeline(args.image)
    else:
        parser.print_help()
        sys.exit(1)
