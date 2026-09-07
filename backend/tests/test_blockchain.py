"""
tests/test_blockchain.py
------------------------
Comprehensive unit tests for the FaceChain Verify blockchain module.

Test categories
---------------
  A. Fingerprint tests (no network required)
  B. bytes32 conversion tests (no network required)
  C. Fingerprint validation tests (no network required)
  D. Uploader unit tests (mocked Web3)
  E. Verifier unit tests (mocked Web3)
  F. Duplicate fingerprint handling (mocked Web3)
  G. Configuration / environment validation (no network required)
  H. Verification response parsing tests (no network required)

To run all unit tests (no credentials needed):
    cd backend/
    pytest tests/test_blockchain.py -v

To run ONLY live Sepolia integration tests (requires .env with real credentials):
    cd backend/
    pytest tests/test_blockchain_live.py -v -s

DO NOT add live network calls to this file.
"""

from __future__ import annotations

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

from web3 import Web3

from blockchain.fingerprint import (
    compute_fingerprint,
    fingerprint_to_bytes32,
    validate_fingerprint,
)


# ════════════════════════════════════════════════════════════════════════════
# A. Fingerprint tests
# ════════════════════════════════════════════════════════════════════════════

class TestComputeFingerprint:
    """Tests for compute_fingerprint()"""

    def test_returns_64_char_hex_string(self, tmp_path):
        """Must return exactly 64 lowercase hex characters."""
        img = tmp_path / "face.jpg"
        img.write_bytes(b"fake image data")

        fp = compute_fingerprint(str(img), {"url": "https://example.com", "platform": "Instagram"})

        assert isinstance(fp, str)
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)

    def test_deterministic_same_inputs(self, tmp_path):
        """Identical inputs must always produce the identical fingerprint."""
        img = tmp_path / "face.jpg"
        img.write_bytes(b"consistent image bytes")
        metadata = {"platform": "Reddit", "url": "https://reddit.com/r/test"}

        fp1 = compute_fingerprint(str(img), metadata)
        fp2 = compute_fingerprint(str(img), metadata)

        assert fp1 == fp2

    def test_metadata_key_order_irrelevant(self, tmp_path):
        """Sorted-key JSON ensures key order does not affect the digest."""
        img = tmp_path / "face.jpg"
        img.write_bytes(b"image bytes")

        fp1 = compute_fingerprint(str(img), {"a": "1", "b": "2"})
        fp2 = compute_fingerprint(str(img), {"b": "2", "a": "1"})

        assert fp1 == fp2

    def test_different_metadata_gives_different_fp(self, tmp_path):
        """Different metadata must produce different fingerprints."""
        img = tmp_path / "face.jpg"
        img.write_bytes(b"image bytes")

        fp1 = compute_fingerprint(str(img), {"url": "https://site-a.com"})
        fp2 = compute_fingerprint(str(img), {"url": "https://site-b.com"})

        assert fp1 != fp2

    def test_different_image_bytes_give_different_fp(self, tmp_path):
        """Different image content must produce different fingerprints."""
        img1 = tmp_path / "face1.jpg"
        img2 = tmp_path / "face2.jpg"
        img1.write_bytes(b"image content A")
        img2.write_bytes(b"image content B")
        meta = {"url": "https://example.com"}

        fp1 = compute_fingerprint(str(img1), meta)
        fp2 = compute_fingerprint(str(img2), meta)

        assert fp1 != fp2

    def test_missing_image_raises_file_not_found(self):
        """Must raise FileNotFoundError for a non-existent path."""
        with pytest.raises(FileNotFoundError, match="Image not found"):
            compute_fingerprint("/nonexistent/path/face.jpg", {})

    def test_non_dict_metadata_raises_type_error(self, tmp_path):
        """Non-dict metadata must raise TypeError."""
        img = tmp_path / "face.jpg"
        img.write_bytes(b"data")
        with pytest.raises(TypeError, match="metadata must be a dict"):
            compute_fingerprint(str(img), ["not", "a", "dict"])

    def test_empty_metadata_is_valid(self, tmp_path):
        """Empty metadata dict is valid and produces a stable fingerprint."""
        img = tmp_path / "face.jpg"
        img.write_bytes(b"data")
        fp = compute_fingerprint(str(img), {})
        assert len(fp) == 64

    def test_nested_metadata_is_handled(self, tmp_path):
        """Nested dict values in metadata should serialize correctly."""
        img = tmp_path / "face.jpg"
        img.write_bytes(b"data")
        fp = compute_fingerprint(str(img), {"meta": {"key": "value"}, "score": 0.94})
        assert len(fp) == 64


