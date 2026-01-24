// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.20;

import "forge-std/Test.sol";
import "../src/v2/ConsortiumGovernanceV2.sol";

contract ConsortiumGovernanceV2Test is Test {
    ConsortiumGovernanceV2 public governance;

    address public owner = address(this);
    address public member1 = address(0x1);
    address public member2 = address(0x2);
    address public nonMember = address(0x3);

    bytes32 public consortiumId;

    event ConsortiumCreated(bytes32 indexed consortiumId, string name, address indexed owner);
    event MemberAdded(bytes32 indexed consortiumId, address indexed member, ConsortiumGovernanceV2.MemberStatus status);
    event ContributionRecorded(bytes32 indexed consortiumId, bytes32 indexed contributionId, address indexed contributor, uint256 recordCount);
    event RewardsAllocated(bytes32 indexed consortiumId, uint256 totalAmount, uint256 memberCount);
    event RewardWithdrawn(bytes32 indexed consortiumId, address indexed member, uint256 amount);

    function setUp() public {
        governance = new ConsortiumGovernanceV2();

        // Create a consortium
        consortiumId = governance.createConsortium(
            "Test Consortium",
            51,  // 51% quorum
            1 hours, // voting duration
            bytes32(uint256(1)) // model config hash
        );
    }

    // ============ Consortium Creation Tests ============

    function test_CreateConsortium() public {
        bytes32 newId = governance.createConsortium(
            "New Consortium",
            60,
            2 hours,
            bytes32(uint256(2))
        );

        (
            string memory name,
            address consortiumOwner,
            ConsortiumGovernanceV2.ConsortiumStatus status,
            uint256 memberCount,
            ,
            uint256 minVotingQuorum,
            uint256 votingDuration
        ) = governance.getConsortium(newId);

        assertEq(name, "New Consortium");
        assertEq(consortiumOwner, address(this));
        assertEq(uint256(status), uint256(ConsortiumGovernanceV2.ConsortiumStatus.Active));
        assertEq(memberCount, 1);
        assertEq(minVotingQuorum, 60);
        assertEq(votingDuration, 2 hours);
    }

    function test_RevertWhen_EmptyName() public {
        vm.expectRevert(ConsortiumGovernanceV2.InvalidName.selector);
        governance.createConsortium("", 51, 1 hours, bytes32(0));
    }

    function test_RevertWhen_InvalidQuorum() public {
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.InvalidQuorum.selector, 0));
        governance.createConsortium("Test", 0, 1 hours, bytes32(0));

        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.InvalidQuorum.selector, 101));
        governance.createConsortium("Test", 101, 1 hours, bytes32(0));
    }

    function test_RevertWhen_InvalidVotingDuration() public {
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.InvalidVotingDuration.selector, 30 minutes));
        governance.createConsortium("Test", 51, 30 minutes, bytes32(0));
    }

    // ============ Member Management Tests ============

    function test_AddMember() public {
        governance.addMember(consortiumId, member1);

        (
            ConsortiumGovernanceV2.MemberStatus status,
            uint256 joinedAt,
            ,
            ,

        ) = governance.getMember(consortiumId, member1);

        assertEq(uint256(status), uint256(ConsortiumGovernanceV2.MemberStatus.Active));
        assertGt(joinedAt, 0);
    }

    function test_RevertWhen_AddingZeroAddress() public {
        vm.expectRevert(ConsortiumGovernanceV2.ZeroAddress.selector);
        governance.addMember(consortiumId, address(0));
    }

    function test_RevertWhen_MemberAlreadyExists() public {
        governance.addMember(consortiumId, member1);

        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.MemberAlreadyExists.selector, member1));
        governance.addMember(consortiumId, member1);
    }

    function test_RevertWhen_NonOwnerAddsMember() public {
        vm.prank(member1);
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.NotConsortiumOwner.selector, member1));
        governance.addMember(consortiumId, member2);
    }

    // ============ Contribution Tests ============

    function test_RecordContribution() public {
        bytes32 dataHash = keccak256("encrypted_data");
        bytes32 checksumHash = keccak256("checksum");

        bytes32 contributionId = governance.recordContribution(
            consortiumId,
            100, // recordCount
            10,  // featureCount
            dataHash,
            checksumHash
        );

        assertNotEq(contributionId, bytes32(0));

        (
            ,
            ,
            uint256 contributionCount,
            uint256 contributionWeight,

        ) = governance.getMember(consortiumId, address(this));

        assertEq(contributionCount, 100);
        assertEq(contributionWeight, 10000); // 100% since only member
    }

    function test_RevertWhen_ZeroRecordCount() public {
        vm.expectRevert(ConsortiumGovernanceV2.InvalidRecordCount.selector);
        governance.recordContribution(consortiumId, 0, 10, bytes32(0), bytes32(0));
    }

    function test_RevertWhen_NonMemberContributes() public {
        vm.prank(nonMember);
        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.NotActiveMember.selector, nonMember));
        governance.recordContribution(consortiumId, 100, 10, bytes32(0), bytes32(0));
    }

    // ============ Reward Distribution Tests (Pull Pattern) ============

    function test_AllocateAndWithdrawRewards() public {
        // Add member and make contributions
        governance.addMember(consortiumId, member1);

        vm.prank(member1);
        governance.recordContribution(consortiumId, 100, 10, bytes32(0), bytes32(0));

        // Allocate rewards
        governance.allocateRewards{value: 1 ether}(consortiumId);

        // Check pending withdrawal
        uint256 pending = governance.getPendingWithdrawal(consortiumId, member1);
        assertEq(pending, 1 ether); // member1 has 100% weight

        // Withdraw
        uint256 balanceBefore = member1.balance;
        vm.prank(member1);
        governance.withdrawRewards(consortiumId);

        assertEq(member1.balance - balanceBefore, 1 ether);
        assertEq(governance.getPendingWithdrawal(consortiumId, member1), 0);
    }

    function test_RevertWhen_NoRewardsToClaim() public {
        vm.prank(member1);
        vm.expectRevert(ConsortiumGovernanceV2.NoRewardsToClaim.selector);
        governance.withdrawRewards(consortiumId);
    }

    // ============ Voting Tests ============

    function test_CreateAndVoteOnProposal() public {
        governance.addMember(consortiumId, member1);

        // Make contributions so votes have weight
        governance.recordContribution(consortiumId, 50, 10, bytes32(0), bytes32(0));
        vm.prank(member1);
        governance.recordContribution(consortiumId, 50, 10, bytes32(0), bytes32(0));

        // Create proposal
        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(uint256(999)))
        );

        // Vote
        governance.vote(proposalId, true);
        vm.prank(member1);
        governance.vote(proposalId, true);

        // Fast forward past voting period
        vm.warp(block.timestamp + 2 hours);

        // Execute
        governance.executeProposal(proposalId);

        // Verify proposal passed - check executed flag via direct struct access
        (,,,, ConsortiumGovernanceV2.ProposalStatus status,,,,,,, bool executed) = governance.proposals(proposalId);
        assertEq(uint256(status), uint256(ConsortiumGovernanceV2.ProposalStatus.Passed));
        assertTrue(executed);
    }

    function test_RevertWhen_VotingTwice() public {
        bytes32 proposalId = governance.createProposal(
            consortiumId,
            ConsortiumGovernanceV2.ProposalType.UpdateConfig,
            abi.encode(bytes32(0))
        );

        governance.vote(proposalId, true);

        vm.expectRevert(abi.encodeWithSelector(ConsortiumGovernanceV2.AlreadyVoted.selector, address(this)));
        governance.vote(proposalId, false);
    }

    // ============ Pause Tests ============

    function test_Pause() public {
        governance.pause();

        vm.expectRevert();
        governance.createConsortium("Paused", 51, 1 hours, bytes32(0));

        governance.unpause();

        // Should work now
        governance.createConsortium("Unpaused", 51, 1 hours, bytes32(0));
    }

    // ============ Audit Trail Tests ============

    function test_AuditTrailIntegrity() public {
        governance.addMember(consortiumId, member1);
        governance.recordContribution(consortiumId, 100, 10, bytes32(0), bytes32(0));

        uint256 trailLength = governance.getAuditTrailLength(consortiumId);
        assertGt(trailLength, 0);

        bool valid = governance.verifyAuditTrail(consortiumId);
        assertTrue(valid);
    }

    // ============ Fuzz Tests ============

    function testFuzz_CreateConsortium(
        string memory name,
        uint256 quorum,
        uint256 duration
    ) public {
        // Bound inputs to valid ranges
        vm.assume(bytes(name).length > 0 && bytes(name).length <= 128);
        quorum = bound(quorum, 1, 100);
        duration = bound(duration, 1 hours, 30 days);

        bytes32 id = governance.createConsortium(name, quorum, duration, bytes32(0));
        assertNotEq(id, bytes32(0));
    }

    function testFuzz_RecordContribution(uint256 recordCount, uint256 featureCount) public {
        recordCount = bound(recordCount, 1, type(uint128).max);
        featureCount = bound(featureCount, 1, 1000);

        bytes32 contributionId = governance.recordContribution(
            consortiumId,
            recordCount,
            featureCount,
            bytes32(0),
            bytes32(0)
        );

        assertNotEq(contributionId, bytes32(0));
    }

    // ============ Helper Functions ============

    receive() external payable {}
}
