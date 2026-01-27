"""
Reports module tests for Xcapit FHE-ML Platform.
"""

import pytest
from django.utils import timezone
from rest_framework import status

from apps.core.models import Report


@pytest.fixture
def report(db, company, user):
    """Create a test report."""
    return Report.objects.create(
        company=company,
        created_by=user,
        name="Monthly Performance Report",
        report_type=Report.ReportType.PERFORMANCE,
        format=Report.Format.PDF,
        date_from=timezone.now().date(),
        date_to=timezone.now().date(),
        sections=["summary", "metrics", "charts"],
        status=Report.Status.PENDING,
    )


@pytest.mark.django_db
class TestReportModel:
    """Tests for Report model."""

    def test_create_report(self, report):
        """Test creating a report."""
        assert report.id is not None
        assert report.name == "Monthly Performance Report"
        assert report.report_type == Report.ReportType.PERFORMANCE
        assert report.status == Report.Status.PENDING

    def test_mark_generating(self, report):
        """Test marking report as generating."""
        report.mark_generating()
        report.refresh_from_db()

        assert report.status == Report.Status.GENERATING

    def test_mark_completed(self, report):
        """Test marking report as completed."""
        report.mark_completed(
            file_path="/reports/test.pdf",
            file_size=1024,
            download_url="https://example.com/reports/test.pdf",
        )
        report.refresh_from_db()

        assert report.status == Report.Status.COMPLETED
        assert report.file_path == "/reports/test.pdf"
        assert report.file_size == 1024
        assert report.download_url == "https://example.com/reports/test.pdf"
        assert report.completed_at is not None
        assert report.download_expires_at is not None

    def test_mark_failed(self, report):
        """Test marking report as failed."""
        report.mark_failed("Generation error: out of memory")
        report.refresh_from_db()

        assert report.status == Report.Status.FAILED
        assert "out of memory" in report.error_message

    def test_report_types(self, company, user):
        """Test different report types."""
        report_types = [
            Report.ReportType.PERFORMANCE,
            Report.ReportType.COMPLIANCE,
            Report.ReportType.CONSORTIUM,
            Report.ReportType.USAGE,
            Report.ReportType.AUDIT,
            Report.ReportType.CUSTOM,
        ]

        for report_type in report_types:
            report = Report.objects.create(
                company=company,
                created_by=user,
                name=f"Test {report_type} Report",
                report_type=report_type,
                format=Report.Format.PDF,
            )
            assert report.report_type == report_type

    def test_report_formats(self, company, user):
        """Test different report formats."""
        formats = [
            Report.Format.PDF,
            Report.Format.CSV,
            Report.Format.JSON,
            Report.Format.EXCEL,
        ]

        for format_type in formats:
            report = Report.objects.create(
                company=company,
                created_by=user,
                name=f"Test {format_type} Report",
                report_type=Report.ReportType.PERFORMANCE,
                format=format_type,
            )
            assert report.format == format_type


@pytest.mark.django_db
class TestReportAPI:
    """Tests for Report API endpoints."""

    def test_list_reports(self, authenticated_client, report):
        """Test listing reports."""
        response = authenticated_client.get("/api/v2/reports/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_create_report(self, authenticated_client, company):
        """Test creating a report."""
        data = {
            "name": "New Test Report",
            "report_type": "performance",
            "format": "pdf",
            "sections": ["summary", "metrics"],
        }
        response = authenticated_client.post("/api/v2/reports/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Test Report"
        assert response.data["status"] == "pending"

    def test_retrieve_report(self, authenticated_client, report):
        """Test retrieving a single report."""
        response = authenticated_client.get(f"/api/v2/reports/{report.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(report.id)
        assert response.data["name"] == report.name

    def test_generate_report(self, authenticated_client, report):
        """Test triggering report generation."""
        response = authenticated_client.post(f"/api/v2/reports/{report.id}/generate/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "completed"

    def test_download_completed_report(self, authenticated_client, report):
        """Test downloading a completed report."""
        # First complete the report
        report.mark_completed("/reports/test.pdf", 1024)

        response = authenticated_client.get(f"/api/v2/reports/{report.id}/download/")

        assert response.status_code == status.HTTP_200_OK
        assert "download_url" in response.data

    def test_download_pending_report_fails(self, authenticated_client, report):
        """Test that downloading a pending report fails."""
        response = authenticated_client.get(f"/api/v2/reports/{report.id}/download/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_reports_by_type(self, authenticated_client, report):
        """Test filtering reports by type."""
        response = authenticated_client.get("/api/v2/reports/?type=performance")

        assert response.status_code == status.HTTP_200_OK

    def test_filter_reports_by_status(self, authenticated_client, report):
        """Test filtering reports by status."""
        response = authenticated_client.get("/api/v2/reports/?status=pending")

        assert response.status_code == status.HTTP_200_OK

    def test_delete_report(self, authenticated_client, report):
        """Test deleting a report."""
        response = authenticated_client.delete(f"/api/v2/reports/{report.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Report.objects.filter(id=report.id).exists()


@pytest.mark.django_db
class TestReportValidation:
    """Tests for report validation."""

    def test_invalid_report_type(self, authenticated_client):
        """Test that invalid report type is rejected."""
        data = {
            "name": "Test Report",
            "report_type": "invalid_type",
            "format": "pdf",
        }
        response = authenticated_client.post("/api/v2/reports/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_format(self, authenticated_client):
        """Test that invalid format is rejected."""
        data = {
            "name": "Test Report",
            "report_type": "performance",
            "format": "invalid_format",
        }
        response = authenticated_client.post("/api/v2/reports/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_date_range(self, authenticated_client):
        """Test that invalid date range is rejected."""
        data = {
            "name": "Test Report",
            "report_type": "performance",
            "format": "pdf",
            "date_from": "2024-12-31",
            "date_to": "2024-01-01",  # End before start
        }
        response = authenticated_client.post("/api/v2/reports/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
