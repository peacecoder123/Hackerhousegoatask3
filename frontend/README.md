# `frontend/` — Next.js Demo UI

This folder contains the **Next.js 16 frontend** for the FaceChain Verify pipeline.  
It provides an interactive, browser-based walkthrough of the full pipeline.

## Tech Stack

| Tool | Version |
|------|---------|
| Next.js | 16.x |
| React | 19.x |
| TypeScript | 5.7 |
| Tailwind CSS | v4 |
| lucide-react | icons |

## Directory Structure

```
frontend/
├── app/
│   ├── globals.css     # Global styles & design tokens
│   ├── layout.tsx      # Root layout (Google Fonts, metadata)
│   └── page.tsx        # Main pipeline UI (all stages)
├── components/
│   └── ui/             # shadcn/ui base components
├── lib/
│   └── utils.ts        # cn() utility
├── public/             # Static assets
├── next.config.mjs
├── package.json
└── tsconfig.json
```

## Getting Started

```bash
cd frontend/

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Pipeline Stages (Demo Mode)

| Stage | Description |
|-------|-------------|
| Upload | Drop a face image (JPG/PNG/WEBP) |
| Analysis | Face detected, confidence shown |
| Searching | Animated web search simulation |
| Results | Ranked candidate matches |
| Fingerprint | SHA-256 hash generated |
| Recording | Blockchain transaction submitted |
| Verified ✓ | Match confirmed |
| Mismatch ✗ | Tampered content detected |

> **Note**: The UI is in DEMO MODE with mock data. Connect to the `backend/` scripts to run the real pipeline.
