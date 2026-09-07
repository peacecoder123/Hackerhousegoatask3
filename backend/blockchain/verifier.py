"""
blockchain/verifier.py
-----------------------
Verify a SHA-256 content fingerprint against the FaceChainVerify on-chain record.

This is a READ-ONLY operation — it calls the view function verify(bytes32) and
does NOT send a transaction or spend any gas.

Tamper detection logic
----------------------
ORIGINAL CONTENT
    → compute_fingerprint(image_path, metadata) → HASH_A
    → upload_to_chain(HASH_A)  (Member 3 stores it on Sepolia)

LATER VERIFICATION
    → compute_fingerprint(possibly_modified_content, metadata) → HASH_B
    → verify_on_chain(HASH_B)

    If HASH_B == on-chain HASH_A → CONTENT INTEGRITY VERIFIED ✓
    If HASH_B != on-chain HASH_A → INTEGRITY MISMATCH / CONTENT CHANGED ✗
    (Different hash → verify() returns isValid=False)

Member 3 owns this file.
"""

from __future__ import annotations

import logging
import os
from typing import Tuple

from web3 import Web3
from web3.exceptions import Web3Exception

from .abi import FACECHAIN_VERIFY_ABI
from .fingerprint import validate_fingerprint, fingerprint_to_bytes32

log = logging.getLogger(__name__)

EXPECTED_CHAIN_ID = 11155111
EXPECTED_NETWORK = "Ethereum Sepolia"


def verify_on_chain(fingerprint: str) -> Tuple[bool, int]:
    """
    Query the FaceChainVerify smart contract to check if a fingerprint was stored.

    This is a VIEW call — no transaction is sent, no gas is consumed.

    Args:
        fingerprint: A 64-character lowercase hex SHA-256 digest.

    Returns:
        A tuple (is_valid, timestamp):
            - is_valid:  True if the fingerprint is found on-chain.
            - timestamp: Unix timestamp when it was stored (0 if not found).

    Raises:
        ValueError:   Invalid fingerprint.
        RuntimeError: Missing env vars, wrong network, or RPC failure.

    Note:
        For a richer response dict, use verify_on_chain_full() instead.
    """
    result = verify_on_chain_full(fingerprint)
    return result["verified"], result["timestamp"]


def verify_on_chain_full(fingerprint: str) -> dict:
    """
    Full structured verification against the on-chain record.

    Args:
        fingerprint: A 64-character lowercase hex SHA-256 digest.

    Returns:
        A dict:
            {
                "verified":   True | False,
                "timestamp":  <unix timestamp> | 0,
                "fingerprint": "abc123...",
                "network":    "Ethereum Sepolia",
                "message":    "Content integrity verified" | "Integrity mismatch"
            }

    Raises:
        ValueError:   Invalid fingerprint.
        RuntimeError: Missing env vars, wrong network, or RPC failure.
    """
    # ── 1. Validate fingerprint ──────────────────────────────────────────────
    validate_fingerprint(fingerprint)
    fp_bytes32: bytes = fingerprint_to_bytes32(fingerprint)

    # ── 2. Load env (no private key needed for reads) ────────────────────────
    provider_url, contract_address = _load_read_env()

    # ── 3. Connect to RPC ────────────────────────────────────────────────────
    w3 = _connect(provider_url)

    # ── 4. Validate network ──────────────────────────────────────────────────
    _validate_network(w3)

    # ── 5. Load contract ─────────────────────────────────────────────────────
    contract = _load_contract(w3, contract_address)

    # ── 6. Call verify() view function ──────────────────────────────────────
    try:
        is_valid, timestamp = contract.functions.verify(fp_bytes32).call()
    except Web3Exception as exc:
        raise RuntimeError(
            f"Failed to call verify() on contract {contract_address}: {exc}"
        ) from exc

    log.info(
        "verify_on_chain: fingerprint=%s...%s  verified=%s  timestamp=%s",
        fingerprint[:10],
        fingerprint[-6:],
        is_valid,
        timestamp,
    )

    if is_valid:
        message = "Content integrity verified — fingerprint matches on-chain record ✓"
    else:
        message = (
            "Integrity mismatch — fingerprint NOT found on-chain. "
            "Content may have been tampered with or was never uploaded. ✗"
        )

    return {
        "verified": bool(is_valid),
        "timestamp": int(timestamp),
        "fingerprint": fingerprint,
        "network": EXPECTED_NETWORK,
        "message": message,
    }


# ── Private helpers ────────────────────────────────────────────────────────

def _load_read_env() -> tuple[str, str]:
    """Load env vars needed for read-only verification (no private key)."""
    missing = []
    provider_url = os.getenv("WEB3_PROVIDER_URL", "").strip()
    contract_address = os.getenv("CONTRACT_ADDRESS", "").strip()

    if not provider_url:
        missing.append("WEB3_PROVIDER_URL")
    if not contract_address:
        missing.append("CONTRACT_ADDRESS")

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in your credentials."
        )
    return provider_url, contract_address


def _connect(provider_url: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(provider_url))
    if not w3.is_connected():
        raise RuntimeError(
            f"Cannot connect to Ethereum RPC: {provider_url}\n"
            "Check WEB3_PROVIDER_URL is correct and the endpoint is reachable."
        )
    return w3


def _validate_network(w3: Web3) -> None:
    try:
        chain_id = w3.eth.chain_id
    except Exception as exc:
        raise RuntimeError(f"Could not fetch chain ID from RPC: {exc}") from exc

    if chain_id != EXPECTED_CHAIN_ID:
        raise RuntimeError(
            f"Wrong network! Expected {EXPECTED_NETWORK} (chain ID {EXPECTED_CHAIN_ID}), "
            f"but connected to chain ID {chain_id}."
        )


def _load_contract(w3: Web3, raw_address: str):
    try:
        checksummed = Web3.to_checksum_address(raw_address)
    except Exception as exc:
        raise ValueError(
            f"CONTRACT_ADDRESS '{raw_address}' is not a valid Ethereum address: {exc}"
        ) from exc

    code = w3.eth.get_code(checksummed)
    if code == b"" or code == b"0x":
        raise RuntimeError(
            f"No contract found at {checksummed} on {EXPECTED_NETWORK}. "
            "Deploy it first with: npx hardhat run scripts/deploy.js --network sepolia"
        )

    return w3.eth.contract(address=checksummed, abi=FACECHAIN_VERIFY_ABI)
