"""
blockchain/health_check.py
---------------------------
Quick health check for the FaceChainVerify blockchain integration.

Reports:
  - RPC connectivity
  - Network name and chain ID
  - Wallet address (derived from private key)
  - Wallet balance in ETH
  - Contract address and reachability

Usage:
    cd backend/
    python -m blockchain.health_check

Never prints the private key.
"""

from __future__ import annotations

import os
import sys
import logging

from dotenv import load_dotenv
from web3 import Web3

from .abi import FACECHAIN_VERIFY_ABI

load_dotenv()

EXPECTED_CHAIN_ID = 11155111
EXPECTED_NETWORK = "Ethereum Sepolia"


def run_health_check() -> bool:
    """
    Run all blockchain health checks and print a status report.

    Returns:
        True if all checks pass, False if any check fails.
    """
    print("\n" + "=" * 55)
    print("  FaceChain Verify — Blockchain Health Check")
    print("=" * 55)

    all_ok = True

    # ── Env vars ────────────────────────────────────────────────────
    provider_url = os.getenv("WEB3_PROVIDER_URL", "").strip()
    private_key = os.getenv("WALLET_PRIVATE_KEY", "").strip()
    contract_address = os.getenv("CONTRACT_ADDRESS", "").strip()

    _print_check("WEB3_PROVIDER_URL set", bool(provider_url))
    _print_check("WALLET_PRIVATE_KEY set", bool(private_key))
    _print_check("CONTRACT_ADDRESS set", bool(contract_address))

    if not all([provider_url, private_key, contract_address]):
        print("\n[ERROR] One or more required env vars are missing.")
        print("  Copy .env.example to .env and fill in your credentials.\n")
        return False

    # ── RPC Connection ───────────────────────────────────────────────
    w3 = Web3(Web3.HTTPProvider(provider_url))
    rpc_ok = w3.is_connected()
    _print_check("RPC connection", rpc_ok)
    if not rpc_ok:
        print(f"\n[ERROR] Cannot connect to: {provider_url}")
        print("  Check WEB3_PROVIDER_URL (Infura/Alchemy Sepolia endpoint).\n")
        return False

    # ── Network / Chain ID ──────────────────────────────────────────
    try:
        chain_id = w3.eth.chain_id
        network_ok = (chain_id == EXPECTED_CHAIN_ID)
        _print_check(
            f"Network: {EXPECTED_NETWORK} (chain ID {EXPECTED_CHAIN_ID})",
            network_ok,
            fail_msg=f"connected to chain ID {chain_id} instead",
        )
        all_ok = all_ok and network_ok
    except Exception as exc:
        _print_check("Chain ID fetch", False, fail_msg=str(exc))
        all_ok = False
        chain_id = None

    # ── Wallet ──────────────────────────────────────────────────────
    try:
        account = w3.eth.account.from_key(private_key)
        wallet_address = account.address
        _print_check("WALLET_PRIVATE_KEY valid", True)
    except Exception as exc:
        _print_check("WALLET_PRIVATE_KEY valid", False, fail_msg=str(exc))
        all_ok = False
        wallet_address = None

    if wallet_address:
        balance_wei = w3.eth.get_balance(wallet_address)
        balance_eth = float(w3.from_wei(balance_wei, "ether"))
        balance_ok = balance_wei > 0
        _print_check(
            f"Wallet balance: {balance_eth:.6f} ETH",
            balance_ok,
            fail_msg="0 ETH — get test ETH from https://sepoliafaucet.com",
        )
        all_ok = all_ok and balance_ok

    # ── Contract ────────────────────────────────────────────────────
    try:
        checksummed = Web3.to_checksum_address(contract_address)
        code = w3.eth.get_code(checksummed)
        contract_ok = code not in (b"", b"0x", bytes.fromhex("0x".replace("0x", "") or ""))
        # robust empty-code check
        contract_ok = len(code) > 2
        _print_check(
            f"Contract at {checksummed[:10]}...{checksummed[-6:]}",
            contract_ok,
            fail_msg="no bytecode — deploy the contract first",
        )
        all_ok = all_ok and contract_ok
    except Exception as exc:
        _print_check("Contract reachable", False, fail_msg=str(exc))
        all_ok = False

    # ── Summary ─────────────────────────────────────────────────────
    print("\n" + "-" * 55)
    if wallet_address:
        print(f"  Wallet : {wallet_address}")
    print(f"  Contract: {contract_address}")
    safe_url = provider_url.split("/v3/")[0] + "/v3/***" if "/v3/" in provider_url else provider_url
    print(f"  RPC     : {safe_url}")
    print("-" * 55)

    if all_ok:
        print("  ✓ All checks passed — blockchain integration ready\n")
    else:
        print("  ✗ Some checks failed — see details above\n")

    return all_ok


def _print_check(label: str, ok: bool, fail_msg: str = "") -> None:
    status = "✓" if ok else "✗"
    suffix = f"  [{fail_msg}]" if (not ok and fail_msg) else ""
    print(f"  {status}  {label}{suffix}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)  # suppress web3 noise during health check
    success = run_health_check()
    sys.exit(0 if success else 1)