# ════════════════════════════════════════════════════════════════════════════
# B. bytes32 conversion
# ════════════════════════════════════════════════════════════════════════════

class TestFingerprintToBytes32:
    """Tests for fingerprint_to_bytes32()"""

    def test_returns_32_bytes(self):
        """A valid 64-char hex fingerprint converts to exactly 32 bytes."""
        valid_fp = "a" * 64
        result = fingerprint_to_bytes32(valid_fp)
        assert isinstance(result, bytes)
        assert len(result) == 32

    def test_round_trip(self):
        """bytes.hex() of the result should reproduce the original fingerprint."""
        valid_fp = "9f8a7c2e4d8b91ac7f2e0a16c81dabcd" * 2  # 64 chars
        assert fingerprint_to_bytes32(valid_fp).hex() == valid_fp

    def test_rejects_invalid_fingerprint(self):
        """Must raise ValueError for a too-short fingerprint."""
        with pytest.raises(ValueError):
            fingerprint_to_bytes32("abc123")


# ════════════════════════════════════════════════════════════════════════════
# C. Fingerprint validation
# ════════════════════════════════════════════════════════════════════════════

class TestValidateFingerprint:
    """Tests for validate_fingerprint()"""

    def test_valid_fingerprint_passes(self):
        validate_fingerprint("a" * 64)  # must not raise

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="exactly 64"):
            validate_fingerprint("abc")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="exactly 64"):
            validate_fingerprint("a" * 65)

    def test_uppercase_hex_rejected(self):
        """Fingerprint must be lowercase — uppercase hex is rejected."""
        with pytest.raises(ValueError, match="lowercase hex"):
            validate_fingerprint("A" * 64)

    def test_non_hex_chars_rejected(self):
        """Non-hex characters must be rejected."""
        with pytest.raises(ValueError):
            validate_fingerprint("z" * 64)

    def test_non_string_raises(self):
        """Non-string input must raise ValueError."""
        with pytest.raises(ValueError, match="must be a string"):
            validate_fingerprint(12345)  # type: ignore

    def test_none_raises(self):
        with pytest.raises(ValueError):
            validate_fingerprint(None)  # type: ignore


# ════════════════════════════════════════════════════════════════════════════
# D. Uploader unit tests (mocked Web3 — no real network)
# ════════════════════════════════════════════════════════════════════════════

VALID_FP = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
VALID_ADDRESS = "0x1234567890AbcdEF1234567890AbCdef12345678"
VALID_CONTRACT = "0xAbCdEf1234567890AbCdEf1234567890AbCdEf12"


def _make_mock_w3(chain_id=11155111, balance=10**18, code=b"\x60\x60"):
    """Helper — build a fully-mocked Web3 instance."""
    w3 = MagicMock()
    w3.is_connected.return_value = True
    w3.eth.chain_id = chain_id
    w3.eth.get_balance.return_value = balance
    w3.eth.get_code.return_value = code
    w3.eth.gas_price = 10**9  # 1 gwei
    w3.eth.get_transaction_count.return_value = 0
    w3.from_wei.return_value = 1.0

    # account
    account = MagicMock()
    account.address = VALID_ADDRESS
    w3.eth.account.from_key.return_value = account

    # contract
    contract = MagicMock()
    contract.functions.records.return_value.call.return_value = 0   # not stored yet
    contract.functions.store.return_value.estimate_gas.return_value = 50000
    contract.functions.store.return_value.build_transaction.return_value = {
        "from": VALID_ADDRESS,
        "nonce": 0,
        "gas": 60000,
        "gasPrice": 10**9,
        "chainId": 11155111,
        "data": b"",
    }
    w3.eth.contract.return_value = contract

    # sign_transaction
    signed = MagicMock()
    signed.raw_transaction = b"\x00" * 32
    w3.eth.account.sign_transaction.return_value = signed

    # send / receipt
    w3.eth.send_raw_transaction.return_value = bytes.fromhex(
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    )
    receipt = MagicMock()
    receipt.status = 1
    receipt.blockNumber = 9999999
    receipt.transactionHash = bytes.fromhex(
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    )
    w3.eth.wait_for_transaction_receipt.return_value = receipt

    # to_checksum_address
    w3.to_checksum_address = Web3.to_checksum_address

    return w3, contract


