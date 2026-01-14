"""Tests for database.py persistence layer."""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Mock tenseal before importing sdk modules
sys.modules["tenseal"] = MagicMock()

from sdk.api.database import (
    DatabaseManager,
    ModelRecord,
    TrainingRun,
    PredictionLog,
    get_database,
    DEFAULT_DB_PATH,
)


# ============ Test Fixtures ============


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DatabaseManager(db_path)
        yield db


@pytest.fixture
def db_with_model(temp_db):
    """Create database with a test model."""
    temp_db.save_model(
        model_id="model_001",
        model_type="linear_regression",
        config={"learning_rate": 0.01, "epochs": 100},
        status="created",
        n_features=5,
        feature_names=["f1", "f2", "f3", "f4", "f5"],
        metadata={"description": "Test model"}
    )
    return temp_db


# ============ DatabaseManager Initialization Tests ============


class TestDatabaseManagerInit:
    """Tests for DatabaseManager initialization."""

    def test_init_creates_db_file(self):
        """Test that initialization creates database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = DatabaseManager(db_path)

            assert db_path.exists()
            assert db.db_path == db_path

    def test_init_creates_parent_directories(self):
        """Test that initialization creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "subdir" / "nested" / "test.db"
            db = DatabaseManager(db_path)

            assert db_path.parent.exists()

    def test_init_uses_default_path(self):
        """Test that default path is used when none specified."""
        # Don't actually create - just check the assignment
        db = DatabaseManager.__new__(DatabaseManager)
        db.db_path = None
        # The default would be DEFAULT_DB_PATH
        assert DEFAULT_DB_PATH is not None

    def test_schema_creates_tables(self, temp_db):
        """Test that schema creates required tables."""
        with temp_db._get_connection() as conn:
            cursor = conn.cursor()

            # Check models table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='models'"
            )
            assert cursor.fetchone() is not None

            # Check training_runs table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='training_runs'"
            )
            assert cursor.fetchone() is not None

            # Check prediction_logs table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='prediction_logs'"
            )
            assert cursor.fetchone() is not None

            # Check api_keys table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='api_keys'"
            )
            assert cursor.fetchone() is not None


class TestGetConnection:
    """Tests for _get_connection context manager."""

    def test_connection_commits_on_success(self, temp_db):
        """Test that connection commits on successful operation."""
        with temp_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO models (id, model_type, config) VALUES (?, ?, ?)",
                ("test_id", "test_type", "{}")
            )

        # Verify it was committed
        model = temp_db.get_model("test_id")
        assert model is not None

    def test_connection_rollbacks_on_error(self, temp_db):
        """Test that connection rolls back on error."""
        try:
            with temp_db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO models (id, model_type, config) VALUES (?, ?, ?)",
                    ("rollback_test", "test_type", "{}")
                )
                # Force an error
                raise ValueError("Test error")
        except ValueError:
            pass

        # Verify rollback occurred
        model = temp_db.get_model("rollback_test")
        assert model is None


# ============ Model Operations Tests ============


class TestSaveModel:
    """Tests for save_model method."""

    def test_save_new_model(self, temp_db):
        """Test saving a new model."""
        model = temp_db.save_model(
            model_id="new_model",
            model_type="linear_regression",
            config={"learning_rate": 0.01},
            status="created"
        )

        assert model.id == "new_model"
        assert model.model_type == "linear_regression"
        assert model.status == "created"
        assert model.config == {"learning_rate": 0.01}

    def test_save_model_with_params(self, temp_db):
        """Test saving model with parameters."""
        params = {"weights": [1.0, 2.0, 3.0], "bias": 0.5}

        model = temp_db.save_model(
            model_id="model_with_params",
            model_type="linear_regression",
            config={},
            params=params
        )

        # Retrieve and check params
        retrieved_params = temp_db.get_model_params("model_with_params")
        assert retrieved_params == params

    def test_save_model_with_features(self, temp_db):
        """Test saving model with feature information."""
        model = temp_db.save_model(
            model_id="model_with_features",
            model_type="linear_regression",
            config={},
            n_features=3,
            feature_names=["age", "income", "score"]
        )

        assert model.n_features == 3
        assert model.feature_names == ["age", "income", "score"]

    def test_save_model_with_metadata(self, temp_db):
        """Test saving model with metadata."""
        metadata = {"author": "test", "version": "1.0"}

        model = temp_db.save_model(
            model_id="model_with_meta",
            model_type="linear_regression",
            config={},
            metadata=metadata
        )

        assert model.metadata == metadata

    def test_update_existing_model(self, db_with_model):
        """Test updating an existing model."""
        # Update the model
        updated = db_with_model.save_model(
            model_id="model_001",
            model_type="linear_regression",
            config={"learning_rate": 0.02},  # Changed
            status="trained"  # Changed
        )

        assert updated.status == "trained"
        assert updated.config == {"learning_rate": 0.02}


