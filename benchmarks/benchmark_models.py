#!/usr/bin/env python3
"""Performance benchmarks for FHE models.

Measures training time, prediction time, and accuracy for all SDK models
on synthetic and standard datasets.

Usage:
    python benchmarks/benchmark_models.py
    python benchmarks/benchmark_models.py --models linear-regression logistic-regression
    python benchmarks/benchmark_models.py --sizes 100 500 1000
"""

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from sklearn.datasets import make_classification, make_regression, make_blobs
from sklearn.metrics import (
    accuracy_score,
    mean_squared_error,
    r2_score,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    model_name: str
    dataset_size: int
    n_features: int
    train_time: float
    predict_time: float
    metric_name: str
    metric_value: float
    memory_mb: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs."""

    n_epochs: int = 50
    learning_rate: float = 0.01
    n_clusters: int = 3
    test_size: float = 0.2
    random_state: int = 42
    verbose: bool = False


def generate_regression_data(
    n_samples: int,
    n_features: int = 10,
    noise: float = 0.1,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic regression data."""
    X, y = make_regression(
        n_samples=n_samples,
        n_features=n_features,
        noise=noise,
        random_state=random_state,
    )
    # Normalize
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    y = (y - y.mean()) / y.std()
    return X, y


def generate_classification_data(
    n_samples: int,
    n_features: int = 10,
    n_classes: int = 2,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic classification data."""
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=min(n_features, 5),
        n_redundant=min(n_features - 5, 2) if n_features > 5 else 0,
        n_classes=n_classes,
        random_state=random_state,
    )
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    return X, y


def generate_clustering_data(
    n_samples: int,
    n_features: int = 10,
    n_clusters: int = 3,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic clustering data."""
    X, y = make_blobs(
        n_samples=n_samples,
        n_features=n_features,
        centers=n_clusters,
        random_state=random_state,
    )
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    return X, y


def benchmark_linear_regression(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    config: BenchmarkConfig,
) -> BenchmarkResult:
    """Benchmark LinearRegression model."""
    from sdk.models import LinearRegression, ModelConfig

    model_config = ModelConfig(
        learning_rate=config.learning_rate,
        n_epochs=config.n_epochs,
        verbose=config.verbose,
    )

    model = LinearRegression(config=model_config)

    # Train
    start = time.perf_counter()
    model._fit_plaintext(X_train, y_train)
    train_time = time.perf_counter() - start

    # Predict
    start = time.perf_counter()
    y_pred = model._predict_plaintext(X_test)
    predict_time = time.perf_counter() - start

    # Metrics
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    return BenchmarkResult(
        model_name="LinearRegression",
        dataset_size=len(X_train),
        n_features=X_train.shape[1],
        train_time=train_time,
        predict_time=predict_time,
        metric_name="R2",
        metric_value=r2,
        extra={"mse": mse, "final_loss": model.history.losses[-1] if model.history.losses else None},
    )


def benchmark_logistic_regression(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    config: BenchmarkConfig,
) -> BenchmarkResult:
    """Benchmark LogisticRegression model."""
    from sdk.models import LogisticRegression, ModelConfig

    model_config = ModelConfig(
        learning_rate=config.learning_rate,
        n_epochs=config.n_epochs,
        verbose=config.verbose,
    )

    model = LogisticRegression(config=model_config)

    # Train
    start = time.perf_counter()
    model._fit_plaintext(X_train, y_train)
    train_time = time.perf_counter() - start

    # Predict
    start = time.perf_counter()
    y_pred = model._predict_plaintext(X_test)
    y_pred_binary = (y_pred > 0.5).astype(int)
    predict_time = time.perf_counter() - start

    # Metrics
    accuracy = accuracy_score(y_test, y_pred_binary)

    return BenchmarkResult(
        model_name="LogisticRegression",
        dataset_size=len(X_train),
        n_features=X_train.shape[1],
        train_time=train_time,
        predict_time=predict_time,
        metric_name="Accuracy",
        metric_value=accuracy,
        extra={"final_loss": model.history.losses[-1] if model.history.losses else None},
    )


def benchmark_decision_tree(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    config: BenchmarkConfig,
) -> BenchmarkResult:
    """Benchmark DecisionTreeClassifier model."""
    from sdk.models import DecisionTreeClassifier, TreeConfig

    tree_config = TreeConfig(
        max_depth=4,
        learning_rate=config.learning_rate,
        n_epochs=min(config.n_epochs, 30),
    )

    model = DecisionTreeClassifier(config=tree_config)

    # Train
    start = time.perf_counter()
    model._fit_plaintext(X_train, y_train)
    train_time = time.perf_counter() - start

    # Predict
    start = time.perf_counter()
    y_pred = model._predict_plaintext(X_test)
    predict_time = time.perf_counter() - start

    # Metrics
    accuracy = accuracy_score(y_test, y_pred)

    return BenchmarkResult(
        model_name="DecisionTreeClassifier",
        dataset_size=len(X_train),
        n_features=X_train.shape[1],
        train_time=train_time,
        predict_time=predict_time,
        metric_name="Accuracy",
        metric_value=accuracy,
        extra={"max_depth": tree_config.max_depth},
    )


def benchmark_kmeans(
    X: np.ndarray,
    y_true: np.ndarray,
    config: BenchmarkConfig,
) -> BenchmarkResult:
    """Benchmark KMeans model."""
    from sdk.models import KMeans, KMeansConfig

    kmeans_config = KMeansConfig(
        n_clusters=config.n_clusters,
        max_iter=config.n_epochs,
    )

    model = KMeans(config=kmeans_config)

    # Fit
    start = time.perf_counter()
    model._fit_plaintext(X)
    train_time = time.perf_counter() - start

    # Predict
    start = time.perf_counter()
    labels = model._predict_plaintext(X)
    predict_time = time.perf_counter() - start

    # Metrics
    if len(np.unique(labels)) > 1:
        silhouette = silhouette_score(X, labels)
    else:
        silhouette = 0.0

    return BenchmarkResult(
        model_name="KMeans",
        dataset_size=len(X),
        n_features=X.shape[1],
        train_time=train_time,
        predict_time=predict_time,
        metric_name="Silhouette",
        metric_value=silhouette,
        extra={
            "n_clusters": config.n_clusters,
            "inertia": model.inertia if hasattr(model, "inertia") else None,
        },
    )


def run_benchmarks(
    models: List[str],
    sizes: List[int],
    n_features: int = 10,
    config: Optional[BenchmarkConfig] = None,
) -> List[BenchmarkResult]:
    """Run benchmarks for specified models and dataset sizes."""
    config = config or BenchmarkConfig()
    results = []

    for size in sizes:
        print(f"\n{'='*60}")
        print(f"Dataset size: {size} samples, {n_features} features")
        print("=" * 60)

        # LinearRegression
        if "linear-regression" in models or "all" in models:
            print("\nBenchmarking LinearRegression...")
            X, y = generate_regression_data(size, n_features, random_state=config.random_state)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=config.test_size, random_state=config.random_state
            )
            result = benchmark_linear_regression(X_train, y_train, X_test, y_test, config)
            results.append(result)
            print(f"  Train: {result.train_time:.4f}s | Predict: {result.predict_time:.4f}s | R2: {result.metric_value:.4f}")

        # LogisticRegression
        if "logistic-regression" in models or "all" in models:
            print("\nBenchmarking LogisticRegression...")
            X, y = generate_classification_data(size, n_features, n_classes=2, random_state=config.random_state)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=config.test_size, random_state=config.random_state
            )
            result = benchmark_logistic_regression(X_train, y_train, X_test, y_test, config)
            results.append(result)
            print(f"  Train: {result.train_time:.4f}s | Predict: {result.predict_time:.4f}s | Accuracy: {result.metric_value:.4f}")

        # DecisionTree
        if "decision-tree" in models or "all" in models:
            print("\nBenchmarking DecisionTreeClassifier...")
            X, y = generate_classification_data(size, n_features, n_classes=2, random_state=config.random_state)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=config.test_size, random_state=config.random_state
            )
            result = benchmark_decision_tree(X_train, y_train, X_test, y_test, config)
            results.append(result)
            print(f"  Train: {result.train_time:.4f}s | Predict: {result.predict_time:.4f}s | Accuracy: {result.metric_value:.4f}")

        # KMeans
        if "kmeans" in models or "all" in models:
            print("\nBenchmarking KMeans...")
            X, y = generate_clustering_data(size, n_features, n_clusters=config.n_clusters, random_state=config.random_state)
            result = benchmark_kmeans(X, y, config)
            results.append(result)
            print(f"  Train: {result.train_time:.4f}s | Predict: {result.predict_time:.4f}s | Silhouette: {result.metric_value:.4f}")

    return results


