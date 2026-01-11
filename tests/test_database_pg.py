"""Tests for PostgreSQL database layer."""

import pickle
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from sdk.api.database_pg import ModelRecord, TrainingRun, get_db_path


class TestPostgresDatabaseManagerInit:
    """Tests for PostgresDatabaseManager initialization."""

    def test_init_without_psycopg2_raises_import_error(self):
        """Test that initialization fails when psycopg2 is not available."""
        with patch("sdk.api.database_pg.POSTGRES_AVAILABLE", False):
            from importlib import reload
            import sdk.api.database_pg as db_pg

            # We need to test with POSTGRES_AVAILABLE=False
            original = db_pg.POSTGRES_AVAILABLE
            db_pg.POSTGRES_AVAILABLE = False

            try:
                with pytest.raises(ImportError) as exc_info:
                    db_pg.PostgresDatabaseManager("postgresql://test:test@localhost/test")

                assert "psycopg2" in str(exc_info.value)
            finally:
                db_pg.POSTGRES_AVAILABLE = original

    def test_init_without_database_url_raises_value_error(self):
        """Test that initialization fails without database URL."""
        import os
        from sdk.api.database_pg import PostgresDatabaseManager

        # Remove DATABASE_URL if it exists
        old_url = os.environ.pop("DATABASE_URL", None)
        try:
            with pytest.raises(ValueError) as exc_info:
                PostgresDatabaseManager()
            assert "DATABASE_URL" in str(exc_info.value)
        finally:
            if old_url:
                os.environ["DATABASE_URL"] = old_url

    def test_init_with_custom_database_url(self):
        """Test initialization stores custom database URL."""
        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            mock_pool.return_value = MagicMock()

            from sdk.api.database_pg import PostgresDatabaseManager

            with patch.object(PostgresDatabaseManager, "_init_schema"):
                manager = PostgresDatabaseManager(
                    database_url="postgresql://custom@host/db"
                )
                assert manager.database_url == "postgresql://custom@host/db"

    def test_init_creates_connection_pool(self):
        """Test that initialization creates a connection pool."""
        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            from sdk.api.database_pg import PostgresDatabaseManager

            with patch.object(PostgresDatabaseManager, "_init_schema"):
                manager = PostgresDatabaseManager(
                    database_url="postgresql://test@localhost/db",
                    min_connections=2,
                    max_connections=20,
                )

            mock_pool.assert_called_once_with(
                2, 20, "postgresql://test@localhost/db"
            )


class TestPostgresDatabaseManagerConnection:
    """Tests for connection management."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mocked PostgresDatabaseManager."""
        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            from sdk.api.database_pg import PostgresDatabaseManager

            with patch.object(PostgresDatabaseManager, "_init_schema"):
                manager = PostgresDatabaseManager("postgresql://test@localhost/db")
                manager._pool = mock_pool_instance
                return manager

    def test_get_connection_returns_connection(self, mock_manager):
        """Test _get_connection returns a connection from pool."""
        mock_conn = MagicMock()
        mock_manager._pool.getconn.return_value = mock_conn

        with mock_manager._get_connection() as conn:
            assert conn == mock_conn

        mock_manager._pool.getconn.assert_called_once()
        mock_manager._pool.putconn.assert_called_once_with(mock_conn)

    def test_get_connection_commits_on_success(self, mock_manager):
        """Test connection commits on successful block."""
        mock_conn = MagicMock()
        mock_manager._pool.getconn.return_value = mock_conn

        with mock_manager._get_connection() as conn:
            pass

        mock_conn.commit.assert_called_once()

    def test_get_connection_rollbacks_on_exception(self, mock_manager):
        """Test connection rollbacks on exception."""
        mock_conn = MagicMock()
        mock_manager._pool.getconn.return_value = mock_conn

        with pytest.raises(ValueError):
            with mock_manager._get_connection() as conn:
                raise ValueError("Test error")

        mock_conn.rollback.assert_called_once()
        mock_manager._pool.putconn.assert_called_once_with(mock_conn)

    def test_close_closes_all_connections(self, mock_manager):
        """Test close method closes all pool connections."""
        mock_manager.close()
        mock_manager._pool.closeall.assert_called_once()


