"""
blockchain/uploader.py
-----------------------
Upload a content fingerprint to the FaceChainVerify smart contract on Ethereum Sepolia.

Member 3 owns this file.
"""

from __future__ import annotations
import os


def upload_to_chain(fingerprint: str) -> str:
    """
    Submit the SHA-256 fingerprint to the on-chain smart contract.

    Args:
        fingerprint: A 64-character hex SHA-256 digest.

    Returns:
        The transaction hash (0x-prefixed hex string).

    Raises:
        RuntimeError: If required environment variables are missing.
        Exception: If the blockchain transaction fails or reverts.
    """
    provider_url = os.getenv("WEB3_PROVIDER_URL")
    private_key = os.getenv("WALLET_PRIVATE_KEY")
    contract_address = os.getenv("CONTRACT_ADDRESS")

    if not all([provider_url, private_key, contract_address]):
        raise RuntimeError(
            "Missing one or more required environment variables: "
            "WEB3_PROVIDER_URL, WALLET_PRIVATE_KEY, CONTRACT_ADDRESS"
        )

    # TODO (Member 3): Implement the Web3.py transaction.
    #
    # from web3 import Web3
    # w3 = Web3(Web3.HTTPProvider(provider_url))
    # account = w3.eth.account.from_key(private_key)
    #
    # contract_abi = [...]  # Load from contracts/FaceChainVerify.json
    # contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    #
    # # Convert hex fingerprint to bytes32
    # fp_bytes = bytes.fromhex(fingerprint)
    #
    # txn = contract.functions.store(fp_bytes).build_transaction({
    #     "from": account.address,
    #     "nonce": w3.eth.get_transaction_count(account.address),
    #     "gas": 100000,
    #     "gasPrice": w3.eth.gas_price,
    # })
    # signed = account.sign_transaction(txn)
    # tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    # receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    # return receipt.transactionHash.hex()

    raise NotImplementedError(
        "upload_to_chain() is not yet implemented. "
        "See the TODO comment above for guidance."
    )
