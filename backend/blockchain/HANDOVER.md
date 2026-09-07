# Blockchain & Verification — Member 3 Handover

| Field | Value |
|-------|-------|
| **Status** | Blockchain module: **COMPLETE** · End-to-end pipeline integration: **PENDING** |
| **Owner** | Member 3 — Blockchain & Verification Engineer |
| **Network** | Ethereum Sepolia Testnet |
| **Chain ID** | `11155111` |
| **Deployed Contract** | `0x7Fb9C62FCe11e34667BB04054026382643B08d34` |
| **Web3.py version (installed)** | `8.0.0` (requirements pin `>=7.0.0`) |
| **Unit tests** | **40 / 40 passing** |
| **Live Sepolia tests** | **Passed** — real upload + verification confirmed |

> **READ THIS BEFORE TOUCHING ANYTHING.**
> This document is the integration guide for the teammate connecting Member 1 (face detection) and Member 2 (web search) output to the blockchain module.

---

## Table of Contents

1. [Project Pipeline](#1-project-pipeline)
2. [What is Complete](#2-what-is-complete)
3. [Proven Live Tests](#3-proven-live-tests)
4. [Architecture](#4-architecture)
5. [File Reference](#5-file-reference)
6. [Function Reference](#6-function-reference)
7. [Smart Contract](#7-smart-contract)
8. [Tamper Detection](#8-tamper-detection)
9. [How to Integrate — Integration Instructions](#9-how-to-integrate)
10. [Environment Setup](#10-environment-setup)
11. [Running Tests](#11-running-tests)
12. [End-to-End Demo Plan](#12-end-to-end-demo-plan)
13. [Known Limitations](#13-known-limitations)
14. [Troubleshooting](#14-troubleshooting)
15. [DO NOT CHANGE WITHOUT COORDINATION](#15-do-not-change-without-coordination)
16. [Final Integration Checklist](#16-final-integration-checklist)

---

## 1. Project Pipeline

```
Face Scan / Input Image
        │
        ▼  [Member 1]
Face Detection + Face Embedding
        │
        ▼  [Member 2]
Genuine Web / Social Media Search
        │
        ▼  [Member 2 → Member 3 handoff point]
Matching Social Media / Web Post
  (image file path + post metadata dict)
        │
        ▼  [Member 3 — blockchain/ module]
compute_fingerprint(image_path, metadata)
        │  SHA-256 over image bytes + sorted metadata JSON
        ▼
64-char hex fingerprint
        │  bytes.fromhex() → bytes32
        ▼
upload_to_chain(fingerprint)
        │  Web3.py → FaceChainVerify.store(bytes32) → Sepolia
        ▼
Transaction confirmed on Ethereum Sepolia
        │
        ▼
verify_on_chain_full(fingerprint)
        │  view call → FaceChainVerify.verify(bytes32) → (bool, uint256)
        ▼
Integrity Result → Pipeline / Frontend
```

**The handoff point from Member 2 to Member 3 is a local image file + a metadata dict.**

---

## 2. What is Complete

The following items are fully implemented and tested:

| # | Component | Status | Location |
|---|-----------|--------|----------|
| 1 | SHA-256 fingerprint generation | ✅ Complete | `blockchain/fingerprint.py` |
| 2 | Fingerprint validation (64-char hex) | ✅ Complete | `blockchain/fingerprint.py` |
| 3 | SHA-256 hex → bytes32 conversion | ✅ Complete | `blockchain/fingerprint.py` |
| 4 | Web3.py Ethereum integration | ✅ Complete | `blockchain/uploader.py` |
| 5 | Sepolia chain ID validation (`11155111`) | ✅ Complete | `blockchain/uploader.py` |
| 6 | Smart contract (`FaceChainVerify.sol`) | ✅ Complete | `blockchain/contracts/` |
| 7 | Hardhat compilation config | ✅ Complete | `blockchain/contracts/hardhat.config.js` |
| 8 | Hardhat deployment script | ✅ Complete | `blockchain/contracts/scripts/deploy.js` |
| 9 | Contract deployed on Sepolia | ✅ Live | `0x7Fb9C62FCe11e34667BB04054026382643B08d34` |
| 10 | Transaction build / sign / broadcast | ✅ Complete | `blockchain/uploader.py` |
| 11 | Transaction confirmation wait | ✅ Complete | `blockchain/uploader.py` |
| 12 | Duplicate fingerprint graceful handling | ✅ Complete | `blockchain/uploader.py` |
| 13 | Read-only on-chain verification | ✅ Complete | `blockchain/verifier.py` |
| 14 | Tamper detection (different hash → False) | ✅ Proven live | See Section 3 |
| 15 | Blockchain health check | ✅ Complete | `blockchain/health_check.py` |
| 16 | Embedded ABI (no Hardhat runtime needed) | ✅ Complete | `blockchain/abi.py` |
| 17 | 40 unit tests (fully mocked) | ✅ 40/40 pass | `tests/test_blockchain.py` |
| 18 | Live Sepolia upload + verification | ✅ Confirmed | See Section 3 |

**What remains:**

| # | Component | Status |
|---|-----------|--------|
| A | Connect real matching post from Member 2 → `compute_fingerprint()` | ⏳ Pending integration |
| B | Call `upload_to_chain()` in the full live pipeline | ⏳ Pending integration |
| C | Display transaction hash and verification result in frontend | ⏳ Pending integration |
| D | Full end-to-end screen recording for submission | ⏳ Pending |

---

## 3. Proven Live Tests

These tests were performed against the **real deployed contract on Ethereum Sepolia**. No mocking.

### Test 1 — Upload and Verify (SUCCESS)

```
Test file : blockchain/test_image.txt
Metadata  : {"url": "https://example.com/test", "platform": "test", "title": "Blockchain Integration Test"}
Fingerprint: 8f44e262d075fe6384bab049d909cde12f77b59d584a18fa64b00c38bd6e47c6

upload_to_chain() result:
  success          : True
  already_exists   : False
  transaction_hash : 0x812fa98909da148f4bc072aad044a0823dd54c9c2414610cba0008464ed1d2b3
  block_number     : 11654132
  network          : Ethereum Sepolia
  message          : Fingerprint stored successfully
```

### Test 2 — Verification of Stored Fingerprint (SUCCESS)

```
Fingerprint: 8f44e262d075fe6384bab049d909cde12f77b59d584a18fa64b00c38bd6e47c6

verify_on_chain_full() result:
  verified   : True
  timestamp  : 1788783684
  network    : Ethereum Sepolia
  message    : Content integrity verified — fingerprint matches on-chain record ✓
```

### Test 3 — Tamper Detection (SUCCESS)

A different fingerprint (representing modified/tampered content) was verified:

```
Tampered fingerprint: 5a7865acf599e1da75946ad3559d9eee29cbf1966fe6a02c076aa858da653f06

verify_on_chain_full() result:
  verified   : False
  timestamp  : 0
  message    : Integrity mismatch — fingerprint NOT found on-chain. Content may have been tampered with or was never uploaded. ✗
```

> These three tests prove the complete `fingerprint → upload → verify → tamper-detect` flow works against the real Sepolia contract.

---

## 4. Architecture

### Fingerprinting

```
image_path (local file)
    +
metadata (dict: url, platform, title, score, ...)
    │
    ▼  hashlib.sha256()
SHA-256(image_bytes || sorted_metadata_json)
    │
    ▼
64-char lowercase hex string
    │  bytes.fromhex()
    ▼
32 bytes  (= Solidity bytes32)
```

### ABI Architecture (Intentional Design Decision)

```
FaceChainVerify.sol
    │
    ├──────── compiled + deployed via Hardhat → Sepolia
    │
    └──────── backend/blockchain/abi.py
                        │  (embedded Python constant, no Hardhat runtime needed)
                        ▼
                   Web3.py contract object
                        │
                        ▼
                   Ethereum Sepolia
```

> **Why embedded ABI?** Eliminates Hardhat as a Python runtime dependency. Keeps the Python layer simple and portable. Works identically in tests and production.
>
> **Risk:** If `FaceChainVerify.sol` is modified, `abi.py` must be manually updated to match. See [Section 15](#15-do-not-change-without-coordination).

### Upload Flow

```
fingerprint (str, 64 hex chars)
    │  validate_fingerprint()
    │  fingerprint_to_bytes32()
    ▼
Web3.HTTPProvider(WEB3_PROVIDER_URL)
    │  assert chain_id == 11155111
    │  account = from_key(WALLET_PRIVATE_KEY)
    │  check balance > 0 ETH
    │  pre-check records() for duplicate
    ▼
contract.functions.store(fp_bytes32).build_transaction(...)
    │  sign_transaction(private_key)
    │  send_raw_transaction()
    │  wait_for_transaction_receipt(timeout=300s)
    ▼
dict: { success, transaction_hash, block_number, network, ... }
```

### Verification Flow (READ-ONLY, no gas)

```
fingerprint (str, 64 hex chars)
    │  validate_fingerprint()
    │  fingerprint_to_bytes32()
    ▼
Web3.HTTPProvider(WEB3_PROVIDER_URL)
    │  assert chain_id == 11155111
    │  no private key needed
    ▼
contract.functions.verify(fp_bytes32).call()
    │  returns (bool isValid, uint256 timestamp)
    ▼
dict: { verified, timestamp, fingerprint, network, message }
```

---

## 5. File Reference

```
backend/blockchain/
├── fingerprint.py        SHA-256 fingerprinting, validation, bytes32 conversion
├── uploader.py           Web3 upload to Sepolia (full transaction flow)
├── verifier.py           Read-only on-chain verification + tamper detection
├── abi.py                FaceChainVerify ABI embedded as Python constant
├── health_check.py       CLI connectivity/configuration health check
├── __init__.py           Package exports (compute_fingerprint, upload_to_chain, ...)
├── README.md             Technical documentation
├── HANDOVER.md           This file
└── contracts/
    ├── FaceChainVerify.sol       Solidity smart contract (do not modify casually)
    ├── hardhat.config.js         Hardhat network config (Sepolia + localhost)
    └── scripts/
        └── deploy.js             Hardhat deployment script
```

---

## 6. Function Reference

All functions are importable from `blockchain` (the package `__init__.py` exports them all).

```python
from blockchain import compute_fingerprint, upload_to_chain, verify_on_chain_full
```

---

### `compute_fingerprint(image_path, metadata) → str`

**File:** `blockchain/fingerprint.py`

**Purpose:** Compute a deterministic SHA-256 fingerprint of a discovered image + its post metadata.

**Signature:**
```python
def compute_fingerprint(image_path: str, metadata: dict) -> str:
```

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `image_path` | `str` | Absolute or relative path to the downloaded/discovered image file |
| `metadata` | `dict` | Post metadata dict — any JSON-serialisable key/value pairs |

**Output:** 64-character lowercase hex string (e.g. `"8f44e262d075fe63..."`).

**When to call:** After Member 2 has downloaded the matching post image and constructed the metadata dict.

**Important:**
- Metadata key order does **not** matter — keys are sorted before hashing.
- The **same** image bytes + **same** metadata always produce the **same** fingerprint.
- Changing **any** byte of the image or **any** metadata value produces a **different** fingerprint.
- `image_path` must exist on disk — pass a downloaded file, not a URL.

**Errors:**
- `FileNotFoundError` — `image_path` does not exist
- `TypeError` — `metadata` is not a dict
- `ValueError` — `metadata` contains non-JSON-serialisable values

---

### `validate_fingerprint(fingerprint) → None`

**File:** `blockchain/fingerprint.py`

**Purpose:** Assert that a string is a valid 64-char lowercase hex SHA-256 fingerprint. Raises `ValueError` if not.

**Signature:**
```python
def validate_fingerprint(fingerprint: str) -> None:
```

**When to call:** Optional — `upload_to_chain()` and `verify_on_chain_full()` call this internally. Only call directly if you need early validation.

---

### `fingerprint_to_bytes32(fingerprint) → bytes`

**File:** `blockchain/fingerprint.py`

**Purpose:** Convert a 64-char hex fingerprint to 32 bytes (Solidity `bytes32`).

**Signature:**
```python
def fingerprint_to_bytes32(fingerprint: str) -> bytes:
```

**When to call:** Normally you do **not** call this directly — `upload_to_chain()` and `verify_on_chain_full()` handle it internally.

---

### `upload_to_chain(fingerprint) → dict`

**File:** `blockchain/uploader.py`

**Purpose:** Submit the fingerprint to the `FaceChainVerify.store(bytes32)` function on Ethereum Sepolia. Requires `WALLET_PRIVATE_KEY` in `.env` (costs gas).

**Signature:**
```python
def upload_to_chain(fingerprint: str) -> dict:
```

**Input:** 64-char lowercase hex SHA-256 fingerprint string.

**Output dict:**

```python
# New record stored:
{
    "success": True,
    "already_exists": False,
    "transaction_hash": "0x812fa989...",   # 0x + 64 hex chars
    "block_number": 11654132,
    "contract_address": "0x7Fb9C62F...",
    "fingerprint": "8f44e262...",
    "network": "Ethereum Sepolia",
    "message": "Fingerprint stored successfully"
}

# Fingerprint already on-chain (no new TX sent):
{
    "success": True,
    "already_exists": True,
    "verified": True,
    "transaction_hash": None,
    "block_number": None,
    "contract_address": "0x7Fb9C62F...",
    "fingerprint": "8f44e262...",
    "network": "Ethereum Sepolia",
    "timestamp": 1788783684,
    "message": "Fingerprint already exists on-chain — no new transaction needed"
}
```

**When to call:** After `compute_fingerprint()`, before `verify_on_chain_full()`.

**Requires in `.env`:** `WEB3_PROVIDER_URL`, `WALLET_PRIVATE_KEY`, `CONTRACT_ADDRESS`.

**Errors:**
- `ValueError` — invalid fingerprint format
- `RuntimeError` — missing env vars / wrong network / zero balance / RPC down / TX failure

---

### `verify_on_chain_full(fingerprint) → dict`

**File:** `blockchain/verifier.py`

**Purpose:** Read-only check — queries `FaceChainVerify.verify(bytes32)` view function. No gas, no private key needed.

**Signature:**
```python
def verify_on_chain_full(fingerprint: str) -> dict:
```

**Input:** 64-char lowercase hex SHA-256 fingerprint string.

**Output dict:**

```python
# Found on-chain:
{
    "verified": True,
    "timestamp": 1788783684,       # Unix timestamp of original storage
    "fingerprint": "8f44e262...",
    "network": "Ethereum Sepolia",
    "message": "Content integrity verified — fingerprint matches on-chain record ✓"
}

# Not found (tampered or never uploaded):
{
    "verified": False,
    "timestamp": 0,
    "fingerprint": "5a7865ac...",
    "network": "Ethereum Sepolia",
    "message": "Integrity mismatch — fingerprint NOT found on-chain. Content may have been tampered with or was never uploaded. ✗"
}
```

**When to call:** After `upload_to_chain()` to confirm storage, or independently to verify any fingerprint.

**Requires in `.env`:** `WEB3_PROVIDER_URL`, `CONTRACT_ADDRESS` (no private key needed for reads).

**Backward-compatible tuple variant:**
```python
from blockchain import verify_on_chain
is_valid, timestamp = verify_on_chain(fingerprint)   # returns (bool, int)
```

**Errors:**
- `ValueError` — invalid fingerprint format
- `RuntimeError` — missing env vars / wrong network / RPC down

---

### `verify_on_chain(fingerprint) → Tuple[bool, int]`

**File:** `blockchain/verifier.py`

**Purpose:** Backward-compatible wrapper around `verify_on_chain_full()`. Returns `(True/False, timestamp)`.

**When to call:** Only if you need the simple tuple form. Prefer `verify_on_chain_full()` for new code.

---

### `run_health_check() → bool`

**File:** `blockchain/health_check.py`

**Purpose:** Prints a human-readable report of RPC connectivity, chain ID, wallet validity, balance, and contract reachability.

**Usage:**
```bash
cd backend/
python -m blockchain.health_check
```

**Returns:** `True` if all checks pass, `False` otherwise. Exit code `0` = healthy, `1` = unhealthy.

---

## 7. Smart Contract

**File:** `backend/blockchain/contracts/FaceChainVerify.sol`  
**Deployed at:** `0x7Fb9C62FCe11e34667BB04054026382643B08d34` on Ethereum Sepolia  
**Etherscan:** https://sepolia.etherscan.io/address/0x7Fb9C62FCe11e34667BB04054026382643B08d34

### Storage

```solidity
mapping(bytes32 => uint256) public records;
```

Maps each stored fingerprint (`bytes32`) to the Unix timestamp it was recorded. A timestamp of `0` means the fingerprint has never been stored.

### `store(bytes32 fingerprint)`

```solidity
function store(bytes32 fingerprint) external {
    require(records[fingerprint] == 0, "FaceChainVerify: fingerprint already recorded");
    records[fingerprint] = block.timestamp;
    emit FingerprintStored(fingerprint, msg.sender, block.timestamp);
}
```

- Writes the fingerprint + current block timestamp to `records`.
- Emits `FingerprintStored` event (indexed by fingerprint and recorder address).
- **Reverts** if the fingerprint has already been stored.
- Costs gas. Requires a funded wallet.

### `verify(bytes32 fingerprint)`

```solidity
function verify(bytes32 fingerprint) external view returns (bool isValid, uint256 timestamp) {
    timestamp = records[fingerprint];
    isValid = timestamp != 0;
}
```

- Free read — no gas, no transaction.
- Returns `(true, <timestamp>)` if stored, `(false, 0)` if not.

### What is stored on-chain

**Stored:** A 32-byte SHA-256 fingerprint + Unix timestamp.  
**NOT stored:** The original image, the post URL, any personal data, or any private key.

Storing only the fingerprint is appropriate because:
- Images are too large and costly to store on-chain
- A SHA-256 hash is a tamper-evident commitment to the content — if the content changes, the hash changes
- The timestamp proves *when* the commitment was made

### Duplicate Fingerprint Handling

The contract rejects duplicate fingerprints via `require`. `upload_to_chain()` pre-checks `records()` before attempting a transaction, so a duplicate returns `already_exists: True` gracefully without a failed transaction or crash.

---

## 8. Tamper Detection

The blockchain does **not** determine whether content is true, authentic, or real-world accurate. It verifies **fingerprint integrity** against a previously recorded fingerprint.

```
RECORD PHASE (one time)
─────────────────────────────────────────────
Original post image + metadata
        ↓  compute_fingerprint()
HASH_A = SHA-256(image_bytes || metadata_json)
        ↓  upload_to_chain(HASH_A)
on-chain: records[HASH_A] = block.timestamp

VERIFICATION PHASE (any time later)
─────────────────────────────────────────────
Content to verify (same or modified)
        ↓  compute_fingerprint()
HASH_B = SHA-256(current_image_bytes || current_metadata_json)
        ↓  verify_on_chain_full(HASH_B)

HASH_B == HASH_A  →  records[HASH_B] > 0  →  verified = True   ✓
HASH_B != HASH_A  →  records[HASH_B] == 0 →  verified = False  ✗
```

### Proven results (live Sepolia)

| Scenario | Fingerprint | `verified` | `timestamp` |
|----------|-------------|-----------|-------------|
| Original content | `8f44e262...` | `True` | `1788783684` |
| Tampered content | `5a7865ac...` | `False` | `0` |

### Important Distinction

The blockchain records a cryptographic commitment to the content that was discovered at a specific point in time. It **cannot**:
- Prove that the content was real or authentic at the time of recording
- Prove the real-world identity of any person in an image
- Verify the source or authenticity of a social media post itself

It **can**:
- Prove that the content being verified today matches exactly what was fingerprinted and recorded earlier
- Detect any byte-level modification to the content or metadata since recording

---

## 9. How to Integrate

### Responsibility Split

| Member | Task |
|--------|------|
| Member 1 | Face detection, face embedding, confidence score |
| Member 2 | Web/social media search, return best matching post (image URL/file + metadata) |
| **You (integrating)** | Connect Member 2's output → `compute_fingerprint()` → `upload_to_chain()` → `verify_on_chain_full()` |
| Frontend | Display pipeline stages, fingerprint, TX hash, verification result |

### What the Blockchain Module Needs from Member 2

`compute_fingerprint()` needs:
1. **A local file path** to the discovered post image (must be downloaded first)
2. **A metadata dict** — any JSON-serialisable key/value dict describing the post

The metadata dict is flexible. Use whatever Member 2's search returns:

```python
# Example metadata dict from Member 2's search result:
metadata = {
    "url": "https://instagram.com/p/abc123",
    "platform": "Instagram",
    "title": "Post caption or description",
    "score": 0.94,          # similarity score from Member 2
    # ... any other fields Member 2 returns
}
```

> **Important:** The blockchain module does not care which social media platform the post came from. Do not add Instagram/Twitter/Facebook-specific logic to the blockchain module. Map whatever Member 2 returns into the fingerprint call.

### Integration Code

This is the exact pattern that `backend/pipeline.py` already uses:

```python
from blockchain import compute_fingerprint, upload_to_chain, verify_on_chain_full

# --- After Member 2 returns the best matching post ---
best_match = matches[0]   # dict from search_by_image()
# best_match should have at minimum: url, platform, title

# 1. Member 2 must download the post image to a local path
image_path = "/path/to/downloaded/post_image.jpg"  # local file

# 2. Compute fingerprint
fingerprint = compute_fingerprint(image_path, best_match)
print(f"Fingerprint: {fingerprint}")

# 3. Upload to Sepolia
upload_result = upload_to_chain(fingerprint)

if upload_result["already_exists"]:
    print("Already on-chain — no new transaction.")
else:
    print(f"TX hash: {upload_result['transaction_hash']}")
    print(f"Block:   {upload_result['block_number']}")

# 4. Verify
verify_result = verify_on_chain_full(fingerprint)
print(f"Verified: {verify_result['verified']}")
print(f"Message:  {verify_result['message']}")

# 5. Return to pipeline / frontend
return {
    "fingerprint": fingerprint,
    "upload": upload_result,
    "verification": verify_result,
}
```

### Integration Rule

> The matching post **must** come from the real web/social search stage (Member 2). Do not hardcode a specific social media post. The demo must demonstrate a genuine search → match → fingerprint → verify flow.

---

## 10. Environment Setup

Create `backend/.env` (copy from `.env.example`, never commit):

```env
WEB3_PROVIDER_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
WALLET_PRIVATE_KEY=0x...your_private_key...
CONTRACT_ADDRESS=0x7Fb9C62FCe11e34667BB04054026382643B08d34
```

| Variable | Purpose | Notes |
|----------|---------|-------|
| `WEB3_PROVIDER_URL` | Sepolia RPC endpoint | Use Infura or Alchemy Sepolia URL |
| `WALLET_PRIVATE_KEY` | Signs transactions | Keep secret — never commit |
| `CONTRACT_ADDRESS` | Deployed contract | Already deployed: `0x7Fb9C62FCe11e34667BB04054026382643B08d34` |

> **`.env` must NEVER be committed to GitHub.** It is in `.gitignore`. Verify this before every `git push`.

Get a free Infura RPC key: https://infura.io  
Get a free Alchemy RPC key: https://alchemy.com  
Get free Sepolia test ETH: https://sepoliafaucet.com

---

## 11. Running Tests

### Unit Tests (no credentials, no network required)

```bash
cd backend/
pytest tests/test_blockchain.py -v
```

Expected: **40 passed**

Test categories covered:
- A. SHA-256 fingerprint generation (9 tests)
- B. bytes32 conversion (3 tests)
- C. Fingerprint validation (7 tests)
- D. Uploader with mocked Web3 (8 tests)
- E. Verifier with mocked Web3 (5 tests)
- F. Duplicate fingerprint handling (1 test)
- G. Configuration / env validation (2 tests)
- H. ABI structure validation (5 tests)

> Unit tests are **fully mocked**. Passing all 40 does NOT prove live blockchain transactions work.

### Blockchain Health Check

```bash
cd backend/
python -m blockchain.health_check
```

Run this first whenever you set up on a new machine or after changing `.env`.

### Live Sepolia Integration Tests

```bash
cd backend/
pytest tests/test_blockchain_live.py -v -s
```

Requires: valid `.env` with funded wallet + deployed contract.  
Tests **auto-skip** if env vars are missing.

Covers: upload, verify-after-upload, verify unknown fingerprint, duplicate handling, `verify_on_chain_full()` dict, tamper detection end-to-end.

### Manual Spot Check

```bash
cd backend/

# Compute a fingerprint
python -c "
from blockchain.fingerprint import compute_fingerprint
fp = compute_fingerprint('blockchain/test_image.txt', {'url': 'https://example.com', 'platform': 'test'})
print('Fingerprint:', fp)
"

# Verify an existing fingerprint
python -c "
from blockchain.verifier import verify_on_chain_full
result = verify_on_chain_full('8f44e262d075fe6384bab049d909cde12f77b59d584a18fa64b00c38bd6e47c6')
print(result)
"
```

---

## 12. End-to-End Demo Plan

The final submission must demonstrate this complete flow:

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Upload / input a face image | Image appears in UI |
| 2 | Face detection runs | Face detected, confidence score shown |
| 3 | Genuine web/social media search runs | Search in progress visible |
| 4 | Best matching post identified | Post URL + platform + title displayed |
| 5 | Post image downloaded locally | (internal step) |
| 6 | `compute_fingerprint(image_path, metadata)` | 64-char fingerprint displayed |
| 7 | `upload_to_chain(fingerprint)` | Sepolia TX submitted |
| 8 | Transaction confirmation | TX hash + block number displayed |
| 9 | `verify_on_chain_full(fingerprint)` | `verified: True` displayed |
| 10 | Display "Content Integrity Verified ✓" | Green verified result |
| 11 | Simulate tamper — modify the content or metadata | Different fingerprint computed |
| 12 | `verify_on_chain_full(tampered_fingerprint)` | `verified: False` |
| 13 | Display "Integrity Mismatch ✗" | Red mismatch result |

> Steps 11–13 are **mandatory** for the demo. Do not skip tamper detection.

---

## 13. Known Limitations

- **Only the fingerprint is stored on-chain**, not the image itself. Verification requires re-computing the fingerprint from the same original inputs.
- **Input sensitivity:** Changing any byte of the image or any metadata value produces a completely different fingerprint, which will fail verification.
- **Sepolia is a testnet.** Sepolia ETH has no monetary value. The same contract logic applies to mainnet but is not deployed there.
- **Transaction confirmation latency:** Sepolia typically confirms in 12–30 seconds, but can be slower under network congestion. `upload_to_chain()` waits up to 300 seconds.
- **Wallet needs Sepolia ETH.** Verification (read calls) are free. Uploads cost gas. Get test ETH from sepoliafaucet.com.
- **ABI must match the deployed contract.** If `FaceChainVerify.sol` is ever redeployed with changes, `abi.py` must be updated and the `CONTRACT_ADDRESS` in `.env` updated to the new address.
- **Blockchain cannot prove social post authenticity.** It proves that the fingerprint submitted now matches the fingerprint recorded earlier. It cannot verify that the original post was real, public, or unmanipulated before recording.
- **Duplicate fingerprints do not create a second transaction.** `upload_to_chain()` returns `already_exists: True` and the existing record remains valid.
- **Private key must remain local.** Never commit it. Never log it. If it leaks, generate a new wallet.

---

## 14. Troubleshooting

**Before modifying any code, check the error message and read this table.**

| Error | Likely cause | What to check / fix |
|-------|-------------|---------------------|
| `Missing required environment variables: WEB3_PROVIDER_URL` | `.env` not found or not loaded | Confirm `backend/.env` exists and contains the variable |
| `WALLET_PRIVATE_KEY is not a valid Ethereum private key` | Key format wrong | Must be `0x` + 64 hex chars; re-export from MetaMask |
| `Wallet ... has 0 ETH on Sepolia` | Empty wallet | Send Sepolia ETH from sepoliafaucet.com |
| `Wrong network! Expected Ethereum Sepolia (chain ID 11155111), but connected to chain ID ...` | RPC URL points to mainnet or another chain | Update `WEB3_PROVIDER_URL` to a Sepolia endpoint |
| `Cannot connect to Ethereum RPC` | Bad URL or service down | Check the Infura/Alchemy dashboard for the correct URL |
| `No contract found at 0x... on Ethereum Sepolia` | Wrong `CONTRACT_ADDRESS` or contract not deployed | Use `0x7Fb9C62FCe11e34667BB04054026382643B08d34` in `.env` |
| `Fingerprint already exists on-chain` | Normal behaviour — duplicate | `upload_to_chain()` returns `already_exists: True`; no action needed |
| `Fingerprint must be exactly 64 hex characters` | Wrong fingerprint format | Verify `compute_fingerprint()` output before passing to upload/verify |
| `Failed to call verify() on contract ...` | RPC/contract issue | Check network connection; run health check |
| `verify_on_chain_full()` returns `verified: False` | Fingerprint not on chain | Either never uploaded, or content was tampered (different fingerprint) |
| ABI mismatch errors from Web3 | `abi.py` doesn't match deployed contract | Check if contract was redeployed; update `abi.py` to match |
| Web3 transaction errors | Various | Read the exact error; check gas, nonce, chain ID; do not speculatively rewrite Web3 code |

---

## 15. DO NOT CHANGE WITHOUT COORDINATION

> ⚠️ The following items are stable shared interfaces. Changing them breaks other modules or the live deployment.

| Item | Risk if changed | Required action before changing |
|------|-----------------|--------------------------------|
| `FaceChainVerify.sol` | Breaks deployed contract interface; old fingerprints may become unverifiable | Coordinate with all members; redeploy; update `abi.py`; update `CONTRACT_ADDRESS` |
| Deployed contract address `0x7Fb9C62FCe11e34667BB04054026382643B08d34` | All existing on-chain records become inaccessible | Only change if contract is redeployed for a genuine reason |
| `backend/blockchain/abi.py` | Web3 calls will fail if ABI doesn't match deployed contract | Only update if `FaceChainVerify.sol` is changed AND redeployed |
| Web3 transaction flow in `uploader.py` | May break live Sepolia uploads | Only change if there is an observed, reproducible error — not speculatively |
| Fingerprint format (64-char lowercase hex SHA-256) | Breaks all existing on-chain records | Do not change the algorithm or encoding |
| `bytes32` conversion (`bytes.fromhex()`) | Breaks ABI encoding | Do not change |
| `.env` variable names (`WEB3_PROVIDER_URL`, `WALLET_PRIVATE_KEY`, `CONTRACT_ADDRESS`) | Breaks `_load_env()` in uploader and verifier | Coordinate if renaming is necessary |
| `upload_to_chain()` return dict structure | Breaks `pipeline.py` and any frontend consuming the result | Check all callers before adding/removing keys |
| `verify_on_chain_full()` return dict structure | Breaks `pipeline.py` and frontend | Check all callers before modifying |
| Web3.py version | May introduce API incompatibilities | Only change version if a real error demands it; do not downgrade speculatively |

---

## 16. Final Integration Checklist

Use this checklist when connecting the blockchain module to the rest of the pipeline:

- [ ] Pull latest repository changes (`git pull`)
- [ ] Confirm `backend/.env` exists locally with all three variables
- [ ] Run blockchain health check: `cd backend && python -m blockchain.health_check`
- [ ] Run unit tests: `cd backend && pytest tests/test_blockchain.py -v` (expect 40 passed)
- [ ] Understand the data structure Member 2's `search_by_image()` returns
- [ ] Ensure Member 2 downloads the matching post image to a local file before fingerprinting
- [ ] Call `compute_fingerprint(local_image_path, metadata_dict)` with Member 2's output
- [ ] Call `upload_to_chain(fingerprint)` and capture the result dict
- [ ] Log or display `result["transaction_hash"]` and `result["block_number"]` (if not `already_exists`)
- [ ] Call `verify_on_chain_full(fingerprint)` and capture the result dict
- [ ] Pass `verify_result["verified"]` and `verify_result["message"]` to the frontend/display layer
- [ ] Test the complete end-to-end flow with a real face image and real search result
- [ ] Test tamper detection: modify the image or metadata → recompute fingerprint → verify → confirm `verified: False`
- [ ] Confirm no hardcoded social media post is introduced into the pipeline
- [ ] Confirm no secrets appear in logs, output, or committed files
- [ ] Run `git status` before committing — confirm `.env` is not staged

---

*Document created by Member 3 — Blockchain & Verification Engineer.*  
*Last updated: 2026-09-07*
