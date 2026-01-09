"""Tests for API module (auth, database, server)."""

# Import database module directly to avoid TenSEAL dependency
import importlib.util
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sdk_api_path = project_root / "sdk" / "api"


def load_module_from_path(module_name, file_path):
    """Load a module from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Load database module
database_module = load_module_from_path("sdk.api.database", sdk_api_path / "database.py")
DatabaseManager = database_module.DatabaseManager
ModelRecord = database_module.ModelRecord
TrainingRun = database_module.TrainingRun
PredictionLog = database_module.PredictionLog


class TestDatabaseManager:
    """Tests for DatabaseManager."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = DatabaseManager(db_path)
            yield db

    def test_init_creates_tables(self, temp_db):
        """Test that initialization creates all tables."""
        with temp_db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master WHERE type='table'
            """)
            tables = {row[0] for row in cursor.fetchall()}

        assert "models" in tables
        assert "training_runs" in tables
        assert "prediction_logs" in tables
        assert "api_keys" in tables

    def test_save_model(self, temp_db):
        """Test saving a model."""
        record = temp_db.save_model(
            model_id="test_model_1",
            model_type="linear_regression",
            config={"learning_rate": 0.01},
            status="created",
        )

        assert record is not None
        assert record.id == "test_model_1"
        assert record.model_type == "linear_regression"
        assert record.status == "created"

    def test_get_model(self, temp_db):
        """Test retrieving a model."""
        temp_db.save_model(
            model_id="test_model_2",
            model_type="logistic_regression",
            config={"n_epochs": 100},
        )

        record = temp_db.get_model("test_model_2")

        assert record is not None
        assert record.id == "test_model_2"
        assert record.model_type == "logistic_regression"
        assert record.config["n_epochs"] == 100

    def test_get_model_not_found(self, temp_db):
        """Test retrieving non-existent model."""
        record = temp_db.get_model("nonexistent")
        assert record is None

    def test_list_models(self, temp_db):
        """Test listing models."""
        temp_db.save_model("model_a", "linear_regression", {})
        temp_db.save_model("model_b", "logistic_regression", {})
        temp_db.save_model("model_c", "kmeans", {})

        models = temp_db.list_models()
        assert len(models) == 3

        # Filter by type
        lr_models = temp_db.list_models(model_type="linear_regression")
        assert len(lr_models) == 1
        assert lr_models[0].model_type == "linear_regression"

    def test_update_model_status(self, temp_db):
        """Test updating model status."""
        temp_db.save_model("model_status", "linear_regression", {})

        success = temp_db.update_model_status(
            model_id="model_status",
            status="trained",
            trained_at=datetime.utcnow(),
            training_epochs=100,
            final_loss=0.01,
        )

        assert success is True

        record = temp_db.get_model("model_status")
        assert record.status == "trained"
        assert record.training_epochs == 100
        assert record.final_loss == 0.01

    def test_delete_model(self, temp_db):
        """Test deleting a model."""
        temp_db.save_model("model_delete", "linear_regression", {})

        success = temp_db.delete_model("model_delete")
        assert success is True

        record = temp_db.get_model("model_delete")
        assert record is None

    def test_delete_nonexistent_model(self, temp_db):
        """Test deleting non-existent model."""
        success = temp_db.delete_model("nonexistent")
        assert success is False

    def test_create_training_run(self, temp_db):
        """Test creating a training run."""
        temp_db.save_model("model_run", "linear_regression", {})

        run = temp_db.create_training_run("run_1", "model_run")

        assert run is not None
        assert run.id == "run_1"
        assert run.model_id == "model_run"
        assert run.status == "running"

    def test_complete_training_run(self, temp_db):
        """Test completing a training run."""
        temp_db.save_model("model_complete", "linear_regression", {})
        temp_db.create_training_run("run_complete", "model_complete")

        success = temp_db.complete_training_run(
            run_id="run_complete",
            status="completed",
            epochs_completed=100,
            final_loss=0.01,
            metrics={"accuracy": 0.95},
        )

        assert success is True

        run = temp_db.get_training_run("run_complete")
        assert run.status == "completed"
        assert run.epochs_completed == 100

    def test_log_prediction(self, temp_db):
        """Test logging a prediction."""
        temp_db.save_model("model_pred", "linear_regression", {})

        temp_db.log_prediction(
            log_id="pred_1",
            model_id="model_pred",
            n_samples=10,
            latency_ms=50.5,
            encrypted=False,
            api_key_name="test_key",
        )

        stats = temp_db.get_prediction_stats(model_id="model_pred")
        assert stats["total_predictions"] == 1
        assert stats["total_samples"] == 10

    def test_get_stats(self, temp_db):
        """Test getting overall stats."""
        # Create some data
        temp_db.save_model("model_stats", "linear_regression", {})
        temp_db.update_model_status("model_stats", "trained")
        temp_db.log_prediction("pred_stats", "model_stats", 5, 10.0)

        stats = temp_db.get_stats()

        assert stats["models"]["total"] >= 1
        assert stats["predictions"]["total"] >= 1


class TestAPIKeyOperations:
    """Tests for API key operations."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_keys.db"
            db = DatabaseManager(db_path)
            yield db

    def test_create_api_key(self, temp_db):
        """Test creating an API key."""
        key = "fheml_test_key_12345"
        key_hash = temp_db.create_api_key(
            key=key,
            name="test-key",
            permissions=["read", "write"],
            rate_limit=100,
        )

        assert key_hash is not None
        assert len(key_hash) == 64  # SHA256 hex

    def test_validate_api_key(self, temp_db):
        """Test validating an API key."""
        key = "fheml_test_key_valid"
        temp_db.create_api_key(
            key=key,
            name="valid-key",
            permissions=["read", "write", "admin"],
            rate_limit=500,
        )

        info = temp_db.validate_api_key(key)

        assert info is not None
        assert info["name"] == "valid-key"
        assert "admin" in info["permissions"]
        assert info["rate_limit"] == 500

    def test_validate_invalid_api_key(self, temp_db):
        """Test validating an invalid API key."""
        info = temp_db.validate_api_key("invalid_key_12345")
        assert info is None

    def test_revoke_api_key(self, temp_db):
        """Test revoking an API key."""
        key = "fheml_test_key_revoke"
        key_hash = temp_db.create_api_key(
            key=key,
            name="revoke-key",
            permissions=["read"],
            rate_limit=100,
        )

        # Revoke
        success = temp_db.revoke_api_key(key_hash)
        assert success is True

        # Validate should fail now
        info = temp_db.validate_api_key(key)
        assert info is None


