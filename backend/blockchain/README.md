# `blockchain/` — Fingerprinting, On-Chain Upload & Verification

**Owner: Member 3 (Blockchain & Verification Engineer)**

---

## Architecture

```
Matching Post (image + metadata)
        │
        ▼
  [fingerprint.py]
  compute_fingerprint(image_path, metadata)
        │  SHA-256(image_bytes + sorted_metadata_json)
        ▼
  64-char hex digest  →  bytes32
        │
        ▼
  [uploader.py]
  upload_to_chain(fingerprint)
        │  Web3.py → store(bytes32) transaction
        ▼
  Ethereum Sepolia Testnet
  FaceChainVerify.sol → records[fingerprint] = block.timestamp
        │
        ▼
  [verifier.py]
  verify_on_chain(fingerprint)
        │  view call → verify(bytes32)
        ▼
  (True, timestamp)  →  CONTENT INTEGRITY VERIFIED ✓
  (False, 0)         →  INTEGRITY MISMATCH ✗
```

**Important:** Only the SHA-256 fingerprint (32 bytes) is stored on-chain.
The image itself is never uploaded to the blockchain.

---

## How Fingerprinting Works

`fingerprint.py::compute_fingerprint(image_path, metadata)` performs:

1. Reads the raw bytes of the discovered image in 64 KB chunks
2. Serializes the post metadata with `json.dumps(..., sort_keys=True)` for determinism
3. Computes SHA-256 over `image_bytes || metadata_json_bytes`
4. Returns a 64-character lowercase hex string

Properties:
- **Deterministic**: same inputs → always same output
- **Tamper-sensitive**: any byte change → completely different digest
- **Metadata-order-independent**: key order in the dict does not matter
- **bytes32-compatible**: 64 hex chars = 32 bytes, exactly matching Solidity `bytes32`

---

## How Blockchain Storage Works

`uploader.py::upload_to_chain(fingerprint)`:

1. Validates the 64-char hex fingerprint
2. Connects to Ethereum Sepolia via `WEB3_PROVIDER_URL`
3. Verifies chain ID = 11155111 (rejects mainnet or other chains)
4. Checks wallet balance (requires > 0 Sepolia ETH)
5. Pre-checks if fingerprint already exists (avoids duplicate revert)
6. Calls `FaceChainVerify.store(bytes32)` — costs a small gas fee
7. Waits for transaction confirmation (up to 5 minutes)
8. Returns a structured dict with TX hash, block number, network

Returns:
```python
{
    "success": True,
    "already_exists": False,
    "transaction_hash": "0x...",
    "block_number": 8421907,
    "contract_address": "0x...",
    "fingerprint": "9f8a7c2e...",
    "network": "Ethereum Sepolia",
    "message": "Fingerprint stored successfully"
}
```

---

## How Verification Works

`verifier.py::verify_on_chain(fingerprint)` or `verify_on_chain_full(fingerprint)`:

1. Validates the fingerprint
2. Connects to the same RPC (read-only — no gas, no private key required)
3. Calls the `verify(bytes32)` view function on the contract
4. Returns `(True, timestamp)` if found, `(False, 0)` if not

### Tamper Detection Logic

```
ORIGINAL CONTENT
  → compute_fingerprint() → HASH_A
  → upload_to_chain(HASH_A)   ← stored permanently on Sepolia

LATER, VERIFY CONTENT INTEGRITY:
  → compute_fingerprint(content_to_check) → HASH_B
  → verify_on_chain(HASH_B)

  HASH_B == HASH_A  →  Content is unchanged ✓
  HASH_B != HASH_A  →  Content has been tampered with ✗
```

Any modification to the original image bytes or metadata will produce a different
SHA-256 digest, causing `verify_on_chain()` to return `(False, 0)`.

---

## Duplicate Fingerprint Handling

The Solidity contract prevents storing the same fingerprint twice:

```solidity
require(records[fingerprint] == 0, "FaceChainVerify: fingerprint already recorded");
```

`upload_to_chain()` handles this gracefully:
- Pre-checks the `records` mapping before sending a transaction
- If already stored, returns `already_exists=True` without a new TX or crash
- The existing record remains valid and verifiable

---

## Files

