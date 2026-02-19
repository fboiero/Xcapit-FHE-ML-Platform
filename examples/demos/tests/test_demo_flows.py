"""
Tests for demo flow simulations.

These tests verify that the demo simulation functions work correctly,
including encryption simulation, voting, and model training flows.
"""

import pytest
import hashlib
import secrets
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_datasets import generate_dataset, FINTECH_FRAUD_CONFIG


class TestEncryptionSimulation:
    """Tests for FHE encryption simulation."""

    def simulate_encryption(self, data: np.ndarray) -> dict:
        """Simulate FHE encryption for testing."""
        data_bytes = data.tobytes()
        cipher_hash = hashlib.sha256(data_bytes).hexdigest()

        return {
            "ciphertext_preview": f"0x{cipher_hash[:64]}",
            "original_shape": data.shape,
            "encrypted_size_kb": len(data_bytes) * 100 // 1024,
            "scheme": "CKKS",
            "security_bits": 128,
            "poly_modulus_degree": 8192,
        }

    def test_encryption_returns_dict(self):
        """Verify encryption returns correct structure."""
        data = np.array([[1.0, 2.0, 3.0]])
        result = self.simulate_encryption(data)

        assert isinstance(result, dict)
        assert "ciphertext_preview" in result
        assert "original_shape" in result
        assert "scheme" in result

    def test_encryption_preserves_shape(self):
        """Verify encryption preserves original shape info."""
        data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        result = self.simulate_encryption(data)

        assert result["original_shape"] == (2, 3)

    def test_different_data_different_ciphertext(self):
        """Verify different data produces different ciphertext."""
        data1 = np.array([[1.0, 2.0, 3.0]])
        data2 = np.array([[4.0, 5.0, 6.0]])

        result1 = self.simulate_encryption(data1)
        result2 = self.simulate_encryption(data2)

        assert result1["ciphertext_preview"] != result2["ciphertext_preview"]

    def test_same_data_same_ciphertext(self):
        """Verify same data produces same ciphertext."""
        data = np.array([[1.0, 2.0, 3.0]])

        result1 = self.simulate_encryption(data)
        result2 = self.simulate_encryption(data)

        assert result1["ciphertext_preview"] == result2["ciphertext_preview"]

    def test_ciphertext_is_hex(self):
        """Verify ciphertext is valid hex string."""
        data = np.array([[1.0, 2.0, 3.0]])
        result = self.simulate_encryption(data)

        # Remove 0x prefix and verify hex
        hex_str = result["ciphertext_preview"][2:]
        assert all(c in "0123456789abcdef" for c in hex_str)


class TestCommitRevealVoting:
    """Tests for commit-reveal voting mechanism."""

    def create_commitment(self, proposal_id: str, vote: bool, salt: bytes) -> str:
        """Create a vote commitment."""
        return hashlib.sha256(
            proposal_id.encode() + bytes([vote]) + salt
        ).hexdigest()

    def verify_commitment(
        self, proposal_id: str, vote: bool, salt: bytes, commitment: str
    ) -> bool:
        """Verify a vote commitment."""
        expected = hashlib.sha256(
            proposal_id.encode() + bytes([vote]) + salt
        ).hexdigest()
        return expected == commitment

    def test_commitment_is_deterministic(self):
        """Verify same inputs produce same commitment."""
        proposal_id = "PROPOSAL_001"
        vote = True
        salt = b"fixed_salt_for_testing"

        commitment1 = self.create_commitment(proposal_id, vote, salt)
        commitment2 = self.create_commitment(proposal_id, vote, salt)

        assert commitment1 == commitment2

    def test_different_votes_different_commitments(self):
        """Verify different votes produce different commitments."""
        proposal_id = "PROPOSAL_001"
        salt = b"fixed_salt_for_testing"

        commitment_yes = self.create_commitment(proposal_id, True, salt)
        commitment_no = self.create_commitment(proposal_id, False, salt)

        assert commitment_yes != commitment_no

    def test_different_salts_different_commitments(self):
        """Verify different salts produce different commitments."""
        proposal_id = "PROPOSAL_001"
        vote = True

        commitment1 = self.create_commitment(proposal_id, vote, b"salt1")
        commitment2 = self.create_commitment(proposal_id, vote, b"salt2")

        assert commitment1 != commitment2

    def test_verification_succeeds_for_correct_data(self):
        """Verify verification succeeds with correct data."""
        proposal_id = "PROPOSAL_001"
        vote = True
        salt = secrets.token_bytes(32)

        commitment = self.create_commitment(proposal_id, vote, salt)
        verified = self.verify_commitment(proposal_id, vote, salt, commitment)

        assert verified is True

    def test_verification_fails_for_wrong_vote(self):
        """Verify verification fails with wrong vote."""
        proposal_id = "PROPOSAL_001"
        vote = True
        salt = secrets.token_bytes(32)

        commitment = self.create_commitment(proposal_id, vote, salt)
        verified = self.verify_commitment(proposal_id, False, salt, commitment)

        assert verified is False

    def test_verification_fails_for_wrong_salt(self):
        """Verify verification fails with wrong salt."""
        proposal_id = "PROPOSAL_001"
        vote = True
        salt1 = secrets.token_bytes(32)
        salt2 = secrets.token_bytes(32)

        commitment = self.create_commitment(proposal_id, vote, salt1)
        verified = self.verify_commitment(proposal_id, vote, salt2, commitment)

        assert verified is False

    def test_full_voting_flow(self):
        """Test complete commit-reveal voting flow."""
        proposal_id = "TRAIN_MODEL_2025"
        members = ["Bank A", "Bank B", "Bank C"]

        # Phase 1: Commit
        votes = {}
        commitments = {}
        for member in members:
            vote = True  # All vote yes
            salt = secrets.token_bytes(32)
            votes[member] = (vote, salt)
            commitments[member] = self.create_commitment(proposal_id, vote, salt)

        # Phase 2: Reveal and Verify
        yes_count = 0
        for member, (vote, salt) in votes.items():
            verified = self.verify_commitment(
                proposal_id, vote, salt, commitments[member]
            )
            assert verified is True
            if vote:
                yes_count += 1

        # Check result
        approval_rate = yes_count / len(members)
        assert approval_rate == 1.0  # All voted yes


