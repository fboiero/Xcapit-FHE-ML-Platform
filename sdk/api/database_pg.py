"""PostgreSQL database layer for Xcapit FHE-ML API (Production).

This module provides PostgreSQL-based persistence as an alternative to SQLite.
Use environment variable DATABASE_URL to configure the connection.

Example:
    export DATABASE_URL=postgresql://user:password@host:5432/dbname
"""

import json
import os
import pickle
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2 import pool
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


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
    status: str
    epochs_completed: int
    final_loss: Optional[float]
    metrics: Dict[str, Any]
    error_message: Optional[str]


class PostgresDatabaseManager:
    """PostgreSQL database manager for FHE-ML API persistence."""

    def __init__(self, database_url: Optional[str] = None, min_connections: int = 1, max_connections: int = 10):
        """Initialize PostgreSQL database manager.

        Args:
            database_url: PostgreSQL connection URL. Uses DATABASE_URL env var if not provided.
            min_connections: Minimum pool connections.
            max_connections: Maximum pool connections.
        """
        if not POSTGRES_AVAILABLE:
            raise ImportError("psycopg2 is required for PostgreSQL support. Install with: pip install psycopg2-binary")

        self.database_url = database_url or os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        self._pool = pool.ThreadedConnectionPool(
            min_connections,
            max_connections,
            self.database_url
        )
        self._init_schema()

    @contextmanager
    def _get_connection(self):
        """Get database connection from pool."""
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

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
                    config JSONB NOT NULL DEFAULT '{}',
                    params_blob BYTEA,
                    n_features INTEGER,
                    feature_names JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    trained_at TIMESTAMP,
                    training_epochs INTEGER,
                    final_loss REAL,
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # Training runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_runs (
                    id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL REFERENCES models(id) ON DELETE CASCADE,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'running',
                    epochs_completed INTEGER DEFAULT 0,
                    final_loss REAL,
                    metrics JSONB DEFAULT '{}',
                    error_message TEXT
                )
            """)

            # Prediction logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prediction_logs (
                    id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL REFERENCES models(id) ON DELETE CASCADE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    n_samples INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    encrypted BOOLEAN DEFAULT FALSE,
                    api_key_name TEXT
                )
            """)

            # API keys table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_hash TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    permissions JSONB DEFAULT '["read", "write"]',
                    rate_limit INTEGER DEFAULT 100,
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # Companies table (for consortiums)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    api_key_hash TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # Consortiums table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consortiums (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT NOT NULL REFERENCES companies(id),
                    model_type TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    ml_config JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Consortium memberships
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consortium_members (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL REFERENCES consortiums(id) ON DELETE CASCADE,
                    company_id TEXT NOT NULL REFERENCES companies(id),
                    role TEXT NOT NULL DEFAULT 'contributor',
                    status TEXT NOT NULL DEFAULT 'pending',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(consortium_id, company_id)
                )
            """)

            # Contribution proofs (Governance)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contribution_proofs (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL REFERENCES consortiums(id) ON DELETE CASCADE,
                    company_id TEXT NOT NULL REFERENCES companies(id),
                    record_count INTEGER NOT NULL,
                    feature_count INTEGER NOT NULL,
                    data_hash TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    verified BOOLEAN DEFAULT FALSE,
                    blockchain_tx TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Proposals (Governance)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL REFERENCES consortiums(id) ON DELETE CASCADE,
                    proposer_id TEXT NOT NULL REFERENCES companies(id),
                    proposal_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    data JSONB,
                    yes_votes INTEGER DEFAULT 0,
                    no_votes INTEGER DEFAULT 0,
                    voting_weight_yes REAL DEFAULT 0,
                    voting_weight_no REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    executed_at TIMESTAMP
                )
            """)

            # Votes (Governance)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
                    voter_id TEXT NOT NULL REFERENCES companies(id),
                    support BOOLEAN NOT NULL,
                    weight INTEGER NOT NULL DEFAULT 1,
                    comment TEXT,
                    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(proposal_id, voter_id)
                )
            """)

            # Audit events
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL REFERENCES consortiums(id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    target_id TEXT,
                    target_type TEXT,
                    data JSONB DEFAULT '{}',
                    previous_hash TEXT,
                    blockchain_tx TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Compliance checks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL REFERENCES consortiums(id) ON DELETE CASCADE,
                    framework_id TEXT NOT NULL,
                    control_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT,
                    evidence JSONB,
                    checked_by TEXT,
                    notes TEXT,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Quality assessments
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_assessments (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL REFERENCES consortiums(id) ON DELETE CASCADE,
                    company_id TEXT NOT NULL REFERENCES companies(id),
                    contribution_id TEXT,
                    overall_score REAL NOT NULL,
                    completeness_score REAL NOT NULL,
                    consistency_score REAL NOT NULL,
                    uniqueness_score REAL NOT NULL,
                    validity_score REAL NOT NULL,
                    freshness_score REAL NOT NULL,
                    record_count INTEGER NOT NULL,
                    feature_count INTEGER NOT NULL,
                    null_ratio REAL NOT NULL,
                    duplicate_ratio REAL NOT NULL,
                    outlier_ratio REAL NOT NULL,
                    metadata JSONB,
                    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Quality alerts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_alerts (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL REFERENCES consortiums(id) ON DELETE CASCADE,
                    company_id TEXT NOT NULL REFERENCES companies(id),
                    assessment_id TEXT NOT NULL REFERENCES quality_assessments(id),
                    metric TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    message TEXT NOT NULL,
                    acknowledged_at TIMESTAMP,
                    acknowledged_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_status ON models(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_type ON models(model_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_training_runs_model ON training_runs(model_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prediction_logs_model ON prediction_logs(model_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prediction_logs_timestamp ON prediction_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_consortium_members_consortium ON consortium_members(consortium_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_consortium ON audit_events(consortium_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_proposals_consortium ON proposals(consortium_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_quality_assessments_consortium ON quality_assessments(consortium_id)")

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
        """Save or update a model in the database."""
        params_blob = pickle.dumps(params) if params else None
        now = datetime.utcnow()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO models (id, model_type, status, config, params_blob, n_features, feature_names, created_at, updated_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    model_type = EXCLUDED.model_type,
                    status = EXCLUDED.status,
                    config = EXCLUDED.config,
                    params_blob = EXCLUDED.params_blob,
                    n_features = EXCLUDED.n_features,
                    feature_names = EXCLUDED.feature_names,
                    updated_at = EXCLUDED.updated_at,
                    metadata = EXCLUDED.metadata
            """, (
                model_id, model_type, status,
                json.dumps(config), params_blob, n_features,
                json.dumps(feature_names) if feature_names else None,
                now, now, json.dumps(metadata or {})
            ))

        return self.get_model(model_id)

    def get_model(self, model_id: str) -> Optional[ModelRecord]:
        """Get a model by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM models WHERE id = %s", (model_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return ModelRecord(
                id=row["id"],
                model_type=row["model_type"],
                status=row["status"],
                config=row["config"] if isinstance(row["config"], dict) else json.loads(row["config"]),
                params_blob=row["params_blob"],
                n_features=row["n_features"],
                feature_names=row["feature_names"] if isinstance(row["feature_names"], list) else (json.loads(row["feature_names"]) if row["feature_names"] else None),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                trained_at=row["trained_at"],
                training_epochs=row["training_epochs"],
                final_loss=row["final_loss"],
                metadata=row["metadata"] if isinstance(row["metadata"], dict) else json.loads(row["metadata"] or "{}"),
            )

    def get_model_params(self, model_id: str) -> Optional[Dict]:
        """Get model parameters (unpickled)."""
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
        """List models with optional filtering."""
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = "SELECT * FROM models WHERE TRUE"
            params = []

            if status:
                query += " AND status = %s"
                params.append(status)
            if model_type:
                query += " AND model_type = %s"
                params.append(model_type)

            query += " ORDER BY updated_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                ModelRecord(
                    id=row["id"],
                    model_type=row["model_type"],
                    status=row["status"],
                    config=row["config"] if isinstance(row["config"], dict) else json.loads(row["config"]),
                    params_blob=row["params_blob"],
                    n_features=row["n_features"],
                    feature_names=row["feature_names"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    trained_at=row["trained_at"],
                    training_epochs=row["training_epochs"],
                    final_loss=row["final_loss"],
                    metadata=row["metadata"] if isinstance(row["metadata"], dict) else json.loads(row["metadata"] or "{}"),
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
        """Update model status and training info."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            updates = ["status = %s", "updated_at = %s"]
            values = [status, datetime.utcnow()]

            if trained_at:
                updates.append("trained_at = %s")
                values.append(trained_at)
            if training_epochs is not None:
                updates.append("training_epochs = %s")
                values.append(training_epochs)
            if final_loss is not None:
                updates.append("final_loss = %s")
                values.append(final_loss)
            if params is not None:
                updates.append("params_blob = %s")
                values.append(pickle.dumps(params))

            values.append(model_id)

            cursor.execute(
                f"UPDATE models SET {', '.join(updates)} WHERE id = %s",
                values
            )

            return cursor.rowcount > 0

    def delete_model(self, model_id: str) -> bool:
        """Delete a model."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM models WHERE id = %s", (model_id,))
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
        """Log a prediction request."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prediction_logs (id, model_id, n_samples, latency_ms, encrypted, api_key_name)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (log_id, model_id, n_samples, latency_ms, encrypted, api_key_name))

    def get_prediction_stats(
        self,
        model_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get prediction statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT
                    COUNT(*) as total_predictions,
                    COALESCE(SUM(n_samples), 0) as total_samples,
                    COALESCE(AVG(latency_ms), 0) as avg_latency_ms,
                    COALESCE(MIN(latency_ms), 0) as min_latency_ms,
                    COALESCE(MAX(latency_ms), 0) as max_latency_ms,
                    COALESCE(SUM(CASE WHEN encrypted THEN 1 ELSE 0 END), 0) as encrypted_predictions
                FROM prediction_logs WHERE TRUE
            """
            params = []

            if model_id:
                query += " AND model_id = %s"
                params.append(model_id)
            if since:
                query += " AND timestamp >= %s"
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
        """Create a new API key."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        permissions = permissions or ["read", "write"]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO api_keys (key_hash, name, permissions, rate_limit)
                VALUES (%s, %s, %s, %s)
            """, (key_hash, name, json.dumps(permissions), rate_limit))

        return key_hash

    def validate_api_key(self, key: str) -> Optional[Dict]:
        """Validate an API key and return its info."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM api_keys WHERE key_hash = %s AND is_active = TRUE
            """, (key_hash,))
            row = cursor.fetchone()

            if not row:
                return None

            cursor.execute("""
                UPDATE api_keys SET last_used_at = %s WHERE key_hash = %s
            """, (datetime.utcnow(), key_hash))

            return {
                "name": row["name"],
                "permissions": row["permissions"] if isinstance(row["permissions"], list) else json.loads(row["permissions"]),
                "rate_limit": row["rate_limit"],
                "created_at": row["created_at"],
                "last_used_at": row["last_used_at"],
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get overall database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT
                    COUNT(*) as total_models,
                    SUM(CASE WHEN status = 'trained' THEN 1 ELSE 0 END) as trained_models,
                    SUM(CASE WHEN status = 'created' THEN 1 ELSE 0 END) as untrained_models
                FROM models
            """)
            model_stats = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) as total_predictions FROM prediction_logs")
            pred_stats = cursor.fetchone()

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

    def close(self):
        """Close database connection pool."""
        if self._pool:
            self._pool.closeall()


# Factory function to get the appropriate database
def get_db_path():
    """Get database path for SQLite compatibility."""
    from pathlib import Path
    return Path("./data/fheml.db")


def get_database_auto():
    """Automatically select database based on environment.

    Uses PostgreSQL if DATABASE_URL is set, otherwise falls back to SQLite.
    """
    database_url = os.environ.get("DATABASE_URL")

    if database_url and POSTGRES_AVAILABLE:
        return PostgresDatabaseManager(database_url)
    else:
        # Fall back to SQLite
        from .database import get_database
        return get_database()
