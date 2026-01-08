"""Tests for TIER 3 Compliance features.

Tests cover:
- Compliance frameworks (GDPR, HIPAA, SOC2, PCI-DSS)
- Compliance checks
- Compliance reports
- Attestations
- Data processing records (GDPR Article 30)
- Compliance dashboard
"""

import sys
from pathlib import Path
import pytest
import tempfile
from datetime import datetime, timedelta
import importlib.util

project_root = Path(__file__).parent.parent
sdk_api_path = project_root / "sdk" / "api"


def load_module_from_path(module_name, file_path):
    """Load a module from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Load consortium module package
consortium_package_path = sdk_api_path / "consortium"
consortium_module = load_module_from_path(
    "sdk.api.consortium",
    consortium_package_path / "__init__.py"
)
ConsortiumManager = consortium_module.ConsortiumManager
ConsortiumStatus = consortium_module.ConsortiumStatus
MemberRole = consortium_module.MemberRole
MemberStatus = consortium_module.MemberStatus


class TestComplianceFrameworks:
    """Tests for compliance frameworks functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_compliance.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium with members for testing."""
        # Create owner company
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")

        # Create member company
        member, _ = manager.create_company("Member Corp", "member@test.com")

        # Create consortium
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing compliance",
            owner_id=owner.id,
            model_type="linear_regression"
        )

        # Add member via invitation
        invitation = manager.create_invitation(
            consortium_id=consortium.id,
            invited_by=owner.id,
            invite_email="member@test.com",
            role=MemberRole.CONTRIBUTOR
        )
        manager.accept_invitation(invitation.invite_code, member.id)

        return {
            "consortium": consortium,
            "owner": owner,
            "member": member
        }

    def test_get_compliance_frameworks(self, manager):
        """Test getting all compliance frameworks."""
        frameworks = manager.get_compliance_frameworks()

        assert len(frameworks) == 4
        names = {f["name"] for f in frameworks}
        assert "GDPR" in names
        assert "HIPAA" in names
        assert "SOC2" in names
        assert "PCI-DSS" in names

    def test_get_compliance_framework_by_id(self, manager):
        """Test getting a specific compliance framework."""
        framework = manager.get_compliance_framework("framework_gdpr")

        assert framework is not None
        assert framework["name"] == "GDPR"
        assert framework["region"] == "EU"
        assert "General Data Protection" in framework["description"]

    def test_get_nonexistent_framework(self, manager):
        """Test getting a non-existent framework returns None."""
        framework = manager.get_compliance_framework("framework_nonexistent")
        assert framework is None

    def test_enable_compliance_framework(self, manager, setup_consortium):
        """Test enabling a compliance framework for a consortium."""
        consortium = setup_consortium["consortium"]

        result = manager.enable_compliance_framework(
            consortium.id,
            "framework_gdpr"
        )

        assert result["consortium_id"] == consortium.id
        assert "framework_gdpr" in result["enabled_frameworks"]

    def test_enable_multiple_frameworks(self, manager, setup_consortium):
        """Test enabling multiple compliance frameworks."""
        consortium = setup_consortium["consortium"]

        manager.enable_compliance_framework(consortium.id, "framework_gdpr")
        manager.enable_compliance_framework(consortium.id, "framework_hipaa")
        result = manager.enable_compliance_framework(consortium.id, "framework_soc2")

        assert len(result["enabled_frameworks"]) == 3
        assert "framework_gdpr" in result["enabled_frameworks"]
        assert "framework_hipaa" in result["enabled_frameworks"]
        assert "framework_soc2" in result["enabled_frameworks"]

    def test_enable_same_framework_twice(self, manager, setup_consortium):
        """Test enabling same framework twice doesn't duplicate."""
        consortium = setup_consortium["consortium"]

        manager.enable_compliance_framework(consortium.id, "framework_gdpr")
        result = manager.enable_compliance_framework(consortium.id, "framework_gdpr")

        assert result["enabled_frameworks"].count("framework_gdpr") == 1


