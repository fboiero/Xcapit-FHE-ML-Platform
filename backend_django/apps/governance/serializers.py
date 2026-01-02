"""
Governance serializers for Xcapit FHE-ML Platform.
"""

from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import AuditEvent, Proposal, RewardDistribution, Vote


class ProposalSerializer(serializers.ModelSerializer):
    """Serializer for Proposal model."""

    proposer_name = serializers.CharField(source="proposer.name", read_only=True)
    total_voters = serializers.IntegerField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Proposal
        fields = [
            "id",
            "consortium",
            "proposer",
            "proposer_name",
            "proposal_type",
            "title",
            "description",
            "data",
            "status",
            "yes_votes",
            "no_votes",
            "voting_weight_yes",
            "voting_weight_no",
            "total_voters",
            "blockchain_tx",
            "created_at",
            "expires_at",
            "executed_at",
            "is_expired",
        ]
        read_only_fields = [
            "id",
            "proposer",
            "status",
            "yes_votes",
            "no_votes",
            "voting_weight_yes",
            "voting_weight_no",
            "blockchain_tx",
            "created_at",
            "executed_at",
        ]


class ProposalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a Proposal."""

    voting_days = serializers.IntegerField(
        write_only=True,
        default=7,
        min_value=1,
        max_value=30,
    )

    class Meta:
        model = Proposal
        fields = [
            "consortium",
            "proposal_type",
            "title",
            "description",
            "data",
            "voting_days",
        ]

    def validate_title(self, value):
        """Validate title length."""
        if len(value) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters.")
        return value

    def validate_data(self, value):
        """Validate proposal data based on type."""
        proposal_type = self.initial_data.get("proposal_type")

        if proposal_type == Proposal.Type.ADD_MEMBER:
            if "company_email" not in value:
                raise serializers.ValidationError("company_email is required for add_member proposals.")

        if proposal_type == Proposal.Type.DISTRIBUTE_REWARDS:
            if "amount" not in value:
                raise serializers.ValidationError("amount is required for distribute_rewards proposals.")

        return value

    def create(self, validated_data):
        """Create proposal with expiration."""
        voting_days = validated_data.pop("voting_days")
        proposer = self.context["request"].user.company

        proposal = Proposal.objects.create(
            proposer=proposer,
            expires_at=timezone.now() + timedelta(days=voting_days),
            **validated_data,
        )

        return proposal


class VoteSerializer(serializers.ModelSerializer):
    """Serializer for Vote model."""

    voter_name = serializers.CharField(source="voter.name", read_only=True)

    class Meta:
        model = Vote
        fields = [
            "id",
            "proposal",
            "voter",
            "voter_name",
            "support",
            "weight",
            "comment",
            "voted_at",
        ]
        read_only_fields = ["id", "voter", "weight", "voted_at"]


class VoteCreateSerializer(serializers.ModelSerializer):
    """Serializer for casting a Vote."""

    class Meta:
        model = Vote
        fields = ["proposal", "support", "comment"]

    def validate_comment(self, value):
        """Validate comment length."""
        if value and len(value) > 500:
            raise serializers.ValidationError("Comment must be at most 500 characters.")
        return value


class AuditEventSerializer(serializers.ModelSerializer):
    """Serializer for AuditEvent model."""

    actor_name = serializers.CharField(source="actor.name", read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "consortium",
            "actor",
            "actor_name",
            "event_type",
            "target_id",
            "target_type",
            "data",
            "previous_hash",
            "event_hash",
            "blockchain_tx",
            "created_at",
        ]
        read_only_fields = fields


class RewardDistributionSerializer(serializers.ModelSerializer):
    """Serializer for RewardDistribution model."""

    class Meta:
        model = RewardDistribution
        fields = [
            "id",
            "consortium",
            "total_amount",
            "currency",
            "distributions",
            "blockchain_tx",
            "distributed_at",
        ]
        read_only_fields = fields


class RewardDistributionCreateSerializer(serializers.Serializer):
    """Serializer for creating a reward distribution."""

    consortium_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=20, decimal_places=8, min_value=0.00000001)

    def validate_amount(self, value):
        """Validate amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return value
