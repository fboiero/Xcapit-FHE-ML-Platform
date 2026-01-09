"""Governance client for blockchain interaction."""

import json
from datetime import datetime
from typing import Optional

from web3 import Web3

from ..connector import BlockchainConnector, Network
from .abi import GOVERNANCE_ABI
from .models import (
    AuditEvent,
    AuditEventType,
    ConsortiumInfo,
    ConsortiumStatus,
    MemberInfo,
    MemberStatus,
    ProposalInfo,
    ProposalStatus,
    ProposalType,
)


class GovernanceClient:
    """Client for interacting with ConsortiumGovernance contract.

    Example:
        >>> client = GovernanceClient(contract_address="0x...")
        >>> client.connect(private_key="0x...")
        >>> consortium_id = client.create_consortium("My Consortium", 51, 86400)
        >>> client.record_contribution(consortium_id, 1000, 10, data_hash, checksum)
    """

    def __init__(
        self,
        contract_address: str,
        network: Network = Network.ARBITRUM_SEPOLIA,
        rpc_url: Optional[str] = None,
    ):
        """Initialize governance client.

        Args:
            contract_address: Deployed contract address.
            network: Target network.
            rpc_url: Custom RPC URL.
        """
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.connector = BlockchainConnector(network, rpc_url)
        self._contract = None

    def connect(self, private_key: str) -> str:
        """Connect to network and set account.

        Args:
            private_key: Account private key.

        Returns:
            Account address.
        """
        self.connector.set_account(private_key)
        self.connector.connect()
        self._contract = self.connector.get_contract(self.contract_address, GOVERNANCE_ABI)
        return self.connector.address

    @property
    def contract(self):
        """Get contract instance."""
        if self._contract is None:
            raise RuntimeError("Not connected. Call connect() first.")
        return self._contract

    # ============ Consortium Management ============

    def create_consortium(
        self,
        name: str,
        min_voting_quorum: int = 51,
        voting_duration: int = 86400,  # 24 hours
        model_config: Optional[dict] = None,
    ) -> bytes:
        """Create a new consortium on-chain.

        Args:
            name: Consortium name.
            min_voting_quorum: Minimum voting quorum (0-100).
            voting_duration: Voting duration in seconds.
            model_config: Model configuration (hashed).

        Returns:
            Consortium ID (bytes32).
        """
        config_hash = self._hash_config(model_config) if model_config else b"\x00" * 32

        tx = self.contract.functions.createConsortium(
            name, min_voting_quorum, voting_duration, config_hash
        ).build_transaction(
            {
                "from": self.connector.address,
                "nonce": self.connector.get_nonce(),
                "gas": 500000,
                "gasPrice": self.connector.get_gas_price(),
                "chainId": self.connector.config.chain_id,
            }
        )

        signed = self.connector.account.sign_transaction(tx)
        tx_hash = self.connector.web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.connector.web3.eth.wait_for_transaction_receipt(tx_hash)

        # Extract consortium ID from event logs
        logs = self.contract.events.ConsortiumCreated().process_receipt(receipt)
        if logs:
            return logs[0]["args"]["consortiumId"]

        raise RuntimeError("Failed to get consortium ID from transaction")

    def add_member(self, consortium_id: bytes, member_address: str) -> str:
        """Add a member to consortium.

        Args:
            consortium_id: Consortium ID.
            member_address: New member address.

        Returns:
            Transaction hash.
        """
        tx = self.contract.functions.addMember(
            consortium_id, Web3.to_checksum_address(member_address)
        ).build_transaction(
            {
                "from": self.connector.address,
                "nonce": self.connector.get_nonce(),
                "gas": 200000,
                "gasPrice": self.connector.get_gas_price(),
                "chainId": self.connector.config.chain_id,
            }
        )

        signed = self.connector.account.sign_transaction(tx)
        tx_hash = self.connector.web3.eth.send_raw_transaction(signed.raw_transaction)
        self.connector.web3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    def get_consortium(self, consortium_id: bytes) -> ConsortiumInfo:
        """Get consortium details.

        Args:
            consortium_id: Consortium ID.

        Returns:
            ConsortiumInfo object.
        """
        result = self.contract.functions.getConsortium(consortium_id).call()
        return ConsortiumInfo(
            id=consortium_id,
            name=result[0],
            owner=result[1],
            status=ConsortiumStatus(result[2]),
            member_count=result[3],
            total_contributions=result[4],
            min_voting_quorum=result[5],
            voting_duration=result[6],
        )

    def get_members(self, consortium_id: bytes) -> list[str]:
        """Get all member addresses for a consortium.

        Args:
            consortium_id: Consortium ID.

        Returns:
            List of member addresses.
        """
        return self.contract.functions.getMembers(consortium_id).call()

    def get_member(self, consortium_id: bytes, address: str) -> MemberInfo:
        """Get member details.

        Args:
            consortium_id: Consortium ID.
            address: Member address.

        Returns:
            MemberInfo object.
        """
        result = self.contract.functions.getMember(
            consortium_id, Web3.to_checksum_address(address)
        ).call()

        return MemberInfo(
            address=address,
            status=MemberStatus(result[0]),
            joined_at=datetime.fromtimestamp(result[1]) if result[1] > 0 else None,
            contribution_count=result[2],
            contribution_weight=result[3],
            last_contribution_at=datetime.fromtimestamp(result[4]) if result[4] > 0 else None,
        )

    # ============ Contribution Proofs ============

    def record_contribution(
        self,
        consortium_id: bytes,
        record_count: int,
        feature_count: int,
        encrypted_data: bytes,
    ) -> bytes:
        """Record a contribution proof on-chain.

        Args:
            consortium_id: Consortium ID.
            record_count: Number of records contributed.
            feature_count: Number of features.
            encrypted_data: The encrypted data blob (for hashing).

        Returns:
            Contribution ID (bytes32).
        """
        # Hash the encrypted data (we never store actual data on-chain)
        data_hash = Web3.keccak(encrypted_data)
        checksum_hash = Web3.keccak(
            encrypted_data[:32] + encrypted_data[-32:]
            if len(encrypted_data) > 64
            else encrypted_data
        )

        tx = self.contract.functions.recordContribution(
            consortium_id, record_count, feature_count, data_hash, checksum_hash
        ).build_transaction(
            {
                "from": self.connector.address,
                "nonce": self.connector.get_nonce(),
                "gas": 300000,
                "gasPrice": self.connector.get_gas_price(),
                "chainId": self.connector.config.chain_id,
            }
        )

        signed = self.connector.account.sign_transaction(tx)
        tx_hash = self.connector.web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.connector.web3.eth.wait_for_transaction_receipt(tx_hash)

        # Extract contribution ID from event
        logs = self.contract.events.ContributionRecorded().process_receipt(receipt)
        if logs:
            return logs[0]["args"]["contributionId"]

        raise RuntimeError("Failed to get contribution ID from transaction")

    def verify_contribution(self, contribution_id: bytes) -> str:
        """Verify a contribution (owner only).

        Args:
            contribution_id: Contribution ID.

        Returns:
            Transaction hash.
        """
        tx = self.contract.functions.verifyContribution(contribution_id).build_transaction(
            {
                "from": self.connector.address,
                "nonce": self.connector.get_nonce(),
                "gas": 100000,
                "gasPrice": self.connector.get_gas_price(),
                "chainId": self.connector.config.chain_id,
            }
        )

        signed = self.connector.account.sign_transaction(tx)
        tx_hash = self.connector.web3.eth.send_raw_transaction(signed.raw_transaction)
        self.connector.web3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    def get_contribution_count(self, consortium_id: bytes) -> int:
        """Get number of contributions for a consortium."""
        return self.contract.functions.getContributionCount(consortium_id).call()

    # ============ Voting System ============

    def create_proposal(
        self,
        consortium_id: bytes,
        proposal_type: ProposalType,
        data: bytes = b"",
    ) -> bytes:
        """Create a new proposal.

        Args:
            consortium_id: Consortium ID.
            proposal_type: Type of proposal.
            data: Encoded proposal data.

        Returns:
            Proposal ID (bytes32).
        """
        tx = self.contract.functions.createProposal(
            consortium_id, proposal_type.value, data
        ).build_transaction(
            {
                "from": self.connector.address,
                "nonce": self.connector.get_nonce(),
                "gas": 300000,
                "gasPrice": self.connector.get_gas_price(),
                "chainId": self.connector.config.chain_id,
            }
        )

        signed = self.connector.account.sign_transaction(tx)
        tx_hash = self.connector.web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.connector.web3.eth.wait_for_transaction_receipt(tx_hash)

        # Get proposal ID from logs
        for log in receipt["logs"]:
            if len(log["topics"]) > 0:
                # ProposalCreated event
                return log["topics"][2]  # proposalId is indexed

        raise RuntimeError("Failed to get proposal ID")

    def create_remove_member_proposal(
        self,
        consortium_id: bytes,
        member_to_remove: str,
    ) -> bytes:
        """Create a proposal to remove a member.

        Args:
            consortium_id: Consortium ID.
            member_to_remove: Address of member to remove.

        Returns:
            Proposal ID.
        """
        # Encode the member address as proposal data
        data = Web3.to_bytes(hexstr=Web3.to_checksum_address(member_to_remove))
        return self.create_proposal(consortium_id, ProposalType.REMOVE_MEMBER, data)

    def vote(self, proposal_id: bytes, support: bool) -> str:
        """Cast a vote on a proposal.

        Args:
            proposal_id: Proposal ID.
            support: True for yes, False for no.

        Returns:
            Transaction hash.
        """
        tx = self.contract.functions.vote(proposal_id, support).build_transaction(
            {
                "from": self.connector.address,
                "nonce": self.connector.get_nonce(),
                "gas": 150000,
                "gasPrice": self.connector.get_gas_price(),
                "chainId": self.connector.config.chain_id,
            }
        )

        signed = self.connector.account.sign_transaction(tx)
        tx_hash = self.connector.web3.eth.send_raw_transaction(signed.raw_transaction)
        self.connector.web3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    def execute_proposal(self, proposal_id: bytes) -> tuple[str, bool]:
        """Execute a proposal after voting ends.

        Args:
            proposal_id: Proposal ID.

        Returns:
            Tuple of (transaction hash, passed).
        """
        tx = self.contract.functions.executeProposal(proposal_id).build_transaction(
            {
                "from": self.connector.address,
                "nonce": self.connector.get_nonce(),
                "gas": 300000,
                "gasPrice": self.connector.get_gas_price(),
                "chainId": self.connector.config.chain_id,
            }
        )

        signed = self.connector.account.sign_transaction(tx)
        tx_hash = self.connector.web3.eth.send_raw_transaction(signed.raw_transaction)
        self.connector.web3.eth.wait_for_transaction_receipt(tx_hash)

        # Check proposal status after execution
        proposal = self.get_proposal(proposal_id)
        return tx_hash.hex(), proposal.status == ProposalStatus.PASSED

    def get_proposal(self, proposal_id: bytes) -> ProposalInfo:
        """Get proposal details.

        Args:
            proposal_id: Proposal ID.

        Returns:
            ProposalInfo object.
        """
        result = self.contract.functions.getProposal(proposal_id).call()
        return ProposalInfo(
            id=proposal_id,
            consortium_id=result[0],
            proposal_type=ProposalType(result[1]),
            proposer=result[2],
            status=ProposalStatus(result[3]),
            yes_votes=result[4],
            no_votes=result[5],
            expires_at=datetime.fromtimestamp(result[6]),
            executed=result[7],
        )

    def get_proposal_count(self, consortium_id: bytes) -> int:
        """Get number of proposals for a consortium."""
        return self.contract.functions.getProposalCount(consortium_id).call()

    # ============ Audit Trail ============

    def get_audit_trail_length(self, consortium_id: bytes) -> int:
        """Get audit trail length for a consortium."""
        return self.contract.functions.getAuditTrailLength(consortium_id).call()

    def get_audit_event(self, consortium_id: bytes, index: int) -> AuditEvent:
        """Get audit event by index.

        Args:
            consortium_id: Consortium ID.
            index: Event index.

        Returns:
            AuditEvent object.
        """
        result = self.contract.functions.getAuditEvent(consortium_id, index).call()
        return AuditEvent(
            id=result[0],
            event_type=AuditEventType(result[1]),
            actor=result[2],
            target_id=result[3],
            timestamp=datetime.fromtimestamp(result[4]),
            previous_hash=result[5],
        )

    def get_full_audit_trail(self, consortium_id: bytes) -> list[AuditEvent]:
        """Get complete audit trail for a consortium.

        Args:
            consortium_id: Consortium ID.

        Returns:
            List of AuditEvent objects.
        """
        length = self.get_audit_trail_length(consortium_id)
        events = []
        for i in range(length):
            events.append(self.get_audit_event(consortium_id, i))
        return events

    def verify_audit_trail(self, consortium_id: bytes) -> bool:
        """Verify audit trail integrity.

        Args:
            consortium_id: Consortium ID.

        Returns:
            True if audit trail is valid.
        """
        return self.contract.functions.verifyAuditTrail(consortium_id).call()

    # ============ Rewards ============

    def distribute_rewards(
        self,
        consortium_id: bytes,
        amount_wei: int,
    ) -> str:
        """Distribute rewards to members based on contribution weight.

        Args:
            consortium_id: Consortium ID.
            amount_wei: Amount in wei to distribute.

        Returns:
            Transaction hash.
        """
        tx = self.contract.functions.distributeRewards(consortium_id).build_transaction(
            {
                "from": self.connector.address,
                "value": amount_wei,
                "nonce": self.connector.get_nonce(),
                "gas": 500000,
                "gasPrice": self.connector.get_gas_price(),
                "chainId": self.connector.config.chain_id,
            }
        )

        signed = self.connector.account.sign_transaction(tx)
        tx_hash = self.connector.web3.eth.send_raw_transaction(signed.raw_transaction)
        self.connector.web3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    # ============ Helpers ============

    def _hash_config(self, config: dict) -> bytes:
        """Hash a configuration dictionary."""
        config_json = json.dumps(config, sort_keys=True)
        return Web3.keccak(text=config_json)

    @staticmethod
    def compute_data_hash(data: bytes) -> bytes:
        """Compute hash for contribution data.

        Args:
            data: Raw data bytes.

        Returns:
            Keccak256 hash.
        """
        return Web3.keccak(data)

    def get_explorer_url(self, tx_hash: str) -> str:
        """Get block explorer URL for a transaction."""
        return self.connector.get_explorer_url(tx_hash)


__all__ = ["GovernanceClient"]