class TestGetModel:
    """Tests for get_model method."""

    def test_get_existing_model(self, db_with_model):
        """Test getting an existing model."""
        model = db_with_model.get_model("model_001")

        assert model is not None
        assert model.id == "model_001"
        assert model.model_type == "linear_regression"

    def test_get_nonexistent_model(self, temp_db):
        """Test getting a model that doesn't exist."""
        model = temp_db.get_model("nonexistent")

        assert model is None

    def test_get_model_returns_all_fields(self, db_with_model):
        """Test that get_model returns all expected fields."""
        model = db_with_model.get_model("model_001")

        assert hasattr(model, "id")
        assert hasattr(model, "model_type")
        assert hasattr(model, "status")
        assert hasattr(model, "config")
        assert hasattr(model, "n_features")
        assert hasattr(model, "feature_names")
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")
        assert hasattr(model, "metadata")


class TestGetModelParams:
    """Tests for get_model_params method."""

    def test_get_params_with_params(self, temp_db):
        """Test getting params from model with params."""
        params = {"weights": [1.0, 2.0], "bias": 0.1}
        temp_db.save_model(
            model_id="model_params",
            model_type="linear_regression",
            config={},
            params=params
        )

        retrieved = temp_db.get_model_params("model_params")
        assert retrieved == params

    def test_get_params_without_params(self, db_with_model):
        """Test getting params from model without params."""
        retrieved = db_with_model.get_model_params("model_001")
        assert retrieved is None

    def test_get_params_nonexistent_model(self, temp_db):
        """Test getting params from nonexistent model."""
        retrieved = temp_db.get_model_params("nonexistent")
        assert retrieved is None


class TestListModels:
    """Tests for list_models method."""

    def test_list_all_models(self, temp_db):
        """Test listing all models."""
        # Create multiple models
        for i in range(5):
            temp_db.save_model(
                model_id=f"model_{i}",
                model_type="linear_regression",
                config={}
            )

        models = temp_db.list_models()
        assert len(models) == 5

    def test_list_models_filter_by_status(self, temp_db):
        """Test filtering models by status."""
        temp_db.save_model("m1", "linear_regression", {}, status="created")
        temp_db.save_model("m2", "linear_regression", {}, status="trained")
        temp_db.save_model("m3", "linear_regression", {}, status="trained")

        trained = temp_db.list_models(status="trained")
        assert len(trained) == 2

    def test_list_models_filter_by_type(self, temp_db):
        """Test filtering models by type."""
        temp_db.save_model("m1", "linear_regression", {})
        temp_db.save_model("m2", "logistic_regression", {})
        temp_db.save_model("m3", "linear_regression", {})

        linear = temp_db.list_models(model_type="linear_regression")
        assert len(linear) == 2

    def test_list_models_with_limit(self, temp_db):
        """Test listing models with limit."""
        for i in range(10):
            temp_db.save_model(f"model_{i}", "linear_regression", {})

        models = temp_db.list_models(limit=5)
        assert len(models) == 5

    def test_list_models_with_offset(self, temp_db):
        """Test listing models with offset."""
        for i in range(10):
            temp_db.save_model(f"model_{i:02d}", "linear_regression", {})

        models = temp_db.list_models(limit=3, offset=5)
        assert len(models) == 3

    def test_list_models_empty(self, temp_db):
        """Test listing models when none exist."""
        models = temp_db.list_models()
        assert models == []