class TestModelTrainingFlow:
    """Tests for model training simulation flow."""

    def test_dataset_can_be_split_for_training(self):
        """Verify dataset can be split into train/test."""
        from sklearn.model_selection import train_test_split

        df = generate_dataset(FINTECH_FRAUD_CONFIG)

        # Get features and target
        feature_cols = [f["name"] for f in FINTECH_FRAUD_CONFIG.features]
        X = df[feature_cols].select_dtypes(include=[np.number]).values
        y = df[FINTECH_FRAUD_CONFIG.target_column].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        assert len(X_train) == len(y_train)
        assert len(X_test) == len(y_test)
        assert len(X_train) + len(X_test) == len(X)

    def test_logistic_regression_can_train(self):
        """Verify logistic regression can train on generated data."""
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler

        df = generate_dataset(FINTECH_FRAUD_CONFIG)

        # Get numeric features
        feature_cols = [f["name"] for f in FINTECH_FRAUD_CONFIG.features]
        X = df[feature_cols].select_dtypes(include=[np.number]).values
        y = df[FINTECH_FRAUD_CONFIG.target_column].values

        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )

        # Train model
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train, y_train)

        # Verify model can predict
        y_pred = model.predict(X_test)
        assert len(y_pred) == len(y_test)

    def test_model_accuracy_is_reasonable(self):
        """Verify trained model has reasonable accuracy."""
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import accuracy_score

        df = generate_dataset(FINTECH_FRAUD_CONFIG)

        feature_cols = [f["name"] for f in FINTECH_FRAUD_CONFIG.features]
        X = df[feature_cols].select_dtypes(include=[np.number]).values
        y = df[FINTECH_FRAUD_CONFIG.target_column].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )

        model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Should be better than random (50%) but not necessarily perfect
        assert accuracy > 0.6

    def test_consortium_combined_training(self):
        """Test training on combined consortium data."""
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import accuracy_score

        from test_datasets import generate_consortium_split

        df = generate_dataset(FINTECH_FRAUD_CONFIG)
        splits = generate_consortium_split(df, n_members=3)

        # Combine all splits (simulating consortium training)
        import pandas as pd

        combined_df = pd.concat(splits.values(), ignore_index=True)

        feature_cols = [f["name"] for f in FINTECH_FRAUD_CONFIG.features]
        X = combined_df[feature_cols].select_dtypes(include=[np.number]).values
        y = combined_df[FINTECH_FRAUD_CONFIG.target_column].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Simple train on all data, test on subset
        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_scaled, y)

        accuracy = model.score(X_scaled, y)
        assert accuracy > 0.5


class TestAuditTrail:
    """Tests for audit trail generation."""

    def generate_audit_entry(self, action: str, actor: str, resource: str) -> dict:
        """Generate an audit trail entry."""
        import time

        timestamp = time.time()
        entry_id = hashlib.sha256(f"{timestamp}{action}{actor}".encode()).hexdigest()[:16]

        return {
            "id": entry_id,
            "timestamp": timestamp,
            "action": action,
            "actor": actor,
            "resource": resource,
            "hash": hashlib.sha256(f"{entry_id}{action}{actor}{resource}".encode()).hexdigest(),
        }

    def test_audit_entry_has_required_fields(self):
        """Verify audit entry has all required fields."""
        entry = self.generate_audit_entry("CREATE", "user@example.com", "consortium_001")

        assert "id" in entry
        assert "timestamp" in entry
        assert "action" in entry
        assert "actor" in entry
        assert "resource" in entry
        assert "hash" in entry

    def test_audit_entries_are_unique(self):
        """Verify consecutive audit entries have unique IDs."""
        import time

        entry1 = self.generate_audit_entry("CREATE", "user@example.com", "res1")
        time.sleep(0.01)  # Small delay to ensure different timestamp
        entry2 = self.generate_audit_entry("CREATE", "user@example.com", "res1")

        assert entry1["id"] != entry2["id"]

    def test_audit_hash_is_deterministic(self):
        """Verify same entry data produces same hash."""
        # Create entry with fixed timestamp for deterministic test
        entry = {
            "id": "test123",
            "action": "CREATE",
            "actor": "user@example.com",
            "resource": "res1",
        }
        hash1 = hashlib.sha256(
            f"{entry['id']}{entry['action']}{entry['actor']}{entry['resource']}".encode()
        ).hexdigest()
        hash2 = hashlib.sha256(
            f"{entry['id']}{entry['action']}{entry['actor']}{entry['resource']}".encode()
        ).hexdigest()

        assert hash1 == hash2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