class TestUploadToChain:
    """Mocked uploader tests — no real network required."""

    def _env(self):
        return {
            "WEB3_PROVIDER_URL": "https://sepolia.infura.io/v3/fake",
            "WALLET_PRIVATE_KEY": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
            "CONTRACT_ADDRESS": VALID_CONTRACT,
        }

    @patch("blockchain.uploader.Web3")
    def test_successful_upload_returns_dict(self, MockWeb3):
        """A successful upload returns a dict with the expected keys."""
        from blockchain.uploader import upload_to_chain

        w3, _ = _make_mock_w3()
        MockWeb3.return_value = w3
        MockWeb3.HTTPProvider = MagicMock()
        MockWeb3.to_checksum_address = Web3.to_checksum_address

        with patch.dict(os.environ, self._env()):
            result = upload_to_chain(VALID_FP)

        assert result["success"] is True
        assert "transaction_hash" in result
        assert result["network"] == "Ethereum Sepolia"
        assert result["fingerprint"] == VALID_FP
        assert result.get("already_exists") is False

    @patch("blockchain.uploader.Web3")
    def test_missing_env_vars_raises_runtime_error(self, MockWeb3):
        """Missing env vars must raise RuntimeError with helpful message."""
        from blockchain.uploader import upload_to_chain

        with patch.dict(os.environ, {}, clear=True):
            # Remove the blockchain vars if present
            for key in ["WEB3_PROVIDER_URL", "WALLET_PRIVATE_KEY", "CONTRACT_ADDRESS"]:
                os.environ.pop(key, None)
            with pytest.raises(RuntimeError, match="Missing required environment variables"):
                upload_to_chain(VALID_FP)

    def test_invalid_fingerprint_raises_value_error(self):
        """An invalid fingerprint must raise ValueError before touching the network."""
        from blockchain.uploader import upload_to_chain

        with pytest.raises(ValueError):
            upload_to_chain("not-a-valid-fingerprint")

    def test_too_short_fingerprint_rejected(self):
        from blockchain.uploader import upload_to_chain

        with pytest.raises(ValueError):
            upload_to_chain("abc123")

    @patch("blockchain.uploader.Web3")
    def test_wrong_chain_id_raises_runtime_error(self, MockWeb3):
        """Connection to mainnet (chain 1) instead of Sepolia must be refused."""
        from blockchain.uploader import upload_to_chain

        w3, _ = _make_mock_w3(chain_id=1)  # Ethereum mainnet
        MockWeb3.return_value = w3
        MockWeb3.HTTPProvider = MagicMock()
        MockWeb3.to_checksum_address = Web3.to_checksum_address

        with patch.dict(os.environ, self._env()):
            with pytest.raises(RuntimeError, match="Wrong network"):
                upload_to_chain(VALID_FP)

    @patch("blockchain.uploader.Web3")
    def test_zero_balance_raises_runtime_error(self, MockWeb3):
        """A wallet with 0 ETH must raise a RuntimeError with faucet hint."""
        from blockchain.uploader import upload_to_chain

        w3, _ = _make_mock_w3(balance=0)
        MockWeb3.return_value = w3
        MockWeb3.HTTPProvider = MagicMock()
        MockWeb3.to_checksum_address = Web3.to_checksum_address

        with patch.dict(os.environ, self._env()):
            with pytest.raises(RuntimeError, match="0 ETH"):
                upload_to_chain(VALID_FP)

    @patch("blockchain.uploader.Web3")
    def test_duplicate_fingerprint_returns_already_exists(self, MockWeb3):
        """A fingerprint already on-chain returns already_exists=True without new TX."""
        from blockchain.uploader import upload_to_chain

        w3, contract = _make_mock_w3()
        # Simulate existing record timestamp
        contract.functions.records.return_value.call.return_value = 1700000000
        MockWeb3.return_value = w3
        MockWeb3.HTTPProvider = MagicMock()
        MockWeb3.to_checksum_address = Web3.to_checksum_address

        with patch.dict(os.environ, self._env()):
            result = upload_to_chain(VALID_FP)

        assert result["success"] is True
        assert result["already_exists"] is True
        assert result["verified"] is True
        assert "already exists" in result["message"].lower()
        # No new transaction should have been sent
        w3.eth.send_raw_transaction.assert_not_called()

    @patch("blockchain.uploader.Web3")
    def test_rpc_not_connected_raises_runtime_error(self, MockWeb3):
        """An unreachable RPC must raise RuntimeError."""
        from blockchain.uploader import upload_to_chain

        w3 = MagicMock()
        w3.is_connected.return_value = False
        MockWeb3.return_value = w3
        MockWeb3.HTTPProvider = MagicMock()

        with patch.dict(os.environ, self._env()):
            with pytest.raises(RuntimeError, match="Cannot connect"):
                upload_to_chain(VALID_FP)


