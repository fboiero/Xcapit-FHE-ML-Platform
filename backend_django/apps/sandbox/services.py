"""
Sandbox services for Xcapit FHE-ML Platform.

Provides the consortium demo service that runs real FHE training
comparisons for the sandbox experience.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
from django.db import models
from django.utils import timezone

from apps.core.services.base import BaseService, ServiceResult

logger = logging.getLogger(__name__)

# Tier limits for sandbox consortium demo
TIER_DEMO_LIMITS: dict[str, dict[str, int]] = {
    "free": {"max_samples_per_member": 20, "max_members": 3, "max_features": 3, "daily_runs": 5},
    "starter": {"max_samples_per_member": 200, "max_members": 5, "max_features": 10, "daily_runs": 50},
    "professional": {"max_samples_per_member": 5000, "max_members": 20, "max_features": 50, "daily_runs": 500},
    "enterprise": {"max_samples_per_member": -1, "max_members": -1, "max_features": -1, "daily_runs": -1},
}


class ConsortiumDemoService(BaseService):
    """
    Runs the real FHE consortium demo with TenSEAL CKKS encryption.

    Generates synthetic data for N members, trains local models,
    trains a consortium model, and returns comparison metrics.
    """

    def run_demo(
        self,
        members: list[dict[str, Any]],
        tier: str = "free",
    ) -> ServiceResult[dict[str, Any]]:
        """
        Execute a consortium demo with FHE encryption.

        Args:
            members: List of member configs, each with:
                - name: str
                - samples: int
                - age_range: [min, max]
                - bmi_bias: float
                - severity_bias: float
            tier: User's tier for limit enforcement.

        Returns:
            ServiceResult with full comparison metrics.
        """
        limits = TIER_DEMO_LIMITS.get(tier, TIER_DEMO_LIMITS["free"])

        # Enforce tier limits
        if limits["max_members"] != -1 and len(members) > limits["max_members"]:
            return ServiceResult.fail(
                f"Tier '{tier}' allows max {limits['max_members']} members. "
                f"Upgrade to add more.",
                error_code="tier_limit_members",
            )

        for m in members:
            max_s = limits["max_samples_per_member"]
            if max_s != -1 and m.get("samples", 20) > max_s:
                return ServiceResult.fail(
                    f"Tier '{tier}' allows max {max_s} samples per member. "
                    f"Upgrade for larger datasets.",
                    error_code="tier_limit_samples",
                )

        try:
            result = self._execute_fhe_demo(members)
            return ServiceResult.ok(result)
        except ImportError:
            logger.warning("TenSEAL not available, running simulated demo")
            result = self._execute_simulated_demo(members)
            return ServiceResult.ok(result)
        except Exception as e:
            logger.exception("Consortium demo failed: %s", str(e))
            return ServiceResult.fail(str(e), error_code="demo_failed")

    def _execute_fhe_demo(self, members: list[dict]) -> dict[str, Any]:
        """Run the real FHE demo with TenSEAL."""
        from sdk.encryption.context_manager import CKKSParameters, SecurityLevel
        from sdk.models.linear_regression import LinearRegression
        from sdk.utils.data_loader import SecureDataLoader

        np.random.seed(42)

        params = CKKSParameters(
            poly_modulus_degree=8192,
            coeff_mod_bit_sizes=(60, 40, 40, 60),
            scale=2**40,
            security_level=SecurityLevel.TC128,
        )

        # Generate data for each member
        member_data: dict[str, dict] = {}
        all_dfs = []

        for m in members:
            df = self._generate_patient_data(
                n_samples=m.get("samples", 20),
                age_range=tuple(m.get("age_range", [18, 90])),
                bmi_bias=m.get("bmi_bias", 0),
                severity_bias=m.get("severity_bias", 0),
            )
            member_data[m["name"]] = {"df": df}
            all_dfs.append(df)

        # Generate test data
        np.random.seed(99)
        import pandas as pd

        test_df = self._generate_patient_data(200, (18, 90), 0, 0)
        np.random.seed(42)

        # Build global scaler
        all_combined = pd.concat([*[md["df"] for md in member_data.values()], test_df])
        X_all = all_combined[["edad", "bmi", "severidad"]].values
        y_all = all_combined["costo_tratamiento"].values

        x_min, x_max = X_all.min(axis=0), X_all.max(axis=0)
        x_range = x_max - x_min
        x_range[x_range == 0] = 1.0
        y_min, y_max = float(y_all.min()), float(y_all.max())
        y_range = y_max - y_min if y_max != y_min else 1.0

        def norm_X(X: np.ndarray) -> np.ndarray:
            return 2.0 * (X - x_min) / x_range - 1.0

        def norm_y(y: np.ndarray) -> np.ndarray:
            return 2.0 * (y - y_min) / y_range - 1.0

        def denorm_y(y_n: np.ndarray) -> np.ndarray:
            return (y_n + 1.0) / 2.0 * y_range + y_min

        X_test_norm = norm_X(test_df[["edad", "bmi", "severidad"]].values)
        y_test_raw = test_df["costo_tratamiento"].values

        t_start = time.time()

        # Encrypt each member's data
        encrypted_members = {}
        loaders = {}
        encryption_details = []

        for name, md in member_data.items():
            df = md["df"]
            X_norm = norm_X(df[["edad", "bmi", "severidad"]].values)
            y_norm = norm_y(df["costo_tratamiento"].values)

            df_norm = pd.DataFrame(X_norm, columns=["edad", "bmi", "severidad"])
            df_norm["costo"] = y_norm

            loader = SecureDataLoader(params=params, normalize=False)
            t0 = time.time()
            enc_ds = loader.encrypt(df_norm, target_column="costo")
            t_enc = time.time() - t0

            encrypted_members[name] = enc_ds
            loaders[name] = loader

            sample_row = enc_ds.X[0]
            cipher_bytes = sample_row.serialize()
            encryption_details.append({
                "name": name,
                "samples": len(df),
                "encryption_time_s": round(t_enc, 2),
                "ciphertext_size_bytes": len(cipher_bytes),
            })

        # Encrypt consortium data
        cons_df = pd.concat([md["df"] for md in member_data.values()])
        X_cons_norm = norm_X(cons_df[["edad", "bmi", "severidad"]].values)
        y_cons_norm = norm_y(cons_df["costo_tratamiento"].values)

        df_cons_norm = pd.DataFrame(X_cons_norm, columns=["edad", "bmi", "severidad"])
        df_cons_norm["costo"] = y_cons_norm

        cons_loader = SecureDataLoader(params=params, normalize=False)
        t0 = time.time()
        enc_consortium = cons_loader.encrypt(df_cons_norm, target_column="costo")
        t_cons_enc = time.time() - t0

        # Train local models
        local_results = []
        for name, enc_ds in encrypted_members.items():
            loader = loaders[name]
            model = LinearRegression(
                learning_rate=0.05,
                n_epochs=300,
                early_stopping_patience=30,
                tolerance=1e-6,
                encryptor=loader.encryptor,
            )
            model.fit(enc_ds)

            y_pred_norm = model.predict_plaintext(X_test_norm)
            y_pred_real = denorm_y(y_pred_norm)

            ss_res = np.sum((y_test_raw - y_pred_real) ** 2)
            ss_tot = np.sum((y_test_raw - np.mean(y_test_raw)) ** 2)
            r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
            mae = float(np.mean(np.abs(y_test_raw - y_pred_real)))

            df_orig = member_data[name]["df"]
            local_results.append({
                "name": name,
                "samples": len(df_orig),
                "r2": round(r2, 4),
                "mae": round(mae, 2),
                "age_mean": round(float(df_orig["edad"].mean()), 1),
                "age_range": [round(float(df_orig["edad"].min())), round(float(df_orig["edad"].max()))],
                "bmi_mean": round(float(df_orig["bmi"].mean()), 1),
                "severity_mean": round(float(df_orig["severidad"].mean()), 2),
                "cost_mean": round(float(df_orig["costo_tratamiento"].mean()), 0),
            })

        # Train consortium model
        cons_model = LinearRegression(
            learning_rate=0.05,
            n_epochs=300,
            early_stopping_patience=30,
            tolerance=1e-6,
            encryptor=cons_loader.encryptor,
        )
        cons_model.fit(enc_consortium)

        y_pred_cons_norm = cons_model.predict_plaintext(X_test_norm)
        y_pred_cons_real = denorm_y(y_pred_cons_norm)

        ss_res_c = np.sum((y_test_raw - y_pred_cons_real) ** 2)
        ss_tot_c = np.sum((y_test_raw - np.mean(y_test_raw)) ** 2)
        r2_cons = float(1 - ss_res_c / ss_tot_c) if ss_tot_c > 0 else 0.0
        mae_cons = float(np.mean(np.abs(y_test_raw - y_pred_cons_real)))

        total_time = time.time() - t_start

        avg_local_r2 = sum(r["r2"] for r in local_results) / len(local_results)
        avg_local_mae = sum(r["mae"] for r in local_results) / len(local_results)

        mae_reduction = ((avg_local_mae - mae_cons) / avg_local_mae * 100) if avg_local_mae else 0

        # Sample predictions
        np.random.seed(77)
        sample_idx = np.random.choice(200, 5, replace=False)
        predictions = []
        for idx in sample_idx:
            row = {
                "real": round(float(y_test_raw[idx]), 0),
                "consortium": round(float(y_pred_cons_real[idx]), 0),
                "error": round(float(abs(y_test_raw[idx] - y_pred_cons_real[idx])), 0),
            }
            predictions.append(row)

        return {
            "fhe_real": True,
            "encryption": {
                "scheme": "CKKS",
                "security_bits": 128,
                "poly_degree": 8192,
                "scale": "2^40",
                "members": encryption_details,
                "consortium_encryption_time_s": round(t_cons_enc, 2),
            },
            "local_results": local_results,
            "consortium_result": {
                "total_samples": int(enc_consortium.n_samples),
                "r2": round(r2_cons, 4),
                "mae": round(mae_cons, 2),
            },
            "improvement": {
                "r2_local_avg": round(avg_local_r2, 4),
                "r2_consortium": round(r2_cons, 4),
                "r2_delta": round(r2_cons - avg_local_r2, 4),
                "mae_local_avg": round(avg_local_mae, 2),
                "mae_consortium": round(mae_cons, 2),
                "mae_reduction_pct": round(mae_reduction, 1),
            },
            "sample_predictions": predictions,
            "total_time_s": round(total_time, 2),
            "test_set_size": 200,
        }

    def _execute_simulated_demo(self, members: list[dict]) -> dict[str, Any]:
        """Fallback simulated demo when TenSEAL is not available."""
        np.random.seed(42)

        local_results = []
        total_samples = 0

        for m in members:
            n = m.get("samples", 20)
            total_samples += n
            age_range = m.get("age_range", [18, 90])
            span = age_range[1] - age_range[0]
            r2 = max(0.3, min(0.99, 0.5 + span / 200 + n / 100))
            mae = max(200, 3000 - r2 * 2500)

            local_results.append({
                "name": m["name"],
                "samples": n,
                "r2": round(r2, 4),
                "mae": round(mae, 2),
                "age_mean": round((age_range[0] + age_range[1]) / 2, 1),
                "age_range": age_range,
                "bmi_mean": round(25 + m.get("bmi_bias", 0), 1),
                "severity_mean": round(2.5 + m.get("severity_bias", 0), 2),
                "cost_mean": round(12000 + m.get("bmi_bias", 0) * 500, 0),
            })

        avg_r2 = sum(r["r2"] for r in local_results) / len(local_results)
        avg_mae = sum(r["mae"] for r in local_results) / len(local_results)
        cons_r2 = min(0.99, avg_r2 + 0.15)
        cons_mae = max(200, avg_mae * 0.35)

        return {
            "fhe_real": False,
            "simulated": True,
            "encryption": {
                "scheme": "CKKS (simulated)",
                "security_bits": 128,
                "poly_degree": 8192,
                "scale": "2^40",
                "members": [
                    {"name": m["name"], "samples": m.get("samples", 20),
                     "encryption_time_s": 0.5, "ciphertext_size_bytes": 334000}
                    for m in members
                ],
            },
            "local_results": local_results,
            "consortium_result": {
                "total_samples": total_samples,
                "r2": round(cons_r2, 4),
                "mae": round(cons_mae, 2),
            },
            "improvement": {
                "r2_local_avg": round(avg_r2, 4),
                "r2_consortium": round(cons_r2, 4),
                "r2_delta": round(cons_r2 - avg_r2, 4),
                "mae_local_avg": round(avg_mae, 2),
                "mae_consortium": round(cons_mae, 2),
                "mae_reduction_pct": round((avg_mae - cons_mae) / avg_mae * 100, 1),
            },
            "sample_predictions": [],
            "total_time_s": 0.1,
            "test_set_size": 200,
        }

    @staticmethod
    def _generate_patient_data(
        n_samples: int,
        age_range: tuple[float, float],
        bmi_bias: float,
        severity_bias: float,
    ):
        """Generate synthetic patient data with known linear relationship."""
        import pandas as pd

        age = np.random.uniform(*age_range, n_samples)
        bmi = np.random.normal(25 + bmi_bias, 3.5, n_samples).clip(16, 48)
        severity = np.random.beta(2 + severity_bias, 5, n_samples) * 10
        cost = (
            200.0 * age + 150.0 * bmi + 300.0 * severity
            - 500.0 + np.random.normal(0, 250, n_samples)
        )
        cost = cost.clip(500, None)

        return pd.DataFrame({
            "edad": age, "bmi": bmi,
            "severidad": severity, "costo_tratamiento": cost,
        })

    @staticmethod
    def get_tier_limits(tier: str = "free") -> dict:
        """Return tier limits for display."""
        return TIER_DEMO_LIMITS.get(tier, TIER_DEMO_LIMITS["free"])


# =============================================================================
# TRIAL SERVICE
# =============================================================================


class TrialService(BaseService):
    """
    Manages company trial lifecycle: start → enforce limits → upgrade.
    """

    def start_trial(self, company) -> ServiceResult:
        """Start a 14-day trial for a company on the FREE tier."""
        from .models import Subscription

        if company.tier != company.Tier.FREE:
            return ServiceResult.fail(
                "Solo las empresas en tier FREE pueden iniciar un trial.",
                error_code="already_paid",
            )

        if company.trial_started_at is not None:
            return ServiceResult.fail(
                "Esta empresa ya tiene un trial activo o finalizado.",
                error_code="trial_already_started",
            )

        company.start_trial()

        # Create subscription record
        now = timezone.now()
        sub, _ = Subscription.objects.get_or_create(
            company=company,
            defaults={
                "plan": "free",
                "status": Subscription.Status.TRIALING,
                "trial_end": company.trial_expires_at,
                "current_period_start": now,
                "current_period_end": company.trial_expires_at,
            },
        )

        return ServiceResult.ok({
            "trial_started_at": company.trial_started_at,
            "trial_expires_at": company.trial_expires_at,
            "trial_days": company.TRIAL_DURATION_DAYS,
            "subscription_id": str(sub.id),
        })

    def get_usage_summary(self, company) -> ServiceResult:
        """Return current usage vs limits for the company."""
        from apps.core.models import UsageTracking
        from apps.consortiums.models import ConsortiumMember
        from .models import DataUpload, Sandbox

        today_usage = UsageTracking.objects.filter(
            company=company,
            date=timezone.now().date(),
        ).first()

        total_uploaded = (
            DataUpload.objects.filter(company=company)
            .aggregate(total=models.Sum("file_size"))["total"]
            or 0
        )

        active_sandboxes = Sandbox.objects.filter(
            owner=company, status="active"
        ).count()

        active_consortiums = ConsortiumMember.objects.filter(
            company=company, status="active"
        ).count()

        return ServiceResult.ok({
            "tier": company.tier,
            "is_trial": company.is_trial,
            "trial_days_remaining": company.trial_days_remaining,
            "trial_expired": company.trial_expired,
            "usage": {
                "api_requests_today": today_usage.api_requests if today_usage else 0,
                "training_runs_today": today_usage.training_runs if today_usage else 0,
                "data_uploaded_bytes": total_uploaded,
                "active_sandboxes": active_sandboxes,
                "active_consortiums": active_consortiums,
            },
            "limits": {
                "daily_requests": company.daily_limit,
                "training_runs_per_day": company.training_limit,
                "upload_bytes": company.upload_limit,
                "max_sandboxes": company.sandbox_limit,
                "max_consortiums": company.consortium_limit,
                "max_models": company.model_limit,
                "rate_limit_rpm": company.rate_limit,
            },
        })

    def check_upload_allowed(self, company, file_size: int) -> ServiceResult:
        """Check if a data upload is allowed under the company's tier limits."""
        from .models import DataUpload

        if company.trial_expired:
            return ServiceResult.fail(
                "El periodo de prueba ha expirado. Upgrade para continuar.",
                error_code="trial_expired",
            )

        if company.upload_limit == -1:
            return ServiceResult.ok({"allowed": True})

        total_uploaded = (
            DataUpload.objects.filter(company=company)
            .aggregate(total=models.Sum("file_size"))["total"]
            or 0
        )

        if total_uploaded + file_size > company.upload_limit:
            return ServiceResult.fail(
                f"Limite de upload excedido. "
                f"Usado: {total_uploaded / 1024 / 1024:.1f} MB / "
                f"{company.upload_limit / 1024 / 1024:.0f} MB. "
                f"Upgrade para subir mas datos.",
                error_code="upload_limit_exceeded",
            )

        return ServiceResult.ok({
            "allowed": True,
            "used_bytes": total_uploaded,
            "remaining_bytes": company.upload_limit - total_uploaded,
        })

    def check_training_allowed(self, company) -> ServiceResult:
        """Check if the company can run another training today."""
        from apps.core.models import UsageTracking

        if company.trial_expired:
            return ServiceResult.fail(
                "El periodo de prueba ha expirado. Upgrade para continuar.",
                error_code="trial_expired",
            )

        if company.training_limit == -1:
            return ServiceResult.ok({"allowed": True})

        today_usage = UsageTracking.objects.filter(
            company=company,
            date=timezone.now().date(),
        ).first()

        runs_today = today_usage.training_runs if today_usage else 0

        if runs_today >= company.training_limit:
            return ServiceResult.fail(
                f"Limite de training alcanzado ({runs_today}/{company.training_limit} "
                f"runs hoy). Upgrade para mas capacidad.",
                error_code="training_limit_exceeded",
            )

        return ServiceResult.ok({
            "allowed": True,
            "runs_today": runs_today,
            "remaining": company.training_limit - runs_today,
        })

    def request_upgrade(self, company, target_tier: str) -> ServiceResult:
        """
        Process an upgrade request. In production this would integrate
        with Stripe or another payment provider. For now it updates
        the tier directly.
        """
        from .models import Subscription

        valid_tiers = ["starter", "professional", "enterprise"]
        if target_tier not in valid_tiers:
            return ServiceResult.fail(
                f"Tier invalido. Opciones: {', '.join(valid_tiers)}",
                error_code="invalid_tier",
            )

        tier_order = {"free": 0, "starter": 1, "professional": 2, "enterprise": 3}
        if tier_order.get(target_tier, 0) <= tier_order.get(company.tier, 0):
            return ServiceResult.fail(
                "Solo se puede hacer upgrade a un tier superior.",
                error_code="invalid_upgrade",
            )

        old_tier = company.tier
        company.tier = target_tier
        company.trial_expires_at = None  # Clear trial expiry
        company.save(update_fields=["tier", "trial_expires_at", "updated_at"])

        # Update subscription
        sub = getattr(company, "subscription", None)
        if sub:
            sub.activate(target_tier, period_days=30)
        else:
            now = timezone.now()
            sub = Subscription.objects.create(
                company=company,
                plan=target_tier,
                status=Subscription.Status.ACTIVE,
                current_period_start=now,
                current_period_end=now + timezone.timedelta(days=30),
            )

        return ServiceResult.ok({
            "old_tier": old_tier,
            "new_tier": target_tier,
            "subscription_id": str(sub.id),
            "period_end": sub.current_period_end,
        })

    @staticmethod
    def get_plans_comparison() -> list[dict]:
        """Return plan comparison data for the pricing page."""
        from apps.core.models import Company

        plans = []
        for tier_value, tier_label in Company.Tier.choices:
            plans.append({
                "tier": tier_value,
                "name": tier_label,
                "rate_limit_rpm": Company.TIER_RATE_LIMITS[tier_value],
                "daily_requests": Company.TIER_DAILY_LIMITS[tier_value],
                "max_models": Company.TIER_MODEL_LIMITS[tier_value],
                "max_consortiums": Company.TIER_CONSORTIUM_LIMITS[tier_value],
                "max_upload_mb": (
                    -1 if Company.TIER_UPLOAD_LIMITS[tier_value] == -1
                    else Company.TIER_UPLOAD_LIMITS[tier_value] / 1024 / 1024
                ),
                "training_runs_per_day": Company.TIER_TRAINING_LIMITS[tier_value],
                "max_sandboxes": Company.TIER_SANDBOX_LIMITS[tier_value],
            })
        return plans
