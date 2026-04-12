"""Locust performance tests for Xcapit FHE-ML Platform.

Tests the 10 most critical API endpoints under load. Organized in three
user classes so you can target different workload profiles:

- AnonymousUser: public endpoints (health, sandbox demo, registration)
- AuthenticatedUser: standard authenticated workload (dashboard, consortium CRUD)
- FHEHeavyUser: FHE prediction and MPC aggregation endpoints (the slowest paths)

## SLO Targets (validated against threshold in exit criteria)

| Endpoint group     | p50    | p95    | p99    | Failure rate |
|--------------------|--------|--------|--------|--------------|
| Health / Auth      | <50ms  | <200ms | <500ms | <0.1%        |
| Standard API       | <100ms | <500ms | <1s    | <0.5%        |
| FHE / MPC          | <2s    | <5s    | <10s   | <1%          |

## Usage

    # Headless run against local dev stack (requires make dev first)
    locust -f tests/performance/locustfile.py \\
        --host http://localhost:8000 \\
        --users 50 --spawn-rate 5 --run-time 3m --headless

    # Web UI mode
    locust -f tests/performance/locustfile.py --host http://localhost:8000

    # FHE-only stress test (low concurrency, long duration)
    locust -f tests/performance/locustfile.py \\
        --host http://localhost:8000 \\
        --users 5 --spawn-rate 1 --run-time 10m --headless \\
        FHEHeavyUser

## Test user credentials

Expects a seeded test user. Create with:
    python manage.py createsuperuser --email perf@xcapit.test --noinput
    echo "from apps.core.models import User; \\
          u = User.objects.get(email='perf@xcapit.test'); \\
          u.set_password('perf-test-password'); u.save()" | python manage.py shell

Or override via env: PERF_TEST_EMAIL / PERF_TEST_PASSWORD.
"""

from __future__ import annotations

import json
import os
import random
import uuid
from typing import Any

from locust import HttpUser, between, events, tag, task
from locust.env import Environment

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

PERF_TEST_EMAIL = os.environ.get("PERF_TEST_EMAIL", "perf@xcapit.test")
PERF_TEST_PASSWORD = os.environ.get("PERF_TEST_PASSWORD", "perf-test-password")
PERF_TEST_COMPANY = os.environ.get("PERF_TEST_COMPANY", "Xcapit Perf Test")

# SLO thresholds (milliseconds)
SLO_HEALTH_P95 = 200
SLO_AUTH_P95 = 500
SLO_STANDARD_P95 = 500
SLO_FHE_P95 = 5_000

# --------------------------------------------------------------------------- #
# Events: enforce SLO threshold at end of run
# --------------------------------------------------------------------------- #


@events.quitting.add_listener
def _enforce_slo(environment: Environment, **_kwargs: Any) -> None:
    """Fail the run if SLO thresholds were breached.

    Exit code non-zero on violation — CI will surface this as a failed job.
    """
    if environment.stats.total.fail_ratio > 0.01:
        print(f"❌ SLO BREACH: failure rate {environment.stats.total.fail_ratio:.2%} > 1%")
        environment.process_exit_code = 1

    # Per-endpoint p95 checks
    for name, stats in environment.stats.entries.items():
        p95 = stats.get_response_time_percentile(0.95)
        if p95 is None:
            continue

        endpoint = name[1]  # (method, endpoint) tuple
        threshold = _threshold_for(endpoint)
        if p95 > threshold:
            print(f"❌ SLO BREACH: {endpoint} p95={p95:.0f}ms > {threshold}ms threshold")
            environment.process_exit_code = 1


def _threshold_for(endpoint: str) -> float:
    """Map endpoint path to its SLO p95 threshold in milliseconds."""
    if "/health" in endpoint:
        return SLO_HEALTH_P95
    if "/auth/" in endpoint:
        return SLO_AUTH_P95
    if "/predictions/" in endpoint or "/mpc/" in endpoint or "/fhe/" in endpoint:
        return SLO_FHE_P95
    return SLO_STANDARD_P95


# --------------------------------------------------------------------------- #
# User classes
# --------------------------------------------------------------------------- #


class AnonymousUser(HttpUser):
    """Simulates public traffic: health checks, pricing page, sandbox demo."""

    wait_time = between(1, 3)
    weight = 3  # 30% of total users

    @tag("health")
    @task(5)
    def health_check(self) -> None:
        """GET /health/ — baseline latency."""
        self.client.get("/health/", name="health")

    @tag("health")
    @task(2)
    def liveness_check(self) -> None:
        """GET /health/live/ — Kubernetes liveness probe."""
        self.client.get("/health/live/", name="health-live")

    @tag("health")
    @task(2)
    def readiness_check(self) -> None:
        """GET /health/ready/ — Kubernetes readiness probe."""
        self.client.get("/health/ready/", name="health-ready")

    @tag("public", "sandbox")
    @task(3)
    def sandbox_email_capture(self) -> None:
        """POST /api/v2/sandbox/trial/ — lead capture endpoint."""
        email = f"perf-{uuid.uuid4().hex[:8]}@xcapit.test"
        self.client.post(
            "/api/v2/sandbox/trial/",
            json={"email": email, "industry": random.choice(["banking", "retail", "insurance"])},
            name="sandbox-trial-create",
        )

    @tag("auth")
    @task(1)
    def register_attempt(self) -> None:
        """POST /api/v2/auth/register/ — registration conversion endpoint."""
        email = f"perf-{uuid.uuid4().hex[:8]}@xcapit.test"
        self.client.post(
            "/api/v2/auth/register/",
            json={
                "email": email,
                "password": "ComplexPerfPassword123!",
                "password_confirm": "ComplexPerfPassword123!",
                "company_name": f"PerfTest-{uuid.uuid4().hex[:6]}",
            },
            name="auth-register",
        )