class TestModelRecordDataclass:
    """Tests for ModelRecord dataclass."""

    def test_model_record_creation(self):
        """Test creating a ModelRecord."""
        record = ModelRecord(
            id="test_id",
            model_type="linear_regression",
            status="created",
            config={"learning_rate": 0.01},
            params_blob=None,
            n_features=5,
            feature_names=["a", "b", "c", "d", "e"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            trained_at=None,
            training_epochs=None,
            final_loss=None,
            metadata={},
        )

        assert record.id == "test_id"
        assert record.model_type == "linear_regression"
        assert record.n_features == 5


class TestTrainingRunDataclass:
    """Tests for TrainingRun dataclass."""

    def test_training_run_creation(self):
        """Test creating a TrainingRun."""
        run = TrainingRun(
            id="run_1",
            model_id="model_1",
            started_at=datetime.utcnow(),
            completed_at=None,
            status="running",
            epochs_completed=0,
            final_loss=None,
            metrics={},
            error_message=None,
        )

        assert run.id == "run_1"
        assert run.status == "running"


class TestPredictionLogDataclass:
    """Tests for PredictionLog dataclass."""

    def test_prediction_log_creation(self):
        """Test creating a PredictionLog."""
        log = PredictionLog(
            id="pred_1",
            model_id="model_1",
            timestamp=datetime.utcnow(),
            n_samples=100,
            latency_ms=25.5,
            encrypted=False,
        )

        assert log.id == "pred_1"
        assert log.n_samples == 100
        assert log.latency_ms == 25.5


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "integration.db"
            db = DatabaseManager(db_path)
            yield db

    def test_full_model_lifecycle(self, temp_db):
        """Test complete model lifecycle."""
        # 1. Create model
        temp_db.save_model(
            model_id="lifecycle_model",
            model_type="linear_regression",
            config={"learning_rate": 0.01, "n_epochs": 100},
            status="created",
        )

        # 2. Start training
        temp_db.create_training_run("lifecycle_run", "lifecycle_model")

        # 3. Complete training
        temp_db.complete_training_run(
            run_id="lifecycle_run",
            status="completed",
            epochs_completed=100,
            final_loss=0.01,
        )

        temp_db.update_model_status(
            model_id="lifecycle_model",
            status="trained",
            trained_at=datetime.utcnow(),
            training_epochs=100,
            final_loss=0.01,
            params={"weights": [1.0, 2.0, 3.0], "bias": 0.5},
        )

        # 4. Make predictions
        for i in range(5):
            temp_db.log_prediction(
                log_id=f"lifecycle_pred_{i}",
                model_id="lifecycle_model",
                n_samples=10,
                latency_ms=10.0 + i,
            )

        # 5. Check stats
        stats = temp_db.get_stats()
        assert stats["models"]["trained"] >= 1
        assert stats["predictions"]["total"] >= 5

        pred_stats = temp_db.get_prediction_stats(model_id="lifecycle_model")
        assert pred_stats["total_predictions"] == 5
        assert pred_stats["total_samples"] == 50

    def test_model_params_persistence(self, temp_db):
        """Test model parameters are persisted correctly."""

        params = {
            "weights": [1.0, 2.0, 3.0],
            "bias": 0.5,
            "state": "trained",
        }

        temp_db.save_model(
            model_id="params_model",
            model_type="linear_regression",
            config={},
            params=params,
        )

        # Retrieve and check
        retrieved_params = temp_db.get_model_params("params_model")
        assert retrieved_params["weights"] == params["weights"]
        assert retrieved_params["bias"] == params["bias"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
