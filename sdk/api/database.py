"""Database persistence layer for Xcapit FHE-ML API.

This module provides SQLite-based persistence for models, training runs,
and API usage metrics.
"""

import json
import pickle
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib


# Default database path
DEFAULT_DB_PATH = Path("./data/fheml.db")


@dataclass
class ModelRecord:
    """Database record for a stored model."""
    id: str
    model_type: str
    status: str
    config: Dict[str, Any]
    params_blob: Optional[bytes]
    n_features: Optional[int]
    feature_names: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    trained_at: Optional[datetime]
    training_epochs: Optional[int]
    final_loss: Optional[float]
    metadata: Dict[str, Any]


@dataclass
class TrainingRun:
    """Record of a training run."""
    id: str
    model_id: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: str  # running, completed, failed
    epochs_completed: int
    final_loss: Optional[float]
    metrics: Dict[str, Any]
    error_message: Optional[str]


@dataclass
class PredictionLog:
    """Log entry for a prediction request."""
    id: str
    model_id: str
    timestamp: datetime
    n_samples: int
    latency_ms: float
    encrypted: bool


class DatabaseManager:
    """SQLite database manager for FHE-ML API persistence."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file. Creates if not exists.
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager."""
        conn = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Models table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'created',
                    config TEXT NOT NULL,
                    params_blob BLOB,
                    n_features INTEGER,
                    feature_names TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trained_at TIMESTAMP,
                    training_epochs INTEGER,
                    final_loss REAL,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            # Training runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_runs (
                    id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'running',
                    epochs_completed INTEGER DEFAULT 0,
                    final_loss REAL,
                    metrics TEXT DEFAULT '{}',
                    error_message TEXT,
                    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
                )
            """)

            # Prediction logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prediction_logs (
                    id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    n_samples INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    encrypted BOOLEAN DEFAULT 0,
                    api_key_name TEXT,
                    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
                )
            """)

            # API keys table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_hash TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    permissions TEXT DEFAULT '["read", "write"]',
                    rate_limit INTEGER DEFAULT 100,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            # Indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_models_status ON models(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_models_type ON models(model_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_training_runs_model ON training_runs(model_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_prediction_logs_model ON prediction_logs(model_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_prediction_logs_timestamp ON prediction_logs(timestamp)
            """)

    # ========== Model Operations ==========

    def save_model(
        self,
        model_id: str,
        model_type: str,
        config: Dict[str, Any],
        status: str = "created",
        params: Optional[Dict] = None,
        n_features: Optional[int] = None,
        feature_names: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> ModelRecord:
        """Save or update a model in the database.

        Args:
            model_id: Unique model identifier.
            model_type: Type of model (linear_regression, etc.)
            config: Model configuration dict.
            status: Current status (created, training, trained, failed).
            params: Model parameters (weights, bias, etc.)
            n_features: Number of features.
            feature_names: List of feature names.
            metadata: Additional metadata.

        Returns:
            ModelRecord of the saved model.
        """
        params_blob = pickle.dumps(params) if params else None
        feature_names_json = json.dumps(feature_names) if feature_names else None
        config_json = json.dumps(config)
        metadata_json = json.dumps(metadata or {})
        now = datetime.utcnow()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if model exists
            cursor.execute("SELECT id FROM models WHERE id = ?", (model_id,))
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute("""
                    UPDATE models SET
                        model_type = ?,
                        status = ?,
                        config = ?,
                        params_blob = ?,
                        n_features = ?,
                        feature_names = ?,
                        updated_at = ?,
                        metadata = ?
                    WHERE id = ?
                """, (
                    model_type, status, config_json, params_blob,
                    n_features, feature_names_json, now, metadata_json, model_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO models (
                        id, model_type, status, config, params_blob,
                        n_features, feature_names, created_at, updated_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    model_id, model_type, status, config_json, params_blob,
                    n_features, feature_names_json, now, now, metadata_json
                ))

        return self.get_model(model_id)

    def get_model(self, model_id: str) -> Optional[ModelRecord]:
        """Get a model by ID.

        Args:
            model_id: Model identifier.

        Returns:
            ModelRecord or None if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return ModelRecord(
                id=row["id"],
                model_type=row["model_type"],
                status=row["status"],
                config=json.loads(row["config"]),
                params_blob=row["params_blob"],
                n_features=row["n_features"],
                feature_names=json.loads(row["feature_names"]) if row["feature_names"] else None,
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                trained_at=row["trained_at"],
                training_epochs=row["training_epochs"],
                final_loss=row["final_loss"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )

    def get_model_params(self, model_id: str) -> Optional[Dict]:
        """Get model parameters (unpickled).

        Args:
            model_id: Model identifier.

        Returns:
            Parameters dict or None.
        """
        model = self.get_model(model_id)
        if model and model.params_blob:
            return pickle.loads(model.params_blob)
        return None

    def list_models(
        self,
        status: Optional[str] = None,
        model_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ModelRecord]:
        """List models with optional filtering.

        Args:
            status: Filter by status.
            model_type: Filter by model type.
            limit: Maximum number of results.
            offset: Pagination offset.

        Returns:
            List of ModelRecords.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM models WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)
            if model_type:
                query += " AND model_type = ?"
                params.append(model_type)

            query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                ModelRecord(
                    id=row["id"],
                    model_type=row["model_type"],
                    status=row["status"],
                    config=json.loads(row["config"]),
                    params_blob=row["params_blob"],
                    n_features=row["n_features"],
                    feature_names=json.loads(row["feature_names"]) if row["feature_names"] else None,
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    trained_at=row["trained_at"],
                    training_epochs=row["training_epochs"],
                    final_loss=row["final_loss"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in rows
            ]

    def update_model_status(
        self,
        model_id: str,
        status: str,
        trained_at: Optional[datetime] = None,
        training_epochs: Optional[int] = None,
        final_loss: Optional[float] = None,
        params: Optional[Dict] = None,
    ) -> bool:
        """Update model status and training info.

        Args:
            model_id: Model identifier.
            status: New status.
            trained_at: Training completion timestamp.
            training_epochs: Number of epochs trained.
            final_loss: Final training loss.
            params: Updated model parameters.

        Returns:
            True if updated, False if model not found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            updates = ["status = ?", "updated_at = ?"]
            values = [status, datetime.utcnow()]

            if trained_at:
                updates.append("trained_at = ?")
                values.append(trained_at)
            if training_epochs is not None:
                updates.append("training_epochs = ?")
                values.append(training_epochs)
            if final_loss is not None:
                updates.append("final_loss = ?")
                values.append(final_loss)
            if params is not None:
                updates.append("params_blob = ?")
                values.append(pickle.dumps(params))

            values.append(model_id)

            cursor.execute(
                f"UPDATE models SET {', '.join(updates)} WHERE id = ?",
                values
            )

            return cursor.rowcount > 0

    def delete_model(self, model_id: str) -> bool:
        """Delete a model.

        Args:
            model_id: Model identifier.

        Returns:
            True if deleted, False if not found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
            return cursor.rowcount > 0

    # ========== Training Run Operations ==========

    def create_training_run(
        self,
        run_id: str,
        model_id: str,
    ) -> TrainingRun:
        """Create a new training run record.

        Args:
            run_id: Unique run identifier.
            model_id: Model being trained.

        Returns:
            TrainingRun record.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO training_runs (id, model_id, status)
                VALUES (?, ?, 'running')
            """, (run_id, model_id))

        return self.get_training_run(run_id)

    def get_training_run(self, run_id: str) -> Optional[TrainingRun]:
        """Get a training run by ID.

        Args:
            run_id: Run identifier.

        Returns:
            TrainingRun or None.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM training_runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return TrainingRun(
                id=row["id"],
                model_id=row["model_id"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                status=row["status"],
                epochs_completed=row["epochs_completed"],
                final_loss=row["final_loss"],
                metrics=json.loads(row["metrics"]) if row["metrics"] else {},
                error_message=row["error_message"],
            )

    def complete_training_run(
        self,
        run_id: str,
        status: str,
        epochs_completed: int,
        final_loss: Optional[float] = None,
        metrics: Optional[Dict] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Complete a training run.

        Args:
            run_id: Run identifier.
            status: Final status (completed, failed).
            epochs_completed: Total epochs completed.
            final_loss: Final loss value.
            metrics: Training metrics.
            error_message: Error message if failed.

        Returns:
            True if updated.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE training_runs SET
                    completed_at = ?,
                    status = ?,
                    epochs_completed = ?,
                    final_loss = ?,
                    metrics = ?,
                    error_message = ?
                WHERE id = ?
            """, (
                datetime.utcnow(), status, epochs_completed,
                final_loss, json.dumps(metrics or {}), error_message, run_id
            ))
            return cursor.rowcount > 0

    # ========== Prediction Log Operations ==========

    def log_prediction(
        self,
        log_id: str,
        model_id: str,
        n_samples: int,
        latency_ms: float,
        encrypted: bool = False,
        api_key_name: Optional[str] = None,
    ) -> None:
        """Log a prediction request.

        Args:
            log_id: Unique log identifier.
            model_id: Model used for prediction.
            n_samples: Number of samples predicted.
            latency_ms: Prediction latency in milliseconds.
            encrypted: Whether prediction was on encrypted data.
            api_key_name: Name of API key used for request.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prediction_logs (id, model_id, n_samples, latency_ms, encrypted, api_key_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (log_id, model_id, n_samples, latency_ms, encrypted, api_key_name))

    def get_prediction_stats(
        self,
        model_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get prediction statistics.

        Args:
            model_id: Filter by model ID.
            since: Filter by timestamp.

        Returns:
            Statistics dict with total_predictions, avg_latency, etc.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    COUNT(*) as total_predictions,
                    SUM(n_samples) as total_samples,
                    AVG(latency_ms) as avg_latency_ms,
                    MIN(latency_ms) as min_latency_ms,
                    MAX(latency_ms) as max_latency_ms,
                    SUM(CASE WHEN encrypted THEN 1 ELSE 0 END) as encrypted_predictions
                FROM prediction_logs WHERE 1=1
            """
            params = []

            if model_id:
                query += " AND model_id = ?"
                params.append(model_id)
            if since:
                query += " AND timestamp >= ?"
                params.append(since)

            cursor.execute(query, params)
            row = cursor.fetchone()

            return {
                "total_predictions": row["total_predictions"] or 0,
                "total_samples": row["total_samples"] or 0,
                "avg_latency_ms": round(row["avg_latency_ms"] or 0, 2),
                "min_latency_ms": round(row["min_latency_ms"] or 0, 2),
                "max_latency_ms": round(row["max_latency_ms"] or 0, 2),
                "encrypted_predictions": row["encrypted_predictions"] or 0,
            }

    # ========== API Key Operations ==========

    def create_api_key(
        self,
        key: str,
        name: str,
        permissions: Optional[List[str]] = None,
        rate_limit: int = 100,
    ) -> str:
        """Create a new API key.

        Args:
            key: The API key (will be hashed).
            name: Human-readable name for the key.
            permissions: List of permissions (default: ["read", "write"]).
            rate_limit: Requests per minute limit.

        Returns:
            The key hash for reference.
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        permissions = permissions or ["read", "write"]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO api_keys (key_hash, name, permissions, rate_limit)
                VALUES (?, ?, ?, ?)
            """, (key_hash, name, json.dumps(permissions), rate_limit))

        return key_hash

    def validate_api_key(self, key: str) -> Optional[Dict]:
        """Validate an API key and return its info.

        Args:
            key: The API key to validate.

        Returns:
            Dict with key info if valid, None otherwise.
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1
            """, (key_hash,))
            row = cursor.fetchone()

            if not row:
                return None

            # Update last used
            cursor.execute("""
                UPDATE api_keys SET last_used_at = ? WHERE key_hash = ?
            """, (datetime.utcnow(), key_hash))

            return {
                "name": row["name"],
                "permissions": json.loads(row["permissions"]),
                "rate_limit": row["rate_limit"],
                "created_at": row["created_at"],
                "last_used_at": row["last_used_at"],
            }

    def revoke_api_key(self, key_hash: str) -> bool:
        """Revoke an API key.

        Args:
            key_hash: Hash of the key to revoke.

        Returns:
            True if revoked.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE api_keys SET is_active = 0 WHERE key_hash = ?
            """, (key_hash,))
            return cursor.rowcount > 0

    # ========== Utility Methods ==========

    def get_stats(self) -> Dict[str, Any]:
        """Get overall database statistics.

        Returns:
            Dict with model counts, prediction counts, etc.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Model stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_models,
                    SUM(CASE WHEN status = 'trained' THEN 1 ELSE 0 END) as trained_models,
                    SUM(CASE WHEN status = 'created' THEN 1 ELSE 0 END) as untrained_models
                FROM models
            """)
            model_stats = cursor.fetchone()

            # Prediction stats
            cursor.execute("""
                SELECT COUNT(*) as total_predictions FROM prediction_logs
            """)
            pred_stats = cursor.fetchone()

            # Training stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_runs,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_runs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs
                FROM training_runs
            """)
            train_stats = cursor.fetchone()

            return {
                "models": {
                    "total": model_stats["total_models"] or 0,
                    "trained": model_stats["trained_models"] or 0,
                    "untrained": model_stats["untrained_models"] or 0,
                },
                "predictions": {
                    "total": pred_stats["total_predictions"] or 0,
                },
                "training_runs": {
                    "total": train_stats["total_runs"] or 0,
                    "completed": train_stats["completed_runs"] or 0,
                    "failed": train_stats["failed_runs"] or 0,
                },
            }

    def vacuum(self) -> None:
        """Optimize database by running VACUUM."""
        with self._get_connection() as conn:
            conn.execute("VACUUM")


# Global database instance
_db: Optional[DatabaseManager] = None


def get_database(db_path: Optional[Path] = None) -> DatabaseManager:
    """Get the database manager instance.

    Args:
        db_path: Optional custom database path.

    Returns:
        DatabaseManager instance.
    """
    global _db
    if _db is None or (db_path and db_path != _db.db_path):
        _db = DatabaseManager(db_path)
    return _db
