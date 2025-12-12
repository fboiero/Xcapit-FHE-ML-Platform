"""Unit tests for DataQualityCalculator class.

Tests cover all individual metric calculations:
- Completeness score calculation
- Consistency score calculation
- Uniqueness score calculation
- Validity score calculation
- Freshness score calculation
- Overall score calculation
- DataProfile assessment
"""

import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sdk.quality.calculator import (
    DataQualityCalculator,
    DataProfile,
    QualityScore,
    calculate_quality_from_encrypted_metadata
)


class TestCompletenessCalculation:
    """Tests for completeness score calculation."""

    @pytest.fixture
    def calculator(self):
        return DataQualityCalculator()

    def test_completeness_perfect(self, calculator):
        """Test completeness with no nulls."""
        score = calculator.calculate_completeness(
            record_count=1000,
            feature_count=10,
            null_count=0
        )
        assert score == 100.0

    def test_completeness_with_nulls(self, calculator):
        """Test completeness with some null values."""
        # 1000 records, 10 features = 10000 cells
        # 1000 nulls = 10% null rate = 90% completeness
        score = calculator.calculate_completeness(
            record_count=1000,
            feature_count=10,
            null_count=1000
        )
        assert score == 90.0

    def test_completeness_half_nulls(self, calculator):
        """Test completeness with 50% nulls."""
        score = calculator.calculate_completeness(
            record_count=100,
            feature_count=10,
            null_count=500
        )
        assert score == 50.0

    def test_completeness_all_nulls(self, calculator):
        """Test completeness with all nulls."""
        score = calculator.calculate_completeness(
            record_count=100,
            feature_count=10,
            null_count=1000
        )
        assert score == 0.0

    def test_completeness_empty_records(self, calculator):
        """Test completeness with no records."""
        score = calculator.calculate_completeness(
            record_count=0,
            feature_count=10,
            null_count=0
        )
        assert score == 0.0

    def test_completeness_zero_features(self, calculator):
        """Test completeness with no features."""
        score = calculator.calculate_completeness(
            record_count=1000,
            feature_count=0,
            null_count=0
        )
        assert score == 0.0

    def test_completeness_negative_nulls_capped(self, calculator):
        """Test that negative null counts are treated as 0."""
        score = calculator.calculate_completeness(
            record_count=100,
            feature_count=10,
            null_count=-50
        )
        assert score == 100.0

    def test_completeness_excessive_nulls_capped(self, calculator):
        """Test that nulls exceeding total cells are capped."""
        score = calculator.calculate_completeness(
            record_count=100,
            feature_count=10,
            null_count=2000  # More than 1000 cells
        )
        assert score == 0.0

    def test_completeness_with_per_feature_nulls(self, calculator):
        """Test completeness with per-feature null counts."""
        null_counts = {
            'feature_0': 100,
            'feature_1': 200,
            'feature_2': 50
        }
        # Total: 350 nulls, 1000 records * 10 features = 10000 cells
        # 350/10000 = 3.5% null = 96.5% completeness
        score = calculator.calculate_completeness(
            record_count=1000,
            feature_count=10,
            null_count=0,
            null_counts_per_feature=null_counts
        )
        assert score == 96.5


class TestConsistencyCalculation:
    """Tests for consistency score calculation."""

    @pytest.fixture
    def calculator(self):
        return DataQualityCalculator()

    def test_consistency_perfect(self, calculator):
        """Test consistency with no violations."""
        score = calculator.calculate_consistency(
            record_count=1000,
            schema_violations=0,
            format_violations=0,
            range_violations=0
        )
        assert score == 100.0

    def test_consistency_with_violations(self, calculator):
        """Test consistency with some violations."""
        # 1000 records, max violations = 3000
        # 300 total violations = 10% violation rate = 90% consistency
        score = calculator.calculate_consistency(
            record_count=1000,
            schema_violations=100,
            format_violations=100,
            range_violations=100
        )
        assert score == 90.0

    def test_consistency_all_violations(self, calculator):
        """Test consistency when all records have violations."""
        score = calculator.calculate_consistency(
            record_count=100,
            schema_violations=100,
            format_violations=100,
            range_violations=100
        )
        assert score == 0.0

    def test_consistency_empty_records(self, calculator):
        """Test consistency with no records."""
        score = calculator.calculate_consistency(
            record_count=0,
            schema_violations=0
        )
        assert score == 0.0

    def test_consistency_negative_violations_capped(self, calculator):
        """Test that negative violations are treated as 0."""
        score = calculator.calculate_consistency(
            record_count=100,
            schema_violations=-10
        )
        assert score == 100.0


