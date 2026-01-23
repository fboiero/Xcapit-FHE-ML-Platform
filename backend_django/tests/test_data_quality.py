"""
Data quality module tests for Xcapit FHE-ML Platform.
"""

import pytest
from rest_framework import status

from apps.data_quality.models import QualityAlert, QualityAssessment, QualityRule


@pytest.fixture
def quality_assessment(db, company, consortium):
    """Create a test quality assessment."""
    return QualityAssessment.objects.create(
        consortium=consortium,
        company=company,
        record_count=1000,
        feature_count=10,
        null_count=50,
        duplicate_count=10,
        outlier_count=5,
        schema_violations=2,
        format_violations=3,
        range_violations=1,
        status=QualityAssessment.Status.PENDING,
    )


@pytest.fixture
def quality_rule(db, consortium):
    """Create a test quality rule."""
    return QualityRule.objects.create(
        consortium=consortium,
        name="Min Completeness Score",
        description="Completeness score must be at least 80%",
        rule_type=QualityRule.RuleType.THRESHOLD,
        metric="completeness_score",
        condition={"operator": ">=", "value": 80},
        severity=QualityRule.Severity.WARNING,
        is_active=True,
    )


@pytest.fixture
def quality_alert(db, quality_rule, quality_assessment, company):
    """Create a test quality alert."""
    return QualityAlert.objects.create(
        rule=quality_rule,
        assessment=quality_assessment,
        company=company,
        message="Completeness score below threshold",
        actual_value=75.5,
        expected_value=">=80",
        status=QualityAlert.Status.OPEN,
    )


@pytest.mark.django_db
class TestQualityAssessmentModel:
    """Tests for QualityAssessment model."""

    def test_create_assessment(self, quality_assessment):
        """Test creating a quality assessment."""
        assert quality_assessment.id is not None
        assert quality_assessment.record_count == 1000
        assert quality_assessment.status == QualityAssessment.Status.PENDING

    def test_calculate_scores(self, quality_assessment):
        """Test score calculation."""
        quality_assessment.calculate_scores()
        quality_assessment.refresh_from_db()

        assert quality_assessment.status == QualityAssessment.Status.COMPLETED
        assert quality_assessment.completeness_score > 0
        assert quality_assessment.consistency_score > 0
        assert quality_assessment.accuracy_score > 0
        assert quality_assessment.timeliness_score > 0
        assert quality_assessment.overall_score > 0
        assert quality_assessment.last_assessed_at is not None

    def test_completeness_calculation(self, company, consortium):
        """Test completeness score calculation."""
        assessment = QualityAssessment.objects.create(
            consortium=consortium,
            company=company,
            record_count=100,
            feature_count=10,
            null_count=0,  # No nulls = 100% complete
        )
        assessment.calculate_scores()

        assert assessment.completeness_score == 100.0

    def test_zero_records_handling(self, company, consortium):
        """Test handling of zero records."""
        assessment = QualityAssessment.objects.create(
            consortium=consortium,
            company=company,
            record_count=0,
            feature_count=0,
        )
        assessment.calculate_scores()

        assert assessment.completeness_score == 0
        assert assessment.overall_score == 0


@pytest.mark.django_db
class TestQualityRuleModel:
    """Tests for QualityRule model."""

    def test_create_rule(self, quality_rule):
        """Test creating a quality rule."""
        assert quality_rule.id is not None
        assert quality_rule.name == "Min Completeness Score"
        assert quality_rule.is_active is True

    def test_rule_condition_json(self, quality_rule):
        """Test rule condition is stored as JSON."""
        assert quality_rule.condition == {"operator": ">=", "value": 80}


@pytest.mark.django_db
class TestQualityAlertModel:
    """Tests for QualityAlert model."""

    def test_create_alert(self, quality_alert):
        """Test creating a quality alert."""
        assert quality_alert.id is not None
        assert quality_alert.status == QualityAlert.Status.OPEN

    def test_resolve_alert(self, quality_alert, user):
        """Test resolving an alert."""
        quality_alert.resolve(user, "Issue addressed by data cleanup")
        quality_alert.refresh_from_db()

        assert quality_alert.status == QualityAlert.Status.RESOLVED
        assert quality_alert.resolved_by == user
        assert quality_alert.resolution_note == "Issue addressed by data cleanup"
        assert quality_alert.resolved_at is not None


@pytest.mark.django_db
class TestQualityAssessmentEndpoints:
    """Tests for quality assessment API endpoints."""

    def test_list_assessments(self, auth_client, quality_assessment):
        """Test listing quality assessments."""
        url = "/api/v2/data-quality/assessments/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_assessment(self, auth_client, consortium):
        """Test creating a quality assessment."""
        url = "/api/v2/data-quality/assessments/"
        data = {
            "consortium": str(consortium.id),
            "record_count": 500,
            "feature_count": 8,
            "null_count": 20,
            "duplicate_count": 5,
            "outlier_count": 3,
            "schema_violations": 1,
            "format_violations": 2,
            "range_violations": 0,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["overall_score"] > 0

    def test_get_assessment_summary(self, auth_client, quality_assessment):
        """Test getting assessment summary."""
        # First calculate scores
        quality_assessment.calculate_scores()

        url = "/api/v2/data-quality/assessments/summary/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "avg_overall" in response.data

    def test_recalculate_assessment(self, auth_client, quality_assessment):
        """Test recalculating assessment scores."""
        url = f"/api/v2/data-quality/assessments/{quality_assessment.id}/recalculate/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "completed"


@pytest.mark.django_db
class TestQualityAlertEndpoints:
    """Tests for quality alert API endpoints."""

    def test_list_alerts(self, auth_client, quality_alert):
        """Test listing quality alerts."""
        url = "/api/v2/data-quality/alerts/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_acknowledge_alert(self, auth_client, quality_alert):
        """Test acknowledging an alert."""
        url = f"/api/v2/data-quality/alerts/{quality_alert.id}/acknowledge/"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "acknowledged"

    def test_resolve_alert(self, auth_client, quality_alert):
        """Test resolving an alert."""
        url = f"/api/v2/data-quality/alerts/{quality_alert.id}/resolve/"
        data = {"note": "Fixed the data issue"}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "resolved"

    def test_get_open_alerts_count(self, auth_client, quality_alert):
        """Test getting open alerts count."""
        url = "/api/v2/data-quality/alerts/open_count/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "open_alerts" in response.data
        assert response.data["open_alerts"] >= 1


@pytest.mark.django_db
class TestDataIsolation:
    """Tests for data isolation between companies."""

    def test_cannot_see_other_company_assessments(
        self, auth_client, other_company, consortium
    ):
        """Test user cannot see another company's assessments."""
        # Create assessment for other company
        QualityAssessment.objects.create(
            consortium=consortium,
            company=other_company,
            record_count=100,
            feature_count=5,
        )

        url = "/api/v2/data-quality/assessments/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for assessment in response.data:
            assert assessment.get("company") != str(other_company.id)
