"""
Compliance module tests for Xcapit FHE-ML Platform.

Tests for compliance frameworks, checks, reports, attestations, and GDPR records.
"""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from apps.compliance.models import (
    Attestation,
    ComplianceCheck,
    ComplianceFramework,
    ComplianceReport,
    ConsortiumCompliance,
    DataProcessingRecord,
)
from apps.consortiums.models import ConsortiumMember


@pytest.mark.django_db
class TestComplianceFrameworkEndpoints:
    """Tests for compliance framework (read-only) operations."""

    def test_list_frameworks(self, auth_client):
        """Test listing compliance frameworks."""
        ComplianceFramework.objects.create(
            id="framework_gdpr",
            name="GDPR",
            version="2018",
            description="General Data Protection Regulation",
            region="EU",
        )

        url = "/api/v2/compliance/frameworks/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_frameworks_by_region(self, auth_client):
        """Test filtering frameworks by region."""
        ComplianceFramework.objects.create(
            id="framework_gdpr",
            name="GDPR",
            version="2018",
            region="EU",
        )
        ComplianceFramework.objects.create(
            id="framework_hipaa",
            name="HIPAA",
            version="1996",
            region="US",
        )

        url = "/api/v2/compliance/frameworks/?region=EU"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for fw in response.data.get("results", response.data):
            assert fw["region"] == "EU"

    def test_filter_frameworks_by_industry(self, auth_client):
        """Test filtering frameworks by industry."""
        ComplianceFramework.objects.create(
            id="framework_hipaa",
            name="HIPAA",
            version="1996",
            industry="healthcare",
        )
        ComplianceFramework.objects.create(
            id="framework_pci",
            name="PCI-DSS",
            version="4.0",
            industry="finance",
        )

        url = "/api/v2/compliance/frameworks/?industry=healthcare"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for fw in response.data.get("results", response.data):
            assert fw["industry"] in ["healthcare", ""]

    def test_get_framework(self, auth_client):
        """Test getting a single framework."""
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )

        url = f"/api/v2/compliance/frameworks/{framework.id}/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Framework"

    def test_get_framework_controls(self, auth_client):
        """Test getting framework controls."""
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
            controls=[
                {"id": "ctrl1", "name": "Control 1", "description": "First control"},
                {"id": "ctrl2", "name": "Control 2", "description": "Second control"},
            ],
        )

        url = f"/api/v2/compliance/frameworks/{framework.id}/controls/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert len(response.data["controls"]) == 2

    def test_frameworks_are_read_only(self, auth_client):
        """Test frameworks cannot be created via API."""
        url = "/api/v2/compliance/frameworks/"
        data = {"id": "new_framework", "name": "New Framework", "version": "1.0"}

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestConsortiumComplianceEndpoints:
    """Tests for consortium compliance settings."""

    def test_list_compliance_settings(self, auth_client, consortium, company):
        """Test listing consortium compliance settings."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        ConsortiumCompliance.objects.create(
            consortium=consortium,
            auto_check_interval=24,
        )

        url = f"/api/v2/compliance/settings/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_get_compliance_summary(self, auth_client, consortium, company):
        """Test getting compliance summary."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        compliance = ConsortiumCompliance.objects.create(consortium=consortium)
        compliance.enabled_frameworks.add(framework)

        # Add some checks
        ComplianceCheck.objects.create(
            consortium=consortium,
            framework=framework,
            control_id="ctrl1",
            status=ComplianceCheck.Status.PASSED,
            result="Control passed",
            checked_by=company,
        )
        ComplianceCheck.objects.create(
            consortium=consortium,
            framework=framework,
            control_id="ctrl2",
            status=ComplianceCheck.Status.PASSED,
            result="Control passed",
            checked_by=company,
        )

        url = f"/api/v2/compliance/settings/{compliance.id}/summary/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]["overall_score"] == 100.0


