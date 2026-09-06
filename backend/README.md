# `backend/` — Python Pipeline

This directory contains the **entire Python backend** for the FaceChain Verify pipeline.

## Subdirectory Structure

```
backend/
├── face_detection/     # Step 1: Face detection & embedding generation
├── web_search/         # Step 2: Reverse image search & social post retrieval
├── blockchain/         # Step 3: Fingerprint, upload, and re-verify on-chain
├── utils/              # Shared helpers (hashing, logging, config)
├── tests/              # Unit & integration tests
├── pipeline.py         # Entrypoint — runs all three steps in sequence
└── requirements.txt    # Python dependencies
```

## Quick Start

```bash
pip install -r requirements.txt
python pipeline.py --image path/to/face.jpg
```

## Environment Variables

Create a `.env` file in this directory (never commit it):

```env
SERPAPI_KEY=
WEB3_PROVIDER_URL=
WALLET_PRIVATE_KEY=
CONTRACT_ADDRESS=
```
