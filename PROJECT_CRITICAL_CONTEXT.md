# PROJECT_CRITICAL_CONTEXT.md

> **READ THIS FIRST before modifying any file in this repository.**
> This document is permanent engineering context for all team members and Antigravity agents.
> Its purpose is to prevent one teammate or agent from accidentally breaking another's work.

---

## PROJECT: FACECHAIN VERIFY — HACKERHOUSE GOA 2026 TASK 3

### Core Required Pipeline

```
Face Scan / Input Image
        ↓
Face Detection + Face Embedding
        ↓
Genuine Web / Social Media Search
        ↓
Matching Social Media / Web Post
        ↓
Content Fingerprint (SHA-256)
        ↓
Ethereum Sepolia Blockchain
        ↓
On-chain Verification
        ↓
Tamper Detection
```

The final system must demonstrate this pipeline **end-to-end**.

---

## Repository Structure

```
Hackerhousegoatask3/
├── frontend/                        ← Next.js 16 demo UI (Member 1 UI / shared)
│   └── app/
│       ├── globals.css
│       ├── layout.tsx
│       └── page.tsx
├── backend/
│   ├── face_detection/              ← Member 1: Face ID & embedding
│   ├── web_search/                  ← Member 2: Web/social search
│   ├── blockchain/                  ← Member 3: Fingerprint, upload, verify
│   │   ├── fingerprint.py
│   │   ├── uploader.py
│   │   ├── verifier.py
│   │   ├── abi.py
│   │   ├── health_check.py
│   │   └── contracts/
│   │       ├── FaceChainVerify.sol
│   │       ├── hardhat.config.js
│   │       └── scripts/deploy.js
│   ├── utils/                       ← Shared helpers (config, logger)
│   ├── tests/                       ← Unit + live integration tests
│   ├── pipeline.py                  ← Main entrypoint — orchestrates all 3 steps
│   └── requirements.txt
├── .env.example                     ← Template — NEVER commit .env
├── .gitignore
├── README.md
└── PROJECT_CRITICAL_CONTEXT.md      ← This file
```

---

## Team Module Boundaries

| Module | Owner | Primary Files |
|--------|-------|---------------|
| Face Identification | **Member 1** | `backend/face_detection/detector.py` |
| Web / Social Search | **Member 2** | `backend/web_search/searcher.py`, `scorer.py` |
| Blockchain | **Member 3** | `backend/blockchain/` (all files) |
| Frontend UI | Shared | `frontend/app/page.tsx`, `globals.css`, `layout.tsx` |
| Pipeline Orchestration | Shared | `backend/pipeline.py` |

### General Rules for ALL Agents and Team Members

> [!IMPORTANT]
> Before modifying **any** file, read it first. Identify which module/member owns it. Do not rewrite another member's module simply because you prefer a different approach.

1. Make the **minimum safe change** required.
2. Do **not** break existing interfaces between modules.
3. Run the relevant tests after your change.
4. Check that **other modules were not broken**.
5. Do **not** modify frontend files while working on backend blockchain tasks, and vice versa.

---

## Blockchain Module — Critical Context

**Location:** `backend/blockchain/`

**Network:** Ethereum Sepolia Testnet  
**Chain ID:** `11155111`

### What the Blockchain Stores

> [!IMPORTANT]
> The project does **NOT** store images on Ethereum. Only the SHA-256 fingerprint (32 bytes) is stored on-chain.

```
Discovered Content (image bytes + metadata)
        ↓
Deterministic SHA-256 Fingerprint
        ↓
bytes32
        ↓
FaceChainVerify.store(bytes32)
        ↓
Ethereum Sepolia
        ↓
records[fingerprint] = block.timestamp
```

**Purpose:** Prove that content being verified today has the same cryptographic fingerprint as content recorded previously. This proves **content integrity**, not real-world identity.

---

## Critical Point 1 — The ABI

The Python blockchain code uses an **embedded ABI** in `backend/blockchain/abi.py`.

```
FaceChainVerify.sol
        │
        ├──────── deployed to Sepolia (via hardhat deploy.js)
        │
        └──────── backend/blockchain/abi.py  ← Python constant, manually maintained
                              │
                              ↓
                         Web3.py → Sepolia
```

> [!CAUTION]
> **If `FaceChainVerify.sol` is modified, `backend/blockchain/abi.py` MUST be updated to match.**
> The embedded ABI does NOT auto-update when Solidity changes.

**Before modifying the Solidity contract:**
1. Inspect the existing ABI in `abi.py`.
2. Understand all existing contract functions.
3. Make the minimum required contract change.
4. Update `abi.py` to match the new ABI exactly.
5. Verify all Python/Web3 calls still match the deployed contract.

**Do NOT introduce into the contract:**
- NFTs or ERC-20 tokens
- DAOs or governance
- Multiple contracts
- IPFS dependencies
- Tokenomics
- Zero-knowledge proofs
- Wallet login

The existing simple `store` / `verify` architecture is sufficient for this hackathon.

---

## Critical Point 2 — Web3.py Version

- **`requirements.txt` specifies:** `web3 >= 7.0.0`
- **Currently installed:** `web3 8.0.0`

