"""
Tests for the 3 resolved TODOs:
1. Async report generation (Celery)
2. Timeliness calculation
3. Proposal execution dispatcher
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from django.utils import timezone


class TestAsyncReportGeneration:
    """Tests for TODO 1: Async competitive report generation."""

    def test_task_exists(self):
        """Test that generate_competitive_report task exists."""
        from apps.competitive_insights.tasks import generate_competitive_report

        assert callable(generate_competitive_report)
        # Verify it's a Celery task
        assert hasattr(generate_competitive_report, "delay")

    def test_cleanup_task_exists(self):
        """Test that cleanup_old_reports task exists."""
        from apps.competitive_insights.tasks import cleanup_old_reports

        assert callable(cleanup_old_reports)
        assert hasattr(cleanup_old_reports, "delay")

    def test_views_trigger_async(self):
        """Test that views use async task."""
        from apps.competitive_insights.views import CompetitiveReportViewSet

        # Check that perform_create imports the task
        import inspect
        source = inspect.getsource(CompetitiveReportViewSet.perform_create)
        assert "generate_competitive_report" in source
        assert ".delay(" in source


class TestTimelinessCalculation:
    """Tests for TODO 2: Timeliness calculation."""

    @pytest.fixture
    def assessment_service(self):
        """Create assessment service."""
        from apps.data_quality.services.assessment import QualityAssessmentService

        return QualityAssessmentService()

    def test_fresh_data_score(self, assessment_service):
        """Test that fresh data (< 1 day) gets score of 100."""
        assessment = MagicMock()
        assessment.contribution = MagicMock()
        assessment.contribution.created_at = timezone.now() - timedelta(hours=12)
        assessment.created_at = timezone.now()

        score = assessment_service._calculate_timeliness(assessment)
        assert score == 100.0

    def test_one_week_old_data(self, assessment_service):
        """Test data 1-7 days old gets score 90-99."""
        assessment = MagicMock()
        assessment.contribution = MagicMock()
        assessment.contribution.created_at = timezone.now() - timedelta(days=3)
        assessment.created_at = timezone.now()

        score = assessment_service._calculate_timeliness(assessment)
        assert 90 <= score < 100

    def test_month_old_data(self, assessment_service):
        """Test data 7-30 days old gets score 70-89."""
        assessment = MagicMock()
        assessment.contribution = MagicMock()
        assessment.contribution.created_at = timezone.now() - timedelta(days=15)
        assessment.created_at = timezone.now()

        score = assessment_service._calculate_timeliness(assessment)
        assert 70 <= score < 90

    def test_old_data(self, assessment_service):
        """Test data 30-90 days old gets score 50-69."""
        assessment = MagicMock()
        assessment.contribution = MagicMock()
        assessment.contribution.created_at = timezone.now() - timedelta(days=60)
        assessment.created_at = timezone.now()

        score = assessment_service._calculate_timeliness(assessment)
        assert 50 <= score < 70

    def test_very_old_data(self, assessment_service):
        """Test data 90+ days old gets score 0-49."""
        assessment = MagicMock()
        assessment.contribution = MagicMock()
        assessment.contribution.created_at = timezone.now() - timedelta(days=120)
        assessment.created_at = timezone.now()

        score = assessment_service._calculate_timeliness(assessment)
        assert 0 <= score < 50

    def test_ancient_data_zero_score(self, assessment_service):
        """Test very old data gets minimum score of 0."""
        assessment = MagicMock()
        assessment.contribution = MagicMock()
        assessment.contribution.created_at = timezone.now() - timedelta(days=365)
        assessment.created_at = timezone.now()

        score = assessment_service._calculate_timeliness(assessment)
        assert score == 0.0

    def test_no_contribution_uses_assessment_time(self, assessment_service):
        """Test fallback to assessment creation time when no contribution."""
        assessment = MagicMock()
        assessment.contribution = None
        assessment.created_at = timezone.now() - timedelta(hours=6)

        score = assessment_service._calculate_timeliness(assessment)
        assert score == 100.0

    def test_no_more_todo_in_timeliness(self, assessment_service):
        """Verify TODO comment is removed from timeliness calculation."""
        import inspect

        source = inspect.getsource(assessment_service._calculate_timeliness)
        assert "TODO" not in source


class TestProposalExecutionDispatcher:
    """Tests for TODO 3: Proposal execution dispatcher."""

    @pytest.fixture
    def execution_service(self):
        """Create execution service."""
        from apps.governance.services import ProposalExecutionService

        return ProposalExecutionService()

    def test_service_exists(self):
        """Test ProposalExecutionService exists."""
        from apps.governance.services import ProposalExecutionService

        service = ProposalExecutionService()
        assert service is not None

    def test_execution_result_dataclass(self):
        """Test ExecutionResult dataclass exists."""
        from apps.governance.services import ExecutionResult

        result = ExecutionResult(success=True, message="Test")
        assert result.success
        assert result.message == "Test"

    def test_all_handlers_exist(self, execution_service):
        """Test handlers exist for all proposal types."""
        from apps.governance.models import Proposal

        for proposal_type in Proposal.Type.values:
            handler = execution_service._get_handler(proposal_type)
            assert handler is not None, f"Missing handler for {proposal_type}"

    def test_invalid_status_fails(self, execution_service):
        """Test execution fails for non-PASSED proposals."""
        from apps.governance.models import Proposal

        proposal = MagicMock()
        proposal.status = Proposal.Status.ACTIVE

        result = execution_service.execute(proposal)

        assert not result.success
        assert "PASSED" in result.error

    def test_unknown_handler_fails(self, execution_service):
        """Test unknown proposal type returns None handler."""
        handler = execution_service._get_handler("unknown_type")
        assert handler is None

    def test_views_use_execution_service(self):
        """Test that views use ProposalExecutionService."""
        from apps.governance.views import ProposalViewSet

        import inspect
        source = inspect.getsource(ProposalViewSet.execute)
        assert "ProposalExecutionService" in source
        assert "execution_service.execute" in source

    def test_no_todo_in_views(self):
        """Verify TODO comment is removed from governance views execute."""
        from apps.governance.views import ProposalViewSet

        import inspect
        source = inspect.getsource(ProposalViewSet.execute)
        assert "TODO" not in source


class TestCeleryConfiguration:
    """Test Celery configuration."""

    def test_celery_app_exists(self):
        """Test Celery app is properly configured."""
        from config.celery import app

        assert app is not None
        assert app.main == "xcapit_fheml"

    def test_celery_in_settings(self):
        """Test Celery settings are defined."""
        from django.conf import settings

        assert hasattr(settings, "CELERY_BROKER_URL")
        assert hasattr(settings, "CELERY_RESULT_BACKEND")
        assert hasattr(settings, "CELERY_TASK_ROUTES")

    def test_task_routes_defined(self):
        """Test task routes are properly defined."""
        from django.conf import settings

        routes = settings.CELERY_TASK_ROUTES
        assert "apps.competitive_insights.tasks.*" in routes
        assert "apps.governance.tasks.*" in routes
