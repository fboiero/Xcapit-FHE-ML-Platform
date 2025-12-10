"""Tests for governance client module.

Requires: pip install -e ".[dev]" to install tenseal and other dependencies.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from sdk.blockchain.governance.models import (
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


class TestGovernanceModels:
    """Tests for governance model enums and dataclasses."""

    def test_consortium_status_values(self):
        """Test ConsortiumStatus enum values."""
        assert ConsortiumStatus.ACTIVE == 0
        assert ConsortiumStatus.PAUSED == 1
        assert ConsortiumStatus.COMPLETED == 2
        assert ConsortiumStatus.DISSOLVED == 3

    def test_member_status_values(self):
        """Test MemberStatus enum values."""
        assert MemberStatus.PENDING == 0
        assert MemberStatus.ACTIVE == 1
        assert MemberStatus.SUSPENDED == 2
        assert MemberStatus.REMOVED == 3

    def test_proposal_type_values(self):
        """Test ProposalType enum values."""
        assert ProposalType.ADD_MEMBER == 0
        assert ProposalType.REMOVE_MEMBER == 1
        assert ProposalType.CHANGE_MODEL == 2
        assert ProposalType.START_TRAINING == 3
        assert ProposalType.DISTRIBUTE_REWARDS == 4
        assert ProposalType.UPDATE_CONFIG == 5
        assert ProposalType.DISSOLVE == 6

    def test_proposal_status_values(self):
        """Test ProposalStatus enum values."""
        assert ProposalStatus.ACTIVE == 0
        assert ProposalStatus.PASSED == 1
        assert ProposalStatus.REJECTED == 2
        assert ProposalStatus.EXECUTED == 3
        assert ProposalStatus.CANCELLED == 4

    def test_audit_event_type_values(self):
        """Test AuditEventType enum values."""
        assert AuditEventType.CONSORTIUM_CREATED == 0
        assert AuditEventType.MEMBER_JOINED == 1
        assert AuditEventType.DATA_CONTRIBUTED == 4
        assert AuditEventType.REWARDS_DISTRIBUTED == 10

    def test_consortium_info_dataclass(self):
        """Test ConsortiumInfo dataclass."""
        info = ConsortiumInfo(
            id=b"consortium_id",
            name="Test Consortium",
            owner="0x" + "1" * 40,
            status=ConsortiumStatus.ACTIVE,
            member_count=5,
            total_contributions=100,
            min_voting_quorum=51,
            voting_duration=86400,
        )

        assert info.name == "Test Consortium"
        assert info.status == ConsortiumStatus.ACTIVE
        assert info.member_count == 5

    def test_member_info_dataclass(self):
        """Test MemberInfo dataclass."""
        info = MemberInfo(
            address="0x" + "2" * 40,
            status=MemberStatus.ACTIVE,
            joined_at=datetime(2024, 1, 1),
            contribution_count=10,
            contribution_weight=100,
            last_contribution_at=datetime(2024, 1, 15),
        )

        assert info.status == MemberStatus.ACTIVE
        assert info.contribution_count == 10

    def test_proposal_info_dataclass(self):
        """Test ProposalInfo dataclass."""
        info = ProposalInfo(
            id=b"proposal_id",
            consortium_id=b"consortium_id",
            proposal_type=ProposalType.ADD_MEMBER,
            proposer="0x" + "3" * 40,
            status=ProposalStatus.ACTIVE,
            yes_votes=10,
            no_votes=2,
            expires_at=datetime(2024, 1, 7),
            executed=False,
        )

        assert info.proposal_type == ProposalType.ADD_MEMBER
        assert info.yes_votes == 10

    def test_audit_event_dataclass(self):
        """Test AuditEvent dataclass."""
        event = AuditEvent(
            id=b"event_id",
            event_type=AuditEventType.MEMBER_JOINED,
            actor="0x" + "4" * 40,
            target_id=b"target_id",
            timestamp=datetime(2024, 1, 1),
            previous_hash=b"prev_hash",
        )

        assert event.event_type == AuditEventType.MEMBER_JOINED


class TestGovernanceClientInit:
    """Tests for GovernanceClient initialization."""

    def test_init_stores_contract_address(self):
        """Test initialization stores contract address."""
        with patch("sdk.blockchain.governance.client.BlockchainConnector"):
            with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
                mock_web3.to_checksum_address.return_value = "0x" + "1" * 40

                from sdk.blockchain.governance.client import GovernanceClient

                client = GovernanceClient("0x" + "1" * 40)

                assert client.contract_address == "0x" + "1" * 40
                assert client._contract is None

    def test_init_creates_connector(self):
        """Test initialization creates connector."""
        with patch("sdk.blockchain.governance.client.BlockchainConnector") as mock_conn:
            with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
                mock_web3.to_checksum_address.return_value = "0x" + "1" * 40

                from sdk.blockchain.connector import Network
                from sdk.blockchain.governance.client import GovernanceClient

                GovernanceClient("0x" + "1" * 40, Network.ARBITRUM_ONE)

                mock_conn.assert_called_once()


class TestGovernanceClientConnect:
    """Tests for connect functionality."""

    def test_connect_sets_account_and_connects(self):
        """Test connect sets account and establishes connection."""
        with patch("sdk.blockchain.governance.client.BlockchainConnector") as mock_conn_class:
            with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
                mock_web3.to_checksum_address.return_value = "0x" + "1" * 40

                mock_connector = MagicMock()
                mock_connector.address = "0x" + "2" * 40
                mock_connector.get_contract.return_value = MagicMock()
                mock_conn_class.return_value = mock_connector

                from sdk.blockchain.governance.client import GovernanceClient

                client = GovernanceClient("0x" + "1" * 40)
                address = client.connect("a" * 64)

                mock_connector.set_account.assert_called_once_with("a" * 64)
                mock_connector.connect.assert_called_once()
                assert address == "0x" + "2" * 40

    def test_contract_property_raises_when_not_connected(self):
        """Test contract property raises when not connected."""
        with patch("sdk.blockchain.governance.client.BlockchainConnector"):
            with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
                mock_web3.to_checksum_address.return_value = "0x" + "1" * 40

                from sdk.blockchain.governance.client import GovernanceClient

                client = GovernanceClient("0x" + "1" * 40)

                with pytest.raises(RuntimeError) as exc_info:
                    _ = client.contract

                assert "Not connected" in str(exc_info.value)


class TestGovernanceClientConsortium:
    """Tests for consortium management."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected GovernanceClient."""
        with patch("sdk.blockchain.governance.client.BlockchainConnector") as mock_conn_class:
            with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
                mock_web3.to_checksum_address.return_value = "0x" + "1" * 40
                mock_web3.keccak.return_value = b"hash" * 8

                mock_connector = MagicMock()
                mock_connector.address = "0x" + "2" * 40
                mock_connector.get_nonce.return_value = 5
                mock_connector.get_gas_price.return_value = 20000000000
                mock_connector.config.chain_id = 421614

                mock_contract = MagicMock()
                mock_connector.get_contract.return_value = mock_contract

                mock_account = MagicMock()
                mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
                mock_connector.account = mock_account

                mock_conn_class.return_value = mock_connector

                from sdk.blockchain.governance.client import GovernanceClient

                client = GovernanceClient("0x" + "1" * 40)
                client.connect("a" * 64)

                # Store references for tests
                client._mock_connector = mock_connector
                client._mock_contract = mock_contract

                return client

    def test_create_consortium(self, connected_client):
        """Test create_consortium sends transaction."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.createConsortium.return_value = mock_tx_builder

        mock_receipt = {"status": 1, "logs": []}
        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = b"tx_hash"
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = (
            mock_receipt
        )

        # Mock event processing
        mock_logs = [{"args": {"consortiumId": b"consortium_123"}}]
        connected_client._contract.events.ConsortiumCreated.return_value.process_receipt.return_value = mock_logs

        result = connected_client.create_consortium(
            name="Test Consortium",
            min_voting_quorum=51,
            voting_duration=86400,
        )

        assert result == b"consortium_123"
        connected_client._contract.functions.createConsortium.assert_called_once()

    def test_create_consortium_fallback_on_missing_event(self, connected_client):
        """Test create_consortium falls back to tx_hash when event not found."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.createConsortium.return_value = mock_tx_builder

        mock_receipt = {"status": 1, "logs": []}
        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = b"tx_hash"
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = (
            mock_receipt
        )

        # Empty logs - no event
        connected_client._contract.events.ConsortiumCreated.return_value.process_receipt.return_value = []

        # Should fall back to returning tx_hash instead of raising
        result = connected_client.create_consortium("Test")
        assert result == b"tx_hash"

    def test_add_member(self, connected_client):
        """Test add_member sends transaction."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.addMember.return_value = mock_tx_builder

        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = (
            b"0x" + b"a" * 64
        )
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {
            "status": 1
        }

        result = connected_client.add_member(b"consortium_id", "0x" + "3" * 40)

        assert result is not None
        connected_client._contract.functions.addMember.assert_called_once()

    def test_get_consortium_returns_info(self, connected_client):
        """Test get_consortium returns ConsortiumInfo."""
        connected_client._contract.functions.getConsortium.return_value.call.return_value = (
            "Test Consortium",  # name
            "0x" + "2" * 40,  # owner
            0,  # status (ACTIVE)
            5,  # member_count
            100,  # total_contributions
            51,  # min_voting_quorum
            86400,  # voting_duration
        )

        result = connected_client.get_consortium(b"consortium_id")

        assert isinstance(result, ConsortiumInfo)
        assert result.name == "Test Consortium"
        assert result.status == ConsortiumStatus.ACTIVE
        assert result.member_count == 5

    def test_get_members_returns_list(self, connected_client):
        """Test get_members returns list of addresses."""
        expected_members = ["0x" + "1" * 40, "0x" + "2" * 40, "0x" + "3" * 40]
        connected_client._contract.functions.getMembers.return_value.call.return_value = (
            expected_members
        )

        result = connected_client.get_members(b"consortium_id")

        assert result == expected_members

    def test_get_member_returns_info(self, connected_client):
        """Test get_member returns MemberInfo."""
        connected_client._contract.functions.getMember.return_value.call.return_value = (
            1,  # status (ACTIVE)
            1704067200,  # joined_at timestamp
            10,  # contribution_count
            100,  # contribution_weight
            1704153600,  # last_contribution_at timestamp
        )

        with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
            mock_web3.to_checksum_address.return_value = "0x" + "3" * 40

            result = connected_client.get_member(b"consortium_id", "0x" + "3" * 40)

        assert isinstance(result, MemberInfo)
        assert result.status == MemberStatus.ACTIVE
        assert result.contribution_count == 10


class TestGovernanceClientContributions:
    """Tests for contribution operations."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected GovernanceClient."""
        with patch("sdk.blockchain.governance.client.BlockchainConnector") as mock_conn_class:
            with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
                mock_web3.to_checksum_address.return_value = "0x" + "1" * 40
                mock_web3.keccak.return_value = b"hash" * 8

                mock_connector = MagicMock()
                mock_connector.address = "0x" + "2" * 40
                mock_connector.get_nonce.return_value = 5
                mock_connector.get_gas_price.return_value = 20000000000
                mock_connector.config.chain_id = 421614

                mock_contract = MagicMock()
                mock_connector.get_contract.return_value = mock_contract

                mock_account = MagicMock()
                mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
                mock_connector.account = mock_account

                mock_conn_class.return_value = mock_connector

                from sdk.blockchain.governance.client import GovernanceClient

                client = GovernanceClient("0x" + "1" * 40)
                client.connect("a" * 64)

                client._mock_connector = mock_connector
                client._mock_contract = mock_contract

                return client

    def test_record_contribution(self, connected_client):
        """Test record_contribution sends transaction."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.recordContribution.return_value = mock_tx_builder

        mock_receipt = {"status": 1}
        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = b"tx_hash"
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = (
            mock_receipt
        )

        mock_logs = [{"args": {"contributionId": b"contribution_123"}}]
        connected_client._contract.events.ContributionRecorded.return_value.process_receipt.return_value = mock_logs

        result = connected_client.record_contribution(
            b"consortium_id",
            record_count=1000,
            feature_count=10,
            encrypted_data=b"encrypted_data" * 10,
        )

        assert result == b"contribution_123"

    def test_record_contribution_short_data(self, connected_client):
        """Test record_contribution handles short data."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.recordContribution.return_value = mock_tx_builder

        mock_receipt = {"status": 1}
        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = b"tx_hash"
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = (
            mock_receipt
        )

        mock_logs = [{"args": {"contributionId": b"contribution_456"}}]
        connected_client._contract.events.ContributionRecorded.return_value.process_receipt.return_value = mock_logs

        # Short data (less than 64 bytes)
        result = connected_client.record_contribution(
            b"consortium_id",
            record_count=100,
            feature_count=5,
            encrypted_data=b"short",
        )

        assert result == b"contribution_456"

    def test_verify_contribution(self, connected_client):
        """Test verify_contribution sends transaction."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.verifyContribution.return_value = mock_tx_builder

        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = (
            b"0x" + b"a" * 64
        )
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {
            "status": 1
        }

        result = connected_client.verify_contribution(b"contribution_id")

        assert result is not None

    def test_get_contribution_count(self, connected_client):
        """Test get_contribution_count returns count."""
        connected_client._contract.functions.getContributionCount.return_value.call.return_value = (
            42
        )

        result = connected_client.get_contribution_count(b"consortium_id")

        assert result == 42


class TestGovernanceClientVoting:
    """Tests for voting operations."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected GovernanceClient."""
        with patch("sdk.blockchain.governance.client.BlockchainConnector") as mock_conn_class:
            with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
                mock_web3.to_checksum_address.return_value = "0x" + "1" * 40
                mock_web3.keccak.return_value = b"hash" * 8
                mock_web3.to_bytes.return_value = b"bytes"

                mock_connector = MagicMock()
                mock_connector.address = "0x" + "2" * 40
                mock_connector.get_nonce.return_value = 5
                mock_connector.get_gas_price.return_value = 20000000000
                mock_connector.config.chain_id = 421614

                mock_contract = MagicMock()
                mock_connector.get_contract.return_value = mock_contract

                mock_account = MagicMock()
                mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
                mock_connector.account = mock_account

                mock_conn_class.return_value = mock_connector

                from sdk.blockchain.governance.client import GovernanceClient

                client = GovernanceClient("0x" + "1" * 40)
                client.connect("a" * 64)

                client._mock_connector = mock_connector
                client._mock_contract = mock_contract

                return client

    def test_create_proposal(self, connected_client):
        """Test create_proposal sends transaction."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.createProposal.return_value = mock_tx_builder

        mock_receipt = {
            "status": 1,
            "logs": [{"topics": [b"event", b"consortium", b"proposal_id"]}],
        }
        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = b"tx_hash"
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = (
            mock_receipt
        )

        result = connected_client.create_proposal(
            b"consortium_id",
            ProposalType.ADD_MEMBER,
            data=b"member_address",
        )

        assert result == b"proposal_id"

    def test_create_remove_member_proposal(self, connected_client):
        """Test create_remove_member_proposal creates correct proposal."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.createProposal.return_value = mock_tx_builder

        mock_receipt = {
            "status": 1,
            "logs": [{"topics": [b"event", b"consortium", b"proposal_id"]}],
        }
        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = b"tx_hash"
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = (
            mock_receipt
        )

        result = connected_client.create_remove_member_proposal(
            b"consortium_id",
            "0x" + "3" * 40,
        )

        assert result == b"proposal_id"

    def test_commit_vote(self, connected_client):
        """Test committing a vote during commit phase."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.commitVote.return_value = mock_tx_builder

        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = (
            b"0x" + b"a" * 64
        )
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {
            "status": 1
        }

        commitment = b"0x" + b"c" * 32
        result = connected_client.commit_vote(b"proposal_id", commitment)

        assert result is not None
        connected_client._contract.functions.commitVote.assert_called_once_with(
            b"proposal_id", commitment
        )

    def test_reveal_vote(self, connected_client):
        """Test revealing a vote during reveal phase."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.revealVote.return_value = mock_tx_builder

        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = (
            b"0x" + b"b" * 64
        )
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {
            "status": 1
        }

        salt = b"0x" + b"s" * 32
        result = connected_client.reveal_vote(b"proposal_id", support=True, salt=salt)

        assert result is not None
        connected_client._contract.functions.revealVote.assert_called_once_with(
            b"proposal_id", True, salt
        )

    def test_compute_vote_commitment(self, connected_client):
        """Test computing vote commitment hash."""
        expected_hash = b"0x" + b"h" * 32
        connected_client._contract.functions.computeVoteCommitment.return_value.call.return_value = expected_hash

        salt = b"0x" + b"s" * 32
        result = connected_client.compute_vote_commitment(b"proposal_id", True, salt)

        assert result == expected_hash
        connected_client._contract.functions.computeVoteCommitment.assert_called_once_with(
            b"proposal_id", True, salt
        )

    def test_get_proposal_phase(self, connected_client):
        """Test getting proposal phase."""
        import time

        current_time = int(time.time())
        connected_client._contract.functions.getProposalPhase.return_value.call.return_value = (
            True,  # is_commit_phase
            False,  # is_reveal_phase
            False,  # is_ended
            current_time + 3600,  # commit_deadline
            current_time + 7200,  # reveal_deadline
        )

        result = connected_client.get_proposal_phase(b"proposal_id")

        assert result["is_commit_phase"] is True
        assert result["is_reveal_phase"] is False
        assert result["is_ended"] is False
        assert result["commit_deadline"] is not None
        assert result["reveal_deadline"] is not None

    def test_execute_proposal_passed(self, connected_client):
        """Test executing a passed proposal."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.executeProposal.return_value = mock_tx_builder

        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = (
            b"0x" + b"c" * 64
        )
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {
            "status": 1
        }

        # Mock get_proposal to return a passed proposal
        connected_client._contract.functions.getProposal.return_value.call.return_value = (
            b"consortium_id",
            0,  # proposal_type
            "0x" + "3" * 40,  # proposer
            1,  # status (PASSED)
            10,  # yes_votes
            2,  # no_votes
            1704153600,  # expires_at
            True,  # executed
        )

        tx_hash, passed = connected_client.execute_proposal(b"proposal_id")

        assert tx_hash is not None
        assert passed is True

    def test_get_proposal_returns_info(self, connected_client):
        """Test get_proposal returns ProposalInfo."""
        connected_client._contract.functions.getProposal.return_value.call.return_value = (
            b"consortium_id",
            0,  # proposal_type (ADD_MEMBER)
            "0x" + "3" * 40,  # proposer
            0,  # status (ACTIVE)
            5,  # yes_votes
            1,  # no_votes
            1704153600,  # expires_at
            False,  # executed
        )

        result = connected_client.get_proposal(b"proposal_id")

        assert isinstance(result, ProposalInfo)
        assert result.proposal_type == ProposalType.ADD_MEMBER
        assert result.status == ProposalStatus.ACTIVE
        assert result.yes_votes == 5

    def test_get_proposal_count(self, connected_client):
        """Test get_proposal_count returns count."""
        connected_client._contract.functions.getProposalCount.return_value.call.return_value = 15

        result = connected_client.get_proposal_count(b"consortium_id")

        assert result == 15


class TestGovernanceClientAudit:
    """Tests for audit trail operations."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected GovernanceClient."""
        with patch("sdk.blockchain.governance.client.BlockchainConnector") as mock_conn_class:
            with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
                mock_web3.to_checksum_address.return_value = "0x" + "1" * 40

                mock_connector = MagicMock()
                mock_connector.address = "0x" + "2" * 40

                mock_contract = MagicMock()
                mock_connector.get_contract.return_value = mock_contract

                mock_conn_class.return_value = mock_connector

                from sdk.blockchain.governance.client import GovernanceClient

                client = GovernanceClient("0x" + "1" * 40)
                client.connect("a" * 64)

                client._mock_connector = mock_connector
                client._mock_contract = mock_contract

                return client

    def test_get_audit_trail_length(self, connected_client):
        """Test get_audit_trail_length returns length."""
        connected_client._contract.functions.getAuditTrailLength.return_value.call.return_value = 25

        result = connected_client.get_audit_trail_length(b"consortium_id")

        assert result == 25

    def test_get_audit_event_returns_info(self, connected_client):
        """Test get_audit_event returns AuditEvent."""
        connected_client._contract.functions.getAuditEvent.return_value.call.return_value = (
            b"event_id",
            1,  # event_type (MEMBER_JOINED)
            "0x" + "3" * 40,  # actor
            b"target_id",
            1704067200,  # timestamp
            b"previous_hash",
        )

        result = connected_client.get_audit_event(b"consortium_id", 0)

        assert isinstance(result, AuditEvent)
        assert result.event_type == AuditEventType.MEMBER_JOINED

    def test_get_full_audit_trail(self, connected_client):
        """Test get_full_audit_trail returns all events."""
        connected_client._contract.functions.getAuditTrailLength.return_value.call.return_value = 3
        connected_client._contract.functions.getAuditEvent.return_value.call.side_effect = [
            (b"event_0", 0, "0x" + "1" * 40, b"target", 1704067200, b"hash"),
            (b"event_1", 1, "0x" + "2" * 40, b"target", 1704153600, b"hash"),
            (b"event_2", 4, "0x" + "3" * 40, b"target", 1704240000, b"hash"),
        ]

        result = connected_client.get_full_audit_trail(b"consortium_id")

        assert len(result) == 3
        assert result[0].event_type == AuditEventType.CONSORTIUM_CREATED
        assert result[1].event_type == AuditEventType.MEMBER_JOINED

    def test_verify_audit_trail(self, connected_client):
        """Test verify_audit_trail returns bool."""
        connected_client._contract.functions.verifyAuditTrail.return_value.call.return_value = True

        result = connected_client.verify_audit_trail(b"consortium_id")

        assert result is True


