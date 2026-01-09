"""Tests for TIER 3 Data Quality Score feature.

Tests cover:
- Data quality assessments
- Quality metrics (completeness, consistency, uniqueness, validity, freshness)
- Quality rules
- Quality alerts
- Quality dashboard
"""

import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

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
    "sdk.api.consortium", consortium_package_path / "__init__.py"
)
ConsortiumManager = consortium_module.ConsortiumManager
ConsortiumStatus = consortium_module.ConsortiumStatus
MemberRole = consortium_module.MemberRole
MemberStatus = consortium_module.MemberStatus


class TestDataQualityAssessment:
    """Tests for data quality assessment functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_quality.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium with members for testing."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        member, _ = manager.create_company("Member Corp", "member@test.com")

        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing data quality",
            owner_id=owner.id,
            model_type="linear_regression",
        )

        invitation = manager.create_invitation(
            consortium_id=consortium.id,
            invited_by=owner.id,
            invite_email="member@test.com",
            role=MemberRole.CONTRIBUTOR,
        )
        manager.accept_invitation(invitation.invite_code, member.id)

        return {"consortium": consortium, "owner": owner, "member": member}

    def test_assess_data_quality_basic(self, manager, setup_consortium):
        """Test basic data quality assessment."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        assessment = manager.assess_data_quality(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=1000,
            feature_count=10,
            null_count=50,
            duplicate_count=20,
            outlier_count=30,
        )

        assert assessment is not None
        assert "id" in assessment
        assert assessment["consortium_id"] == consortium.id
        assert assessment["company_id"] == owner.id
        assert "overall_score" in assessment

    def test_assess_data_quality_scores_calculation(self, manager, setup_consortium):
        """Test that quality scores are calculated correctly."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # 10000 records, 10 features = 100000 cells
        # 1000 nulls = 1% null ratio = 99% completeness
        assessment = manager.assess_data_quality(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=10000,
            feature_count=10,
            null_count=1000,  # 1% nulls
            duplicate_count=500,  # 5% duplicates
            outlier_count=300,  # 0.3% outliers
        )

        # Completeness = 1 - (1000 / 100000) = 0.99 = 99%
        assert abs(assessment["scores"]["completeness"] - 99.0) < 0.1

        # Uniqueness = 1 - (500 / 10000) = 0.95 = 95%
        assert abs(assessment["scores"]["uniqueness"] - 95.0) < 0.1

        # Validity is calculated differently - includes outliers relative to records
        # Validity = 1 - (outlier_count / record_count) = 1 - (300 / 10000) = 0.97 = 97%
        assert assessment["scores"]["validity"] > 95.0

    def test_assess_data_quality_perfect_data(self, manager, setup_consortium):
        """Test assessment with perfect data (no issues)."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        assessment = manager.assess_data_quality(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=1000,
            feature_count=10,
            null_count=0,
            duplicate_count=0,
            outlier_count=0,
        )

        assert assessment["scores"]["completeness"] == 100.0
        assert assessment["scores"]["uniqueness"] == 100.0
        assert assessment["scores"]["validity"] == 100.0
        assert assessment["overall_score"] >= 95.0  # High score

    def test_assess_data_quality_metrics(self, manager, setup_consortium):
        """Test assessment includes correct metrics."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        assessment = manager.assess_data_quality(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=500,
            feature_count=5,
            null_count=50,
            duplicate_count=10,
            outlier_count=5,
        )

        assert "metrics" in assessment
        assert assessment["metrics"]["record_count"] == 500
        assert assessment["metrics"]["feature_count"] == 5


class TestGetQualityAssessments:
    """Tests for retrieving quality assessments."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_quality_get.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_with_assessments(self, manager):
        """Create consortium with multiple assessments."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        member, _ = manager.create_company("Member Corp", "member@test.com")

        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing",
            owner_id=owner.id,
            model_type="linear_regression",
        )

        invitation = manager.create_invitation(
            consortium_id=consortium.id, invited_by=owner.id, invite_email="member@test.com"
        )
        manager.accept_invitation(invitation.invite_code, member.id)

        # Create assessments for both companies
        for i in range(3):
            manager.assess_data_quality(
                consortium_id=consortium.id,
                company_id=owner.id,
                record_count=1000 * (i + 1),
                feature_count=10,
            )

        for i in range(2):
            manager.assess_data_quality(
                consortium_id=consortium.id,
                company_id=member.id,
                record_count=500 * (i + 1),
                feature_count=8,
            )

        return {"consortium": consortium, "owner": owner, "member": member}

    def test_get_all_assessments(self, manager, setup_with_assessments):
        """Test getting all assessments for a consortium."""
        consortium = setup_with_assessments["consortium"]

        assessments = manager.get_quality_assessments(consortium.id)

        assert len(assessments) == 5  # 3 + 2

    def test_get_assessments_by_company(self, manager, setup_with_assessments):
        """Test filtering assessments by company."""
        consortium = setup_with_assessments["consortium"]
        owner = setup_with_assessments["owner"]

        assessments = manager.get_quality_assessments(consortium.id, company_id=owner.id)

        assert len(assessments) == 3
        for a in assessments:
            assert a["company_id"] == owner.id

    def test_get_assessments_with_limit(self, manager, setup_with_assessments):
        """Test limiting number of assessments returned."""
        consortium = setup_with_assessments["consortium"]

        assessments = manager.get_quality_assessments(consortium.id, limit=2)

        assert len(assessments) == 2


class TestQualityRules:
    """Tests for quality rules functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_quality_rules.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium for testing."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing rules",
            owner_id=owner.id,
            model_type="linear_regression",
        )
        return {"consortium": consortium, "owner": owner}

    def test_set_quality_rule(self, manager, setup_consortium):
        """Test setting a quality rule."""
        consortium = setup_consortium["consortium"]

        rule_id = manager.set_quality_rule(
            consortium_id=consortium.id,
            rule_name="completeness_min",
            rule_type="completeness",
            threshold_min=90.0,
            weight=1.0,
        )

        assert rule_id is not None
        assert rule_id.startswith("rule_")

    def test_get_quality_rules(self, manager, setup_consortium):
        """Test getting all quality rules for a consortium."""
        consortium = setup_consortium["consortium"]

        # Set rules for multiple metrics
        metrics = ["completeness", "consistency", "uniqueness", "validity", "freshness"]
        for metric in metrics:
            manager.set_quality_rule(
                consortium_id=consortium.id,
                rule_name=f"{metric}_threshold",
                rule_type=metric,
                threshold_min=85.0,
                weight=1.0,
            )

        rules = manager.get_quality_rules(consortium.id)

        assert len(rules) == 5