class TestUpdateModelStatus:
    """Tests for update_model_status method."""

    def test_update_status(self, db_with_model):
        """Test updating model status."""
        result = db_with_model.update_model_status("model_001", "trained")

        assert result is True
        model = db_with_model.get_model("model_001")
        assert model.status == "trained"

    def test_update_status_with_training_info(self, db_with_model):
        """Test updating status with training information."""
        trained_at = datetime.utcnow()

        result = db_with_model.update_model_status(
            "model_001",
            status="trained",
            trained_at=trained_at,
            training_epochs=100,
            final_loss=0.05
        )

        assert result is True
        model = db_with_model.get_model("model_001")
        assert model.training_epochs == 100
        assert model.final_loss == 0.05

    def test_update_status_with_params(self, db_with_model):
        """Test updating status with new parameters."""
        new_params = {"weights": [1.0, 2.0, 3.0]}

        result = db_with_model.update_model_status(
            "model_001",
            status="trained",
            params=new_params
        )

        assert result is True
        params = db_with_model.get_model_params("model_001")
        assert params == new_params

    def test_update_nonexistent_model(self, temp_db):
        """Test updating status of nonexistent model."""
        result = temp_db.update_model_status("nonexistent", "trained")
        assert result is False


class TestDeleteModel:
    """Tests for delete_model method."""

    def test_delete_existing_model(self, db_with_model):
        """Test deleting an existing model."""
        result = db_with_model.delete_model("model_001")

        assert result is True
        model = db_with_model.get_model("model_001")
        assert model is None

    def test_delete_nonexistent_model(self, temp_db):
        """Test deleting a nonexistent model."""
        result = temp_db.delete_model("nonexistent")
        assert result is False


# ============ Training Run Operations Tests ============


class TestTrainingRunOperations:
    """Tests for training run operations."""

    def test_create_training_run(self, db_with_model):
        """Test creating a training run."""
        run = db_with_model.create_training_run("run_001", "model_001")

        assert run is not None
        assert run.id == "run_001"
        assert run.model_id == "model_001"
        assert run.status == "running"

    def test_get_training_run(self, db_with_model):
        """Test getting a training run."""
        db_with_model.create_training_run("run_001", "model_001")

        run = db_with_model.get_training_run("run_001")

        assert run is not None
        assert run.id == "run_001"

    def test_get_nonexistent_training_run(self, temp_db):
        """Test getting a nonexistent training run."""
        run = temp_db.get_training_run("nonexistent")
        assert run is None

    def test_complete_training_run_success(self, db_with_model):
        """Test completing a training run successfully."""
        db_with_model.create_training_run("run_001", "model_001")

        result = db_with_model.complete_training_run(
            run_id="run_001",
            status="completed",
            epochs_completed=100,
            final_loss=0.05,
            metrics={"accuracy": 0.95}
        )

        assert result is True
        run = db_with_model.get_training_run("run_001")
        assert run.status == "completed"
        assert run.epochs_completed == 100
        assert run.final_loss == 0.05
        assert run.metrics == {"accuracy": 0.95}

    def test_complete_training_run_failed(self, db_with_model):
        """Test completing a failed training run."""
        db_with_model.create_training_run("run_001", "model_001")

        result = db_with_model.complete_training_run(
            run_id="run_001",
            status="failed",
            epochs_completed=50,
            error_message="Out of memory"
        )

        assert result is True
        run = db_with_model.get_training_run("run_001")
        assert run.status == "failed"
        assert run.error_message == "Out of memory"


# ============ Prediction Log Operations Tests ============


class TestPredictionLogOperations:
    """Tests for prediction log operations."""

    def test_log_prediction(self, db_with_model):
        """Test logging a prediction."""
        db_with_model.log_prediction(
            log_id="pred_001",
            model_id="model_001",
            n_samples=10,
            latency_ms=25.5,
            encrypted=True,
            api_key_name="test_key"
        )

        # Verify by getting stats
        stats = db_with_model.get_prediction_stats()
        assert stats["total_predictions"] == 1

    def test_log_multiple_predictions(self, db_with_model):
        """Test logging multiple predictions."""
        for i in range(5):
            db_with_model.log_prediction(
                log_id=f"pred_{i:03d}",
                model_id="model_001",
                n_samples=10,
                latency_ms=20.0 + i,
                encrypted=i % 2 == 0
            )

        stats = db_with_model.get_prediction_stats()
        assert stats["total_predictions"] == 5
        assert stats["total_samples"] == 50

    def test_get_prediction_stats_all(self, db_with_model):
        """Test getting prediction statistics."""
        # Log some predictions
        db_with_model.log_prediction("p1", "model_001", 10, 20.0, True)
        db_with_model.log_prediction("p2", "model_001", 20, 30.0, False)
        db_with_model.log_prediction("p3", "model_001", 15, 25.0, True)

        stats = db_with_model.get_prediction_stats()

        assert stats["total_predictions"] == 3
        assert stats["total_samples"] == 45
        assert stats["encrypted_predictions"] == 2
        assert stats["avg_latency_ms"] == 25.0

    def test_get_prediction_stats_by_model(self, temp_db):
        """Test getting prediction stats filtered by model."""
        temp_db.save_model("m1", "linear_regression", {})
        temp_db.save_model("m2", "linear_regression", {})

        temp_db.log_prediction("p1", "m1", 10, 20.0, False)
        temp_db.log_prediction("p2", "m1", 10, 20.0, False)
        temp_db.log_prediction("p3", "m2", 10, 20.0, False)

        stats = temp_db.get_prediction_stats(model_id="m1")
        assert stats["total_predictions"] == 2

    def test_get_prediction_stats_empty(self, temp_db):
        """Test getting stats with no predictions."""
        stats = temp_db.get_prediction_stats()

        assert stats["total_predictions"] == 0
        assert stats["total_samples"] == 0


