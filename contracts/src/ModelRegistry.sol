// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.0;

/**
 * @title ModelRegistry
 * @dev Registry for FHE-ML model verification and auditability on blockchain.
 *
 * This contract allows:
 * - Registering ML models with metadata
 * - Saving training checkpoints with weights hashes
 * - Verifying model provenance and training history
 * - Tracking model ownership and access control
 */
contract ModelRegistry {
    // ============ Structs ============

    struct Model {
        address owner;
        string modelType;       // e.g., "LinearRegression", "LogisticRegression"
        string version;
        bytes32 weightsHash;    // Hash of final trained weights
        uint256 createdAt;
        uint256 updatedAt;
        bool verified;
        bool active;
    }

    struct Checkpoint {
        uint256 epoch;
        bytes32 weightsHash;
        bytes32 metricsHash;    // Hash of training metrics (loss, accuracy, etc.)
        uint256 timestamp;
    }

    struct TrainingRun {
        bytes32 modelId;
        bytes32 datasetHash;    // Hash of training data (for reproducibility)
        uint256 startTime;
        uint256 endTime;
        uint256 totalEpochs;
        bool completed;
    }

    // ============ State Variables ============

    // Model ID => Model
    mapping(bytes32 => Model) public models;

    // Model ID => Checkpoint[]
    mapping(bytes32 => Checkpoint[]) public checkpoints;

    // Model ID => TrainingRun[]
    mapping(bytes32 => TrainingRun[]) public trainingRuns;

    // Owner => Model IDs
    mapping(address => bytes32[]) public ownerModels;

    // Model ID => authorized addresses
    mapping(bytes32 => mapping(address => bool)) public authorized;

    // Counter for generating unique IDs
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

    // ============ Modifiers ============

    modifier onlyModelOwner(bytes32 modelId) {
        require(models[modelId].owner == msg.sender, "Not model owner");
        _;
    }

    modifier onlyAuthorized(bytes32 modelId) {
        require(
            models[modelId].owner == msg.sender || authorized[modelId][msg.sender],
            "Not authorized"
        );
        _;
    }

    modifier modelExists(bytes32 modelId) {
        require(models[modelId].createdAt != 0, "Model does not exist");
        _;
    }

    modifier modelActive(bytes32 modelId) {
        require(models[modelId].active, "Model is not active");
        _;
    }

    // ============ External Functions ============

    /**
     * @dev Register a new ML model.
     * @param modelType Type of model (e.g., "LinearRegression")
     * @param version Version string (e.g., "1.0.0")
     * @return modelId Unique identifier for the registered model
     */
    function registerModel(
        string calldata modelType,
        string calldata version
    ) external returns (bytes32 modelId) {
        _modelCounter++;

        modelId = keccak256(
            abi.encodePacked(
                msg.sender,
                modelType,
                version,
                block.timestamp,
                _modelCounter
            )
        );

        models[modelId] = Model({
            owner: msg.sender,
            modelType: modelType,
            version: version,
            weightsHash: bytes32(0),
            createdAt: block.timestamp,
            updatedAt: block.timestamp,
            verified: false,
            active: true
        });

        ownerModels[msg.sender].push(modelId);

        emit ModelRegistered(modelId, msg.sender, modelType, version);

        return modelId;
    }

    /**
     * @dev Save a training checkpoint.
     * @param modelId Model identifier
     * @param epoch Training epoch number
     * @param weightsHash Hash of model weights at this epoch
     * @param metricsHash Hash of training metrics
     */
    function saveCheckpoint(
        bytes32 modelId,
        uint256 epoch,
        bytes32 weightsHash,
        bytes32 metricsHash
    ) external modelExists(modelId) onlyAuthorized(modelId) modelActive(modelId) {
        checkpoints[modelId].push(Checkpoint({
            epoch: epoch,
            weightsHash: weightsHash,
            metricsHash: metricsHash,
            timestamp: block.timestamp
        }));

        // Update model's latest weights hash
        models[modelId].weightsHash = weightsHash;
        models[modelId].updatedAt = block.timestamp;

        emit CheckpointSaved(modelId, epoch, weightsHash, metricsHash);
    }

    /**
     * @dev Start a new training run.
     * @param modelId Model identifier
     * @param datasetHash Hash of training dataset
     * @return runId Unique identifier for this training run
     */
    function startTraining(
        bytes32 modelId,
        bytes32 datasetHash
    ) external modelExists(modelId) onlyAuthorized(modelId) modelActive(modelId) returns (bytes32 runId) {
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
     * @param modelId Model identifier
     * @param runIndex Index of the training run
     * @param totalEpochs Total epochs completed
     * @param finalWeightsHash Hash of final model weights
     */
    function completeTraining(
        bytes32 modelId,
        uint256 runIndex,
        uint256 totalEpochs,
        bytes32 finalWeightsHash
    ) external modelExists(modelId) onlyAuthorized(modelId) {
        require(runIndex < trainingRuns[modelId].length, "Invalid run index");
        require(!trainingRuns[modelId][runIndex].completed, "Already completed");

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
     * @dev Mark a model as verified (e.g., after audit).
     * @param modelId Model identifier
     */
    function verifyModel(
        bytes32 modelId
    ) external modelExists(modelId) onlyModelOwner(modelId) {
        models[modelId].verified = true;
        models[modelId].updatedAt = block.timestamp;

        emit ModelVerified(modelId, msg.sender);
    }

    /**
     * @dev Deactivate a model (soft delete).
     * @param modelId Model identifier
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
     * @param modelId Model identifier
     * @param grantee Address to authorize
     */
    function grantAuthorization(
        bytes32 modelId,
        address grantee
    ) external modelExists(modelId) onlyModelOwner(modelId) {
        authorized[modelId][grantee] = true;

        emit AuthorizationGranted(modelId, grantee);
    }

    /**
     * @dev Revoke authorization from an address.
     * @param modelId Model identifier
     * @param grantee Address to revoke
     */
    function revokeAuthorization(
        bytes32 modelId,
        address grantee
    ) external modelExists(modelId) onlyModelOwner(modelId) {
        authorized[modelId][grantee] = false;

        emit AuthorizationRevoked(modelId, grantee);
    }

    // ============ View Functions ============

    /**
     * @dev Get model details.
     * @param modelId Model identifier
     */
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

    /**
     * @dev Get number of checkpoints for a model.
     * @param modelId Model identifier
     */
    function getCheckpointCount(bytes32 modelId) external view returns (uint256) {
        return checkpoints[modelId].length;
    }

    /**
     * @dev Get a specific checkpoint.
     * @param modelId Model identifier
     * @param index Checkpoint index
     */
    function getCheckpoint(
        bytes32 modelId,
        uint256 index
    ) external view returns (
        uint256 epoch,
        bytes32 weightsHash,
        bytes32 metricsHash,
        uint256 timestamp
    ) {
        require(index < checkpoints[modelId].length, "Invalid index");
        Checkpoint storage cp = checkpoints[modelId][index];
        return (cp.epoch, cp.weightsHash, cp.metricsHash, cp.timestamp);
    }

    /**
     * @dev Get number of training runs for a model.
     * @param modelId Model identifier
     */
    function getTrainingRunCount(bytes32 modelId) external view returns (uint256) {
        return trainingRuns[modelId].length;
    }

    /**
     * @dev Get models owned by an address.
     * @param owner Owner address
     */
    function getOwnerModels(address owner) external view returns (bytes32[] memory) {
        return ownerModels[owner];
    }

    /**
     * @dev Check if an address is authorized for a model.
     * @param modelId Model identifier
     * @param addr Address to check
     */
    function isAuthorized(bytes32 modelId, address addr) external view returns (bool) {
        return models[modelId].owner == addr || authorized[modelId][addr];
    }

    /**
     * @dev Verify a weights hash matches a checkpoint.
     * @param modelId Model identifier
     * @param epoch Epoch to verify
     * @param weightsHash Hash to verify
     */
    function verifyCheckpoint(
        bytes32 modelId,
        uint256 epoch,
        bytes32 weightsHash
    ) external view returns (bool) {
        Checkpoint[] storage cps = checkpoints[modelId];
        for (uint256 i = 0; i < cps.length; i++) {
            if (cps[i].epoch == epoch && cps[i].weightsHash == weightsHash) {
                return true;
            }
        }
        return false;
    }
}
