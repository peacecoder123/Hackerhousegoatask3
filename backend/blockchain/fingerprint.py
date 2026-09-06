"""
blockchain/fingerprint.py
--------------------------
Compute a SHA-256 fingerprint of discovered content.

Member 3 owns this file.
"""

from __future__ import annotations
import hashlib
import json
import os


def compute_fingerprint(image_path: str, metadata: dict) -> str:
    """
    Compute a SHA-256 fingerprint of the image bytes + sorted metadata JSON.

    The fingerprint is computed over:
      - The raw bytes of the discovered image
      - The JSON-serialised metadata (keys sorted for determinism)

    Args:
        image_path: Path to the discovered/matching image file.
        metadata: Dict of post metadata (url, platform, title, etc.).

    Returns:
        A hex-encoded SHA-256 digest string (64 hex characters).

    Raises:
        FileNotFoundError: If the image path does not exist.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    hasher = hashlib.sha256()

    # Hash the raw image bytes
    with open(image_path, "rb") as f:
        hasher.update(f.read())

    # Hash the metadata (sorted keys ensure determinism)
    meta_bytes = json.dumps(metadata, sort_keys=True).encode("utf-8")
    hasher.update(meta_bytes)

    return hasher.hexdigest()
