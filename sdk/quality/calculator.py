"""Data Quality Calculator for FHE-ML Platform.

This module provides real data quality calculations based on metadata
and statistical properties of data WITHOUT accessing the actual values.

Quality Metrics:
- Completeness: Measures the proportion of non-null values
- Consistency: Measures adherence to expected formats and ranges
- Uniqueness: Measures the proportion of unique/non-duplicate values
- Validity: Measures values that pass validation rules
- Freshness: Measures how recent the data is

All calculations work on aggregated statistics, not raw data,
preserving privacy while providing quality insights.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass
class DataProfile:
    """Profile of data characteristics without exposing values."""
    record_count: int
    feature_count: int
    null_counts: Dict[str, int] = field(default_factory=dict)
    duplicate_count: int = 0
    outlier_count: int = 0
    schema_violations: int = 0
    format_violations: int = 0
    range_violations: int = 0
    last_updated: Optional[datetime] = None
    data_hash: Optional[str] = None


@dataclass
class QualityScore:
    """Quality assessment scores."""
    overall: float
    completeness: float
    consistency: float
    uniqueness: float
    validity: float
    freshness: float
    details: Dict[str, Any] = field(default_factory=dict)


class DataQualityCalculator:
    """Calculator for data quality metrics from metadata."""

    def __init__(self, freshness_threshold_days: int = 30):
        """Initialize the calculator.

        Args:
            freshness_threshold_days: Days after which data is considered stale.
        """
        self.freshness_threshold_days = freshness_threshold_days

    def calculate_completeness(
        self,
        record_count: int,
        feature_count: int,
        null_count: int = 0,
        null_counts_per_feature: Optional[Dict[str, int]] = None
    ) -> float:
        """Calculate completeness score (0-100).

        Measures the proportion of non-null values in the dataset.

        Args:
            record_count: Total number of records.
            feature_count: Number of features/columns.
            null_count: Total null values across all features.
            null_counts_per_feature: Optional per-feature null counts.

        Returns:
            Completeness score from 0 to 100.
        """
        if record_count == 0 or feature_count == 0:
            return 0.0

        total_cells = record_count * feature_count

        if null_counts_per_feature:
            null_count = sum(null_counts_per_feature.values())

        if null_count < 0:
            null_count = 0
        if null_count > total_cells:
            null_count = total_cells

        completeness = ((total_cells - null_count) / total_cells) * 100
        return round(min(100.0, max(0.0, completeness)), 2)

    def calculate_consistency(
        self,
        record_count: int,
        schema_violations: int = 0,
        format_violations: int = 0,
        range_violations: int = 0
    ) -> float:
        """Calculate consistency score (0-100).

        Measures adherence to expected formats, schemas, and ranges.

        Args:
            record_count: Total number of records.
            schema_violations: Records with schema issues.
            format_violations: Records with format issues.
            range_violations: Records with out-of-range values.

        Returns:
            Consistency score from 0 to 100.
        """
        if record_count == 0:
            return 0.0

        total_violations = schema_violations + format_violations + range_violations

        if total_violations < 0:
            total_violations = 0

        # Each violation type has equal weight
        max_violations = record_count * 3  # 3 types of violations

        consistency = ((max_violations - total_violations) / max_violations) * 100
        return round(min(100.0, max(0.0, consistency)), 2)

    def calculate_uniqueness(
        self,
        record_count: int,
        duplicate_count: int = 0
    ) -> float:
        """Calculate uniqueness score (0-100).

        Measures the proportion of unique (non-duplicate) records.

        Args:
            record_count: Total number of records.
            duplicate_count: Number of duplicate records.

        Returns:
            Uniqueness score from 0 to 100.
        """
        if record_count == 0:
            return 0.0

        if duplicate_count < 0:
            duplicate_count = 0
        if duplicate_count > record_count:
            duplicate_count = record_count

        uniqueness = ((record_count - duplicate_count) / record_count) * 100
        return round(min(100.0, max(0.0, uniqueness)), 2)

    def calculate_validity(
        self,
        record_count: int,
        invalid_count: int = 0,
        validation_rules_passed: int = 0,
        total_validation_rules: int = 0
    ) -> float:
        """Calculate validity score (0-100).

        Measures records that pass business validation rules.

        Args:
            record_count: Total number of records.
            invalid_count: Number of records failing validation.
            validation_rules_passed: Number of rules passed.
            total_validation_rules: Total validation rules applied.

        Returns:
            Validity score from 0 to 100.
        """
        if record_count == 0:
            return 0.0

        # Record-level validity
        record_validity = ((record_count - invalid_count) / record_count) * 100

        # Rule-level validity (if rules are provided)
        if total_validation_rules > 0:
            rule_validity = (validation_rules_passed / total_validation_rules) * 100
            # Combine both metrics
            validity = (record_validity + rule_validity) / 2
        else:
            validity = record_validity

        return round(min(100.0, max(0.0, validity)), 2)

    def calculate_freshness(
        self,
        last_updated: Optional[datetime] = None,
        reference_time: Optional[datetime] = None
    ) -> float:
        """Calculate freshness score (0-100).

        Measures how recent the data is relative to threshold.

        Args:
            last_updated: When data was last updated.
            reference_time: Reference time (defaults to now).

        Returns:
            Freshness score from 0 to 100.
        """
        if not last_updated:
            return 0.0

        reference = reference_time or datetime.utcnow()

        if isinstance(last_updated, str):
            try:
                last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            except ValueError:
                return 0.0

        # Remove timezone info for comparison
        if last_updated.tzinfo is not None:
            last_updated = last_updated.replace(tzinfo=None)
        if reference.tzinfo is not None:
            reference = reference.replace(tzinfo=None)

        age_days = (reference - last_updated).total_seconds() / 86400

        if age_days <= 0:
            return 100.0

        if age_days >= self.freshness_threshold_days:
            return 0.0

        # Linear decay
        freshness = ((self.freshness_threshold_days - age_days) / self.freshness_threshold_days) * 100
        return round(min(100.0, max(0.0, freshness)), 2)

    def calculate_overall(
        self,
        completeness: float,
        consistency: float,
        uniqueness: float,
        validity: float,
        freshness: float,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate overall quality score (0-100).

        Weighted average of all quality dimensions.

        Args:
            completeness: Completeness score.
            consistency: Consistency score.
            uniqueness: Uniqueness score.
            validity: Validity score.
            freshness: Freshness score.
            weights: Optional custom weights (default: equal).

        Returns:
            Overall quality score from 0 to 100.
        """
        if weights is None:
            weights = {
                'completeness': 0.25,
                'consistency': 0.20,
                'uniqueness': 0.20,
                'validity': 0.20,
                'freshness': 0.15,
            }

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0

        overall = (
            completeness * weights.get('completeness', 0.2) +
            consistency * weights.get('consistency', 0.2) +
            uniqueness * weights.get('uniqueness', 0.2) +
            validity * weights.get('validity', 0.2) +
            freshness * weights.get('freshness', 0.2)
        ) / total_weight

        return round(min(100.0, max(0.0, overall)), 2)

    def assess_quality(self, profile: DataProfile) -> QualityScore:
        """Perform complete quality assessment from data profile.

        Args:
            profile: DataProfile containing metadata about the data.

        Returns:
            QualityScore with all metrics calculated.
        """
        # Calculate total nulls from per-feature counts
        total_nulls = sum(profile.null_counts.values()) if profile.null_counts else 0

        completeness = self.calculate_completeness(
            profile.record_count,
            profile.feature_count,
            total_nulls
        )

        consistency = self.calculate_consistency(
            profile.record_count,
            profile.schema_violations,
            profile.format_violations,
            profile.range_violations
        )

        uniqueness = self.calculate_uniqueness(
            profile.record_count,
            profile.duplicate_count
        )

        # For validity, we estimate from outliers and violations
        invalid_count = profile.outlier_count + profile.schema_violations
        validity = self.calculate_validity(
            profile.record_count,
            invalid_count
        )

        freshness = self.calculate_freshness(profile.last_updated)

        overall = self.calculate_overall(
            completeness, consistency, uniqueness, validity, freshness
        )

        return QualityScore(
            overall=overall,
            completeness=completeness,
            consistency=consistency,
            uniqueness=uniqueness,
            validity=validity,
            freshness=freshness,
            details={
                'record_count': profile.record_count,
                'feature_count': profile.feature_count,
                'null_ratio': round(total_nulls / (profile.record_count * profile.feature_count) * 100, 2) if profile.record_count > 0 and profile.feature_count > 0 else 0,
                'duplicate_ratio': round(profile.duplicate_count / profile.record_count * 100, 2) if profile.record_count > 0 else 0,
                'outlier_ratio': round(profile.outlier_count / profile.record_count * 100, 2) if profile.record_count > 0 else 0,
            }
        )

    def assess_from_metadata(
        self,
        record_count: int,
        feature_count: int,
        null_count: int = 0,
        duplicate_count: int = 0,
        outlier_count: int = 0,
        last_updated: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Assess quality directly from metadata values.

        Convenience method that creates a profile and assesses it.

        Args:
            record_count: Total records.
            feature_count: Total features.
            null_count: Total null values.
            duplicate_count: Duplicate records.
            outlier_count: Outlier values detected.
            last_updated: Last update timestamp.
            metadata: Additional metadata.

        Returns:
            Dictionary with all quality metrics and assessment ID.
        """
        profile = DataProfile(
            record_count=record_count,
            feature_count=feature_count,
            duplicate_count=duplicate_count,
            outlier_count=outlier_count,
            last_updated=last_updated or datetime.utcnow(),
        )

        # Distribute nulls evenly if only total is provided
        if null_count > 0 and feature_count > 0:
            nulls_per_feature = null_count // feature_count
            for i in range(feature_count):
                profile.null_counts[f'feature_{i}'] = nulls_per_feature

        score = self.assess_quality(profile)

        assessment_id = f"qa_{uuid.uuid4().hex[:12]}"

        return {
            'id': assessment_id,
            'overall_score': score.overall,
            'completeness_score': score.completeness,
            'consistency_score': score.consistency,
            'uniqueness_score': score.uniqueness,
            'validity_score': score.validity,
            'freshness_score': score.freshness,
            'record_count': record_count,
            'feature_count': feature_count,
            'null_ratio': score.details.get('null_ratio', 0),
            'duplicate_ratio': score.details.get('duplicate_ratio', 0),
            'outlier_ratio': score.details.get('outlier_ratio', 0),
            'assessed_at': datetime.utcnow(),
            'metadata': metadata,
        }


def calculate_quality_from_encrypted_metadata(
    encrypted_record_count: int,
    encrypted_feature_count: int,
    stats_summary: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate quality metrics from FHE-encrypted data statistics.

    This function works with aggregated statistics that can be computed
    on encrypted data, providing quality insights without decryption.

    Args:
        encrypted_record_count: Count of encrypted records.
        encrypted_feature_count: Count of encrypted features.
        stats_summary: Summary statistics (can be computed on encrypted data):
            - null_bitmap_count: Count of null indicators
            - duplicate_hash_collisions: Hash collisions (approximate duplicates)
            - range_check_failures: Out-of-range values detected
            - timestamp: When statistics were computed

    Returns:
        Quality assessment dictionary.
    """
    calculator = DataQualityCalculator()

    return calculator.assess_from_metadata(
        record_count=encrypted_record_count,
        feature_count=encrypted_feature_count,
        null_count=stats_summary.get('null_bitmap_count', 0),
        duplicate_count=stats_summary.get('duplicate_hash_collisions', 0),
        outlier_count=stats_summary.get('range_check_failures', 0),
        last_updated=stats_summary.get('timestamp'),
        metadata={'source': 'fhe_encrypted', 'stats_summary': stats_summary}
    )