class TestGovernanceClientRewards:
    """Tests for reward distribution."""

    @pytest.fixture
    def connected_client(self):
        """Create a connected GovernanceClient."""
        with patch("sdk.blockchain.governance.client.BlockchainConnector") as mock_conn_class:
            with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
                mock_web3.to_checksum_address.return_value = "0x" + "1" * 40

                mock_connector = MagicMock()
                mock_connector.address = "0x" + "2" * 40
                mock_connector.get_nonce.return_value = 5
                mock_connector.get_gas_price.return_value = 20000000000
                mock_connector.config.chain_id = 421614

                mock_contract = MagicMock()
                mock_connector.get_contract.return_value = mock_contract

                mock_account = MagicMock()
                mock_account.sign_transaction.return_value = MagicMock(raw_transaction=b"signed")
                mock_connector.account = mock_account

                mock_conn_class.return_value = mock_connector

                from sdk.blockchain.governance.client import GovernanceClient

                client = GovernanceClient("0x" + "1" * 40)
                client.connect("a" * 64)

                client._mock_connector = mock_connector
                client._mock_contract = mock_contract

                return client

    def test_distribute_rewards(self, connected_client):
        """Test distribute_rewards sends transaction with value."""
        mock_tx_builder = MagicMock()
        mock_tx_builder.build_transaction.return_value = {}
        connected_client._contract.functions.distributeRewards.return_value = mock_tx_builder

        connected_client._mock_connector.web3.eth.send_raw_transaction.return_value = (
            b"0x" + b"d" * 64
        )
        connected_client._mock_connector.web3.eth.wait_for_transaction_receipt.return_value = {
            "status": 1
        }

        result = connected_client.distribute_rewards(
            b"consortium_id",
            amount_wei=1000000000000000000,  # 1 ETH
        )

        assert result is not None
        # Verify that the transaction included a value
        call_args = mock_tx_builder.build_transaction.call_args[0][0]
        assert "value" in call_args
        assert call_args["value"] == 1000000000000000000