class TestModelOperations:
    """Tests for model CRUD operations."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mocked PostgresDatabaseManager."""
        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            from sdk.api.database_pg import PostgresDatabaseManager

            with patch.object(PostgresDatabaseManager, "_init_schema"):
                manager = PostgresDatabaseManager("postgresql://test@localhost/db")
                manager._pool = mock_pool_instance
                return manager

    def test_save_model_creates_new_model(self, mock_manager):
        """Test saving a new model."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        # Mock get_model for the return value
        with patch.object(mock_manager, "get_model") as mock_get:
            expected_record = ModelRecord(
                id="model_001",
                model_type="LinearRegression",
                status="created",
                config={"lr": 0.01},
                params_blob=None,
                n_features=10,
                feature_names=["f1", "f2"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                trained_at=None,
                training_epochs=None,
                final_loss=None,
                metadata={},
            )
            mock_get.return_value = expected_record

            result = mock_manager.save_model(
                model_id="model_001",
                model_type="LinearRegression",
                config={"lr": 0.01},
                n_features=10,
                feature_names=["f1", "f2"],
            )

            assert result.id == "model_001"
            mock_cursor.execute.assert_called_once()

    def test_get_model_returns_none_when_not_found(self, mock_manager):
        """Test get_model returns None when model doesn't exist."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.get_model("nonexistent")

        assert result is None

    def test_get_model_returns_model_record(self, mock_manager):
        """Test get_model returns ModelRecord when found."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_row = {
            "id": "model_001",
            "model_type": "LogisticRegression",
            "status": "trained",
            "config": {"C": 1.0},
            "params_blob": pickle.dumps({"weights": [1, 2, 3]}),
            "n_features": 5,
            "feature_names": ["a", "b", "c", "d", "e"],
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 2),
            "trained_at": datetime(2024, 1, 2),
            "training_epochs": 100,
            "final_loss": 0.05,
            "metadata": {"accuracy": 0.95},
        }
        mock_cursor.fetchone.return_value = mock_row
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.get_model("model_001")

        assert result is not None
        assert result.id == "model_001"
        assert result.model_type == "LogisticRegression"
        assert result.status == "trained"
        assert result.n_features == 5

    def test_get_model_params_returns_unpickled_params(self, mock_manager):
        """Test get_model_params returns unpickled parameters."""
        params = {"weights": [1, 2, 3], "bias": 0.5}

        with patch.object(mock_manager, "get_model") as mock_get:
            mock_get.return_value = ModelRecord(
                id="model_001",
                model_type="Linear",
                status="trained",
                config={},
                params_blob=pickle.dumps(params),
                n_features=3,
                feature_names=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                trained_at=None,
                training_epochs=None,
                final_loss=None,
                metadata={},
            )

            result = mock_manager.get_model_params("model_001")

            assert result == params

    def test_get_model_params_returns_none_when_no_params(self, mock_manager):
        """Test get_model_params returns None when no params."""
        with patch.object(mock_manager, "get_model") as mock_get:
            mock_get.return_value = ModelRecord(
                id="model_001",
                model_type="Linear",
                status="created",
                config={},
                params_blob=None,
                n_features=3,
                feature_names=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                trained_at=None,
                training_epochs=None,
                final_loss=None,
                metadata={},
            )

            result = mock_manager.get_model_params("model_001")

            assert result is None

    def test_list_models_with_filters(self, mock_manager):
        """Test list_models with status and model_type filters."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_rows = [
            {
                "id": "model_001",
                "model_type": "Linear",
                "status": "trained",
                "config": {},
                "params_blob": None,
                "n_features": 3,
                "feature_names": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "trained_at": None,
                "training_epochs": None,
                "final_loss": None,
                "metadata": {},
            }
        ]
        mock_cursor.fetchall.return_value = mock_rows
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.list_models(status="trained", model_type="Linear", limit=10)

        assert len(result) == 1
        assert result[0].id == "model_001"

    def test_update_model_status_returns_true_on_success(self, mock_manager):
        """Test update_model_status returns True on successful update."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.update_model_status("model_001", "trained")

        assert result is True

    def test_update_model_status_returns_false_when_not_found(self, mock_manager):
        """Test update_model_status returns False when model not found."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.update_model_status("nonexistent", "trained")

        assert result is False

    def test_update_model_status_with_training_params(self, mock_manager):
        """Test update_model_status with training parameters."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.update_model_status(
            "model_001",
            "trained",
            trained_at=datetime.utcnow(),
            training_epochs=100,
            final_loss=0.05,
            params={"weights": [1, 2, 3]},
        )

        assert result is True

    def test_delete_model_returns_true_on_success(self, mock_manager):
        """Test delete_model returns True on successful deletion."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.delete_model("model_001")

        assert result is True

    def test_delete_model_returns_false_when_not_found(self, mock_manager):
        """Test delete_model returns False when model doesn't exist."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.delete_model("nonexistent")

        assert result is False


class TestPredictionLogOperations:
    """Tests for prediction logging operations."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mocked PostgresDatabaseManager."""
        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            from sdk.api.database_pg import PostgresDatabaseManager

            with patch.object(PostgresDatabaseManager, "_init_schema"):
                manager = PostgresDatabaseManager("postgresql://test@localhost/db")
                manager._pool = mock_pool_instance
                return manager

    def test_log_prediction_inserts_record(self, mock_manager):
        """Test log_prediction inserts a new record."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        mock_manager.log_prediction(
            log_id="log_001",
            model_id="model_001",
            n_samples=100,
            latency_ms=15.5,
            encrypted=True,
            api_key_name="test_key",
        )

        mock_cursor.execute.assert_called_once()

    def test_get_prediction_stats_returns_statistics(self, mock_manager):
        """Test get_prediction_stats returns aggregated statistics."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_row = {
            "total_predictions": 100,
            "total_samples": 10000,
            "avg_latency_ms": 12.5,
            "min_latency_ms": 5.0,
            "max_latency_ms": 50.0,
            "encrypted_predictions": 25,
        }
        mock_cursor.fetchone.return_value = mock_row
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.get_prediction_stats()

        assert result["total_predictions"] == 100
        assert result["total_samples"] == 10000
        assert result["avg_latency_ms"] == 12.5
        assert result["encrypted_predictions"] == 25

    def test_get_prediction_stats_with_model_filter(self, mock_manager):
        """Test get_prediction_stats with model_id filter."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_row = {
            "total_predictions": 50,
            "total_samples": 5000,
            "avg_latency_ms": 10.0,
            "min_latency_ms": 3.0,
            "max_latency_ms": 30.0,
            "encrypted_predictions": 10,
        }
        mock_cursor.fetchone.return_value = mock_row
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.get_prediction_stats(model_id="model_001")

        assert result["total_predictions"] == 50

    def test_get_prediction_stats_handles_null_values(self, mock_manager):
        """Test get_prediction_stats handles NULL values gracefully."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_row = {
            "total_predictions": None,
            "total_samples": None,
            "avg_latency_ms": None,
            "min_latency_ms": None,
            "max_latency_ms": None,
            "encrypted_predictions": None,
        }
        mock_cursor.fetchone.return_value = mock_row
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.get_prediction_stats()

        assert result["total_predictions"] == 0
        assert result["avg_latency_ms"] == 0