class TestQualityAlerts:
    """Tests for quality alerts functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_quality_alerts.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium(self, manager):
        """Create a consortium for testing."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing alerts",
            owner_id=owner.id,
            model_type="linear_regression",
        )
        return {"consortium": consortium, "owner": owner}

    def test_get_quality_alerts_empty(self, manager, setup_consortium):
        """Test getting alerts when none exist."""
        consortium = setup_consortium["consortium"]

        alerts = manager.get_quality_alerts(consortium.id)

        assert isinstance(alerts, list)
        assert len(alerts) == 0

    def test_create_and_get_alerts(self, manager, setup_consortium):
        """Test creating assessments that may generate alerts."""
        consortium = setup_consortium["consortium"]
        owner = setup_consortium["owner"]

        # Create assessment with low quality
        manager.assess_data_quality(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=1000,
            feature_count=10,
            null_count=5000,  # 50% nulls - very low completeness
            duplicate_count=400,  # 40% duplicates
            outlier_count=2000,
        )

        # Alerts may or may not be generated depending on rules
        alerts = manager.get_quality_alerts(consortium.id)
        assert isinstance(alerts, list)


class TestQualityHistory:
    """Tests for quality metrics history."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_quality_history.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_with_history(self, manager):
        """Create consortium with historical assessments."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing history",
            owner_id=owner.id,
            model_type="linear_regression",
        )

        # Create several assessments to generate history
        for i in range(5):
            manager.assess_data_quality(
                consortium_id=consortium.id,
                company_id=owner.id,
                record_count=1000,
                feature_count=10,
                null_count=100 * (5 - i),  # Improving quality
                duplicate_count=50 * (5 - i),
                outlier_count=30 * (5 - i),
            )

        return {"consortium": consortium, "owner": owner}

    def test_get_quality_history(self, manager, setup_with_history):
        """Test getting quality history."""
        consortium = setup_with_history["consortium"]

        history = manager.get_quality_history(consortium.id)

        assert len(history) > 0

    def test_get_quality_history_by_company(self, manager, setup_with_history):
        """Test filtering history by company."""
        consortium = setup_with_history["consortium"]
        owner = setup_with_history["owner"]

        history = manager.get_quality_history(consortium.id, company_id=owner.id)

        for entry in history:
            assert entry["company_id"] == owner.id


