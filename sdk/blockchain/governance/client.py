"""Governance client for creating and managing on-chain proposals.

Provides a high-level interface for consortium governance actions
such as creating proposals, voting, and executing approved proposals.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from ..connector import BlockchainConnector
from ..contracts import GovernanceContract

# Default ABI for the Governance contract.
GOVERNANCE_ABI: list[dict] = [
    {
        "inputs": [
            {"name": "description", "type": "string"},
            {"name": "targets", "type": "address[]"},
            {"name": "calldatas", "type": "bytes[]"},
            {"name": "values", "type": "uint256[]"},
        ],
        "name": "createProposal",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "proposalId", "type": "uint256"},
            {"name": "support", "type": "bool"},
        ],
        "name": "vote",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "proposalId", "type": "uint256"}],
        "name": "executeProposal",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "proposalId", "type": "uint256"}],
        "name": "getProposal",
        "outputs": [
            {"name": "description", "type": "string"},
            {"name": "proposer", "type": "address"},
            {"name": "votesFor", "type": "uint256"},
            {"name": "votesAgainst", "type": "uint256"},
            {"name": "status", "type": "uint8"},
            {"name": "createdAt", "type": "uint256"},
            {"name": "executed", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "getProposalCount",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class ProposalStatus(Enum):
    """Status of a governance proposal."""

    PENDING = 0
    ACTIVE = 1
    PASSED = 2
    REJECTED = 3
    EXECUTED = 4
    CANCELLED = 5


@dataclass
class Proposal:
    """Represents an on-chain governance proposal."""

    proposal_id: int
    description: str
    proposer: str
    votes_for: int
    votes_against: int
    status: str
    created_at: int
    executed: bool


class GovernanceClient:
    """High-level client for consortium governance.

    Example:
        >>> from sdk.blockchain import BlockchainConnector, Network
        >>> from sdk.blockchain.governance import GovernanceClient
        >>> connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
        >>> connector.set_account(private_key)
        >>> connector.connect()
        >>> gov = GovernanceClient(connector, contract_address)
        >>> proposal_id = gov.create_proposal(
        ...     description="Add new member",
        ...     actions=[{"target": "0x...", "calldata": b"", "value": 0}],
        ... )
    """

    def __init__(
        self,
        connector: BlockchainConnector,
        contract_address: Optional[str] = None,
        abi: Optional[list] = None,
    ):
        """Initialize the governance client.

        Args:
            connector: An active BlockchainConnector.
            contract_address: Address of the deployed Governance contract.
            abi: Contract ABI. Defaults to the built-in ABI.
        """
        self._connector = connector
        self._contract_address = contract_address
        self._abi = abi or GOVERNANCE_ABI
        self._gov: Optional[GovernanceContract] = None

        if contract_address:
            self._gov = GovernanceContract(
                connector, contract_address, self._abi
            )

    def _ensure_contract(self):
        """Ensure the governance contract is available."""
        if self._gov is None:
            raise ValueError(
                "No contract address set. "
                "Pass contract_address to the constructor."
            )

    def create_proposal(
        self,
        description: str,
        actions: Optional[list[dict]] = None,
    ) -> str:
        """Create a new governance proposal.

        Args:
            description: Human-readable description.
            actions: List of action dicts with target, calldata, value.

        Returns:
            Transaction hash.
        """
        self._ensure_contract()
        actions = actions or []
        return self._gov.create_proposal(description, actions)

    def vote(
        self,
        proposal_id: int,
        support: bool,
        reason: Optional[str] = None,
    ) -> str:
        """Cast a vote on a proposal.

        Args:
            proposal_id: The proposal to vote on.
            support: True = in favour, False = against.
            reason: Optional reason (logged off-chain).

        Returns:
            Transaction hash.
        """
        self._ensure_contract()
        return self._gov.vote(proposal_id, support)

    def execute(self, proposal_id: int) -> str:
        """Execute a passed proposal.

        Args:
            proposal_id: The proposal to execute.

        Returns:
            Transaction hash.
        """
        self._ensure_contract()
        return self._gov.execute_proposal(proposal_id)

    def get_proposal(self, proposal_id: int) -> Proposal:
        """Retrieve proposal details.

        Args:
            proposal_id: The proposal identifier.

        Returns:
            Proposal dataclass with all on-chain fields.
        """
        self._ensure_contract()
        data = self._gov.get_proposal(proposal_id)

        # Map numeric status to string
        status_val = data.get("status", 0)
        try:
            status_str = ProposalStatus(status_val).name.lower()
        except (ValueError, KeyError):
            status_str = str(status_val)

        return Proposal(
            proposal_id=proposal_id,
            description=data.get("description", ""),
            proposer=data.get("proposer", ""),
            votes_for=data.get("votes_for", 0),
            votes_against=data.get("votes_against", 0),
            status=status_str,
            created_at=data.get("created_at", 0),
            executed=data.get("executed", False),
        )

    def list_proposals(self) -> list[Proposal]:
        """List all governance proposals.

        Returns:
            List of Proposal objects.
        """
        self._ensure_contract()
        count = self._gov.call("getProposalCount")
        proposals = []
        for i in range(count):
            try:
                proposals.append(self.get_proposal(i))
            except Exception:
                continue
        return proposals

    def __repr__(self) -> str:
        addr = self._contract_address or "not set"
        return f"GovernanceClient(contract={addr})"
