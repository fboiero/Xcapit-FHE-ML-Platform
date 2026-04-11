"""
URL configuration para la app de Consortiums.

Endpoints:
  /consortiums/                              — CRUD de consorcios
  /consortiums/{id}/members/                 — listar miembros
  /consortiums/{id}/members/join/            — solicitar unirse
  /consortiums/{id}/members/leave/           — abandonar consorcio
  /consortiums/{id}/contributions/           — pruebas de contribución (solo lectura)
  /consortiums/{id}/training-results/        — resultados de entrenamiento (solo lectura)
  /invitations/                              — listar/crear invitaciones
  /invitations/{id}/accept/                  — aceptar invitación
  /invitations/{id}/reject/                  — rechazar invitación

  Crypto endpoints:
  /consortiums/{id}/zkp/verify-contribution/ — verificar contribución con ZKP
  /consortiums/{id}/zkp/verify-accuracy/     — verificar precisión de modelo con ZKP
  /consortiums/{id}/mpc/setup-keys/          — generar claves Shamir
  /consortiums/{id}/mpc/aggregate/           — agregación segura MPC
  /consortiums/{id}/dp/privatize/            — privatizar datos con DP
  /consortiums/{id}/dp/budget-check/         — verificar presupuesto de privacidad
  /consortiums/{id}/crypto/status/           — estado de módulos criptográficos
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views_crypto import (
    CryptoStatusView,
    DPBudgetCheckView,
    DPPrivatizeView,
    MPCAggregateView,
    MPCSetupKeysView,
    ZKPVerifyContributionView,
    ZKPVerifyModelAccuracyView,
)

# Router principal para consorcios e invitaciones
router = DefaultRouter()
router.register(r"consortiums", views.ConsortiumViewSet, basename="consortium")
router.register(r"invitations", views.ConsortiumInvitationViewSet, basename="invitation")
# Also register invitations under /consortiums/invitations/ for nested access
consortium_invitations_router = DefaultRouter()
consortium_invitations_router.register(
    r"consortiums/invitations", views.ConsortiumInvitationViewSet, basename="consortium-invitation"
)

# Routers anidados para recursos dentro de un consorcio
members_router = DefaultRouter()
members_router.register(r"members", views.ConsortiumMemberViewSet, basename="consortium-member")

contributions_router = DefaultRouter()
contributions_router.register(
    r"contributions", views.ContributionProofViewSet, basename="consortium-contribution"
)

training_results_router = DefaultRouter()
training_results_router.register(
    r"training-results", views.TrainingResultViewSet, basename="consortium-training-result"
)

urlpatterns = [
    # Invitations at /consortiums/invitations/ must come BEFORE the main router
    # so it is matched before consortiums/<pk>/ catches it
    path("", include(consortium_invitations_router.urls)),
    # Rutas principales
    path("", include(router.urls)),
    # Rutas anidadas bajo /consortiums/{consortium_pk}/
    path(
        "consortiums/<uuid:consortium_pk>/",
        include(members_router.urls),
    ),
    path(
        "consortiums/<uuid:consortium_pk>/",
        include(contributions_router.urls),
    ),
    path(
        "consortiums/<uuid:consortium_pk>/",
        include(training_results_router.urls),
    ),
    # ── Crypto endpoints ───────────────────────────────────────────────
    path(
        "consortiums/<uuid:consortium_pk>/zkp/verify-contribution/",
        ZKPVerifyContributionView.as_view(),
        name="consortium-zkp-verify-contribution",
    ),
    path(
        "consortiums/<uuid:consortium_pk>/zkp/verify-accuracy/",
        ZKPVerifyModelAccuracyView.as_view(),
        name="consortium-zkp-verify-accuracy",
    ),
    path(
        "consortiums/<uuid:consortium_pk>/mpc/setup-keys/",
        MPCSetupKeysView.as_view(),
        name="consortium-mpc-setup-keys",
    ),
    path(
        "consortiums/<uuid:consortium_pk>/mpc/aggregate/",
        MPCAggregateView.as_view(),
        name="consortium-mpc-aggregate",
    ),
    path(
        "consortiums/<uuid:consortium_pk>/dp/privatize/",
        DPPrivatizeView.as_view(),
        name="consortium-dp-privatize",
    ),
    path(
        "consortiums/<uuid:consortium_pk>/dp/budget-check/",
        DPBudgetCheckView.as_view(),
        name="consortium-dp-budget-check",
    ),
    path(
        "consortiums/<uuid:consortium_pk>/crypto/status/",
        CryptoStatusView.as_view(),
        name="consortium-crypto-status",
    ),
]