class TestComplianceSettings:
    """Tests for consortium compliance settings."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_compliance_settings.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium for testing."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing compliance settings",
            owner_id=owner.id,
            model_type="linear_regression"
        )
        return {"consortium": consortium, "owner": owner}

    def test_get_default_settings(self, manager, setup_consortium):
        """Test getting default settings for new consortium."""
        consortium = setup_consortium["consortium"]

        settings = manager.get_consortium_compliance_settings(consortium.id)

        assert settings["consortium_id"] == consortium.id
        assert settings["enabled_frameworks"] == []
        assert settings["auto_check_interval"] == 86400  # 24 hours
        assert settings["notification_emails"] == []

    def test_settings_after_enabling_framework(self, manager, setup_consortium):
        """Test settings are created after enabling framework."""
        consortium = setup_consortium["consortium"]

        manager.enable_compliance_framework(consortium.id, "framework_gdpr")
        settings = manager.get_consortium_compliance_settings(consortium.id)

        assert "framework_gdpr" in settings["enabled_frameworks"]


class TestComplianceChecks:
    """Tests for compliance check functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_compliance_checks.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium with compliance enabled."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing compliance checks",
            owner_id=owner.id,
            model_type="linear_regression"
        )
        manager.enable_compliance_framework(consortium.id, "framework_gdpr")
        return {"consortium": consortium, "owner": owner}

    def test_record_compliance_check(self, manager, setup_consortium):
        """Test recording a compliance check."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        check_id = manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_encryption",
            status="passed",
            result="Data encryption verified",
            evidence={"encryption_type": "AES-256", "verified": True},
            checked_by=owner.id,
            notes="Automated verification"
        )

        assert check_id is not None
        assert check_id.startswith("check_")

    def test_get_compliance_checks(self, manager, setup_consortium):
        """Test getting compliance checks for a consortium."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Record multiple checks
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_encryption",
            status="passed",
            result="Encryption OK",
            checked_by=owner.id
        )
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_access_control",
            status="failed",
            result="Access control needs improvement",
            checked_by=owner.id
        )

        checks = manager.get_compliance_checks(consortium.id)

        assert len(checks) == 2

    def test_get_compliance_checks_by_framework(self, manager, setup_consortium):
        """Test filtering compliance checks by framework."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Enable another framework
        manager.enable_compliance_framework(consortium.id, "framework_hipaa")

        # Record checks for both frameworks
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_encryption",
            status="passed",
            result="OK",
            checked_by=owner.id
        )
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_hipaa",
            control_id="hipaa_phi_protection",
            status="pending",
            result="Pending review",
            checked_by=owner.id
        )

        # Get only GDPR checks
        gdpr_checks = manager.get_compliance_checks(consortium.id, framework_id="framework_gdpr")
        assert len(gdpr_checks) == 1
        assert gdpr_checks[0]["control_id"] == "gdpr_encryption"

    def test_get_compliance_checks_by_status(self, manager, setup_consortium):
        """Test filtering compliance checks by status."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_check_1",
            status="passed",
            result="OK",
            checked_by=owner.id
        )
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_check_2",
            status="failed",
            result="Failed",
            checked_by=owner.id
        )

        passed_checks = manager.get_compliance_checks(consortium.id, status="passed")
        assert len(passed_checks) == 1
        assert passed_checks[0]["status"] == "passed"


