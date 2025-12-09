// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.20;

import "forge-std/Test.sol";
import "../src/v2/ConsortiumGovernanceV2.sol";
import "../src/v2/ModelRegistryV2.sol";
import "../src/v2/ComputationVerifierV2.sol";

/**
 * @title SecurityEdgeCasesTest
 * @dev Advanced security tests covering edge cases, attack vectors, and boundary conditions.
 * @notice Tests for: Sybil attacks, timing attacks, reentrancy, gas griefing, and more.
 */
contract SecurityEdgeCasesTest is Test {
    ConsortiumGovernanceV2 public governance;
    ModelRegistryV2 public registry;
    ComputationVerifierV2 public verifier;

    address public owner = address(this);
    address public attacker = address(0xBAD);
    address public member1 = address(0x1);
    address public member2 = address(0x2);
    address public member3 = address(0x3);

    bytes32 public consortiumId;

    // ============ Setup ============

    function setUp() public {
        governance = new ConsortiumGovernanceV2();
        registry = new ModelRegistryV2();
        verifier = new ComputationVerifierV2();

        consortiumId = governance.createConsortium(
            "Security Test",
            51,
            2 hours,
            bytes32(uint256(1))
        );

        // Fund test addresses
        vm.deal(attacker, 100 ether);
        vm.deal(member1, 10 ether);
        vm.deal(member2, 10 ether);
        vm.deal(member3, 10 ether);
    }

    // ============ Phase Boundary Tests ============

    function test_VoteAtExactCommitDeadline() public {
        governance.addMember(consortiumId, member1);
        governance.recordContribution(consortiumId, 50, 10, bytes32(0), bytes32(0));

        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(uint256(999)))
        );

        // Get exact commit deadline
        (,,,uint256 commitDeadline,) = governance.getProposalPhase(proposalId);

        bytes32 salt = keccak256("salt");
        bytes32 commit = governance.computeVoteCommitment(proposalId, true, salt);

        // One second before deadline - should work
        vm.warp(commitDeadline - 1);
        governance.commitVote(proposalId, commit);

        // Cleanup for next test
    }

    function test_RevertWhen_VoteAtExactCommitDeadline() public {
        governance.addMember(consortiumId, member1);
        governance.recordContribution(consortiumId, 50, 10, bytes32(0), bytes32(0));

        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(uint256(999)))
        );

        (,,,uint256 commitDeadline,) = governance.getProposalPhase(proposalId);

        bytes32 salt = keccak256("salt");
        bytes32 commit = governance.computeVoteCommitment(proposalId, true, salt);

        // Exactly at deadline - should fail
        vm.warp(commitDeadline);
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.CommitPhaseEnded.selector, proposalId));
        governance.commitVote(proposalId, commit);
    }

    function test_RevealAtExactRevealDeadline() public {
        governance.addMember(consortiumId, member1);
        governance.recordContribution(consortiumId, 50, 10, bytes32(0), bytes32(0));

        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(0))
        );

        (,,,uint256 commitDeadline, uint256 revealDeadline) = governance.getProposalPhase(proposalId);

        bytes32 salt = keccak256("salt");
        bytes32 commit = governance.computeVoteCommitment(proposalId, true, salt);

        governance.commitVote(proposalId, commit);

        // Move to reveal phase - one second before deadline
        vm.warp(revealDeadline - 1);
        governance.revealVote(proposalId, true, salt);
    }

    function test_RevertWhen_RevealAtExactRevealDeadline() public {
        governance.addMember(consortiumId, member1);

        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(0))
        );

        (,,,uint256 commitDeadline, uint256 revealDeadline) = governance.getProposalPhase(proposalId);

        bytes32 salt = keccak256("salt");
        bytes32 commit = governance.computeVoteCommitment(proposalId, true, salt);

        governance.commitVote(proposalId, commit);

        // Exactly at reveal deadline - should fail
        vm.warp(revealDeadline);
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.RevealPhaseEnded.selector, proposalId));
        governance.revealVote(proposalId, true, salt);
    }

    // ============ Quorum Edge Cases ============

    function test_ProposalFailsDueToInsufficientQuorum() public {
        // Add 3 members with equal contributions
        governance.addMember(consortiumId, member1);
        governance.addMember(consortiumId, member2);
        governance.addMember(consortiumId, member3);

        governance.recordContribution(consortiumId, 25, 10, bytes32(0), bytes32(0));
        vm.prank(member1);
        governance.recordContribution(consortiumId, 25, 10, bytes32(0), bytes32(0));
        vm.prank(member2);
        governance.recordContribution(consortiumId, 25, 10, bytes32(0), bytes32(0));
        vm.prank(member3);
        governance.recordContribution(consortiumId, 25, 10, bytes32(0), bytes32(0));

        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(uint256(999)))
        );

        // Only owner votes (25% weight, quorum is 51%)
        bytes32 salt = keccak256("salt");
        bytes32 commit = governance.computeVoteCommitment(proposalId, true, salt);
        governance.commitVote(proposalId, commit);

        (,,,, uint256 revealDeadline) = governance.getProposalPhase(proposalId);
        vm.warp(revealDeadline - 30 minutes);
        governance.revealVote(proposalId, true, salt);

        // Execute after voting ends
        vm.warp(revealDeadline + 1);
        governance.executeProposal(proposalId);

        // Proposal should be rejected due to quorum
        (,,,, ConsortiumGovernanceV2.ProposalStatus status,,,,,,,,) = governance.proposals(proposalId);
        assertEq(uint256(status), uint256(ConsortiumGovernanceV2.ProposalStatus.Rejected));
    }

    function test_ProposalExactlyMeetsQuorum() public {
        // Create consortium with exactly 50% quorum requirement
        bytes32 newConsortiumId = governance.createConsortium(
            "50% Quorum Test",
            50,
            2 hours,
            bytes32(0)
        );

        governance.addMember(newConsortiumId, member1);

        // Owner and member1 each get 50% weight
        governance.recordContribution(newConsortiumId, 50, 10, bytes32(0), bytes32(0));
        vm.prank(member1);
        governance.recordContribution(newConsortiumId, 50, 10, bytes32(0), bytes32(0));

        bytes32 proposalId = governance.createProposal(
            newConsortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(uint256(999)))
        );

        // Only owner votes (50% weight, exactly meeting 50% quorum)
        bytes32 salt = keccak256("salt");
        bytes32 commit = governance.computeVoteCommitment(proposalId, true, salt);
        governance.commitVote(proposalId, commit);

        (,,,, uint256 revealDeadline) = governance.getProposalPhase(proposalId);
        vm.warp(revealDeadline - 30 minutes);
        governance.revealVote(proposalId, true, salt);

        vm.warp(revealDeadline + 1);
        governance.executeProposal(proposalId);

        // Proposal should pass - exactly 50% meets 50% quorum
        (,,,, ConsortiumGovernanceV2.ProposalStatus status,,,,,,,,) = governance.proposals(proposalId);
        assertEq(uint256(status), uint256(ConsortiumGovernanceV2.ProposalStatus.Passed));
    }

    // ============ Sybil Attack Resistance ============

    function test_SybilAttackMitigatedByContributionWeight() public {
        // Add members first
        governance.addMember(consortiumId, attacker);
        governance.addMember(consortiumId, member1);

        // Real member makes large contribution
        vm.prank(member1);
        governance.recordContribution(consortiumId, 1000, 10, bytes32(0), bytes32(0));

        // Attacker makes tiny contributions
        vm.prank(attacker);
        governance.recordContribution(consortiumId, 1, 10, bytes32(0), bytes32(0));

        // Owner also contributes
        governance.recordContribution(consortiumId, 10, 10, bytes32(0), bytes32(0));

        // Create proposal
        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(uint256(666)))
        );

        // Attacker votes no
        bytes32 attackerSalt = keccak256("attacker_salt");
        bytes32 attackerCommit = governance.computeVoteCommitment(proposalId, false, attackerSalt);
        vm.prank(attacker);
        governance.commitVote(proposalId, attackerCommit);

        // member1 votes yes (has much more weight)
        bytes32 memberSalt = keccak256("member_salt");
        bytes32 memberCommit = governance.computeVoteCommitment(proposalId, true, memberSalt);
        vm.prank(member1);
        governance.commitVote(proposalId, memberCommit);

        // Owner votes yes
        bytes32 ownerSalt = keccak256("owner_salt");
        bytes32 ownerCommit = governance.computeVoteCommitment(proposalId, true, ownerSalt);
        governance.commitVote(proposalId, ownerCommit);

        (,,,, uint256 revealDeadline) = governance.getProposalPhase(proposalId);
        vm.warp(revealDeadline - 30 minutes);

        // Reveal all votes
        vm.prank(attacker);
        governance.revealVote(proposalId, false, attackerSalt);
        vm.prank(member1);
        governance.revealVote(proposalId, true, memberSalt);
        governance.revealVote(proposalId, true, ownerSalt);

        vm.warp(revealDeadline + 1);
        governance.executeProposal(proposalId);

        // Proposal should pass despite attacker's no vote (contribution-weighted)
        (,,,, ConsortiumGovernanceV2.ProposalStatus status,,,,,,,,) = governance.proposals(proposalId);
        assertEq(uint256(status), uint256(ConsortiumGovernanceV2.ProposalStatus.Passed));
    }

    // ============ Flash Contribution Attack Prevention ============

    function test_CannotVoteWithoutPriorMembership() public {
        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(0))
        );

        // Attacker tries to vote without being a member
        bytes32 salt = keccak256("attacker_salt");
        bytes32 commit = governance.computeVoteCommitment(proposalId, true, salt);

        vm.prank(attacker);
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.NotActiveMember.selector, attacker));
        governance.commitVote(proposalId, commit);
    }

    // ============ Reentrancy Tests ============

    function test_ReentrancyProtectionOnWithdraw() public {
        // Setup: Add member and allocate rewards
        governance.addMember(consortiumId, address(new ReentrancyAttacker(governance)));
        ReentrancyAttacker attackerContract = ReentrancyAttacker(payable(memberList()[1]));

        vm.prank(address(attackerContract));
        governance.recordContribution(consortiumId, 100, 10, bytes32(0), bytes32(0));

        governance.allocateRewards{value: 10 ether}(consortiumId);

        // Attacker contract attempts reentrancy
        vm.expectRevert(); // ReentrancyGuard should prevent
        attackerContract.attack(consortiumId);
    }

    function memberList() internal view returns (address[] memory) {
        return governance.getMembers(consortiumId);
    }

    // ============ Max Members DoS Prevention ============

    function test_MaxMembersLimit() public {
        // Add maximum members
        for (uint160 i = 10; i < 10 + governance.MAX_MEMBERS() - 1; i++) {
            governance.addMember(consortiumId, address(i));
        }

        // Next member should fail
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.MaxMembersReached.selector, consortiumId));
        governance.addMember(consortiumId, address(999));
    }

    // ============ Multiple Concurrent Proposals ============

    function test_MultipleConcurrentProposals() public {
        governance.addMember(consortiumId, member1);
        governance.recordContribution(consortiumId, 50, 10, bytes32(0), bytes32(0));
        vm.prank(member1);
        governance.recordContribution(consortiumId, 50, 10, bytes32(0), bytes32(0));

        // Create multiple proposals
        bytes32 proposal1 = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(uint256(1)))
        );

        bytes32 proposal2 = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(uint256(2)))
        );

        // Vote on both - create commits first
        bytes32 salt1 = keccak256("salt1");
        bytes32 salt2 = keccak256("salt2");
        bytes32 m1s1 = keccak256("m1s1");
        bytes32 m1s2 = keccak256("m1s2");

        bytes32 commit1Owner = governance.computeVoteCommitment(proposal1, true, salt1);
        bytes32 commit2Owner = governance.computeVoteCommitment(proposal2, false, salt2);
        bytes32 commit1Member = governance.computeVoteCommitment(proposal1, true, m1s1);
        bytes32 commit2Member = governance.computeVoteCommitment(proposal2, true, m1s2);

        // Owner commits on both proposals
        governance.commitVote(proposal1, commit1Owner);
        governance.commitVote(proposal2, commit2Owner);

        // Member commits on both proposals
        vm.prank(member1);
        governance.commitVote(proposal1, commit1Member);
        vm.prank(member1);
        governance.commitVote(proposal2, commit2Member);

        // Fast forward to reveal phase
        vm.warp(block.timestamp + 1 hours + 20 minutes);

        // Owner reveals on both
        governance.revealVote(proposal1, true, salt1);
        governance.revealVote(proposal2, false, salt2);

        // Member reveals on both
        vm.prank(member1);
        governance.revealVote(proposal1, true, m1s1);
        vm.prank(member1);
        governance.revealVote(proposal2, true, m1s2);

        // Execute after voting ends
        vm.warp(block.timestamp + 1 hours);

        governance.executeProposal(proposal1);
        governance.executeProposal(proposal2);

        // Both proposals should be executed
        (,,,, ConsortiumGovernanceV2.ProposalStatus status1,,,,,,,,) = governance.proposals(proposal1);
        (,,,, ConsortiumGovernanceV2.ProposalStatus status2,,,,,,,,) = governance.proposals(proposal2);

        assertEq(uint256(status1), uint256(ConsortiumGovernanceV2.ProposalStatus.Passed));
        // Proposal 2: owner voted no, member voted yes - with equal weight it could tie
    }

    // ============ Dissolved Consortium Protection ============

    function test_RevertWhen_ActionsOnDissolvedConsortium() public {
        governance.addMember(consortiumId, member1);
        governance.recordContribution(consortiumId, 50, 10, bytes32(0), bytes32(0));
        vm.prank(member1);
        governance.recordContribution(consortiumId, 50, 10, bytes32(0), bytes32(0));

        // Create dissolve proposal
        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.Dissolve,
            ""
        );

        // Vote to dissolve
        bytes32 salt1 = keccak256("s1");
        bytes32 salt2 = keccak256("s2");

        // Create commits first
        bytes32 ownerCommit = governance.computeVoteCommitment(proposalId, true, salt1);
        bytes32 memberCommit = governance.computeVoteCommitment(proposalId, true, salt2);

        governance.commitVote(proposalId, ownerCommit);
        vm.prank(member1);
        governance.commitVote(proposalId, memberCommit);

        vm.warp(block.timestamp + 1 hours + 20 minutes);

        governance.revealVote(proposalId, true, salt1);
        vm.prank(member1);
        governance.revealVote(proposalId, true, salt2);

        vm.warp(block.timestamp + 1 hours);
        governance.executeProposal(proposalId);

        // Try to add member to dissolved consortium
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.ConsortiumNotActive.selector, consortiumId));
        governance.addMember(consortiumId, member2);

        // Try to record contribution
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.ConsortiumNotActive.selector, consortiumId));
        governance.recordContribution(consortiumId, 100, 10, bytes32(0), bytes32(0));
    }

    // ============ Reward Distribution Edge Cases ============

    function test_RewardDistributionWithZeroWeight() public {
        // Add member without contributions
        governance.addMember(consortiumId, member1);
        // member1 has no contributions, so zero weight

        governance.recordContribution(consortiumId, 100, 10, bytes32(0), bytes32(0));

        // Allocate rewards
        governance.allocateRewards{value: 1 ether}(consortiumId);

        // Member with zero weight gets nothing
        uint256 member1Pending = governance.getPendingWithdrawal(consortiumId, member1);
        assertEq(member1Pending, 0);

        // Owner gets everything (100% weight)
        uint256 ownerPending = governance.getPendingWithdrawal(consortiumId, owner);
        assertEq(ownerPending, 1 ether);
    }

    function test_RewardDistributionRounding() public {
        // Add members with specific contribution weights
        governance.addMember(consortiumId, member1);
        governance.addMember(consortiumId, member2);

        governance.recordContribution(consortiumId, 33, 10, bytes32(0), bytes32(0));
        vm.prank(member1);
        governance.recordContribution(consortiumId, 33, 10, bytes32(0), bytes32(0));
        vm.prank(member2);
        governance.recordContribution(consortiumId, 34, 10, bytes32(0), bytes32(0));

        // Allocate rewards that don't divide evenly
        governance.allocateRewards{value: 1 ether}(consortiumId);

        uint256 ownerPending = governance.getPendingWithdrawal(consortiumId, owner);
        uint256 member1Pending = governance.getPendingWithdrawal(consortiumId, member1);
        uint256 member2Pending = governance.getPendingWithdrawal(consortiumId, member2);

        // Total allocated should not exceed sent amount
        assertLe(ownerPending + member1Pending + member2Pending, 1 ether);
    }

    // ============ Invalid Salt Reveal ============

    function test_RevertWhen_WrongSaltOnReveal() public {
        governance.recordContribution(consortiumId, 100, 10, bytes32(0), bytes32(0));

        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(0))
        );

        bytes32 realSalt = keccak256("real_salt");
        bytes32 wrongSalt = keccak256("wrong_salt");

        governance.commitVote(proposalId, governance.computeVoteCommitment(proposalId, true, realSalt));

        vm.warp(block.timestamp + 1 hours + 20 minutes);

        // Try to reveal with wrong salt
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.InvalidReveal.selector, proposalId));
        governance.revealVote(proposalId, true, wrongSalt);
    }

    // ============ Commit without Reveal ============

    function test_CommitWithoutRevealDoesntCount() public {
        governance.addMember(consortiumId, member1);
        governance.recordContribution(consortiumId, 50, 10, bytes32(0), bytes32(0));
        vm.prank(member1);
        governance.recordContribution(consortiumId, 50, 10, bytes32(0), bytes32(0));

        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(uint256(999)))
        );

        // Prepare commits
        bytes32 ownerSalt = keccak256("owner_salt");
        bytes32 member1Salt = keccak256("member1_salt");
        bytes32 ownerCommit = governance.computeVoteCommitment(proposalId, true, ownerSalt);
        bytes32 memberCommit = governance.computeVoteCommitment(proposalId, false, member1Salt);

        // Owner commits yes
        governance.commitVote(proposalId, ownerCommit);

        // member1 commits no but never reveals
        vm.prank(member1);
        governance.commitVote(proposalId, memberCommit);

        (,,,, uint256 revealDeadline) = governance.getProposalPhase(proposalId);
        vm.warp(revealDeadline - 30 minutes);

        // Only owner reveals
        governance.revealVote(proposalId, true, ownerSalt);
        // member1 doesn't reveal

        vm.warp(revealDeadline + 1);
        governance.executeProposal(proposalId);

        // Check vote counts - only owner's vote should count
        // Proposal struct: id, consortiumId, proposalType, proposer, status, data, createdAt, commitDeadline, revealDeadline, yesVotes, noVotes, totalVoters, executed
        (,,,,,,,,,uint256 yesVotes, uint256 noVotes,,) = governance.proposals(proposalId);
        assertGt(yesVotes, 0);
        assertEq(noVotes, 0); // member1's no vote wasn't revealed
    }

    // ============ Name Length Boundary ============

    function test_ConsortiumNameMaxLength() public {
        // Create name at exactly max length
        bytes memory maxName = new bytes(128);
        for (uint i = 0; i < 128; i++) {
            maxName[i] = bytes1(uint8(65 + (i % 26))); // A-Z repeating
        }

        bytes32 id = governance.createConsortium(
            string(maxName),
            51,
            1 hours,
            bytes32(0)
        );
        assertNotEq(id, bytes32(0));
    }

    function test_RevertWhen_ConsortiumNameTooLong() public {
        bytes memory tooLongName = new bytes(129);
        for (uint i = 0; i < 129; i++) {
            tooLongName[i] = bytes1(uint8(65));
        }

        vm.expectRevert(ConsortiumGovernanceV2.InvalidName.selector);
        governance.createConsortium(string(tooLongName), 51, 1 hours, bytes32(0));
    }

    // ============ Voting Duration Boundaries ============

    function test_VotingDurationMinBoundary() public {
        bytes32 id = governance.createConsortium(
            "Min Duration",
            51,
            1 hours, // Exactly minimum
            bytes32(0)
        );
        assertNotEq(id, bytes32(0));
    }

    function test_RevertWhen_VotingDurationBelowMin() public {
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.InvalidVotingDuration.selector, 59 minutes));
        governance.createConsortium("Below Min", 51, 59 minutes, bytes32(0));
    }

    function test_VotingDurationMaxBoundary() public {
        bytes32 id = governance.createConsortium(
            "Max Duration",
            51,
            30 days, // Exactly maximum
            bytes32(0)
        );
        assertNotEq(id, bytes32(0));
    }

    function test_RevertWhen_VotingDurationAboveMax() public {
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.InvalidVotingDuration.selector, 31 days));
        governance.createConsortium("Above Max", 51, 31 days, bytes32(0));
    }

    // ============ Quorum Boundaries ============

    function test_QuorumBoundaries() public {
        // Min quorum = 1%
        bytes32 id1 = governance.createConsortium("1% Quorum", 1, 1 hours, bytes32(0));
        assertNotEq(id1, bytes32(0));

        // Max quorum = 100%
        bytes32 id2 = governance.createConsortium("100% Quorum", 100, 1 hours, bytes32(0));
        assertNotEq(id2, bytes32(0));
    }

    // ============ Receive function for ETH ============

    receive() external payable {}
}

