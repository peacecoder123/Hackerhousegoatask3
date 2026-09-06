// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title FaceChainVerify
 * @notice Stores SHA-256 content fingerprints on-chain for tamper-evident verification.
 * @dev Part of the HH Goa 2026 Face Identification & Blockchain Verification pipeline.
 *
 * Member 3 owns this contract.
 */
contract FaceChainVerify {
    /// @notice Maps a SHA-256 fingerprint (as bytes32) to the Unix timestamp it was stored.
    mapping(bytes32 => uint256) public records;

    /// @notice Emitted when a new fingerprint is stored.
    event FingerprintStored(bytes32 indexed fingerprint, address indexed recorder, uint256 timestamp);

    /**
     * @notice Store a content fingerprint on-chain.
     * @param fingerprint The SHA-256 hash of (image bytes + metadata), as bytes32.
     */
    function store(bytes32 fingerprint) external {
        require(records[fingerprint] == 0, "FaceChainVerify: fingerprint already recorded");
        records[fingerprint] = block.timestamp;
        emit FingerprintStored(fingerprint, msg.sender, block.timestamp);
    }

    /**
     * @notice Verify whether a fingerprint has been recorded on-chain.
     * @param fingerprint The SHA-256 hash to check.
     * @return isValid True if the fingerprint exists on-chain.
     * @return timestamp Unix timestamp of when it was recorded (0 if not found).
     */
    function verify(bytes32 fingerprint) external view returns (bool isValid, uint256 timestamp) {
        timestamp = records[fingerprint];
        isValid = timestamp != 0;
    }
}
