"""Data Quality module for Xcapit FHE-ML Platform.

Provides quality assessment without accessing actual data values,
working only with metadata and aggregated statistics.
"""

from .calculator import (
    DataProfile,
    DataQualityCalculator,
    QualityScore,
    calculate_quality_from_encrypted_metadata,
)

__all__ = [
    "DataProfile",
    "QualityScore",
    "DataQualityCalculator",
    "calculate_quality_from_encrypted_metadata",
]