| File | Purpose |
|------|---------|
| `fingerprint.py` | SHA-256 hashing + validation (fully implemented) |
| `uploader.py` | Web3.py upload to Sepolia (fully implemented) |
| `verifier.py` | On-chain read verification (fully implemented) |
| `abi.py` | FaceChainVerify ABI embedded as Python constant |
| `health_check.py` | Connectivity and configuration health check |
| `contracts/FaceChainVerify.sol` | Solidity smart contract |
| `contracts/hardhat.config.js` | Hardhat network config |
| `contracts/scripts/deploy.js` | Deployment script |

---

## Environment Variables

Create a `.env` file in the project root (never commit it):

```env
# Infura or Alchemy Sepolia endpoint
WEB3_PROVIDER_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID

# Sepolia wallet private key — KEEP SECRET
WALLET_PRIVATE_KEY=0x...

# Deployed FaceChainVerify contract address (from deploy.js output)
CONTRACT_ADDRESS=0x...
```

Get a free Infura key: https://infura.io  
Get a free Alchemy key: https://alchemy.com  
Get Sepolia test ETH: https://sepoliafaucet.com

---

## Deployment Instructions

```bash
# 1. Install Hardhat
cd backend/blockchain/contracts
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox dotenv

# 2. Compile the contract
npx hardhat compile

# 3. Deploy to Sepolia (requires WEB3_PROVIDER_URL + WALLET_PRIVATE_KEY in .env)
npx hardhat run scripts/deploy.js --network sepolia

# 4. Copy the printed address to your .env file
CONTRACT_ADDRESS=0x...

# 5. (Optional) Verify source on Etherscan
npx hardhat verify --network sepolia <CONTRACT_ADDRESS>
```

Local testing without real ETH:
```bash
# Start a local Hardhat node
npx hardhat node

# Deploy locally
npx hardhat run scripts/deploy.js --network localhost
```

---

## Running Tests

### Unit tests (no credentials needed — fully mocked)

```bash
cd backend/
pip install -r requirements.txt
pytest tests/test_blockchain.py -v
```

### Live Sepolia integration tests (requires real credentials + funded wallet)

```bash
cd backend/
pytest tests/test_blockchain_live.py -v -s
```

The live tests auto-skip if `.env` credentials are not present.

---

## Blockchain Health Check

```bash
cd backend/
python -m blockchain.health_check
```

Example output:
```
=======================================================
  FaceChain Verify — Blockchain Health Check
=======================================================
  ✓  WEB3_PROVIDER_URL set
  ✓  WALLET_PRIVATE_KEY set
  ✓  CONTRACT_ADDRESS set
  ✓  RPC connection
  ✓  Network: Ethereum Sepolia (chain ID 11155111)
  ✓  WALLET_PRIVATE_KEY valid
  ✓  Wallet balance: 0.250000 ETH
  ✓  Contract at 0xAbCdEf...AbCd
-------------------------------------------------------
  Wallet : 0x1234...5678
  Contract: 0xAbCdEf1234...
  RPC     : https://sepolia.infura.io/v3/***
-------------------------------------------------------
  ✓ All checks passed — blockchain integration ready
```

---

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Missing required environment variables` | `.env` not filled | Copy `.env.example` → `.env` |
| `Cannot connect to Ethereum RPC` | Bad URL or network down | Check `WEB3_PROVIDER_URL` |
| `Wrong network! Expected Ethereum Sepolia` | Wrong RPC endpoint | Use a Sepolia endpoint |
| `Wallet ... has 0 ETH on Sepolia` | Empty wallet | Get ETH from sepoliafaucet.com |
| `No contract found at 0x...` | Contract not deployed | Run `deploy.js` first |
| `WALLET_PRIVATE_KEY is not a valid Ethereum private key` | Bad key format | Must be 0x + 64 hex chars |
| `Transaction was REVERTED` | Contract revert (e.g. duplicate) | Check Etherscan for details |
| `not confirmed within 300s` | Network congestion | Try again or increase gas |

---

## Network Details

| Property | Value |
|----------|-------|
| Network | Ethereum Sepolia |
| Chain ID | 11155111 |
| Currency | Sepolia ETH (test only, no value) |
| Explorer | https://sepolia.etherscan.io |
| Faucet | https://sepoliafaucet.com |
