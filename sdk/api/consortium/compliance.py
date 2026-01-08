"""
Compliance operations for consortium management.

This module handles all compliance-related functionality including:
- Compliance frameworks management
- Compliance checks and reports
- Attestations
- Data processing records (GDPR Article 30)
- Compliance dashboards
"""

import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .database import DatabaseManager


class ComplianceManager:
    """Manages compliance operations for consortiums."""

    def __init__(self, db_path: str = "fhe_platform.db"):
        """Initialize compliance manager.

        Args:
            db_path: Path to SQLite database.
        """
        self._db = DatabaseManager(db_path)

    def _get_connection(self):
        """Get database connection."""
        return self._db.get_connection()

    def _init_compliance_schema(self):
        """Initialize compliance schema."""
        self._db.init_compliance_schema()

    def get_compliance_frameworks(self) -> List[Dict]:
        """Get all available compliance frameworks."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM compliance_frameworks ORDER BY name")
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_compliance_framework(self, framework_id: str) -> Optional[Dict]:
        """Get a specific compliance framework."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM compliance_frameworks WHERE id = ?", (framework_id,))
            row = cursor.fetchone()

        return dict(row) if row else None

    def enable_compliance_framework(
        self,
        consortium_id: str,
        framework_id: str
    ) -> Dict:
        """Enable a compliance framework for a consortium.

        Args:
            consortium_id: Consortium ID.
            framework_id: Framework ID to enable.

        Returns:
            Updated compliance settings.
        """
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get or create settings
            cursor.execute("""
                SELECT enabled_frameworks FROM consortium_compliance_settings
                WHERE consortium_id = ?
            """, (consortium_id,))
            row = cursor.fetchone()

            if row:
                enabled = json.loads(row["enabled_frameworks"])
                if framework_id not in enabled:
                    enabled.append(framework_id)
                cursor.execute("""
                    UPDATE consortium_compliance_settings
                    SET enabled_frameworks = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE consortium_id = ?
                """, (json.dumps(enabled), consortium_id))
            else:
                settings_id = f"compl_settings_{secrets.token_hex(8)}"
                enabled = [framework_id]
                cursor.execute("""
                    INSERT INTO consortium_compliance_settings
                    (id, consortium_id, enabled_frameworks)
                    VALUES (?, ?, ?)
                """, (settings_id, consortium_id, json.dumps(enabled)))

            conn.commit()

        return {"consortium_id": consortium_id, "enabled_frameworks": enabled}

    def get_consortium_compliance_settings(self, consortium_id: str) -> Dict:
        """Get compliance settings for a consortium."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM consortium_compliance_settings WHERE consortium_id = ?
            """, (consortium_id,))
            row = cursor.fetchone()

        if not row:
            return {
                "consortium_id": consortium_id,
                "enabled_frameworks": [],
                "auto_check_interval": 86400,
                "notification_emails": [],
                "settings": {}
            }

        result = dict(row)
        result["enabled_frameworks"] = json.loads(result["enabled_frameworks"])
        result["notification_emails"] = json.loads(result["notification_emails"])
        result["settings"] = json.loads(result["settings"])
        return result

    def record_compliance_check(
        self,
        consortium_id: str,
        framework_id: str,
        control_id: str,
        status: str,
        result: str,
        evidence: Optional[Dict] = None,
        checked_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """Record a compliance check result.

        Args:
            consortium_id: Consortium ID.
            framework_id: Framework ID.
            control_id: Control ID.
            status: Check status (passed, failed, pending, na).
            result: Result description.
            evidence: Evidence data.
            checked_by: Checker company ID.
            notes: Additional notes.

        Returns:
            Check ID.
        """
        self._init_compliance_schema()
        check_id = f"check_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compliance_checks
                (id, consortium_id, framework_id, control_id, status, result, evidence, checked_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                check_id,
                consortium_id,
                framework_id,
                control_id,
                status,
                result,
                json.dumps(evidence) if evidence else None,
                checked_by,
                notes
            ))

        return check_id

    def get_compliance_checks(
        self,
        consortium_id: str,
        framework_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """Get compliance checks for a consortium.

        Args:
            consortium_id: Consortium ID.
            framework_id: Optional framework filter.
            status: Optional status filter.

        Returns:
            List of compliance checks.
        """
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM compliance_checks WHERE consortium_id = ?"
            params = [consortium_id]

            if framework_id:
                query += " AND framework_id = ?"
                params.append(framework_id)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY checked_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            if r.get("evidence"):
                r["evidence"] = json.loads(r["evidence"])
            result.append(r)

        return result

    def generate_compliance_report(
        self,
        consortium_id: str,
        framework_id: str
    ) -> Dict:
        """Generate a compliance report for a consortium.

        Args:
            consortium_id: Consortium ID.
            framework_id: Framework ID.

        Returns:
            Generated report.
        """
        self._init_compliance_schema()

        checks = self.get_compliance_checks(consortium_id, framework_id)

        passed = sum(1 for c in checks if c["status"] == "passed")
        failed = sum(1 for c in checks if c["status"] == "failed")
        pending = sum(1 for c in checks if c["status"] == "pending")
        total = len(checks)

        score = (passed / total * 100) if total > 0 else 0
        status = "compliant" if failed == 0 and pending == 0 and total > 0 else "non_compliant"

        report_id = f"report_{secrets.token_hex(8)}"
        now = datetime.utcnow()
        valid_until = now + timedelta(days=90)

        # Serialize checks for JSON storage (convert datetime to string)
        serialized_checks = []
        for check in checks:
            sc = dict(check)
            if sc.get("checked_at") and hasattr(sc["checked_at"], "isoformat"):
                sc["checked_at"] = sc["checked_at"].isoformat()
            if sc.get("expires_at") and hasattr(sc["expires_at"], "isoformat"):
                sc["expires_at"] = sc["expires_at"].isoformat()
            serialized_checks.append(sc)

        report_data = {
            "checks": serialized_checks,
            "summary": {
                "passed": passed,
                "failed": failed,
                "pending": pending,
                "total": total,
                "score": round(score, 2)
            }
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compliance_reports
                (id, consortium_id, framework_id, overall_score, passed_controls,
                 failed_controls, pending_controls, total_controls, status, valid_until, report_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                consortium_id,
                framework_id,
                score,
                passed,
                failed,
                pending,
                total,
                status,
                valid_until,
                json.dumps(report_data)
            ))

        return {
            "id": report_id,
            "consortium_id": consortium_id,
            "framework_id": framework_id,
            "overall_score": round(score, 2),
            "passed_controls": passed,
            "failed_controls": failed,
            "pending_controls": pending,
            "total_controls": total,
            "status": status,
            "generated_at": now.isoformat(),
            "valid_until": valid_until.isoformat(),
            "report_data": report_data
        }

    def get_compliance_reports(
        self,
        consortium_id: str,
        framework_id: Optional[str] = None
    ) -> List[Dict]:
        """Get compliance reports for a consortium."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT r.*, f.name as framework_name
                FROM compliance_reports r
                JOIN compliance_frameworks f ON r.framework_id = f.id
                WHERE r.consortium_id = ?
            """
            params = [consortium_id]

            if framework_id:
                query += " AND r.framework_id = ?"
                params.append(framework_id)

            query += " ORDER BY r.generated_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            if r.get("report_data"):
                r["report_data"] = json.loads(r["report_data"])
            result.append(r)

        return result

    def create_attestation(
        self,
        consortium_id: str,
        framework_id: str,
        attested_by: str,
        statement: str,
        control_id: Optional[str] = None,
        attester_role: Optional[str] = None,
        attestation_type: str = "manual",
        evidence_urls: Optional[List[str]] = None,
        valid_days: int = 365
    ) -> str:
        """Create a compliance attestation.

        Args:
            consortium_id: Consortium ID.
            framework_id: Framework ID.
            attested_by: Attester company ID.
            statement: Attestation statement.
            control_id: Optional specific control ID.
            attester_role: Role of attester.
            attestation_type: Type of attestation.
            evidence_urls: URLs to supporting evidence.
            valid_days: Validity period in days.

        Returns:
            Attestation ID.
        """
        self._init_compliance_schema()

        attestation_id = f"attest_{secrets.token_hex(8)}"
        now = datetime.utcnow()
        valid_until = now + timedelta(days=valid_days)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO compliance_attestations
                (id, consortium_id, framework_id, control_id, attested_by, attester_role,
                 attestation_type, statement, evidence_urls, valid_until)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attestation_id,
                consortium_id,
                framework_id,
                control_id,
                attested_by,
                attester_role,
                attestation_type,
                statement,
                json.dumps(evidence_urls) if evidence_urls else None,
                valid_until
            ))

        return attestation_id

    def get_attestations(
        self,
        consortium_id: str,
        framework_id: Optional[str] = None,
        include_revoked: bool = False
    ) -> List[Dict]:
        """Get attestations for a consortium."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT a.*, c.name as attester_name
                FROM compliance_attestations a
                JOIN companies c ON a.attested_by = c.id
                WHERE a.consortium_id = ?
            """
            params = [consortium_id]

            if framework_id:
                query += " AND a.framework_id = ?"
                params.append(framework_id)

            if not include_revoked:
                query += " AND a.revoked = 0"

            query += " ORDER BY a.valid_from DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            if r.get("evidence_urls"):
                r["evidence_urls"] = json.loads(r["evidence_urls"])
            result.append(r)

        return result

    def record_data_processing(
        self,
        consortium_id: str,
        company_id: str,
        processing_purpose: str,
        data_categories: List[str],
        legal_basis: str,
        data_subjects: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        retention_period: Optional[str] = None,
        security_measures: Optional[List[str]] = None,
        cross_border_transfer: bool = False,
        transfer_safeguards: Optional[str] = None
    ) -> str:
        """Record a data processing activity (GDPR Article 30).

        Args:
            consortium_id: Consortium ID.
            company_id: Company performing processing.
            processing_purpose: Purpose of processing.
            data_categories: Categories of data processed.
            legal_basis: Legal basis for processing.
            data_subjects: Description of data subjects.
            recipients: List of data recipients.
            retention_period: Data retention period.
            security_measures: Security measures in place.
            cross_border_transfer: Whether data is transferred cross-border.
            transfer_safeguards: Safeguards for cross-border transfer.

        Returns:
            Processing record ID.
        """
        self._init_compliance_schema()
        record_id = f"dpr_{secrets.token_hex(8)}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO data_processing_records
                (id, consortium_id, company_id, processing_purpose, data_categories,
                 data_subjects, recipients, retention_period, security_measures,
                 legal_basis, cross_border_transfer, transfer_safeguards)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_id,
                consortium_id,
                company_id,
                processing_purpose,
                json.dumps(data_categories),
                data_subjects,
                json.dumps(recipients) if recipients else None,
                retention_period,
                json.dumps(security_measures) if security_measures else None,
                legal_basis,
                1 if cross_border_transfer else 0,
                transfer_safeguards
            ))

        return record_id

    def get_data_processing_records(
        self,
        consortium_id: str,
        company_id: Optional[str] = None
    ) -> List[Dict]:
        """Get data processing records for a consortium."""
        self._init_compliance_schema()
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT dpr.*, c.name as company_name
                FROM data_processing_records dpr
                JOIN companies c ON dpr.company_id = c.id
                WHERE dpr.consortium_id = ?
            """
            params = [consortium_id]

            if company_id:
                query += " AND dpr.company_id = ?"
                params.append(company_id)

            query += " ORDER BY dpr.created_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

        result = []
        for row in rows:
            r = dict(row)
            r["data_categories"] = json.loads(r["data_categories"])
            if r.get("recipients"):
                r["recipients"] = json.loads(r["recipients"])
            if r.get("security_measures"):
                r["security_measures"] = json.loads(r["security_measures"])
            r["cross_border_transfer"] = bool(r["cross_border_transfer"])
            result.append(r)

        return result

    def get_compliance_dashboard(self, consortium_id: str) -> Dict:
        """Get compliance dashboard summary for a consortium.

        Args:
            consortium_id: Consortium ID.

        Returns:
            Dashboard data with overall compliance status.
        """
        self._init_compliance_schema()

        settings = self.get_consortium_compliance_settings(consortium_id)
        enabled_frameworks = settings.get("enabled_frameworks", [])

        frameworks_status = []
        for fw_id in enabled_frameworks:
            framework = self.get_compliance_framework(fw_id)
            if not framework:
                continue

            checks = self.get_compliance_checks(consortium_id, fw_id)
            passed = sum(1 for c in checks if c["status"] == "passed")
            failed = sum(1 for c in checks if c["status"] == "failed")
            pending = sum(1 for c in checks if c["status"] == "pending")
            total = len(checks)

            score = (passed / total * 100) if total > 0 else 0
            status = "compliant" if failed == 0 and pending == 0 and total > 0 else "non_compliant"

            frameworks_status.append({
                "framework_id": fw_id,
                "framework_name": framework["name"],
                "score": round(score, 2),
                "status": status,
                "passed": passed,
                "failed": failed,
                "pending": pending,
                "total": total
            })

        # Calculate overall score
        if frameworks_status:
            overall_score = sum(f["score"] for f in frameworks_status) / len(frameworks_status)
            overall_compliant = all(f["status"] == "compliant" for f in frameworks_status)
        else:
            overall_score = 0
            overall_compliant = False

        return {
            "consortium_id": consortium_id,
            "overall_score": round(overall_score, 2),
            "overall_status": "compliant" if overall_compliant else "non_compliant",
            "enabled_frameworks_count": len(enabled_frameworks),
            "frameworks": frameworks_status,
            "last_check_at": settings.get("last_check_at"),
            "next_check_at": settings.get("next_check_at")
        }


# Export all public classes and functions
__all__ = ["ComplianceManager"]
