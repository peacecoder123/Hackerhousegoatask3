"""
blockchain/abi.py
-----------------
The ABI for FaceChainVerify.sol, embedded as a Python constant.

This avoids requiring a compiled Hardhat artifacts/ directory at runtime.
The ABI is derived directly from FaceChainVerify.sol and must be kept in
sync with any changes to the Solidity contract.

Functions exposed by the contract:
  - store(bytes32 fingerprint)          external      [writes, costs gas]
  - verify(bytes32 fingerprint)         external view [reads, free]
  - records(bytes32)                    public view   [auto-generated getter]

Events:
  - FingerprintStored(bytes32 fingerprint, address recorder, uint256 timestamp)
"""

FACECHAIN_VERIFY_ABI = [
    # ── store(bytes32 fingerprint) ─────────────────────────────────────────
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "fingerprint",
                "type": "bytes32",
            }
        ],
        "name": "store",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # ── verify(bytes32 fingerprint) → (bool isValid, uint256 timestamp) ───
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "fingerprint",
                "type": "bytes32",
            }
        ],
        "name": "verify",
        "outputs": [
            {
                "internalType": "bool",
                "name": "isValid",
                "type": "bool",
            },
            {
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256",
            },
        ],
        "stateMutability": "view",
        "type": "function",
    },
    # ── records(bytes32) → uint256  (public mapping auto-getter) ──────────
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "",
                "type": "bytes32",
            }
        ],
        "name": "records",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    # ── FingerprintStored event ────────────────────────────────────────────
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "fingerprint",
                "type": "bytes32",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "recorder",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "timestamp",
                "type": "uint256",
            },
        ],
        "name": "FingerprintStored",
        "type": "event",
    },
]
