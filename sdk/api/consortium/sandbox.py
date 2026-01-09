"""
Sandbox operations for consortium management.

This module handles all sandbox-related functionality including:
- Sandbox environment management
- Synthetic dataset generation
- Experiment creation and execution
- Sandbox templates
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Optional

from .database import DatabaseManager


class SandboxManager:
    """Manages sandbox operations for testing and experimentation."""

    def __init__(self, db_path: str = "fhe_platform.db"):
        """Initialize sandbox manager.

        Args:
            db_path: Path to SQLite database.
        """
        self._db = DatabaseManager(db_path)

    def _get_connection(self):
        """Get database connection."""
        return self._db.get_connection()

    def _init_sandbox_schema(self):
        """Initialize sandbox schema."""
        self._db.init_sandbox_schema()

    def create_sandbox(
        self,
        name: str,
        owner_id: str,
        description: Optional[str] = None,
        template_id: Optional[str] = None,
        industry: Optional[str] = None,
        expires_days: int = 7,
    ) -> dict:
        """Create a new sandbox environment.

        Args:
            name: Sandbox name.
            owner_id: Owner company ID.
            description: Optional description.
            template_id: Optional template to initialize from.
            industry: Industry type.
            expires_days: Days until expiration.

        Returns:
            Created sandbox data.
        """
        self._init_sandbox_schema()

        sandbox_id = f"sandbox_{uuid.uuid4().hex[:16]}"
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

        template_type = "custom"
        if template_id:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT template_type FROM sandbox_templates WHERE id = ?", (template_id,)
                )
                row = cursor.fetchone()
                if row:
                    template_type = row[0]

        config = {
            "template_id": template_id,
            "max_datasets": 10,
            "max_experiments": 20,
            "max_records_per_dataset": 100000,
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sandbox_environments
                (id, name, description, owner_id, template_type, industry, expires_at, config)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    sandbox_id,
                    name,
                    description,
                    owner_id,
                    template_type,
                    industry,
                    expires_at,
                    json.dumps(config),
                ),
            )
            conn.commit()

        # If template provided, generate initial datasets
        if template_id:
            self._initialize_sandbox_from_template(sandbox_id, template_id, owner_id)

        return self.get_sandbox(sandbox_id)

    def _initialize_sandbox_from_template(self, sandbox_id: str, template_id: str, owner_id: str):
        """Initialize sandbox with template data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sandbox_templates WHERE id = ?", (template_id,))
            template = cursor.fetchone()

            if not template:
                return

            template = dict(template)
            datasets_config = json.loads(template.get("datasets", "[]"))

            for ds_config in datasets_config:
                self.generate_synthetic_dataset(
                    sandbox_id=sandbox_id,
                    name=f"Sample {ds_config.get('type', 'dataset').title()}",
                    dataset_type=ds_config.get("type", "generic"),
                    record_count=ds_config.get("records", 1000),
                    created_by=owner_id,
                    config=ds_config,
                )

    def get_sandbox(self, sandbox_id: str) -> Optional[dict]:
        """Get a sandbox environment by ID.

        Args:
            sandbox_id: Sandbox ID.

        Returns:
            Sandbox data or None if not found.
        """
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.*, c.name as owner_name
                FROM sandbox_environments s
                JOIN companies c ON s.owner_id = c.id
                WHERE s.id = ?
            """,
                (sandbox_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            sandbox = dict(row)
            sandbox["config"] = json.loads(sandbox.get("config", "{}"))
            sandbox["metadata"] = json.loads(sandbox.get("metadata", "{}"))

            # Get counts
            cursor.execute(
                "SELECT COUNT(*) FROM synthetic_datasets WHERE sandbox_id = ?", (sandbox_id,)
            )
            sandbox["dataset_count"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM sandbox_experiments WHERE sandbox_id = ?", (sandbox_id,)
            )
            sandbox["experiment_count"] = cursor.fetchone()[0]

            return sandbox

    def list_sandboxes(
        self, owner_id: Optional[str] = None, status: Optional[str] = None
    ) -> list[dict]:
        """List sandbox environments.

        Args:
            owner_id: Optional owner filter.
            status: Optional status filter.

        Returns:
            List of sandboxes.
        """
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT s.*, c.name as owner_name
                FROM sandbox_environments s
                JOIN companies c ON s.owner_id = c.id
                WHERE 1=1
            """
            params = []

            if owner_id:
                query += " AND s.owner_id = ?"
                params.append(owner_id)

            if status:
                query += " AND s.status = ?"
                params.append(status)

            query += " ORDER BY s.created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

        sandboxes = []
        for row in rows:
            sandbox = dict(row)
            sandbox["config"] = json.loads(sandbox.get("config", "{}"))
            sandboxes.append(sandbox)

        return sandboxes

    def delete_sandbox(self, sandbox_id: str, owner_id: Optional[str] = None) -> bool:
        """Delete a sandbox environment.

        Args:
            sandbox_id: Sandbox ID.
            owner_id: Optional owner ID for verification.

        Returns:
            True if deleted successfully.
        """
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verify ownership if owner_id provided
            if owner_id:
                cursor.execute(
                    "SELECT owner_id FROM sandbox_environments WHERE id = ?", (sandbox_id,)
                )
                row = cursor.fetchone()
                if not row or row[0] != owner_id:
                    return False

            # Delete experiments
            cursor.execute("DELETE FROM sandbox_experiments WHERE sandbox_id = ?", (sandbox_id,))

            # Delete datasets
            cursor.execute("DELETE FROM synthetic_datasets WHERE sandbox_id = ?", (sandbox_id,))

            # Delete sandbox
            cursor.execute("DELETE FROM sandbox_environments WHERE id = ?", (sandbox_id,))

            conn.commit()
            return cursor.rowcount > 0

    def generate_synthetic_dataset(
        self,
        sandbox_id: str,
        name: str,
        dataset_type: str,
        created_by: str,
        record_count: int = 1000,
        description: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> dict:
        """Generate a synthetic dataset for the sandbox.

        Args:
            sandbox_id: Sandbox ID.
            name: Dataset name.
            dataset_type: Type of dataset (transactions, applications, etc.).
            created_by: Creator company ID.
            record_count: Number of records to generate.
            description: Optional description.
            config: Optional configuration.

        Returns:
            Created dataset data.
        """
        self._init_sandbox_schema()

        config = config or {}
        dataset_id = f"ds_{uuid.uuid4().hex[:16]}"

        # Generate features based on dataset type
        features, statistics, preview = self._generate_synthetic_data(
            dataset_type, record_count, config
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get industry from sandbox
            cursor.execute("SELECT industry FROM sandbox_environments WHERE id = ?", (sandbox_id,))
            row = cursor.fetchone()
            industry = row[0] if row else None

            cursor.execute(
                """
                INSERT INTO synthetic_datasets
                (id, sandbox_id, name, description, dataset_type, industry,
                 record_count, feature_count, features, data_preview, statistics, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    dataset_id,
                    sandbox_id,
                    name,
                    description,
                    dataset_type,
                    industry,
                    record_count,
                    len(features),
                    json.dumps(features),
                    json.dumps(preview),
                    json.dumps(statistics),
                    created_by,
                ),
            )
            conn.commit()

        return self.get_dataset(dataset_id)

    def _generate_synthetic_data(self, dataset_type: str, record_count: int, config: dict) -> tuple:
        """Generate synthetic data based on type."""
        features = []
        statistics = {}
        preview = []

        if dataset_type == "transactions":
            features = [
                {
                    "name": "transaction_id",
                    "type": "string",
                    "description": "Unique transaction ID",
                },
                {"name": "amount", "type": "float", "description": "Transaction amount"},
                {
                    "name": "merchant_category",
                    "type": "category",
                    "description": "Merchant category code",
                },
                {"name": "time_of_day", "type": "integer", "description": "Hour of day (0-23)"},
                {"name": "day_of_week", "type": "integer", "description": "Day of week (0-6)"},
                {
                    "name": "is_international",
                    "type": "boolean",
                    "description": "International transaction",
                },
                {"name": "is_fraud", "type": "boolean", "description": "Fraud label"},
            ]
            fraud_rate = config.get("fraud_rate", 0.02)
            statistics = {
                "fraud_rate": fraud_rate,
                "avg_amount": 150.50,
                "max_amount": 5000.00,
                "international_rate": 0.15,
            }
            for _i in range(min(5, record_count)):
                preview.append(
                    {
                        "transaction_id": f"txn_{uuid.uuid4().hex[:8]}",
                        "amount": round(random.uniform(10, 500), 2),
                        "merchant_category": random.choice(["retail", "food", "travel", "online"]),
                        "time_of_day": random.randint(0, 23),
                        "day_of_week": random.randint(0, 6),
                        "is_international": random.random() < 0.15,
                        "is_fraud": random.random() < fraud_rate,
                    }
                )

        elif dataset_type == "applications":
            features = [
                {"name": "application_id", "type": "string", "description": "Application ID"},
                {"name": "income", "type": "float", "description": "Annual income"},
                {"name": "debt_ratio", "type": "float", "description": "Debt to income ratio"},
                {
                    "name": "credit_history_months",
                    "type": "integer",
                    "description": "Credit history length",
                },
                {"name": "num_accounts", "type": "integer", "description": "Number of accounts"},
                {"name": "employment_years", "type": "float", "description": "Years employed"},
                {"name": "defaulted", "type": "boolean", "description": "Default label"},
            ]
            default_rate = config.get("default_rate", 0.15)
            statistics = {"default_rate": default_rate, "avg_income": 55000, "avg_debt_ratio": 0.35}
            for _i in range(min(5, record_count)):
                preview.append(
                    {
                        "application_id": f"app_{uuid.uuid4().hex[:8]}",
                        "income": round(random.uniform(25000, 150000), 2),
                        "debt_ratio": round(random.uniform(0.1, 0.6), 2),
                        "credit_history_months": random.randint(12, 240),
                        "num_accounts": random.randint(1, 10),
                        "employment_years": round(random.uniform(0.5, 20), 1),
                        "defaulted": random.random() < default_rate,
                    }
                )

        elif dataset_type == "customers":
            features = [
                {"name": "customer_id", "type": "string", "description": "Customer ID"},
                {"name": "tenure_months", "type": "integer", "description": "Months as customer"},
                {"name": "monthly_spend", "type": "float", "description": "Average monthly spend"},
                {"name": "num_purchases", "type": "integer", "description": "Total purchases"},
                {
                    "name": "last_purchase_days",
                    "type": "integer",
                    "description": "Days since last purchase",
                },
                {"name": "segment", "type": "category", "description": "Customer segment"},
                {"name": "churned", "type": "boolean", "description": "Churn label"},
            ]
            churn_rate = config.get("churn_rate", 0.20)
            statistics = {"churn_rate": churn_rate, "avg_tenure": 24, "avg_monthly_spend": 125}
            for _i in range(min(5, record_count)):
                preview.append(
                    {
                        "customer_id": f"cust_{uuid.uuid4().hex[:8]}",
                        "tenure_months": random.randint(1, 60),
                        "monthly_spend": round(random.uniform(20, 500), 2),
                        "num_purchases": random.randint(1, 100),
                        "last_purchase_days": random.randint(1, 180),
                        "segment": random.choice(["bronze", "silver", "gold", "platinum"]),
                        "churned": random.random() < churn_rate,
                    }
                )

        elif dataset_type == "patients":
            features = [
                {"name": "patient_id", "type": "string", "description": "Patient ID"},
                {"name": "age", "type": "integer", "description": "Patient age"},
                {"name": "gender", "type": "category", "description": "Gender"},
                {"name": "bmi", "type": "float", "description": "Body mass index"},
                {"name": "blood_pressure", "type": "float", "description": "Blood pressure"},
                {"name": "cholesterol", "type": "category", "description": "Cholesterol level"},
                {"name": "smoker", "type": "boolean", "description": "Smoking status"},
            ]
            statistics = {"avg_age": 45, "avg_bmi": 26.5, "smoker_rate": 0.18}
            for _i in range(min(5, record_count)):
                preview.append(
                    {
                        "patient_id": f"pat_{uuid.uuid4().hex[:8]}",
                        "age": random.randint(18, 85),
                        "gender": random.choice(["M", "F"]),
                        "bmi": round(random.uniform(18, 40), 1),
                        "blood_pressure": round(random.uniform(90, 160), 0),
                        "cholesterol": random.choice(["normal", "borderline", "high"]),
                        "smoker": random.random() < 0.18,
                    }
                )

        else:  # generic
            features = [
                {"name": "id", "type": "string", "description": "Record ID"},
                {"name": "feature_1", "type": "float", "description": "Numeric feature 1"},
                {"name": "feature_2", "type": "float", "description": "Numeric feature 2"},
                {"name": "feature_3", "type": "float", "description": "Numeric feature 3"},
                {"name": "category", "type": "category", "description": "Category feature"},
                {"name": "label", "type": "boolean", "description": "Target label"},
            ]
            statistics = {"feature_1_mean": 0.5, "feature_2_mean": 0.5, "label_rate": 0.3}
            for _i in range(min(5, record_count)):
                preview.append(
                    {
                        "id": f"rec_{uuid.uuid4().hex[:8]}",
                        "feature_1": round(random.random(), 3),
                        "feature_2": round(random.random(), 3),
                        "feature_3": round(random.random(), 3),
                        "category": random.choice(["A", "B", "C"]),
                        "label": random.random() < 0.3,
                    }
                )

        return features, statistics, preview

    def get_dataset(self, dataset_id: str) -> Optional[dict]:
        """Get a synthetic dataset by ID.

        Args:
            dataset_id: Dataset ID.

        Returns:
            Dataset data or None if not found.
        """
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM synthetic_datasets WHERE id = ?", (dataset_id,))
            row = cursor.fetchone()

            if not row:
                return None

            dataset = dict(row)
            dataset["features"] = json.loads(dataset.get("features", "[]"))
            dataset["data_preview"] = json.loads(dataset.get("data_preview", "[]"))
            dataset["statistics"] = json.loads(dataset.get("statistics", "{}"))
            dataset["metadata"] = json.loads(dataset.get("metadata", "{}"))

            return dataset

    def list_datasets(self, sandbox_id: str) -> list[dict]:
        """List datasets in a sandbox.

        Args:
            sandbox_id: Sandbox ID.

        Returns:
            List of datasets.
        """
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM synthetic_datasets
                WHERE sandbox_id = ?
                ORDER BY created_at DESC
            """,
                (sandbox_id,),
            )
            rows = cursor.fetchall()

        datasets = []
        for row in rows:
            dataset = dict(row)
            dataset["features"] = json.loads(dataset.get("features", "[]"))
            dataset["statistics"] = json.loads(dataset.get("statistics", "{}"))
            datasets.append(dataset)

        return datasets

    def delete_dataset(self, dataset_id: str, owner_id: Optional[str] = None) -> bool:
        """Delete a dataset.

        Args:
            dataset_id: Dataset ID.
            owner_id: Optional owner ID for verification.

        Returns:
            True if deleted successfully.
        """
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verify ownership via sandbox if owner_id provided
            if owner_id:
                cursor.execute(
                    """
                    SELECT s.owner_id FROM synthetic_datasets d
                    JOIN sandbox_environments s ON d.sandbox_id = s.id
                    WHERE d.id = ?
                """,
                    (dataset_id,),
                )
                row = cursor.fetchone()
                if not row or row[0] != owner_id:
                    return False

            cursor.execute("DELETE FROM synthetic_datasets WHERE id = ?", (dataset_id,))
            conn.commit()
            return cursor.rowcount > 0

    def create_experiment(
        self,
        sandbox_id: str,
        name: str,
        experiment_type: str,
        created_by: str,
        model_type: Optional[str] = None,
        dataset_id: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[dict] = None,
    ) -> dict:
        """Create a new experiment in the sandbox.

        Args:
            sandbox_id: Sandbox ID.
            name: Experiment name.
            experiment_type: Type of experiment.
            created_by: Creator company ID.
            model_type: Optional model type.
            dataset_id: Optional dataset to use.
            description: Optional description.
            config: Optional configuration.

        Returns:
            Created experiment data.
        """
        self._init_sandbox_schema()

        experiment_id = f"exp_{uuid.uuid4().hex[:16]}"
        config = config or {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sandbox_experiments
                (id, sandbox_id, name, description, experiment_type, model_type,
                 dataset_id, config, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    experiment_id,
                    sandbox_id,
                    name,
                    description,
                    experiment_type,
                    model_type,
                    dataset_id,
                    json.dumps(config),
                    created_by,
                ),
            )
            conn.commit()

        return self.get_experiment(experiment_id)

    def get_experiment(self, experiment_id: str) -> Optional[dict]:
        """Get an experiment by ID.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Experiment data or None if not found.
        """
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.*, d.name as dataset_name
                FROM sandbox_experiments e
                LEFT JOIN synthetic_datasets d ON e.dataset_id = d.id
                WHERE e.id = ?
            """,
                (experiment_id,),
            )
            row = cursor.fetchone()

            if not row:
                return None

            experiment = dict(row)
            experiment["config"] = json.loads(experiment.get("config", "{}"))
            experiment["results"] = json.loads(experiment.get("results", "{}"))

            return experiment

    def list_experiments(self, sandbox_id: str) -> list[dict]:
        """List experiments in a sandbox.

        Args:
            sandbox_id: Sandbox ID.

        Returns:
            List of experiments.
        """
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT e.*, d.name as dataset_name
                FROM sandbox_experiments e
                LEFT JOIN synthetic_datasets d ON e.dataset_id = d.id
                WHERE e.sandbox_id = ?
                ORDER BY e.created_at DESC
            """,
                (sandbox_id,),
            )
            rows = cursor.fetchall()

        experiments = []
        for row in rows:
            exp = dict(row)
            exp["config"] = json.loads(exp.get("config", "{}"))
            exp["results"] = json.loads(exp.get("results", "{}"))
            experiments.append(exp)

        return experiments

    def run_experiment(self, experiment_id: str) -> dict:
        """Run an experiment and return results.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Updated experiment with results.
        """
        self._init_sandbox_schema()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Update status to running
            cursor.execute(
                """
                UPDATE sandbox_experiments
                SET status = 'running', started_at = ?
                WHERE id = ?
            """,
                (datetime.utcnow(), experiment_id),
            )
            conn.commit()

            # Get experiment details
            cursor.execute("SELECT * FROM sandbox_experiments WHERE id = ?", (experiment_id,))
            exp = dict(cursor.fetchone())
            exp_type = exp.get("experiment_type")
            model_type = exp.get("model_type")

            # Simulate experiment results
            results = self._simulate_experiment_results(exp_type, model_type)

            # Update with results
            cursor.execute(
                """
                UPDATE sandbox_experiments
                SET status = 'completed', completed_at = ?, results = ?
                WHERE id = ?
            """,
                (datetime.utcnow(), json.dumps(results), experiment_id),
            )
            conn.commit()

        return self.get_experiment(experiment_id)

    def _simulate_experiment_results(self, experiment_type: str, model_type: Optional[str]) -> dict:
        """Simulate experiment results."""
        if experiment_type == "training":
            return {
                "status": "success",
                "epochs": 100,
                "training_time_seconds": round(random.uniform(5, 30), 2),
                "final_loss": round(random.uniform(0.1, 0.5), 4),
                "metrics": {
                    "accuracy": round(random.uniform(0.75, 0.95), 3),
                    "precision": round(random.uniform(0.70, 0.90), 3),
                    "recall": round(random.uniform(0.65, 0.88), 3),
                    "f1_score": round(random.uniform(0.68, 0.89), 3),
                },
            }
        elif experiment_type == "evaluation":
            return {
                "status": "success",
                "evaluation_time_seconds": round(random.uniform(1, 5), 2),
                "metrics": {
                    "accuracy": round(random.uniform(0.75, 0.92), 3),
                    "auc": round(random.uniform(0.80, 0.95), 3),
                    "precision": round(random.uniform(0.70, 0.88), 3),
                    "recall": round(random.uniform(0.65, 0.85), 3),
                },
                "confusion_matrix": {
                    "true_positive": random.randint(800, 950),
                    "true_negative": random.randint(800, 950),
                    "false_positive": random.randint(50, 150),
                    "false_negative": random.randint(50, 150),
                },
            }
        elif experiment_type in ("clustering", "segmentation"):
            n_clusters = random.randint(3, 6)
            return {
                "status": "success",
                "n_clusters": n_clusters,
                "inertia": round(random.uniform(100, 500), 2),
                "silhouette_score": round(random.uniform(0.4, 0.8), 3),
                "cluster_sizes": [random.randint(100, 500) for _ in range(n_clusters)],
            }
        elif experiment_type == "encryption_benchmark":
            return {
                "status": "success",
                "encryption_time_ms": round(random.uniform(50, 200), 2),
                "decryption_time_ms": round(random.uniform(30, 150), 2),
                "key_generation_time_ms": round(random.uniform(100, 500), 2),
                "ciphertext_size_kb": round(random.uniform(10, 100), 1),
                "noise_budget": round(random.uniform(20, 40), 1),
            }
        else:
            return {
                "status": "success",
                "message": f"Experiment type '{experiment_type}' completed",
                "execution_time_seconds": round(random.uniform(1, 10), 2),
            }

    def delete_experiment(self, experiment_id: str, owner_id: Optional[str] = None) -> bool:
        """Delete an experiment.

        Args:
            experiment_id: Experiment ID.
            owner_id: Optional owner ID for verification.

        Returns:
            True if deleted successfully.
        """
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verify ownership via sandbox if owner_id provided
            if owner_id:
                cursor.execute(
                    """
                    SELECT s.owner_id FROM sandbox_experiments e
                    JOIN sandbox_environments s ON e.sandbox_id = s.id
                    WHERE e.id = ?
                """,
                    (experiment_id,),
                )
                row = cursor.fetchone()
                if not row or row[0] != owner_id:
                    return False

            cursor.execute("DELETE FROM sandbox_experiments WHERE id = ?", (experiment_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_sandbox_templates(self, industry: Optional[str] = None) -> list[dict]:
        """List available sandbox templates.

        Args:
            industry: Optional industry filter.

        Returns:
            List of templates.
        """
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM sandbox_templates WHERE is_public = 1"
            params = []

            if industry:
                query += " AND (industry = ? OR industry = 'general')"
                params.append(industry)

            query += " ORDER BY name"

            cursor.execute(query, params)
            rows = cursor.fetchall()

        templates = []
        for row in rows:
            tpl = dict(row)
            tpl["datasets"] = json.loads(tpl.get("datasets", "[]"))
            tpl["experiments"] = json.loads(tpl.get("experiments", "[]"))
            templates.append(tpl)

        return templates

    def get_sandbox_stats(self, owner_id: Optional[str] = None) -> dict:
        """Get sandbox statistics.

        Args:
            owner_id: Optional owner filter.

        Returns:
            Sandbox statistics.
        """
        self._init_sandbox_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            base_query = ""
            params = []
            if owner_id:
                base_query = " WHERE owner_id = ?"
                params = [owner_id]

            cursor.execute(f"SELECT COUNT(*) FROM sandbox_environments{base_query}", params)
            total_sandboxes = cursor.fetchone()[0]

            cursor.execute(
                f"SELECT COUNT(*) FROM sandbox_environments WHERE status = 'active'{' AND owner_id = ?' if owner_id else ''}",
                params,
            )
            active_sandboxes = cursor.fetchone()[0]

            if owner_id:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM synthetic_datasets d
                    JOIN sandbox_environments s ON d.sandbox_id = s.id
                    WHERE s.owner_id = ?
                """,
                    (owner_id,),
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM synthetic_datasets")
            total_datasets = cursor.fetchone()[0]

            if owner_id:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM sandbox_experiments e
                    JOIN sandbox_environments s ON e.sandbox_id = s.id
                    WHERE s.owner_id = ?
                """,
                    (owner_id,),
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM sandbox_experiments")
            total_experiments = cursor.fetchone()[0]

            if owner_id:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM sandbox_experiments e
                    JOIN sandbox_environments s ON e.sandbox_id = s.id
                    WHERE s.owner_id = ? AND e.status = 'completed'
                """,
                    (owner_id,),
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM sandbox_experiments WHERE status = 'completed'"
                )
            completed_experiments = cursor.fetchone()[0]

        return {
            "total_sandboxes": total_sandboxes,
            "active_sandboxes": active_sandboxes,
            "total_datasets": total_datasets,
            "total_experiments": total_experiments,
            "completed_experiments": completed_experiments,
        }


# Export all public classes and functions
__all__ = ["SandboxManager"]