> [!WARNING]
> Do **not** downgrade Web3.py or preemptively rewrite blockchain code for a different version.
> Only make version-related changes if an **actual error** is observed during a live Sepolia test.

If a Web3 error occurs involving `build_transaction`, `sign_transaction`, `send_raw_transaction`, `raw_transaction`, nonce, or gas estimation — inspect the actual error and fix based on the installed version. Do not blindly copy old tutorials.

---

## Blockchain Fingerprinting

```
Image Bytes (chunked read)
        +
Canonical Metadata (json.dumps, sort_keys=True)
        ↓
SHA-256
        ↓
64 lowercase hexadecimal characters
        ↓
bytes.fromhex() → bytes32
        ↓
Blockchain
```

- The fingerprint is **always exactly 64 lowercase hex characters**.
- The same content + same canonical metadata **always produces the same fingerprint**.
- Metadata key order does **not** affect the fingerprint (keys are sorted before hashing).
- Do **not** introduce additional hashing algorithms. SHA-256 is sufficient.

---

## Smart Contract — `FaceChainVerify.sol`

**Core behaviour:**
- `store(bytes32 fingerprint)` — writes fingerprint → timestamp on-chain (costs gas)
- `verify(bytes32 fingerprint)` — returns `(bool isValid, uint256 timestamp)` (free read)
- `records(bytes32)` — public mapping getter (free read)

**Duplicate protection:** The contract `require`s that a fingerprint has not been stored before. This is intentional. The Python layer (`uploader.py`) handles duplicates gracefully by pre-checking `records()` before sending a transaction, avoiding an unexplained revert.

> [!NOTE]
> Do not remove the duplicate protection from the contract. Handle it at the application layer instead.

---

## Blockchain Upload Flow

```
SHA-256 fingerprint (64 hex chars)
        ↓  validate_fingerprint()
Validate fingerprint format
        ↓  fingerprint_to_bytes32()
Convert to bytes32
        ↓  Web3.HTTPProvider
Connect to Sepolia RPC
        ↓  w3.eth.chain_id
Assert Chain ID == 11155111
        ↓  abi.py
Load embedded ABI
        ↓  w3.eth.contract()
Create contract object
        ↓  w3.eth.get_balance()
Check wallet balance > 0
        ↓  contract.functions.records().call()
Pre-check for duplicate
        ↓  contract.functions.store().build_transaction()
Build transaction
        ↓  w3.eth.account.sign_transaction()
Sign transaction
        ↓  w3.eth.send_raw_transaction()
Broadcast to Sepolia
        ↓  w3.eth.wait_for_transaction_receipt()
Wait for confirmation
        ↓
Return structured dict (tx_hash, block_number, network, fingerprint, ...)
```

---

## Blockchain Verification Flow

> [!IMPORTANT]
> Verification is a **READ operation**. It must NOT send a transaction or spend gas.

```
Content to verify (image + metadata)
        ↓  compute_fingerprint()
Current SHA-256 fingerprint
        ↓  fingerprint_to_bytes32()
Convert to bytes32
        ↓  contract.functions.verify().call()
Query on-chain record
        ↓
(isValid=True,  timestamp=T)  →  CONTENT INTEGRITY VERIFIED ✓
(isValid=False, timestamp=0)  →  INTEGRITY MISMATCH / CONTENT CHANGED ✗
```

---

## Tamper Detection — Mandatory Demo

> [!IMPORTANT]
> This test is **mandatory** for final submission validation.

```
STEP 1 — RECORD ORIGINAL
  Original Image → SHA-256 → HASH_A → store on blockchain

STEP 2 — VERIFY ORIGINAL (should pass)
  Same Image → SHA-256 → HASH_A → verify() → HASH_A == HASH_A → VERIFIED ✓

STEP 3 — TAMPER AND VERIFY (must detect tampering)
  Modified Image → SHA-256 → HASH_B → verify() → HASH_B ≠ HASH_A → MISMATCH ✗
```

Do **not** only test `upload → verify same fingerprint`.  
You **must** also test `original → record → modify → verify → mismatch`.

---

## Secrets and Security

> [!CAUTION]
> **NEVER commit secrets to the repository under any circumstances.**

- `WALLET_PRIVATE_KEY` — stays in `.env` only, never in source code
- `WEB3_PROVIDER_URL` — stays in `.env` only
- `CONTRACT_ADDRESS` — safe to commit (it is a public address)
- `SERPAPI_KEY` — stays in `.env` only

**Rules:**
- Never print the private key in logs, error messages, tests, or UI
- Never hardcode credentials in any source file
- `.env` is in `.gitignore` — verify this before every commit
- Use `.env.example` for documentation (with empty values only)

---

## Required Environment Variables

```env
# backend/blockchain — required for upload
WEB3_PROVIDER_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
WALLET_PRIVATE_KEY=0x...

# backend/blockchain — required for upload + verify
CONTRACT_ADDRESS=0x...

# backend/web_search — required for Member 2
SERPAPI_KEY=...

# optional
ETHERSCAN_API_KEY=...
```