class TestComplianceReports:
    """Tests for compliance report generation."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_compliance_reports.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium_with_checks(self, manager):
        """Create a consortium with compliance checks."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing reports",
            owner_id=owner.id,
            model_type="linear_regression"
        )
        manager.enable_compliance_framework(consortium.id, "framework_gdpr")

        # Add some checks
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_check_1",
            status="passed",
            result="OK",
            checked_by=owner.id
        )
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_check_2",
            status="passed",
            result="OK",
            checked_by=owner.id
        )
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_check_3",
            status="failed",
            result="Needs attention",
            checked_by=owner.id
        )

        return {"consortium": consortium, "owner": owner}

    def test_generate_compliance_report(self, manager, setup_consortium_with_checks):
        """Test generating a compliance report."""
        consortium = setup_consortium_with_checks["consortium"]

        report = manager.generate_compliance_report(consortium.id, "framework_gdpr")

        assert report["id"] is not None
        assert report["consortium_id"] == consortium.id
        assert report["framework_id"] == "framework_gdpr"
        assert report["passed_controls"] == 2
        assert report["failed_controls"] == 1
        assert report["total_controls"] == 3
        assert abs(report["overall_score"] - 66.67) < 1  # ~66.67%
        assert report["status"] == "non_compliant"  # Has failed controls

    def test_generate_report_all_passed(self, manager):
        """Test report when all checks pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_all_passed.db"
            mgr = ConsortiumManager(db_path)

            owner, _ = mgr.create_company("Owner Corp", "owner@test.com")
            consortium = mgr.create_consortium(
                name="Perfect Consortium",
                description="All checks pass",
                owner_id=owner.id,
                model_type="linear_regression"
            )
            mgr.enable_compliance_framework(consortium.id, "framework_gdpr")

            # All passed
            for i in range(3):
                mgr.record_compliance_check(
                    consortium_id=consortium.id,
                    framework_id="framework_gdpr",
                    control_id=f"gdpr_check_{i}",
                    status="passed",
                    result="OK",
                    checked_by=owner.id
                )

            report = mgr.generate_compliance_report(consortium.id, "framework_gdpr")

            assert report["overall_score"] == 100.0
            assert report["status"] == "compliant"

    def test_get_compliance_reports(self, manager, setup_consortium_with_checks):
        """Test getting compliance reports."""
        consortium = setup_consortium_with_checks["consortium"]

        # Generate multiple reports
        manager.generate_compliance_report(consortium.id, "framework_gdpr")
        manager.generate_compliance_report(consortium.id, "framework_gdpr")

        reports = manager.get_compliance_reports(consortium.id)

        assert len(reports) == 2


class TestAttestations:
    """Tests for compliance attestations."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_attestations.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium for testing."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing attestations",
            owner_id=owner.id,
            model_type="linear_regression"
        )
        manager.enable_compliance_framework(consortium.id, "framework_gdpr")
        return {"consortium": consortium, "owner": owner}

    def test_create_attestation(self, manager, setup_consortium):
        """Test creating an attestation."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        attestation_id = manager.create_attestation(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            attested_by=owner.id,
            statement="We confirm data is encrypted at rest and in transit",
            attester_role="CTO",
            attestation_type="security",
            evidence_urls=["https://docs.example.com/security-policy"],
            valid_days=365
        )

        assert attestation_id is not None
        assert attestation_id.startswith("attest_")

    def test_get_attestations(self, manager, setup_consortium):
        """Test getting attestations for a consortium."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        manager.create_attestation(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            attested_by=owner.id,
            statement="Attestation 1"
        )
        manager.create_attestation(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            attested_by=owner.id,
            statement="Attestation 2"
        )

        attestations = manager.get_attestations(consortium.id)

        assert len(attestations) == 2

    def test_get_attestations_by_framework(self, manager, setup_consortium):
        """Test filtering attestations by framework."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        manager.enable_compliance_framework(consortium.id, "framework_hipaa")

        manager.create_attestation(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            attested_by=owner.id,
            statement="GDPR attestation"
        )
        manager.create_attestation(
            consortium_id=consortium.id,
            framework_id="framework_hipaa",
            attested_by=owner.id,
            statement="HIPAA attestation"
        )

        gdpr_attestations = manager.get_attestations(
            consortium.id, framework_id="framework_gdpr"
        )

        assert len(gdpr_attestations) == 1
        assert gdpr_attestations[0]["statement"] == "GDPR attestation"


class TestDataProcessingRecords:
    """Tests for GDPR Article 30 data processing records."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_dpr.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium for testing."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing DPR",
            owner_id=owner.id,
            model_type="linear_regression"
        )
        return {"consortium": consortium, "owner": owner}

    def test_record_data_processing(self, manager, setup_consortium):
        """Test recording a data processing activity."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        record_id = manager.record_data_processing(
            consortium_id=consortium.id,
            company_id=owner.id,
            processing_purpose="Fraud detection model training",
            data_categories=["transaction_data", "user_behavior"],
            legal_basis="Legitimate interest",
            data_subjects="Banking customers",
            recipients=["Consortium members"],
            retention_period="2 years",
            security_measures=["Encryption", "Access control", "FHE"],
            cross_border_transfer=False
        )

        assert record_id is not None
        assert record_id.startswith("dpr_")

    def test_record_data_processing_cross_border(self, manager, setup_consortium):
        """Test recording cross-border data processing."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        record_id = manager.record_data_processing(
            consortium_id=consortium.id,
            company_id=owner.id,
            processing_purpose="International fraud analysis",
            data_categories=["transaction_data"],
            legal_basis="Contractual necessity",
            cross_border_transfer=True,
            transfer_safeguards="Standard Contractual Clauses"
        )

        records = manager.get_data_processing_records(consortium.id)
        assert len(records) == 1
        assert records[0]["cross_border_transfer"] is True
        assert records[0]["transfer_safeguards"] == "Standard Contractual Clauses"

    def test_get_data_processing_records(self, manager, setup_consortium):
        """Test getting data processing records."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        manager.record_data_processing(
            consortium_id=consortium.id,
            company_id=owner.id,
            processing_purpose="Purpose 1",
            data_categories=["category1"],
            legal_basis="Legal basis 1"
        )
        manager.record_data_processing(
            consortium_id=consortium.id,
            company_id=owner.id,
            processing_purpose="Purpose 2",
            data_categories=["category2", "category3"],
            legal_basis="Legal basis 2"
        )

        records = manager.get_data_processing_records(consortium.id)

        assert len(records) == 2

    def test_get_data_processing_records_by_company(self, manager, setup_consortium):
        """Test filtering data processing records by company."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Create another company
        other, _ = manager.create_company("Other Corp", "other@test.com")
        invitation = manager.create_invitation(
            consortium_id=consortium.id,
            invited_by=owner.id,
            invite_email="other@test.com"
        )
        manager.accept_invitation(invitation.invite_code, other.id)

        # Record for owner
        manager.record_data_processing(
            consortium_id=consortium.id,
            company_id=owner.id,
            processing_purpose="Owner processing",
            data_categories=["cat1"],
            legal_basis="Basis 1"
        )
        # Record for other
        manager.record_data_processing(
            consortium_id=consortium.id,
            company_id=other.id,
            processing_purpose="Other processing",
            data_categories=["cat2"],
            legal_basis="Basis 2"
        )

        owner_records = manager.get_data_processing_records(
            consortium.id, company_id=owner.id
        )

        assert len(owner_records) == 1
        assert owner_records[0]["processing_purpose"] == "Owner processing"


