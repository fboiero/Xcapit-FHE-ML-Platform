"""
Tests for apps.models.views — MLModelViewSet, TrainingRunViewSet,
BatchPredictionJobViewSet, ModelVersionViewSet, ModelExportViewSet,
ModelShareViewSet, ModelShareRequestViewSet.

Target: raise models/views.py from 37% to ~80%+ coverage.
"""

import uuid

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.consortiums.models import Consortium, ConsortiumMember
from apps.core.models import Company
from apps.models.models import (
    BatchPredictionJob,
    MLModel,
    ModelCheckpoint,
    ModelExport,
    ModelShare,
    ModelShareRequest,
    ModelVersion,
    PredictionLog,
    TrainingRun,
)

pytestmark = pytest.mark.django_db


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def company(db):
    return Company.objects.create(name="TestCo", email="test@testco.com", industry="technology")


@pytest.fixture
def other_company(db):
    return Company.objects.create(name="OtherCo", email="other@otherco.com", industry="finance")


@pytest.fixture
def user(company):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email="u@testco.com", password="pass1234", company=company
    )


@pytest.fixture
def other_user(other_company):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email="u@otherco.com", password="pass1234", company=other_company
    )


@pytest.fixture
def auth(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return c


@pytest.fixture
def other_auth(other_user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other_user).access_token}")
    return c


@pytest.fixture
def consortium(company):
    return Consortium.objects.create(
        name="TestConsortium", owner=company, status=Consortium.Status.ACTIVE
    )


@pytest.fixture
def other_consortium(other_company):
    return Consortium.objects.create(
        name="OtherConsortium", owner=other_company, status=Consortium.Status.ACTIVE
    )


@pytest.fixture
def membership(company, consortium):
    return ConsortiumMember.objects.create(
        company=company,
        consortium=consortium,
        role=ConsortiumMember.Role.OWNER,
        status=ConsortiumMember.Status.ACTIVE,
    )


@pytest.fixture
def other_membership(other_company, other_consortium):
    return ConsortiumMember.objects.create(
        company=other_company,
        consortium=other_consortium,
        role=ConsortiumMember.Role.OWNER,
        status=ConsortiumMember.Status.ACTIVE,
    )


@pytest.fixture
def trained_model(company, consortium):
    return MLModel.objects.create(
        name="Trained",
        owner=company,
        consortium=consortium,
        model_type=MLModel.ModelType.LOGISTIC_REGRESSION,
        status=MLModel.Status.TRAINED,
        n_features=5,
        feature_names=["a", "b", "c", "d", "e"],
        config={"learning_rate": 0.01},
        params={"weights": [1, 2, 3]},
        training_epochs=10,
        final_loss=0.15,
        trained_at=timezone.now(),
    )


@pytest.fixture
def created_model(company, consortium):
    return MLModel.objects.create(
        name="Created",
        owner=company,
        consortium=consortium,
        model_type=MLModel.ModelType.LINEAR_REGRESSION,
        status=MLModel.Status.CREATED,
    )


@pytest.fixture
def anomaly_model(company, consortium):
    return MLModel.objects.create(
        name="AnomalyModel",
        owner=company,
        consortium=consortium,
        model_type=MLModel.ModelType.ISOLATION_FOREST,
        status=MLModel.Status.TRAINED,
        n_features=5,
        trained_at=timezone.now(),
    )


@pytest.fixture
def timeseries_model(company, consortium):
    return MLModel.objects.create(
        name="TimeSeriesModel",
        owner=company,
        consortium=consortium,
        model_type=MLModel.ModelType.ARIMA,
        status=MLModel.Status.TRAINED,
        n_features=1,
        trained_at=timezone.now(),
    )


# ── MLModelViewSet ───────────────────────────────────────────────────


