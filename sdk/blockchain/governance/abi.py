"""ConsortiumGovernance contract ABI definition."""

# Contract ABI (simplified - in production, load from compiled JSON)
GOVERNANCE_ABI = [
    # Consortium Management
    {
        "inputs": [
            {"name": "name", "type": "string"},
            {"name": "minVotingQuorum", "type": "uint256"},
            {"name": "votingDuration", "type": "uint256"},
            {"name": "modelConfigHash", "type": "bytes32"},
        ],
        "name": "createConsortium",
        "outputs": [{"name": "consortiumId", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "consortiumId", "type": "bytes32"},
            {"name": "newMember", "type": "address"},
        ],
        "name": "addMember",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # Contributions
    {
        "inputs": [
            {"name": "consortiumId", "type": "bytes32"},
            {"name": "recordCount", "type": "uint256"},
            {"name": "featureCount", "type": "uint256"},
            {"name": "dataHash", "type": "bytes32"},
            {"name": "checksumHash", "type": "bytes32"},
        ],
        "name": "recordContribution",
        "outputs": [{"name": "contributionId", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "contributionId", "type": "bytes32"}],
        "name": "verifyContribution",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # Proposals
    {
        "inputs": [
            {"name": "consortiumId", "type": "bytes32"},
            {"name": "proposalType", "type": "uint8"},
            {"name": "data", "type": "bytes"},
        ],
        "name": "createProposal",
        "outputs": [{"name": "proposalId", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "proposalId", "type": "bytes32"}, {"name": "support", "type": "bool"}],
        "name": "vote",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "proposalId", "type": "bytes32"}],
        "name": "executeProposal",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    # Rewards
    {
        "inputs": [{"name": "consortiumId", "type": "bytes32"}],
        "name": "distributeRewards",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
    # View Functions
    {
        "inputs": [{"name": "consortiumId", "type": "bytes32"}],
        "name": "getConsortium",
        "outputs": [
            {"name": "name", "type": "string"},
            {"name": "owner", "type": "address"},
            {"name": "status", "type": "uint8"},
            {"name": "memberCount", "type": "uint256"},
            {"name": "totalContributions", "type": "uint256"},
            {"name": "minVotingQuorum", "type": "uint256"},
            {"name": "votingDuration", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "consortiumId", "type": "bytes32"},
            {"name": "addr", "type": "address"},
        ],
        "name": "getMember",
        "outputs": [
            {"name": "status", "type": "uint8"},
            {"name": "joinedAt", "type": "uint256"},
            {"name": "contributionCount", "type": "uint256"},
            {"name": "contributionWeight", "type": "uint256"},
            {"name": "lastContributionAt", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "consortiumId", "type": "bytes32"}],
        "name": "getMembers",
        "outputs": [{"name": "", "type": "address[]"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "proposalId", "type": "bytes32"}],
        "name": "getProposal",
        "outputs": [
            {"name": "consortiumId", "type": "bytes32"},
            {"name": "proposalType", "type": "uint8"},
            {"name": "proposer", "type": "address"},
            {"name": "status", "type": "uint8"},
            {"name": "yesVotes", "type": "uint256"},
            {"name": "noVotes", "type": "uint256"},
            {"name": "expiresAt", "type": "uint256"},
            {"name": "executed", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "consortiumId", "type": "bytes32"}],
        "name": "getAuditTrailLength",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "consortiumId", "type": "bytes32"},
            {"name": "index", "type": "uint256"},
        ],
        "name": "getAuditEvent",
        "outputs": [
            {"name": "id", "type": "bytes32"},
            {"name": "eventType", "type": "uint8"},
            {"name": "actor", "type": "address"},
            {"name": "targetId", "type": "bytes32"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "previousEventHash", "type": "bytes32"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "consortiumId", "type": "bytes32"}],
        "name": "verifyAuditTrail",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "consortiumId", "type": "bytes32"}],
        "name": "getContributionCount",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "consortiumId", "type": "bytes32"}],
        "name": "getProposalCount",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    # Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "consortiumId", "type": "bytes32"},
            {"indexed": False, "name": "name", "type": "string"},
            {"indexed": True, "name": "owner", "type": "address"},
        ],
        "name": "ConsortiumCreated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "consortiumId", "type": "bytes32"},
            {"indexed": True, "name": "contributionId", "type": "bytes32"},
            {"indexed": True, "name": "contributor", "type": "address"},
            {"indexed": False, "name": "recordCount", "type": "uint256"},
        ],
        "name": "ContributionRecorded",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "proposalId", "type": "bytes32"},
            {"indexed": True, "name": "voter", "type": "address"},
            {"indexed": False, "name": "vote", "type": "bool"},
            {"indexed": False, "name": "weight", "type": "uint256"},
        ],
        "name": "VoteCast",
        "type": "event",
    },
]


__all__ = ["GOVERNANCE_ABI"]