class TestUniquenessCalculation:
    """Tests for uniqueness score calculation."""

    @pytest.fixture
    def calculator(self):
        return DataQualityCalculator()

    def test_uniqueness_perfect(self, calculator):
        """Test uniqueness with no duplicates."""
        score = calculator.calculate_uniqueness(
            record_count=1000,
            duplicate_count=0
        )
        assert score == 100.0

    def test_uniqueness_with_duplicates(self, calculator):
        """Test uniqueness with some duplicates."""
        # 100 duplicates out of 1000 = 10% duplicates = 90% uniqueness
        score = calculator.calculate_uniqueness(
            record_count=1000,
            duplicate_count=100
        )
        assert score == 90.0

    def test_uniqueness_half_duplicates(self, calculator):
        """Test uniqueness with 50% duplicates."""
        score = calculator.calculate_uniqueness(
            record_count=100,
            duplicate_count=50
        )
        assert score == 50.0

    def test_uniqueness_all_duplicates(self, calculator):
        """Test uniqueness when all are duplicates."""
        score = calculator.calculate_uniqueness(
            record_count=100,
            duplicate_count=100
        )
        assert score == 0.0

    def test_uniqueness_empty_records(self, calculator):
        """Test uniqueness with no records."""
        score = calculator.calculate_uniqueness(
            record_count=0,
            duplicate_count=0
        )
        assert score == 0.0

    def test_uniqueness_negative_duplicates_capped(self, calculator):
        """Test that negative duplicates are treated as 0."""
        score = calculator.calculate_uniqueness(
            record_count=100,
            duplicate_count=-20
        )
        assert score == 100.0

    def test_uniqueness_excessive_duplicates_capped(self, calculator):
        """Test that duplicates exceeding records are capped."""
        score = calculator.calculate_uniqueness(
            record_count=100,
            duplicate_count=150
        )
        assert score == 0.0


class TestValidityCalculation:
    """Tests for validity score calculation."""

    @pytest.fixture
    def calculator(self):
        return DataQualityCalculator()

    def test_validity_perfect(self, calculator):
        """Test validity with no invalid records."""
        score = calculator.calculate_validity(
            record_count=1000,
            invalid_count=0
        )
        assert score == 100.0

    def test_validity_with_invalid(self, calculator):
        """Test validity with some invalid records."""
        # 100 invalid out of 1000 = 10% invalid = 90% validity
        score = calculator.calculate_validity(
            record_count=1000,
            invalid_count=100
        )
        assert score == 90.0

    def test_validity_empty_records(self, calculator):
        """Test validity with no records."""
        score = calculator.calculate_validity(
            record_count=0,
            invalid_count=0
        )
        assert score == 0.0

    def test_validity_with_rules(self, calculator):
        """Test validity with validation rules."""
        # Record validity: 1000 records, 100 invalid = 90%
        # Rule validity: 8 passed out of 10 = 80%
        # Combined: (90 + 80) / 2 = 85%
        score = calculator.calculate_validity(
            record_count=1000,
            invalid_count=100,
            validation_rules_passed=8,
            total_validation_rules=10
        )
        assert score == 85.0

    def test_validity_all_rules_passed(self, calculator):
        """Test validity when all rules pass."""
        score = calculator.calculate_validity(
            record_count=1000,
            invalid_count=0,
            validation_rules_passed=10,
            total_validation_rules=10
        )
        assert score == 100.0