class TestQualityDashboard:
    """Tests for quality dashboard functionality."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_quality_dashboard.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    @pytest.fixture
    def setup_consortium_with_quality(self, manager):
        """Create a consortium with quality data from multiple companies."""
        owner, _ = manager.create_company("Owner Corp", "owner@test.com")
        member1, _ = manager.create_company("Member One", "member1@test.com")
        member2, _ = manager.create_company("Member Two", "member2@test.com")

        consortium = manager.create_consortium(
            name="Test Consortium",
            description="Testing dashboard",
            owner_id=owner.id,
            model_type="linear_regression",
        )

        # Add members
        for member in [member1, member2]:
            invitation = manager.create_invitation(
                consortium_id=consortium.id,
                invited_by=owner.id,
                invite_email=f"{member.name.lower().replace(' ', '')}@test.com",
            )
            manager.accept_invitation(invitation.invite_code, member.id)

        # Create assessments for each company
        manager.assess_data_quality(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=10000,
            feature_count=10,
            null_count=500,  # 99.5% completeness
            duplicate_count=100,  # 99% uniqueness
            outlier_count=200,  # 99.8% validity
        )

        manager.assess_data_quality(
            consortium_id=consortium.id,
            company_id=member1.id,
            record_count=8000,
            feature_count=10,
            null_count=4000,  # 95% completeness
            duplicate_count=800,  # 90% uniqueness
            outlier_count=400,  # 99.5% validity
        )

        manager.assess_data_quality(
            consortium_id=consortium.id,
            company_id=member2.id,
            record_count=5000,
            feature_count=10,
            null_count=2500,  # 95% completeness
            duplicate_count=250,  # 95% uniqueness
            outlier_count=150,  # 99.7% validity
        )

        return {"consortium": consortium, "owner": owner, "member1": member1, "member2": member2}

    def test_get_quality_dashboard(self, manager, setup_consortium_with_quality):
        """Test getting quality dashboard."""
        consortium = setup_consortium_with_quality["consortium"]

        dashboard = manager.get_consortium_quality_dashboard(consortium.id)

        assert dashboard["consortium_id"] == consortium.id
        assert "overall_score" in dashboard
        assert "member_count" in dashboard

    def test_dashboard_overall_score(self, manager, setup_consortium_with_quality):
        """Test dashboard overall score calculation."""
        consortium = setup_consortium_with_quality["consortium"]

        dashboard = manager.get_consortium_quality_dashboard(consortium.id)

        # Overall score should be average of all companies
        assert dashboard["overall_score"] > 0
        assert dashboard["overall_score"] <= 100

    def test_dashboard_score_breakdown(self, manager, setup_consortium_with_quality):
        """Test dashboard shows correct score breakdown."""
        consortium = setup_consortium_with_quality["consortium"]

        dashboard = manager.get_consortium_quality_dashboard(consortium.id)

        assert "score_breakdown" in dashboard
        assert "completeness" in dashboard["score_breakdown"]
        assert "consistency" in dashboard["score_breakdown"]
        assert "uniqueness" in dashboard["score_breakdown"]
        assert "validity" in dashboard["score_breakdown"]
        assert "freshness" in dashboard["score_breakdown"]

    def test_dashboard_members(self, manager, setup_consortium_with_quality):
        """Test dashboard includes member-level data."""
        consortium = setup_consortium_with_quality["consortium"]

        dashboard = manager.get_consortium_quality_dashboard(consortium.id)

        assert "members" in dashboard
        assert dashboard["member_count"] == 3

    def test_dashboard_empty_consortium(self, manager):
        """Test dashboard with no assessments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_empty.db"
            mgr = ConsortiumManager(db_path)

            owner, _ = mgr.create_company("Owner Corp", "owner@test.com")
            consortium = mgr.create_consortium(
                name="Empty Consortium",
                description="No data",
                owner_id=owner.id,
                model_type="linear_regression",
            )

            dashboard = mgr.get_consortium_quality_dashboard(consortium.id)

            assert dashboard["member_count"] == 0
            assert dashboard["overall_score"] == 0


