#!/usr/bin/env python3
"""Generate synthetic fraud detection data for bank consortium demo.

This script generates two datasets with different fraud patterns:
- Bank A (5000 records): Late-night high-value, rapid velocity, online+international
- Bank B (3000 records): Travel+distance, gas station, weekend patterns

Each bank can detect ~70-75% of their own fraud patterns, but miss the other bank's
patterns. Combined in a consortium, they can achieve ~87% accuracy.
"""

import argparse
import os
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd

# Set seed for reproducibility
np.random.seed(42)

# Merchant categories
MERCHANT_CATEGORIES = ['retail', 'food', 'travel', 'online', 'gas', 'entertainment']

# Fraud rate (2% baseline)
BASE_FRAUD_RATE = 0.02


def generate_base_transaction(n_samples: int) -> pd.DataFrame:
    """Generate base transaction features without fraud patterns."""

    data = {
        # Transaction features
        'amount': np.random.lognormal(mean=4.0, sigma=1.2, size=n_samples),  # $1 - ~$50,000
        'merchant_category': np.random.choice(MERCHANT_CATEGORIES, n_samples),
        'hour_of_day': np.random.choice(24, n_samples),
        'is_international': np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        'distance_from_home': np.abs(np.random.exponential(scale=15, size=n_samples)),

        # Behavior features
        'avg_monthly_spend': np.random.lognormal(mean=7.0, sigma=0.8, size=n_samples),
        'num_txns_last_24h': np.random.poisson(lam=3, size=n_samples),
        'ratio_to_avg_amount': np.random.lognormal(mean=0, sigma=0.5, size=n_samples),
    }

    df = pd.DataFrame(data)

    # Clip amount to reasonable range
    df['amount'] = df['amount'].clip(1, 50000)

    # Clip distance
    df['distance_from_home'] = df['distance_from_home'].clip(0, 500)

    return df


def inject_bank_a_fraud_patterns(df: pd.DataFrame) -> np.ndarray:
    """Inject Bank A's fraud patterns focused on TIME and VELOCITY features.

    Bank A's fraud patterns:
    1. Late-night transactions (10pm-6am)
    2. High transaction velocity (>4 in 24h)
    3. International transactions

    Demo target accuracies:
    - Bank A alone: ~72% (can detect these patterns)
    - Bank B alone: ~68% (focuses on different features, misses these)
    - Consortium: ~87% (learns all patterns from combined data)
    """
    n = len(df)
    fraud_labels = np.zeros(n, dtype=int)

    # Pattern 1: Late-night transactions (10pm-6am)
    late_night = (df['hour_of_day'] >= 22) | (df['hour_of_day'] <= 6)
    fraud_labels[late_night & (np.random.random(n) < 0.35)] = 1

    # Pattern 2: High transaction velocity (>4 in 24h)
    high_velocity = df['num_txns_last_24h'] > 4
    fraud_labels[high_velocity & (np.random.random(n) < 0.40)] = 1

    # Pattern 3: International transactions
    international = df['is_international'] == 1
    fraud_labels[international & (np.random.random(n) < 0.50)] = 1

    return fraud_labels


def inject_bank_b_fraud_patterns(df: pd.DataFrame) -> np.ndarray:
    """Inject Bank B's fraud patterns focused on LOCATION and MERCHANT features.

    Bank B's fraud patterns:
    1. Far from home (>30 miles)
    2. Gas station transactions
    3. Travel merchant category

    Demo target accuracies:
    - Bank A alone: ~72% (focuses on different features, misses these)
    - Bank B alone: ~68% (can detect these patterns)
    - Consortium: ~87% (learns all patterns from combined data)
    """
    n = len(df)
    fraud_labels = np.zeros(n, dtype=int)

    # Pattern 1: Far from home (>30 miles)
    far_from_home = df['distance_from_home'] > 30
    fraud_labels[far_from_home & (np.random.random(n) < 0.30)] = 1

    # Pattern 2: Gas station transactions
    gas_station = df['merchant_category'] == 'gas'
    fraud_labels[gas_station & (np.random.random(n) < 0.70)] = 1

    # Pattern 3: Travel merchant
    travel = df['merchant_category'] == 'travel'
    fraud_labels[travel & (np.random.random(n) < 0.60)] = 1

    return fraud_labels


def generate_bank_a_data(n_samples: int = 5000) -> pd.DataFrame:
    """Generate Bank A's dataset with their specific fraud patterns."""
    print(f"Generating Bank A data ({n_samples} samples)...")

    df = generate_base_transaction(n_samples)
    df['is_fraud'] = inject_bank_a_fraud_patterns(df)

    # Add bank identifier
    df['bank_id'] = 'A'

    fraud_count = df['is_fraud'].sum()
    fraud_rate = fraud_count / n_samples * 100
    print(f"  - Fraud cases: {fraud_count} ({fraud_rate:.1f}%)")

    return df