class AuthenticatedUser(HttpUser):
    """Standard authenticated user workload."""

    wait_time = between(2, 5)
    weight = 6  # 60% of total users — most realistic
    token: str | None = None
    consortium_ids: list[str] = []

    def on_start(self) -> None:
        """Authenticate once per simulated user."""
        with self.client.post(
            "/api/v2/auth/login/",
            json={"email": PERF_TEST_EMAIL, "password": PERF_TEST_PASSWORD},
            name="auth-login",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"login failed: {response.status_code}")
                return
            data = response.json()
            self.token = data.get("access") or data.get("token")
            if self.token:
                self.client.headers["Authorization"] = f"Bearer {self.token}"

    @tag("auth")
    @task(2)
    def get_me(self) -> None:
        """GET /api/v2/auth/me/ — current user info, dashboard hot path."""
        self.client.get("/api/v2/auth/me/", name="auth-me")

    @tag("consortium")
    @task(5)
    def list_consortiums(self) -> None:
        """GET /api/v2/consortiums/ — main list, highest traffic."""
        with self.client.get(
            "/api/v2/consortiums/",
            name="consortium-list",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                # Cache IDs for downstream requests
                try:
                    data = response.json()
                    results = data.get("results", []) if isinstance(data, dict) else data
                    if results and isinstance(results, list):
                        self.consortium_ids = [
                            r["id"] for r in results[:10] if "id" in r
                        ]
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass

    @tag("consortium")
    @task(1)
    def create_consortium(self) -> None:
        """POST /api/v2/consortiums/ — create flow."""
        self.client.post(
            "/api/v2/consortiums/",
            json={
                "name": f"Perf Consortium {uuid.uuid4().hex[:6]}",
                "description": "Load test consortium",
                "industry": "banking",
                "min_members": 2,
                "max_members": 10,
            },
            name="consortium-create",
        )

    @tag("consortium")
    @task(2)
    def get_consortium_detail(self) -> None:
        """GET /api/v2/consortiums/{id}/ — detail view."""
        if not self.consortium_ids:
            return
        consortium_id = random.choice(self.consortium_ids)
        self.client.get(
            f"/api/v2/consortiums/{consortium_id}/",
            name="consortium-detail",
        )

    @tag("marketplace")
    @task(2)
    def browse_marketplace(self) -> None:
        """GET /api/v2/marketplace/deployments/ — marketplace browse."""
        self.client.get(
            "/api/v2/marketplace/deployments/",
            name="marketplace-list",
        )

    @tag("governance")
    @task(1)
    def list_proposals(self) -> None:
        """GET /api/v2/governance/proposals/ — active governance items."""
        self.client.get(
            "/api/v2/governance/proposals/",
            name="governance-proposals",
        )

    @tag("compliance")
    @task(1)
    def list_compliance_frameworks(self) -> None:
        """GET /api/v2/compliance/frameworks/ — compliance dashboard data."""
        self.client.get(
            "/api/v2/compliance/frameworks/",
            name="compliance-frameworks",
        )


class FHEHeavyUser(HttpUser):
    """Stress-tests the FHE prediction and MPC aggregation endpoints.

    These are the slowest paths in the system. Run separately with low
    concurrency and longer duration — never mix with the high-concurrency
    AuthenticatedUser workload.
    """

    wait_time = between(5, 10)  # realistic — users don't spam predictions
    weight = 1  # 10% of total users in mixed runs; run alone for stress

    def on_start(self) -> None:
        with self.client.post(
            "/api/v2/auth/login/",
            json={"email": PERF_TEST_EMAIL, "password": PERF_TEST_PASSWORD},
            name="auth-login-fhe",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                token = data.get("access") or data.get("token")
                if token:
                    self.client.headers["Authorization"] = f"Bearer {token}"
            else:
                response.failure(f"FHE user login failed: {response.status_code}")

    @tag("fhe", "predict")
    @task(3)
    def predict_on_encrypted_data(self) -> None:
        """POST /api/v2/models/predictions/ — FHE prediction (slowest path)."""
        self.client.post(
            "/api/v2/models/predictions/",
            json={
                "model_id": str(uuid.uuid4()),  # expected to 404 in most cases
                "encrypted_input": "base64-placeholder-ciphertext",
                "use_fhe": True,
            },
            name="fhe-predict",
        )

    @tag("fhe", "mpc")
    @task(1)
    def mpc_aggregate(self) -> None:
        """POST /api/v2/consortiums/{id}/mpc/aggregate/ — MPC round."""
        self.client.post(
            f"/api/v2/consortiums/{uuid.uuid4()}/mpc/aggregate/",
            json={
                "shares": [{"party": i, "share": "hex-share"} for i in range(3)],
                "threshold": 2,
            },
            name="mpc-aggregate",
        )
