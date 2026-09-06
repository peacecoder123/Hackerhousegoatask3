# `blockchain/` — Fingerprinting, On-Chain Upload & Verification

**Owner: Member 3 (Blockchain & Verification Engineer)**

## Responsibility

This module is the third and final step in the pipeline:

1. **Fingerprint**: Compute a SHA-256 hash of the discovered content (image bytes + metadata)
2. **Upload**: Submit the fingerprint to a Solidity smart contract on Ethereum Sepolia
3. **Verify**: Re-compute the hash and compare against the on-chain record

## Files

| File | Purpose |
|------|---------|
| `fingerprint.py` | SHA-256 content hashing |
| `uploader.py` | Ethereum transaction to store hash on-chain |
| `verifier.py` | Re-hash content and compare against chain |
| `contracts/` | Solidity smart contract source + ABI |
| `README.md` | This file |

## Smart Contract

The contract stores fingerprints like this:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FaceChainVerify {
    mapping(bytes32 => uint256) public records; // fingerprint → timestamp

    function store(bytes32 fingerprint) external {
        records[fingerprint] = block.timestamp;
    }

    function verify(bytes32 fingerprint) external view returns (bool, uint256) {
        uint256 ts = records[fingerprint];
        return (ts != 0, ts);
    }
}
```

## Deploy to Sepolia

```bash
# Using Hardhat
cd contracts/
npm install
npx hardhat run scripts/deploy.js --network sepolia
```

Save the deployed `CONTRACT_ADDRESS` in your `.env`.

## Usage

```python
from blockchain.fingerprint import compute_fingerprint
from blockchain.uploader import upload_to_chain
from blockchain.verifier import verify_on_chain

# 1. Fingerprint
fp = compute_fingerprint(image_path="face.jpg", metadata={"url": "...", "platform": "Instagram"})

# 2. Upload
tx_hash = upload_to_chain(fingerprint=fp)

# 3. Verify later
is_valid, timestamp = verify_on_chain(fingerprint=fp)
```

## Environment Variables Required

```env
WEB3_PROVIDER_URL=https://sepolia.infura.io/v3/your_project_id
WALLET_PRIVATE_KEY=your_wallet_private_key
CONTRACT_ADDRESS=0xYourDeployedContractAddress
```

## Known Limitations

- Sepolia confirmations take 10–30 seconds
- Private key must have test ETH (from [sepoliafaucet.com](https://sepoliafaucet.com))
- ABI must match the deployed contract version exactly