@pytest.mark.django_db
class TestComplianceCheckEndpoints:
    """Tests for compliance checks."""

    def test_create_check(self, auth_client, consortium, company):
        """Test creating a compliance check."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )

        url = "/api/v2/compliance/checks/"
        data = {
            "consortium": str(consortium.id),
            "framework": framework.id,
            "control_id": "ctrl1",
            "status": ComplianceCheck.Status.PASSED,
            "result": "Control passed verification",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] == "passed"

    def test_list_checks(self, auth_client, consortium, company):
        """Test listing compliance checks."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        ComplianceCheck.objects.create(
            consortium=consortium,
            framework=framework,
            control_id="ctrl1",
            status=ComplianceCheck.Status.PASSED,
            result="Test",
            checked_by=company,
        )

        url = f"/api/v2/compliance/checks/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_checks_by_framework(self, auth_client, consortium, company):
        """Test filtering checks by framework."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework1 = ComplianceFramework.objects.create(
            id="framework_1",
            name="Framework 1",
            version="1.0",
        )
        framework2 = ComplianceFramework.objects.create(
            id="framework_2",
            name="Framework 2",
            version="1.0",
        )
        ComplianceCheck.objects.create(
            consortium=consortium,
            framework=framework1,
            control_id="ctrl1",
            result="Test",
        )
        ComplianceCheck.objects.create(
            consortium=consortium,
            framework=framework2,
            control_id="ctrl1",
            result="Test",
        )

        url = f"/api/v2/compliance/checks/?consortium_id={consortium.id}&framework_id=framework_1"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for check in response.data.get("results", response.data):
            assert check["framework"] == "framework_1"

    def test_filter_checks_by_status(self, auth_client, consortium, company):
        """Test filtering checks by status."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        ComplianceCheck.objects.create(
            consortium=consortium,
            framework=framework,
            control_id="ctrl1",
            status=ComplianceCheck.Status.PASSED,
            result="Test",
        )
        ComplianceCheck.objects.create(
            consortium=consortium,
            framework=framework,
            control_id="ctrl2",
            status=ComplianceCheck.Status.FAILED,
            result="Test",
        )

        url = f"/api/v2/compliance/checks/?consortium_id={consortium.id}&status=passed"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for check in response.data.get("results", response.data):
            assert check["status"] == "passed"


@pytest.mark.django_db
class TestComplianceReportEndpoints:
    """Tests for compliance reports."""

    def test_list_reports(self, auth_client, consortium, company):
        """Test listing compliance reports."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        ComplianceReport.objects.create(
            consortium=consortium,
            framework=framework,
            overall_score=85.0,
            status=ComplianceReport.Status.PARTIAL,
            passed_controls=8,
            failed_controls=2,
            total_controls=10,
        )

        url = f"/api/v2/compliance/reports/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_generate_report(self, auth_client, consortium, company):
        """Test generating a compliance report."""
        consortium.owner = company
        consortium.save()
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.ADMIN,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        ConsortiumCompliance.objects.create(consortium=consortium)

        # Add checks
        for i in range(9):
            ComplianceCheck.objects.create(
                consortium=consortium,
                framework=framework,
                control_id=f"ctrl{i}",
                status=ComplianceCheck.Status.PASSED,
                result="Passed",
            )
        ComplianceCheck.objects.create(
            consortium=consortium,
            framework=framework,
            control_id="ctrl9",
            status=ComplianceCheck.Status.FAILED,
            result="Failed",
        )

        url = "/api/v2/compliance/reports/generate/"
        data = {
            "consortium_id": str(consortium.id),
            "framework_id": framework.id,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["overall_score"] == 90.0
        assert response.data["status"] == "compliant"

    def test_generate_report_no_checks(self, auth_client, consortium, company):
        """Test generating report without checks fails."""
        consortium.owner = company
        consortium.save()
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.ADMIN,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )

        url = "/api/v2/compliance/reports/generate/"
        data = {
            "consortium_id": str(consortium.id),
            "framework_id": framework.id,
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no compliance checks" in response.data["detail"].lower()

    def test_filter_reports_by_framework(self, auth_client, consortium, company):
        """Test filtering reports by framework."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework1 = ComplianceFramework.objects.create(
            id="framework_1",
            name="Framework 1",
            version="1.0",
        )
        framework2 = ComplianceFramework.objects.create(
            id="framework_2",
            name="Framework 2",
            version="1.0",
        )
        ComplianceReport.objects.create(
            consortium=consortium,
            framework=framework1,
            overall_score=90,
            status=ComplianceReport.Status.COMPLIANT,
            total_controls=10,
        )
        ComplianceReport.objects.create(
            consortium=consortium,
            framework=framework2,
            overall_score=70,
            status=ComplianceReport.Status.PARTIAL,
            total_controls=10,
        )

        url = f"/api/v2/compliance/reports/?consortium_id={consortium.id}&framework_id=framework_1"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for report in response.data.get("results", response.data):
            assert report["framework"] == "framework_1"