class TestGovernanceClientHelpers:
    """Tests for helper methods."""

    def test_hash_config(self):
        """Test _hash_config produces consistent hashes."""
        with patch("sdk.blockchain.governance.client.BlockchainConnector"):
            with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
                mock_web3.to_checksum_address.return_value = "0x" + "1" * 40
                mock_web3.keccak.return_value = b"config_hash"

                from sdk.blockchain.governance.client import GovernanceClient

                client = GovernanceClient("0x" + "1" * 40)

                config = {"model_type": "linear", "epochs": 100}
                result = client._hash_config(config)

                assert result == b"config_hash"

    def test_compute_data_hash(self):
        """Test compute_data_hash static method."""
        with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
            mock_web3.keccak.return_value = b"data_hash"

            from sdk.blockchain.governance.client import GovernanceClient

            result = GovernanceClient.compute_data_hash(b"test_data")

            mock_web3.keccak.assert_called_once_with(b"test_data")
            assert result == b"data_hash"

    def test_get_explorer_url(self):
        """Test get_explorer_url delegates to connector."""
        with patch("sdk.blockchain.governance.client.BlockchainConnector") as mock_conn_class:
            with patch("sdk.blockchain.governance.client.Web3") as mock_web3:
                mock_web3.to_checksum_address.return_value = "0x" + "1" * 40

                mock_connector = MagicMock()
                mock_connector.get_explorer_url.return_value = "https://arbiscan.io/tx/0xabc"
                mock_conn_class.return_value = mock_connector

                from sdk.blockchain.governance.client import GovernanceClient

                client = GovernanceClient("0x" + "1" * 40)
                result = client.get_explorer_url("0xabc")

                assert result == "https://arbiscan.io/tx/0xabc"
