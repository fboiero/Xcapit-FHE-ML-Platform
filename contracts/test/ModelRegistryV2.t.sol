// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.20;

import "forge-std/Test.sol";
import "../src/v2/ModelRegistryV2.sol";

contract ModelRegistryV2Test is Test {
    ModelRegistryV2 public registry;

    address public owner = address(this);
    address public user1 = address(0x1);
    address public verifier = address(0x2);

    bytes32 public modelId;

    event ModelRegistered(bytes32 indexed modelId, address indexed owner, string modelType, string version);
    event CheckpointSaved(bytes32 indexed modelId, uint256 indexed epoch, bytes32 weightsHash, bytes32 metricsHash);
    event ModelVerified(bytes32 indexed modelId, address indexed verifier);

    function setUp() public {
        registry = new ModelRegistryV2();
        registry.addVerifier(verifier);

        // Register a model
        modelId = registry.registerModel("LinearRegression", "1.0.0");
    }

    // ============ Model Registration Tests ============

    function test_RegisterModel() public {
        bytes32 newModelId = registry.registerModel("LogisticRegression", "2.0.0");

        (
            address modelOwner,
            string memory modelType,
            string memory version,
            ,
            uint256 createdAt,
            ,
            bool verified,
            bool active
        ) = registry.getModel(newModelId);

        assertEq(modelOwner, address(this));
        assertEq(modelType, "LogisticRegression");
        assertEq(version, "2.0.0");
        assertGt(createdAt, 0);
        assertFalse(verified);
        assertTrue(active);
    }

    function test_RevertWhen_EmptyModelType() public {
        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.InvalidStringLength.selector, "modelType"));
        registry.registerModel("", "1.0.0");
    }

    function test_RevertWhen_EmptyVersion() public {
        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.InvalidStringLength.selector, "version"));
        registry.registerModel("LinearRegression", "");
    }

    // ============ Checkpoint Tests ============

    function test_SaveCheckpoint() public {
        bytes32 weightsHash = keccak256("weights_epoch_1");
        bytes32 metricsHash = keccak256("metrics_epoch_1");

        registry.saveCheckpoint(modelId, 1, weightsHash, metricsHash);

        uint256 count = registry.getCheckpointCount(modelId);
        assertEq(count, 1);

        (uint256 epoch, bytes32 storedWeights, bytes32 storedMetrics, uint256 timestamp) = registry.getCheckpoint(modelId, 0);

        assertEq(epoch, 1);
        assertEq(storedWeights, weightsHash);
        assertEq(storedMetrics, metricsHash);
        assertGt(timestamp, 0);
    }

    function test_VerifyCheckpoint_O1() public {
        bytes32 weightsHash = keccak256("weights_epoch_1");
        registry.saveCheckpoint(modelId, 1, weightsHash, bytes32(0));

        // O(1) verification
        bool valid = registry.verifyCheckpoint(modelId, 1, weightsHash);
        assertTrue(valid);

        // Wrong epoch
        bool invalid = registry.verifyCheckpoint(modelId, 2, weightsHash);
        assertFalse(invalid);

        // Wrong hash
        bool wrongHash = registry.verifyCheckpoint(modelId, 1, keccak256("wrong"));
        assertFalse(wrongHash);
    }

    function test_RevertWhen_UnauthorizedSavesCheckpoint() public {
        vm.prank(user1);
        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.Unauthorized.selector, user1));
        registry.saveCheckpoint(modelId, 1, bytes32(0), bytes32(0));
    }

    // ============ Training Run Tests ============

    function test_StartAndCompleteTraining() public {
        bytes32 datasetHash = keccak256("training_data");

        bytes32 runId = registry.startTraining(modelId, datasetHash);
        assertNotEq(runId, bytes32(0));

        uint256 runCount = registry.getTrainingRunCount(modelId);
        assertEq(runCount, 1);

        // Complete training
        bytes32 finalWeights = keccak256("final_weights");
        registry.completeTraining(modelId, 0, 100, finalWeights);

        (
            ,
            ,
            ,
            bytes32 storedWeights,
            ,
            ,
            ,

        ) = registry.getModel(modelId);
        assertEq(storedWeights, finalWeights);
    }

    function test_RevertWhen_CompletingNonExistentRun() public {
        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.RunNotFound.selector, 999));
        registry.completeTraining(modelId, 999, 100, bytes32(0));
    }

    function test_RevertWhen_CompletingAlreadyCompletedRun() public {
        registry.startTraining(modelId, bytes32(0));
        registry.completeTraining(modelId, 0, 100, bytes32(0));

        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.RunAlreadyCompleted.selector, 0));
        registry.completeTraining(modelId, 0, 100, bytes32(0));
    }

    // ============ Verification Tests ============

    function test_VerifyModel() public {
        vm.prank(verifier);
        registry.verifyModel(modelId);

        (,,,,,, bool verified,) = registry.getModel(modelId);
        assertTrue(verified);
    }

    function test_RevertWhen_OwnerVerifiesOwnModel() public {
        // Owner is also a verifier by default
        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.CannotVerifyOwnModel.selector, modelId));
        registry.verifyModel(modelId);
    }

    function test_RevertWhen_UnauthorizedVerifies() public {
        vm.prank(user1);
        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.Unauthorized.selector, user1));
        registry.verifyModel(modelId);
    }

    function test_RevertWhen_VerifyingAlreadyVerified() public {
        vm.prank(verifier);
        registry.verifyModel(modelId);

        vm.prank(verifier);
        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.AlreadyVerified.selector, modelId));
        registry.verifyModel(modelId);
    }

    // ============ Authorization Tests ============

    function test_GrantAndRevokeAuthorization() public {
        registry.grantAuthorization(modelId, user1);
        assertTrue(registry.isAuthorized(modelId, user1));

        // User1 can now save checkpoints
        vm.prank(user1);
        registry.saveCheckpoint(modelId, 1, bytes32(0), bytes32(0));

        // Revoke
        registry.revokeAuthorization(modelId, user1);
        assertFalse(registry.isAuthorized(modelId, user1));

        // User1 can no longer save checkpoints
        vm.prank(user1);
        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.Unauthorized.selector, user1));
        registry.saveCheckpoint(modelId, 2, bytes32(0), bytes32(0));
    }

    function test_RevertWhen_GrantingToZeroAddress() public {
        vm.expectRevert(ModelRegistryV2.ZeroAddress.selector);
        registry.grantAuthorization(modelId, address(0));
    }

    // ============ Deactivation Tests ============

    function test_DeactivateModel() public {
        registry.deactivateModel(modelId);

        (,,,,,,, bool active) = registry.getModel(modelId);
        assertFalse(active);
    }

    function test_RevertWhen_SavingCheckpointOnInactiveModel() public {
        registry.deactivateModel(modelId);

        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.ModelNotActive.selector, modelId));
        registry.saveCheckpoint(modelId, 1, bytes32(0), bytes32(0));
    }

    // ============ Pagination Tests ============

    function test_GetCheckpointsPaginated() public {
        // Save 10 checkpoints
        for (uint256 i = 1; i <= 10; i++) {
            registry.saveCheckpoint(modelId, i, bytes32(i), bytes32(i * 2));
        }

        // Get first 5
        ModelRegistryV2.Checkpoint[] memory page1 = registry.getCheckpoints(modelId, 0, 5);
        assertEq(page1.length, 5);
        assertEq(page1[0].epoch, 1);
        assertEq(page1[4].epoch, 5);

        // Get next 5
        ModelRegistryV2.Checkpoint[] memory page2 = registry.getCheckpoints(modelId, 5, 5);
        assertEq(page2.length, 5);
        assertEq(page2[0].epoch, 6);
        assertEq(page2[4].epoch, 10);

        // Out of bounds
        ModelRegistryV2.Checkpoint[] memory empty = registry.getCheckpoints(modelId, 100, 5);
        assertEq(empty.length, 0);
    }

    // ============ Owner Models Tests ============

    function test_GetOwnerModels() public {
        registry.registerModel("Model2", "1.0.0");
        registry.registerModel("Model3", "1.0.0");

        bytes32[] memory models = registry.getOwnerModels(address(this));
        assertEq(models.length, 3);
    }

    // ============ Pause Tests ============

    function test_Pause() public {
        registry.pause();

        vm.expectRevert();
        registry.registerModel("Paused", "1.0.0");

        registry.unpause();
        registry.registerModel("Unpaused", "1.0.0");
    }

    // ============ Fuzz Tests ============

    function testFuzz_RegisterModel(string memory modelType, string memory version) public {
        vm.assume(bytes(modelType).length > 0 && bytes(modelType).length <= 256);
        vm.assume(bytes(version).length > 0 && bytes(version).length <= 256);

        bytes32 id = registry.registerModel(modelType, version);
        assertNotEq(id, bytes32(0));
    }

    function testFuzz_SaveCheckpoint(uint256 epoch, bytes32 weightsHash, bytes32 metricsHash) public {
        registry.saveCheckpoint(modelId, epoch, weightsHash, metricsHash);

        (uint256 storedEpoch, bytes32 storedWeights, bytes32 storedMetrics,) = registry.getCheckpoint(modelId, 0);

        assertEq(storedEpoch, epoch);
        assertEq(storedWeights, weightsHash);
        assertEq(storedMetrics, metricsHash);
    }
}
