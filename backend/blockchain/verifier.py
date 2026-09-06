"""
blockchain/verifier.py
-----------------------
Re-verify a content fingerprint against the on-chain record.

Member 3 owns this file.
"""

from __future__ import annotations
import os
from typing import Tuple


def verify_on_chain(fingerprint: str) -> Tuple[bool, int]:
    """
    Query the smart contract to verify a fingerprint matches the stored record.

    Args:
        fingerprint: A 64-character hex SHA-256 digest to verify.

    Returns:
        A tuple (is_valid, timestamp) where:
          - is_valid: True if the fingerprint exists on-chain.
          - timestamp: Unix timestamp of when it was recorded (0 if not found).

    Raises:
        RuntimeError: If required environment variables are missing.
    """
    provider_url = os.getenv("WEB3_PROVIDER_URL")
    contract_address = os.getenv("CONTRACT_ADDRESS")

    if not all([provider_url, contract_address]):
        raise RuntimeError(
            "Missing one or more required environment variables: "
            "WEB3_PROVIDER_URL, CONTRACT_ADDRESS"
        )

    # TODO (Member 3): Implement the on-chain query.
    #
    # from web3 import Web3
    # w3 = Web3(Web3.HTTPProvider(provider_url))
    #
    # contract_abi = [...]  # Load ABI from contracts/FaceChainVerify.json
    # contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    #
    # fp_bytes = bytes.fromhex(fingerprint)
    # is_valid, timestamp = contract.functions.verify(fp_bytes).call()
    # return is_valid, timestamp

    raise NotImplementedError(
        "verify_on_chain() is not yet implemented. "
        "See the TODO comment above for guidance."
    )
