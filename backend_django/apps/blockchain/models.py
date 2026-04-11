"""
Blockchain models for Xcapit FHE-ML Platform.

Registro de transacciones on-chain, despliegues de contratos inteligentes
y eventos de blockchain para auditoría y trazabilidad.
"""

import uuid

from django.db import models


class Transaction(models.Model):
    """Registro de transacción on-chain."""

    class Network(models.TextChoices):
        ARBITRUM_ONE = "arbitrum-one", "Arbitrum One"
        ARBITRUM_SEPOLIA = "arbitrum-sepolia", "Arbitrum Sepolia"
        ETHEREUM_MAINNET = "ethereum-mainnet", "Ethereum Mainnet"
        ETHEREUM_SEPOLIA = "ethereum-sepolia", "Ethereum Sepolia"

    class TxType(models.TextChoices):
        DEPLOY_CONTRACT = "deploy_contract", "Deploy Contract"
        REGISTER_MODEL = "register_model", "Register Model"
        SUBMIT_PROOF = "submit_proof", "Submit Proof"
        GOVERNANCE_VOTE = "governance_vote", "Governance Vote"
        REWARD_DISTRIBUTION = "reward_distribution", "Reward Distribution"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"
        REVERTED = "reverted", "Reverted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="blockchain_transactions",
    )
    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.SET_NULL,
        related_name="blockchain_transactions",
        null=True,
        blank=True,
    )

    tx_hash = models.CharField(max_length=66, unique=True, db_index=True)
    block_number = models.BigIntegerField(null=True, blank=True)
    network = models.CharField(
        max_length=30,
        choices=Network.choices,
        default=Network.ARBITRUM_SEPOLIA,
    )
    tx_type = models.CharField(max_length=30, choices=TxType.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    gas_used = models.BigIntegerField(null=True, blank=True)
    gas_price = models.BigIntegerField(null=True, blank=True)
    value_wei = models.CharField(max_length=78, default="0")

    from_address = models.CharField(max_length=42)
    to_address = models.CharField(max_length=42, blank=True)
    contract_address = models.CharField(max_length=42, blank=True)

    input_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "transaction"
        verbose_name_plural = "transactions"
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["network", "block_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.tx_type} — {self.tx_hash[:12]}… ({self.status})"


class SmartContractDeployment(models.Model):
    """Registro de contrato inteligente desplegado."""

    class ContractType(models.TextChoices):
        GOVERNANCE = "governance", "Governance"
        MODEL_REGISTRY = "model_registry", "Model Registry"
        COMPUTATION_VERIFIER = "computation_verifier", "Computation Verifier"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="smart_contract_deployments",
    )
    consortium = models.ForeignKey(
        "consortiums.Consortium",
        on_delete=models.SET_NULL,
        related_name="smart_contract_deployments",
        null=True,
        blank=True,
    )

    contract_type = models.CharField(max_length=30, choices=ContractType.choices)
    address = models.CharField(max_length=42, unique=True, db_index=True)
    network = models.CharField(
        max_length=30,
        choices=Transaction.Network.choices,
        default=Transaction.Network.ARBITRUM_SEPOLIA,
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        related_name="contract_deployments",
        null=True,
        blank=True,
    )

    abi = models.JSONField(default=list)
    bytecode_hash = models.CharField(max_length=66, blank=True)
    version = models.CharField(max_length=20, default="1.0.0")
    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "smart contract deployment"
        verbose_name_plural = "smart contract deployments"
        indexes = [
            models.Index(fields=["company", "contract_type"]),
            models.Index(fields=["network", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.contract_type} @ {self.address[:12]}… (v{self.version})"


class BlockchainEvent(models.Model):
    """Evento emitido por un contrato inteligente."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    contract = models.ForeignKey(
        SmartContractDeployment,
        on_delete=models.CASCADE,
        related_name="events",
    )

    event_name = models.CharField(max_length=100, db_index=True)
    block_number = models.BigIntegerField(db_index=True)
    tx_hash = models.CharField(max_length=66, db_index=True)
    args = models.JSONField(default=dict)
    processed = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "blockchain event"
        verbose_name_plural = "blockchain events"
        indexes = [
            models.Index(fields=["contract", "event_name"]),
            models.Index(fields=["processed"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_name} @ block {self.block_number}"