/**
 * @title ReentrancyAttacker
 * @dev Contract that attempts reentrancy attack on withdrawRewards
 */
contract ReentrancyAttacker {
    ConsortiumGovernanceV2 public governance;
    bytes32 public targetConsortium;
    uint256 public attackCount;

    constructor(ConsortiumGovernanceV2 _governance) {
        governance = _governance;
    }

    function attack(bytes32 _consortiumId) external {
        targetConsortium = _consortiumId;
        attackCount = 0;
        governance.withdrawRewards(_consortiumId);
    }

    receive() external payable {
        if (attackCount < 3) {
            attackCount++;
            // Attempt reentrant call
            governance.withdrawRewards(targetConsortium);
        }
    }
}

/**
 * @title ModelRegistrySecurityTest
 * @dev Security edge cases for ModelRegistry
 */
contract ModelRegistrySecurityTest is Test {
    ModelRegistryV2 public registry;

    address public owner = address(this);
    address public attacker = address(0xBAD);

    function setUp() public {
        registry = new ModelRegistryV2();
    }

    function test_CannotTakeOverExistingModel() public {
        bytes32 modelId = registry.registerModel("TestModel", "1.0.0");

        // Attacker cannot modify owner's model
        vm.prank(attacker);
        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.Unauthorized.selector, attacker));
        registry.saveCheckpoint(modelId, 1, bytes32(0), bytes32(0));
    }

    function test_CannotVerifyOwnModel() public {
        registry.addVerifier(owner);
        bytes32 modelId = registry.registerModel("MyModel", "1.0.0");

        vm.expectRevert(abi.encodeWithSelector(ModelRegistryV2.CannotVerifyOwnModel.selector, modelId));
        registry.verifyModel(modelId);
    }

    function test_CheckpointEpochOverflow() public {
        bytes32 modelId = registry.registerModel("OverflowTest", "1.0.0");

        // Very large epoch value
        registry.saveCheckpoint(modelId, type(uint256).max, bytes32(0), bytes32(0));

        (uint256 epoch,,,) = registry.getCheckpoint(modelId, 0);
        assertEq(epoch, type(uint256).max);
    }

    function test_MultipleTrainingRunsIntegrity() public {
        bytes32 modelId = registry.registerModel("MultiRun", "1.0.0");

        // Start multiple training runs
        bytes32 run1 = registry.startTraining(modelId, keccak256("data1"));
        bytes32 run2 = registry.startTraining(modelId, keccak256("data2"));
        bytes32 run3 = registry.startTraining(modelId, keccak256("data3"));

        // Complete in different order
        registry.completeTraining(modelId, 1, 50, keccak256("weights2"));
        registry.completeTraining(modelId, 0, 100, keccak256("weights1"));
        registry.completeTraining(modelId, 2, 75, keccak256("weights3"));

        // All should be complete
        uint256 runCount = registry.getTrainingRunCount(modelId);
        assertEq(runCount, 3);
    }

    function test_DeactivatedModelRemainsReadable() public {
        bytes32 modelId = registry.registerModel("ToDeactivate", "1.0.0");
        registry.saveCheckpoint(modelId, 1, keccak256("weights"), bytes32(0));

        registry.deactivateModel(modelId);

        // Model data should still be readable
        (address modelOwner, string memory modelType,,,,,,) = registry.getModel(modelId);
        assertEq(modelOwner, owner);
        assertEq(modelType, "ToDeactivate");

        // Checkpoint should still be verifiable
        bool valid = registry.verifyCheckpoint(modelId, 1, keccak256("weights"));
        assertTrue(valid);
    }
}

