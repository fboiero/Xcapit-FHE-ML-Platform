#!/usr/bin/env python3
"""
Comprehensive Evidence Tests for Xcapit FHE-ML Platform
This script runs all components and captures evidence of functionality.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Ensure SDK is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np

# Results storage
results = {
    "timestamp": datetime.now().isoformat(),
    "platform": "Xcapit FHE-ML Platform",
    "version": "1.0.0",
    "tests": []
}

def add_result(test_name, status, details):
    """Add a test result."""
    results["tests"].append({
        "name": test_name,
        "status": status,
        "details": details
    })
    print(f"{'PASSED' if status else 'FAILED'}: {test_name}")
    if details:
        for key, value in details.items():
            print(f"  {key}: {value}")

# ============================================================
# TEST 1: Linear Regression Model
# ============================================================
print("\n" + "="*60)
print("TEST 1: Linear Regression Model")
print("="*60)

try:
    from sdk.models import LinearRegression, ModelConfig
    from sdk.utils import SecureDataLoader

    np.random.seed(42)
    X = np.random.randn(100, 3)
    y = 2 * X[:, 0] + 3 * X[:, 1] - X[:, 2] + 1 + np.random.randn(100) * 0.1

    loader = SecureDataLoader(normalize=True)
    X_proc, y_proc = loader.prepare_data(X, y)

    model = LinearRegression(learning_rate=0.01, n_epochs=50)
    predictions = model.predict_plaintext(X_proc)

    add_result("Linear Regression - Initialization", True, {
        "n_features": X.shape[1],
        "n_samples": X.shape[0],
        "predictions_shape": str(predictions.shape)
    })
except Exception as e:
    add_result("Linear Regression - Initialization", False, {"error": str(e)})

# ============================================================
# TEST 2: Logistic Regression Model
# ============================================================
print("\n" + "="*60)
print("TEST 2: Logistic Regression Model")
print("="*60)

try:
    from sdk.models import LogisticRegression

    np.random.seed(42)
    X = np.random.randn(100, 2)
    y = (X[:, 0] + X[:, 1] > 0).astype(float)

    loader = SecureDataLoader(normalize=True)
    X_proc, y_proc = loader.prepare_data(X, y)

    model = LogisticRegression(learning_rate=0.1, n_epochs=50)
    predictions = model.predict_plaintext(X_proc)

    add_result("Logistic Regression - Initialization", True, {
        "n_features": X.shape[1],
        "n_samples": X.shape[0],
        "unique_predictions": len(np.unique(predictions))
    })
except Exception as e:
    add_result("Logistic Regression - Initialization", False, {"error": str(e)})

# ============================================================
# TEST 3: Decision Tree Classifier
# ============================================================
print("\n" + "="*60)
print("TEST 3: Decision Tree Classifier")
print("="*60)

try:
    from sdk.models import DecisionTreeClassifier, TreeConfig

    np.random.seed(42)
    X = np.random.randn(100, 4)
    y = (X[:, 0] > 0).astype(int)

    config = TreeConfig(max_depth=3, min_samples_split=5)
    model = DecisionTreeClassifier(config=config)
    model.fit(X, y)
    predictions = model.predict(X)
    accuracy = np.mean(predictions == y)

    add_result("Decision Tree Classifier", True, {
        "max_depth": config.max_depth,
        "accuracy": f"{accuracy:.2%}",
        "n_features": X.shape[1]
    })
except Exception as e:
    add_result("Decision Tree Classifier", False, {"error": str(e)})

# ============================================================
# TEST 4: KMeans Clustering
# ============================================================
print("\n" + "="*60)
print("TEST 4: KMeans Clustering")
print("="*60)

try:
    from sdk.models import KMeans, KMeansConfig

    np.random.seed(42)
    X = np.vstack([
        np.random.randn(30, 2) + [2, 2],
        np.random.randn(30, 2) + [-2, -2],
        np.random.randn(30, 2) + [2, -2]
    ])

    config = KMeansConfig(n_clusters=3, max_iter=100)
    model = KMeans(config=config)
    model.fit(X)
    labels = model.predict(X)

    add_result("KMeans Clustering", True, {
        "n_clusters": config.n_clusters,
        "unique_labels": len(np.unique(labels)),
        "n_samples": X.shape[0]
    })
except Exception as e:
    add_result("KMeans Clustering", False, {"error": str(e)})

# ============================================================
# TEST 5: Model Serialization
# ============================================================
print("\n" + "="*60)
print("TEST 5: Model Serialization")
print("="*60)

try:
    from sdk.utils.serialization import save_model, load_model, get_model_info
    import tempfile
    import os

    model = LinearRegression(learning_rate=0.01, n_epochs=50)

    with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
        temp_path = f.name

    save_model(model, temp_path, metadata={"test": "evidence"})
    info = get_model_info(temp_path)

    os.unlink(temp_path)

    add_result("Model Serialization", True, {
        "model_type": info.get("model_type", "unknown"),
        "saved_successfully": True
    })
except Exception as e:
    add_result("Model Serialization", False, {"error": str(e)})

# ============================================================
# TEST 6: Data Validation
# ============================================================
print("\n" + "="*60)
print("TEST 6: Data Validation")
print("="*60)

try:
    from sdk.utils.validation import (
        validate_numeric_data,
        validate_data_shape,
        check_fhe_compatibility
    )

    X = np.random.randn(100, 5)

    # Test validation functions
    validate_numeric_data(X)
    validate_data_shape(X, min_samples=10, min_features=2)
    compat = check_fhe_compatibility(X)

    add_result("Data Validation", True, {
        "is_fhe_compatible": compat["compatible"],
        "n_features": compat["stats"]["n_features"],
        "n_samples": compat["stats"]["n_samples"]
    })
except Exception as e:
    add_result("Data Validation", False, {"error": str(e)})

# ============================================================
# TEST 7: Training History
# ============================================================
print("\n" + "="*60)
print("TEST 7: Training History")
print("="*60)

try:
    from sdk.models import TrainingHistory

    history = TrainingHistory()
    for i in range(10):
        history.add_epoch(loss=1.0/(i+1), accuracy=0.5 + i*0.05)

    add_result("Training History", True, {
        "epochs": history.epochs,
        "final_loss": f"{history.losses[-1]:.4f}",
        "final_accuracy": f"{history.metrics['accuracy'][-1]:.2%}"
    })
except Exception as e:
    add_result("Training History", False, {"error": str(e)})

# ============================================================
# TEST 8: FHE Model Factory
# ============================================================
print("\n" + "="*60)
print("TEST 8: FHE Model Factory")
print("="*60)

try:
    from sdk.models import FHEModel

    lr_model = FHEModel.LinearRegression(learning_rate=0.1)
    log_model = FHEModel.LogisticRegression(learning_rate=0.05)

    add_result("FHE Model Factory", True, {
        "linear_regression_created": True,
        "logistic_regression_created": True,
        "lr_learning_rate": lr_model.config.learning_rate,
        "log_learning_rate": log_model.config.learning_rate
    })
except Exception as e:
    add_result("FHE Model Factory", False, {"error": str(e)})

# ============================================================
# TEST 9: Data Quality Calculator
# ============================================================
print("\n" + "="*60)
print("TEST 9: Data Quality Calculator")
print("="*60)

try:
    from sdk.quality import DataQualityCalculator
    import pandas as pd

    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [1.0, 2.0, None, 4.0, 5.0],
        'C': ['a', 'b', 'c', 'd', 'e']
    })

    calculator = DataQualityCalculator()
    report = calculator.calculate(df)

    add_result("Data Quality Calculator", True, {
        "overall_score": f"{report['overall_score']:.2%}",
        "completeness": f"{report['dimensions']['completeness']:.2%}",
        "n_issues": len(report.get('issues', []))
    })
except Exception as e:
    add_result("Data Quality Calculator", False, {"error": str(e)})

# ============================================================
# TEST 10: Governance Module
# ============================================================
print("\n" + "="*60)
print("TEST 10: Governance Module")
print("="*60)

try:
    from sdk.api.governance import (
        ConsortiumStore,
        ProposalStore,
        ContributionStore,
        AuditStore
    )

    consortium_store = ConsortiumStore()
    proposal_store = ProposalStore()
    contribution_store = ContributionStore()
    audit_store = AuditStore()

    add_result("Governance Module", True, {
        "consortium_store": "initialized",
        "proposal_store": "initialized",
        "contribution_store": "initialized",
        "audit_store": "initialized"
    })
except Exception as e:
    add_result("Governance Module", False, {"error": str(e)})

# ============================================================
# TEST 11: Compliance Module
# ============================================================
print("\n" + "="*60)
print("TEST 11: Compliance Module")
print("="*60)

try:
    from sdk.api.compliance_routes import ComplianceFramework

    frameworks = [f.value for f in ComplianceFramework]

    add_result("Compliance Module", True, {
        "available_frameworks": frameworks,
        "n_frameworks": len(frameworks)
    })
except Exception as e:
    add_result("Compliance Module", False, {"error": str(e)})

# ============================================================
# TEST 12: Sandbox Module
# ============================================================
print("\n" + "="*60)
print("TEST 12: Sandbox Module")
print("="*60)

try:
    from sdk.api.sandbox import (
        SandboxTemplateManager,
        SyntheticDataGenerator,
        ExperimentManager
    )

    template_mgr = SandboxTemplateManager()
    templates = template_mgr.list_templates()

    data_gen = SyntheticDataGenerator()
    exp_mgr = ExperimentManager()

    add_result("Sandbox Module", True, {
        "templates_available": len(templates),
        "template_industries": list(set(t.industry for t in templates)),
        "data_generator": "initialized",
        "experiment_manager": "initialized"
    })
except Exception as e:
    add_result("Sandbox Module", False, {"error": str(e)})

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

passed = sum(1 for t in results["tests"] if t["status"])
failed = sum(1 for t in results["tests"] if not t["status"])
total = len(results["tests"])

print(f"\nTotal Tests: {total}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Pass Rate: {passed/total:.1%}")

results["summary"] = {
    "total": total,
    "passed": passed,
    "failed": failed,
    "pass_rate": f"{passed/total:.1%}"
}

# Save results
output_path = Path(__file__).parent / "evidence_results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\nResults saved to: {output_path}")
