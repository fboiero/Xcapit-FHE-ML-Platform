// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.20;

import "@openzeppelin/contracts/access/Ownable2Step.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ModelRegistryV2
 * @dev Secure registry for FHE-ML model verification and auditability.
 * @notice Version 2.0.0 - Security hardened for mainnet
 *
 * Changes from V1:
 * - Added ReentrancyGuard
 * - Added Pausable
 * - Added Ownable2Step for ownership transfer
 * - Added trusted verifiers (owners cannot verify own models)
 * - Added input validation with limits
 * - Added bounded loops with pagination
 * - Fixed pragma to specific version
 * - Added custom errors for gas efficiency
 */
contract ModelRegistryV2 is Ownable2Step, Pausable, ReentrancyGuard {
    // ============ Constants ============

    uint256 public constant MAX_STRING_LENGTH = 256;
    uint256 public constant MAX_CHECKPOINTS_PER_QUERY = 100;
    string public constant VERSION = "2.0.0";

    // ============ Custom Errors ============

    error InvalidStringLength(string parameter);
    error ModelNotFound(bytes32 modelId);
    error ModelNotActive(bytes32 modelId);
    error Unauthorized(address caller);
    error InvalidIndex(uint256 index, uint256 max);
    error AlreadyVerified(bytes32 modelId);
    error CannotVerifyOwnModel(bytes32 modelId);
    error RunNotFound(uint256 runIndex);
    error RunAlreadyCompleted(uint256 runIndex);
    error ZeroAddress();

    // ============ Structs ============

    struct Model {
        address owner;
        string modelType;
        string version;
        bytes32 weightsHash;
        uint256 createdAt;
        uint256 updatedAt;
        bool verified;
        bool active;
    }

    struct Checkpoint {
        uint256 epoch;
        bytes32 weightsHash;
        bytes32 metricsHash;
        uint256 timestamp;
    }

    struct TrainingRun {
        bytes32 modelId;
        bytes32 datasetHash;
        uint256 startTime;
        uint256 endTime;
        uint256 totalEpochs;
        bool completed;
    }

    // ============ State Variables ============

    mapping(bytes32 => Model) public models;
    mapping(bytes32 => Checkpoint[]) public checkpoints;
    mapping(bytes32 => TrainingRun[]) public trainingRuns;
    mapping(address => bytes32[]) public ownerModels;
    mapping(bytes32 => mapping(address => bool)) public authorized;

    // Trusted verifiers for model verification
    mapping(address => bool) public trustedVerifiers;

    // Indexed checkpoint lookup for O(1) verification
    mapping(bytes32 => mapping(uint256 => bytes32)) public checkpointWeightsByEpoch;

    uint256 private _modelCounter;

    // ============ Events ============

    event ModelRegistered(
        bytes32 indexed modelId,
        address indexed owner,
        string modelType,
        string version
    );

    event CheckpointSaved(
        bytes32 indexed modelId,
        uint256 indexed epoch,
        bytes32 weightsHash,
        bytes32 metricsHash
    );

    event TrainingStarted(
        bytes32 indexed modelId,
        bytes32 indexed runId,
        bytes32 datasetHash
    );

    event TrainingCompleted(
        bytes32 indexed modelId,
        bytes32 indexed runId,
        uint256 totalEpochs,
        bytes32 finalWeightsHash
    );

    event ModelVerified(
        bytes32 indexed modelId,
        address indexed verifier
    );

    event ModelDeactivated(
        bytes32 indexed modelId,
        address indexed owner
    );

    event AuthorizationGranted(
        bytes32 indexed modelId,
        address indexed grantee
    );

    event AuthorizationRevoked(
        bytes32 indexed modelId,
        address indexed grantee
    );

    event VerifierAdded(address indexed verifier);
    event VerifierRemoved(address indexed verifier);

    // ============ Modifiers ============

    modifier onlyModelOwner(bytes32 modelId) {
        if (models[modelId].owner != msg.sender) revert Unauthorized(msg.sender);
        _;
    }

    modifier onlyAuthorized(bytes32 modelId) {
        if (models[modelId].owner != msg.sender && !authorized[modelId][msg.sender]) {
            revert Unauthorized(msg.sender);
        }
        _;
    }

    modifier modelExists(bytes32 modelId) {
        if (models[modelId].createdAt == 0) revert ModelNotFound(modelId);
        _;
    }

    modifier modelActive(bytes32 modelId) {
        if (!models[modelId].active) revert ModelNotActive(modelId);
        _;
    }

    modifier onlyTrustedVerifier() {
        if (!trustedVerifiers[msg.sender]) revert Unauthorized(msg.sender);
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
     * @dev Register a new ML model.
     * @param modelType Type of model (e.g., "LinearRegression")
     * @param modelVersion Version string (e.g., "1.0.0")
     * @return modelId Unique identifier for the registered model
     */
    function registerModel(
        string calldata modelType,
        string calldata modelVersion
    ) external whenNotPaused nonReentrant returns (bytes32 modelId) {
        // Input validation
        if (bytes(modelType).length == 0 || bytes(modelType).length > MAX_STRING_LENGTH) {
            revert InvalidStringLength("modelType");
        }
        if (bytes(modelVersion).length == 0 || bytes(modelVersion).length > MAX_STRING_LENGTH) {
            revert InvalidStringLength("version");
        }

        unchecked {
            ++_modelCounter;
        }

        modelId = keccak256(
            abi.encodePacked(
                msg.sender,
                modelType,
                modelVersion,
                block.timestamp,
                _modelCounter
            )
        );

        models[modelId] = Model({
            owner: msg.sender,
            modelType: modelType,
            version: modelVersion,
            weightsHash: bytes32(0),
            createdAt: block.timestamp,
            updatedAt: block.timestamp,
            verified: false,
            active: true
        });

        ownerModels[msg.sender].push(modelId);

        emit ModelRegistered(modelId, msg.sender, modelType, modelVersion);

        return modelId;
    }

    /**
     * @dev Save a training checkpoint.
     */
    function saveCheckpoint(
        bytes32 modelId,
        uint256 epoch,
        bytes32 weightsHash,
        bytes32 metricsHash
    ) external
        whenNotPaused
        nonReentrant
        modelExists(modelId)
        onlyAuthorized(modelId)
        modelActive(modelId)
    {
        checkpoints[modelId].push(Checkpoint({
            epoch: epoch,
            weightsHash: weightsHash,
            metricsHash: metricsHash,
            timestamp: block.timestamp
        }));

        // Store in indexed mapping for O(1) verification
        checkpointWeightsByEpoch[modelId][epoch] = weightsHash;

        models[modelId].weightsHash = weightsHash;
        models[modelId].updatedAt = block.timestamp;

        emit CheckpointSaved(modelId, epoch, weightsHash, metricsHash);
    }

    /**
     * @dev Start a new training run.
     */
    function startTraining(
        bytes32 modelId,
        bytes32 datasetHash
    ) external
        whenNotPaused
        nonReentrant
        modelExists(modelId)
        onlyAuthorized(modelId)
        modelActive(modelId)
        returns (bytes32 runId)
    {
        runId = keccak256(
            abi.encodePacked(modelId, datasetHash, block.timestamp, trainingRuns[modelId].length)
        );

        trainingRuns[modelId].push(TrainingRun({
            modelId: modelId,
            datasetHash: datasetHash,
            startTime: block.timestamp,
            endTime: 0,
            totalEpochs: 0,
            completed: false
        }));

        emit TrainingStarted(modelId, runId, datasetHash);

        return runId;
    }

    /**
     * @dev Complete a training run.
     */
    function completeTraining(
        bytes32 modelId,
        uint256 runIndex,
        uint256 totalEpochs,
        bytes32 finalWeightsHash
    ) external
        whenNotPaused
        nonReentrant
        modelExists(modelId)
        onlyAuthorized(modelId)
    {
        if (runIndex >= trainingRuns[modelId].length) {
            revert RunNotFound(runIndex);
        }
        if (trainingRuns[modelId][runIndex].completed) {
            revert RunAlreadyCompleted(runIndex);
        }

        TrainingRun storage run = trainingRuns[modelId][runIndex];
        run.endTime = block.timestamp;
        run.totalEpochs = totalEpochs;
        run.completed = true;

        models[modelId].weightsHash = finalWeightsHash;
        models[modelId].updatedAt = block.timestamp;

        bytes32 runId = keccak256(
            abi.encodePacked(modelId, run.datasetHash, run.startTime, runIndex)
        );

        emit TrainingCompleted(modelId, runId, totalEpochs, finalWeightsHash);
    }

    /**
     * @dev Mark a model as verified (by trusted verifier only).
     * @notice Owners cannot verify their own models.
     */
    function verifyModel(
        bytes32 modelId
    ) external
        whenNotPaused
        modelExists(modelId)
        onlyTrustedVerifier
    {
        if (models[modelId].owner == msg.sender) {
            revert CannotVerifyOwnModel(modelId);
        }
        if (models[modelId].verified) {
            revert AlreadyVerified(modelId);
        }

        models[modelId].verified = true;
        models[modelId].updatedAt = block.timestamp;

        emit ModelVerified(modelId, msg.sender);
    }

    /**
     * @dev Deactivate a model (soft delete).
     */
    function deactivateModel(
        bytes32 modelId
    ) external modelExists(modelId) onlyModelOwner(modelId) {
        models[modelId].active = false;
        models[modelId].updatedAt = block.timestamp;

        emit ModelDeactivated(modelId, msg.sender);
    }

    /**
     * @dev Grant authorization to an address for a model.
     */
    function grantAuthorization(
        bytes32 modelId,
        address grantee
    ) external modelExists(modelId) onlyModelOwner(modelId) {
        if (grantee == address(0)) revert ZeroAddress();
        authorized[modelId][grantee] = true;

        emit AuthorizationGranted(modelId, grantee);
    }

    /**
     * @dev Revoke authorization from an address.
     */
    function revokeAuthorization(
        bytes32 modelId,
        address grantee
    ) external modelExists(modelId) onlyModelOwner(modelId) {
        authorized[modelId][grantee] = false;

        emit AuthorizationRevoked(modelId, grantee);
    }

    // ============ View Functions ============

    function getModel(bytes32 modelId) external view returns (
        address owner,
        string memory modelType,
        string memory version,
        bytes32 weightsHash,
        uint256 createdAt,
        uint256 updatedAt,
        bool verified,
        bool active
    ) {
        Model storage m = models[modelId];
        return (
            m.owner,
            m.modelType,
            m.version,
            m.weightsHash,
            m.createdAt,
            m.updatedAt,
            m.verified,
            m.active
        );
    }

    function getCheckpointCount(bytes32 modelId) external view returns (uint256) {
        return checkpoints[modelId].length;
    }

    /**
     * @dev Get checkpoints with pagination.
     */
    function getCheckpoints(
        bytes32 modelId,
        uint256 offset,
        uint256 limit
    ) external view returns (Checkpoint[] memory) {
        uint256 total = checkpoints[modelId].length;
        if (offset >= total) {
            return new Checkpoint[](0);
        }

        uint256 end = offset + limit;
        if (end > total) end = total;
        if (limit > MAX_CHECKPOINTS_PER_QUERY) {
            end = offset + MAX_CHECKPOINTS_PER_QUERY;
        }

        uint256 length = end - offset;
        Checkpoint[] memory result = new Checkpoint[](length);

        for (uint256 i = 0; i < length;) {
            result[i] = checkpoints[modelId][offset + i];
            unchecked { ++i; }
        }

        return result;
    }

    function getCheckpoint(
        bytes32 modelId,
        uint256 index
    ) external view returns (
        uint256 epoch,
        bytes32 weightsHash,
        bytes32 metricsHash,
        uint256 timestamp
    ) {
        if (index >= checkpoints[modelId].length) {
            revert InvalidIndex(index, checkpoints[modelId].length);
        }
        Checkpoint storage cp = checkpoints[modelId][index];
        return (cp.epoch, cp.weightsHash, cp.metricsHash, cp.timestamp);
    }

    function getTrainingRunCount(bytes32 modelId) external view returns (uint256) {
        return trainingRuns[modelId].length;
    }

    function getOwnerModels(address modelOwner) external view returns (bytes32[] memory) {
        return ownerModels[modelOwner];
    }

    function isAuthorized(bytes32 modelId, address addr) external view returns (bool) {
        return models[modelId].owner == addr || authorized[modelId][addr];
    }

    /**
     * @dev O(1) checkpoint verification using indexed mapping.
     */
    function verifyCheckpoint(
        bytes32 modelId,
        uint256 epoch,
        bytes32 weightsHash
    ) external view returns (bool) {
        return checkpointWeightsByEpoch[modelId][epoch] == weightsHash && weightsHash != bytes32(0);
    }
}
