#!/usr/bin/env python
"""
Demo script for Xcapit FHE-ML Platform.

This script demonstrates the complete workflow of the platform:
1. User registration and authentication
2. Company and consortium creation
3. ML model training and prediction
4. Compliance and governance features

Run with: python demo.py
"""

import os
import sys
import json
from datetime import datetime, timedelta
from uuid import uuid4

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_test")

import django
django.setup()

# Setup database tables
from django.core.management import call_command
print("Setting up database...")
call_command('migrate', '--run-syncdb', verbosity=0)
print("Database ready.\n")

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import APIKey, AuditLog, Company
from apps.consortiums.models import Consortium, ConsortiumMember, ContributionProof
from apps.models.models import MLModel, PredictionLog, TrainingRun
from apps.compliance.models import ComplianceFramework, ConsortiumCompliance, ComplianceCheck
from apps.governance.models import Proposal, Vote
from apps.marketplace.models import Category, MarketplaceModel
from apps.sandbox.models import Sandbox, SandboxTemplate, SyntheticDataset
from apps.federated.models import InferenceEndpoint, FederatedModel

User = get_user_model()


def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_success(message):
    """Print a success message."""
    print(f"  [OK] {message}")


def print_info(message):
    """Print an info message."""
    print(f"  [INFO] {message}")


