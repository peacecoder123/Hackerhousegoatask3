# `contracts/` — Solidity Smart Contract

**Owner: Member 3 (Blockchain & Verification Engineer)**

## Overview

This folder contains the Solidity smart contract that stores and verifies SHA-256 fingerprints on the Ethereum Sepolia testnet.

## Files

| File | Purpose |
|------|---------|
| `FaceChainVerify.sol` | Main Solidity contract |
| `FaceChainVerify.json` | Compiled ABI (generated after compile) |
| `hardhat.config.js` | Hardhat network configuration |
| `scripts/deploy.js` | Deployment script |
| `README.md` | This file |

## How to Compile & Deploy

```bash
# Install Hardhat in this directory
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox dotenv

# Compile
npx hardhat compile

# Deploy to Sepolia
npx hardhat run scripts/deploy.js --network sepolia
```

The deployed contract address will be printed. Copy it into your root `.env` file:

```env
CONTRACT_ADDRESS=0x...
```

## Contract Interface

| Function | Description |
|---------|-------------|
| `store(bytes32 fingerprint)` | Record a fingerprint on-chain (costs gas) |
| `verify(bytes32 fingerprint)` | Read whether a fingerprint was stored (free) |

## Verify on Etherscan

After deploying, verify the contract source on [sepolia.etherscan.io](https://sepolia.etherscan.io):

```bash
npx hardhat verify --network sepolia <CONTRACT_ADDRESS>
```
