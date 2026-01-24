// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.20;

import "@openzeppelin/contracts/access/Ownable2Step.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ConsortiumGovernanceV2
 * @dev Secure governance contract for FHE-ML consortiums.
 * @notice Version 2.0.0 - Security hardened for mainnet
 *
 * Security Improvements:
 * - Pull-over-push pattern for reward distribution (no reentrancy)
 * - Bounded member limits to prevent DoS
 * - Custom errors for gas efficiency
 * - Pausable for emergency stops
 * - Two-step ownership transfer
 */
contract ConsortiumGovernanceV2 is Ownable2Step, Pausable, ReentrancyGuard {
    // ============ Constants ============

    uint256 public constant MAX_MEMBERS = 100;
    uint256 public constant MAX_NAME_LENGTH = 128;
    uint256 public constant MIN_VOTING_DURATION = 1 hours;
    uint256 public constant MAX_VOTING_DURATION = 30 days;
    uint256 public constant WEIGHT_PRECISION = 10000;
    string public constant VERSION = "2.0.0";

    // ============ Custom Errors ============

    error ConsortiumNotFound(bytes32 consortiumId);
    error ConsortiumNotActive(bytes32 consortiumId);
    error NotConsortiumOwner(address caller);
    error NotActiveMember(address caller);
    error MemberAlreadyExists(address member);
    error MaxMembersReached(bytes32 consortiumId);
    error InvalidName();
    error InvalidQuorum(uint256 quorum);
    error InvalidVotingDuration(uint256 duration);
    error InvalidRecordCount();
    error ProposalNotFound(bytes32 proposalId);
    error VotingClosed(bytes32 proposalId);
    error VotingNotEnded(bytes32 proposalId);
    error AlreadyVoted(address voter);
    error AlreadyExecuted(bytes32 proposalId);
    error ContributionNotFound(bytes32 contributionId);
    error CannotRemoveOwner();
    error MemberNotActive(address member);
    error NoRewardsToClaim();
    error TransferFailed();
    error ZeroAddress();
    error ZeroAmount();

    // ============ Enums ============

    enum ConsortiumStatus { Active, Paused, Completed, Dissolved }
    enum MemberStatus { Pending, Active, Suspended, Removed }
    enum ProposalType { AddMember, RemoveMember, ChangeModel, StartTraining, DistributeRewards, UpdateConfig, Dissolve }
    enum ProposalStatus { Active, Passed, Rejected, Executed, Cancelled }
    enum AuditEventType { ConsortiumCreated, MemberJoined, MemberLeft, MemberRemoved, DataContributed, TrainingStarted, TrainingCompleted, ProposalCreated, ProposalVoted, ProposalExecuted, RewardsDistributed, ConfigUpdated }

    // ============ Structs ============

    struct Consortium {
        bytes32 id;
        string name;
        address owner;
        ConsortiumStatus status;
        uint256 createdAt;
        uint256 memberCount;
        uint256 totalContributions;
        uint256 minVotingQuorum;
        uint256 votingDuration;
        bytes32 modelConfigHash;
    }

    struct Member {
        address addr;
        MemberStatus status;
        uint256 joinedAt;
        uint256 contributionCount;
        uint256 contributionWeight;
        uint256 lastContributionAt;
        bytes32 latestContributionHash;
    }

    struct Contribution {
        bytes32 id;
        bytes32 consortiumId;
        address contributor;
        uint256 recordCount;
        uint256 featureCount;
        bytes32 dataHash;
        bytes32 checksumHash;
        uint256 timestamp;
        bool verified;
    }

    struct Proposal {
        bytes32 id;
        bytes32 consortiumId;
        ProposalType proposalType;
        address proposer;
        ProposalStatus status;
        bytes data;
        uint256 createdAt;
        uint256 expiresAt;
        uint256 yesVotes;
        uint256 noVotes;
        uint256 totalVoters;
        bool executed;
    }

    struct AuditEvent {
        bytes32 id;
        bytes32 consortiumId;
        AuditEventType eventType;
        address actor;
        bytes32 targetId;
        bytes data;
        uint256 timestamp;
        bytes32 previousEventHash;
    }

    // ============ State Variables ============

    mapping(bytes32 => Consortium) public consortiums;
    mapping(bytes32 => mapping(address => Member)) public members;
    mapping(bytes32 => address[]) public memberList;
    mapping(bytes32 => Contribution) public contributions;
    mapping(bytes32 => bytes32[]) public consortiumContributions;
    mapping(bytes32 => Proposal) public proposals;
    mapping(bytes32 => bytes32[]) public consortiumProposals;
    mapping(bytes32 => mapping(address => bool)) public hasVoted;
    mapping(bytes32 => mapping(address => bool)) public votes;
    mapping(bytes32 => AuditEvent[]) public auditTrail;
    mapping(bytes32 => bytes32) public lastEventHash;

    // Pull-over-push: pending withdrawals instead of direct transfers
    mapping(bytes32 => mapping(address => uint256)) public pendingWithdrawals;
    mapping(bytes32 => uint256) public totalPendingWithdrawals;

    uint256 private _consortiumCounter;
    uint256 private _contributionCounter;
    uint256 private _proposalCounter;
    uint256 private _eventCounter;

    // ============ Events ============

    event ConsortiumCreated(bytes32 indexed consortiumId, string name, address indexed owner);
    event MemberAdded(bytes32 indexed consortiumId, address indexed member, MemberStatus status);
    event MemberStatusChanged(bytes32 indexed consortiumId, address indexed member, MemberStatus oldStatus, MemberStatus newStatus);
    event ContributionRecorded(bytes32 indexed consortiumId, bytes32 indexed contributionId, address indexed contributor, uint256 recordCount);
    event ProposalCreated(bytes32 indexed consortiumId, bytes32 indexed proposalId, ProposalType proposalType, address indexed proposer);
    event VoteCast(bytes32 indexed proposalId, address indexed voter, bool vote, uint256 weight);
    event ProposalExecuted(bytes32 indexed proposalId, bool passed);
    event AuditEventRecorded(bytes32 indexed consortiumId, bytes32 indexed eventId, AuditEventType eventType);
    event RewardsAllocated(bytes32 indexed consortiumId, uint256 totalAmount, uint256 memberCount);
    event RewardWithdrawn(bytes32 indexed consortiumId, address indexed member, uint256 amount);

    // ============ Modifiers ============

    modifier consortiumExists(bytes32 consortiumId) {
        if (consortiums[consortiumId].createdAt == 0) revert ConsortiumNotFound(consortiumId);
        _;
    }

    modifier onlyConsortiumOwner(bytes32 consortiumId) {
        if (consortiums[consortiumId].owner != msg.sender) revert NotConsortiumOwner(msg.sender);
        _;
    }

    modifier onlyActiveMember(bytes32 consortiumId) {
        if (members[consortiumId][msg.sender].status != MemberStatus.Active) revert NotActiveMember(msg.sender);
        _;
    }

    modifier consortiumActive(bytes32 consortiumId) {
        if (consortiums[consortiumId].status != ConsortiumStatus.Active) revert ConsortiumNotActive(consortiumId);
        _;
    }

    // ============ Constructor ============

    constructor() Ownable(msg.sender) {}

    // ============ Admin Functions ============

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    // ============ Consortium Management ============

    function createConsortium(
        string calldata name,
        uint256 minVotingQuorum,
        uint256 votingDuration,
        bytes32 modelConfigHash
    ) external whenNotPaused nonReentrant returns (bytes32 consortiumId) {
        if (bytes(name).length == 0 || bytes(name).length > MAX_NAME_LENGTH) revert InvalidName();
        if (minVotingQuorum == 0 || minVotingQuorum > 100) revert InvalidQuorum(minVotingQuorum);
        if (votingDuration < MIN_VOTING_DURATION || votingDuration > MAX_VOTING_DURATION) {
            revert InvalidVotingDuration(votingDuration);
        }

        unchecked { ++_consortiumCounter; }

        consortiumId = keccak256(
            abi.encodePacked(msg.sender, name, block.timestamp, _consortiumCounter)
        );

        consortiums[consortiumId] = Consortium({
            id: consortiumId,
            name: name,
            owner: msg.sender,
            status: ConsortiumStatus.Active,
            createdAt: block.timestamp,
            memberCount: 1,
            totalContributions: 0,
            minVotingQuorum: minVotingQuorum,
            votingDuration: votingDuration,
            modelConfigHash: modelConfigHash
        });

        members[consortiumId][msg.sender] = Member({
            addr: msg.sender,
            status: MemberStatus.Active,
            joinedAt: block.timestamp,
            contributionCount: 0,
            contributionWeight: 0,
            lastContributionAt: 0,
            latestContributionHash: bytes32(0)
        });
        memberList[consortiumId].push(msg.sender);

        _recordAuditEvent(
            consortiumId,
            AuditEventType.ConsortiumCreated,
            msg.sender,
            consortiumId,
            abi.encode(name, modelConfigHash)
        );

        emit ConsortiumCreated(consortiumId, name, msg.sender);
        return consortiumId;
    }

    function addMember(
        bytes32 consortiumId,
        address newMember
    ) external
        whenNotPaused
        nonReentrant
        consortiumExists(consortiumId)
        onlyConsortiumOwner(consortiumId)
        consortiumActive(consortiumId)
    {
        if (newMember == address(0)) revert ZeroAddress();
        if (members[consortiumId][newMember].joinedAt != 0) revert MemberAlreadyExists(newMember);
        if (consortiums[consortiumId].memberCount >= MAX_MEMBERS) {
            revert MaxMembersReached(consortiumId);
        }

        members[consortiumId][newMember] = Member({
            addr: newMember,
            status: MemberStatus.Active,
            joinedAt: block.timestamp,
            contributionCount: 0,
            contributionWeight: 0,
            lastContributionAt: 0,
            latestContributionHash: bytes32(0)
        });
        memberList[consortiumId].push(newMember);

        unchecked {
            ++consortiums[consortiumId].memberCount;
        }

        _recordAuditEvent(
            consortiumId,
            AuditEventType.MemberJoined,
            msg.sender,
            bytes32(uint256(uint160(newMember))),
            ""
        );

        emit MemberAdded(consortiumId, newMember, MemberStatus.Active);
    }

    // ============ Contribution Recording ============

    function recordContribution(
        bytes32 consortiumId,
        uint256 recordCount,
        uint256 featureCount,
        bytes32 dataHash,
        bytes32 checksumHash
    ) external
        whenNotPaused
        nonReentrant
        consortiumExists(consortiumId)
        onlyActiveMember(consortiumId)
        consortiumActive(consortiumId)
        returns (bytes32 contributionId)
    {
        if (recordCount == 0) revert InvalidRecordCount();

        unchecked { ++_contributionCounter; }

        contributionId = keccak256(
            abi.encodePacked(consortiumId, msg.sender, block.timestamp, _contributionCounter)
        );

        contributions[contributionId] = Contribution({
            id: contributionId,
            consortiumId: consortiumId,
            contributor: msg.sender,
            recordCount: recordCount,
            featureCount: featureCount,
            dataHash: dataHash,
            checksumHash: checksumHash,
            timestamp: block.timestamp,
            verified: false
        });

        consortiumContributions[consortiumId].push(contributionId);

        Member storage m = members[consortiumId][msg.sender];
        unchecked {
            m.contributionCount += recordCount;
            consortiums[consortiumId].totalContributions += recordCount;
        }
        m.lastContributionAt = block.timestamp;
        m.latestContributionHash = dataHash;

        _updateContributionWeights(consortiumId);

        _recordAuditEvent(
            consortiumId,
            AuditEventType.DataContributed,
            msg.sender,
            contributionId,
            abi.encode(recordCount, featureCount, dataHash)
        );

        emit ContributionRecorded(consortiumId, contributionId, msg.sender, recordCount);
        return contributionId;
    }

    // ============ Voting System ============

    function createProposal(
        bytes32 consortiumId,
        ProposalType proposalType,
        bytes calldata data
    ) external
        whenNotPaused
        nonReentrant
        consortiumExists(consortiumId)
        onlyActiveMember(consortiumId)
        consortiumActive(consortiumId)
        returns (bytes32 proposalId)
    {
        unchecked { ++_proposalCounter; }

        proposalId = keccak256(
            abi.encodePacked(consortiumId, msg.sender, block.timestamp, _proposalCounter)
        );

        uint256 expiresAt = block.timestamp + consortiums[consortiumId].votingDuration;

        proposals[proposalId] = Proposal({
            id: proposalId,
            consortiumId: consortiumId,
            proposalType: proposalType,
            proposer: msg.sender,
            status: ProposalStatus.Active,
            data: data,
            createdAt: block.timestamp,
            expiresAt: expiresAt,
            yesVotes: 0,
            noVotes: 0,
            totalVoters: consortiums[consortiumId].memberCount,
            executed: false
        });

        consortiumProposals[consortiumId].push(proposalId);

        _recordAuditEvent(
            consortiumId,
            AuditEventType.ProposalCreated,
            msg.sender,
            proposalId,
            abi.encode(uint8(proposalType))
        );

        emit ProposalCreated(consortiumId, proposalId, proposalType, msg.sender);
        return proposalId;
    }

    function vote(bytes32 proposalId, bool support) external whenNotPaused nonReentrant {
        Proposal storage p = proposals[proposalId];
        if (p.createdAt == 0) revert ProposalNotFound(proposalId);
        if (p.status != ProposalStatus.Active) revert VotingClosed(proposalId);
        if (block.timestamp >= p.expiresAt) revert VotingClosed(proposalId);
        if (hasVoted[proposalId][msg.sender]) revert AlreadyVoted(msg.sender);
        if (members[p.consortiumId][msg.sender].status != MemberStatus.Active) {
            revert NotActiveMember(msg.sender);
        }

        hasVoted[proposalId][msg.sender] = true;
        votes[proposalId][msg.sender] = support;

        uint256 weight = members[p.consortiumId][msg.sender].contributionWeight;
        if (weight == 0) weight = 1;

        if (support) {
            unchecked { p.yesVotes += weight; }
        } else {
            unchecked { p.noVotes += weight; }
        }

        _recordAuditEvent(
            p.consortiumId,
            AuditEventType.ProposalVoted,
            msg.sender,
            proposalId,
            abi.encode(support, weight)
        );

        emit VoteCast(proposalId, msg.sender, support, weight);
    }

    function executeProposal(bytes32 proposalId) external whenNotPaused nonReentrant {
        Proposal storage p = proposals[proposalId];
        if (p.createdAt == 0) revert ProposalNotFound(proposalId);
        if (p.status != ProposalStatus.Active) revert AlreadyExecuted(proposalId);
        if (block.timestamp < p.expiresAt) revert VotingNotEnded(proposalId);
        if (p.executed) revert AlreadyExecuted(proposalId);

        uint256 totalVotes = p.yesVotes + p.noVotes;
        uint256 quorum = consortiums[p.consortiumId].minVotingQuorum;
        uint256 totalWeight = _getTotalVotingWeight(p.consortiumId);

        bool quorumMet = totalWeight > 0 && (totalVotes * 100) >= (totalWeight * quorum);
        bool passed = quorumMet && (p.yesVotes > p.noVotes);

        p.executed = true;
        p.status = passed ? ProposalStatus.Passed : ProposalStatus.Rejected;

        if (passed) {
            _executeProposalAction(p);
        }

        _recordAuditEvent(
            p.consortiumId,
            AuditEventType.ProposalExecuted,
            msg.sender,
            proposalId,
            abi.encode(passed, p.yesVotes, p.noVotes)
        );

        emit ProposalExecuted(proposalId, passed);
    }

    // ============ Reward Distribution (Pull Pattern) ============

    /**
     * @dev Allocate rewards to members based on contribution weight.
     * Uses pull-over-push pattern: no ETH transfers, just accounting.
     */
    function allocateRewards(
        bytes32 consortiumId
    ) external
        payable
        whenNotPaused
        nonReentrant
        consortiumExists(consortiumId)
        onlyConsortiumOwner(consortiumId)
    {
        if (msg.value == 0) revert ZeroAmount();

        address[] storage memberAddrs = memberList[consortiumId];
        uint256 allocated = 0;

        for (uint256 i = 0; i < memberAddrs.length;) {
            Member storage m = members[consortiumId][memberAddrs[i]];
            if (m.status == MemberStatus.Active && m.contributionWeight > 0) {
                uint256 share = (msg.value * m.contributionWeight) / WEIGHT_PRECISION;
                if (share > 0) {
                    pendingWithdrawals[consortiumId][m.addr] += share;
                    allocated += share;
                }
            }
            unchecked { ++i; }
        }

        totalPendingWithdrawals[consortiumId] += allocated;

        // Return any remainder to sender
        if (msg.value > allocated) {
            uint256 remainder = msg.value - allocated;
            (bool success, ) = payable(msg.sender).call{value: remainder}("");
            if (!success) revert TransferFailed();
        }

        _recordAuditEvent(
            consortiumId,
            AuditEventType.RewardsDistributed,
            msg.sender,
            keccak256(abi.encodePacked(consortiumId, msg.value, block.timestamp)),
            abi.encode(msg.value, allocated)
        );

        emit RewardsAllocated(consortiumId, allocated, memberAddrs.length);
    }

    /**
     * @dev Withdraw pending rewards (pull pattern - reentrancy safe).
     */
    function withdrawRewards(bytes32 consortiumId) external nonReentrant {
        uint256 amount = pendingWithdrawals[consortiumId][msg.sender];
        if (amount == 0) revert NoRewardsToClaim();

        // Effects before interactions
        pendingWithdrawals[consortiumId][msg.sender] = 0;
        totalPendingWithdrawals[consortiumId] -= amount;

        // Interaction
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        if (!success) revert TransferFailed();

        emit RewardWithdrawn(consortiumId, msg.sender, amount);
    }

    // ============ Internal Functions ============

    function _removeMember(bytes32 consortiumId, address member) internal {
        if (members[consortiumId][member].status != MemberStatus.Active) {
            revert MemberNotActive(member);
        }
        if (member == consortiums[consortiumId].owner) revert CannotRemoveOwner();

        members[consortiumId][member].status = MemberStatus.Removed;
        unchecked {
            --consortiums[consortiumId].memberCount;
        }

        _recordAuditEvent(
            consortiumId,
            AuditEventType.MemberRemoved,
            msg.sender,
            bytes32(uint256(uint160(member))),
            ""
        );

        emit MemberStatusChanged(consortiumId, member, MemberStatus.Active, MemberStatus.Removed);
    }

    function _updateContributionWeights(bytes32 consortiumId) internal {
        uint256 total = consortiums[consortiumId].totalContributions;
        if (total == 0) return;

        address[] storage memberAddrs = memberList[consortiumId];
        for (uint256 i = 0; i < memberAddrs.length;) {
            Member storage m = members[consortiumId][memberAddrs[i]];
            if (m.status == MemberStatus.Active && m.contributionCount > 0) {
                m.contributionWeight = (m.contributionCount * WEIGHT_PRECISION) / total;
            }
            unchecked { ++i; }
        }
    }

    function _executeProposalAction(Proposal storage p) internal {
        if (p.proposalType == ProposalType.RemoveMember) {
            address memberToRemove = abi.decode(p.data, (address));
            _removeMember(p.consortiumId, memberToRemove);
        } else if (p.proposalType == ProposalType.Dissolve) {
            consortiums[p.consortiumId].status = ConsortiumStatus.Dissolved;
        } else if (p.proposalType == ProposalType.UpdateConfig) {
            bytes32 newConfigHash = abi.decode(p.data, (bytes32));
            consortiums[p.consortiumId].modelConfigHash = newConfigHash;
        }
    }

    function _getTotalVotingWeight(bytes32 consortiumId) internal view returns (uint256) {
        uint256 total = 0;
        address[] storage memberAddrs = memberList[consortiumId];
        for (uint256 i = 0; i < memberAddrs.length;) {
            Member storage m = members[consortiumId][memberAddrs[i]];
            if (m.status == MemberStatus.Active) {
                total += m.contributionWeight > 0 ? m.contributionWeight : 1;
            }
            unchecked { ++i; }
        }
        return total;
    }

    function _recordAuditEvent(
        bytes32 consortiumId,
        AuditEventType eventType,
        address actor,
        bytes32 targetId,
        bytes memory data
    ) internal {
        unchecked { ++_eventCounter; }

        bytes32 eventId = keccak256(
            abi.encodePacked(consortiumId, eventType, block.timestamp, _eventCounter)
        );

        bytes32 previousHash = lastEventHash[consortiumId];

        auditTrail[consortiumId].push(AuditEvent({
            id: eventId,
            consortiumId: consortiumId,
            eventType: eventType,
            actor: actor,
            targetId: targetId,
            data: data,
            timestamp: block.timestamp,
            previousEventHash: previousHash
        }));

        lastEventHash[consortiumId] = keccak256(
            abi.encodePacked(eventId, previousHash, block.timestamp)
        );

        emit AuditEventRecorded(consortiumId, eventId, eventType);
    }

    // ============ View Functions ============

    function getConsortium(bytes32 consortiumId) external view returns (
        string memory name,
        address owner,
        ConsortiumStatus status,
        uint256 memberCount,
        uint256 totalContributions,
        uint256 minVotingQuorum,
        uint256 votingDuration
    ) {
        Consortium storage c = consortiums[consortiumId];
        return (c.name, c.owner, c.status, c.memberCount, c.totalContributions, c.minVotingQuorum, c.votingDuration);
    }

    function getMember(bytes32 consortiumId, address addr) external view returns (
        MemberStatus status,
        uint256 joinedAt,
        uint256 contributionCount,
        uint256 contributionWeight,
        uint256 lastContributionAt
    ) {
        Member storage m = members[consortiumId][addr];
        return (m.status, m.joinedAt, m.contributionCount, m.contributionWeight, m.lastContributionAt);
    }

    function getMembers(bytes32 consortiumId) external view returns (address[] memory) {
        return memberList[consortiumId];
    }

    function getPendingWithdrawal(bytes32 consortiumId, address member) external view returns (uint256) {
        return pendingWithdrawals[consortiumId][member];
    }

    function getAuditTrailLength(bytes32 consortiumId) external view returns (uint256) {
        return auditTrail[consortiumId].length;
    }

    function verifyAuditTrail(bytes32 consortiumId) external view returns (bool) {
        AuditEvent[] storage events = auditTrail[consortiumId];
        if (events.length == 0) return true;

        bytes32 computedHash = bytes32(0);
        for (uint256 i = 0; i < events.length;) {
            if (events[i].previousEventHash != computedHash) {
                return false;
            }
            computedHash = keccak256(
                abi.encodePacked(events[i].id, computedHash, events[i].timestamp)
            );
            unchecked { ++i; }
        }

        return computedHash == lastEventHash[consortiumId];
    }
}
