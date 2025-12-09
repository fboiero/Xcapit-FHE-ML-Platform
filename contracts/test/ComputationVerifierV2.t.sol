// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.20;

import "forge-std/Test.sol";
import "../src/v2/ComputationVerifierV2.sol";

contract ComputationVerifierV2Test is Test {
    ComputationVerifierV2 public verifier;

    address public owner = address(this);
    address public executor = address(0x1);
    address public trustedVerifier = address(0x2);

    bytes32 public modelId = keccak256("test_model");

    event ComputationRegistered(bytes32 indexed computationId, bytes32 indexed modelId, bytes32 inputHash, bytes32 outputHash, address executor);
    event ComputationVerified(bytes32 indexed computationId, address indexed verifier, bool success);
    event BatchRegistered(bytes32 indexed batchId, bytes32 indexed modelId, uint256 batchSize, address executor);

    function setUp() public {
        verifier = new ComputationVerifierV2();
        verifier.addVerifier(trustedVerifier);
    }

    // ============ Computation Registration Tests ============

    function test_RegisterComputation() public {
        bytes32 inputHash = keccak256("encrypted_input");
        bytes32 outputHash = keccak256("encrypted_output");
        bytes32 proofHash = keccak256("zk_proof");

        vm.prank(executor);
        bytes32 computationId = verifier.registerComputation(modelId, inputHash, outputHash, proofHash);

        assertNotEq(computationId, bytes32(0));

        (
            bytes32 storedModelId,
            bytes32 storedInput,
            bytes32 storedOutput,
            bytes32 storedProof,
            address storedExecutor,
            uint256 timestamp,
            bool verified
        ) = verifier.getComputation(computationId);

        assertEq(storedModelId, modelId);
        assertEq(storedInput, inputHash);
        assertEq(storedOutput, outputHash);
        assertEq(storedProof, proofHash);
        assertEq(storedExecutor, executor);
        assertGt(timestamp, 0);
        assertFalse(verified);
    }

    function test_ModelComputationCount() public {
        vm.prank(executor);
        verifier.registerComputation(modelId, bytes32(uint256(1)), bytes32(uint256(2)), bytes32(0));

        vm.prank(executor);
        verifier.registerComputation(modelId, bytes32(uint256(3)), bytes32(uint256(4)), bytes32(0));

        uint256 count = verifier.getModelComputationCount(modelId);
        assertEq(count, 2);
    }

    // ============ O(1) Verification Tests ============

    function test_VerifyOutput_O1() public {
        bytes32 inputHash = keccak256("input");
        bytes32 outputHash = keccak256("output");

        vm.prank(executor);
        bytes32 computationId = verifier.registerComputation(modelId, inputHash, outputHash, bytes32(0));

        // O(1) verification
        (bool valid, bytes32 foundId) = verifier.verifyOutput(modelId, inputHash, outputHash);
        assertTrue(valid);
        assertEq(foundId, computationId);

        // Wrong output
        (bool invalid,) = verifier.verifyOutput(modelId, inputHash, keccak256("wrong"));
        assertFalse(invalid);

        // Wrong input
        (bool wrongInput,) = verifier.verifyOutput(modelId, keccak256("wrong"), outputHash);
        assertFalse(wrongInput);
    }

    function test_GetExpectedOutput() public {
        bytes32 inputHash = keccak256("input");
        bytes32 outputHash = keccak256("output");

        vm.prank(executor);
        verifier.registerComputation(modelId, inputHash, outputHash, bytes32(0));

        bytes32 expected = verifier.getExpectedOutput(modelId, inputHash);
        assertEq(expected, outputHash);
    }

    // ============ Batch Registration Tests ============

    function test_RegisterBatch() public {
        bytes32[] memory inputs = new bytes32[](3);
        bytes32[] memory outputs = new bytes32[](3);

        for (uint256 i = 0; i < 3; i++) {
            inputs[i] = keccak256(abi.encodePacked("input", i));
            outputs[i] = keccak256(abi.encodePacked("output", i));
        }

        vm.prank(executor);
        bytes32 batchId = verifier.registerBatch(modelId, inputs, outputs);

        assertNotEq(batchId, bytes32(0));

        (
            bytes32 storedModelId,
            uint256 batchSize,
            uint256 timestamp,
            address storedExecutor,
            bytes32 merkleRoot
        ) = verifier.getBatch(batchId);

        assertEq(storedModelId, modelId);
        assertEq(batchSize, 3);
        assertGt(timestamp, 0);
        assertEq(storedExecutor, executor);
        assertNotEq(merkleRoot, bytes32(0));

        // Verify count
        uint256 count = verifier.getModelComputationCount(modelId);
        assertEq(count, 3);
    }

    function test_BatchVerification_O1() public {
        bytes32[] memory inputs = new bytes32[](3);
        bytes32[] memory outputs = new bytes32[](3);

        for (uint256 i = 0; i < 3; i++) {
            inputs[i] = keccak256(abi.encodePacked("input", i));
            outputs[i] = keccak256(abi.encodePacked("output", i));
        }

        vm.prank(executor);
        bytes32 batchId = verifier.registerBatch(modelId, inputs, outputs);

        // Verify each computation from batch with O(1) lookup
        for (uint256 i = 0; i < 3; i++) {
            (bool valid, bytes32 foundId) = verifier.verifyOutput(modelId, inputs[i], outputs[i]);
            assertTrue(valid);
            assertEq(foundId, batchId);
        }
    }

    function test_RevertWhen_EmptyBatch() public {
        bytes32[] memory inputs = new bytes32[](0);
        bytes32[] memory outputs = new bytes32[](0);

        vm.prank(executor);
        vm.expectRevert(ComputationVerifierV2.EmptyBatch.selector);
        verifier.registerBatch(modelId, inputs, outputs);
    }

    function test_RevertWhen_ArrayLengthMismatch() public {
        bytes32[] memory inputs = new bytes32[](3);
        bytes32[] memory outputs = new bytes32[](2);

        vm.prank(executor);
        vm.expectRevert(ComputationVerifierV2.ArrayLengthMismatch.selector);
        verifier.registerBatch(modelId, inputs, outputs);
    }

    function test_RevertWhen_BatchTooLarge() public {
        bytes32[] memory inputs = new bytes32[](1001);
        bytes32[] memory outputs = new bytes32[](1001);

        vm.prank(executor);
        vm.expectRevert(abi.encodeWithSelector(ComputationVerifierV2.BatchTooLarge.selector, 1001, 1000));
        verifier.registerBatch(modelId, inputs, outputs);
    }

    // ============ Verification Tests ============

    function test_VerifyComputation() public {
        vm.prank(executor);
        bytes32 computationId = verifier.registerComputation(modelId, bytes32(0), bytes32(0), bytes32(0));

        vm.prank(trustedVerifier);
        verifier.verifyComputation(computationId, true);

        (,,,,,, bool verified) = verifier.getComputation(computationId);
        assertTrue(verified);
    }

    function test_RevertWhen_UntrustedVerifierVerifies() public {
        vm.prank(executor);
        bytes32 computationId = verifier.registerComputation(modelId, bytes32(0), bytes32(0), bytes32(0));

        vm.prank(executor);
        vm.expectRevert(abi.encodeWithSelector(ComputationVerifierV2.NotTrustedVerifier.selector, executor));
        verifier.verifyComputation(computationId, true);
    }

    function test_RevertWhen_VerifyingNonExistent() public {
        bytes32 fakeId = keccak256("fake");

        vm.prank(trustedVerifier);
        vm.expectRevert(abi.encodeWithSelector(ComputationVerifierV2.ComputationNotFound.selector, fakeId));
        verifier.verifyComputation(fakeId, true);
    }

    // ============ Verifier Management Tests ============

    function test_AddAndRemoveVerifier() public {
        address newVerifier = address(0x999);

        verifier.addVerifier(newVerifier);
        assertTrue(verifier.trustedVerifiers(newVerifier));

        verifier.removeVerifier(newVerifier);
        assertFalse(verifier.trustedVerifiers(newVerifier));
    }

    function test_RevertWhen_AddingZeroAddressVerifier() public {
        vm.expectRevert(ComputationVerifierV2.ZeroAddress.selector);
        verifier.addVerifier(address(0));
    }

    // ============ Pagination Tests ============

    function test_GetExecutorComputationsPaginated() public {
        // Register 10 computations
        for (uint256 i = 0; i < 10; i++) {
            vm.prank(executor);
            verifier.registerComputation(modelId, bytes32(i), bytes32(i + 100), bytes32(0));
        }

        uint256 count = verifier.getExecutorComputationCount(executor);
        assertEq(count, 10);

        // Get first 5
        bytes32[] memory page1 = verifier.getExecutorComputationsPaginated(executor, 0, 5);
        assertEq(page1.length, 5);

        // Get next 5
        bytes32[] memory page2 = verifier.getExecutorComputationsPaginated(executor, 5, 5);
        assertEq(page2.length, 5);

        // Out of bounds
        bytes32[] memory empty = verifier.getExecutorComputationsPaginated(executor, 100, 5);
        assertEq(empty.length, 0);
    }

    // ============ Pause Tests ============

    function test_Pause() public {
        verifier.pause();

        vm.prank(executor);
        vm.expectRevert();
        verifier.registerComputation(modelId, bytes32(0), bytes32(0), bytes32(0));

        verifier.unpause();

        vm.prank(executor);
        verifier.registerComputation(modelId, bytes32(0), bytes32(0), bytes32(0));
    }

    // ============ Fuzz Tests ============

    function testFuzz_RegisterComputation(
        bytes32 inputHash,
        bytes32 outputHash,
        bytes32 proofHash
    ) public {
        vm.prank(executor);
        bytes32 computationId = verifier.registerComputation(modelId, inputHash, outputHash, proofHash);

        assertNotEq(computationId, bytes32(0));

        // Verify O(1) lookup works
        (bool valid,) = verifier.verifyOutput(modelId, inputHash, outputHash);
        assertTrue(valid);
    }

    function testFuzz_BatchRegistration(uint8 batchSize) public {
        vm.assume(batchSize > 0 && batchSize <= 100); // Reasonable bound for test

        bytes32[] memory inputs = new bytes32[](batchSize);
        bytes32[] memory outputs = new bytes32[](batchSize);

        for (uint256 i = 0; i < batchSize; i++) {
            inputs[i] = keccak256(abi.encodePacked("fuzz_input", i));
            outputs[i] = keccak256(abi.encodePacked("fuzz_output", i));
        }

        vm.prank(executor);
        bytes32 batchId = verifier.registerBatch(modelId, inputs, outputs);

        (,uint256 storedSize,,,) = verifier.getBatch(batchId);
        assertEq(storedSize, batchSize);
    }
}
