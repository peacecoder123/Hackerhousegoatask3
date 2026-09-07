"""
tests/test_blockchain_live.py
------------------------------
LIVE INTEGRATION TESTS for FaceChain Verify blockchain module.

⚠ These tests send REAL transactions to Ethereum Sepolia.
⚠ They require a funded wallet and valid RPC credentials in your .env file.
⚠ Each test_upload run will consume a small amount of Sepolia test ETH.

Prerequisites
-------------
1. Copy .env.example to .env in the project root.
2. Fill in all variables:
      WEB3_PROVIDER_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
      WALLET_PRIVATE_KEY=0x...your_sepolia_private_key...
      CONTRACT_ADDRESS=0x...your_deployed_contract...
3. Make sure the wallet has Sepolia ETH:
      https://sepoliafaucet.com
4. Deploy the contract first if needed:
      cd backend/blockchain/contracts
      npm install
      npx hardhat run scripts/deploy.js --network sepolia

Run ONLY these live tests:
    cd backend/
    pytest tests/test_blockchain_live.py -v -s

Do NOT run these tests in CI without real credentials.
"""

from __future__ import annotations

import os
import sys
import time
import hashlib
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")  # load from repo root

# ── Skip entire module if env vars are not set ──────────────────────────────
REQUIRED_VARS = ["WEB3_PROVIDER_URL", "WALLET_PRIVATE_KEY", "CONTRACT_ADDRESS"]

missing_vars = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing_vars:
    pytest.skip(
        f"Skipping live tests — missing env vars: {', '.join(missing_vars)}\n"
        "Fill in your .env file to run live integration tests.",
        allow_module_level=True,
    )


from blockchain.fingerprint import compute_fingerprint
from blockchain.uploader import upload_to_chain
from blockchain.verifier import verify_on_chain, verify_on_chain_full


def _make_unique_fingerprint(salt: str = "") -> tuple[str, Path]:
    """
    Create a temporary fake image with unique content so each test
    uses a fresh fingerprint (avoiding the duplicate-fingerprint contract revert).
    """
    import tempfile

    unique_bytes = f"live-test-image-{salt}-{time.time_ns()}".encode()
    tmp = Path(tempfile.mktemp(suffix=".jpg"))
    tmp.write_bytes(unique_bytes)
    meta = {"url": "https://example.com/test", "platform": "LiveTest", "salt": salt}
    fp = compute_fingerprint(str(tmp), meta)
    return fp, tmp


class TestLiveBlockchain:
    """Live Sepolia integration tests."""

    def test_upload_returns_success_dict(self):
        """Upload a fresh fingerprint and confirm the returned dict is correct."""
        fp, tmp = _make_unique_fingerprint("upload-test")
        try:
            result = upload_to_chain(fp)
            assert result["success"] is True
            assert result["network"] == "Ethereum Sepolia"
            assert result["fingerprint"] == fp
            # If not a duplicate, must have a real tx hash
            if not result.get("already_exists"):
                tx = result["transaction_hash"]
                assert isinstance(tx, str)
                assert tx.startswith("0x")
                assert len(tx) == 66  # 0x + 64 hex chars
                assert isinstance(result["block_number"], int)
                print(f"\n  ✓ TX: {tx}")
                print(f"  ✓ Block: {result['block_number']}")
        finally:
            tmp.unlink(missing_ok=True)

    def test_verify_after_upload(self):
        """Upload then immediately verify — must return verified=True."""
        fp, tmp = _make_unique_fingerprint("verify-after-upload")
        try:
            upload_result = upload_to_chain(fp)
            assert upload_result["success"] is True

            # Give Sepolia a moment to propagate (usually instant after receipt)
            time.sleep(2)

            is_valid, timestamp = verify_on_chain(fp)
            assert is_valid is True
            assert timestamp > 0
            print(f"\n  ✓ Verified at timestamp {timestamp}")
        finally:
            tmp.unlink(missing_ok=True)

    def test_verify_unknown_fingerprint_returns_false(self):
        """A fingerprint that was never uploaded must verify as False."""
        # Use a fingerprint derived from the current nanosecond — guaranteed novel
        fake_fp = hashlib.sha256(f"never-uploaded-{time.time_ns()}".encode()).hexdigest()
        is_valid, timestamp = verify_on_chain(fake_fp)
        assert is_valid is False
        assert timestamp == 0

    def test_duplicate_upload_does_not_crash(self):
        """Uploading the same fingerprint twice must return already_exists=True gracefully."""
        fp, tmp = _make_unique_fingerprint("dup-test")
        try:
            r1 = upload_to_chain(fp)
            assert r1["success"] is True

            # Second upload of the same fingerprint
            r2 = upload_to_chain(fp)
            assert r2["success"] is True
            assert r2["already_exists"] is True
            assert "already exists" in r2["message"].lower()
            print("\n  ✓ Duplicate fingerprint handled gracefully")
        finally:
            tmp.unlink(missing_ok=True)

    def test_verify_full_returns_structured_dict(self):
        """verify_on_chain_full() returns a complete structured response."""
        fp, tmp = _make_unique_fingerprint("full-verify-test")
        try:
            upload_to_chain(fp)
            time.sleep(2)

            result = verify_on_chain_full(fp)
            assert "verified" in result
            assert "timestamp" in result
            assert "message" in result
            assert "network" in result
            assert result["network"] == "Ethereum Sepolia"
            print(f"\n  ✓ {result['message']}")
        finally:
            tmp.unlink(missing_ok=True)

    def test_tamper_detection(self):
        """
        TAMPER DETECTION END-TO-END TEST

        1. Create ORIGINAL content → compute fingerprint A → store on-chain
        2. Modify content → compute fingerprint B
        3. Verify fingerprint B → should NOT match (is_valid=False)
        """
        import tempfile

        # ── 1. Original content ──────────────────────────────────────
        original_path = Path(tempfile.mktemp(suffix=".jpg"))
        original_path.write_bytes(b"ORIGINAL IMAGE CONTENT")
        meta = {"url": "https://example.com/original", "platform": "Instagram"}
        fp_original = compute_fingerprint(str(original_path), meta)
        print(f"\n  Original fingerprint: {fp_original[:16]}...")

        # ── 2. Store original fingerprint ────────────────────────────
        upload_result = upload_to_chain(fp_original)
        assert upload_result["success"] is True
        time.sleep(2)

        # ── 3. Tampered content ──────────────────────────────────────
        tampered_path = Path(tempfile.mktemp(suffix=".jpg"))
        tampered_path.write_bytes(b"TAMPERED IMAGE CONTENT — different bytes!")
        fp_tampered = compute_fingerprint(str(tampered_path), meta)
        print(f"  Tampered fingerprint: {fp_tampered[:16]}...")

        assert fp_original != fp_tampered, "Tampered content must produce a different fingerprint"

        # ── 4. Verify tampered fingerprint → must fail ───────────────
        is_valid, timestamp = verify_on_chain(fp_tampered)
        assert is_valid is False
        assert timestamp == 0
        print("  ✓ Tampered content correctly detected as NOT verified")

        # ── 5. Verify original fingerprint → must pass ───────────────
        is_valid_orig, ts_orig = verify_on_chain(fp_original)
        assert is_valid_orig is True
        print(f"  ✓ Original content correctly verified (timestamp: {ts_orig})")

        # Cleanup
        original_path.unlink(missing_ok=True)
        tampered_path.unlink(missing_ok=True)