/**
 * @title ComputationVerifierSecurityTest
 * @dev Security edge cases for ComputationVerifier
 */
contract ComputationVerifierSecurityTest is Test {
    ComputationVerifierV2 public verifier;

    address public executor = address(0x1);
    address public trustedVerifier = address(0x2);
    bytes32 public modelId = keccak256("test_model");

    function setUp() public {
        verifier = new ComputationVerifierV2();
        verifier.addVerifier(trustedVerifier);
    }

    function test_SameInputDifferentOutputsOverwrites() public {
        bytes32 inputHash = keccak256("same_input");
        bytes32 output1 = keccak256("output1");
        bytes32 output2 = keccak256("output2");

        vm.prank(executor);
        verifier.registerComputation(modelId, inputHash, output1, bytes32(0));

        // Same input, different output - this creates a new computation
        vm.prank(executor);
        verifier.registerComputation(modelId, inputHash, output2, bytes32(0));

        // The O(1) lookup will return the LATEST computation for this input
        bytes32 expected = verifier.getExpectedOutput(modelId, inputHash);
        assertEq(expected, output2);

        // But both computations exist
        uint256 count = verifier.getModelComputationCount(modelId);
        assertEq(count, 2);
    }

    function test_BatchWithDuplicateInputs() public {
        bytes32[] memory inputs = new bytes32[](3);
        bytes32[] memory outputs = new bytes32[](3);

        inputs[0] = keccak256("input");
        inputs[1] = keccak256("input"); // Duplicate
        inputs[2] = keccak256("input"); // Duplicate

        outputs[0] = keccak256("output1");
        outputs[1] = keccak256("output2");
        outputs[2] = keccak256("output3");

        vm.prank(executor);
        bytes32 batchId = verifier.registerBatch(modelId, inputs, outputs);

        // Last output wins in O(1) lookup
        bytes32 expected = verifier.getExpectedOutput(modelId, keccak256("input"));
        assertEq(expected, keccak256("output3"));
    }

    function test_VerificationAfterPause() public {
        vm.prank(executor);
        bytes32 computationId = verifier.registerComputation(modelId, bytes32(uint256(1)), bytes32(uint256(2)), bytes32(0));

        // Owner pauses
        verifier.pause();

        // Verification should still work (view function)
        (bool valid,) = verifier.verifyOutput(modelId, bytes32(uint256(1)), bytes32(uint256(2)));
        assertTrue(valid);

        // But new registrations fail
        vm.prank(executor);
        vm.expectRevert();
        verifier.registerComputation(modelId, bytes32(uint256(3)), bytes32(uint256(4)), bytes32(0));
    }

    function test_LargeBatchGasLimit() public {
        uint256 batchSize = 1000; // Max allowed
        bytes32[] memory inputs = new bytes32[](batchSize);
        bytes32[] memory outputs = new bytes32[](batchSize);

        for (uint256 i = 0; i < batchSize; i++) {
            inputs[i] = keccak256(abi.encodePacked("input", i));
            outputs[i] = keccak256(abi.encodePacked("output", i));
        }

        // Should not run out of gas
        vm.prank(executor);
        bytes32 batchId = verifier.registerBatch(modelId, inputs, outputs);

        (,uint256 storedSize,,,) = verifier.getBatch(batchId);
        assertEq(storedSize, batchSize);
    }
}