Copy `.env.example` → `.env` and fill in your credentials. Never commit `.env`.

---

## Current Test Status

| Test Type | Count | Status |
|-----------|-------|--------|
| Unit tests (mocked, no credentials) | 40 | ✅ All passing |
| Live Sepolia integration tests | 6 | ⏳ Pending credentials + deployed contract |

> [!WARNING]
> **40/40 unit tests passing does NOT mean live Sepolia is verified.**
> The blockchain module cannot be declared complete until a real Sepolia transaction succeeds and tamper detection is demonstrated live.

**To run unit tests (no credentials needed):**
```bash
cd backend/
pytest tests/test_blockchain.py -v
```

**To run live Sepolia tests (requires `.env` + deployed contract):**
```bash
cd backend/
pytest tests/test_blockchain_live.py -v -s
```

**To run blockchain health check:**
```bash
cd backend/
python -m blockchain.health_check
```

---

## Contract Deployment (One-Time Setup — Member 3)

```bash
cd backend/blockchain/contracts/
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox dotenv
npx hardhat compile
npx hardhat run scripts/deploy.js --network sepolia
# Copy the printed CONTRACT_ADDRESS into .env
```

Get free Sepolia ETH: https://sepoliafaucet.com  
Get a free Infura key: https://infura.io  
Get a free Alchemy key: https://alchemy.com

---

## Pipeline Integration — `backend/pipeline.py`

The pipeline orchestrates all three modules in sequence:

```python
encode_face(image_path)          # Member 1
search_by_image(image_path)      # Member 2
compute_fingerprint(image, meta) # Member 3
upload_to_chain(fingerprint)     # Member 3  → returns dict
verify_on_chain_full(fingerprint) # Member 3 → returns dict
```

> [!IMPORTANT]
> `upload_to_chain()` returns a **dict**, not a plain string.
> `verify_on_chain()` returns a **(bool, int) tuple** (backward compat).
> `verify_on_chain_full()` returns a **dict** with richer information.
>
> Before changing any of these signatures, check all callers in `pipeline.py`.

---

## Live Validation Checklist — Required Before Final Submission

- [ ] RPC connection works
- [ ] Chain ID confirms as `11155111` (Sepolia)
- [ ] Wallet connects successfully
- [ ] Wallet has Sepolia ETH
- [ ] Contract is deployed at `CONTRACT_ADDRESS`
- [ ] Contract bytecode is reachable
- [ ] Real fingerprint upload succeeds (transaction hash obtained)
- [ ] Real transaction receipt confirmed
- [ ] Real on-chain verification returns `(True, timestamp)`
- [ ] Tampered content produces `(False, 0)` — mismatch confirmed
- [ ] No private key appears anywhere in logs or output

---

## Rules for All Future Antigravity Agents

> [!IMPORTANT]
> Before making **any** change to this repository:
>
> 1. Read `PROJECT_CRITICAL_CONTEXT.md` (this file).
> 2. Inspect the relevant existing code — do not assume its contents.
> 3. Identify module ownership from the table above.
> 4. Understand the existing interfaces before touching them.
> 5. Verify the requested change is actually necessary.
> 6. Make the **smallest safe change**.
> 7. Run the relevant tests.
> 8. Confirm other modules were not broken.

**Do NOT:**
- Blindly rewrite files that already have working implementations
- Replace working architecture because a different style is preferred
- Change dependencies without a concrete observed reason
- Modify `FaceChainVerify.sol` without updating `abi.py`
- Change Web3.py version without evidence of incompatibility
- Remove tests because they fail — fix the root cause instead
- Hardcode credentials or API keys anywhere in source code
- Commit `.env`
- Modify frontend code while working on backend blockchain tasks
- Claim live blockchain functionality without a real Sepolia test receipt

---

## Before Final Submission — Full Demo Must Show

```
Face Scan (uploaded image)
        ↓
Face detected + embedding generated
        ↓
Real web/social media search performed
        ↓
Matching post identified
        ↓
SHA-256 fingerprint computed
        ↓
Ethereum Sepolia transaction submitted
        ↓
Transaction hash displayed
        ↓
On-chain verification: VERIFIED ✓
        ↓
Content modified / tampered
        ↓
Different SHA-256 computed
        ↓
On-chain verification: INTEGRITY MISMATCH ✗
```

The submission must include:
- Working GitHub repository link
- README covering what the project does, how to run it, which blockchain was used, and known limitations
- Screen recording of the full pipeline working end-to-end
- No committed secrets

Submission form: https://forms.gle/oZbQGuwiNeHVcHWo8  
**No resubmissions are allowed.**

---

## Final Instruction

> This document is the authoritative engineering context for this project.
>
> **Read `PROJECT_CRITICAL_CONTEXT.md` before modifying anything.**
>
> If a requested change conflicts with the rules in this document, explain the conflict before making a destructive architectural change.
>
> The goal is not maximum complexity. The goal is:
>
> **RELIABLE · DEMONSTRABLE · SECURE · MINIMAL · END-TO-END WORKING**
>
> — FaceChain Verify, HackerHouse Goa 2026