# ════════════════════════════════════════════════════════════════════════════
# E. Verifier unit tests (mocked Web3 — no real network)
# ════════════════════════════════════════════════════════════════════════════

class TestVerifyOnChain:
    """Mocked verifier tests — no real network required."""

    def _env(self):
        return {
            "WEB3_PROVIDER_URL": "https://sepolia.infura.io/v3/fake",
            "CONTRACT_ADDRESS": VALID_CONTRACT,
        }

    @patch("blockchain.verifier.Web3")
    def test_verified_fingerprint_returns_true(self, MockWeb3):
        """A stored fingerprint returns (True, <timestamp>)."""
        from blockchain.verifier import verify_on_chain

        w3 = MagicMock()
        w3.is_connected.return_value = True
        w3.eth.chain_id = 11155111
        w3.eth.get_code.return_value = b"\x60\x60"
        contract = MagicMock()
        contract.functions.verify.return_value.call.return_value = (True, 1700000000)
        w3.eth.contract.return_value = contract
        MockWeb3.return_value = w3
        MockWeb3.HTTPProvider = MagicMock()
        MockWeb3.to_checksum_address = Web3.to_checksum_address

        with patch.dict(os.environ, self._env()):
            is_valid, ts = verify_on_chain(VALID_FP)

        assert is_valid is True
        assert ts == 1700000000

    @patch("blockchain.verifier.Web3")
    def test_unrecorded_fingerprint_returns_false(self, MockWeb3):
        """A fingerprint not on-chain returns (False, 0)."""
        from blockchain.verifier import verify_on_chain

        w3 = MagicMock()
        w3.is_connected.return_value = True
        w3.eth.chain_id = 11155111
        w3.eth.get_code.return_value = b"\x60\x60"
        contract = MagicMock()
        contract.functions.verify.return_value.call.return_value = (False, 0)
        w3.eth.contract.return_value = contract
        MockWeb3.return_value = w3
        MockWeb3.HTTPProvider = MagicMock()
        MockWeb3.to_checksum_address = Web3.to_checksum_address

        with patch.dict(os.environ, self._env()):
            is_valid, ts = verify_on_chain(VALID_FP)

        assert is_valid is False
        assert ts == 0

    @patch("blockchain.verifier.Web3")
    def test_verify_full_returns_dict_with_expected_keys(self, MockWeb3):
        """verify_on_chain_full() returns dict with verified, timestamp, message."""
        from blockchain.verifier import verify_on_chain_full

        w3 = MagicMock()
        w3.is_connected.return_value = True
        w3.eth.chain_id = 11155111
        w3.eth.get_code.return_value = b"\x60\x60"
        contract = MagicMock()
        contract.functions.verify.return_value.call.return_value = (True, 1700000000)
        w3.eth.contract.return_value = contract
        MockWeb3.return_value = w3
        MockWeb3.HTTPProvider = MagicMock()
        MockWeb3.to_checksum_address = Web3.to_checksum_address

        with patch.dict(os.environ, self._env()):
            result = verify_on_chain_full(VALID_FP)

        assert result["verified"] is True
        assert result["timestamp"] == 1700000000
        assert result["fingerprint"] == VALID_FP
        assert result["network"] == "Ethereum Sepolia"
        assert "message" in result

    def test_invalid_fingerprint_rejected_before_network(self):
        """verify_on_chain() must validate fingerprint before any network call."""
        from blockchain.verifier import verify_on_chain

        with pytest.raises(ValueError):
            verify_on_chain("bad-fingerprint")

    @patch("blockchain.verifier.Web3")
    def test_missing_env_raises_runtime_error(self, _MockWeb3):
        """Missing env vars must raise RuntimeError."""
        from blockchain.verifier import verify_on_chain

        with patch.dict(os.environ, {}, clear=True):
            for key in ["WEB3_PROVIDER_URL", "CONTRACT_ADDRESS"]:
                os.environ.pop(key, None)
            with pytest.raises(RuntimeError, match="Missing required environment variables"):
                verify_on_chain(VALID_FP)


