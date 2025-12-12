// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.0;

/**
 * @title ConsortiumGovernance
 * @dev Governance contract for FHE-ML consortiums.
 *
 * This contract provides:
 * - Consortium creation and membership management
 * - Contribution proof (quantity, not content)
 * - Voting system for consortium decisions
 * - Immutable audit trail
 * - Fair revenue/reward distribution based on contribution
 */
contract ConsortiumGovernance {
    // ============ Enums ============

    enum ConsortiumStatus {
        Active,
        Paused,
        Completed,
        Dissolved
    }

    enum MemberStatus {
        Pending,
        Active,
        Suspended,
        Removed
    }

    enum ProposalType {
        AddMember,
        RemoveMember,
        ChangeModel,
        StartTraining,
        DistributeRewards,
        UpdateConfig,
        Dissolve
    }

    enum ProposalStatus {
        Active,
        Passed,
        Rejected,
        Executed,
        Cancelled
    }

    enum AuditEventType {
        ConsortiumCreated,
        MemberJoined,
        MemberLeft,
        MemberRemoved,
        DataContributed,
        TrainingStarted,
        TrainingCompleted,
        ProposalCreated,
        ProposalVoted,
        ProposalExecuted,
        RewardsDistributed,
        ConfigUpdated
    }

    // ============ Structs ============

    struct Consortium {
        bytes32 id;
        string name;
        address owner;
        ConsortiumStatus status;
        uint256 createdAt;
        uint256 memberCount;
        uint256 totalContributions;  // Total data records contributed
        uint256 minVotingQuorum;     // Percentage (0-100)
        uint256 votingDuration;      // In seconds
        bytes32 modelConfigHash;     // Hash of model configuration
    }

    struct Member {
        address addr;
        MemberStatus status;
        uint256 joinedAt;
        uint256 contributionCount;   // Number of records contributed
        uint256 contributionWeight;  // Calculated weight for rewards
        uint256 lastContributionAt;
        bytes32 latestContributionHash;  // Hash of latest contribution
    }

    struct Contribution {
        bytes32 id;
        bytes32 consortiumId;
        address contributor;
        uint256 recordCount;
        uint256 featureCount;
        bytes32 dataHash;           // Hash of encrypted data (for verification)
        bytes32 checksumHash;       // Checksum of the blob
        uint256 timestamp;
        bool verified;
    }

    struct Proposal {
        bytes32 id;
        bytes32 consortiumId;
        ProposalType proposalType;
        address proposer;
        ProposalStatus status;
        bytes data;                 // Encoded proposal data
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
        bytes32 targetId;           // Related entity (member, proposal, etc)
        bytes data;                 // Event-specific data
        uint256 timestamp;
        bytes32 previousEventHash; // Chain of events
    }

    struct RewardDistribution {
        bytes32 consortiumId;
        uint256 totalAmount;
        uint256 distributedAt;
        bytes32 distributionHash;   // Hash of distribution details
    }

    // ============ State Variables ============

    // Consortium ID => Consortium
    mapping(bytes32 => Consortium) public consortiums;

    // Consortium ID => Member Address => Member
    mapping(bytes32 => mapping(address => Member)) public members;

    // Consortium ID => Member addresses array
    mapping(bytes32 => address[]) public memberList;

    // Contribution ID => Contribution
    mapping(bytes32 => Contribution) public contributions;

    // Consortium ID => Contribution IDs
    mapping(bytes32 => bytes32[]) public consortiumContributions;

    // Proposal ID => Proposal
    mapping(bytes32 => Proposal) public proposals;

    // Consortium ID => Proposal IDs
    mapping(bytes32 => bytes32[]) public consortiumProposals;

    // Proposal ID => Voter => has voted
    mapping(bytes32 => mapping(address => bool)) public hasVoted;

    // Proposal ID => Voter => vote (true = yes, false = no)
    mapping(bytes32 => mapping(address => bool)) public votes;

    // Consortium ID => Audit Events
    mapping(bytes32 => AuditEvent[]) public auditTrail;

    // Consortium ID => Last event hash (for chaining)
    mapping(bytes32 => bytes32) public lastEventHash;

    // Consortium ID => Reward Distributions
    mapping(bytes32 => RewardDistribution[]) public rewardDistributions;

    // Counters
    uint256 private _consortiumCounter;
    uint256 private _contributionCounter;
    uint256 private _proposalCounter;
    uint256 private _eventCounter;

    // ============ Events ============

    event ConsortiumCreated(
        bytes32 indexed consortiumId,
        string name,
        address indexed owner
    );

    event MemberAdded(
        bytes32 indexed consortiumId,
        address indexed member,
        MemberStatus status
    );

    event MemberStatusChanged(
        bytes32 indexed consortiumId,
        address indexed member,
        MemberStatus oldStatus,
        MemberStatus newStatus
    );

    event ContributionRecorded(
        bytes32 indexed consortiumId,
        bytes32 indexed contributionId,
        address indexed contributor,
        uint256 recordCount
    );

    event ProposalCreated(
        bytes32 indexed consortiumId,
        bytes32 indexed proposalId,
        ProposalType proposalType,
        address indexed proposer
    );

    event VoteCast(
        bytes32 indexed proposalId,
        address indexed voter,
        bool vote,
        uint256 weight
    );

    event ProposalExecuted(
        bytes32 indexed proposalId,
        bool passed
    );

    event AuditEventRecorded(
        bytes32 indexed consortiumId,
        bytes32 indexed eventId,
        AuditEventType eventType
    );

    event RewardsDistributed(
        bytes32 indexed consortiumId,
        uint256 totalAmount,
        uint256 memberCount
    );

    // ============ Modifiers ============

    modifier consortiumExists(bytes32 consortiumId) {
        require(consortiums[consortiumId].createdAt != 0, "Consortium does not exist");
        _;
    }

    modifier onlyConsortiumOwner(bytes32 consortiumId) {
        require(consortiums[consortiumId].owner == msg.sender, "Not consortium owner");
        _;
    }

    modifier onlyActiveMember(bytes32 consortiumId) {
        require(
            members[consortiumId][msg.sender].status == MemberStatus.Active,
            "Not an active member"
        );
        _;
    }

    modifier consortiumActive(bytes32 consortiumId) {
        require(
            consortiums[consortiumId].status == ConsortiumStatus.Active,
            "Consortium is not active"
        );
        _;
    }

    // ============ Consortium Management ============

    /**
     * @dev Create a new consortium.
     */
    function createConsortium(
        string calldata name,
        uint256 minVotingQuorum,
        uint256 votingDuration,
        bytes32 modelConfigHash
    ) external returns (bytes32 consortiumId) {
        require(bytes(name).length > 0, "Name required");
        require(minVotingQuorum > 0 && minVotingQuorum <= 100, "Invalid quorum");
        require(votingDuration >= 1 hours, "Voting duration too short");

        _consortiumCounter++;
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

        // Add owner as first member
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

        // Record audit event
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

    /**
     * @dev Add a new member to consortium (owner only, or via proposal).
     */
    function addMember(
        bytes32 consortiumId,
        address newMember
    ) external consortiumExists(consortiumId) onlyConsortiumOwner(consortiumId) consortiumActive(consortiumId) {
        require(newMember != address(0), "Invalid address");
        require(members[consortiumId][newMember].joinedAt == 0, "Already a member");

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
        consortiums[consortiumId].memberCount++;

        _recordAuditEvent(
            consortiumId,
            AuditEventType.MemberJoined,
            msg.sender,
            bytes32(uint256(uint160(newMember))),
            ""
        );

        emit MemberAdded(consortiumId, newMember, MemberStatus.Active);
    }

    /**
     * @dev Remove a member (via proposal execution).
     */
    function _removeMember(
        bytes32 consortiumId,
        address member
    ) internal {
        require(members[consortiumId][member].status == MemberStatus.Active, "Not active");
        require(member != consortiums[consortiumId].owner, "Cannot remove owner");

        members[consortiumId][member].status = MemberStatus.Removed;
        consortiums[consortiumId].memberCount--;

        _recordAuditEvent(
            consortiumId,
            AuditEventType.MemberRemoved,
            msg.sender,
            bytes32(uint256(uint160(member))),
            ""
        );

        emit MemberStatusChanged(consortiumId, member, MemberStatus.Active, MemberStatus.Removed);
    }

    // ============ Contribution Proofs ============

    /**
     * @dev Record a data contribution (proof of contribution, not the data itself).
     */
    function recordContribution(
        bytes32 consortiumId,
        uint256 recordCount,
        uint256 featureCount,
        bytes32 dataHash,
        bytes32 checksumHash
    ) external consortiumExists(consortiumId) onlyActiveMember(consortiumId) consortiumActive(consortiumId) returns (bytes32 contributionId) {
        require(recordCount > 0, "Must contribute records");

        _contributionCounter++;
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

        // Update member stats
        Member storage m = members[consortiumId][msg.sender];
        m.contributionCount += recordCount;
        m.lastContributionAt = block.timestamp;
        m.latestContributionHash = dataHash;

        // Update consortium total
        consortiums[consortiumId].totalContributions += recordCount;

        // Recalculate contribution weights
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

    /**
     * @dev Verify a contribution (by consortium owner or validator).
     */
    function verifyContribution(
        bytes32 contributionId
    ) external {
        Contribution storage c = contributions[contributionId];
        require(c.timestamp != 0, "Contribution not found");
        require(
            consortiums[c.consortiumId].owner == msg.sender,
            "Only owner can verify"
        );

        c.verified = true;
    }

    /**
     * @dev Update contribution weights for all members.
     */
    function _updateContributionWeights(bytes32 consortiumId) internal {
        uint256 total = consortiums[consortiumId].totalContributions;
        if (total == 0) return;

        address[] storage memberAddrs = memberList[consortiumId];
        for (uint256 i = 0; i < memberAddrs.length; i++) {
            Member storage m = members[consortiumId][memberAddrs[i]];
            if (m.status == MemberStatus.Active && m.contributionCount > 0) {
                // Weight as percentage (scaled by 10000 for precision)
                m.contributionWeight = (m.contributionCount * 10000) / total;
            }
        }
    }

    // ============ Voting System ============

    /**
     * @dev Create a new proposal.
     */
    function createProposal(
        bytes32 consortiumId,
        ProposalType proposalType,
        bytes calldata data
    ) external consortiumExists(consortiumId) onlyActiveMember(consortiumId) consortiumActive(consortiumId) returns (bytes32 proposalId) {
        _proposalCounter++;
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

    /**
     * @dev Cast a vote on a proposal.
     */
    function vote(
        bytes32 proposalId,
        bool support
    ) external {
        Proposal storage p = proposals[proposalId];
        require(p.createdAt != 0, "Proposal not found");
        require(p.status == ProposalStatus.Active, "Voting closed");
        require(block.timestamp < p.expiresAt, "Voting expired");
        require(!hasVoted[proposalId][msg.sender], "Already voted");
        require(
            members[p.consortiumId][msg.sender].status == MemberStatus.Active,
            "Not an active member"
        );

        hasVoted[proposalId][msg.sender] = true;
        votes[proposalId][msg.sender] = support;

        // Weight votes by contribution
        uint256 weight = members[p.consortiumId][msg.sender].contributionWeight;
        if (weight == 0) weight = 1; // Minimum weight for members without contributions

        if (support) {
            p.yesVotes += weight;
        } else {
            p.noVotes += weight;
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

    /**
     * @dev Execute a proposal after voting ends.
     */
    function executeProposal(bytes32 proposalId) external {
        Proposal storage p = proposals[proposalId];
        require(p.createdAt != 0, "Proposal not found");
        require(p.status == ProposalStatus.Active, "Already processed");
        require(block.timestamp >= p.expiresAt, "Voting not ended");
        require(!p.executed, "Already executed");

        // Check quorum
        uint256 totalVotes = p.yesVotes + p.noVotes;
        uint256 quorum = consortiums[p.consortiumId].minVotingQuorum;
        uint256 totalWeight = _getTotalVotingWeight(p.consortiumId);

        bool quorumMet = (totalVotes * 100) >= (totalWeight * quorum);
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

    /**
     * @dev Execute the action of a passed proposal.
     */
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
        // Other proposal types can be handled here
    }

    /**
     * @dev Get total voting weight for a consortium.
     */
    function _getTotalVotingWeight(bytes32 consortiumId) internal view returns (uint256) {
        uint256 total = 0;
        address[] storage memberAddrs = memberList[consortiumId];
        for (uint256 i = 0; i < memberAddrs.length; i++) {
            Member storage m = members[consortiumId][memberAddrs[i]];
            if (m.status == MemberStatus.Active) {
                total += m.contributionWeight > 0 ? m.contributionWeight : 1;
            }
        }
        return total;
    }

    // ============ Audit Trail ============

    /**
     * @dev Record an audit event (internal).
     */
    function _recordAuditEvent(
        bytes32 consortiumId,
        AuditEventType eventType,
        address actor,
        bytes32 targetId,
        bytes memory data
    ) internal {
        _eventCounter++;
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

        // Update chain
        lastEventHash[consortiumId] = keccak256(
            abi.encodePacked(eventId, previousHash, block.timestamp)
        );

        emit AuditEventRecorded(consortiumId, eventId, eventType);
    }

    /**
     * @dev Get audit trail length.
     */
    function getAuditTrailLength(bytes32 consortiumId) external view returns (uint256) {
        return auditTrail[consortiumId].length;
    }

    /**
     * @dev Get audit event by index.
     */
    function getAuditEvent(
        bytes32 consortiumId,
        uint256 index
    ) external view returns (
        bytes32 id,
        AuditEventType eventType,
        address actor,
        bytes32 targetId,
        uint256 timestamp,
        bytes32 previousEventHash
    ) {
        require(index < auditTrail[consortiumId].length, "Invalid index");
        AuditEvent storage e = auditTrail[consortiumId][index];
        return (e.id, e.eventType, e.actor, e.targetId, e.timestamp, e.previousEventHash);
    }

    /**
     * @dev Verify audit trail integrity.
     */
    function verifyAuditTrail(bytes32 consortiumId) external view returns (bool) {
        AuditEvent[] storage events = auditTrail[consortiumId];
        if (events.length == 0) return true;

        bytes32 computedHash = bytes32(0);
        for (uint256 i = 0; i < events.length; i++) {
            if (events[i].previousEventHash != computedHash) {
                return false;
            }
            computedHash = keccak256(
                abi.encodePacked(events[i].id, computedHash, events[i].timestamp)
            );
        }

        return computedHash == lastEventHash[consortiumId];
    }

    // ============ Revenue Distribution ============

    /**
     * @dev Distribute rewards to members based on contribution weight.
     */
    function distributeRewards(
        bytes32 consortiumId
    ) external payable consortiumExists(consortiumId) onlyConsortiumOwner(consortiumId) {
        require(msg.value > 0, "Must send ETH");

        uint256 totalDistributed = 0;
        address[] storage memberAddrs = memberList[consortiumId];

        for (uint256 i = 0; i < memberAddrs.length; i++) {
            Member storage m = members[consortiumId][memberAddrs[i]];
            if (m.status == MemberStatus.Active && m.contributionWeight > 0) {
                uint256 share = (msg.value * m.contributionWeight) / 10000;
                if (share > 0) {
                    payable(m.addr).transfer(share);
                    totalDistributed += share;
                }
            }
        }

        // Return remainder to sender
        if (msg.value > totalDistributed) {
            payable(msg.sender).transfer(msg.value - totalDistributed);
        }

        bytes32 distributionHash = keccak256(
            abi.encodePacked(consortiumId, msg.value, block.timestamp)
        );

        rewardDistributions[consortiumId].push(RewardDistribution({
            consortiumId: consortiumId,
            totalAmount: totalDistributed,
            distributedAt: block.timestamp,
            distributionHash: distributionHash
        }));

        _recordAuditEvent(
            consortiumId,
            AuditEventType.RewardsDistributed,
            msg.sender,
            distributionHash,
            abi.encode(msg.value, totalDistributed)
        );

        emit RewardsDistributed(consortiumId, totalDistributed, memberAddrs.length);
    }

    // ============ View Functions ============

    /**
     * @dev Get consortium details.
     */
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
        return (
            c.name,
            c.owner,
            c.status,
            c.memberCount,
            c.totalContributions,
            c.minVotingQuorum,
            c.votingDuration
        );
    }

    /**
     * @dev Get member details.
     */
    function getMember(
        bytes32 consortiumId,
        address addr
    ) external view returns (
        MemberStatus status,
        uint256 joinedAt,
        uint256 contributionCount,
        uint256 contributionWeight,
        uint256 lastContributionAt
    ) {
        Member storage m = members[consortiumId][addr];
        return (
            m.status,
            m.joinedAt,
            m.contributionCount,
            m.contributionWeight,
            m.lastContributionAt
        );
    }

    /**
     * @dev Get member list for a consortium.
     */
    function getMembers(bytes32 consortiumId) external view returns (address[] memory) {
        return memberList[consortiumId];
    }

    /**
     * @dev Get contribution count for a consortium.
     */
    function getContributionCount(bytes32 consortiumId) external view returns (uint256) {
        return consortiumContributions[consortiumId].length;
    }

    /**
     * @dev Get proposal count for a consortium.
     */
    function getProposalCount(bytes32 consortiumId) external view returns (uint256) {
        return consortiumProposals[consortiumId].length;
    }

    /**
     * @dev Get proposal details.
     */
    function getProposal(bytes32 proposalId) external view returns (
        bytes32 consortiumId,
        ProposalType proposalType,
        address proposer,
        ProposalStatus status,
        uint256 yesVotes,
        uint256 noVotes,
        uint256 expiresAt,
        bool executed
    ) {
        Proposal storage p = proposals[proposalId];
        return (
            p.consortiumId,
            p.proposalType,
            p.proposer,
            p.status,
            p.yesVotes,
            p.noVotes,
            p.expiresAt,
            p.executed
        );
    }

    /**
     * @dev Get reward distribution history.
     */
    function getRewardDistributionCount(bytes32 consortiumId) external view returns (uint256) {
        return rewardDistributions[consortiumId].length;
    }
}
