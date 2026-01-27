"""
Scheduled tasks module tests for Xcapit FHE-ML Platform.
"""

import pytest
from django.utils import timezone
from rest_framework import status

from apps.core.models import ScheduledTask, ScheduledTaskRun, Workflow, Report


@pytest.fixture
def scheduled_task(db, company, user):
    """Create a test scheduled task."""
    return ScheduledTask.objects.create(
        company=company,
        created_by=user,
        name="Daily Report Generation",
        description="Generate daily performance report",
        task_type=ScheduledTask.TaskType.CUSTOM,
        cron_expression="0 0 * * *",  # Every day at midnight
        timezone="UTC",
        config={"report_type": "performance"},
        status=ScheduledTask.Status.ACTIVE,
    )


@pytest.fixture
def scheduled_task_run(db, scheduled_task):
    """Create a test scheduled task run."""
    return ScheduledTaskRun.objects.create(
        task=scheduled_task,
        scheduled_at=timezone.now(),
        status=ScheduledTaskRun.Status.PENDING,
    )


@pytest.mark.django_db
class TestScheduledTaskModel:
    """Tests for ScheduledTask model."""

    def test_create_scheduled_task(self, scheduled_task):
        """Test creating a scheduled task."""
        assert scheduled_task.id is not None
        assert scheduled_task.name == "Daily Report Generation"
        assert scheduled_task.cron_expression == "0 0 * * *"
        assert scheduled_task.status == ScheduledTask.Status.ACTIVE

    def test_task_types(self, company, user):
        """Test different task types."""
        task_types = [
            ScheduledTask.TaskType.REPORT,
            ScheduledTask.TaskType.WORKFLOW,
            ScheduledTask.TaskType.DATA_SYNC,
            ScheduledTask.TaskType.CLEANUP,
            ScheduledTask.TaskType.BACKUP,
            ScheduledTask.TaskType.CUSTOM,
        ]

        for task_type in task_types:
            task = ScheduledTask.objects.create(
                company=company,
                created_by=user,
                name=f"Test {task_type} Task",
                task_type=task_type,
                cron_expression="0 * * * *",
            )
            assert task.task_type == task_type

    def test_task_statuses(self, company, user):
        """Test different task statuses."""
        statuses = [
            ScheduledTask.Status.ACTIVE,
            ScheduledTask.Status.PAUSED,
            ScheduledTask.Status.DISABLED,
        ]

        for task_status in statuses:
            task = ScheduledTask.objects.create(
                company=company,
                created_by=user,
                name=f"Test {task_status} Task",
                task_type=ScheduledTask.TaskType.CUSTOM,
                cron_expression="0 * * * *",
                status=task_status,
            )
            assert task.status == task_status

    def test_update_stats_success(self, scheduled_task):
        """Test updating stats on successful run."""
        initial_total = scheduled_task.total_runs

        scheduled_task.update_stats(success=True)

        assert scheduled_task.total_runs == initial_total + 1
        assert scheduled_task.successful_runs == 1
        assert scheduled_task.consecutive_failures == 0

    def test_update_stats_failure(self, scheduled_task):
        """Test updating stats on failed run."""
        initial_total = scheduled_task.total_runs

        scheduled_task.update_stats(success=False)

        assert scheduled_task.total_runs == initial_total + 1
        assert scheduled_task.failed_runs == 1
        assert scheduled_task.consecutive_failures == 1

    def test_auto_disable_on_consecutive_failures(self, scheduled_task):
        """Test auto-disabling after consecutive failures."""
        scheduled_task.max_consecutive_failures = 3
        scheduled_task.save(update_fields=["max_consecutive_failures"])

        for _ in range(3):
            scheduled_task.update_stats(success=False)

        assert scheduled_task.status == ScheduledTask.Status.DISABLED

    def test_consecutive_failures_reset_on_success(self, scheduled_task):
        """Test that consecutive failures reset on success."""
        scheduled_task.consecutive_failures = 2
        scheduled_task.save()

        scheduled_task.update_stats(success=True)

        assert scheduled_task.consecutive_failures == 0


@pytest.mark.django_db
class TestScheduledTaskRunModel:
    """Tests for ScheduledTaskRun model."""

    def test_create_task_run(self, scheduled_task_run):
        """Test creating a scheduled task run."""
        assert scheduled_task_run.id is not None
        assert scheduled_task_run.status == ScheduledTaskRun.Status.PENDING
        assert scheduled_task_run.scheduled_at is not None

    def test_start_run(self, scheduled_task_run):
        """Test starting a task run."""
        scheduled_task_run.start()

        assert scheduled_task_run.status == ScheduledTaskRun.Status.RUNNING
        assert scheduled_task_run.started_at is not None

    def test_complete_run(self, scheduled_task_run):
        """Test completing a task run."""
        scheduled_task_run.start()
        scheduled_task_run.complete(output={"records_processed": 100})

        assert scheduled_task_run.status == ScheduledTaskRun.Status.COMPLETED
        assert scheduled_task_run.completed_at is not None
        assert scheduled_task_run.output == {"records_processed": 100}
        assert scheduled_task_run.duration_seconds is not None

    def test_fail_run(self, scheduled_task_run):
        """Test failing a task run."""
        scheduled_task_run.start()
        scheduled_task_run.fail("Connection timeout")

        assert scheduled_task_run.status == ScheduledTaskRun.Status.FAILED
        assert scheduled_task_run.completed_at is not None
        assert "timeout" in scheduled_task_run.error_message


