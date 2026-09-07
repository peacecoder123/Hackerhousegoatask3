"""
blockchain/uploader.py
-----------------------
Upload a SHA-256 content fingerprint to the FaceChainVerify smart contract
on Ethereum Sepolia.

Architecture
------------
  fingerprint (64 hex chars)
       │
       ▼
  bytes.fromhex() → bytes32
       │
       ▼
  contract.functions.store(fp_bytes32)
       │
       ▼
  sign & broadcast → Ethereum Sepolia
       │
       ▼
  wait for receipt → return structured result

Backward compatibility
----------------------
The public upload_to_chain(fingerprint) function returns a dict, but also
exposes the transaction hash at result["transaction_hash"] so the existing
pipeline.py (which does `tx_hash = upload_to_chain(fingerprint)` and then
logs it) can be updated to access `tx_result["transaction_hash"]`.

See pipeline.py — the pipeline is updated to handle the dict return.

Member 3 owns this file.
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import ContractLogicError, Web3Exception

from .abi import FACECHAIN_VERIFY_ABI
from .fingerprint import validate_fingerprint, fingerprint_to_bytes32

# Load backend/.env so _load_env() can read credentials when uploader is
# imported directly (e.g. in tests or one-off scripts).  load_dotenv() is
# a no-op if the file does not exist or vars are already set.
BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

log = logging.getLogger(__name__)

# Sepolia Chain ID — any connection to a different chain is rejected.
EXPECTED_CHAIN_ID = 11155111
EXPECTED_NETWORK = "Ethereum Sepolia"

# Gas limit for the store() call.  The function is simple (one SSTORE + event),
# so 100 000 is a generous ceiling.  Estimation is used first; this is the cap.
GAS_LIMIT_CEILING = 120_000

# How long to wait for transaction confirmation (seconds).
TX_TIMEOUT_SECONDS = 300


def upload_to_chain(fingerprint: str) -> dict:
    """
    Store a SHA-256 content fingerprint on the FaceChainVerify smart contract.

    Args:
        fingerprint: A 64-character lowercase hex SHA-256 digest.

    Returns:
        A dict containing:
            {
                "success": True,
                "transaction_hash": "0x...",
                "block_number": 12345678,
                "contract_address": "0x...",
                "fingerprint": "abc123...",
                "network": "Ethereum Sepolia",
                "already_exists": False,   # True if duplicate
                "message": "Fingerprint stored successfully"
            }

    Raises:
        ValueError:       Invalid fingerprint or environment configuration.
        RuntimeError:     Missing env vars, wrong network, RPC failure,
                          insufficient balance, or transaction failure.
    """
    # ── 1. Validate fingerprint ──────────────────────────────────────────────
    validate_fingerprint(fingerprint)
    fp_bytes32: bytes = fingerprint_to_bytes32(fingerprint)

    # ── 2. Load environment variables ────────────────────────────────────────
    provider_url, private_key, contract_address = _load_env()

    # ── 3. Connect to RPC ────────────────────────────────────────────────────
    w3 = _connect(provider_url)

    # ── 4. Validate network (chain ID) ───────────────────────────────────────
    _validate_network(w3)

    # ── 5. Load account ──────────────────────────────────────────────────────
    try:
        account = w3.eth.account.from_key(private_key)
    except Exception as exc:
        raise ValueError(
            f"WALLET_PRIVATE_KEY is not a valid Ethereum private key: {exc}"
        ) from exc
    wallet_address = account.address
    log.info("Wallet address: %s", wallet_address)

    # ── 6. Check balance ─────────────────────────────────────────────────────
    balance_wei = w3.eth.get_balance(wallet_address)
    balance_eth = w3.from_wei(balance_wei, "ether")
    log.info("Wallet balance: %s ETH", float(balance_eth))
    if balance_wei == 0:
        raise RuntimeError(
            f"Wallet {wallet_address} has 0 ETH on Sepolia. "
            "Get test ETH from https://sepoliafaucet.com and try again."
        )

    # ── 7. Load contract ─────────────────────────────────────────────────────
    contract = _load_contract(w3, contract_address)

    # ── 8. Pre-check: is this fingerprint already stored? ────────────────────
    already_stored_ts = _check_existing(contract, fp_bytes32)
    if already_stored_ts:
        log.info(
            "Fingerprint already exists on-chain (timestamp: %d). Skipping upload.",
            already_stored_ts,
        )
        return {
            "success": True,
            "already_exists": True,
            "verified": True,
            "transaction_hash": None,
            "block_number": None,
            "contract_address": contract_address,
            "fingerprint": fingerprint,
            "network": EXPECTED_NETWORK,
            "timestamp": already_stored_ts,
            "message": "Fingerprint already exists on-chain — no new transaction needed",
        }

    # ── 9. Build transaction ──────────────────────────────────────────────────
    nonce = w3.eth.get_transaction_count(wallet_address)
    gas_price = w3.eth.gas_price

    try:
        estimated_gas = contract.functions.store(fp_bytes32).estimate_gas(
            {"from": wallet_address}
        )
        gas = min(int(estimated_gas * 1.2), GAS_LIMIT_CEILING)  # 20% headroom
    except ContractLogicError as exc:
        # Contract would revert — catch the duplicate case specifically
        if "already recorded" in str(exc):
            return _already_exists_response(contract, fp_bytes32, fingerprint, contract_address)
        raise RuntimeError(f"Gas estimation failed — contract would revert: {exc}") from exc
    except Exception as exc:
        log.warning("Gas estimation failed (%s); using ceiling %d", exc, GAS_LIMIT_CEILING)
        gas = GAS_LIMIT_CEILING

    txn = contract.functions.store(fp_bytes32).build_transaction(
        {
            "from": wallet_address,
            "nonce": nonce,
            "gas": gas,
            "gasPrice": gas_price,
            "chainId": EXPECTED_CHAIN_ID,
        }
    )

    # ── 10. Sign & send ──────────────────────────────────────────────────────
    signed = w3.eth.account.sign_transaction(txn, private_key=private_key)
    log.info("Sending transaction to Ethereum Sepolia...")

    try:
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    except Web3Exception as exc:
        raise RuntimeError(f"Failed to broadcast transaction: {exc}") from exc

    tx_hash_hex = tx_hash.hex()
    if not tx_hash_hex.startswith("0x"):
        tx_hash_hex = "0x" + tx_hash_hex
    log.info("Transaction submitted: %s", tx_hash_hex)

    # ── 11. Wait for receipt ─────────────────────────────────────────────────
    log.info("Waiting for confirmation (up to %ds)...", TX_TIMEOUT_SECONDS)
    try:
        receipt = w3.eth.wait_for_transaction_receipt(
            tx_hash, timeout=TX_TIMEOUT_SECONDS
        )
    except Exception as exc:
        raise RuntimeError(
            f"Transaction {tx_hash_hex} was not confirmed within "
            f"{TX_TIMEOUT_SECONDS}s. Check it on "
            f"https://sepolia.etherscan.io/tx/{tx_hash_hex}"
        ) from exc

    # ── 12. Verify receipt status ────────────────────────────────────────────
    if receipt.status != 1:
        raise RuntimeError(
            f"Transaction {tx_hash_hex} was REVERTED on-chain (status=0). "
            "This may be a duplicate fingerprint or a gas issue. "
            f"Check: https://sepolia.etherscan.io/tx/{tx_hash_hex}"
        )

    block_number = receipt.blockNumber
    log.info(
        "✓ Fingerprint stored — block #%d, tx: %s", block_number, tx_hash_hex
    )

    return {
        "success": True,
        "already_exists": False,
        "transaction_hash": tx_hash_hex,
        "block_number": block_number,
        "contract_address": contract_address,
        "fingerprint": fingerprint,
        "network": EXPECTED_NETWORK,
        "message": "Fingerprint stored successfully",
    }


# ── Private helpers ────────────────────────────────────────────────────────

def _load_env() -> tuple[str, str, str]:
    """Read and validate required environment variables."""
    missing = []
    provider_url = os.getenv("WEB3_PROVIDER_URL", "").strip()
    private_key = os.getenv("WALLET_PRIVATE_KEY", "").strip()
    contract_address = os.getenv("CONTRACT_ADDRESS", "").strip()

    if not provider_url:
        missing.append("WEB3_PROVIDER_URL")
    if not private_key:
        missing.append("WALLET_PRIVATE_KEY")
    if not contract_address:
        missing.append("CONTRACT_ADDRESS")

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in your credentials."
        )
    return provider_url, private_key, contract_address


def _connect(provider_url: str) -> Web3:
    """Connect to the Ethereum RPC and verify connectivity."""
    w3 = Web3(Web3.HTTPProvider(provider_url))
    if not w3.is_connected():
        raise RuntimeError(
            f"Cannot connect to Ethereum RPC: {provider_url}\n"
            "Check that WEB3_PROVIDER_URL is correct and the node is reachable."
        )
    log.info("RPC connected: %s", provider_url.split("/v3/")[0] + "/v3/***")
    return w3


def _validate_network(w3: Web3) -> None:
    """Ensure the connected network is Ethereum Sepolia (chain ID 11155111)."""
    try:
        chain_id = w3.eth.chain_id
    except Exception as exc:
        raise RuntimeError(f"Could not fetch chain ID from RPC: {exc}") from exc

    if chain_id != EXPECTED_CHAIN_ID:
        raise RuntimeError(
            f"Wrong network! Expected {EXPECTED_NETWORK} (chain ID {EXPECTED_CHAIN_ID}), "
            f"but connected to chain ID {chain_id}. "
            "Update WEB3_PROVIDER_URL to point to a Sepolia endpoint."
        )
    log.info("Network: %s (chain ID %d)", EXPECTED_NETWORK, chain_id)


def _load_contract(w3: Web3, raw_address: str) -> Any:
    """Checksum and load the FaceChainVerify contract."""
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
            "Deploy the contract first:\n"
            "  cd backend/blockchain/contracts && npx hardhat run scripts/deploy.js --network sepolia"
        )

    return w3.eth.contract(address=checksummed, abi=FACECHAIN_VERIFY_ABI)


def _check_existing(contract: Any, fp_bytes32: bytes) -> int:
    """
    Check if the fingerprint is already stored.

    Returns:
        The stored timestamp (> 0) if it exists, or 0 if not found.
    """
    try:
        ts: int = contract.functions.records(fp_bytes32).call()
        return ts
    except Exception:
        return 0


def _already_exists_response(
    contract: Any, fp_bytes32: bytes, fingerprint: str, contract_address: str
) -> dict:
    """Build the 'already exists' response after a contract revert."""
    ts = _check_existing(contract, fp_bytes32)
    return {
        "success": True,
        "already_exists": True,
        "verified": True,
        "transaction_hash": None,
        "block_number": None,
        "contract_address": contract_address,
        "fingerprint": fingerprint,
        "network": EXPECTED_NETWORK,
        "timestamp": ts,
        "message": "Fingerprint already exists on-chain — no new transaction needed",
    }
