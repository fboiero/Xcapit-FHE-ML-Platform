"""
Tests for the dataset generation module.

These tests verify that the synthetic dataset generators work correctly
and produce data suitable for FHE-ML demos.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_datasets import (
    generate_dataset,
    generate_consortium_split,
    get_sample_data,
    DatasetConfig,
    FINTECH_FRAUD_CONFIG,
    FINTECH_CREDIT_CONFIG,
    HEALTHCARE_DIABETES_CONFIG,
    HEALTHCARE_READMISSION_CONFIG,
    INSURANCE_CLAIMS_CONFIG,
    GOVERNMENT_SERVICES_CONFIG,
    RETAIL_CHURN_CONFIG,
)


class TestDatasetConfig:
    """Tests for DatasetConfig dataclass."""

    def test_fintech_fraud_config_exists(self):
        """Verify FINTECH_FRAUD_CONFIG has required fields."""
        assert FINTECH_FRAUD_CONFIG.name == "fintech_fraud_transactions"
        assert FINTECH_FRAUD_CONFIG.vertical == "fintech"
        assert FINTECH_FRAUD_CONFIG.n_samples == 10000
        assert FINTECH_FRAUD_CONFIG.target_column == "is_fraud"
        assert FINTECH_FRAUD_CONFIG.target_type == "binary"
        assert FINTECH_FRAUD_CONFIG.positive_rate == 0.02

    def test_healthcare_config_exists(self):
        """Verify HEALTHCARE_DIABETES_CONFIG has required fields."""
        assert HEALTHCARE_DIABETES_CONFIG.name == "healthcare_diabetes_risk"
        assert HEALTHCARE_DIABETES_CONFIG.vertical == "healthcare"
        assert HEALTHCARE_DIABETES_CONFIG.target_column == "has_diabetes"
        assert len(HEALTHCARE_DIABETES_CONFIG.features) > 0

    def test_insurance_config_exists(self):
        """Verify INSURANCE_CLAIMS_CONFIG has required fields."""
        assert INSURANCE_CLAIMS_CONFIG.name == "insurance_claims_fraud"
        assert INSURANCE_CLAIMS_CONFIG.vertical == "insurance"
        assert INSURANCE_CLAIMS_CONFIG.n_samples == 15000
        assert INSURANCE_CLAIMS_CONFIG.positive_rate == 0.05

    def test_government_config_is_regression(self):
        """Verify GOVERNMENT_SERVICES_CONFIG is regression type."""
        assert GOVERNMENT_SERVICES_CONFIG.target_type == "regression"
        assert GOVERNMENT_SERVICES_CONFIG.positive_rate is None

    def test_retail_config_exists(self):
        """Verify RETAIL_CHURN_CONFIG has required fields."""
        assert RETAIL_CHURN_CONFIG.name == "retail_customer_churn"
        assert RETAIL_CHURN_CONFIG.vertical == "retail"
        assert RETAIL_CHURN_CONFIG.positive_rate == 0.18


class TestDatasetGeneration:
    """Tests for dataset generation functions."""

    def test_fintech_dataset_shape(self):
        """Verify fintech dataset has correct shape."""
        df = generate_dataset(FINTECH_FRAUD_CONFIG)
        assert len(df) == FINTECH_FRAUD_CONFIG.n_samples
        assert FINTECH_FRAUD_CONFIG.target_column in df.columns
        assert "record_id" in df.columns

    def test_fintech_fraud_rate_approximate(self):
        """Verify fraud rate is approximately correct."""
        df = generate_dataset(FINTECH_FRAUD_CONFIG)
        actual_rate = df["is_fraud"].mean()
        expected_rate = FINTECH_FRAUD_CONFIG.positive_rate
        # Allow 5% tolerance
        assert abs(actual_rate - expected_rate) < 0.05

    def test_healthcare_dataset_shape(self):
        """Verify healthcare dataset has correct shape."""
        df = generate_dataset(HEALTHCARE_DIABETES_CONFIG)
        assert len(df) == HEALTHCARE_DIABETES_CONFIG.n_samples
        assert "has_diabetes" in df.columns

    def test_insurance_dataset_shape(self):
        """Verify insurance dataset has correct shape."""
        df = generate_dataset(INSURANCE_CLAIMS_CONFIG)
        assert len(df) == INSURANCE_CLAIMS_CONFIG.n_samples
        assert "is_fraudulent" in df.columns

    def test_government_dataset_is_regression(self):
        """Verify government dataset has continuous target."""
        df = generate_dataset(GOVERNMENT_SERVICES_CONFIG)
        # Regression target should have many unique values
        unique_values = df["service_demand_score"].nunique()
        assert unique_values > 100

    def test_retail_dataset_shape(self):
        """Verify retail dataset has correct shape."""
        df = generate_dataset(RETAIL_CHURN_CONFIG)
        assert len(df) == RETAIL_CHURN_CONFIG.n_samples
        assert "churned" in df.columns

    def test_all_features_present(self):
        """Verify all configured features are in the dataset."""
        df = generate_dataset(FINTECH_FRAUD_CONFIG)
        for feature in FINTECH_FRAUD_CONFIG.features:
            assert feature["name"] in df.columns, f"Missing feature: {feature['name']}"

    def test_reproducibility(self):
        """Verify same seed produces same data."""
        df1 = generate_dataset(FINTECH_FRAUD_CONFIG, seed=42)
        df2 = generate_dataset(FINTECH_FRAUD_CONFIG, seed=42)
        assert df1.equals(df2)

    def test_different_seeds_produce_different_data(self):
        """Verify different seeds produce different data."""
        df1 = generate_dataset(FINTECH_FRAUD_CONFIG, seed=42)
        df2 = generate_dataset(FINTECH_FRAUD_CONFIG, seed=123)
        assert not df1.equals(df2)

    def test_record_id_is_unique(self):
        """Verify record_id is unique for all rows."""
        df = generate_dataset(FINTECH_FRAUD_CONFIG)
        assert df["record_id"].nunique() == len(df)


class TestConsortiumSplit:
    """Tests for consortium split functionality."""

    def test_split_preserves_total(self):
        """Verify split preserves total number of records."""
        df = generate_dataset(FINTECH_FRAUD_CONFIG)
        splits = generate_consortium_split(df, n_members=3)
        total = sum(len(s) for s in splits.values())
        assert total == len(df)

    def test_split_creates_correct_members(self):
        """Verify split creates correct number of members."""
        df = generate_dataset(FINTECH_FRAUD_CONFIG)
        splits = generate_consortium_split(df, n_members=3)
        assert len(splits) == 3

    def test_split_with_custom_names(self):
        """Verify split works with custom member names."""
        df = generate_dataset(FINTECH_FRAUD_CONFIG)
        names = ["Banco A", "Banco B", "Banco C"]
        splits = generate_consortium_split(df, n_members=3, member_names=names)
        assert set(splits.keys()) == set(names)

    def test_splits_are_mutually_exclusive(self):
        """Verify splits don't share records."""
        df = generate_dataset(FINTECH_FRAUD_CONFIG)
        splits = generate_consortium_split(df, n_members=3)

        # Get all record IDs from splits
        all_ids = []
        for split_df in splits.values():
            all_ids.extend(split_df["record_id"].tolist())

        # Should have no duplicates
        assert len(all_ids) == len(set(all_ids))

    def test_split_approximately_equal(self):
        """Verify splits are approximately equal in size."""
        df = generate_dataset(FINTECH_FRAUD_CONFIG)
        splits = generate_consortium_split(df, n_members=3)

        sizes = [len(s) for s in splits.values()]
        avg_size = sum(sizes) / len(sizes)

        # Each split should be within 10% of average
        for size in sizes:
            assert abs(size - avg_size) / avg_size < 0.1


