"""Data quality calculator for profiling and assessing datasets.

Provides missing-value analysis, outlier detection, correlation analysis,
and composite quality scores.
"""

from typing import Any

import numpy as np

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def _require_pandas():
    if not HAS_PANDAS:
        raise ImportError(
            "pandas is required for data quality analysis. Install it with: pip install pandas"
        )


class DataQualityCalculator:
    """Assess and profile the quality of tabular datasets.

    Analyses completeness, consistency, outliers, and correlations
    to produce an overall quality report.

    Example:
        >>> from sdk.quality import DataQualityCalculator
        >>> calc = DataQualityCalculator()
        >>> report = calc.report(df)
        >>> print(report["overall_score"])
    """

    def __init__(self):
        pass

    def profile(self, df: "pd.DataFrame") -> dict[str, Any]:
        """Generate a high-level profile of the dataset.

        Args:
            df: Input DataFrame.

        Returns:
            Dict with n_rows, n_cols, dtypes, memory_usage, etc.
        """
        _require_pandas()

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        return {
            "n_rows": len(df),
            "n_cols": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
            "duplicated_rows": int(df.duplicated().sum()),
        }

    def missing_analysis(self, df: "pd.DataFrame") -> dict[str, Any]:
        """Analyse missing values in the dataset.

        Args:
            df: Input DataFrame.

        Returns:
            Dict with per-column and overall missing-value statistics.
        """
        _require_pandas()

        total_cells = df.shape[0] * df.shape[1]
        missing_counts = df.isnull().sum()
        total_missing = int(missing_counts.sum())

        per_column = {}
        for col in df.columns:
            count = int(missing_counts[col])
            per_column[col] = {
                "count": count,
                "percentage": round(count / len(df) * 100, 2) if len(df) > 0 else 0.0,
            }

        return {
            "total_missing": total_missing,
            "total_cells": total_cells,
            "overall_missing_pct": round(total_missing / total_cells * 100, 2)
            if total_cells > 0
            else 0.0,
            "per_column": per_column,
            "columns_with_missing": [col for col, info in per_column.items() if info["count"] > 0],
        }

    def outlier_detection(
        self,
        df: "pd.DataFrame",
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> dict[str, Any]:
        """Detect outliers in numeric columns.

        Args:
            df: Input DataFrame.
            method: Detection method. "iqr" (interquartile range) or
                "zscore" (z-score with threshold).
            threshold: IQR multiplier (default 1.5) or z-score threshold
                (default 3.0 when method="zscore").

        Returns:
            Dict with per-column outlier counts and indices.
        """
        _require_pandas()

        numeric_df = df.select_dtypes(include=[np.number])
        results: dict[str, Any] = {}
        total_outliers = 0

        for col in numeric_df.columns:
            values = numeric_df[col].dropna().values

            if len(values) == 0:
                results[col] = {"count": 0, "percentage": 0.0, "indices": []}
                continue

            if method == "zscore":
                z_threshold = threshold if threshold > 2 else 3.0
                mean = np.mean(values)
                std = np.std(values)
                if std == 0:
                    outlier_mask = np.zeros(len(numeric_df[col]), dtype=bool)
                else:
                    z_scores = np.abs((numeric_df[col].values - mean) / std)
                    outlier_mask = z_scores > z_threshold
            else:
                # IQR method
                q1 = np.percentile(values, 25)
                q3 = np.percentile(values, 75)
                iqr = q3 - q1
                lower = q1 - threshold * iqr
                upper = q3 + threshold * iqr
                col_values = numeric_df[col].values
                outlier_mask = (col_values < lower) | (col_values > upper)

            # Handle NaN in original column — don't flag NaN as outlier
            nan_mask = numeric_df[col].isnull().values
            outlier_mask = outlier_mask & ~nan_mask

            count = int(outlier_mask.sum())
            total_outliers += count

            indices = list(np.where(outlier_mask)[0])

            results[col] = {
                "count": count,
                "percentage": round(count / len(df) * 100, 2) if len(df) > 0 else 0.0,
                "indices": indices[:100],  # Limit for readability
            }

        return {
            "method": method,
            "threshold": threshold,
            "total_outliers": total_outliers,
            "per_column": results,
        }

    def correlation_analysis(self, df: "pd.DataFrame") -> dict[str, Any]:
        """Compute correlation matrix for numeric columns.

        Args:
            df: Input DataFrame.

        Returns:
            Dict with correlation matrix and highly correlated pairs.
        """
        _require_pandas()

        numeric_df = df.select_dtypes(include=[np.number])

        if numeric_df.shape[1] < 2:
            return {
                "correlation_matrix": {},
                "high_correlations": [],
            }

        corr_matrix = numeric_df.corr()

        # Find highly correlated pairs (|r| > 0.8, excluding self-correlation)
        high_corr = []
        cols = corr_matrix.columns.tolist()
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                r = corr_matrix.iloc[i, j]
                if abs(r) > 0.8:
                    high_corr.append(
                        {
                            "feature_1": cols[i],
                            "feature_2": cols[j],
                            "correlation": round(float(r), 4),
                        }
                    )

        # Sort by absolute correlation descending
        high_corr.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "correlation_matrix": corr_matrix.to_dict(),
            "high_correlations": high_corr,
        }

    def completeness_score(self, df: "pd.DataFrame") -> float:
        """Compute a completeness score (0-1) based on non-missing values.

        Args:
            df: Input DataFrame.

        Returns:
            Score between 0 (all missing) and 1 (no missing).
        """
        _require_pandas()

        total = df.shape[0] * df.shape[1]
        if total == 0:
            return 1.0
        missing = int(df.isnull().sum().sum())
        return round(1.0 - missing / total, 4)

    def consistency_score(self, df: "pd.DataFrame") -> float:
        """Compute a consistency score (0-1) based on duplicate rows and type uniformity.

        A perfect score means no duplicates and consistent types within columns.

        Args:
            df: Input DataFrame.

        Returns:
            Score between 0 and 1.
        """
        _require_pandas()

        if len(df) == 0:
            return 1.0

        # Duplicate penalty
        dup_ratio = df.duplicated().sum() / len(df)

        # Type consistency — check if numeric columns have mixed types
        type_issues = 0
        for col in df.columns:
            if df[col].dtype == object:
                # Check if values are mixed numeric/string
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    numeric_count = pd.to_numeric(non_null, errors="coerce").notna().sum()
                    if 0 < numeric_count < len(non_null):
                        type_issues += 1

        type_penalty = type_issues / max(len(df.columns), 1)

        score = 1.0 - (dup_ratio * 0.5 + type_penalty * 0.5)
        return round(max(0.0, min(1.0, score)), 4)

    def report(self, df: "pd.DataFrame") -> dict[str, Any]:
        """Generate a comprehensive data quality report.

        Args:
            df: Input DataFrame.

        Returns:
            Dict with profile, missing analysis, outlier detection,
            correlation analysis, and overall quality score.
        """
        _require_pandas()

        profile = self.profile(df)
        missing = self.missing_analysis(df)
        outliers = self.outlier_detection(df)
        correlations = self.correlation_analysis(df)
        completeness = self.completeness_score(df)
        consistency = self.consistency_score(df)

        # Outlier penalty
        total_values = df.select_dtypes(include=[np.number]).shape[0] * max(
            df.select_dtypes(include=[np.number]).shape[1], 1
        )
        outlier_ratio = outliers["total_outliers"] / total_values if total_values > 0 else 0.0
        outlier_score = max(0.0, 1.0 - outlier_ratio * 5)  # Penalise heavily

        # Overall score: weighted average
        overall = round(completeness * 0.4 + consistency * 0.3 + outlier_score * 0.3, 4)

        return {
            "profile": profile,
            "missing": missing,
            "outliers": outliers,
            "correlations": correlations,
            "completeness_score": completeness,
            "consistency_score": consistency,
            "outlier_score": round(outlier_score, 4),
            "overall_score": overall,
        }