def generate_bank_b_data(n_samples: int = 3000) -> pd.DataFrame:
    """Generate Bank B's dataset with their specific fraud patterns."""
    print(f"Generating Bank B data ({n_samples} samples)...")

    df = generate_base_transaction(n_samples)
    df['is_fraud'] = inject_bank_b_fraud_patterns(df)

    # Add bank identifier
    df['bank_id'] = 'B'

    fraud_count = df['is_fraud'].sum()
    fraud_rate = fraud_count / n_samples * 100
    print(f"  - Fraud cases: {fraud_count} ({fraud_rate:.1f}%)")

    return df


def encode_categorical(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode categorical features."""
    # One-hot encode merchant_category
    df_encoded = pd.get_dummies(df, columns=['merchant_category'], prefix='cat')
    return df_encoded


def save_datasets(
    bank_a_df: pd.DataFrame,
    bank_b_df: pd.DataFrame,
    output_dir: str,
) -> Tuple[str, str, str]:
    """Save datasets to CSV files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save raw data
    bank_a_path = output_path / 'bank_a_fraud_data.csv'
    bank_b_path = output_path / 'bank_b_fraud_data.csv'
    combined_path = output_path / 'combined_fraud_data.csv'

    # Encode categorical before saving
    bank_a_encoded = encode_categorical(bank_a_df.copy())
    bank_b_encoded = encode_categorical(bank_b_df.copy())

    bank_a_encoded.to_csv(bank_a_path, index=False)
    bank_b_encoded.to_csv(bank_b_path, index=False)

    # Combined dataset for consortium
    combined = pd.concat([bank_a_encoded, bank_b_encoded], ignore_index=True)
    combined.to_csv(combined_path, index=False)

    print(f"\nDatasets saved:")
    print(f"  - Bank A: {bank_a_path}")
    print(f"  - Bank B: {bank_b_path}")
    print(f"  - Combined: {combined_path}")

    return str(bank_a_path), str(bank_b_path), str(combined_path)


def generate_test_transaction() -> dict:
    """Generate a sample suspicious transaction for demo."""
    return {
        'description': 'Late-night international online purchase',
        'amount': 2500.00,
        'merchant_category': 'online',
        'hour_of_day': 2,  # 2 AM
        'is_international': 1,
        'distance_from_home': 0,  # At home but buying internationally
        'avg_monthly_spend': 1200.00,
        'num_txns_last_24h': 7,  # Unusual velocity
        'ratio_to_avg_amount': 2.08,  # Higher than average
    }


def print_dataset_summary(df: pd.DataFrame, name: str) -> None:
    """Print summary statistics for a dataset."""
    print(f"\n{'='*50}")
    print(f"{name} Dataset Summary")
    print('='*50)
    print(f"Total records: {len(df)}")
    print(f"Fraud cases: {df['is_fraud'].sum()} ({df['is_fraud'].mean()*100:.1f}%)")
    print(f"\nFeature statistics:")
    print(df.describe().round(2))


def main():
    parser = argparse.ArgumentParser(
        description='Generate synthetic fraud detection data for bank consortium demo'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='/tmp/privacy-platform/data/demo',
        help='Output directory for CSV files'
    )
    parser.add_argument(
        '--bank-a-size',
        type=int,
        default=5000,
        help='Number of records for Bank A'
    )
    parser.add_argument(
        '--bank-b-size',
        type=int,
        default=3000,
        help='Number of records for Bank B'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed statistics'
    )

    args = parser.parse_args()

    print("="*60)
    print("Fraud Detection Data Generator")
    print("Bank Consortium Demo - Xcapit Privacy Platform")
    print("="*60)

    # Generate datasets
    bank_a_df = generate_bank_a_data(args.bank_a_size)
    bank_b_df = generate_bank_b_data(args.bank_b_size)

    if args.verbose:
        print_dataset_summary(bank_a_df, 'Bank A')
        print_dataset_summary(bank_b_df, 'Bank B')

    # Save datasets
    paths = save_datasets(bank_a_df, bank_b_df, args.output_dir)

    # Print test transaction
    print("\n" + "="*60)
    print("Sample Suspicious Transaction (for demo inference):")
    print("="*60)
    test_txn = generate_test_transaction()
    for key, value in test_txn.items():
        print(f"  {key}: {value}")

    print("\n" + "="*60)
    print("Data generation complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Run fraud_detection_demo.py to see individual vs consortium accuracy")
    print("2. Navigate to /demo/bank-consortium in the dashboard")

    return paths


if __name__ == '__main__':
    main()
