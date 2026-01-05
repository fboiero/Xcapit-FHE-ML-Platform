"""
Data generation service for synthetic datasets.

Handles:
- Feature schema generation by dataset type
- Synthetic data preview generation
- Statistical profile calculation
"""

from __future__ import annotations

import random
from typing import Any

from apps.core.services.base import BaseService, ServiceResult


class DataGenerationService(BaseService):
    """
    Service for generating synthetic data.

    Encapsulates all logic for creating synthetic datasets with
    configurable features and realistic statistical distributions.
    """

    # Default feature schemas by dataset type
    DEFAULT_FEATURES = {
        "transactions": [
            {"name": "amount", "type": "float", "min": 0, "max": 10000},
            {
                "name": "merchant_category",
                "type": "category",
                "values": ["retail", "food", "travel", "online"],
            },
            {"name": "hour", "type": "int", "min": 0, "max": 23},
            {"name": "is_fraud", "type": "bool", "true_ratio": 0.02},
        ],
        "patients": [
            {"name": "age", "type": "int", "min": 18, "max": 90},
            {"name": "blood_pressure", "type": "float", "min": 80, "max": 180},
            {"name": "cholesterol", "type": "float", "min": 100, "max": 300},
            {
                "name": "diagnosis",
                "type": "category",
                "values": ["healthy", "at_risk", "condition"],
            },
        ],
        "credit_scores": [
            {"name": "income", "type": "float", "min": 20000, "max": 200000},
            {"name": "debt_ratio", "type": "float", "min": 0, "max": 1},
            {"name": "credit_history_months", "type": "int", "min": 0, "max": 360},
            {"name": "default", "type": "bool", "true_ratio": 0.05},
        ],
        "claims": [
            {"name": "claim_amount", "type": "float", "min": 100, "max": 100000},
            {
                "name": "claim_type",
                "type": "category",
                "values": ["auto", "health", "property", "liability"],
            },
            {"name": "days_to_process", "type": "int", "min": 1, "max": 90},
            {"name": "is_fraudulent", "type": "bool", "true_ratio": 0.03},
        ],
        "default": [
            {"name": "feature_1", "type": "float", "min": 0, "max": 100},
            {"name": "feature_2", "type": "float", "min": 0, "max": 100},
            {"name": "label", "type": "bool", "true_ratio": 0.5},
        ],
    }

    def get_default_features(self, dataset_type: str) -> list[dict[str, Any]]:
        """
        Get default feature schema for a dataset type.

        Args:
            dataset_type: Type of dataset (transactions, patients, etc.)

        Returns:
            List of feature specifications
        """
        return self.DEFAULT_FEATURES.get(
            dataset_type.lower(),
            self.DEFAULT_FEATURES["default"],
        )

    def generate_preview(
        self,
        features: list[dict[str, Any]],
        count: int = 10,
        seed: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generate preview data rows based on feature specifications.

        Args:
            features: List of feature specifications
            count: Number of rows to generate
            seed: Optional random seed for reproducibility

        Returns:
            List of generated data rows
        """
        if seed is not None:
            random.seed(seed)

        rows = []
        for _ in range(count):
            row = self._generate_row(features)
            rows.append(row)

        return rows

    def _generate_row(self, features: list[dict[str, Any]]) -> dict[str, Any]:
        """Generate a single data row."""
        row = {}

        for feature in features:
            name = feature["name"]
            ftype = feature["type"]

            if ftype == "float":
                row[name] = round(
                    random.uniform(
                        feature.get("min", 0),
                        feature.get("max", 100),
                    ),
                    2,
                )
            elif ftype == "int":
                row[name] = random.randint(
                    feature.get("min", 0),
                    feature.get("max", 100),
                )
            elif ftype == "category":
                row[name] = random.choice(
                    feature.get("values", ["A", "B", "C"])
                )
            elif ftype == "bool":
                row[name] = random.random() < feature.get("true_ratio", 0.5)
            else:
                row[name] = None

        return row

    def calculate_statistics(
        self,
        features: list[dict[str, Any]],
        record_count: int,
    ) -> dict[str, Any]:
        """
        Calculate statistical profile for the dataset.

        Args:
            features: List of feature specifications
            record_count: Total number of records

        Returns:
            Dictionary with statistics for each feature
        """
        stats: dict[str, Any] = {
            "record_count": record_count,
            "feature_count": len(features),
            "features": {},
        }

        for feature in features:
            name = feature["name"]
            ftype = feature["type"]
            feature_stats = self._calculate_feature_stats(feature, ftype)
            stats["features"][name] = feature_stats

        return stats

    def _calculate_feature_stats(
        self,
        feature: dict[str, Any],
        ftype: str,
    ) -> dict[str, Any]:
        """Calculate statistics for a single feature."""
        if ftype in ["float", "int"]:
            min_val = feature.get("min", 0)
            max_val = feature.get("max", 100)
            return {
                "type": ftype,
                "min": min_val,
                "max": max_val,
                "mean": (min_val + max_val) / 2,
                "std_estimate": (max_val - min_val) / 4,  # Rough estimate
            }
        elif ftype == "category":
            values = feature.get("values", [])
            return {
                "type": ftype,
                "unique_values": len(values),
                "values": values,
                "distribution": "uniform",
            }
        elif ftype == "bool":
            ratio = feature.get("true_ratio", 0.5)
            return {
                "type": ftype,
                "true_ratio": ratio,
                "false_ratio": 1 - ratio,
            }
        else:
            return {"type": ftype}

    def generate_dataset(
        self,
        dataset_type: str,
        record_count: int,
        features: list[dict[str, Any]] | None = None,
        preview_count: int = 10,
    ) -> ServiceResult[dict]:
        """
        Generate a complete synthetic dataset specification.

        Args:
            dataset_type: Type of dataset to generate
            record_count: Number of records
            features: Optional custom features (uses defaults if not provided)
            preview_count: Number of preview rows to generate

        Returns:
            ServiceResult with dataset specification including features,
            statistics, and preview data
        """
        # Use provided features or defaults
        if not features:
            features = self.get_default_features(dataset_type)

        # Validate record count
        if record_count <= 0:
            return ServiceResult.fail(
                "Record count must be positive",
                error_code="validation_error",
            )

        if record_count > 1_000_000:
            return ServiceResult.fail(
                "Record count exceeds maximum (1,000,000)",
                error_code="validation_error",
            )

        # Generate preview and statistics
        preview = self.generate_preview(features, min(preview_count, record_count))
        statistics = self.calculate_statistics(features, record_count)

        result = {
            "dataset_type": dataset_type,
            "record_count": record_count,
            "feature_count": len(features),
            "features": features,
            "statistics": statistics,
            "preview": preview,
        }

        return ServiceResult.ok(result)