class TestMLModelViewSet:
    url = "/api/v2/models/"

    def test_list(self, auth, trained_model):
        r = auth.get(self.url)
        assert r.status_code == status.HTTP_200_OK

    def test_create(self, auth, consortium):
        r = auth.post(self.url, {
            "name": "NewModel",
            "model_type": "linear_regression",
            "consortium": str(consortium.id),
        }, format="json")
        assert r.status_code == status.HTTP_201_CREATED
        assert r.data["name"] == "NewModel"

    # ── train action ──

    def test_train_ok(self, auth, created_model):
        r = auth.post(f"{self.url}{created_model.id}/train/", {"epochs": 5}, format="json")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["detail"] == "Training started."
        created_model.refresh_from_db()
        assert created_model.status == MLModel.Status.TRAINING

    def test_train_already_training(self, auth, created_model):
        created_model.status = MLModel.Status.TRAINING
        created_model.save(update_fields=["status"])
        r = auth.post(f"{self.url}{created_model.id}/train/", format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    # ── predict action ──

    def test_predict_ok(self, auth, trained_model):
        r = auth.post(
            f"{self.url}{trained_model.id}/predict/",
            {"data": [[1, 2, 3, 4, 5]], "encrypted": False},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK
        assert "predictions" in r.data

    def test_predict_not_trained(self, auth, created_model):
        r = auth.post(
            f"{self.url}{created_model.id}/predict/",
            {"data": [[1, 2, 3]], "encrypted": False},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    # ── stats action ──

    def test_stats(self, auth, trained_model):
        r = auth.get(f"{self.url}{trained_model.id}/stats/")
        assert r.status_code == status.HTTP_200_OK
        assert "total_predictions" in r.data

    # ── checkpoints action ──

    def test_checkpoints(self, auth, trained_model):
        ModelCheckpoint.objects.create(
            model=trained_model, epoch=1, loss=0.5, weights_hash="abc123"
        )
        r = auth.get(f"{self.url}{trained_model.id}/checkpoints/")
        assert r.status_code == status.HTTP_200_OK
        assert len(r.data) == 1

    # ── detect_anomalies action ──

    def test_detect_anomalies_ok(self, auth, anomaly_model):
        r = auth.post(
            f"{self.url}{anomaly_model.id}/detect_anomalies/",
            {"data": [[1, 2, 3, 4, 5]]},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK
        assert "anomaly_scores" in r.data

    def test_detect_anomalies_wrong_model_type(self, auth, trained_model):
        r = auth.post(
            f"{self.url}{trained_model.id}/detect_anomalies/",
            {"data": [[1, 2, 3]]},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_detect_anomalies_not_trained(self, auth, company, consortium):
        m = MLModel.objects.create(
            name="untrained_anomaly",
            owner=company,
            consortium=consortium,
            model_type=MLModel.ModelType.ISOLATION_FOREST,
            status=MLModel.Status.CREATED,
        )
        r = auth.post(f"{self.url}{m.id}/detect_anomalies/", {"data": [[1]]}, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_detect_anomalies_no_data(self, auth, anomaly_model):
        r = auth.post(f"{self.url}{anomaly_model.id}/detect_anomalies/", {}, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    # ── forecast action ──

    def test_forecast_ok(self, auth, timeseries_model):
        r = auth.post(
            f"{self.url}{timeseries_model.id}/forecast/",
            {"steps": 5},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK
        assert len(r.data["forecasts"]) == 5

    def test_forecast_wrong_type(self, auth, trained_model):
        r = auth.post(f"{self.url}{trained_model.id}/forecast/", {"steps": 5}, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_forecast_not_trained(self, auth, company, consortium):
        m = MLModel.objects.create(
            name="ts_untrained",
            owner=company,
            consortium=consortium,
            model_type=MLModel.ModelType.ARIMA,
            status=MLModel.Status.CREATED,
        )
        r = auth.post(f"{self.url}{m.id}/forecast/", {"steps": 5}, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_forecast_bad_steps(self, auth, timeseries_model):
        r = auth.post(f"{self.url}{timeseries_model.id}/forecast/", {"steps": 0}, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST
        r2 = auth.post(f"{self.url}{timeseries_model.id}/forecast/", {"steps": 500}, format="json")
        assert r2.status_code == status.HTTP_400_BAD_REQUEST

    # ── tune_hyperparameters action ──

    def test_tune_ok(self, auth, trained_model):
        r = auth.post(
            f"{self.url}{trained_model.id}/tune_hyperparameters/",
            {"param_grid": {"learning_rate": [0.01, 0.1]}, "method": "random"},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK
        assert r.data["detail"] == "Hyperparameter tuning started."

    def test_tune_already_training(self, auth, created_model):
        created_model.status = MLModel.Status.TRAINING
        created_model.save(update_fields=["status"])
        r = auth.post(
            f"{self.url}{created_model.id}/tune_hyperparameters/",
            {"param_grid": {"lr": [0.01]}},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_tune_no_param_grid(self, auth, trained_model):
        r = auth.post(
            f"{self.url}{trained_model.id}/tune_hyperparameters/",
            {"method": "random"},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_tune_bad_method(self, auth, trained_model):
        r = auth.post(
            f"{self.url}{trained_model.id}/tune_hyperparameters/",
            {"param_grid": {"lr": [0.01]}, "method": "invalid"},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    # ── model_types and model_categories ──

    def test_model_types(self, auth):
        r = auth.get(f"{self.url}model_types/")
        assert r.status_code == status.HTTP_200_OK
        assert "model_types" in r.data

    def test_model_categories(self, auth):
        r = auth.get(f"{self.url}model_categories/")
        assert r.status_code == status.HTTP_200_OK
        assert "categories" in r.data
        assert "core" in r.data["categories"]

    # ── versions action ──

    def test_versions_list(self, auth, trained_model):
        trained_model.create_version(bump_type="patch", changelog="initial")
        r = auth.get(f"{self.url}{trained_model.id}/versions/")
        assert r.status_code == status.HTTP_200_OK
        assert len(r.data) == 1

    # ── create_version action ──

    def test_create_version_ok(self, auth, trained_model):
        r = auth.post(
            f"{self.url}{trained_model.id}/create_version/",
            {"bump_type": "minor", "changelog": "new feature", "release_notes": "notes"},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED
        assert r.data["version"] == "1.0.0"

    def test_create_version_not_trained(self, auth, created_model):
        r = auth.post(
            f"{self.url}{created_model.id}/create_version/",
            {"bump_type": "patch"},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    # ── publish_version action ──

    def test_publish_version_ok(self, auth, trained_model):
        v = trained_model.create_version()
        r = auth.post(f"{self.url}{trained_model.id}/versions/{v.id}/publish/")
        assert r.status_code == status.HTTP_200_OK
        v.refresh_from_db()
        assert v.status == ModelVersion.VersionStatus.PUBLISHED

    def test_publish_version_not_found(self, auth, trained_model):
        r = auth.post(f"{self.url}{trained_model.id}/versions/{uuid.uuid4()}/publish/")
        assert r.status_code == status.HTTP_404_NOT_FOUND

    # ── rollback_version action ──

    def test_rollback_version_ok(self, auth, trained_model):
        v = trained_model.create_version()
        r = auth.post(f"{self.url}{trained_model.id}/versions/{v.id}/rollback/")
        assert r.status_code == status.HTTP_200_OK
        assert "Rolled back" in r.data["detail"]

    def test_rollback_version_not_found(self, auth, trained_model):
        r = auth.post(f"{self.url}{trained_model.id}/versions/{uuid.uuid4()}/rollback/")
        assert r.status_code == status.HTTP_404_NOT_FOUND

    # ── batch_predict action ──

    def test_batch_predict_sync(self, auth, trained_model):
        r = auth.post(
            f"{self.url}{trained_model.id}/batch_predict/",
            {
                "data": [[1, 2, 3, 4, 5]],
                "encrypted": False,
                "priority": "normal",
                "async_mode": False,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK

    def test_batch_predict_async(self, auth, trained_model):
        r = auth.post(
            f"{self.url}{trained_model.id}/batch_predict/",
            {
                "data": [[1, 2, 3, 4, 5]],
                "encrypted": False,
                "priority": "high",
                "async_mode": True,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_202_ACCEPTED

    def test_batch_predict_not_trained(self, auth, created_model):
        r = auth.post(
            f"{self.url}{created_model.id}/batch_predict/",
            {"data": [[1, 2, 3]], "encrypted": False, "async_mode": False},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    # ── batch_jobs action ──

    def test_batch_jobs(self, auth, trained_model, company):
        BatchPredictionJob.objects.create(
            model=trained_model, requester=company, n_samples=10
        )
        r = auth.get(f"{self.url}{trained_model.id}/batch_jobs/")
        assert r.status_code == status.HTTP_200_OK
        assert len(r.data) == 1

    # ── export_model action ──

    def test_export_model_ok(self, auth, trained_model):
        r = auth.post(
            f"{self.url}{trained_model.id}/export_model/",
            {"format": "fheml_json", "include_weights": True},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK
        assert "export" in r.data

    def test_export_model_not_trained(self, auth, created_model):
        r = auth.post(
            f"{self.url}{created_model.id}/export_model/",
            {"format": "fheml_json"},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_export_model_with_version(self, auth, trained_model):
        v = trained_model.create_version()
        r = auth.post(
            f"{self.url}{trained_model.id}/export_model/",
            {"format": "fheml_json", "include_weights": True, "version_id": str(v.id)},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK

    def test_export_model_version_not_found(self, auth, trained_model):
        r = auth.post(
            f"{self.url}{trained_model.id}/export_model/",
            {"format": "fheml_json", "version_id": str(uuid.uuid4())},
            format="json",
        )
        assert r.status_code == status.HTTP_404_NOT_FOUND

    # ── exports action ──

    def test_exports_list(self, auth, trained_model, company):
        ModelExport.create_export(model=trained_model, exported_by=company)
        r = auth.get(f"{self.url}{trained_model.id}/exports/")
        assert r.status_code == status.HTTP_200_OK
        assert len(r.data) == 1

    # ── download_export action ──

    def test_download_export_ok(self, auth, trained_model, company):
        export = ModelExport.create_export(model=trained_model, exported_by=company)
        r = auth.get(f"{self.url}{trained_model.id}/exports/{export.id}/download/")
        assert r.status_code == status.HTTP_200_OK
        assert "data" in r.data

    def test_download_export_not_found(self, auth, trained_model):
        r = auth.get(f"{self.url}{trained_model.id}/exports/{uuid.uuid4()}/download/")
        assert r.status_code == status.HTTP_404_NOT_FOUND

    # ── import_model action ──

    def test_import_model_ok(self, auth, trained_model, company):
        export = ModelExport.create_export(model=trained_model, exported_by=company)
        r = auth.post(
            f"{self.url}import_model/",
            {"export_data": export.export_data, "new_name": "Imported Model"},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED
        assert r.data["name"] == "Imported Model"

    def test_import_model_invalid_format(self, auth):
        r = auth.post(
            f"{self.url}import_model/",
            {"export_data": {"bad": "format"}},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_import_model_with_consortium(self, auth, trained_model, company, consortium):
        export = ModelExport.create_export(model=trained_model, exported_by=company)
        r = auth.post(
            f"{self.url}import_model/",
            {
                "export_data": export.export_data,
                "consortium_id": str(consortium.id),
            },
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED

    def test_import_model_default_name(self, auth, trained_model, company):
        export = ModelExport.create_export(model=trained_model, exported_by=company)
        r = auth.post(
            f"{self.url}import_model/",
            {"export_data": export.export_data},
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED
        assert "(imported)" in r.data["name"]


# ── TrainingRunViewSet ───────────────────────────────────────────────


class TestTrainingRunViewSet:
    url = "/api/v2/models/training-runs/"

    def test_list(self, auth, trained_model):
        TrainingRun.objects.create(model=trained_model, epochs_total=10)
        r = auth.get(self.url)
        assert r.status_code == status.HTTP_200_OK

    def test_cancel_running(self, auth, trained_model):
        run = TrainingRun.objects.create(
            model=trained_model, status=TrainingRun.Status.RUNNING, epochs_total=10
        )
        r = auth.post(f"{self.url}{run.id}/cancel/")
        assert r.status_code == status.HTTP_200_OK
        run.refresh_from_db()
        assert run.status == TrainingRun.Status.CANCELLED

    def test_cancel_not_running(self, auth, trained_model):
        run = TrainingRun.objects.create(
            model=trained_model, status=TrainingRun.Status.COMPLETED, epochs_total=10
        )
        r = auth.post(f"{self.url}{run.id}/cancel/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_no_company_forbidden(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(
            email="nocompany@test.com", password="pass", company=None
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(self.url)
        assert r.status_code == status.HTTP_403_FORBIDDEN


# ── BatchPredictionJobViewSet ────────────────────────────────────────


class TestBatchPredictionJobViewSet:
    url = "/api/v2/models/batch-jobs/"

    @pytest.fixture
    def job(self, trained_model, company):
        return BatchPredictionJob.objects.create(
            model=trained_model, requester=company, n_samples=10
        )

    def test_list(self, auth, job):
        r = auth.get(self.url)
        assert r.status_code == status.HTTP_200_OK

    def test_status_action(self, auth, job):
        r = auth.get(f"{self.url}{job.id}/status/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["status"] == "pending"

    def test_results_completed(self, auth, job):
        job.start()
        job.complete([0.5] * 10, 100.0)
        r = auth.get(f"{self.url}{job.id}/results/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["predictions"] == [0.5] * 10

    def test_results_not_completed(self, auth, job):
        r = auth.get(f"{self.url}{job.id}/results/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_cancel_pending(self, auth, job):
        r = auth.post(f"{self.url}{job.id}/cancel/")
        assert r.status_code == status.HTTP_200_OK
        job.refresh_from_db()
        assert job.status == BatchPredictionJob.Status.CANCELLED

    def test_cancel_processing(self, auth, job):
        job.start()
        r = auth.post(f"{self.url}{job.id}/cancel/")
        assert r.status_code == status.HTTP_200_OK

    def test_cancel_completed(self, auth, job):
        job.start()
        job.complete([], 0)
        r = auth.post(f"{self.url}{job.id}/cancel/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST


# ── ModelVersionViewSet ──────────────────────────────────────────────


class TestModelVersionViewSet:
    url = "/api/v2/models/versions/"

    def test_list(self, auth, trained_model):
        trained_model.create_version()
        r = auth.get(self.url)
        assert r.status_code == status.HTTP_200_OK

    def test_diff_first_version(self, auth, trained_model):
        v = trained_model.create_version()
        r = auth.get(f"{self.url}{v.id}/diff/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["previous_version"] is None

    def test_diff_with_previous(self, auth, trained_model):
        trained_model.create_version(bump_type="patch", changelog="v1")
        trained_model.config = {"learning_rate": 0.05}
        trained_model.save()
        v2 = trained_model.create_version(bump_type="minor", changelog="v2")
        r = auth.get(f"{self.url}{v2.id}/diff/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["previous_version"] is not None


# ── ModelExportViewSet ───────────────────────────────────────────────


class TestModelExportViewSet:
    url = "/api/v2/models/exports/"

    def test_list(self, auth, trained_model, company):
        ModelExport.create_export(model=trained_model, exported_by=company)
        r = auth.get(self.url)
        assert r.status_code == status.HTTP_200_OK

    def test_download(self, auth, trained_model, company):
        e = ModelExport.create_export(model=trained_model, exported_by=company)
        r = auth.get(f"{self.url}{e.id}/download/")
        assert r.status_code == status.HTTP_200_OK
        assert "data" in r.data


# ── ModelShareViewSet ────────────────────────────────────────────────


class TestModelShareViewSet:
    url = "/api/v2/models/shares/"

    @pytest.fixture
    def share_setup(self, auth, trained_model, company, consortium, other_company, other_consortium, membership, other_membership):
        return {
            "auth": auth,
            "model": trained_model,
            "company": company,
            "consortium": consortium,
            "other_company": other_company,
            "target": other_consortium,
        }

    def test_create_share(self, share_setup):
        r = share_setup["auth"].post(
            self.url,
            {
                "model_id": str(share_setup["model"].id),
                "target_consortium_id": str(share_setup["target"].id),
                "share_type": "prediction_only",
                "revenue_share_percent": 10,
                "requires_approval": True,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED

    def test_create_share_no_approval(self, share_setup):
        r = share_setup["auth"].post(
            self.url,
            {
                "model_id": str(share_setup["model"].id),
                "target_consortium_id": str(share_setup["target"].id),
                "share_type": "read_only",
                "revenue_share_percent": 0,
                "requires_approval": False,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED
        share = ModelShare.objects.get(id=r.data["id"])
        assert share.status == ModelShare.Status.APPROVED

    def test_create_share_model_not_found(self, share_setup):
        r = share_setup["auth"].post(
            self.url,
            {
                "model_id": str(uuid.uuid4()),
                "target_consortium_id": str(share_setup["target"].id),
                "share_type": "prediction_only",
                "revenue_share_percent": 0,
                "requires_approval": True,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_create_share_not_owner(self, other_auth, share_setup):
        # other_auth's user doesn't own the model
        r = other_auth.post(
            self.url,
            {
                "model_id": str(share_setup["model"].id),
                "target_consortium_id": str(share_setup["target"].id),
                "share_type": "prediction_only",
                "revenue_share_percent": 0,
                "requires_approval": True,
            },
            format="json",
        )
        assert r.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_create_share_not_trained(self, share_setup, created_model):
        r = share_setup["auth"].post(
            self.url,
            {
                "model_id": str(created_model.id),
                "target_consortium_id": str(share_setup["target"].id),
                "share_type": "prediction_only",
                "revenue_share_percent": 0,
                "requires_approval": True,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_share_target_not_found(self, share_setup):
        r = share_setup["auth"].post(
            self.url,
            {
                "model_id": str(share_setup["model"].id),
                "target_consortium_id": str(uuid.uuid4()),
                "share_type": "prediction_only",
                "revenue_share_percent": 0,
                "requires_approval": True,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_create_share_duplicate(self, share_setup):
        share_setup["auth"].post(
            self.url,
            {
                "model_id": str(share_setup["model"].id),
                "target_consortium_id": str(share_setup["target"].id),
                "share_type": "prediction_only",
                "revenue_share_percent": 0,
                "requires_approval": True,
            },
            format="json",
        )
        r = share_setup["auth"].post(
            self.url,
            {
                "model_id": str(share_setup["model"].id),
                "target_consortium_id": str(share_setup["target"].id),
                "share_type": "full_access",
                "revenue_share_percent": 0,
                "requires_approval": True,
            },
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_approve_share(self, share_setup):
        share = ModelShare.objects.create(
            model=share_setup["model"],
            source_consortium=share_setup["consortium"],
            shared_by=share_setup["company"],
            target_consortium=share_setup["target"],
            status=ModelShare.Status.PENDING,
        )
        r = share_setup["auth"].post(
            f"{self.url}{share.id}/approve/",
            {"action": "approve", "message": "ok"},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK

    def test_reject_share(self, share_setup):
        share = ModelShare.objects.create(
            model=share_setup["model"],
            source_consortium=share_setup["consortium"],
            shared_by=share_setup["company"],
            target_consortium=share_setup["target"],
            status=ModelShare.Status.PENDING,
        )
        r = share_setup["auth"].post(
            f"{self.url}{share.id}/approve/",
            {"action": "reject"},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK

    def test_approve_not_pending(self, share_setup):
        share = ModelShare.objects.create(
            model=share_setup["model"],
            source_consortium=share_setup["consortium"],
            shared_by=share_setup["company"],
            target_consortium=share_setup["target"],
            status=ModelShare.Status.APPROVED,
        )
        r = share_setup["auth"].post(
            f"{self.url}{share.id}/approve/",
            {"action": "approve"},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_revoke_share(self, share_setup):
        share = ModelShare.objects.create(
            model=share_setup["model"],
            source_consortium=share_setup["consortium"],
            shared_by=share_setup["company"],
            target_consortium=share_setup["target"],
            status=ModelShare.Status.APPROVED,
        )
        r = share_setup["auth"].post(
            f"{self.url}{share.id}/revoke/",
            {"message": "revoked"},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK

    def test_revoke_not_approved(self, share_setup):
        share = ModelShare.objects.create(
            model=share_setup["model"],
            source_consortium=share_setup["consortium"],
            shared_by=share_setup["company"],
            target_consortium=share_setup["target"],
            status=ModelShare.Status.PENDING,
        )
        r = share_setup["auth"].post(
            f"{self.url}{share.id}/revoke/",
            {"message": "no"},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_received(self, auth, membership):
        r = auth.get(f"{self.url}received/")
        assert r.status_code == status.HTTP_200_OK

    def test_given(self, auth, membership):
        r = auth.get(f"{self.url}given/")
        assert r.status_code == status.HTTP_200_OK

    def test_received_no_company(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(
            email="nc@test.com", password="pass", company=None
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(f"{self.url}received/")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_given_no_company(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(
            email="nc2@test.com", password="pass", company=None
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(f"{self.url}given/")
        assert r.status_code == status.HTTP_403_FORBIDDEN


# ── ModelShareRequestViewSet ─────────────────────────────────────────


class TestModelShareRequestViewSet:
    url = "/api/v2/models/share-requests/"

    @pytest.fixture
    def req_setup(self, auth, other_auth, trained_model, company, other_company, consortium, other_consortium, membership, other_membership):
        return {
            "auth": auth,
            "other_auth": other_auth,
            "model": trained_model,
            "company": company,
            "other_company": other_company,
            "consortium": consortium,
            "other_consortium": other_consortium,
        }

    def test_create_request(self, req_setup):
        r = req_setup["other_auth"].post(
            self.url,
            {
                "model_id": str(req_setup["model"].id),
                "requested_share_type": "prediction_only",
                "message": "Please share",
            },
            format="json",
        )
        assert r.status_code == status.HTTP_201_CREATED

    def test_create_request_model_not_found(self, req_setup):
        r = req_setup["other_auth"].post(
            self.url,
            {"model_id": str(uuid.uuid4()), "requested_share_type": "prediction_only"},
            format="json",
        )
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_create_request_not_trained(self, req_setup, created_model):
        r = req_setup["other_auth"].post(
            self.url,
            {"model_id": str(created_model.id), "requested_share_type": "prediction_only"},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_request_duplicate(self, req_setup):
        req_setup["other_auth"].post(
            self.url,
            {"model_id": str(req_setup["model"].id), "requested_share_type": "prediction_only"},
            format="json",
        )
        r = req_setup["other_auth"].post(
            self.url,
            {"model_id": str(req_setup["model"].id), "requested_share_type": "full_access"},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_respond_approve(self, req_setup):
        sr = ModelShareRequest.objects.create(
            model=req_setup["model"],
            requesting_consortium=req_setup["other_consortium"],
            requested_by=req_setup["other_company"],
            requested_share_type=ModelShare.ShareType.PREDICTION_ONLY,
        )
        r = req_setup["auth"].post(
            f"{self.url}{sr.id}/respond/",
            {"action": "approve", "message": "OK"},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK
        sr.refresh_from_db()
        assert sr.status == ModelShareRequest.Status.APPROVED

    def test_respond_reject(self, req_setup):
        sr = ModelShareRequest.objects.create(
            model=req_setup["model"],
            requesting_consortium=req_setup["other_consortium"],
            requested_by=req_setup["other_company"],
            requested_share_type=ModelShare.ShareType.PREDICTION_ONLY,
        )
        r = req_setup["auth"].post(
            f"{self.url}{sr.id}/respond/",
            {"action": "reject", "message": "No"},
            format="json",
        )
        assert r.status_code == status.HTTP_200_OK
        sr.refresh_from_db()
        assert sr.status == ModelShareRequest.Status.REJECTED

    def test_respond_not_owner(self, req_setup):
        sr = ModelShareRequest.objects.create(
            model=req_setup["model"],
            requesting_consortium=req_setup["other_consortium"],
            requested_by=req_setup["other_company"],
            requested_share_type=ModelShare.ShareType.PREDICTION_ONLY,
        )
        r = req_setup["other_auth"].post(
            f"{self.url}{sr.id}/respond/",
            {"action": "approve"},
            format="json",
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_respond_not_pending(self, req_setup):
        sr = ModelShareRequest.objects.create(
            model=req_setup["model"],
            requesting_consortium=req_setup["other_consortium"],
            requested_by=req_setup["other_company"],
            requested_share_type=ModelShare.ShareType.PREDICTION_ONLY,
            status=ModelShareRequest.Status.APPROVED,
        )
        r = req_setup["auth"].post(
            f"{self.url}{sr.id}/respond/",
            {"action": "approve"},
            format="json",
        )
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_withdraw(self, req_setup):
        sr = ModelShareRequest.objects.create(
            model=req_setup["model"],
            requesting_consortium=req_setup["other_consortium"],
            requested_by=req_setup["other_company"],
            requested_share_type=ModelShare.ShareType.PREDICTION_ONLY,
        )
        r = req_setup["other_auth"].post(f"{self.url}{sr.id}/withdraw/")
        assert r.status_code == status.HTTP_200_OK
        sr.refresh_from_db()
        assert sr.status == ModelShareRequest.Status.WITHDRAWN

    def test_withdraw_not_requester(self, req_setup):
        sr = ModelShareRequest.objects.create(
            model=req_setup["model"],
            requesting_consortium=req_setup["other_consortium"],
            requested_by=req_setup["other_company"],
            requested_share_type=ModelShare.ShareType.PREDICTION_ONLY,
        )
        r = req_setup["auth"].post(f"{self.url}{sr.id}/withdraw/")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_withdraw_not_pending(self, req_setup):
        sr = ModelShareRequest.objects.create(
            model=req_setup["model"],
            requesting_consortium=req_setup["other_consortium"],
            requested_by=req_setup["other_company"],
            requested_share_type=ModelShare.ShareType.PREDICTION_ONLY,
            status=ModelShareRequest.Status.APPROVED,
        )
        r = req_setup["other_auth"].post(f"{self.url}{sr.id}/withdraw/")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_incoming(self, req_setup):
        r = req_setup["auth"].get(f"{self.url}incoming/")
        assert r.status_code == status.HTTP_200_OK

    def test_outgoing(self, req_setup):
        r = req_setup["other_auth"].get(f"{self.url}outgoing/")
        assert r.status_code == status.HTTP_200_OK

    def test_incoming_no_company(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(
            email="nc3@test.com", password="pass", company=None
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(f"{self.url}incoming/")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_outgoing_no_company(self, db):
        from django.contrib.auth import get_user_model

        u = get_user_model().objects.create_user(
            email="nc4@test.com", password="pass", company=None
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}")
        r = c.get(f"{self.url}outgoing/")
        assert r.status_code == status.HTTP_403_FORBIDDEN


# ── PredictionLogViewSet ─────────────────────────────────────────────


class TestPredictionLogViewSet:
    url = "/api/v2/models/predictions/"

    def test_list(self, auth, trained_model, company):
        PredictionLog.objects.create(
            model=trained_model, requester=company, n_samples=5, latency_ms=10.0
        )
        r = auth.get(self.url)
        assert r.status_code == status.HTTP_200_OK

    def test_filter_by_model(self, auth, trained_model, company):
        PredictionLog.objects.create(
            model=trained_model, requester=company, n_samples=5, latency_ms=10.0
        )
        r = auth.get(f"{self.url}?model_id={trained_model.id}")
        assert r.status_code == status.HTTP_200_OK
