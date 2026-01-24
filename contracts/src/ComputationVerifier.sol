// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.0;

/**
 * @title ComputationVerifier
 * @dev Verifier for FHE computation proofs and prediction audit trail.
 *
 * This contract provides:
 * - Registration of computation results
 * - Verification of prediction outputs
 * - Audit trail for compliance (GDPR/LGPD)
 */
contract ComputationVerifier {
    // ============ Structs ============

    struct Computation {
        bytes32 modelId;
        bytes32 inputHash;      // Hash of encrypted input
        bytes32 outputHash;     // Hash of encrypted output
        bytes32 proofHash;      // Optional ZK proof hash
        address executor;
        uint256 timestamp;
        bool verified;
    }

    struct PredictionBatch {
        bytes32 modelId;
        bytes32[] inputHashes;
        bytes32[] outputHashes;
        uint256 batchSize;
        uint256 timestamp;
        address executor;
    }

    // ============ State Variables ============

    // Computation ID => Computation
    mapping(bytes32 => Computation) public computations;

    // Model ID => computation count
    mapping(bytes32 => uint256) public modelComputationCount;

    // Batch ID => PredictionBatch
    mapping(bytes32 => PredictionBatch) public batches;

    // Executor => computation IDs
    mapping(address => bytes32[]) public executorComputations;

    // Trusted verifiers
    mapping(address => bool) public trustedVerifiers;

    // Contract owner
    address public owner;

    // ============ Events ============

    event ComputationRegistered(
        bytes32 indexed computationId,
        bytes32 indexed modelId,
        bytes32 inputHash,
        bytes32 outputHash,
        address executor
    );

    event ComputationVerified(
        bytes32 indexed computationId,
        address indexed verifier,
        bool success
    );

    event BatchRegistered(
        bytes32 indexed batchId,
        bytes32 indexed modelId,
        uint256 batchSize,
        address executor
    );

    event VerifierAdded(address indexed verifier);
    event VerifierRemoved(address indexed verifier);

    // ============ Modifiers ============

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyTrustedVerifier() {
        require(trustedVerifiers[msg.sender] || msg.sender == owner, "Not trusted verifier");
        _;
    }

    // ============ Constructor ============

    constructor() {
        owner = msg.sender;
        trustedVerifiers[msg.sender] = true;
    }

    // ============ External Functions ============

    /**
     * @dev Register a single computation result.
     * @param modelId Model used for computation
     * @param inputHash Hash of encrypted input data
     * @param outputHash Hash of encrypted output (prediction)
     * @param proofHash Optional hash of computation proof
     * @return computationId Unique identifier for this computation
     */
    function registerComputation(
        bytes32 modelId,
        bytes32 inputHash,
        bytes32 outputHash,
        bytes32 proofHash
    ) external returns (bytes32 computationId) {
        computationId = keccak256(
            abi.encodePacked(
                modelId,
                inputHash,
                outputHash,
                msg.sender,
                block.timestamp,
                modelComputationCount[modelId]
            )
        );

        computations[computationId] = Computation({
            modelId: modelId,
            inputHash: inputHash,
            outputHash: outputHash,
            proofHash: proofHash,
            executor: msg.sender,
            timestamp: block.timestamp,
            verified: false
        });

        modelComputationCount[modelId]++;
        executorComputations[msg.sender].push(computationId);

        emit ComputationRegistered(
            computationId,
            modelId,
            inputHash,
            outputHash,
            msg.sender
        );

        return computationId;
    }

    /**
     * @dev Register a batch of predictions.
     * @param modelId Model used for predictions
     * @param inputHashes Array of input hashes
     * @param outputHashes Array of output hashes
     * @return batchId Unique identifier for this batch
     */
    function registerBatch(
        bytes32 modelId,
        bytes32[] calldata inputHashes,
        bytes32[] calldata outputHashes
    ) external returns (bytes32 batchId) {
        require(inputHashes.length == outputHashes.length, "Array length mismatch");
        require(inputHashes.length > 0, "Empty batch");

        batchId = keccak256(
            abi.encodePacked(
                modelId,
                inputHashes[0],
                msg.sender,
                block.timestamp
            )
        );

        batches[batchId] = PredictionBatch({
            modelId: modelId,
            inputHashes: inputHashes,
            outputHashes: outputHashes,
            batchSize: inputHashes.length,
            timestamp: block.timestamp,
            executor: msg.sender
        });

        modelComputationCount[modelId] += inputHashes.length;

        emit BatchRegistered(batchId, modelId, inputHashes.length, msg.sender);

        return batchId;
    }

    /**
     * @dev Verify a computation (by trusted verifier).
     * @param computationId Computation to verify
     * @param success Whether verification passed
     */
    function verifyComputation(
        bytes32 computationId,
        bool success
    ) external onlyTrustedVerifier {
        require(computations[computationId].timestamp != 0, "Computation not found");

        computations[computationId].verified = success;

        emit ComputationVerified(computationId, msg.sender, success);
    }

    /**
     * @dev Add a trusted verifier.
     * @param verifier Address to add
     */
    function addVerifier(address verifier) external onlyOwner {
        trustedVerifiers[verifier] = true;
        emit VerifierAdded(verifier);
    }

    /**
     * @dev Remove a trusted verifier.
     * @param verifier Address to remove
     */
    function removeVerifier(address verifier) external onlyOwner {
        trustedVerifiers[verifier] = false;
        emit VerifierRemoved(verifier);
    }

    // ============ View Functions ============

    /**
     * @dev Get computation details.
     * @param computationId Computation identifier
     */
    function getComputation(bytes32 computationId) external view returns (
        bytes32 modelId,
        bytes32 inputHash,
        bytes32 outputHash,
        bytes32 proofHash,
        address executor,
        uint256 timestamp,
        bool verified
    ) {
        Computation storage c = computations[computationId];
        return (
            c.modelId,
            c.inputHash,
            c.outputHash,
            c.proofHash,
            c.executor,
            c.timestamp,
            c.verified
        );
    }

    /**
     * @dev Get batch details.
     * @param batchId Batch identifier
     */
    function getBatch(bytes32 batchId) external view returns (
        bytes32 modelId,
        uint256 batchSize,
        uint256 timestamp,
        address executor
    ) {
        PredictionBatch storage b = batches[batchId];
        return (b.modelId, b.batchSize, b.timestamp, b.executor);
    }

    /**
     * @dev Verify an output hash matches a registered computation.
     * @param modelId Model identifier
     * @param inputHash Input hash to check
     * @param outputHash Expected output hash
     */
    function verifyOutput(
        bytes32 modelId,
        bytes32 inputHash,
        bytes32 outputHash
    ) external view returns (bool found, bytes32 computationId) {
        // Search through executor's computations
        // Note: In production, use better indexing
        bytes32[] storage compIds = executorComputations[msg.sender];

        for (uint256 i = 0; i < compIds.length; i++) {
            Computation storage c = computations[compIds[i]];
            if (
                c.modelId == modelId &&
                c.inputHash == inputHash &&
                c.outputHash == outputHash
            ) {
                return (true, compIds[i]);
            }
        }

        return (false, bytes32(0));
    }

    /**
     * @dev Get computation count for a model.
     * @param modelId Model identifier
     */
    function getModelComputationCount(bytes32 modelId) external view returns (uint256) {
        return modelComputationCount[modelId];
    }

    /**
     * @dev Get executor's computation history.
     * @param executor Address to query
     */
    function getExecutorComputations(address executor) external view returns (bytes32[] memory) {
        return executorComputations[executor];
    }
}