@pytest.mark.django_db
class TestAttestationEndpoints:
    """Tests for compliance attestations."""

    def test_create_attestation(self, auth_client, consortium, company):
        """Test creating an attestation."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )

        url = "/api/v2/compliance/attestations/"
        data = {
            "consortium": str(consortium.id),
            "framework": framework.id,
            "control_id": "ctrl1",
            "statement": "I attest that this control is implemented",
            "attester_role": "Security Officer",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["statement"] == "I attest that this control is implemented"

    def test_list_attestations(self, auth_client, consortium, company):
        """Test listing attestations."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        Attestation.objects.create(
            consortium=consortium,
            framework=framework,
            attester=company,
            statement="Test attestation",
        )

        url = f"/api/v2/compliance/attestations/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_valid_attestations(self, auth_client, consortium, company):
        """Test filtering only valid attestations."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        Attestation.objects.create(
            consortium=consortium,
            framework=framework,
            attester=company,
            statement="Valid attestation",
        )
        Attestation.objects.create(
            consortium=consortium,
            framework=framework,
            attester=company,
            statement="Revoked attestation",
            revoked=True,
        )

        url = f"/api/v2/compliance/attestations/?consortium_id={consortium.id}&valid_only=true"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        for att in response.data.get("results", response.data):
            assert att["revoked"] is False

    def test_revoke_attestation(self, auth_client, consortium, company):
        """Test revoking an attestation."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        attestation = Attestation.objects.create(
            consortium=consortium,
            framework=framework,
            attester=company,
            statement="Test attestation",
        )

        url = f"/api/v2/compliance/attestations/{attestation.id}/revoke/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        attestation.refresh_from_db()
        assert attestation.revoked is True

    def test_cannot_revoke_already_revoked(self, auth_client, consortium, company):
        """Test cannot revoke already revoked attestation."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        attestation = Attestation.objects.create(
            consortium=consortium,
            framework=framework,
            attester=company,
            statement="Test attestation",
            revoked=True,
        )

        url = f"/api/v2/compliance/attestations/{attestation.id}/revoke/?consortium_id={consortium.id}"

        response = auth_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already revoked" in response.data["detail"].lower()

    def test_only_attester_can_revoke(self, other_auth_client, consortium, company, other_company):
        """Test only attester can revoke their attestation."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=other_company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        attestation = Attestation.objects.create(
            consortium=consortium,
            framework=framework,
            attester=company,  # Attester is main company
            statement="Test attestation",
        )

        url = f"/api/v2/compliance/attestations/{attestation.id}/revoke/?consortium_id={consortium.id}"

        response = other_auth_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestDataProcessingRecordEndpoints:
    """Tests for GDPR Article 30 data processing records."""

    def test_create_record(self, auth_client, consortium, company):
        """Test creating a data processing record."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )

        url = "/api/v2/compliance/data-processing/"
        data = {
            "consortium": str(consortium.id),
            "processing_purpose": "Fraud detection model training",
            "data_categories": ["transaction_data", "user_behavior"],
            "legal_basis": "Legitimate interest",
            "data_subjects": "Bank customers",
            "retention_period": "5 years",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["processing_purpose"] == "Fraud detection model training"

    def test_list_records(self, auth_client, consortium, company):
        """Test listing data processing records."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        DataProcessingRecord.objects.create(
            consortium=consortium,
            company=company,
            processing_purpose="Test processing",
            legal_basis="Consent",
        )

        url = f"/api/v2/compliance/data-processing/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_export_records(self, auth_client, consortium, company):
        """Test exporting data processing records."""
        ConsortiumMember.objects.create(
            consortium=consortium,
            company=company,
            role=ConsortiumMember.Role.CONTRIBUTOR,
            status=ConsortiumMember.Status.ACTIVE,
        )
        DataProcessingRecord.objects.create(
            consortium=consortium,
            company=company,
            processing_purpose="Test processing 1",
            legal_basis="Consent",
        )
        DataProcessingRecord.objects.create(
            consortium=consortium,
            company=company,
            processing_purpose="Test processing 2",
            legal_basis="Legitimate interest",
        )

        url = f"/api/v2/compliance/data-processing/export/?consortium_id={consortium.id}"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["record_count"] == 2
        assert "records" in response.data

    def test_export_requires_consortium_id(self, auth_client):
        """Test export requires consortium_id."""
        url = "/api/v2/compliance/data-processing/export/"

        response = auth_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "consortium_id" in response.data["detail"]