class TestApiKeyOperations:
    """Tests for API key operations."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mocked PostgresDatabaseManager."""
        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            from sdk.api.database_pg import PostgresDatabaseManager

            with patch.object(PostgresDatabaseManager, "_init_schema"):
                manager = PostgresDatabaseManager("postgresql://test@localhost/db")
                manager._pool = mock_pool_instance
                return manager

    def test_create_api_key_returns_hash(self, mock_manager):
        """Test create_api_key returns the key hash."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.create_api_key(
            key="test_api_key_123",
            name="test_key",
            permissions=["read", "write"],
            rate_limit=100,
        )

        assert isinstance(result, str)
        assert len(result) == 64  # SHA256 hash length

    def test_create_api_key_default_permissions(self, mock_manager):
        """Test create_api_key with default permissions."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.create_api_key(key="test_key", name="default_key")

        assert isinstance(result, str)

    def test_validate_api_key_returns_info_when_valid(self, mock_manager):
        """Test validate_api_key returns key info when valid."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_row = {
            "name": "test_key",
            "permissions": ["read", "write"],
            "rate_limit": 100,
            "created_at": datetime(2024, 1, 1),
            "last_used_at": datetime(2024, 1, 2),
        }
        mock_cursor.fetchone.return_value = mock_row
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.validate_api_key("test_api_key_123")

        assert result is not None
        assert result["name"] == "test_key"
        assert result["rate_limit"] == 100

    def test_validate_api_key_returns_none_when_invalid(self, mock_manager):
        """Test validate_api_key returns None for invalid key."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.validate_api_key("invalid_key")

        assert result is None

    def test_validate_api_key_updates_last_used(self, mock_manager):
        """Test validate_api_key updates last_used_at timestamp."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_row = {
            "name": "test_key",
            "permissions": ["read"],
            "rate_limit": 50,
            "created_at": datetime(2024, 1, 1),
            "last_used_at": None,
        }
        mock_cursor.fetchone.return_value = mock_row
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        mock_manager.validate_api_key("test_key")

        # Check that execute was called for both SELECT and UPDATE
        assert mock_cursor.execute.call_count == 2


class TestStatistics:
    """Tests for statistics methods."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mocked PostgresDatabaseManager."""
        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            from sdk.api.database_pg import PostgresDatabaseManager

            with patch.object(PostgresDatabaseManager, "_init_schema"):
                manager = PostgresDatabaseManager("postgresql://test@localhost/db")
                manager._pool = mock_pool_instance
                return manager

    def test_get_stats_returns_overall_statistics(self, mock_manager):
        """Test get_stats returns comprehensive statistics."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Mock different fetchone calls for different queries
        mock_cursor.fetchone.side_effect = [
            {"total_models": 10, "trained_models": 5, "untrained_models": 5},
            {"total_predictions": 1000},
            {"total_runs": 15, "completed_runs": 12, "failed_runs": 3},
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.get_stats()

        assert result["models"]["total"] == 10
        assert result["models"]["trained"] == 5
        assert result["predictions"]["total"] == 1000
        assert result["training_runs"]["completed"] == 12

    def test_get_stats_handles_null_values(self, mock_manager):
        """Test get_stats handles NULL values gracefully."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [
            {"total_models": None, "trained_models": None, "untrained_models": None},
            {"total_predictions": None},
            {"total_runs": None, "completed_runs": None, "failed_runs": None},
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_manager._pool.getconn.return_value = mock_conn

        result = mock_manager.get_stats()

        assert result["models"]["total"] == 0
        assert result["predictions"]["total"] == 0
        assert result["training_runs"]["total"] == 0