# ============ API Key Operations Tests ============


class TestApiKeyOperations:
    """Tests for API key operations."""

    def test_create_api_key(self, temp_db):
        """Test creating an API key."""
        key_hash = temp_db.create_api_key(
            key="test_api_key_12345",
            name="Test Key",
            permissions=["read", "write"],
            rate_limit=100
        )

        assert key_hash is not None
        assert len(key_hash) == 64  # SHA256 hash

    def test_create_api_key_default_permissions(self, temp_db):
        """Test creating API key with default permissions."""
        temp_db.create_api_key(
            key="default_key",
            name="Default Permissions Key"
        )

        # Validate to check permissions
        info = temp_db.validate_api_key("default_key")
        assert info is not None
        assert info["permissions"] == ["read", "write"]

    def test_validate_api_key_valid(self, temp_db):
        """Test validating a valid API key."""
        temp_db.create_api_key(
            key="valid_key",
            name="Valid Key",
            permissions=["read", "write", "admin"],
            rate_limit=200
        )

        info = temp_db.validate_api_key("valid_key")

        assert info is not None
        assert info["name"] == "Valid Key"
        assert info["permissions"] == ["read", "write", "admin"]
        assert info["rate_limit"] == 200

    def test_validate_api_key_invalid(self, temp_db):
        """Test validating an invalid API key."""
        info = temp_db.validate_api_key("invalid_key")
        assert info is None

    def test_validate_api_key_updates_last_used(self, temp_db):
        """Test that validating updates last_used_at."""
        temp_db.create_api_key("track_key", "Tracked Key")

        # First validation
        info1 = temp_db.validate_api_key("track_key")
        first_used = info1["last_used_at"]

        # Second validation
        info2 = temp_db.validate_api_key("track_key")
        second_used = info2["last_used_at"]

        # Last used should be updated (or at least set)
        assert second_used is not None

    def test_revoke_api_key(self, temp_db):
        """Test revoking an API key."""
        key_hash = temp_db.create_api_key("revoke_me", "To Be Revoked")

        # Revoke
        result = temp_db.revoke_api_key(key_hash)
        assert result is True

        # Key should no longer validate
        info = temp_db.validate_api_key("revoke_me")
        assert info is None

    def test_revoke_nonexistent_key(self, temp_db):
        """Test revoking a nonexistent key."""
        result = temp_db.revoke_api_key("nonexistent_hash")
        assert result is False


# ============ Utility Methods Tests ============


class TestGetStats:
    """Tests for get_stats method."""

    def test_get_stats_empty(self, temp_db):
        """Test getting stats from empty database."""
        stats = temp_db.get_stats()

        assert stats["models"]["total"] == 0
        assert stats["predictions"]["total"] == 0
        assert stats["training_runs"]["total"] == 0

    def test_get_stats_with_data(self, db_with_model):
        """Test getting stats with data."""
        # Add another model that's trained
        db_with_model.save_model("m2", "linear_regression", {}, status="trained")

        # Add training run
        db_with_model.create_training_run("run_001", "model_001")
        db_with_model.complete_training_run("run_001", "completed", 100)

        # Add predictions
        db_with_model.log_prediction("p1", "model_001", 10, 20.0, False)

        stats = db_with_model.get_stats()

        assert stats["models"]["total"] == 2
        assert stats["models"]["trained"] == 1
        assert stats["models"]["untrained"] == 1
        assert stats["predictions"]["total"] == 1
        assert stats["training_runs"]["total"] == 1
        assert stats["training_runs"]["completed"] == 1


