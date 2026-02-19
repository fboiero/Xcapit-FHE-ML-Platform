#!/usr/bin/env python3
"""Add more contributions to the existing consortium on blockchain."""

import hashlib
import os
import sys
import time
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdk.blockchain.governance.client import GovernanceClient
from sdk.blockchain.connector import Network

# Configuration
CONTRACT_ADDRESS = "0xda52326d106A91A1F22A0c41Be2dc1F531C01F11"
CONSORTIUM_ID = bytes.fromhex("425d459cda53ff53ec63044c0dd54aef1a7fc30ec37233ff758a28c99c02fe85")
PRIVATE_KEY = "0xce9976e012e981abf5fcde14617e841c7c6a017f00595c6ac6083c84eeddeb67"

# New contributions (2 per bank)
NEW_CONTRIBUTIONS = [
    # Bank A - Round 2
    {"bank": "Bank A", "round": 2, "records": 15000, "features": 13, "fraud_rate": 24.2},
    # Bank A - Round 3
    {"bank": "Bank A", "round": 3, "records": 8500, "features": 13, "fraud_rate": 26.1},
    # Bank B - Round 2
    {"bank": "Bank B", "round": 2, "records": 12000, "features": 13, "fraud_rate": 23.8},
    # Bank B - Round 3
    {"bank": "Bank B", "round": 3, "records": 9500, "features": 13, "fraud_rate": 25.5},
    # Bank C - Round 2
    {"bank": "Bank C", "round": 2, "records": 18000, "features": 13, "fraud_rate": 24.9},
    # Bank C - Round 3
    {"bank": "Bank C", "round": 3, "records": 11000, "features": 13, "fraud_rate": 25.8},
]


def generate_fake_encrypted_data(bank: str, round_num: int, records: int) -> bytes:
    """Generate fake encrypted data blob for hashing purposes."""
    seed = f"{bank}-round{round_num}-{records}-{time.time()}"
    return hashlib.sha256(seed.encode()).digest() * 4  # 128 bytes


def main():
    print("=" * 70)
    print("       ADDING MORE CONTRIBUTIONS TO CONSORTIUM")
    print("=" * 70)
    print()

    # Connect to blockchain
    print("Connecting to Arbitrum Sepolia...")
    client = GovernanceClient(
        contract_address=CONTRACT_ADDRESS,
        network=Network.ARBITRUM_SEPOLIA,
    )
    address = client.connect(PRIVATE_KEY)
    print(f"  Connected as: {address}")
    print(f"  Contract: {CONTRACT_ADDRESS}")
    print(f"  Consortium ID: {CONSORTIUM_ID.hex()}")
    print()

    # Check wallet balance
    balance = client.connector.get_balance_eth()
    print(f"  Wallet balance: {balance:.4f} ETH")
    if balance < 0.01:
        print("  WARNING: Low balance, transactions may fail!")
    print()

    # Get current consortium stats
    try:
        consortium = client.get_consortium(CONSORTIUM_ID)
        print(f"  Current contributions: {consortium.total_contributions}")
        print(f"  Members: {consortium.member_count}")
    except Exception as e:
        print(f"  Note: Could not fetch consortium info: {e}")
    print()

    # Record new contributions
    print("-" * 70)
    print("Recording new contributions...")
    print("-" * 70)

    results = []
    total_new_records = 0

    for i, contrib in enumerate(NEW_CONTRIBUTIONS, 1):
        print(f"\n[{i}/6] {contrib['bank']} - Round {contrib['round']}")
        print(f"       Records: {contrib['records']:,}")
        print(f"       Features: {contrib['features']}")
        print(f"       Fraud Rate: {contrib['fraud_rate']}%")

        # Generate encrypted data simulation
        encrypted_data = generate_fake_encrypted_data(
            contrib['bank'],
            contrib['round'],
            contrib['records']
        )

        try:
            print("       Sending transaction...")
            contribution_id = client.record_contribution(
                consortium_id=CONSORTIUM_ID,
                record_count=contrib['records'],
                feature_count=contrib['features'],
                encrypted_data=encrypted_data,
            )

            if isinstance(contribution_id, bytes):
                contrib_hex = contribution_id.hex()
            else:
                contrib_hex = str(contribution_id)

            print(f"       SUCCESS! Contribution ID: {contrib_hex[:16]}...")
            results.append({
                "bank": contrib['bank'],
                "round": contrib['round'],
                "records": contrib['records'],
                "contribution_id": contrib_hex,
                "status": "confirmed"
            })
            total_new_records += contrib['records']

            # Small delay to avoid nonce issues
            time.sleep(2)

        except Exception as e:
            print(f"       ERROR: {e}")
            results.append({
                "bank": contrib['bank'],
                "round": contrib['round'],
                "records": contrib['records'],
                "contribution_id": None,
                "status": f"failed: {e}"
            })

    # Summary
    print()
    print("=" * 70)
    print("                         SUMMARY")
    print("=" * 70)

    successful = [r for r in results if r['status'] == 'confirmed']
    failed = [r for r in results if r['status'] != 'confirmed']

    print(f"\nSuccessful contributions: {len(successful)}/6")
    print(f"New records added: {total_new_records:,}")

    # Original + new totals
    original_records = 30000  # 10K + 8K + 12K
    total_records = original_records + total_new_records
    print(f"\nTotal consortium records: {total_records:,}")
    print(f"  - Original (Round 1): {original_records:,}")
    print(f"  - New (Rounds 2-3): {total_new_records:,}")

    # Per-bank totals
    print("\nPer-bank totals:")
    bank_totals = {
        "Bank A": 10000,  # original
        "Bank B": 8000,   # original
        "Bank C": 12000,  # original
    }
    for r in successful:
        bank_totals[r['bank']] = bank_totals.get(r['bank'], 0) + r['records']

    for bank, total in bank_totals.items():
        print(f"  {bank}: {total:,} records")

    if failed:
        print("\nFailed contributions:")
        for r in failed:
            print(f"  - {r['bank']} Round {r['round']}: {r['status']}")

    # Remaining balance
    final_balance = client.connector.get_balance_eth()
    print(f"\nFinal wallet balance: {final_balance:.4f} ETH")
    print(f"Gas spent: {balance - final_balance:.4f} ETH")

    print()
    print("=" * 70)
    print("Explorer: https://sepolia.arbiscan.io/address/" + CONTRACT_ADDRESS)
    print("=" * 70)

    return len(successful)


if __name__ == "__main__":
    success_count = main()
    sys.exit(0 if success_count == 6 else 1)
