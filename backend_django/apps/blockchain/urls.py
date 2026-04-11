"""
Blockchain API URL configuration.

Provides endpoints for:
- Transaction history (ViewSet)
- Smart contract deployments (ViewSet)
- Status and health
- Consortium management
- Model registry
- Computation verification
"""

from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BlockchainStatusView,
    CheckpointSaveView,
    CheckpointVerifyView,
    ComputationBatchView,
    ComputationRegisterView,
    ComputationVerifyView,
    ConsortiumAddMemberView,
    ConsortiumCreateView,
    ConsortiumDetailView,
    ConsortiumMemberView,
    ContractAddressesView,
    ContributionRecordView,
    ModelDetailView,
    ModelRegisterView,
    SmartContractViewSet,
    TransactionViewSet,
    WalletBalanceView,
)

app_name = "blockchain"

router = DefaultRouter()
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"contracts", SmartContractViewSet, basename="contract")

urlpatterns = [
    # Router-based ViewSets
    path("", include(router.urls)),
    # Status
    path("status/", BlockchainStatusView.as_view(), name="status"),
    path("contract-addresses/", ContractAddressesView.as_view(), name="contract-addresses"),
    path("balance/<str:address>/", WalletBalanceView.as_view(), name="balance"),
    # Consortium
    path("consortium/create/", ConsortiumCreateView.as_view(), name="consortium-create"),
    path("consortium/add-member/", ConsortiumAddMemberView.as_view(), name="consortium-add-member"),
    path("consortium/contribution/", ContributionRecordView.as_view(), name="consortium-contribution"),
    path("consortium/<str:consortium_id>/", ConsortiumDetailView.as_view(), name="consortium-detail"),
    path(
        "consortium/<str:consortium_id>/member/<str:address>/",
        ConsortiumMemberView.as_view(),
        name="consortium-member",
    ),
    # Model Registry
    path("model/register/", ModelRegisterView.as_view(), name="model-register"),
    path("model/checkpoint/", CheckpointSaveView.as_view(), name="model-checkpoint"),
    path("model/checkpoint/verify/", CheckpointVerifyView.as_view(), name="model-checkpoint-verify"),
    path("model/<str:model_id>/", ModelDetailView.as_view(), name="model-detail"),
    # Computation Verifier
    path("computation/register/", ComputationRegisterView.as_view(), name="computation-register"),
    path("computation/batch/", ComputationBatchView.as_view(), name="computation-batch"),
    path("computation/verify/", ComputationVerifyView.as_view(), name="computation-verify"),
]