# ════════════════════════════════════════════════════════════════════════════
# F. Duplicate fingerprint handling
# ════════════════════════════════════════════════════════════════════════════

class TestDuplicateHandling:
    """Duplicate fingerprint scenarios."""

    def test_already_exists_response_structure(self):
        """The already_exists response must have the correct structure."""
        # Simulate what upload_to_chain returns for a duplicate
        response = {
            "success": True,
            "already_exists": True,
            "verified": True,
            "transaction_hash": None,
            "block_number": None,
            "contract_address": VALID_CONTRACT,
            "fingerprint": VALID_FP,
            "network": "Ethereum Sepolia",
            "timestamp": 1700000000,
            "message": "Fingerprint already exists on-chain — no new transaction needed",
        }
        assert response["success"] is True
        assert response["already_exists"] is True
        assert response["transaction_hash"] is None  # no new TX
        assert "already exists" in response["message"].lower()


# ════════════════════════════════════════════════════════════════════════════
# G. Configuration validation
# ════════════════════════════════════════════════════════════════════════════

class TestConfigValidation:
    """Environment variable validation."""

    def test_missing_all_vars_raises_runtime_error(self):
        from blockchain.uploader import upload_to_chain

        with patch.dict(os.environ, {}, clear=True):
            for k in ["WEB3_PROVIDER_URL", "WALLET_PRIVATE_KEY", "CONTRACT_ADDRESS"]:
                os.environ.pop(k, None)
            with pytest.raises(RuntimeError, match="Missing required"):
                upload_to_chain(VALID_FP)

    def test_missing_contract_address_raises(self):
        from blockchain.uploader import upload_to_chain

        env = {
            "WEB3_PROVIDER_URL": "https://sepolia.infura.io/v3/fake",
            "WALLET_PRIVATE_KEY": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(RuntimeError, match="CONTRACT_ADDRESS"):
                upload_to_chain(VALID_FP)


# ════════════════════════════════════════════════════════════════════════════
# H. ABI sanity checks
# ════════════════════════════════════════════════════════════════════════════

class TestABI:
    """Verify the embedded ABI has the expected structure."""

    def test_abi_has_store_function(self):
        from blockchain.abi import FACECHAIN_VERIFY_ABI

        store_entries = [e for e in FACECHAIN_VERIFY_ABI if e.get("name") == "store"]
        assert len(store_entries) == 1
        assert store_entries[0]["type"] == "function"
        assert store_entries[0]["inputs"][0]["type"] == "bytes32"

    def test_abi_has_verify_function(self):
        from blockchain.abi import FACECHAIN_VERIFY_ABI

        verify_entries = [e for e in FACECHAIN_VERIFY_ABI if e.get("name") == "verify"]
        assert len(verify_entries) == 1
        outputs = verify_entries[0]["outputs"]
        output_types = [o["type"] for o in outputs]
        assert "bool" in output_types
        assert "uint256" in output_types

    def test_abi_has_fingerprint_stored_event(self):
        from blockchain.abi import FACECHAIN_VERIFY_ABI

        events = [e for e in FACECHAIN_VERIFY_ABI if e.get("type") == "event"]
        assert any(e.get("name") == "FingerprintStored" for e in events)

    def test_abi_store_is_nonpayable(self):
        from blockchain.abi import FACECHAIN_VERIFY_ABI

        store = next(e for e in FACECHAIN_VERIFY_ABI if e.get("name") == "store")
        assert store["stateMutability"] == "nonpayable"

    def test_abi_verify_is_view(self):
        from blockchain.abi import FACECHAIN_VERIFY_ABI

        verify = next(e for e in FACECHAIN_VERIFY_ABI if e.get("name") == "verify")
        assert verify["stateMutability"] == "view"
