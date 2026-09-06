"""
tests/test_blockchain.py
------------------------
Unit tests for blockchain fingerprinting (the one fully implemented module).
"""

import os
import pytest
from backend.blockchain.fingerprint import compute_fingerprint


def test_compute_fingerprint_returns_hex_string(tmp_path):
    """compute_fingerprint() should return a 64-character hex string."""
    img = tmp_path / "face.jpg"
    img.write_bytes(b"fake image data")

    fp = compute_fingerprint(str(img), {"url": "https://example.com", "platform": "Instagram"})

    assert isinstance(fp, str)
    assert len(fp) == 64
    assert all(c in "0123456789abcdef" for c in fp)


def test_compute_fingerprint_deterministic(tmp_path):
    """Same inputs always produce the same fingerprint."""
    img = tmp_path / "face.jpg"
    img.write_bytes(b"consistent image bytes")
    metadata = {"platform": "Reddit", "url": "https://reddit.com/r/test"}

    fp1 = compute_fingerprint(str(img), metadata)
    fp2 = compute_fingerprint(str(img), metadata)

    assert fp1 == fp2


def test_compute_fingerprint_metadata_order_irrelevant(tmp_path):
    """Metadata key order should not affect the fingerprint (keys are sorted)."""
    img = tmp_path / "face.jpg"
    img.write_bytes(b"image bytes")

    fp1 = compute_fingerprint(str(img), {"a": "1", "b": "2"})
    fp2 = compute_fingerprint(str(img), {"b": "2", "a": "1"})

    assert fp1 == fp2


def test_compute_fingerprint_different_metadata_gives_different_fp(tmp_path):
    """Different metadata should produce different fingerprints."""
    img = tmp_path / "face.jpg"
    img.write_bytes(b"image bytes")

    fp1 = compute_fingerprint(str(img), {"url": "https://site-a.com"})
    fp2 = compute_fingerprint(str(img), {"url": "https://site-b.com"})

    assert fp1 != fp2


def test_compute_fingerprint_missing_image():
    """compute_fingerprint() should raise FileNotFoundError for missing images."""
    with pytest.raises(FileNotFoundError):
        compute_fingerprint("/nonexistent/path/face.jpg", {})