@pytest.mark.django_db
class TestScheduledTaskAPI:
    """Tests for ScheduledTask API endpoints."""

    def test_list_scheduled_tasks(self, auth_client, scheduled_task):
        """Test listing scheduled tasks."""
        response = auth_client.get("/api/v2/scheduled-tasks/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_create_scheduled_task(self, auth_client, company):
        """Test creating a scheduled task."""
        data = {
            "name": "New Test Task",
            "description": "Test task description",
            "task_type": "custom",
            "cron_expression": "0 */6 * * *",  # Every 6 hours
            "timezone": "America/New_York",
            "config": {"key": "value"},
            "status": "active",
        }
        response = auth_client.post(
            "/api/v2/scheduled-tasks/", data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Test Task"
        assert response.data["cron_expression"] == "0 */6 * * *"

    def test_retrieve_scheduled_task(self, auth_client, scheduled_task):
        """Test retrieving a single scheduled task."""
        response = auth_client.get(
            f"/api/v2/scheduled-tasks/{scheduled_task.id}/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(scheduled_task.id)
        assert response.data["name"] == scheduled_task.name

    def test_run_task_now(self, auth_client, scheduled_task):
        """Test manually triggering a scheduled task."""
        response = auth_client.post(
            f"/api/v2/scheduled-tasks/{scheduled_task.id}/run_now/"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "completed"

    def test_run_inactive_task_fails(self, auth_client, scheduled_task):
        """Test that running an inactive task fails."""
        scheduled_task.status = ScheduledTask.Status.PAUSED
        scheduled_task.save()

        response = auth_client.post(
            f"/api/v2/scheduled-tasks/{scheduled_task.id}/run_now/"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_pause_task(self, auth_client, scheduled_task):
        """Test pausing a scheduled task."""
        response = auth_client.post(
            f"/api/v2/scheduled-tasks/{scheduled_task.id}/pause/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "paused"

    def test_resume_task(self, auth_client, scheduled_task):
        """Test resuming a paused task."""
        scheduled_task.status = ScheduledTask.Status.PAUSED
        scheduled_task.save()

        response = auth_client.post(
            f"/api/v2/scheduled-tasks/{scheduled_task.id}/resume/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "active"

    def test_filter_tasks_by_type(self, auth_client, scheduled_task):
        """Test filtering tasks by type."""
        response = auth_client.get("/api/v2/scheduled-tasks/?type=custom")

        assert response.status_code == status.HTTP_200_OK

    def test_filter_tasks_by_status(self, auth_client, scheduled_task):
        """Test filtering tasks by status."""
        response = auth_client.get("/api/v2/scheduled-tasks/?status=active")

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestScheduledTaskRunAPI:
    """Tests for ScheduledTaskRun API endpoints."""

    def test_list_task_runs(self, auth_client, scheduled_task_run):
        """Test listing task runs."""
        response = auth_client.get("/api/v2/scheduled-task-runs/")

        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_task_run(self, auth_client, scheduled_task_run):
        """Test retrieving a single task run."""
        response = auth_client.get(
            f"/api/v2/scheduled-task-runs/{scheduled_task_run.id}/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(scheduled_task_run.id)

    def test_filter_runs_by_task(
        self, auth_client, scheduled_task, scheduled_task_run
    ):
        """Test filtering runs by task."""
        response = auth_client.get(
            f"/api/v2/scheduled-task-runs/?task_id={scheduled_task.id}"
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestScheduledTaskValidation:
    """Tests for scheduled task validation."""

    def test_invalid_task_type(self, auth_client):
        """Test that invalid task type is rejected."""
        data = {
            "name": "Test Task",
            "task_type": "invalid_type",
            "cron_expression": "0 0 * * *",
        }
        response = auth_client.post(
            "/api/v2/scheduled-tasks/", data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_cron_expression(self, auth_client):
        """Test that invalid cron expression is rejected."""
        data = {
            "name": "Test Task",
            "task_type": "custom",
            "cron_expression": "invalid cron",
        }
        response = auth_client.post(
            "/api/v2/scheduled-tasks/", data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_report_task_requires_report(self, auth_client):
        """Test that report task type requires report reference."""
        data = {
            "name": "Test Task",
            "task_type": "report",
            "cron_expression": "0 0 * * *",
            # Missing 'report' field
        }
        response = auth_client.post(
            "/api/v2/scheduled-tasks/", data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_workflow_task_requires_workflow(self, auth_client):
        """Test that workflow task type requires workflow reference."""
        data = {
            "name": "Test Task",
            "task_type": "workflow",
            "cron_expression": "0 0 * * *",
            # Missing 'workflow' field
        }
        response = auth_client.post(
            "/api/v2/scheduled-tasks/", data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestScheduledTaskWithRelatedObjects:
    """Tests for scheduled tasks with related workflow/report."""

    def test_task_with_workflow(self, auth_client, company, user):
        """Test creating a task linked to a workflow."""
        # Create workflow first
        workflow = Workflow.objects.create(
            company=company,
            created_by=user,
            name="Test Workflow",
            steps=[],
            trigger={"type": "manual"},
            status=Workflow.Status.ACTIVE,
        )

        data = {
            "name": "Workflow Task",
            "task_type": "workflow",
            "cron_expression": "0 0 * * *",
            "workflow": str(workflow.id),
        }
        response = auth_client.post(
            "/api/v2/scheduled-tasks/", data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data["workflow"]) == str(workflow.id)

    def test_task_with_report(self, auth_client, company, user):
        """Test creating a task linked to a report."""
        # Create report first
        report = Report.objects.create(
            company=company,
            created_by=user,
            name="Test Report",
            report_type=Report.ReportType.PERFORMANCE,
            format=Report.Format.PDF,
        )

        data = {
            "name": "Report Task",
            "task_type": "report",
            "cron_expression": "0 0 * * *",
            "report": str(report.id),
        }
        response = auth_client.post(
            "/api/v2/scheduled-tasks/", data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data["report"]) == str(report.id)