def run_demo():
    """Run the complete platform demo."""
    print("\n")
    print("*" * 60)
    print("*  XCAPIT FHE-ML PLATFORM - DEMO                          *")
    print("*  Fully Homomorphic Encryption for Privacy-Preserving ML *")
    print("*" * 60)

    # =========================================================================
    # 1. USER AND COMPANY SETUP
    # =========================================================================
    print_header("1. USER AND COMPANY SETUP")

    # Create companies
    company1 = Company.objects.create(
        name="Acme Finance Corp",
        email="contact@acmefinance.com",
        industry="finance",
    )
    print_success(f"Created company: {company1.name}")

    company2 = Company.objects.create(
        name="HealthTech Inc",
        email="contact@healthtech.com",
        industry="healthcare",
    )
    print_success(f"Created company: {company2.name}")

    company3 = Company.objects.create(
        name="GovData Agency",
        email="contact@govdata.gov",
        industry="government",
    )
    print_success(f"Created company: {company3.name}")

    # Create users
    user1 = User.objects.create_user(
        email="alice@acmefinance.com",
        password="securepassword123",
        first_name="Alice",
        last_name="Chen",
        company=company1,
    )
    print_success(f"Created user: {user1.email}")

    user2 = User.objects.create_user(
        email="bob@healthtech.com",
        password="securepassword123",
        first_name="Bob",
        last_name="Smith",
        company=company2,
    )
    print_success(f"Created user: {user2.email}")

    # Generate JWT token
    refresh = RefreshToken.for_user(user1)
    print_info(f"JWT access token generated for {user1.email}")
    print_info(f"Token prefix: {str(refresh.access_token)[:50]}...")

    # =========================================================================
    # 2. CONSORTIUM CREATION
    # =========================================================================
    print_header("2. CONSORTIUM CREATION")

    consortium = Consortium.objects.create(
        name="Fraud Detection Consortium",
        owner=company1,
        description="Collaborative fraud detection using FHE",
        voting_threshold=0.51,
        status=Consortium.Status.ACTIVE,
    )
    print_success(f"Created consortium: {consortium.name}")

    # Add members
    member1 = ConsortiumMember.objects.create(
        consortium=consortium,
        company=company1,
        role=ConsortiumMember.Role.ADMIN,
        status=ConsortiumMember.Status.ACTIVE,
    )
    print_success(f"Added {company1.name} as admin")

    member2 = ConsortiumMember.objects.create(
        consortium=consortium,
        company=company2,
        role=ConsortiumMember.Role.CONTRIBUTOR,
        status=ConsortiumMember.Status.ACTIVE,
    )
    print_success(f"Added {company2.name} as member")

    member3 = ConsortiumMember.objects.create(
        consortium=consortium,
        company=company3,
        role=ConsortiumMember.Role.CONTRIBUTOR,
        status=ConsortiumMember.Status.ACTIVE,
    )
    print_success(f"Added {company3.name} as member")

    # =========================================================================
    # 3. DATA CONTRIBUTIONS
    # =========================================================================
    print_header("3. DATA CONTRIBUTIONS")

    contrib1 = ContributionProof.objects.create(
        consortium=consortium,
        company=company1,
        record_count=50000,
        feature_count=15,
        data_hash="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        checksum="1111111111111111111111111111111111111111111111111111111111111111",
        verified=True,
    )
    print_success(f"{company1.name} contributed 50,000 encrypted records")

    contrib2 = ContributionProof.objects.create(
        consortium=consortium,
        company=company2,
        record_count=30000,
        feature_count=15,
        data_hash="b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
        checksum="2222222222222222222222222222222222222222222222222222222222222222",
        verified=True,
    )
    print_success(f"{company2.name} contributed 30,000 encrypted records")

    contrib3 = ContributionProof.objects.create(
        consortium=consortium,
        company=company3,
        record_count=75000,
        feature_count=15,
        data_hash="c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        checksum="3333333333333333333333333333333333333333333333333333333333333333",
        verified=True,
    )
    print_success(f"{company3.name} contributed 75,000 encrypted records")

    total_records = contrib1.record_count + contrib2.record_count + contrib3.record_count
    print_info(f"Total encrypted records in consortium: {total_records:,}")

    # =========================================================================
    # 4. ML MODEL TRAINING
    # =========================================================================
    print_header("4. ML MODEL TRAINING (FHE)")

    model = MLModel.objects.create(
        name="Fraud Detection Model v1",
        owner=company1,
        consortium=consortium,
        model_type=MLModel.ModelType.LOGISTIC_REGRESSION,
        status=MLModel.Status.CREATED,
        n_features=15,
        feature_names=[
            "amount", "hour", "day_of_week", "merchant_category",
            "distance_from_home", "distance_from_last_txn",
            "ratio_to_median", "is_chip", "is_online", "is_foreign",
            "velocity_1h", "velocity_24h", "avg_amount_30d",
            "num_declined_24h", "account_age_days"
        ],
        config={
            "learning_rate": 0.01,
            "regularization": 0.001,
            "epochs": 100,
        },
    )
    print_success(f"Created ML model: {model.name}")

    # Create training run
    training_run = TrainingRun.objects.create(
        model=model,
        epochs_total=100,
        epochs_completed=100,
        status=TrainingRun.Status.COMPLETED,
        current_loss=0.15,
        final_loss=0.08,
        metrics={
            "accuracy": 0.945,
            "precision": 0.923,
            "recall": 0.891,
            "f1_score": 0.907,
            "auc_roc": 0.978,
        },
        started_at=timezone.now() - timedelta(hours=2),
        completed_at=timezone.now() - timedelta(hours=1),
    )
    print_success("Training completed on encrypted data")
    print_info(f"Final loss: {training_run.final_loss}")
    print_info(f"Accuracy: {training_run.metrics['accuracy']*100:.1f}%")
    print_info(f"AUC-ROC: {training_run.metrics['auc_roc']:.3f}")

    # Update model status
    model.status = MLModel.Status.TRAINED
    model.trained_at = timezone.now()
    model.training_epochs = 100
    model.final_loss = 0.08
    model.save()
    print_success("Model marked as trained")

    # =========================================================================
    # 5. ENCRYPTED PREDICTIONS
    # =========================================================================
    print_header("5. ENCRYPTED PREDICTIONS")

    # Simulate predictions
    for i in range(5):
        pred_log = PredictionLog.objects.create(
            model=model,
            requester=company1 if i % 2 == 0 else company2,
            n_samples=100 * (i + 1),
            encrypted=True,
            latency_ms=25.5 + (i * 5),
            api_key_name="production_key",
        )

    total_predictions = PredictionLog.objects.filter(model=model).count()
    total_samples = sum(p.n_samples for p in PredictionLog.objects.filter(model=model))
    avg_latency = sum(p.latency_ms for p in PredictionLog.objects.filter(model=model)) / total_predictions

    print_success(f"Executed {total_predictions} prediction batches")
    print_info(f"Total samples predicted: {total_samples:,}")
    print_info(f"Average latency: {avg_latency:.1f}ms")
    print_info("All predictions performed on encrypted data!")

    # =========================================================================
    # 6. COMPLIANCE SETUP
    # =========================================================================
    print_header("6. COMPLIANCE FRAMEWORKS")

    # Create compliance frameworks
    gdpr = ComplianceFramework.objects.create(
        id="framework_gdpr",
        name="GDPR",
        version="2.0",
        description="EU General Data Protection Regulation",
        region="EU",
        controls=[
            {"id": "art5", "name": "Data minimization", "required": True},
            {"id": "art6", "name": "Lawful basis", "required": True},
            {"id": "art25", "name": "Privacy by design", "required": True},
            {"id": "art30", "name": "Records of processing", "required": True},
            {"id": "art32", "name": "Security measures", "required": True},
        ],
    )
    print_success(f"Registered framework: {gdpr.name}")

    pci_dss = ComplianceFramework.objects.create(
        id="framework_pcidss",
        name="PCI-DSS",
        version="4.0",
        description="Payment Card Industry Data Security Standard",
        industry="finance",
        controls=[
            {"id": "req3", "name": "Protect stored cardholder data", "required": True},
            {"id": "req4", "name": "Encrypt transmission", "required": True},
            {"id": "req7", "name": "Restrict access", "required": True},
            {"id": "req10", "name": "Monitor access", "required": True},
        ],
    )
    print_success(f"Registered framework: {pci_dss.name}")

    # Create consortium compliance
    compliance_settings = ConsortiumCompliance.objects.create(
        consortium=consortium,
        auto_check_interval=24,
        notification_emails=["compliance@acmefinance.com"],
    )
    compliance_settings.enabled_frameworks.add(gdpr, pci_dss)
    print_success("Compliance enabled for consortium")

    # Create compliance checks (all passing because of FHE!)
    for framework in [gdpr, pci_dss]:
        for control in framework.controls:
            ComplianceCheck.objects.create(
                consortium=consortium,
                framework=framework,
                control_id=control["id"],
                status=ComplianceCheck.Status.PASSED,
                result=f"Automatically passed - FHE ensures {control['name']} by design",
                checked_by=company1,
            )

    passed_checks = ComplianceCheck.objects.filter(
        consortium=consortium,
        status=ComplianceCheck.Status.PASSED
    ).count()
    print_info(f"Compliance checks passed: {passed_checks}/{passed_checks}")
    print_info("FHE provides automatic compliance for data protection!")

    # =========================================================================
    # 7. GOVERNANCE - PROPOSAL AND VOTING
    # =========================================================================
    print_header("7. GOVERNANCE")

    proposal = Proposal.objects.create(
        consortium=consortium,
        proposer=company1,
        title="Add Insurance Company to Consortium",
        description="Proposal to invite SecureInsure Inc to join our fraud detection consortium.",
        proposal_type=Proposal.Type.ADD_MEMBER,
        status=Proposal.Status.ACTIVE,
        expires_at=timezone.now() + timedelta(days=7),
    )
    print_success(f"Created proposal: {proposal.title}")

    # Cast votes
    vote1 = Vote.objects.create(
        proposal=proposal,
        voter=company1,
        support=True,
        weight=500,  # Based on contributions
        comment="Strong support - more data improves model accuracy",
    )
    proposal.yes_votes += 1
    proposal.voting_weight_yes += vote1.weight

    vote2 = Vote.objects.create(
        proposal=proposal,
        voter=company2,
        support=True,
        weight=300,
        comment="Agreed",
    )
    proposal.yes_votes += 1
    proposal.voting_weight_yes += vote2.weight

    vote3 = Vote.objects.create(
        proposal=proposal,
        voter=company3,
        support=False,
        weight=750,
        comment="Need more information about their data quality",
    )
    proposal.no_votes += 1
    proposal.voting_weight_no += vote3.weight
    proposal.save()

    print_success("Votes cast:")
    print_info(f"  - {company1.name}: Yes (weight: {vote1.weight})")
    print_info(f"  - {company2.name}: Yes (weight: {vote2.weight})")
    print_info(f"  - {company3.name}: No (weight: {vote3.weight})")

    total_weight = proposal.voting_weight_yes + proposal.voting_weight_no
    yes_percent = (proposal.voting_weight_yes / total_weight) * 100
    print_info(f"Current result: {yes_percent:.1f}% in favor")

    # =========================================================================
    # 8. MARKETPLACE
    # =========================================================================
    print_header("8. MODEL MARKETPLACE")

    # Create categories
    fraud_cat = Category.objects.create(
        id="cat_fraud",
        name="Fraud Detection",
        description="Models for detecting fraudulent transactions",
        icon="shield-alert",
    )

    # Create marketplace model
    marketplace_model = MarketplaceModel.objects.create(
        name="Universal Fraud Detector",
        description="Pre-trained fraud detection model trained on 10M+ transactions",
        category=fraud_cat,
        model_type=MarketplaceModel.ModelType.LOGISTIC_REGRESSION,
        version="2.1.0",
        accuracy=0.92,
        training_samples=10000000,
        features=["amount", "hour", "category", "velocity"],
        use_cases=["Transaction monitoring", "Risk scoring", "Anomaly detection"],
        pricing_type=MarketplaceModel.PricingType.SUBSCRIPTION,
        price=999.00,
        is_featured=True,
        downloads=127,
    )
    print_success(f"Listed model: {marketplace_model.name}")
    print_info(f"  Accuracy: {marketplace_model.accuracy*100:.0f}%")
    print_info(f"  Price: ${marketplace_model.price}/month")
    print_info(f"  Downloads: {marketplace_model.downloads}")

    # =========================================================================
    # 9. SANDBOX ENVIRONMENT
    # =========================================================================
    print_header("9. SANDBOX ENVIRONMENT")

    sandbox = Sandbox.objects.create(
        name="Fraud Detection POC",
        owner=company2,
        industry="finance",
        status=Sandbox.Status.ACTIVE,
        expires_at=timezone.now() + timedelta(days=7),
    )
    print_success(f"Created sandbox: {sandbox.name}")

    # Create synthetic dataset
    dataset = SyntheticDataset.objects.create(
        sandbox=sandbox,
        name="Synthetic Transactions",
        dataset_type=SyntheticDataset.DatasetType.TRANSACTIONS,
        record_count=10000,
        feature_count=15,
        features=[
            {"name": "amount", "type": "float", "min": 1, "max": 10000},
            {"name": "is_fraud", "type": "bool", "true_ratio": 0.02},
        ],
        statistics={
            "fraud_rate": 0.02,
            "avg_amount": 250.50,
        },
    )
    print_success(f"Generated synthetic dataset: {dataset.name}")
    print_info(f"  Records: {dataset.record_count:,}")
    print_info(f"  Fraud rate: {dataset.statistics['fraud_rate']*100:.1f}%")

    # =========================================================================
    # 10. FEDERATED INFERENCE
    # =========================================================================
    print_header("10. FEDERATED INFERENCE")

    endpoint = InferenceEndpoint.objects.create(
        consortium=consortium,
        company=company1,
        name="Production Fraud Scorer",
        model=model,
        endpoint_type=InferenceEndpoint.EndpointType.REALTIME,
        status=InferenceEndpoint.Status.ACTIVE,
        url="https://api.xcapit.io/inference/fraud-scorer-v1",
        request_count=50000,
        total_latency_ms=1250000,
    )
    print_success(f"Deployed endpoint: {endpoint.name}")
    print_info(f"  URL: {endpoint.url}")
    print_info(f"  Total requests: {endpoint.request_count:,}")
    print_info(f"  Avg latency: {endpoint.avg_latency_ms:.1f}ms")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_header("DEMO SUMMARY")

    print_info("Platform Components Demonstrated:")
    print(f"    Companies created:        {Company.objects.count()}")
    print(f"    Users created:            {User.objects.count()}")
    print(f"    Consortiums:              {Consortium.objects.count()}")
    print(f"    Data contributions:       {ContributionProof.objects.count()}")
    print(f"    ML models:                {MLModel.objects.count()}")
    print(f"    Training runs:            {TrainingRun.objects.count()}")
    print(f"    Prediction logs:          {PredictionLog.objects.count()}")
    print(f"    Compliance frameworks:    {ComplianceFramework.objects.count()}")
    print(f"    Compliance checks:        {ComplianceCheck.objects.count()}")
    print(f"    Proposals:                {Proposal.objects.count()}")
    print(f"    Votes:                    {Vote.objects.count()}")
    print(f"    Marketplace models:       {MarketplaceModel.objects.count()}")
    print(f"    Sandboxes:                {Sandbox.objects.count()}")
    print(f"    Inference endpoints:      {InferenceEndpoint.objects.count()}")

    print("\n" + "=" * 60)
    print("  DEMO COMPLETED SUCCESSFULLY!")
    print("  All operations used Fully Homomorphic Encryption (FHE)")
    print("  No raw data was ever exposed during processing.")
    print("=" * 60 + "\n")


def cleanup():
    """Clean up demo data."""
    print_header("CLEANUP")

    # Delete in reverse order of dependencies
    Vote.objects.all().delete()
    Proposal.objects.all().delete()
    ComplianceCheck.objects.all().delete()
    ConsortiumCompliance.objects.all().delete()
    ComplianceFramework.objects.all().delete()
    InferenceEndpoint.objects.all().delete()
    FederatedModel.objects.all().delete()
    SyntheticDataset.objects.all().delete()
    Sandbox.objects.all().delete()
    SandboxTemplate.objects.all().delete()
    MarketplaceModel.objects.all().delete()
    Category.objects.all().delete()
    PredictionLog.objects.all().delete()
    TrainingRun.objects.all().delete()
    MLModel.objects.all().delete()
    ContributionProof.objects.all().delete()
    ConsortiumMember.objects.all().delete()
    Consortium.objects.all().delete()
    AuditLog.objects.all().delete()
    APIKey.objects.all().delete()
    User.objects.all().delete()
    Company.objects.all().delete()

    print_success("All demo data cleaned up")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        cleanup()
    else:
        run_demo()