class TestDataQualityIntegration:
    """Integration tests for data quality workflow."""

    @pytest.fixture
    def manager(self):
        """Create a manager with temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_integration.db"
            mgr = ConsortiumManager(db_path)
            yield mgr

    def test_full_quality_workflow(self, manager):
        """Test complete data quality workflow."""
        # 1. Create consortium
        owner, _ = manager.create_company("Data Corp", "data@corp.com")
        consortium = manager.create_consortium(
            name="Quality Consortium",
            description="Testing data quality",
            owner_id=owner.id,
            model_type="linear_regression",
        )

        # 2. Set quality rules
        metrics = ["completeness", "consistency", "uniqueness", "validity", "freshness"]

        for metric in metrics:
            manager.set_quality_rule(
                consortium_id=consortium.id,
                rule_name=f"{metric}_threshold",
                rule_type=metric,
                threshold_min=80.0,
                weight=1.0,
            )

        rules = manager.get_quality_rules(consortium.id)
        assert len(rules) == 5

        # 3. First assessment - good quality
        assessment1 = manager.assess_data_quality(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=10000,
            feature_count=10,
            null_count=100,  # 99.9% completeness
            duplicate_count=50,  # 99.5% uniqueness
            outlier_count=100,  # 99.9% validity
        )

        assert assessment1["overall_score"] > 95

        # 4. Second assessment - lower quality
        assessment2 = manager.assess_data_quality(
            consortium_id=consortium.id,
            company_id=owner.id,
            record_count=10000,
            feature_count=10,
            null_count=8000,  # 92% completeness
            duplicate_count=1500,  # 85% uniqueness
            outlier_count=1000,  # 99% validity
        )

        # Second assessment should have lower score
        assert assessment2["overall_score"] < assessment1["overall_score"]

        # 5. Check dashboard
        dashboard = manager.get_consortium_quality_dashboard(consortium.id)

        assert dashboard["member_count"] == 1  # Just owner
        assert dashboard["overall_score"] > 0

        # 6. Check history
        history = manager.get_quality_history(consortium.id)
        assert len(history) > 0

    def test_multi_company_quality_comparison(self, manager):
        """Test comparing quality across multiple companies."""
        # Create consortium with multiple members
        companies = []
        owner, _ = manager.create_company("Bank Alpha", "alpha@bank.com")
        companies.append(("Bank Alpha", owner))

        consortium = manager.create_consortium(
            name="Banking Consortium",
            description="Multi-bank quality",
            owner_id=owner.id,
            model_type="linear_regression",
        )

        # Add more members
        for name in ["Bank Beta", "Bank Gamma"]:
            company, _ = manager.create_company(name, f"{name.lower().replace(' ', '')}@bank.com")
            invitation = manager.create_invitation(
                consortium_id=consortium.id,
                invited_by=owner.id,
                invite_email=f"{name.lower().replace(' ', '')}@bank.com",
            )
            manager.accept_invitation(invitation.invite_code, company.id)
            companies.append((name, company))

        # Each company contributes with different quality levels
        quality_levels = [
            {"null_count": 100, "duplicate_count": 50, "outlier_count": 100},  # High quality
            {"null_count": 5000, "duplicate_count": 2000, "outlier_count": 1500},  # Medium quality
            {"null_count": 15000, "duplicate_count": 4000, "outlier_count": 3000},  # Lower quality
        ]

        assessments = []
        for (_name, company), quality in zip(companies, quality_levels):
            assessment = manager.assess_data_quality(
                consortium_id=consortium.id,
                company_id=company.id,
                record_count=10000,
                feature_count=10,
                **quality,
            )
            assessments.append(assessment)

        # Get dashboard
        dashboard = manager.get_consortium_quality_dashboard(consortium.id)

        assert dashboard["member_count"] == 3

        # Companies should have different scores
        members = dashboard["members"]
        scores = [m["overall_score"] for m in members]
        assert len(set(scores)) > 1  # Not all the same

        # Highest quality company should have highest score
        first_assessment = assessments[0]
        last_assessment = assessments[2]
        assert first_assessment["overall_score"] > last_assessment["overall_score"]
