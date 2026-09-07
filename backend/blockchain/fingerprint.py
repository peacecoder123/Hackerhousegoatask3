"""
blockchain/fingerprint.py
--------------------------
Compute a SHA-256 fingerprint of discovered content.

The fingerprint covers:
  - Raw bytes of the matching image file
  - Canonicalized (sorted-key) JSON of the post metadata

This ensures the digest is:
  - Deterministic (same inputs → same 64-hex-char output, always)
  - Sensitive to both content changes AND metadata changes
  - Directly convertible to Ethereum bytes32 for on-chain storage

SHA-256 is the chosen algorithm because:
  - It produces exactly 32 bytes (= bytes32 in Solidity)
  - It is collision-resistant for content integrity purposes
  - It is available in Python's standard library with no extra deps

Member 3 owns this file.
"""

from __future__ import annotations
import hashlib
import json
import os
import re


# ── Public API ──────────────────────────────────────────────────────────────

def compute_fingerprint(image_path: str, metadata: dict) -> str:
    """
    Compute a SHA-256 fingerprint of the image bytes + canonicalized metadata.

    Args:
        image_path: Path to the discovered/matching image file.
        metadata:   Dict of post metadata (url, platform, title, etc.).
                    Keys are sorted before hashing for determinism.

    Returns:
        A 64-character lowercase hex-encoded SHA-256 digest.

    Raises:
        FileNotFoundError: If image_path does not exist.
        TypeError:         If metadata is not a dict.
        ValueError:        If metadata values are not JSON-serialisable.
    """
    if not isinstance(metadata, dict):
        raise TypeError(f"metadata must be a dict, got {type(metadata).__name__}")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    hasher = hashlib.sha256()

    # 1. Hash raw image bytes (in chunks to handle large files without OOM)
    with open(image_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hasher.update(chunk)

    # 2. Hash canonicalized metadata JSON (sort_keys=True ensures determinism)
    try:
        meta_bytes = json.dumps(metadata, sort_keys=True, ensure_ascii=True).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"metadata is not JSON-serialisable: {exc}") from exc
    hasher.update(meta_bytes)

    digest = hasher.hexdigest()
    assert len(digest) == 64, "SHA-256 must always produce 64 hex chars"  # sanity guard
    return digest


def fingerprint_to_bytes32(fingerprint: str) -> bytes:
    """
    Convert a 64-char hex SHA-256 fingerprint to a 32-byte value for Solidity bytes32.

    Args:
        fingerprint: 64-character lowercase hex string.

    Returns:
        32-byte bytes object.

    Raises:
        ValueError: If the fingerprint is not exactly 64 valid hex characters.
    """
    validate_fingerprint(fingerprint)
    return bytes.fromhex(fingerprint)


def validate_fingerprint(fingerprint: str) -> None:
    """
    Raise ValueError if the fingerprint is not a valid 64-char hex SHA-256 digest.

    Args:
        fingerprint: String to validate.

    Raises:
        ValueError: With a descriptive message if invalid.
    """
    if not isinstance(fingerprint, str):
        raise ValueError(
            f"Fingerprint must be a string, got {type(fingerprint).__name__}"
        )
    if len(fingerprint) != 64:
        raise ValueError(
            f"Fingerprint must be exactly 64 hex characters, got {len(fingerprint)}: "
            f"'{fingerprint[:20]}...'"
        )
    if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise ValueError(
            f"Fingerprint must contain only lowercase hex characters [0-9a-f]: "
            f"'{fingerprint[:20]}...'"
        )