class TestDataclasses:
    """Tests for dataclass definitions."""

    def test_model_record_fields(self):
        """Test ModelRecord has all expected fields."""
        record = ModelRecord(
            id="test_id",
            model_type="LinearRegression",
            status="created",
            config={"lr": 0.01},
            params_blob=b"params",
            n_features=10,
            feature_names=["f1", "f2"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            trained_at=None,
            training_epochs=None,
            final_loss=None,
            metadata={},
        )

        assert record.id == "test_id"
        assert record.model_type == "LinearRegression"
        assert record.n_features == 10

    def test_training_run_fields(self):
        """Test TrainingRun has all expected fields."""
        run = TrainingRun(
            id="run_001",
            model_id="model_001",
            started_at=datetime.utcnow(),
            completed_at=None,
            status="running",
            epochs_completed=50,
            final_loss=None,
            metrics={"accuracy": 0.85},
            error_message=None,
        )

        assert run.id == "run_001"
        assert run.status == "running"
        assert run.epochs_completed == 50


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_get_db_path_returns_path(self):
        """Test get_db_path returns a Path object."""
        path = get_db_path()

        assert str(path).endswith("fheml.db")

    def test_get_database_auto_with_postgres_url(self):
        """Test get_database_auto returns PostgresDatabaseManager when DATABASE_URL is set."""
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test@localhost/db"}):
            with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
                mock_pool.return_value = MagicMock()

                with patch("sdk.api.database_pg.PostgresDatabaseManager._init_schema"):
                    from sdk.api.database_pg import get_database_auto, PostgresDatabaseManager

                    result = get_database_auto()

                    assert isinstance(result, PostgresDatabaseManager)

    def test_get_database_auto_fallback_to_sqlite(self):
        """Test get_database_auto falls back to SQLite when DATABASE_URL not set."""
        import os

        # Remove DATABASE_URL if it exists
        old_url = os.environ.pop("DATABASE_URL", None)
        try:
            with patch("sdk.api.database.get_database") as mock_sqlite:
                mock_instance = MagicMock()
                mock_sqlite.return_value = mock_instance

                from sdk.api.database_pg import get_database_auto

                result = get_database_auto()

                mock_sqlite.assert_called_once()
                assert result == mock_instance
        finally:
            if old_url:
                os.environ["DATABASE_URL"] = old_url


class TestSchemaInitialization:
    """Tests for schema initialization."""

    def test_init_schema_creates_tables(self):
        """Test _init_schema creates all required tables."""
        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_pool_instance.getconn.return_value = mock_conn
            mock_pool.return_value = mock_pool_instance

            from sdk.api.database_pg import PostgresDatabaseManager

            # Don't patch _init_schema this time
            manager = PostgresDatabaseManager("postgresql://test@localhost/db")

            # Verify execute was called multiple times for table creation
            assert mock_cursor.execute.call_count > 10  # Tables + indexes

    def test_init_schema_creates_indexes(self):
        """Test _init_schema creates performance indexes."""
        with patch("psycopg2.pool.ThreadedConnectionPool") as mock_pool:
            mock_pool_instance = MagicMock()
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_pool_instance.getconn.return_value = mock_conn
            mock_pool.return_value = mock_pool_instance

            from sdk.api.database_pg import PostgresDatabaseManager

            manager = PostgresDatabaseManager("postgresql://test@localhost/db")

            # Check for index creation calls
            calls = [str(call) for call in mock_cursor.execute.call_args_list]
            index_calls = [c for c in calls if "CREATE INDEX" in c]
            assert len(index_calls) > 0