def save_results(results: List[BenchmarkResult], output_path: Path) -> None:
    """Save benchmark results to JSON."""
    data = {
        "timestamp": datetime.utcnow().isoformat(),
        "results": [
            {
                "model": r.model_name,
                "dataset_size": r.dataset_size,
                "n_features": r.n_features,
                "train_time_s": r.train_time,
                "predict_time_s": r.predict_time,
                "metric_name": r.metric_name,
                "metric_value": r.metric_value,
                **r.extra,
            }
            for r in results
        ],
    }

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nResults saved to: {output_path}")


def print_summary(results: List[BenchmarkResult]) -> None:
    """Print benchmark summary table."""
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"{'Model':<25} {'Size':>8} {'Train(s)':>10} {'Predict(s)':>10} {'Metric':>15}")
    print("-" * 80)

    for r in results:
        metric_str = f"{r.metric_name}={r.metric_value:.4f}"
        print(f"{r.model_name:<25} {r.dataset_size:>8} {r.train_time:>10.4f} {r.predict_time:>10.4f} {metric_str:>15}")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Benchmark FHE-ML models")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["all"],
        choices=["all", "linear-regression", "logistic-regression", "decision-tree", "kmeans"],
        help="Models to benchmark",
    )
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        default=[100, 500, 1000],
        help="Dataset sizes to test",
    )
    parser.add_argument(
        "--features",
        type=int,
        default=10,
        help="Number of features",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Training epochs",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file for results",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose training output",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Xcapit FHE-ML Platform - Model Benchmarks")
    print("=" * 60)
    print(f"Models: {args.models}")
    print(f"Sizes: {args.sizes}")
    print(f"Features: {args.features}")
    print(f"Epochs: {args.epochs}")

    config = BenchmarkConfig(
        n_epochs=args.epochs,
        verbose=args.verbose,
    )

    results = run_benchmarks(
        models=args.models,
        sizes=args.sizes,
        n_features=args.features,
        config=config,
    )

    print_summary(results)

    if args.output:
        save_results(results, Path(args.output))


if __name__ == "__main__":
    main()
