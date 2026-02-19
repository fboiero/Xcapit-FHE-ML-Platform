"""
Workflows module tests for Xcapit FHE-ML Platform.
"""

import pytest
from django.utils import timezone
from rest_framework import status

from apps.core.models import Workflow, WorkflowRun


@pytest.fixture
def workflow(db, company, user):
    """Create a test workflow."""
    return Workflow.objects.create(
        company=company,
        created_by=user,
        name="Data Processing Pipeline",
        description="Process and validate incoming data",
        steps=[
            {"type": "data_fetch", "name": "Fetch Data", "config": {"source": "api"}},
            {"type": "validate", "name": "Validate", "config": {"schema": "standard"}},
            {"type": "transform", "name": "Transform", "config": {"normalize": True}},
        ],
        trigger={"type": "manual"},
        status=Workflow.Status.ACTIVE,
    )


@pytest.fixture
def workflow_run(db, workflow, user):
    """Create a test workflow run."""
    return WorkflowRun.objects.create(
        workflow=workflow,
        triggered_by=user,
        trigger_type="manual",
        status=WorkflowRun.Status.PENDING,
    )


@pytest.mark.django_db
class TestWorkflowModel:
    """Tests for Workflow model."""

    def test_create_workflow(self, workflow):
        """Test creating a workflow."""
        assert workflow.id is not None
        assert workflow.name == "Data Processing Pipeline"
        assert len(workflow.steps) == 3
        assert workflow.status == Workflow.Status.ACTIVE

    def test_workflow_statuses(self, company, user):
        """Test different workflow statuses."""
        statuses = [
            Workflow.Status.DRAFT,
            Workflow.Status.ACTIVE,
            Workflow.Status.PAUSED,
            Workflow.Status.ARCHIVED,
        ]

        for workflow_status in statuses:
            workflow = Workflow.objects.create(
                company=company,
                created_by=user,
                name=f"Test {workflow_status} Workflow",
                steps=[],
                trigger={"type": "manual"},
                status=workflow_status,
            )
            assert workflow.status == workflow_status

    def test_success_rate_no_runs(self, workflow):
        """Test success rate with no runs."""
        assert workflow.success_rate == 0.0

    def test_success_rate_with_runs(self, workflow):
        """Test success rate calculation."""
        workflow.total_runs = 10
        workflow.successful_runs = 7
        workflow.save()

        assert workflow.success_rate == 70.0

    def test_update_stats_success(self, workflow):
        """Test updating stats on successful run."""
        initial_total = workflow.total_runs

        workflow.update_stats(success=True)

        assert workflow.total_runs == initial_total + 1
        assert workflow.successful_runs == 1
        assert workflow.last_success_at is not None

    def test_update_stats_failure(self, workflow):
        """Test updating stats on failed run."""
        initial_total = workflow.total_runs

        workflow.update_stats(success=False)

        assert workflow.total_runs == initial_total + 1
        assert workflow.failed_runs == 1
        assert workflow.last_failure_at is not None


@pytest.mark.django_db
class TestWorkflowRunModel:
    """Tests for WorkflowRun model."""

    def test_create_workflow_run(self, workflow_run):
        """Test creating a workflow run."""
        assert workflow_run.id is not None
        assert workflow_run.status == WorkflowRun.Status.PENDING
        assert workflow_run.trigger_type == "manual"

    def test_start_run(self, workflow_run):
        """Test starting a workflow run."""
        workflow_run.start()

        assert workflow_run.status == WorkflowRun.Status.RUNNING
        assert workflow_run.started_at is not None

    def test_complete_run(self, workflow_run):
        """Test completing a workflow run."""
        workflow_run.start()
        workflow_run.complete(output_data={"result": "success"})

        assert workflow_run.status == WorkflowRun.Status.COMPLETED
        assert workflow_run.completed_at is not None
        assert workflow_run.output_data == {"result": "success"}
        assert workflow_run.duration_seconds is not None

    def test_fail_run(self, workflow_run):
        """Test failing a workflow run."""
        workflow_run.start()
        workflow_run.fail("Step 2 failed: validation error")

        assert workflow_run.status == WorkflowRun.Status.FAILED
        assert workflow_run.completed_at is not None
        assert "validation error" in workflow_run.error_message

    def test_log_step(self, workflow_run):
        """Test logging step execution."""
        workflow_run.start()

        workflow_run.log_step(
            step_name="Fetch Data",
            status="completed",
            output={"records": 100},
        )

        assert len(workflow_run.step_logs) == 1
        assert workflow_run.step_logs[0]["step_name"] == "Fetch Data"
        assert workflow_run.step_logs[0]["status"] == "completed"
        assert workflow_run.current_step == 1


