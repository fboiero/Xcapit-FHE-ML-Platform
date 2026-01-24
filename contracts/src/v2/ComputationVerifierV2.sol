// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.20;

import "@openzeppelin/contracts/access/Ownable2Step.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ComputationVerifierV2
 * @dev Secure verifier for FHE computation proofs and prediction audit trail.
 * @notice Version 2.0.0 - Security hardened for mainnet
 *
 * Security Improvements:
 * - Two-step ownership transfer
 * - Pausable for emergencies
 * - Bounded batch sizes
 * - Input validation
 * - Custom errors for gas efficiency
 * - O(1) output verification with indexed mappings
 */
contract ComputationVerifierV2 is Ownable2Step, Pausable, ReentrancyGuard {
    // ============ Constants ============

    uint256 public constant MAX_BATCH_SIZE = 1000;
    string public constant VERSION = "2.0.0";

    // ============ Custom Errors ============

    error ComputationNotFound(bytes32 computationId);
    error BatchNotFound(bytes32 batchId);
    error NotTrustedVerifier(address caller);
    error ArrayLengthMismatch();
    error EmptyBatch();
    error BatchTooLarge(uint256 size, uint256 max);
    error ZeroAddress();
    error AlreadyVerified(bytes32 computationId);

    // ============ Structs ============

    struct Computation {
        bytes32 modelId;
        bytes32 inputHash;
        bytes32 outputHash;
        bytes32 proofHash;
        address executor;
        uint256 timestamp;
        bool verified;
    }

    struct PredictionBatch {
        bytes32 modelId;
        uint256 batchSize;
        uint256 timestamp;
        address executor;
        bytes32 merkleRoot; // Merkle root of all input/output pairs for efficient verification
    }

    // ============ State Variables ============

    mapping(bytes32 => Computation) public computations;
    mapping(bytes32 => uint256) public modelComputationCount;
    mapping(bytes32 => PredictionBatch) public batches;
    mapping(address => bytes32[]) public executorComputations;
    mapping(address => bool) public trustedVerifiers;

    // Indexed mapping for O(1) output verification
    // keccak256(modelId, inputHash) => outputHash
    mapping(bytes32 => bytes32) public outputIndex;

    // keccak256(modelId, inputHash, outputHash) => computationId
    mapping(bytes32 => bytes32) public computationIndex;

    uint256 private _computationCounter;

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

    modifier onlyTrustedVerifier() {
        if (!trustedVerifiers[msg.sender] && msg.sender != owner()) {
            revert NotTrustedVerifier(msg.sender);
        }
        _;
    }

    // ============ Constructor ============

    constructor() Ownable(msg.sender) {
        trustedVerifiers[msg.sender] = true;
    }

    // ============ Admin Functions ============

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function addVerifier(address verifier) external onlyOwner {
        if (verifier == address(0)) revert ZeroAddress();
        trustedVerifiers[verifier] = true;
        emit VerifierAdded(verifier);
    }

    function removeVerifier(address verifier) external onlyOwner {
        trustedVerifiers[verifier] = false;
        emit VerifierRemoved(verifier);
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
    ) external whenNotPaused nonReentrant returns (bytes32 computationId) {
        unchecked { ++_computationCounter; }

        computationId = keccak256(
            abi.encode(
                modelId,
                inputHash,
                outputHash,
                msg.sender,
                block.timestamp,
                _computationCounter
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

        unchecked {
            ++modelComputationCount[modelId];
        }

        executorComputations[msg.sender].push(computationId);

        // Index for O(1) verification
        bytes32 inputKey = keccak256(abi.encode(modelId, inputHash));
        outputIndex[inputKey] = outputHash;

        bytes32 fullKey = keccak256(abi.encode(modelId, inputHash, outputHash));
        computationIndex[fullKey] = computationId;

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
     * @dev Register a batch of predictions with Merkle root for efficient verification.
     * @param modelId Model used for predictions
     * @param inputHashes Array of input hashes
     * @param outputHashes Array of output hashes
     * @return batchId Unique identifier for this batch
     */
    function registerBatch(
        bytes32 modelId,
        bytes32[] calldata inputHashes,
        bytes32[] calldata outputHashes
    ) external whenNotPaused nonReentrant returns (bytes32 batchId) {
        if (inputHashes.length != outputHashes.length) revert ArrayLengthMismatch();
        if (inputHashes.length == 0) revert EmptyBatch();
        if (inputHashes.length > MAX_BATCH_SIZE) {
            revert BatchTooLarge(inputHashes.length, MAX_BATCH_SIZE);
        }

        // Compute Merkle root for efficient verification
        bytes32 merkleRoot = _computeMerkleRoot(inputHashes, outputHashes);

        batchId = keccak256(
            abi.encode(
                modelId,
                merkleRoot,
                msg.sender,
                block.timestamp
            )
        );

        batches[batchId] = PredictionBatch({
            modelId: modelId,
            batchSize: inputHashes.length,
            timestamp: block.timestamp,
            executor: msg.sender,
            merkleRoot: merkleRoot
        });

        // Index each computation for O(1) lookup
        for (uint256 i = 0; i < inputHashes.length;) {
            bytes32 inputKey = keccak256(abi.encode(modelId, inputHashes[i]));
            outputIndex[inputKey] = outputHashes[i];

            bytes32 fullKey = keccak256(abi.encode(modelId, inputHashes[i], outputHashes[i]));
            computationIndex[fullKey] = batchId;

            unchecked { ++i; }
        }

        unchecked {
            modelComputationCount[modelId] += inputHashes.length;
        }

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
    ) external whenNotPaused onlyTrustedVerifier {
        if (computations[computationId].timestamp == 0) {
            revert ComputationNotFound(computationId);
        }

        computations[computationId].verified = success;

        emit ComputationVerified(computationId, msg.sender, success);
    }

    // ============ View Functions ============

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

    function getBatch(bytes32 batchId) external view returns (
        bytes32 modelId,
        uint256 batchSize,
        uint256 timestamp,
        address executor,
        bytes32 merkleRoot
    ) {
        PredictionBatch storage b = batches[batchId];
        return (b.modelId, b.batchSize, b.timestamp, b.executor, b.merkleRoot);
    }

    /**
     * @dev O(1) output verification using indexed mapping.
     * @param modelId Model identifier
     * @param inputHash Input hash to check
     * @param outputHash Expected output hash
     * @return valid True if the output matches registered computation
     * @return computationId The computation/batch ID if found
     */
    function verifyOutput(
        bytes32 modelId,
        bytes32 inputHash,
        bytes32 outputHash
    ) external view returns (bool valid, bytes32 computationId) {
        bytes32 inputKey = keccak256(abi.encode(modelId, inputHash));
        bytes32 storedOutput = outputIndex[inputKey];

        if (storedOutput == outputHash && storedOutput != bytes32(0)) {
            bytes32 fullKey = keccak256(abi.encode(modelId, inputHash, outputHash));
            return (true, computationIndex[fullKey]);
        }

        return (false, bytes32(0));
    }

    /**
     * @dev Get expected output for a given model and input (O(1)).
     */
    function getExpectedOutput(
        bytes32 modelId,
        bytes32 inputHash
    ) external view returns (bytes32) {
        bytes32 inputKey = keccak256(abi.encode(modelId, inputHash));
        return outputIndex[inputKey];
    }

    function getModelComputationCount(bytes32 modelId) external view returns (uint256) {
        return modelComputationCount[modelId];
    }

    function getExecutorComputations(address executor) external view returns (bytes32[] memory) {
        return executorComputations[executor];
    }

    function getExecutorComputationCount(address executor) external view returns (uint256) {
        return executorComputations[executor].length;
    }

    /**
     * @dev Get paginated executor computations to avoid unbounded returns.
     */
    function getExecutorComputationsPaginated(
        address executor,
        uint256 offset,
        uint256 limit
    ) external view returns (bytes32[] memory) {
        bytes32[] storage allComps = executorComputations[executor];
        uint256 total = allComps.length;

        if (offset >= total) {
            return new bytes32[](0);
        }

        uint256 end = offset + limit;
        if (end > total) end = total;

        uint256 length = end - offset;
        bytes32[] memory result = new bytes32[](length);

        for (uint256 i = 0; i < length;) {
            result[i] = allComps[offset + i];
            unchecked { ++i; }
        }

        return result;
    }

    // ============ Internal Functions ============

    /**
     * @dev Compute simple Merkle root for batch verification.
     */
    function _computeMerkleRoot(
        bytes32[] calldata inputHashes,
        bytes32[] calldata outputHashes
    ) internal pure returns (bytes32) {
        bytes32[] memory leaves = new bytes32[](inputHashes.length);

        for (uint256 i = 0; i < inputHashes.length;) {
            leaves[i] = keccak256(abi.encode(inputHashes[i], outputHashes[i]));
            unchecked { ++i; }
        }

        return _merkleRoot(leaves);
    }

    function _merkleRoot(bytes32[] memory leaves) internal pure returns (bytes32) {
        if (leaves.length == 0) return bytes32(0);
        if (leaves.length == 1) return leaves[0];

        uint256 n = leaves.length;
        while (n > 1) {
            uint256 newN = (n + 1) / 2;
            for (uint256 i = 0; i < newN;) {
                uint256 left = i * 2;
                uint256 right = left + 1;

                if (right < n) {
                    leaves[i] = keccak256(abi.encode(leaves[left], leaves[right]));
                } else {
                    leaves[i] = leaves[left];
                }
                unchecked { ++i; }
            }
            n = newN;
        }

        return leaves[0];
    }
}
