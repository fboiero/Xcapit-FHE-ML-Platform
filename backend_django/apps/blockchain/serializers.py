"""
Blockchain API serializers for Xcapit FHE-ML Platform.

Serializers for blockchain status, transactions, and contract interactions.
"""

from rest_framework import serializers


class BlockchainStatusSerializer(serializers.Serializer):
    """Serializer for blockchain connection status."""

    connected = serializers.BooleanField()
    network = serializers.CharField()
    chain_id = serializers.IntegerField(allow_null=True)
    circuit_breaker = serializers.DictField()


class TransactionResultSerializer(serializers.Serializer):
    """Serializer for blockchain transaction results."""

    success = serializers.BooleanField()
    tx_hash = serializers.CharField(allow_null=True)
    block_number = serializers.IntegerField(allow_null=True)
    gas_used = serializers.IntegerField(allow_null=True)
    error = serializers.CharField(allow_null=True)


class WalletBalanceSerializer(serializers.Serializer):
    """Serializer for wallet balance response."""

    address = serializers.CharField()
    balance_wei = serializers.CharField()
    balance_eth = serializers.FloatField()


class ConsortiumCreateSerializer(serializers.Serializer):
    """Serializer for creating a consortium on-chain."""

    name = serializers.CharField(max_length=100)
    min_voting_quorum = serializers.IntegerField(min_value=1, max_value=100)
    voting_duration = serializers.IntegerField(min_value=3600)  # Minimum 1 hour
    model_config_hash = serializers.CharField(max_length=66)


class ConsortiumIdSerializer(serializers.Serializer):
    """Serializer for consortium ID parameter."""

    consortium_id = serializers.CharField(max_length=66)


class AddMemberSerializer(serializers.Serializer):
    """Serializer for adding a member to consortium."""

    consortium_id = serializers.CharField(max_length=66)
    member_address = serializers.CharField(max_length=42)


class ContributionSerializer(serializers.Serializer):
    """Serializer for recording a contribution."""

    consortium_id = serializers.CharField(max_length=66)
    record_count = serializers.IntegerField(min_value=1)
    feature_count = serializers.IntegerField(min_value=1)
    data_hash = serializers.CharField(max_length=66)
    checksum_hash = serializers.CharField(max_length=66)


class ConsortiumResponseSerializer(serializers.Serializer):
    """Serializer for consortium details response."""

    name = serializers.CharField()
    owner = serializers.CharField()
    status = serializers.IntegerField()
    member_count = serializers.IntegerField()
    total_contributions = serializers.IntegerField()
    min_voting_quorum = serializers.IntegerField()
    voting_duration = serializers.IntegerField()


class MemberResponseSerializer(serializers.Serializer):
    """Serializer for member details response."""

    status = serializers.IntegerField()
    joined_at = serializers.IntegerField()
    contribution_count = serializers.IntegerField()
    contribution_weight = serializers.IntegerField()
    last_contribution_at = serializers.IntegerField()


class ModelRegisterSerializer(serializers.Serializer):
    """Serializer for registering a model on-chain."""

    model_type = serializers.CharField(max_length=50)
    version = serializers.CharField(max_length=20)


class CheckpointSerializer(serializers.Serializer):
    """Serializer for saving a model checkpoint."""

    model_id = serializers.CharField(max_length=66)
    epoch = serializers.IntegerField(min_value=0)
    weights_hash = serializers.CharField(max_length=66)
    metrics_hash = serializers.CharField(max_length=66)


class ModelResponseSerializer(serializers.Serializer):
    """Serializer for model details response."""

    owner = serializers.CharField()
    model_type = serializers.CharField()
    version = serializers.CharField()
    weights_hash = serializers.CharField()
    created_at = serializers.IntegerField()
    updated_at = serializers.IntegerField()
    verified = serializers.BooleanField()
    active = serializers.BooleanField()


class VerifyCheckpointSerializer(serializers.Serializer):
    """Serializer for verifying a checkpoint."""

    model_id = serializers.CharField(max_length=66)
    epoch = serializers.IntegerField(min_value=0)
    weights_hash = serializers.CharField(max_length=66)


class ComputationSerializer(serializers.Serializer):
    """Serializer for registering a computation."""

    model_id = serializers.CharField(max_length=66)
    input_hash = serializers.CharField(max_length=66)
    output_hash = serializers.CharField(max_length=66)
    proof_hash = serializers.CharField(max_length=66, required=False)


class BatchComputationSerializer(serializers.Serializer):
    """Serializer for batch computation registration."""

    model_id = serializers.CharField(max_length=66)
    input_hashes = serializers.ListField(child=serializers.CharField(max_length=66))
    output_hashes = serializers.ListField(child=serializers.CharField(max_length=66))


class VerifyOutputSerializer(serializers.Serializer):
    """Serializer for verifying computation output."""

    model_id = serializers.CharField(max_length=66)
    input_hash = serializers.CharField(max_length=66)
    output_hash = serializers.CharField(max_length=66)


class VerifyOutputResponseSerializer(serializers.Serializer):
    """Serializer for verification response."""

    valid = serializers.BooleanField()
    proof_hash = serializers.CharField()