@pytest.mark.django_db
class TestWorkflowAPI:
    """Tests for Workflow API endpoints."""

    def test_list_workflows(self, auth_client, workflow):
        """Test listing workflows."""
        response = auth_client.get("/api/v2/workflows/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_create_workflow(self, auth_client, company):
        """Test creating a workflow."""
        data = {
            "name": "New Test Workflow",
            "description": "Test workflow description",
            "steps": [
                {"type": "data_fetch", "name": "Step 1", "config": {}},
                {"type": "transform", "name": "Step 2", "config": {}},
            ],
            "trigger": {"type": "manual"},
            "status": "draft",
        }
        response = auth_client.post("/api/v2/workflows/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Test Workflow"
        assert len(response.data["steps"]) == 2

    def test_retrieve_workflow(self, auth_client, workflow):
        """Test retrieving a single workflow."""
        response = auth_client.get(f"/api/v2/workflows/{workflow.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(workflow.id)
        assert response.data["name"] == workflow.name

    def test_run_workflow(self, auth_client, workflow):
        """Test triggering a workflow run."""
        data = {"input_data": {"key": "value"}}
        response = auth_client.post(
            f"/api/v2/workflows/{workflow.id}/run/", data, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "completed"
        assert response.data["trigger_type"] == "manual"

    def test_run_inactive_workflow_fails(self, auth_client, workflow):
        """Test that running an inactive workflow fails."""
        workflow.status = Workflow.Status.DRAFT
        workflow.save()

        response = auth_client.post(f"/api/v2/workflows/{workflow.id}/run/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_activate_workflow(self, auth_client, workflow):
        """Test activating a draft workflow."""
        workflow.status = Workflow.Status.DRAFT
        workflow.save()

        response = auth_client.post(f"/api/v2/workflows/{workflow.id}/activate/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "active"

    def test_pause_workflow(self, auth_client, workflow):
        """Test pausing an active workflow."""
        response = auth_client.post(f"/api/v2/workflows/{workflow.id}/pause/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "paused"

    def test_filter_workflows_by_status(self, auth_client, workflow):
        """Test filtering workflows by status."""
        response = auth_client.get("/api/v2/workflows/?status=active")

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestWorkflowRunAPI:
    """Tests for WorkflowRun API endpoints."""

    def test_list_workflow_runs(self, auth_client, workflow_run):
        """Test listing workflow runs."""
        response = auth_client.get("/api/v2/workflow-runs/")

        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_workflow_run(self, auth_client, workflow_run):
        """Test retrieving a single workflow run."""
        response = auth_client.get(f"/api/v2/workflow-runs/{workflow_run.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(workflow_run.id)

    def test_cancel_workflow_run(self, auth_client, workflow_run):
        """Test cancelling a running workflow run."""
        workflow_run.status = WorkflowRun.Status.RUNNING
        workflow_run.save()

        response = auth_client.post(
            f"/api/v2/workflow-runs/{workflow_run.id}/cancel/"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "cancelled"

    def test_cancel_completed_run_fails(self, auth_client, workflow_run):
        """Test that cancelling a completed run fails."""
        workflow_run.status = WorkflowRun.Status.COMPLETED
        workflow_run.save()

        response = auth_client.post(
            f"/api/v2/workflow-runs/{workflow_run.id}/cancel/"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_runs_by_workflow(self, auth_client, workflow, workflow_run):
        """Test filtering runs by workflow."""
        response = auth_client.get(
            f"/api/v2/workflow-runs/?workflow_id={workflow.id}"
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestWorkflowValidation:
    """Tests for workflow validation."""

    def test_invalid_steps(self, auth_client):
        """Test that invalid steps are rejected."""
        data = {
            "name": "Test Workflow",
            "steps": "not a list",  # Should be a list
            "trigger": {"type": "manual"},
        }
        response = auth_client.post("/api/v2/workflows/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_steps_missing_type(self, auth_client):
        """Test that steps without type are rejected."""
        data = {
            "name": "Test Workflow",
            "steps": [{"name": "Step 1"}],  # Missing 'type'
            "trigger": {"type": "manual"},
        }
        response = auth_client.post("/api/v2/workflows/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_trigger(self, auth_client):
        """Test that invalid trigger is rejected."""
        data = {
            "name": "Test Workflow",
            "steps": [{"type": "transform", "name": "Step 1"}],
            "trigger": {"type": "invalid_type"},
        }
        response = auth_client.post("/api/v2/workflows/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_schedule_trigger_requires_schedule(self, auth_client):
        """Test that schedule trigger requires schedule field."""
        data = {
            "name": "Test Workflow",
            "steps": [{"type": "transform", "name": "Step 1"}],
            "trigger": {"type": "schedule"},  # Missing 'schedule'
        }
        response = auth_client.post("/api/v2/workflows/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
