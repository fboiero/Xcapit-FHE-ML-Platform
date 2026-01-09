"""
Data quality operations for consortium management.

This module handles all data quality-related functionality including:
- Quality assessments
- Quality metrics and scoring
- Quality rules and thresholds
- Quality alerts
- Quality dashboards
"""

import json
import secrets
from datetime import datetime
from typing import Optional

from .database import DatabaseManager


class DataQualityManager:
    """Manages data quality operations for consortiums."""

    def __init__(self, db_path: str = "fhe_platform.db", core_manager=None):
        """Initialize data quality manager.

        Args:
            db_path: Path to SQLite database.
            core_manager: Optional CoreManager instance for company lookups.
        """
        self._db = DatabaseManager(db_path)
        self._core_manager = core_manager

    def _get_connection(self):
        """Get database connection."""
        return self._db.get_connection()

    def _init_data_quality_schema(self):
        """Initialize data quality schema."""
        self._db.init_data_quality_schema()

    def get_company(self, company_id: str):
        """Get company via core manager if available."""
        if self._core_manager:
            return self._core_manager.get_company(company_id)
        return None

    def assess_data_quality(
        self,
        consortium_id: str,
        company_id: str,
        contribution_id: Optional[str] = None,
        record_count: int = 0,
        feature_count: int = 0,
        null_count: int = 0,
        duplicate_count: int = 0,
        outlier_count: int = 0,
        schema_violations: int = 0,
        format_violations: int = 0,
        range_violations: int = 0,
        last_updated: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Assess data quality for a contribution.

        Calculates quality scores based on encrypted data metadata
        without accessing the actual data content. Uses the DataQualityCalculator
        for real metric calculations.

        Args:
            consortium_id: Consortium ID.
            company_id: Company ID.
            contribution_id: Optional contribution ID.
            record_count: Number of records.
            feature_count: Number of features.
            null_count: Count of null/missing values.
            duplicate_count: Count of duplicate records.
            outlier_count: Count of outlier values.
            schema_violations: Records with schema issues.
            format_violations: Records with format issues.
            range_violations: Records with out-of-range values.
            last_updated: When the data was last updated.
            metadata: Additional metadata.

        Returns:
            Assessment results with scores.
        """
        # Import quality calculator directly to avoid TenSEAL dependency via sdk.__init__
        import importlib.util
        import sys
        from pathlib import Path as PathLib

        quality_module_path = PathLib(__file__).parent.parent.parent / "quality" / "calculator.py"
        spec = importlib.util.spec_from_file_location("sdk_quality_calculator", quality_module_path)
        quality_module = importlib.util.module_from_spec(spec)
        sys.modules["sdk_quality_calculator"] = quality_module
        spec.loader.exec_module(quality_module)
        DataQualityCalculator = quality_module.DataQualityCalculator
        DataProfile = quality_module.DataProfile

        self._init_data_quality_schema()
        assessment_id = f"dqa_{secrets.token_hex(8)}"

        # Use DataQualityCalculator for real calculations
        calculator = DataQualityCalculator(freshness_threshold_days=30)

        # Create a DataProfile from the input metadata
        profile = DataProfile(
            record_count=record_count,
            feature_count=feature_count,
            duplicate_count=duplicate_count,
            outlier_count=outlier_count,
            schema_violations=schema_violations,
            format_violations=format_violations,
            range_violations=range_violations,
            last_updated=last_updated or datetime.utcnow(),
        )

        # Distribute nulls evenly across features if only total is provided
        if null_count > 0 and feature_count > 0:
            nulls_per_feature = null_count // feature_count
            for i in range(feature_count):
                profile.null_counts[f"feature_{i}"] = nulls_per_feature

        # Get quality score using the real calculator
        quality_score = calculator.assess_quality(profile)

        # Calculate ratios for storage
        total_cells = record_count * feature_count if record_count and feature_count else 1
        null_ratio = null_count / total_cells if total_cells > 0 else 0
        duplicate_ratio = duplicate_count / record_count if record_count > 0 else 0
        outlier_ratio = outlier_count / total_cells if total_cells > 0 else 0

        # Get rules for custom weighted average if configured
        rules = self.get_quality_rules(consortium_id)
        if rules:
            weights = {r["rule_type"]: r["weight"] for r in rules if r["is_active"]}
            # Recalculate overall with custom weights if rules exist
            overall_score = calculator.calculate_overall(
                quality_score.completeness,
                quality_score.consistency,
                quality_score.uniqueness,
                quality_score.validity,
                quality_score.freshness,
                weights,
            )
        else:
            overall_score = quality_score.overall

        # Use calculated scores
        scores = {
            "completeness": quality_score.completeness,
            "consistency": quality_score.consistency,
            "uniqueness": quality_score.uniqueness,
            "validity": quality_score.validity,
            "freshness": quality_score.freshness,
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO data_quality_assessments
                (id, consortium_id, company_id, contribution_id, overall_score,
                 completeness_score, consistency_score, uniqueness_score,
                 validity_score, freshness_score, record_count, feature_count,
                 null_ratio, duplicate_ratio, outlier_ratio, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    assessment_id,
                    consortium_id,
                    company_id,
                    contribution_id,
                    round(overall_score, 2),
                    round(scores["completeness"], 2),
                    round(scores["consistency"], 2),
                    round(scores["uniqueness"], 2),
                    round(scores["validity"], 2),
                    round(scores["freshness"], 2),
                    record_count,
                    feature_count,
                    round(null_ratio, 4),
                    round(duplicate_ratio, 4),
                    round(outlier_ratio, 4),
                    json.dumps(metadata or {}),
                ),
            )

            # Record metrics history
            for metric_type, value in scores.items():
                history_id = f"dqh_{secrets.token_hex(8)}"
                cursor.execute(
                    """
                    INSERT INTO data_quality_history
                    (id, consortium_id, company_id, metric_type, metric_value)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (history_id, consortium_id, company_id, metric_type, value),
                )

            conn.commit()

        # Check for alerts
        self._check_quality_alerts(
            consortium_id, company_id, scores, null_ratio, duplicate_ratio, outlier_ratio
        )

        # Return format matching QualityAssessmentResponse
        return {
            "id": assessment_id,
            "consortium_id": consortium_id,
            "company_id": company_id,
            "contribution_id": contribution_id,
            "overall_score": round(overall_score, 2),
            "completeness_score": scores["completeness"],
            "consistency_score": scores["consistency"],
            "uniqueness_score": scores["uniqueness"],
            "validity_score": scores["validity"],
            "freshness_score": scores["freshness"],
            "record_count": record_count,
            "feature_count": feature_count,
            "null_ratio": round(null_ratio * 100, 2),
            "duplicate_ratio": round(duplicate_ratio * 100, 2),
            "outlier_ratio": round(outlier_ratio * 100, 2),
            "assessed_at": datetime.utcnow(),
            "metadata": metadata,
            # Additional nested structure for tests
            "scores": scores,
            "metrics": {
                "record_count": record_count,
                "feature_count": feature_count,
                "null_ratio": round(null_ratio * 100, 2),
                "duplicate_ratio": round(duplicate_ratio * 100, 2),
                "outlier_ratio": round(outlier_ratio * 100, 2),
            },
        }

    def _check_quality_alerts(
        self,
        consortium_id: str,
        company_id: str,
        scores: dict[str, float],
        null_ratio: float,
        duplicate_ratio: float,
        outlier_ratio: float,
    ):
        """Check and create quality alerts based on thresholds."""
        alerts = []

        # Default thresholds
        if scores["completeness"] < 80:
            alerts.append(
                {
                    "alert_type": "low_completeness",
                    "severity": "warning" if scores["completeness"] >= 60 else "critical",
                    "message": f"Data completeness is below threshold ({scores['completeness']:.1f}%)",
                    "metric_name": "completeness",
                    "metric_value": scores["completeness"],
                    "threshold_value": 80,
                }
            )

        if scores["uniqueness"] < 90:
            alerts.append(
                {
                    "alert_type": "high_duplicates",
                    "severity": "warning" if scores["uniqueness"] >= 70 else "critical",
                    "message": f"High duplicate ratio detected ({duplicate_ratio * 100:.1f}%)",
                    "metric_name": "uniqueness",
                    "metric_value": scores["uniqueness"],
                    "threshold_value": 90,
                }
            )

        if scores["validity"] < 85:
            alerts.append(
                {
                    "alert_type": "data_quality_issue",
                    "severity": "warning" if scores["validity"] >= 70 else "critical",
                    "message": f"Data validity issues detected ({outlier_ratio * 100:.1f}% outliers)",
                    "metric_name": "validity",
                    "metric_value": scores["validity"],
                    "threshold_value": 85,
                }
            )

        # Create alerts
        for alert in alerts:
            self._create_quality_alert(consortium_id, company_id, alert)

    def _create_quality_alert(self, consortium_id: str, company_id: str, alert_data: dict) -> str:
        """Create a data quality alert."""
        alert_id = f"alert_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO data_quality_alerts
                (id, consortium_id, company_id, alert_type, severity, message,
                 metric_name, metric_value, threshold_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    alert_id,
                    consortium_id,
                    company_id,
                    alert_data["alert_type"],
                    alert_data["severity"],
                    alert_data["message"],
                    alert_data.get("metric_name"),
                    alert_data.get("metric_value"),
                    alert_data.get("threshold_value"),
                ),
            )

        return alert_id

    def get_quality_assessments(
        self, consortium_id: str, company_id: Optional[str] = None, limit: int = 100
    ) -> list[dict]:
        """Get quality assessments for a consortium."""
        self._init_data_quality_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT dqa.*, c.name as company_name
                FROM data_quality_assessments dqa
                JOIN companies c ON dqa.company_id = c.id
                WHERE dqa.consortium_id = ?
            """
            params = [consortium_id]

            if company_id:
                query += " AND dqa.company_id = ?"
                params.append(company_id)

            query += " ORDER BY dqa.assessed_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            if r.get("metadata"):
                r["metadata"] = json.loads(r["metadata"])
            result.append(r)

        return result

    def get_latest_quality_assessment(self, consortium_id: str, company_id: str) -> Optional[dict]:
        """Get the latest quality assessment for a company."""
        assessments = self.get_quality_assessments(consortium_id, company_id=company_id, limit=1)
        return assessments[0] if assessments else None

    def get_quality_history(
        self,
        consortium_id: str,
        company_id: Optional[str] = None,
        metric_type: Optional[str] = None,
        days: int = 30,
    ) -> list[dict]:
        """Get quality metrics history."""
        self._init_data_quality_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT * FROM data_quality_history
                WHERE consortium_id = ?
                AND recorded_at >= datetime('now', ?)
            """
            params = [consortium_id, f"-{days} days"]

            if company_id:
                query += " AND company_id = ?"
                params.append(company_id)

            if metric_type:
                query += " AND metric_type = ?"
                params.append(metric_type)

            query += " ORDER BY recorded_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_quality_rules(self, consortium_id: str) -> list[dict]:
        """Get quality rules for a consortium."""
        self._init_data_quality_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM data_quality_rules
                WHERE consortium_id = ?
                ORDER BY rule_type
            """,
                (consortium_id,),
            )
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def set_quality_rule(
        self,
        consortium_id: str,
        rule_name: str,
        rule_type: str,
        threshold_min: Optional[float] = None,
        threshold_max: Optional[float] = None,
        weight: float = 1.0,
    ) -> str:
        """Set or update a quality rule."""
        self._init_data_quality_schema()
        rule_id = f"rule_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO data_quality_rules
                (id, consortium_id, rule_name, rule_type, threshold_min, threshold_max, weight)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(consortium_id, rule_name) DO UPDATE SET
                    threshold_min = excluded.threshold_min,
                    threshold_max = excluded.threshold_max,
                    weight = excluded.weight
            """,
                (
                    rule_id,
                    consortium_id,
                    rule_name,
                    rule_type,
                    threshold_min,
                    threshold_max,
                    weight,
                ),
            )

        return rule_id

    def get_quality_alerts(
        self,
        consortium_id: str,
        company_id: Optional[str] = None,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get quality alerts for a consortium."""
        self._init_data_quality_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT a.*, c.name as company_name
                FROM data_quality_alerts a
                JOIN companies c ON a.company_id = c.id
                WHERE a.consortium_id = ?
            """
            params = [consortium_id]

            if company_id:
                query += " AND a.company_id = ?"
                params.append(company_id)

            if severity:
                query += " AND a.severity = ?"
                params.append(severity)

            if acknowledged is not None:
                query += " AND a.acknowledged = ?"
                params.append(1 if acknowledged else 0)

            query += " ORDER BY a.created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge a quality alert."""
        self._init_data_quality_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE data_quality_alerts
                SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
                WHERE id = ?
            """,
                (acknowledged_by, datetime.utcnow(), alert_id),
            )

        return True

    def get_consortium_quality_dashboard(self, consortium_id: str) -> dict:
        """Get data quality dashboard for a consortium.

        Returns aggregate quality metrics across all members.
        """
        self._init_data_quality_schema()

        # Get latest assessments per company
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get unique companies with assessments
            cursor.execute(
                """
                SELECT DISTINCT company_id FROM data_quality_assessments
                WHERE consortium_id = ?
            """,
                (consortium_id,),
            )
            companies = [row["company_id"] for row in cursor.fetchall()]

        if not companies:
            return {
                "consortium_id": consortium_id,
                "overall_score": 0,
                "member_count": 0,
                "members": [],
                "alerts_count": {"critical": 0, "warning": 0},
                "score_breakdown": {
                    "completeness": 0,
                    "consistency": 0,
                    "uniqueness": 0,
                    "validity": 0,
                    "freshness": 0,
                },
            }

        # Get latest assessment for each company
        members = []
        total_scores = {
            "overall": 0,
            "completeness": 0,
            "consistency": 0,
            "uniqueness": 0,
            "validity": 0,
            "freshness": 0,
        }

        for company_id in companies:
            assessment = self.get_latest_quality_assessment(consortium_id, company_id)
            if assessment:
                company = self.get_company(company_id)
                members.append(
                    {
                        "company_id": company_id,
                        "company_name": company.name if company else "Unknown",
                        "overall_score": assessment["overall_score"],
                        "completeness": assessment["completeness_score"],
                        "consistency": assessment["consistency_score"],
                        "uniqueness": assessment["uniqueness_score"],
                        "validity": assessment["validity_score"],
                        "freshness": assessment["freshness_score"],
                        "record_count": assessment["record_count"],
                        "assessed_at": assessment["assessed_at"],
                    }
                )
                total_scores["overall"] += assessment["overall_score"]
                total_scores["completeness"] += assessment["completeness_score"]
                total_scores["consistency"] += assessment["consistency_score"]
                total_scores["uniqueness"] += assessment["uniqueness_score"]
                total_scores["validity"] += assessment["validity_score"]
                total_scores["freshness"] += assessment["freshness_score"]

        member_count = len(members)
        avg_scores = {
            k: round(v / member_count, 2) if member_count > 0 else 0
            for k, v in total_scores.items()
        }

        # Get alerts count
        alerts = self.get_quality_alerts(consortium_id, acknowledged=False)
        alerts_count = {
            "critical": sum(1 for a in alerts if a["severity"] == "critical"),
            "warning": sum(1 for a in alerts if a["severity"] == "warning"),
        }

        return {
            "consortium_id": consortium_id,
            "overall_score": avg_scores["overall"],
            "member_count": member_count,
            "members": sorted(members, key=lambda x: x["overall_score"], reverse=True),
            "alerts_count": alerts_count,
            "score_breakdown": {
                "completeness": avg_scores["completeness"],
                "consistency": avg_scores["consistency"],
                "uniqueness": avg_scores["uniqueness"],
                "validity": avg_scores["validity"],
                "freshness": avg_scores["freshness"],
            },
        }


# Export all public classes and functions
__all__ = ["DataQualityManager"]