@pytest.mark.django_db
class TestComplianceModels:
    """Tests for compliance model methods and properties."""

    def test_framework_str(self):
        """Test framework string representation."""
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="2.0",
        )

        assert "Test Framework" in str(framework)
        assert "v2.0" in str(framework)

    def test_framework_controls_count(self):
        """Test framework controls count property."""
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test",
            version="1.0",
            controls=[{"id": "c1"}, {"id": "c2"}, {"id": "c3"}],
        )

        assert framework.controls_count == 3

    def test_consortium_compliance_str(self, consortium):
        """Test consortium compliance string representation."""
        compliance = ConsortiumCompliance.objects.create(consortium=consortium)

        assert consortium.name in str(compliance)

    def test_consortium_compliance_next_check(self, consortium):
        """Test next check calculation."""
        compliance = ConsortiumCompliance.objects.create(
            consortium=consortium,
            auto_check_interval=24,
            last_check_at=timezone.now(),
        )

        assert compliance.next_check_at is not None
        assert compliance.next_check_at > compliance.last_check_at

    def test_check_str(self, consortium):
        """Test compliance check string representation."""
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        check = ComplianceCheck.objects.create(
            consortium=consortium,
            framework=framework,
            control_id="ctrl1",
            status=ComplianceCheck.Status.PASSED,
            result="Passed",
        )

        assert "Test Framework" in str(check)
        assert "ctrl1" in str(check)

    def test_report_str(self, consortium):
        """Test compliance report string representation."""
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        report = ComplianceReport.objects.create(
            consortium=consortium,
            framework=framework,
            overall_score=85,
            status=ComplianceReport.Status.PARTIAL,
            total_controls=10,
        )

        assert consortium.name in str(report)
        assert "Test Framework" in str(report)

    def test_attestation_str(self, consortium, company):
        """Test attestation string representation."""
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        attestation = Attestation.objects.create(
            consortium=consortium,
            framework=framework,
            attester=company,
            statement="Test",
        )

        assert company.name in str(attestation)

    def test_attestation_is_valid(self, consortium, company):
        """Test attestation validity check."""
        framework = ComplianceFramework.objects.create(
            id="framework_test",
            name="Test Framework",
            version="1.0",
        )
        valid_attestation = Attestation.objects.create(
            consortium=consortium,
            framework=framework,
            attester=company,
            statement="Test",
            valid_from=timezone.now() - timedelta(days=1),
        )
        expired_attestation = Attestation.objects.create(
            consortium=consortium,
            framework=framework,
            attester=company,
            statement="Test",
            valid_from=timezone.now() - timedelta(days=10),
            valid_until=timezone.now() - timedelta(days=1),
        )
        revoked_attestation = Attestation.objects.create(
            consortium=consortium,
            framework=framework,
            attester=company,
            statement="Test",
            revoked=True,
        )

        assert valid_attestation.is_valid is True
        assert expired_attestation.is_valid is False
        assert revoked_attestation.is_valid is False

    def test_processing_record_str(self, consortium, company):
        """Test data processing record string representation."""
        record = DataProcessingRecord.objects.create(
            consortium=consortium,
            company=company,
            processing_purpose="Very long processing purpose that exceeds fifty characters",
            legal_basis="Consent",
        )

        assert "..." in str(record)