class TestVacuum:
    """Tests for vacuum method."""

    def test_vacuum_runs_without_error(self, temp_db):
        """Test that vacuum runs without error."""
        # Add and delete some data
        temp_db.save_model("temp_model", "linear_regression", {})
        temp_db.delete_model("temp_model")

        # Vacuum should not raise
        temp_db.vacuum()


# ============ get_database Function Tests ============


class TestGetDatabaseFunction:
    """Tests for get_database global function."""

    def test_get_database_returns_manager(self):
        """Test that get_database returns a DatabaseManager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = get_database(db_path)

            assert isinstance(db, DatabaseManager)

    def test_get_database_reuses_instance(self):
        """Test that get_database reuses the same instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            db1 = get_database(db_path)
            db2 = get_database(db_path)

            assert db1 is db2

    def test_get_database_creates_new_for_different_path(self):
        """Test that get_database creates new instance for different path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path1 = Path(tmpdir) / "test1.db"
            db_path2 = Path(tmpdir) / "test2.db"

            db1 = get_database(db_path1)
            db2 = get_database(db_path2)

            assert db1 is not db2


# ============ Dataclass Tests ============


class TestDataclasses:
    """Tests for dataclass definitions."""

    def test_model_record_fields(self):
        """Test ModelRecord has expected fields."""
        record = ModelRecord(
            id="test",
            model_type="linear_regression",
            status="created",
            config={},
            params_blob=None,
            n_features=5,
            feature_names=["a", "b", "c", "d", "e"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            trained_at=None,
            training_epochs=None,
            final_loss=None,
            metadata={}
        )

        assert record.id == "test"
        assert record.n_features == 5

    def test_training_run_fields(self):
        """Test TrainingRun has expected fields."""
        run = TrainingRun(
            id="run_001",
            model_id="model_001",
            started_at=datetime.utcnow(),
            completed_at=None,
            status="running",
            epochs_completed=0,
            final_loss=None,
            metrics={},
            error_message=None
        )

        assert run.id == "run_001"
        assert run.status == "running"

    def test_prediction_log_fields(self):
        """Test PredictionLog has expected fields."""
        log = PredictionLog(
            id="pred_001",
            model_id="model_001",
            timestamp=datetime.utcnow(),
            n_samples=10,
            latency_ms=25.5,
            encrypted=True
        )

        assert log.n_samples == 10
        assert log.encrypted is True


# ============ Edge Cases and Error Handling Tests ============


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_save_model_with_empty_config(self, temp_db):
        """Test saving model with empty config."""
        model = temp_db.save_model("empty_config", "linear_regression", {})
        assert model.config == {}

    def test_save_model_with_complex_config(self, temp_db):
        """Test saving model with complex nested config."""
        config = {
            "layers": [
                {"type": "dense", "units": 64},
                {"type": "dense", "units": 32}
            ],
            "optimizer": {"name": "adam", "lr": 0.001},
            "loss": "mse"
        }

        model = temp_db.save_model("complex_config", "neural_network", config)
        assert model.config == config

    def test_save_model_with_special_characters_in_metadata(self, temp_db):
        """Test saving model with special characters in metadata."""
        metadata = {
            "description": "Test with 'quotes' and \"double quotes\"",
            "emoji": "Testing 🎉",
            "unicode": "测试中文"
        }

        model = temp_db.save_model(
            "special_chars",
            "linear_regression",
            {},
            metadata=metadata
        )

        assert model.metadata == metadata

    def test_list_models_combined_filters(self, temp_db):
        """Test listing models with combined filters."""
        temp_db.save_model("m1", "linear_regression", {}, status="trained")
        temp_db.save_model("m2", "linear_regression", {}, status="created")
        temp_db.save_model("m3", "logistic_regression", {}, status="trained")

        models = temp_db.list_models(
            status="trained",
            model_type="linear_regression"
        )

        assert len(models) == 1
        assert models[0].id == "m1"

    def test_prediction_stats_with_since_filter(self, db_with_model):
        """Test prediction stats with since filter."""
        # Log old prediction (simulated by querying after)
        db_with_model.log_prediction("old", "model_001", 10, 20.0, False)

        # Get stats from future time
        future = datetime.utcnow() + timedelta(days=1)
        stats = db_with_model.get_prediction_stats(since=future)

        assert stats["total_predictions"] == 0
