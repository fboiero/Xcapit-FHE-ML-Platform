#!/usr/bin/env python3
"""End-to-end test script for Tier 1 functionality.

Tests the complete flow:
1. Register a company
2. Create a consortium
3. Invite another company
4. Accept invitation
5. Upload data
6. Start training
7. Download results
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000/api/v1/consortiums"


def test_tier1_flow():
    print("=" * 60)
    print("Xcapit Privacy Platform - Tier 1 E2E Test")
    print("=" * 60)

    # 1. Register company A
    print("\n[1/8] Registering Company A...")
    response = requests.post(f"{BASE_URL}/companies", json={
        "name": "FinTech Alpha",
        "email": "contact@fintech-alpha.com"
    })
    if response.status_code != 200:
        print(f"  ERROR: {response.json()}")
        return False
    company_a = response.json()
    api_key_a = company_a["api_key"]
    print(f"  OK: Company registered, ID: {company_a['company']['id'][:8]}...")

    # 2. Register company B
    print("\n[2/8] Registering Company B...")
    response = requests.post(f"{BASE_URL}/companies", json={
        "name": "Bank Beta",
        "email": "contact@bank-beta.com"
    })
    if response.status_code != 200:
        print(f"  ERROR: {response.json()}")
        return False
    company_b = response.json()
    api_key_b = company_b["api_key"]
    print(f"  OK: Company registered, ID: {company_b['company']['id'][:8]}...")

    headers_a = {"X-API-Key": api_key_a}
    headers_b = {"X-API-Key": api_key_b}

    # 3. Create consortium
    print("\n[3/8] Creating consortium...")
    response = requests.post(BASE_URL, headers=headers_a, json={
        "name": "Fraud Detection Consortium",
        "description": "Collaborative fraud detection using encrypted data from multiple financial institutions",
        "model_type": "logistic_regression"
    })
    if response.status_code != 200:
        print(f"  ERROR: {response.json()}")
        return False
    consortium = response.json()
    consortium_id = consortium["id"]
    print(f"  OK: Consortium created, ID: {consortium_id[:8]}...")

    # 4. Activate consortium
    print("\n[4/8] Activating consortium...")
    response = requests.post(f"{BASE_URL}/{consortium_id}/activate", headers=headers_a)
    if response.status_code != 200:
        print(f"  ERROR: {response.json()}")
        return False
    print(f"  OK: Consortium status: {response.json()['status']}")

    # 5. Invite company B
    print("\n[5/8] Inviting Company B...")
    response = requests.post(f"{BASE_URL}/{consortium_id}/invite", headers=headers_a, json={
        "email": "contact@bank-beta.com",
        "role": "contributor"
    })
    if response.status_code != 200:
        print(f"  ERROR: {response.json()}")
        return False
    invitation = response.json()
    invite_code = invitation["invite_code"]
    print(f"  OK: Invitation sent, code: {invite_code[:8]}...")

    # 6. Accept invitation
    print("\n[6/8] Company B accepting invitation...")
    response = requests.post(f"{BASE_URL}/join", headers=headers_b, json={
        "invite_code": invite_code
    })
    if response.status_code != 200:
        print(f"  ERROR: {response.json()}")
        return False
    print(f"  OK: Joined as {response.json()['role']}")

    # 7. Both companies upload data
    print("\n[7/8] Uploading encrypted data...")

    # Company A uploads
    response = requests.post(f"{BASE_URL}/{consortium_id}/data", headers=headers_a)
    if response.status_code != 200:
        print(f"  ERROR Company A: {response.json()}")
        return False
    print(f"  OK: Company A uploaded {response.json()['record_count']} records")

    # Company B uploads
    response = requests.post(f"{BASE_URL}/{consortium_id}/data", headers=headers_b)
    if response.status_code != 200:
        print(f"  ERROR Company B: {response.json()}")
        return False
    print(f"  OK: Company B uploaded {response.json()['record_count']} records")

    # Check stats
    response = requests.get(f"{BASE_URL}/{consortium_id}/stats", headers=headers_a)
    stats = response.json()
    print(f"  Stats: {stats['total_contributions']} contributions, {stats['total_records']} total records")

    # 8. Start training and wait
    print("\n[8/8] Starting training...")
    response = requests.post(f"{BASE_URL}/{consortium_id}/train", headers=headers_a)
    if response.status_code != 200:
        print(f"  ERROR: {response.json()}")
        return False
    print(f"  Training started...")

    # Poll for completion
    for i in range(15):
        time.sleep(2)
        response = requests.get(f"{BASE_URL}/{consortium_id}/training-status", headers=headers_a)
        status = response.json()
        print(f"  Progress: {status['progress']}% - {status['current_step']}")
        if status['status'] == 'completed':
            break

    # Download results
    print("\n[FINAL] Downloading results...")
    response = requests.get(f"{BASE_URL}/{consortium_id}/results", headers=headers_a)
    if response.status_code != 200:
        print(f"  ERROR: {response.json()}")
        return False

    results = response.json()
    print(f"  Model type: {results['model_type']}")
    print(f"  Accuracy: {results['metrics']['accuracy']}")
    print(f"  Privacy: {results['privacy_guarantees']['encryption_scheme']}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_tier1_flow()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to server.")
        print("Make sure the server is running: python -m sdk.api.server")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