class TestGetSampleData:
    """Tests for get_sample_data convenience function."""

    def test_fintech_sample(self):
        """Verify fintech sample generation."""
        df = get_sample_data("fintech", n_samples=100)
        assert len(df) == 100
        assert "is_fraud" in df.columns

    def test_healthcare_sample(self):
        """Verify healthcare sample generation."""
        df = get_sample_data("healthcare", n_samples=100)
        assert len(df) == 100
        assert "has_diabetes" in df.columns

    def test_insurance_sample(self):
        """Verify insurance sample generation."""
        df = get_sample_data("insurance", n_samples=100)
        assert len(df) == 100
        assert "is_fraudulent" in df.columns

    def test_government_sample(self):
        """Verify government sample generation."""
        df = get_sample_data("government", n_samples=100)
        assert len(df) == 100
        assert "service_demand_score" in df.columns

    def test_retail_sample(self):
        """Verify retail sample generation."""
        df = get_sample_data("retail", n_samples=100)
        assert len(df) == 100
        assert "churned" in df.columns

    def test_invalid_vertical_raises_error(self):
        """Verify invalid vertical raises ValueError."""
        with pytest.raises(ValueError):
            get_sample_data("invalid_vertical", n_samples=100)

    def test_all_verticals_generate(self):
        """Verify all verticals can generate data."""
        verticals = ["fintech", "healthcare", "insurance", "government", "retail"]
        for vertical in verticals:
            df = get_sample_data(vertical, n_samples=50)
            assert len(df) == 50, f"Failed for vertical: {vertical}"


class TestDataQuality:
    """Tests for data quality and integrity."""

    def test_no_null_values(self):
        """Verify datasets have no null values."""
        configs = [
            FINTECH_FRAUD_CONFIG,
            HEALTHCARE_DIABETES_CONFIG,
            INSURANCE_CLAIMS_CONFIG,
            RETAIL_CHURN_CONFIG,
        ]
        for config in configs:
            # Use smaller sample for speed
            small_config = DatasetConfig(
                name=config.name,
                vertical=config.vertical,
                n_samples=100,
                features=config.features,
                target_column=config.target_column,
                target_type=config.target_type,
                positive_rate=config.positive_rate,
            )
            df = generate_dataset(small_config)
            assert df.isnull().sum().sum() == 0, f"Null values in {config.name}"

    def test_binary_target_values(self):
        """Verify binary targets have only 0 and 1."""
        df = get_sample_data("fintech", n_samples=100)
        assert set(df["is_fraud"].unique()).issubset({0, 1})

    def test_numeric_features_are_numeric(self):
        """Verify numeric features have numeric dtypes."""
        df = get_sample_data("fintech", n_samples=100)
        numeric_cols = ["amount", "hour", "distance_km", "transaction_frequency"]
        for col in numeric_cols:
            if col in df.columns:
                assert df[col].dtype in ["int64", "float64", "int32", "float32"], f"{col} is not numeric"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