class TestFreshnessCalculation:
    """Tests for freshness score calculation."""

    @pytest.fixture
    def calculator(self):
        return DataQualityCalculator(freshness_threshold_days=30)

    def test_freshness_just_updated(self, calculator):
        """Test freshness for data updated right now."""
        now = datetime.utcnow()
        score = calculator.calculate_freshness(
            last_updated=now,
            reference_time=now
        )
        assert score == 100.0

    def test_freshness_one_day_old(self, calculator):
        """Test freshness for 1-day old data."""
        now = datetime.utcnow()
        one_day_ago = now - timedelta(days=1)
        score = calculator.calculate_freshness(
            last_updated=one_day_ago,
            reference_time=now
        )
        # 1/30 days = 3.33% decay = 96.67% freshness
        assert 96 <= score <= 97

    def test_freshness_half_threshold(self, calculator):
        """Test freshness at half the threshold."""
        now = datetime.utcnow()
        fifteen_days_ago = now - timedelta(days=15)
        score = calculator.calculate_freshness(
            last_updated=fifteen_days_ago,
            reference_time=now
        )
        # 15/30 days = 50% decay = 50% freshness
        assert score == 50.0

    def test_freshness_at_threshold(self, calculator):
        """Test freshness at exactly the threshold."""
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        score = calculator.calculate_freshness(
            last_updated=thirty_days_ago,
            reference_time=now
        )
        assert score == 0.0

    def test_freshness_beyond_threshold(self, calculator):
        """Test freshness beyond the threshold."""
        now = datetime.utcnow()
        sixty_days_ago = now - timedelta(days=60)
        score = calculator.calculate_freshness(
            last_updated=sixty_days_ago,
            reference_time=now
        )
        assert score == 0.0

    def test_freshness_no_update(self, calculator):
        """Test freshness with no last_updated."""
        score = calculator.calculate_freshness(last_updated=None)
        assert score == 0.0

    def test_freshness_string_timestamp(self, calculator):
        """Test freshness with ISO string timestamp."""
        now = datetime.utcnow()
        score = calculator.calculate_freshness(
            last_updated=now.isoformat(),
            reference_time=now
        )
        assert score == 100.0

    def test_freshness_future_timestamp(self, calculator):
        """Test freshness with future timestamp."""
        now = datetime.utcnow()
        future = now + timedelta(days=5)
        score = calculator.calculate_freshness(
            last_updated=future,
            reference_time=now
        )
        assert score == 100.0

    def test_freshness_custom_threshold(self):
        """Test freshness with custom threshold."""
        calc = DataQualityCalculator(freshness_threshold_days=7)
        now = datetime.utcnow()
        three_days_ago = now - timedelta(days=3)

        score = calc.calculate_freshness(
            last_updated=three_days_ago,
            reference_time=now
        )
        # 3/7 days = 42.86% decay = 57.14% freshness
        assert 57 <= score <= 58


class TestOverallScoreCalculation:
    """Tests for overall score calculation."""

    @pytest.fixture
    def calculator(self):
        return DataQualityCalculator()

    def test_overall_perfect_scores(self, calculator):
        """Test overall with all perfect scores."""
        score = calculator.calculate_overall(
            completeness=100.0,
            consistency=100.0,
            uniqueness=100.0,
            validity=100.0,
            freshness=100.0
        )
        assert score == 100.0

    def test_overall_all_zero(self, calculator):
        """Test overall with all zero scores."""
        score = calculator.calculate_overall(
            completeness=0.0,
            consistency=0.0,
            uniqueness=0.0,
            validity=0.0,
            freshness=0.0
        )
        assert score == 0.0

    def test_overall_mixed_scores(self, calculator):
        """Test overall with mixed scores."""
        score = calculator.calculate_overall(
            completeness=100.0,
            consistency=80.0,
            uniqueness=90.0,
            validity=70.0,
            freshness=60.0
        )
        # With default weights (0.25, 0.20, 0.20, 0.20, 0.15)
        # = 100*0.25 + 80*0.20 + 90*0.20 + 70*0.20 + 60*0.15
        # = 25 + 16 + 18 + 14 + 9 = 82
        expected = (100*0.25 + 80*0.20 + 90*0.20 + 70*0.20 + 60*0.15)
        assert score == expected

    def test_overall_custom_weights(self, calculator):
        """Test overall with custom weights."""
        custom_weights = {
            'completeness': 0.4,  # Higher weight
            'consistency': 0.15,
            'uniqueness': 0.15,
            'validity': 0.15,
            'freshness': 0.15
        }
        score = calculator.calculate_overall(
            completeness=100.0,
            consistency=50.0,
            uniqueness=50.0,
            validity=50.0,
            freshness=50.0,
            weights=custom_weights
        )
        # 100*0.4 + 50*0.15 + 50*0.15 + 50*0.15 + 50*0.15 = 40 + 30 = 70
        assert score == 70.0

    def test_overall_zero_weights(self, calculator):
        """Test overall with zero total weight."""
        zero_weights = {
            'completeness': 0,
            'consistency': 0,
            'uniqueness': 0,
            'validity': 0,
            'freshness': 0
        }
        score = calculator.calculate_overall(
            completeness=100.0,
            consistency=100.0,
            uniqueness=100.0,
            validity=100.0,
            freshness=100.0,
            weights=zero_weights
        )
        assert score == 0.0


