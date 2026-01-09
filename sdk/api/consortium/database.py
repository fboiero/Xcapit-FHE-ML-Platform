"""Database management for consortium operations.

This module handles database connections, schema initialization,
and seed data for all consortium-related tables.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional


class DatabaseManager:
    """Manages database connections and schema initialization."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database.
        """
        self.db_path = db_path or Path("./data/fheml.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._schemas_initialized = set()

    @contextmanager
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(
            str(self.db_path), detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_core_schema(self):
        """Initialize core database schema (companies, consortiums, memberships)."""
        if "core" in self._schemas_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Companies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    api_key_hash TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            # Consortiums table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consortiums (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    model_type TEXT NOT NULL,
                    model_config TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    training_started_at TIMESTAMP,
                    training_completed_at TIMESTAMP,
                    model_id TEXT,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (owner_id) REFERENCES companies(id)
                )
            """)

            # Memberships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memberships (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'contributor',
                    status TEXT NOT NULL DEFAULT 'pending',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_uploaded BOOLEAN DEFAULT 0,
                    data_record_count INTEGER DEFAULT 0,
                    last_upload_at TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id) ON DELETE CASCADE,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    UNIQUE(consortium_id, company_id)
                )
            """)

            # Invitations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invitations (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    invited_by TEXT NOT NULL,
                    invite_email TEXT NOT NULL,
                    invite_code TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL DEFAULT 'contributor',
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    accepted_at TIMESTAMP,
                    accepted_by TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id) ON DELETE CASCADE,
                    FOREIGN KEY (invited_by) REFERENCES companies(id)
                )
            """)

            # Data contributions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_contributions (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    encrypted_blob_path TEXT NOT NULL,
                    record_count INTEGER NOT NULL,
                    feature_count INTEGER NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id) ON DELETE CASCADE,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_consortiums_owner ON consortiums(owner_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_consortiums_status ON consortiums(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_memberships_consortium ON memberships(consortium_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_memberships_company ON memberships(company_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_invitations_code ON invitations(invite_code)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_invitations_email ON invitations(invite_email)"
            )

        self._schemas_initialized.add("core")

    def init_governance_schema(self):
        """Initialize governance-related database tables."""
        if "governance" in self._schemas_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Contribution proofs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contribution_proofs (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    record_count INTEGER NOT NULL,
                    feature_count INTEGER NOT NULL,
                    data_hash TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified INTEGER DEFAULT 0,
                    blockchain_tx TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Proposals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    proposer_id TEXT NOT NULL,
                    proposal_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    data TEXT,
                    status TEXT DEFAULT 'active',
                    yes_votes INTEGER DEFAULT 0,
                    no_votes INTEGER DEFAULT 0,
                    voting_weight_yes INTEGER DEFAULT 0,
                    voting_weight_no INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    executed_at TIMESTAMP,
                    blockchain_tx TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (proposer_id) REFERENCES companies(id)
                )
            """)

            # Votes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    voter_id TEXT NOT NULL,
                    support INTEGER NOT NULL,
                    weight INTEGER NOT NULL,
                    comment TEXT,
                    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proposal_id) REFERENCES proposals(id),
                    FOREIGN KEY (voter_id) REFERENCES companies(id),
                    UNIQUE(proposal_id, voter_id)
                )
            """)

            # Audit events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    target_id TEXT,
                    target_type TEXT,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    previous_hash TEXT,
                    blockchain_tx TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (actor_id) REFERENCES companies(id)
                )
            """)

            # Reward distributions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reward_distributions (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    distributed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    distributions TEXT NOT NULL,
                    blockchain_tx TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

        self._schemas_initialized.add("governance")

    def init_compliance_schema(self):
        """Initialize compliance-related database tables."""
        if "compliance" in self._schemas_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Compliance frameworks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_frameworks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    version TEXT NOT NULL,
                    description TEXT,
                    region TEXT,
                    industry TEXT,
                    controls_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Compliance controls
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_controls (
                    id TEXT PRIMARY KEY,
                    framework_id TEXT NOT NULL,
                    control_code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    severity TEXT DEFAULT 'medium',
                    verification_type TEXT NOT NULL,
                    verification_config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(id),
                    UNIQUE(framework_id, control_code)
                )
            """)

            # Compliance checks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    framework_id TEXT NOT NULL,
                    control_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    evidence TEXT,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checked_by TEXT,
                    expires_at TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(id),
                    FOREIGN KEY (control_id) REFERENCES compliance_controls(id)
                )
            """)

            # Compliance reports
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_reports (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    framework_id TEXT NOT NULL,
                    report_type TEXT DEFAULT 'automated',
                    overall_score REAL DEFAULT 0,
                    passed_controls INTEGER DEFAULT 0,
                    failed_controls INTEGER DEFAULT 0,
                    pending_controls INTEGER DEFAULT 0,
                    total_controls INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'draft',
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valid_until TIMESTAMP,
                    report_data TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(id)
                )
            """)

            # Compliance attestations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_attestations (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    framework_id TEXT NOT NULL,
                    control_id TEXT,
                    attested_by TEXT NOT NULL,
                    attester_role TEXT,
                    attestation_type TEXT NOT NULL,
                    statement TEXT NOT NULL,
                    evidence_urls TEXT,
                    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valid_until TIMESTAMP,
                    revoked INTEGER DEFAULT 0,
                    revoked_at TIMESTAMP,
                    revoked_reason TEXT,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (framework_id) REFERENCES compliance_frameworks(id),
                    FOREIGN KEY (control_id) REFERENCES compliance_controls(id),
                    FOREIGN KEY (attested_by) REFERENCES companies(id)
                )
            """)

            # Data processing records
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_processing_records (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    processing_purpose TEXT NOT NULL,
                    data_categories TEXT NOT NULL,
                    data_subjects TEXT,
                    recipients TEXT,
                    retention_period TEXT,
                    security_measures TEXT,
                    legal_basis TEXT,
                    cross_border_transfer INTEGER DEFAULT 0,
                    transfer_safeguards TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Consortium compliance settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS consortium_compliance_settings (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL UNIQUE,
                    enabled_frameworks TEXT DEFAULT '[]',
                    auto_check_interval INTEGER DEFAULT 86400,
                    notification_emails TEXT DEFAULT '[]',
                    last_check_at TIMESTAMP,
                    next_check_at TIMESTAMP,
                    settings TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            conn.commit()
            self._seed_compliance_frameworks(cursor, conn)

        self._schemas_initialized.add("compliance")

    def _seed_compliance_frameworks(self, cursor, conn):
        """Seed default compliance frameworks."""
        frameworks = [
            (
                "framework_gdpr",
                "GDPR",
                "2016/679",
                "General Data Protection Regulation - EU data privacy law",
                "EU",
                "all",
            ),
            (
                "framework_hipaa",
                "HIPAA",
                "1996",
                "Health Insurance Portability and Accountability Act - US healthcare data",
                "US",
                "healthcare",
            ),
            (
                "framework_soc2",
                "SOC2",
                "Type II",
                "Service Organization Control 2 - Security, availability, processing integrity",
                "global",
                "technology",
            ),
            (
                "framework_pci_dss",
                "PCI-DSS",
                "4.0",
                "Payment Card Industry Data Security Standard",
                "global",
                "finance",
            ),
        ]

        for fw in frameworks:
            cursor.execute(
                """
                INSERT OR IGNORE INTO compliance_frameworks (id, name, version, description, region, industry)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                fw,
            )
        conn.commit()

    def init_data_quality_schema(self):
        """Initialize data quality-related database tables."""
        if "data_quality" in self._schemas_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Data quality assessments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_assessments (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    contribution_id TEXT,
                    overall_score REAL DEFAULT 0,
                    completeness_score REAL DEFAULT 0,
                    consistency_score REAL DEFAULT 0,
                    uniqueness_score REAL DEFAULT 0,
                    validity_score REAL DEFAULT 0,
                    freshness_score REAL DEFAULT 0,
                    record_count INTEGER DEFAULT 0,
                    feature_count INTEGER DEFAULT 0,
                    null_ratio REAL DEFAULT 0,
                    duplicate_ratio REAL DEFAULT 0,
                    outlier_ratio REAL DEFAULT 0,
                    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Quality metrics history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_history (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Quality rules/thresholds
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_rules (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    threshold_min REAL,
                    threshold_max REAL,
                    weight REAL DEFAULT 1.0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    UNIQUE(consortium_id, rule_name)
                )
            """)

            # Quality alerts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_alerts (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'warning',
                    message TEXT NOT NULL,
                    metric_name TEXT,
                    metric_value REAL,
                    threshold_value REAL,
                    acknowledged INTEGER DEFAULT 0,
                    acknowledged_by TEXT,
                    acknowledged_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

        self._schemas_initialized.add("data_quality")

    def init_marketplace_schema(self):
        """Initialize marketplace-related database tables."""
        if "marketplace" in self._schemas_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Marketplace models table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marketplace_models (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    industry TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    version TEXT DEFAULT '1.0.0',
                    accuracy REAL,
                    training_samples INTEGER,
                    features TEXT DEFAULT '[]',
                    use_cases TEXT DEFAULT '[]',
                    pricing_type TEXT DEFAULT 'free',
                    price REAL DEFAULT 0,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    is_featured INTEGER DEFAULT 0,
                    downloads INTEGER DEFAULT 0,
                    rating REAL DEFAULT 0,
                    rating_count INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            # Model deployments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_deployments (
                    id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    consortium_id TEXT NOT NULL,
                    deployed_by TEXT NOT NULL,
                    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    config TEXT DEFAULT '{}',
                    FOREIGN KEY (model_id) REFERENCES marketplace_models(id),
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            # Model reviews table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_reviews (
                    id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    reviewer_id TEXT NOT NULL,
                    consortium_id TEXT,
                    rating INTEGER NOT NULL,
                    title TEXT,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    helpful_count INTEGER DEFAULT 0,
                    FOREIGN KEY (model_id) REFERENCES marketplace_models(id)
                )
            """)

            # Model categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_categories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    icon TEXT,
                    parent_id TEXT,
                    display_order INTEGER DEFAULT 0
                )
            """)

            conn.commit()
            self._seed_marketplace_data(cursor, conn)

        self._schemas_initialized.add("marketplace")

    def _seed_marketplace_data(self, cursor, conn):
        """Seed default marketplace categories and models."""
        cursor.execute("SELECT COUNT(*) FROM marketplace_models")
        if cursor.fetchone()[0] > 0:
            return

        # Seed categories
        categories = [
            (
                "cat_fraud",
                "Fraud Detection",
                "Modelos para deteccion de fraude",
                "shield-exclamation",
                None,
                1,
            ),
            (
                "cat_credit",
                "Credit Scoring",
                "Modelos para evaluacion crediticia",
                "banknotes",
                None,
                2,
            ),
            ("cat_health", "Healthcare", "Modelos para el sector salud", "heart", None, 3),
            (
                "cat_retail",
                "Retail & E-commerce",
                "Modelos para comercio",
                "shopping-cart",
                None,
                4,
            ),
            ("cat_insurance", "Insurance", "Modelos para seguros", "shield-check", None, 5),
        ]

        for cat in categories:
            cursor.execute(
                """
                INSERT OR IGNORE INTO model_categories
                (id, name, description, icon, parent_id, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                cat,
            )

        # Seed pre-trained models
        models = [
            {
                "id": "model_fraud_transaction",
                "name": "Transaction Fraud Detector",
                "description": "Modelo de deteccion de fraude en transacciones bancarias usando FHE. Entrenado con datos anonimizados de multiples instituciones financieras.",
                "industry": "cat_fraud",
                "model_type": "logistic_regression",
                "version": "2.1.0",
                "accuracy": 94.5,
                "training_samples": 1500000,
                "features": json.dumps(
                    ["amount", "merchant_category", "time_of_day", "device_type", "location_risk"]
                ),
                "use_cases": json.dumps(
                    ["Deteccion en tiempo real", "Scoring de riesgo", "Alertas automaticas"]
                ),
                "pricing_type": "free",
                "is_featured": 1,
                "downloads": 234,
                "rating": 4.8,
                "rating_count": 45,
            },
            {
                "id": "model_fraud_account",
                "name": "Account Takeover Detector",
                "description": "Detecta intentos de apropiacion de cuentas basado en patrones de comportamiento.",
                "industry": "cat_fraud",
                "model_type": "decision_tree",
                "version": "1.3.0",
                "accuracy": 91.2,
                "training_samples": 800000,
                "features": json.dumps(
                    ["login_frequency", "ip_changes", "device_fingerprint", "session_duration"]
                ),
                "use_cases": json.dumps(["Proteccion de cuentas", "Verificacion de identidad"]),
                "pricing_type": "free",
                "is_featured": 0,
                "downloads": 156,
                "rating": 4.5,
                "rating_count": 28,
            },
            {
                "id": "model_credit_default",
                "name": "Credit Default Predictor",
                "description": "Predice probabilidad de default crediticio. Compatible con regulaciones de credit scoring.",
                "industry": "cat_credit",
                "model_type": "logistic_regression",
                "version": "3.0.0",
                "accuracy": 88.7,
                "training_samples": 2000000,
                "features": json.dumps(
                    ["income_ratio", "credit_history", "debt_to_income", "payment_history"]
                ),
                "use_cases": json.dumps(
                    ["Evaluacion de prestamos", "Limite de credito", "Pricing de riesgo"]
                ),
                "pricing_type": "free",
                "is_featured": 1,
                "downloads": 312,
                "rating": 4.7,
                "rating_count": 67,
            },
            {
                "id": "model_credit_score",
                "name": "Alternative Credit Scorer",
                "description": "Score crediticio alternativo para poblacion no bancarizada.",
                "industry": "cat_credit",
                "model_type": "linear_regression",
                "version": "1.5.0",
                "accuracy": 82.3,
                "training_samples": 500000,
                "features": json.dumps(
                    ["utility_payments", "mobile_usage", "social_data", "employment"]
                ),
                "use_cases": json.dumps(["Inclusion financiera", "Microfinanzas"]),
                "pricing_type": "free",
                "is_featured": 0,
                "downloads": 89,
                "rating": 4.2,
                "rating_count": 15,
            },
            {
                "id": "model_health_readmission",
                "name": "Hospital Readmission Risk",
                "description": "Predice riesgo de readmision hospitalaria a 30 dias. HIPAA compliant.",
                "industry": "cat_health",
                "model_type": "logistic_regression",
                "version": "2.0.0",
                "accuracy": 86.4,
                "training_samples": 350000,
                "features": json.dumps(
                    ["diagnosis_codes", "length_of_stay", "age_group", "comorbidities"]
                ),
                "use_cases": json.dumps(
                    ["Gestion de casos", "Prevencion de readmisiones", "Optimizacion de recursos"]
                ),
                "pricing_type": "free",
                "is_featured": 1,
                "downloads": 178,
                "rating": 4.6,
                "rating_count": 34,
            },
            {
                "id": "model_health_diagnosis",
                "name": "Diagnostic Support Model",
                "description": "Modelo de soporte al diagnostico medico basado en sintomas y antecedentes.",
                "industry": "cat_health",
                "model_type": "decision_tree",
                "version": "1.2.0",
                "accuracy": 84.1,
                "training_samples": 200000,
                "features": json.dumps(
                    ["symptoms", "medical_history", "lab_results", "vital_signs"]
                ),
                "use_cases": json.dumps(["Triaje", "Segunda opinion", "Alertas clinicas"]),
                "pricing_type": "free",
                "is_featured": 0,
                "downloads": 145,
                "rating": 4.4,
                "rating_count": 22,
            },
            {
                "id": "model_retail_churn",
                "name": "Customer Churn Predictor",
                "description": "Predice probabilidad de abandono de clientes en retail/e-commerce.",
                "industry": "cat_retail",
                "model_type": "logistic_regression",
                "version": "2.2.0",
                "accuracy": 87.8,
                "training_samples": 1200000,
                "features": json.dumps(
                    ["purchase_frequency", "recency", "monetary_value", "engagement_score"]
                ),
                "use_cases": json.dumps(
                    ["Retencion proactiva", "Campanas personalizadas", "Segmentacion"]
                ),
                "pricing_type": "free",
                "is_featured": 1,
                "downloads": 267,
                "rating": 4.5,
                "rating_count": 52,
            },
            {
                "id": "model_retail_recommend",
                "name": "Product Recommender",
                "description": "Sistema de recomendacion de productos basado en comportamiento colaborativo.",
                "industry": "cat_retail",
                "model_type": "kmeans",
                "version": "1.8.0",
                "accuracy": 79.5,
                "training_samples": 3000000,
                "features": json.dumps(
                    ["purchase_history", "browsing_behavior", "category_affinity"]
                ),
                "use_cases": json.dumps(["Cross-selling", "Personalizacion", "Email marketing"]),
                "pricing_type": "free",
                "is_featured": 0,
                "downloads": 198,
                "rating": 4.3,
                "rating_count": 41,
            },
            {
                "id": "model_insurance_claim",
                "name": "Claim Fraud Detector",
                "description": "Detecta reclamos fraudulentos en seguros de auto y hogar.",
                "industry": "cat_insurance",
                "model_type": "decision_tree",
                "version": "1.6.0",
                "accuracy": 89.3,
                "training_samples": 600000,
                "features": json.dumps(
                    ["claim_amount", "claim_frequency", "policy_age", "incident_type"]
                ),
                "use_cases": json.dumps(
                    ["Investigacion de reclamos", "Fast-track de aprobacion", "SIU support"]
                ),
                "pricing_type": "free",
                "is_featured": 1,
                "downloads": 134,
                "rating": 4.7,
                "rating_count": 29,
            },
            {
                "id": "model_insurance_risk",
                "name": "Underwriting Risk Model",
                "description": "Evaluacion de riesgo para suscripcion de polizas.",
                "industry": "cat_insurance",
                "model_type": "linear_regression",
                "version": "2.4.0",
                "accuracy": 85.6,
                "training_samples": 450000,
                "features": json.dumps(
                    ["age", "health_indicators", "lifestyle_factors", "claims_history"]
                ),
                "use_cases": json.dumps(
                    ["Pricing de polizas", "Seleccion de riesgo", "Segmentacion"]
                ),
                "pricing_type": "free",
                "is_featured": 0,
                "downloads": 112,
                "rating": 4.4,
                "rating_count": 18,
            },
        ]

        for model in models:
            cursor.execute(
                """
                INSERT OR IGNORE INTO marketplace_models
                (id, name, description, industry, model_type, version, accuracy, training_samples,
                 features, use_cases, pricing_type, is_featured, downloads, rating, rating_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    model["id"],
                    model["name"],
                    model["description"],
                    model["industry"],
                    model["model_type"],
                    model["version"],
                    model["accuracy"],
                    model["training_samples"],
                    model["features"],
                    model["use_cases"],
                    model["pricing_type"],
                    model["is_featured"],
                    model["downloads"],
                    model["rating"],
                    model["rating_count"],
                ),
            )
        conn.commit()

    def init_sandbox_schema(self):
        """Initialize sandbox schema."""
        if "sandbox" in self._schemas_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Sandbox environments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sandbox_environments (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT NOT NULL,
                    template_type TEXT DEFAULT 'basic',
                    industry TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    config TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (owner_id) REFERENCES companies(id)
                )
            """)

            # Synthetic datasets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS synthetic_datasets (
                    id TEXT PRIMARY KEY,
                    sandbox_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    dataset_type TEXT NOT NULL,
                    industry TEXT,
                    record_count INTEGER DEFAULT 0,
                    feature_count INTEGER DEFAULT 0,
                    features TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    data_preview TEXT DEFAULT '[]',
                    statistics TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (sandbox_id) REFERENCES sandbox_environments(id),
                    FOREIGN KEY (created_by) REFERENCES companies(id)
                )
            """)

            # Sandbox experiments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sandbox_experiments (
                    id TEXT PRIMARY KEY,
                    sandbox_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    experiment_type TEXT NOT NULL,
                    model_type TEXT,
                    dataset_id TEXT,
                    status TEXT DEFAULT 'pending',
                    config TEXT DEFAULT '{}',
                    results TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_by TEXT,
                    FOREIGN KEY (sandbox_id) REFERENCES sandbox_environments(id),
                    FOREIGN KEY (dataset_id) REFERENCES synthetic_datasets(id),
                    FOREIGN KEY (created_by) REFERENCES companies(id)
                )
            """)

            # Sandbox templates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sandbox_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    industry TEXT,
                    template_type TEXT NOT NULL,
                    datasets TEXT DEFAULT '[]',
                    experiments TEXT DEFAULT '[]',
                    is_public INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)

            conn.commit()
            self._seed_sandbox_templates(cursor, conn)

        self._schemas_initialized.add("sandbox")

    def _seed_sandbox_templates(self, cursor, conn):
        """Seed initial sandbox templates."""
        cursor.execute("SELECT COUNT(*) FROM sandbox_templates")
        if cursor.fetchone()[0] > 0:
            return

        templates = [
            (
                "tpl_fraud_basic",
                "Fraud Detection Starter",
                "Ambiente basico para detectar fraudes",
                "fraud",
                "starter",
                json.dumps([{"type": "transactions", "records": 10000, "fraud_rate": 0.02}]),
                json.dumps([{"type": "training", "model": "logistic_regression"}]),
            ),
            (
                "tpl_credit_basic",
                "Credit Scoring Starter",
                "Ambiente para construir modelos de scoring crediticio",
                "credit",
                "starter",
                json.dumps([{"type": "applications", "records": 5000, "default_rate": 0.15}]),
                json.dumps([{"type": "training", "model": "decision_tree"}]),
            ),
            (
                "tpl_health_basic",
                "Healthcare Analytics Starter",
                "Ambiente para analisis de datos clinicos",
                "health",
                "starter",
                json.dumps(
                    [
                        {"type": "patients", "records": 2000},
                        {"type": "diagnoses", "records": 8000},
                        {"type": "lab_results", "records": 20000},
                    ]
                ),
                json.dumps(
                    [
                        {"type": "training", "model": "logistic_regression"},
                        {"type": "clustering", "model": "kmeans"},
                    ]
                ),
            ),
            (
                "tpl_retail_basic",
                "Retail Analytics Starter",
                "Ambiente para analisis de clientes y prediccion de churn",
                "retail",
                "starter",
                json.dumps(
                    [
                        {"type": "customers", "records": 5000},
                        {"type": "transactions", "records": 100000},
                        {"type": "products", "records": 500},
                    ]
                ),
                json.dumps(
                    [
                        {"type": "segmentation", "model": "kmeans"},
                        {"type": "churn_prediction", "model": "logistic_regression"},
                    ]
                ),
            ),
            (
                "tpl_advanced_fhe",
                "FHE Advanced Workshop",
                "Ambiente avanzado para experimentar con encriptacion homomorfica",
                "general",
                "advanced",
                json.dumps(
                    [
                        {"type": "numeric", "records": 1000, "features": 20},
                        {"type": "encrypted_sample", "records": 100},
                    ]
                ),
                json.dumps(
                    [
                        {"type": "encryption_benchmark"},
                        {"type": "training_encrypted"},
                        {"type": "inference_encrypted"},
                    ]
                ),
            ),
        ]

        for tpl in templates:
            cursor.execute(
                """
                INSERT OR IGNORE INTO sandbox_templates
                (id, name, description, industry, template_type, datasets, experiments)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                tpl,
            )
        conn.commit()

    def init_federated_schema(self):
        """Initialize federated inference tables."""
        if "federated" in self._schemas_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Inference endpoints table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inference_endpoints (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    model_id TEXT,
                    endpoint_type TEXT DEFAULT 'private',
                    status TEXT DEFAULT 'active',
                    encryption_scheme TEXT DEFAULT 'CKKS',
                    max_batch_size INTEGER DEFAULT 100,
                    rate_limit INTEGER DEFAULT 1000,
                    config TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

            # Inference requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inference_requests (
                    id TEXT PRIMARY KEY,
                    endpoint_id TEXT NOT NULL,
                    requester_id TEXT NOT NULL,
                    request_type TEXT DEFAULT 'single',
                    input_shape TEXT,
                    batch_size INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    encryption_verified INTEGER DEFAULT 0,
                    processing_time_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (endpoint_id) REFERENCES inference_endpoints(id),
                    FOREIGN KEY (requester_id) REFERENCES companies(id)
                )
            """)

            # Inference results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inference_results (
                    id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    result_type TEXT DEFAULT 'prediction',
                    encrypted_output TEXT,
                    output_shape TEXT,
                    confidence_encrypted INTEGER DEFAULT 1,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES inference_requests(id)
                )
            """)

            # Federated models table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS federated_models (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    model_type TEXT NOT NULL,
                    input_features TEXT,
                    output_type TEXT,
                    accuracy REAL,
                    is_encrypted INTEGER DEFAULT 1,
                    encryption_scheme TEXT DEFAULT 'CKKS',
                    model_size_bytes INTEGER,
                    training_consortium_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    version TEXT DEFAULT '1.0.0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    config TEXT DEFAULT '{}',
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            # Edge nodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS edge_nodes (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    node_type TEXT DEFAULT 'inference',
                    status TEXT DEFAULT 'active',
                    hardware_info TEXT DEFAULT '{}',
                    last_heartbeat TIMESTAMP,
                    models_deployed TEXT DEFAULT '[]',
                    inference_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)

        self._schemas_initialized.add("federated")

    def init_explainability_schema(self):
        """Initialize explainability-related database tables."""
        if "explainability" in self._schemas_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Explanation requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS explanation_requests (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    model_id TEXT,
                    requester_id TEXT NOT NULL,
                    explanation_type TEXT NOT NULL,
                    input_data TEXT DEFAULT '{}',
                    prediction_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            # Explanation results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS explanation_results (
                    id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    explanation_type TEXT NOT NULL,
                    feature_importance TEXT DEFAULT '[]',
                    feature_contributions TEXT DEFAULT '[]',
                    decision_path TEXT DEFAULT '[]',
                    counterfactuals TEXT DEFAULT '[]',
                    summary TEXT,
                    confidence REAL,
                    privacy_preserved INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES explanation_requests(id)
                )
            """)

            # Feature importance cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feature_importance (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    model_id TEXT,
                    feature_name TEXT NOT NULL,
                    importance_score REAL,
                    importance_type TEXT DEFAULT 'permutation',
                    rank INTEGER,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

            # Model insights
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_insights (
                    id TEXT PRIMARY KEY,
                    consortium_id TEXT NOT NULL,
                    model_id TEXT,
                    insight_type TEXT NOT NULL,
                    insight_data TEXT DEFAULT '{}',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (consortium_id) REFERENCES consortiums(id)
                )
            """)

        self._schemas_initialized.add("explainability")

    def init_competitive_insights_schema(self):
        """Initialize competitive insights database tables."""
        if "competitive_insights" in self._schemas_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Industry benchmarks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS industry_benchmarks (
                    id TEXT PRIMARY KEY,
                    industry TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    percentile_10 REAL,
                    percentile_25 REAL,
                    percentile_50 REAL,
                    percentile_75 REAL,
                    percentile_90 REAL,
                    sample_size INTEGER,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valid_until TIMESTAMP,
                    metadata TEXT
                )
            """)

            # Company performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_metrics (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    consortium_id TEXT,
                    industry TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_anonymized INTEGER DEFAULT 1,
                    metadata TEXT
                )
            """)

            # Benchmark comparisons
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_comparisons (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metrics_compared INTEGER,
                    overall_percentile REAL,
                    strengths TEXT,
                    improvements TEXT,
                    metadata TEXT
                )
            """)

            # Industry trends
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS industry_trends (
                    id TEXT PRIMARY KEY,
                    industry TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    period TEXT NOT NULL,
                    trend_direction TEXT,
                    change_percentage REAL,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

        self._schemas_initialized.add("competitive_insights")

    def init_ensemble_schema(self):
        """Initialize multi-model ensemble database tables."""
        if "ensemble" in self._schemas_initialized:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Ensemble definitions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_ensembles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT NOT NULL,
                    ensemble_type TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            # Models in ensemble
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ensemble_models (
                    id TEXT PRIMARY KEY,
                    ensemble_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    consortium_id TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contribution_approved INTEGER DEFAULT 0,
                    metadata TEXT,
                    FOREIGN KEY (ensemble_id) REFERENCES model_ensembles(id)
                )
            """)

            # Ensemble predictions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ensemble_predictions (
                    id TEXT PRIMARY KEY,
                    ensemble_id TEXT NOT NULL,
                    requester_id TEXT NOT NULL,
                    input_hash TEXT,
                    prediction_result TEXT,
                    confidence REAL,
                    models_used INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    latency_ms REAL,
                    metadata TEXT,
                    FOREIGN KEY (ensemble_id) REFERENCES model_ensembles(id)
                )
            """)

            # Ensemble performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ensemble_metrics (
                    id TEXT PRIMARY KEY,
                    ensemble_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (ensemble_id) REFERENCES model_ensembles(id)
                )
            """)

        self._schemas_initialized.add("ensemble")

    def init_all_schemas(self):
        """Initialize all database schemas."""
        self.init_core_schema()
        self.init_governance_schema()
        self.init_compliance_schema()
        self.init_data_quality_schema()
        self.init_marketplace_schema()
        self.init_sandbox_schema()
        self.init_federated_schema()
        self.init_explainability_schema()
        self.init_competitive_insights_schema()
        self.init_ensemble_schema()


__all__ = ["DatabaseManager"]
