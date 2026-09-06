# FaceChain Verify 🔗

> **HH Goa 2026 — Shortlisting Task 3: Face Identification & Blockchain Verification**

A full end-to-end pipeline that takes a face scan as input, discovers matching content on the web/social media, and creates a tamper-evident blockchain record — then lets you re-verify it.

---

## 📁 Repository Structure

```
Hackerhousegoatask3/
├── frontend/                    # Next.js 16 demo UI
│   ├── app/
│   │   ├── globals.css          # Global styles & design tokens (Inter, Tailwind v4)
│   │   ├── layout.tsx           # Root layout + Google Fonts
│   │   └── page.tsx             # Full pipeline UI (8 stages)
│   ├── components/ui/           # shadcn/ui base components
│   ├── lib/utils.ts             # Utility helpers
│   ├── package.json
│   └── README.md
│
├── backend/                     # Python pipeline scripts
│   ├── face_detection/          # Step 1: Face detection & embedding (Member 1)
│   │   ├── detector.py
│   │   └── README.md
│   ├── web_search/              # Step 2: Reverse image search (Member 2)
│   │   ├── searcher.py
│   │   ├── scorer.py
│   │   └── README.md
│   ├── blockchain/              # Step 3: Fingerprint, upload, verify (Member 3)
│   │   ├── fingerprint.py       # SHA-256 hashing (fully implemented)
│   │   ├── uploader.py          # Web3.py on-chain upload stub
│   │   ├── verifier.py          # On-chain re-verification stub
│   │   ├── contracts/
│   │   │   ├── FaceChainVerify.sol    # Solidity smart contract
│   │   │   ├── hardhat.config.js
│   │   │   ├── scripts/deploy.js
│   │   │   └── README.md
│   │   └── README.md
│   ├── utils/                   # Shared helpers (config, logger)
│   ├── tests/                   # Unit & integration tests
│   ├── pipeline.py              # Main entrypoint (runs all 3 steps)
│   ├── requirements.txt
│   └── README.md
│
├── .gitignore
└── README.md                    # This file
```

---

## 📌 Pipeline Overview

```
Face scan (upload)
      │
      ▼
[Step 1 — Member 1] Face Detection & Encoding
  detect face → generate 128-d embedding
      │
      ▼
[Step 2 — Member 2] Web / Social Media Search
  reverse image search → find matching post → rank candidates
      │
      ▼
[Step 3 — Member 3] Blockchain Verification
  SHA-256 fingerprint → upload to Sepolia → re-verify on-chain
```

---

## 🚀 How to Run

### Frontend (Demo UI)

```bash
cd frontend/
npm install
npm run dev
# Open http://localhost:3000
```

### Backend Pipeline

```bash
cd backend/
pip install -r requirements.txt

# Copy and fill in your credentials
cp ../.env.example .env   # (or create .env manually — see below)

# Run the full pipeline
python pipeline.py --image path/to/face.jpg

# Re-verify only (without re-running detection & search)
python pipeline.py --verify-only <64-char-fingerprint>
```

### Environment Variables

Create a `.env` file in the project root (never commit this):

```env
SERPAPI_KEY=your_serpapi_key
WEB3_PROVIDER_URL=https://sepolia.infura.io/v3/your_project_id
WALLET_PRIVATE_KEY=your_wallet_private_key
CONTRACT_ADDRESS=0xYourDeployedContractAddress
ETHERSCAN_API_KEY=your_etherscan_api_key   # optional, for contract verification
```

### Smart Contract (Ethereum Sepolia)

```bash
cd backend/blockchain/contracts/
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox dotenv

# Compile
npx hardhat compile

# Deploy to Sepolia
npx hardhat run scripts/deploy.js --network sepolia

# Copy the printed CONTRACT_ADDRESS into your .env
```

Get free Sepolia test ETH from [sepoliafaucet.com](https://sepoliafaucet.com).

---

## ⛓️ Blockchain Used

**Ethereum Sepolia Testnet** (Chain ID: 11155111)

- Smart contract: `FaceChainVerify.sol` — stores SHA-256 fingerprints on-chain
- Tool: [web3.py](https://web3py.readthedocs.io/) + [Hardhat](https://hardhat.org/)
- Explorer: [sepolia.etherscan.io](https://sepolia.etherscan.io)
- Verification: re-hash content, call `contract.verify(fingerprint)` — any mismatch = tampered

---

## 👥 3-Member Team Distribution

Equal weightage — each member owns one complete vertical slice:

| Member | Role | Owns |
|--------|------|------|
| **Member 1** | Face Identification Engineer | `backend/face_detection/` — detect & encode faces (face-api.js / DeepFace), generate embeddings, confidence scores |
| **Member 2** | Web / Social Media Search Engineer | `backend/web_search/` — SerpAPI reverse image search, social post scraping, similarity scoring & ranking |
| **Member 3** | Blockchain & Verification Engineer | `backend/blockchain/` — smart contract (Solidity), web3.py upload, on-chain verification, demo recording & README |

All three members collaborate on: `backend/pipeline.py`, `frontend/`, and PR reviews.

---

## ⚠️ Known Limitations

- **Demo UI is DEMO MODE** — the frontend uses mock data. Wire up `backend/pipeline.py` for a live run.
- **SerpAPI rate limits** — free tier: ~100 searches/month. Private/deleted posts won't appear.
- **Face accuracy** — low-resolution or occluded faces may fail detection.
- **Sepolia confirmations** — transactions take 10–30 seconds; network may be congested.
- **No resubmissions** — per competition rules, submit only when final.

---

## 📹 Screen Recording

Record the pipeline end-to-end:

1. Upload a face image → face detected
2. Web search runs → matching social post found
3. SHA-256 fingerprint generated
4. Blockchain TX confirmed (TX hash visible)
5. Re-verification → **"MATCH — VERIFIED"** ✓
6. Simulate tamper → **"CONTENT CHANGED"** ✗

Upload to YouTube (unlisted), Google Drive, or Loom and include the link in your submission.

---

## 📬 Submission

[HH Goa 2026 Submission Form →](https://forms.gle/oZbQGuwiNeHVcHWo8)

> No resubmissions — submit only when your build is final.

---

## 📄 License

MIT