class TestDataProfileAssessment:
    """Tests for DataProfile-based assessment."""

    @pytest.fixture
    def calculator(self):
        return DataQualityCalculator()

    def test_assess_quality_basic(self, calculator):
        """Test basic quality assessment from profile."""
        profile = DataProfile(
            record_count=1000,
            feature_count=10,
            null_counts={'feature_0': 100, 'feature_1': 50},
            duplicate_count=50,
            outlier_count=30,
            last_updated=datetime.utcnow()
        )

        score = calculator.assess_quality(profile)

        assert isinstance(score, QualityScore)
        assert 0 <= score.overall <= 100
        assert 0 <= score.completeness <= 100
        assert 0 <= score.consistency <= 100
        assert 0 <= score.uniqueness <= 100
        assert 0 <= score.validity <= 100
        assert 0 <= score.freshness <= 100

    def test_assess_quality_includes_details(self, calculator):
        """Test that assessment includes details."""
        profile = DataProfile(
            record_count=1000,
            feature_count=10,
            null_counts={'feature_0': 100},
            duplicate_count=50,
            outlier_count=30,
            last_updated=datetime.utcnow()
        )

        score = calculator.assess_quality(profile)

        assert 'record_count' in score.details
        assert 'feature_count' in score.details
        assert 'null_ratio' in score.details
        assert 'duplicate_ratio' in score.details
        assert 'outlier_ratio' in score.details

    def test_assess_quality_with_violations(self, calculator):
        """Test assessment with schema violations."""
        profile = DataProfile(
            record_count=1000,
            feature_count=10,
            schema_violations=100,
            format_violations=50,
            range_violations=25,
            last_updated=datetime.utcnow()
        )

        score = calculator.assess_quality(profile)

        assert score.consistency < 100.0


class TestAssessFromMetadata:
    """Tests for assess_from_metadata convenience method."""

    @pytest.fixture
    def calculator(self):
        return DataQualityCalculator()

    def test_assess_from_metadata_basic(self, calculator):
        """Test basic metadata assessment."""
        result = calculator.assess_from_metadata(
            record_count=1000,
            feature_count=10,
            null_count=100,
            duplicate_count=50,
            outlier_count=30
        )

        assert 'id' in result
        assert result['id'].startswith('qa_')
        assert 'overall_score' in result
        assert 'completeness_score' in result
        assert 'consistency_score' in result
        assert 'uniqueness_score' in result
        assert 'validity_score' in result
        assert 'freshness_score' in result

    def test_assess_from_metadata_includes_counts(self, calculator):
        """Test that assessment includes record/feature counts."""
        result = calculator.assess_from_metadata(
            record_count=500,
            feature_count=15
        )

        assert result['record_count'] == 500
        assert result['feature_count'] == 15

    def test_assess_from_metadata_includes_timestamp(self, calculator):
        """Test that assessment includes timestamp."""
        result = calculator.assess_from_metadata(
            record_count=100,
            feature_count=5
        )

        assert 'assessed_at' in result
        assert isinstance(result['assessed_at'], datetime)

    def test_assess_from_metadata_with_custom_metadata(self, calculator):
        """Test assessment with additional metadata."""
        custom_meta = {'source': 'test', 'version': '1.0'}
        result = calculator.assess_from_metadata(
            record_count=100,
            feature_count=5,
            metadata=custom_meta
        )

        assert result['metadata'] == custom_meta


class TestCalculateQualityFromEncryptedMetadata:
    """Tests for FHE-encrypted metadata quality calculation."""

    def test_basic_encrypted_calculation(self):
        """Test basic quality calculation from encrypted stats."""
        stats = {
            'null_bitmap_count': 100,
            'duplicate_hash_collisions': 50,
            'range_check_failures': 30,
            'timestamp': datetime.utcnow()
        }

        result = calculate_quality_from_encrypted_metadata(
            encrypted_record_count=1000,
            encrypted_feature_count=10,
            stats_summary=stats
        )

        assert 'overall_score' in result
        assert result['metadata']['source'] == 'fhe_encrypted'

    def test_encrypted_calculation_empty_stats(self):
        """Test calculation with empty stats."""
        result = calculate_quality_from_encrypted_metadata(
            encrypted_record_count=1000,
            encrypted_feature_count=10,
            stats_summary={}
        )

        assert result['overall_score'] > 0
        assert result['completeness_score'] == 100.0


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def calculator(self):
        return DataQualityCalculator()

    def test_very_large_dataset(self, calculator):
        """Test with very large record counts."""
        score = calculator.calculate_completeness(
            record_count=10_000_000,
            feature_count=100,
            null_count=1_000_000
        )
        # 1M nulls out of 1B cells = 0.1% null = 99.9% completeness
        assert score == 99.9

    def test_single_record(self, calculator):
        """Test with single record."""
        score = calculator.calculate_completeness(
            record_count=1,
            feature_count=10,
            null_count=1
        )
        assert score == 90.0

    def test_single_feature(self, calculator):
        """Test with single feature."""
        score = calculator.calculate_uniqueness(
            record_count=100,
            duplicate_count=10
        )
        assert score == 90.0

    def test_score_rounding(self, calculator):
        """Test that scores are properly rounded."""
        score = calculator.calculate_completeness(
            record_count=3,
            feature_count=10,
            null_count=1
        )
        # 1/30 = 3.33...% null = 96.67% completeness
        assert score == 96.67


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