class TestComplianceDashboard:
    """Tests for compliance dashboard functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_dashboard.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium_with_compliance(self, manager):
        """Create a consortium with multiple frameworks and checks."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing dashboard",
            owner_id=owner.id,
            model_type="linear_regression"
        )

        # Enable frameworks
        manager.enable_compliance_framework(consortium.id, "framework_gdpr")
        manager.enable_compliance_framework(consortium.id, "framework_soc2")

        # GDPR checks: 2 passed, 1 failed
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_1",
            status="passed",
            result="OK",
            checked_by=owner.id
        )
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_2",
            status="passed",
            result="OK",
            checked_by=owner.id
        )
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            control_id="gdpr_3",
            status="failed",
            result="Failed",
            checked_by=owner.id
        )

        # SOC2 checks: all passed
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_soc2",
            control_id="soc2_1",
            status="passed",
            result="OK",
            checked_by=owner.id
        )
        manager.record_compliance_check(
            consortium_id=consortium.id,
            framework_id="framework_soc2",
            control_id="soc2_2",
            status="passed",
            result="OK",
            checked_by=owner.id
        )

        return {"consortium": consortium, "owner": owner}

    def test_get_compliance_dashboard(self, manager, setup_consortium_with_compliance):
        """Test getting compliance dashboard."""
        consortium = setup_consortium_with_compliance["consortium"]

        dashboard = manager.get_compliance_dashboard(consortium.id)

        assert dashboard["consortium_id"] == consortium.id
        assert dashboard["enabled_frameworks_count"] == 2
        assert len(dashboard["frameworks"]) == 2

    def test_dashboard_framework_scores(self, manager, setup_consortium_with_compliance):
        """Test dashboard shows correct framework scores."""
        consortium = setup_consortium_with_compliance["consortium"]

        dashboard = manager.get_compliance_dashboard(consortium.id)

        # Find frameworks
        gdpr = next(f for f in dashboard["frameworks"] if f["framework_id"] == "framework_gdpr")
        soc2 = next(f for f in dashboard["frameworks"] if f["framework_id"] == "framework_soc2")

        # GDPR: 2/3 passed = 66.67%
        assert abs(gdpr["score"] - 66.67) < 1
        assert gdpr["passed"] == 2
        assert gdpr["failed"] == 1
        assert gdpr["status"] == "non_compliant"

        # SOC2: 2/2 passed = 100%
        assert soc2["score"] == 100.0
        assert soc2["passed"] == 2
        assert soc2["failed"] == 0
        assert soc2["status"] == "compliant"

    def test_dashboard_overall_status(self, manager, setup_consortium_with_compliance):
        """Test dashboard overall status calculation."""
        consortium = setup_consortium_with_compliance["consortium"]

        dashboard = manager.get_compliance_dashboard(consortium.id)

        # Overall score is average: (66.67 + 100) / 2 = 83.33
        assert abs(dashboard["overall_score"] - 83.33) < 1
        # Not fully compliant because GDPR has failures
        assert dashboard["overall_status"] == "non_compliant"

    def test_dashboard_empty_frameworks(self, manager):
        """Test dashboard with no enabled frameworks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_empty.db"
            mgr = ConsortiumManager(db_path)

            owner, _ = mgr.create_company("Owner Corp", "owner@test.com")
            consortium = mgr.create_consortium(
                name="Empty Consortium",
                description="No compliance",
                owner_id=owner.id,
                model_type="linear_regression"
            )

            dashboard = mgr.get_compliance_dashboard(consortium.id)

            assert dashboard["enabled_frameworks_count"] == 0
            assert dashboard["frameworks"] == []
            assert dashboard["overall_score"] == 0
            assert dashboard["overall_status"] == "non_compliant"


class TestComplianceIntegration:
    """Integration tests for compliance workflow."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_integration.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    def test_full_compliance_workflow(self, manager):
        """Test complete compliance workflow."""
        # 1. Create consortium
        owner, _ = manager.create_company("FinTech Corp", "cto@fintech.com")
        consortium = manager.create_consortium(
            name="Fraud Detection Consortium",
            description="Collaborative fraud detection",
            owner_id=owner.id,
            model_type="logistic_regression"
        )

        # 2. Enable compliance frameworks
        manager.enable_compliance_framework(consortium.id, "framework_gdpr")
        manager.enable_compliance_framework(consortium.id, "framework_pci_dss")

        # 3. Record data processing (GDPR Article 30)
        dpr_id = manager.record_data_processing(
            consortium_id=consortium.id,
            company_id=owner.id,
            processing_purpose="Fraud detection using FHE-ML",
            data_categories=["transaction_data", "behavioral_patterns"],
            legal_basis="Legitimate interest in fraud prevention",
            data_subjects="Banking customers",
            recipients=["Consortium members only"],
            retention_period="24 months",
            security_measures=["FHE encryption", "Access controls", "Audit logging"],
            cross_border_transfer=False
        )
        assert dpr_id is not None

        # 4. Run compliance checks
        checks = [
            ("framework_gdpr", "gdpr_encryption", "passed"),
            ("framework_gdpr", "gdpr_access_control", "passed"),
            ("framework_gdpr", "gdpr_data_minimization", "passed"),
            ("framework_pci_dss", "pci_network_security", "passed"),
            ("framework_pci_dss", "pci_access_control", "passed"),
        ]

        for framework, control, status in checks:
            manager.record_compliance_check(
                consortium_id=consortium.id,
                framework_id=framework,
                control_id=control,
                status=status,
                result=f"{control} verification complete",
                checked_by=owner.id
            )

        # 5. Create attestation
        manager.create_attestation(
            consortium_id=consortium.id,
            framework_id="framework_gdpr",
            attested_by=owner.id,
            statement="All personal data is encrypted using FHE and never exposed in plaintext",
            attester_role="CTO",
            attestation_type="technical"
        )

        # 6. Generate reports
        gdpr_report = manager.generate_compliance_report(consortium.id, "framework_gdpr")
        pci_report = manager.generate_compliance_report(consortium.id, "framework_pci_dss")

        assert gdpr_report["overall_score"] == 100.0
        assert gdpr_report["status"] == "compliant"
        assert pci_report["overall_score"] == 100.0
        assert pci_report["status"] == "compliant"

        # 7. Check dashboard
        dashboard = manager.get_compliance_dashboard(consortium.id)

        assert dashboard["overall_score"] == 100.0
        assert dashboard["overall_status"] == "compliant"
        assert dashboard["enabled_frameworks_count"] == 2
