"""
Tests for QualityAssessmentService.

Targets coverage gaps in:
- apps/data_quality/services/assessment.py (37% -> ~85%)
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.consortiums.models import Consortium, ContributionProof
from apps.core.models import Company
from apps.core.services.base import ServiceContext
from apps.data_quality.models import QualityAlert, QualityAssessment, QualityRule
from apps.data_quality.services.assessment import QualityAssessmentService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def assessment(db, consortium, company):
    return QualityAssessment.objects.create(
        consortium=consortium,
        company=company,
        record_count=1000,
        feature_count=20,
        null_count=100,
        duplicate_count=50,
        outlier_count=30,
        schema_violations=10,
        format_violations=20,
        range_violations=15,
        status=QualityAssessment.Status.PENDING,
    )


@pytest.fixture
def zero_assessment(db, consortium, company):
    """Assessment with zero records."""
    return QualityAssessment.objects.create(
        consortium=consortium,
        company=company,
        record_count=0,
        feature_count=0,
        null_count=0,
        duplicate_count=0,
        outlier_count=0,
        schema_violations=0,
        format_violations=0,
        range_violations=0,
        status=QualityAssessment.Status.PENDING,
    )


@pytest.fixture
def perfect_assessment(db, consortium, company):
    """Assessment with perfect data quality."""
    return QualityAssessment.objects.create(
        consortium=consortium,
        company=company,
        record_count=1000,
        feature_count=10,
        null_count=0,
        duplicate_count=0,
        outlier_count=0,
        schema_violations=0,
        format_violations=0,
        range_violations=0,
        status=QualityAssessment.Status.PENDING,
    )


@pytest.fixture
def svc():
    return QualityAssessmentService()


@pytest.fixture
def company_svc(db, user, company):
    """Service with company context for dashboard tests."""
    ctx = ServiceContext(user=user, company=company)
    return QualityAssessmentService(context=ctx)


# ===========================================================================
# Score calculation
# ===========================================================================


@pytest.mark.django_db
class TestCalculateScores:
    def test_calculate_scores_happy_path(self, svc, assessment):
        result = svc.calculate_scores(assessment)
        assert result.success
        scores = result.data
        assert 0 <= scores.completeness <= 100
        assert 0 <= scores.consistency <= 100
        assert 0 <= scores.accuracy <= 100
        assert 0 <= scores.timeliness <= 100
        assert 0 <= scores.overall <= 100

    def test_calculate_scores_custom_weights(self, svc, assessment):
        weights = {
            "completeness": 0.50,
            "consistency": 0.20,
            "accuracy": 0.20,
            "timeliness": 0.10,
        }
        result = svc.calculate_scores(assessment, weights=weights)
        assert result.success
        # Overall should differ from default weights
        scores = result.data
        assert scores.overall > 0

    def test_calculate_scores_zero_records(self, svc, zero_assessment):
        result = svc.calculate_scores(zero_assessment)
        assert result.success
        scores = result.data
        assert scores.completeness == 0.0
        assert scores.consistency == 0.0
        assert scores.accuracy == 0.0

    def test_calculate_scores_perfect_data(self, svc, perfect_assessment):
        result = svc.calculate_scores(perfect_assessment)
        assert result.success
        scores = result.data
        assert scores.completeness == 100.0
        assert scores.consistency == 100.0
        assert scores.accuracy == 100.0


# ===========================================================================
# Individual score calculators
# ===========================================================================


@pytest.mark.django_db
class TestCompleteness:
    def test_no_nulls(self, svc, perfect_assessment):
        score = svc._calculate_completeness(perfect_assessment)
        assert score == 100.0

    def test_some_nulls(self, svc, assessment):
        # 100 nulls / (1000 records * 20 features) = 0.005 null ratio
        score = svc._calculate_completeness(assessment)
        expected = (1 - 100 / 20000) * 100
        assert score == pytest.approx(expected)

    def test_zero_cells(self, svc, zero_assessment):
        score = svc._calculate_completeness(zero_assessment)
        assert score == 0.0


@pytest.mark.django_db
class TestConsistency:
    def test_no_issues(self, svc, perfect_assessment):
        score = svc._calculate_consistency(perfect_assessment)
        assert score == 100.0

    def test_with_issues(self, svc, assessment):
        # dup ratio = 50/1000 = 0.05, format ratio = 20/1000 = 0.02
        # consistency = 1 - (0.05 + 0.02) / 2 = 0.965
        score = svc._calculate_consistency(assessment)
        expected = (1 - (0.05 + 0.02) / 2) * 100
        assert score == pytest.approx(expected)

    def test_zero_records(self, svc, zero_assessment):
        score = svc._calculate_consistency(zero_assessment)
        assert score == 0.0


@pytest.mark.django_db
class TestAccuracy:
    def test_no_violations(self, svc, perfect_assessment):
        score = svc._calculate_accuracy(perfect_assessment)
        assert score == 100.0

    def test_with_violations(self, svc, assessment):
        # violations = 30 + 10 + 15 = 55, ratio = 55/1000 = 0.055
        score = svc._calculate_accuracy(assessment)
        expected = (1 - 55 / 1000) * 100
        assert score == pytest.approx(expected)

    def test_zero_records(self, svc, zero_assessment):
        score = svc._calculate_accuracy(zero_assessment)
        assert score == 0.0


@pytest.mark.django_db
class TestTimeliness:
    def test_fresh_data(self, svc, assessment):
        """Assessment created moments ago should score 100."""
        score = svc._calculate_timeliness(assessment)
        assert score == 100.0

    def test_one_week_old(self, svc, consortium, company):
        contribution = ContributionProof.objects.create(
            consortium=consortium,
            company=company,
            record_count=100,
            feature_count=10,
            data_hash="a" * 64,
            checksum="b" * 64,
        )
        # Override created_at (auto_now_add doesn't allow direct set)
        ContributionProof.objects.filter(id=contribution.id).update(
            created_at=timezone.now() - timedelta(days=7)
        )
        contribution.refresh_from_db()
        qa = QualityAssessment.objects.create(
            consortium=consortium,
            company=company,
            contribution=contribution,
            record_count=100,
            feature_count=10,
        )
        score = svc._calculate_timeliness(qa)
        # 7 days: score should be ~90
        assert 88 <= score <= 92

    def test_one_month_old(self, svc, consortium, company):
        contribution = ContributionProof.objects.create(
            consortium=consortium,
            company=company,
            record_count=100,
            feature_count=10,
            data_hash="c" * 64,
            checksum="d" * 64,
        )
        ContributionProof.objects.filter(id=contribution.id).update(
            created_at=timezone.now() - timedelta(days=30)
        )
        contribution.refresh_from_db()
        qa = QualityAssessment.objects.create(
            consortium=consortium,
            company=company,
            contribution=contribution,
            record_count=100,
            feature_count=10,
        )
        score = svc._calculate_timeliness(qa)
        assert 68 <= score <= 72

    def test_very_old_data(self, svc, consortium, company):
        contribution = ContributionProof.objects.create(
            consortium=consortium,
            company=company,
            record_count=100,
            feature_count=10,
            data_hash="e" * 64,
            checksum="f" * 64,
        )
        ContributionProof.objects.filter(id=contribution.id).update(
            created_at=timezone.now() - timedelta(days=200)
        )
        contribution.refresh_from_db()
        qa = QualityAssessment.objects.create(
            consortium=consortium,
            company=company,
            contribution=contribution,
            record_count=100,
            feature_count=10,
        )
        score = svc._calculate_timeliness(qa)
        assert score == 0.0

    def test_no_contribution(self, svc, assessment):
        """When no contribution linked, uses assessment creation time."""
        score = svc._calculate_timeliness(assessment)
        assert score == 100.0  # Just created


# ===========================================================================
# Run assessment
# ===========================================================================


@pytest.mark.django_db
class TestRunAssessment:
    def test_run_assessment_success(self, svc, assessment):
        result = svc.run_assessment(assessment)
        assert result.success
        assessment.refresh_from_db()
        assert assessment.status == QualityAssessment.Status.COMPLETED
        assert assessment.overall_score > 0
        assert assessment.last_assessed_at is not None

    def test_run_assessment_updates_all_scores(self, svc, perfect_assessment):
        result = svc.run_assessment(perfect_assessment)
        assert result.success
        perfect_assessment.refresh_from_db()
        assert perfect_assessment.completeness_score == 100.0
        assert perfect_assessment.consistency_score == 100.0
        assert perfect_assessment.accuracy_score == 100.0


# ===========================================================================
# Quality rules
# ===========================================================================


@pytest.mark.django_db
class TestCheckQualityRules:
    def test_rule_gte_violated(self, svc, consortium, company, assessment):
        """Rule: completeness_score >= 99. Assessment has ~99.5 completeness."""
        # First run assessment to populate scores
        svc.run_assessment(assessment)
        assessment.refresh_from_db()

        rule = QualityRule.objects.create(
            consortium=consortium,
            name="High completeness",
            metric="completeness_score",
            condition={"operator": ">=", "value": 99.9},
            is_active=True,
        )
        # Re-check rules manually
        svc._check_quality_rules(assessment)
        alerts = QualityAlert.objects.filter(rule=rule, assessment=assessment)
        assert alerts.count() == 1

    def test_rule_lte_violated(self, svc, consortium, company, assessment):
        svc.run_assessment(assessment)
        assessment.refresh_from_db()

        rule = QualityRule.objects.create(
            consortium=consortium,
            name="Max outliers",
            metric="accuracy_score",
            condition={"operator": "<=", "value": 50},
            is_active=True,
        )
        svc._check_quality_rules(assessment)
        alerts = QualityAlert.objects.filter(rule=rule, assessment=assessment)
        # accuracy_score for our assessment is ~94.5, which is > 50, so violated
        assert alerts.count() == 1

    def test_rule_gt_violated(self, svc, consortium, company, assessment):
        svc.run_assessment(assessment)
        assessment.refresh_from_db()

        rule = QualityRule.objects.create(
            consortium=consortium,
            name="Score above threshold",
            metric="overall_score",
            condition={"operator": ">", "value": 99},
            is_active=True,
        )
        svc._check_quality_rules(assessment)
        alerts = QualityAlert.objects.filter(rule=rule, assessment=assessment)
        assert alerts.count() == 1

    def test_rule_lt_violated(self, svc, consortium, company, assessment):
        svc.run_assessment(assessment)
        assessment.refresh_from_db()

        rule = QualityRule.objects.create(
            consortium=consortium,
            name="Score below max",
            metric="consistency_score",
            condition={"operator": "<", "value": 50},
            is_active=True,
        )
        svc._check_quality_rules(assessment)
        alerts = QualityAlert.objects.filter(rule=rule, assessment=assessment)
        # consistency_score ~96.5 which is >= 50, so violated
        assert alerts.count() == 1

    def test_rule_eq_violated(self, svc, consortium, company, assessment):
        svc.run_assessment(assessment)
        assessment.refresh_from_db()

        rule = QualityRule.objects.create(
            consortium=consortium,
            name="Exact score",
            metric="completeness_score",
            condition={"operator": "==", "value": 0},
            is_active=True,
        )
        svc._check_quality_rules(assessment)
        alerts = QualityAlert.objects.filter(rule=rule, assessment=assessment)
        # completeness is not 0, so violated (!=)
        assert alerts.count() == 1

    def test_inactive_rule_skipped(self, svc, consortium, company, assessment):
        svc.run_assessment(assessment)
        assessment.refresh_from_db()

        QualityRule.objects.create(
            consortium=consortium,
            name="Inactive rule",
            metric="completeness_score",
            condition={"operator": ">=", "value": 200},
            is_active=False,
        )
        svc._check_quality_rules(assessment)
        assert QualityAlert.objects.count() == 0

    def test_unknown_metric_skipped(self, svc, consortium, company, assessment):
        svc.run_assessment(assessment)
        assessment.refresh_from_db()

        QualityRule.objects.create(
            consortium=consortium,
            name="Unknown metric",
            metric="nonexistent_field",
            condition={"operator": ">=", "value": 50},
            is_active=True,
        )
        svc._check_quality_rules(assessment)
        assert QualityAlert.objects.count() == 0


# ===========================================================================
# Dashboard
# ===========================================================================


@pytest.mark.django_db
class TestGetDashboard:
    def test_dashboard_with_data(self, company_svc, consortium, company):
        # Create completed assessments with different scores
        for score in [95, 80, 60, 40]:
            QualityAssessment.objects.create(
                consortium=consortium,
                company=company,
                record_count=100,
                feature_count=10,
                overall_score=score,
                status=QualityAssessment.Status.COMPLETED,
            )

        result = company_svc.get_dashboard()
        assert result.success
        dashboard = result.data
        assert dashboard.total_assessments == 4
        assert dashboard.average_score > 0
        assert dashboard.score_distribution["excellent"] == 1  # >=90
        assert dashboard.score_distribution["good"] == 1  # 70-89
        assert dashboard.score_distribution["fair"] == 1  # 50-69
        assert dashboard.score_distribution["poor"] == 1  # <50
        assert len(dashboard.recent_assessments) == 4

    def test_dashboard_empty(self, company_svc):
        result = company_svc.get_dashboard()
        assert result.success
        dashboard = result.data
        assert dashboard.total_assessments == 0
        assert dashboard.average_score == 0

    def test_dashboard_no_company_raises(self):
        svc = QualityAssessmentService()
        with pytest.raises(PermissionError):
            svc.get_dashboard()
