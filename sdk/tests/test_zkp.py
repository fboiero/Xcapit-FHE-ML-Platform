"""Tests for the ZKP module.

Covers:
- PedersenCommitment: commit/verify, binding, hiding properties.
- SchnorrProof: prove/verify standalone Schnorr identification.
- ContributionProof: create/verify contribution proofs.
- ZKProver/ZKVerifier: high-level API for contribution and model accuracy proofs.
- ArithmeticCircuit: circuit construction, evaluation, R1CS.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from sdk.zkp import (
    ArithmeticCircuit,
    ContributionProof,
    Gate,
    PedersenCommitment,
    SchnorrProof,
    ZKProver,
    ZKVerifier,
)


# ============================================================================
# PedersenCommitment
# ============================================================================


class TestPedersenCommitment:
    """Tests for the Pedersen commitment scheme."""

    def test_commit_and_verify(self) -> None:
        pc = PedersenCommitment()
        c, r = pc.commit(42)
        assert pc.verify(c, 42, r)

    def test_wrong_value_rejected(self) -> None:
        pc = PedersenCommitment()
        c, r = pc.commit(42)
        assert not pc.verify(c, 43, r)

    def test_wrong_randomness_rejected(self) -> None:
        pc = PedersenCommitment()
        c, r = pc.commit(42)
        assert not pc.verify(c, 42, r + 1)

    def test_deterministic_with_fixed_randomness(self) -> None:
        pc = PedersenCommitment()
        c1, _ = pc.commit(100, randomness=999)
        c2, _ = pc.commit(100, randomness=999)
        assert c1 == c2

    def test_different_values_different_commitments(self) -> None:
        pc = PedersenCommitment()
        c1, _ = pc.commit(1, randomness=999)
        c2, _ = pc.commit(2, randomness=999)
        assert c1 != c2

    def test_commitment_hiding(self) -> None:
        """Same value with different randomness produces different commitments."""
        pc = PedersenCommitment()
        c1, _ = pc.commit(42, randomness=111)
        c2, _ = pc.commit(42, randomness=222)
        assert c1 != c2

    def test_custom_parameters(self) -> None:
        """Pedersen with small custom primes (not secure, just for testing)."""
        # p=23 is prime, g=4, h=9 -- both quadratic residues mod 23.
        pc = PedersenCommitment(p=23, g=4, h=9)
        c, r = pc.commit(5, randomness=3)
        assert pc.verify(c, 5, r)
        assert not pc.verify(c, 6, r)


# ============================================================================
# SchnorrProof
# ============================================================================


class TestSchnorrProof:
    """Tests for the standalone Schnorr identification protocol."""

    def test_prove_and_verify(self) -> None:
        sp = SchnorrProof()
        proof = sp.prove(secret=12345)
        assert sp.verify(proof)

    def test_tampered_response_fails(self) -> None:
        sp = SchnorrProof()
        proof = sp.prove(secret=42)
        # Tamper with the response.
        proof["response"] = "00"
        assert not sp.verify(proof)

    def test_tampered_challenge_fails(self) -> None:
        sp = SchnorrProof()
        proof = sp.prove(secret=42)
        proof["challenge"] = "ff"
        assert not sp.verify(proof)

    def test_missing_key_fails(self) -> None:
        sp = SchnorrProof()
        assert not sp.verify({"public_key": "aa"})

    def test_different_secrets_different_public_keys(self) -> None:
        sp = SchnorrProof()
        p1 = sp.prove(secret=111)
        p2 = sp.prove(secret=222)
        assert p1["public_key"] != p2["public_key"]

    def test_different_secrets_different_proofs(self) -> None:
        """Different secrets produce different proof responses."""
        sp = SchnorrProof()
        p1 = sp.prove(secret=111)
        p2 = sp.prove(secret=222)
        # Different secrets -> different public keys at minimum
        assert p1["public_key"] != p2["public_key"]
        # Both should verify independently
        assert sp.verify(p1)
        assert sp.verify(p2)


# ============================================================================
# ContributionProof
# ============================================================================


class TestContributionProof:
    """Tests for the ContributionProof create/verify API."""

    def _make_hash(self) -> str:
        return hashlib.sha256(b"test data").hexdigest()

    def test_create_and_verify(self) -> None:
        cp = ContributionProof()
        proof = cp.create_proof(
            data_hash=self._make_hash(),
            n_samples=100,
            n_features=5,
            contributor_id="member-1",
        )
        assert cp.verify_proof(proof)

    def test_tampered_commitment_fails(self) -> None:
        cp = ContributionProof()
        proof = cp.create_proof(
            data_hash=self._make_hash(),
            n_samples=50,
            n_features=3,
            contributor_id="member-1",
        )
        # Tamper with the data commitment.
        proof["commitments"]["C_data"] = "00" * 32
        assert not cp.verify_proof(proof)

    def test_tampered_hash_fails(self) -> None:
        """Modifying data_hash should break verification."""
        cp = ContributionProof()
        proof = cp.create_proof(
            data_hash=self._make_hash(),
            n_samples=50,
            n_features=3,
            contributor_id="member-1",
        )
        proof["public_inputs"]["data_hash"] = hashlib.sha256(b"different").hexdigest()
        assert not cp.verify_proof(proof)

    def test_tampered_samples_fails(self) -> None:
        """Modifying n_samples should break verification."""
        cp = ContributionProof()
        proof = cp.create_proof(
            data_hash=self._make_hash(),
            n_samples=50,
            n_features=3,
            contributor_id="member-1",
        )
        proof["public_inputs"]["n_samples"] = 51
        assert not cp.verify_proof(proof)

    def test_tampered_public_inputs_fails(self) -> None:
        cp = ContributionProof()
        proof = cp.create_proof(
            data_hash=self._make_hash(),
            n_samples=50,
            n_features=3,
            contributor_id="member-1",
        )
        # Tamper with sample count.
        proof["public_inputs"]["n_samples"] = 999
        assert not cp.verify_proof(proof)

    def test_invalid_data_hash_raises(self) -> None:
        cp = ContributionProof()
        with pytest.raises(ValueError, match="not valid hex"):
            cp.create_proof(
                data_hash="not-hex!",
                n_samples=10,
                n_features=2,
                contributor_id="x",
            )

    def test_zero_samples_raises(self) -> None:
        cp = ContributionProof()
        with pytest.raises(ValueError, match="n_samples must be positive"):
            cp.create_proof(
                data_hash=self._make_hash(),
                n_samples=0,
                n_features=2,
                contributor_id="x",
            )

    def test_zero_features_raises(self) -> None:
        cp = ContributionProof()
        with pytest.raises(ValueError, match="n_features must be positive"):
            cp.create_proof(
                data_hash=self._make_hash(),
                n_samples=10,
                n_features=0,
                contributor_id="x",
            )

    def test_proof_contains_expected_keys(self) -> None:
        cp = ContributionProof()
        proof = cp.create_proof(
            data_hash=self._make_hash(),
            n_samples=10,
            n_features=2,
            contributor_id="m1",
        )
        assert proof["proof_type"] == "contribution"
        assert "public_inputs" in proof
        assert "commitments" in proof
        assert "schnorr_proofs" in proof
        assert "blinding_factors" in proof
        assert "binding_challenge" in proof
        assert proof["contributor_id"] == "m1"


# ============================================================================
# ZKProver — contribution proofs
# ============================================================================


class TestZKProverContribution:
    """Tests for ZKProver.prove_contribution."""

    def test_prove_and_verify(self) -> None:
        prover = ZKProver("m1")
        verifier = ZKVerifier()
        data = b"hello world contribution data"
        proof = prover.prove_contribution(data)
        assert verifier.verify_contribution(proof)

    def test_prover_id_attached(self) -> None:
        prover = ZKProver("alice")
        proof = prover.prove_contribution(b"data")
        assert proof["prover_id"] == "alice"

    def test_custom_contributor_id(self) -> None:
        prover = ZKProver("alice")
        proof = prover.prove_contribution(b"data", contributor_id="bob")
        assert proof["contributor_id"] == "bob"
        assert proof["prover_id"] == "alice"

    def test_data_size_recorded(self) -> None:
        prover = ZKProver("m1")
        data = b"x" * 100
        proof = prover.prove_contribution(data)
        assert proof["data_size"] == 100

    def test_tampered_proof_fails(self) -> None:
        prover = ZKProver("m1")
        verifier = ZKVerifier()
        proof = prover.prove_contribution(b"secret data")
        # Tamper with the binding challenge.
        proof["binding_challenge"] = "00" * 32
        assert not verifier.verify_contribution(proof)

    def test_large_data_contribution(self) -> None:
        """10KB of data should produce a valid proof."""
        prover = ZKProver("m1")
        verifier = ZKVerifier()
        data = b"x" * 10240  # 10 KB
        proof = prover.prove_contribution(data)
        assert proof["data_size"] == 10240
        assert verifier.verify_contribution(proof)


# ============================================================================
# ZKProver — model accuracy proofs
# ============================================================================


class TestZKProverModelAccuracy:
    """Tests for ZKProver.prove_model_accuracy."""

    def test_prove_and_verify(self) -> None:
        prover = ZKProver("m1")
        verifier = ZKVerifier()
        metrics = {"accuracy": 0.95, "f1": 0.92}
        proof = prover.prove_model_accuracy(metrics)
        assert verifier.verify_model_accuracy(proof)

    def test_metric_out_of_range_raises(self) -> None:
        prover = ZKProver("m1")
        with pytest.raises(ValueError, match="outside"):
            prover.prove_model_accuracy({"accuracy": 1.5})

    def test_negative_metric_raises(self) -> None:
        prover = ZKProver("m1")
        with pytest.raises(ValueError, match="outside"):
            prover.prove_model_accuracy({"accuracy": -0.1})

    def test_tampered_metric_value_fails(self) -> None:
        prover = ZKProver("m1")
        verifier = ZKVerifier()
        proof = prover.prove_model_accuracy({"accuracy": 0.90})
        # Tamper with the claimed metric.
        proof["metrics"]["accuracy"] = 0.99
        assert not verifier.verify_model_accuracy(proof)

    def test_tampered_metrics_digest_fails(self) -> None:
        prover = ZKProver("m1")
        verifier = ZKVerifier()
        proof = prover.prove_model_accuracy({"accuracy": 0.90})
        proof["metrics_digest"] = "00" * 32
        assert not verifier.verify_model_accuracy(proof)

    def test_multiple_metrics(self) -> None:
        prover = ZKProver("m1")
        verifier = ZKVerifier()
        metrics = {
            "accuracy": 0.95,
            "precision": 0.93,
            "recall": 0.91,
            "f1": 0.92,
        }
        proof = prover.prove_model_accuracy(metrics)
        assert verifier.verify_model_accuracy(proof)

    def test_proof_type_is_model_accuracy(self) -> None:
        prover = ZKProver("m1")
        proof = prover.prove_model_accuracy({"accuracy": 0.5})
        assert proof["proof_type"] == "model_accuracy"


# ============================================================================
# ZKVerifier — edge cases
# ============================================================================


class TestZKVerifierEdgeCases:
    """Edge-case tests for the verifier."""

    def test_malformed_proof_returns_false(self) -> None:
        verifier = ZKVerifier()
        assert not verifier.verify_contribution({})
        assert not verifier.verify_model_accuracy({})

    def test_verify_contribution_with_bad_types(self) -> None:
        verifier = ZKVerifier()
        assert not verifier.verify_contribution({"public_inputs": None})

    def test_verify_model_accuracy_missing_metric_proof(self) -> None:
        verifier = ZKVerifier()
        proof = {
            "scale": 10 ** 8,
            "metrics": {"accuracy": 0.9},
            "metric_proofs": {},  # Missing proof for "accuracy"
            "metrics_digest": hashlib.sha256(
                json.dumps({"accuracy": 0.9}, sort_keys=True).encode()
            ).hexdigest(),
        }
        assert not verifier.verify_model_accuracy(proof)


# ============================================================================
# ArithmeticCircuit
# ============================================================================


class TestArithmeticCircuit:
    """Tests for arithmetic circuit construction, evaluation, and R1CS."""

    def test_add_gate(self) -> None:
        """ADD gate computes left + right."""
        circuit = ArithmeticCircuit()
        w_a = circuit.add_wire()
        w_b = circuit.add_wire()
        w_sum = circuit.add_gate(Gate.ADD, [w_a, w_b])
        result = circuit.evaluate({w_a: 3, w_b: 5})
        assert result[w_sum] == 8

    def test_mul_gate(self) -> None:
        """MUL gate computes left * right."""
        circuit = ArithmeticCircuit()
        w_a = circuit.add_wire()
        w_b = circuit.add_wire()
        w_prod = circuit.add_gate(Gate.MUL, [w_a, w_b])
        result = circuit.evaluate({w_a: 7, w_b: 6})
        assert result[w_prod] == 42

    def test_evaluate_circuit(self) -> None:
        """Multi-gate circuit: (a + b) * c."""
        circuit = ArithmeticCircuit()
        w_a = circuit.add_wire()
        w_b = circuit.add_wire()
        w_c = circuit.add_wire()
        w_sum = circuit.add_gate(Gate.ADD, [w_a, w_b])
        w_prod = circuit.add_gate(Gate.MUL, [w_sum, w_c])
        result = circuit.evaluate({w_a: 2, w_b: 3, w_c: 4})
        assert result[w_sum] == 5
        assert result[w_prod] == 20

    def test_const_gate(self) -> None:
        """CONST gate injects a fixed value."""
        circuit = ArithmeticCircuit()
        w_a = circuit.add_wire()
        w_const = circuit.add_gate(Gate.CONST, [], constant=10)
        w_sum = circuit.add_gate(Gate.ADD, [w_a, w_const])
        result = circuit.evaluate({w_a: 5})
        assert result[w_const] == 10
        assert result[w_sum] == 15

    def test_to_r1cs(self) -> None:
        """R1CS conversion produces valid matrices."""
        circuit = ArithmeticCircuit()
        w_a = circuit.add_wire()
        w_b = circuit.add_wire()
        w_prod = circuit.add_gate(Gate.MUL, [w_a, w_b])

        A, B, C = circuit.to_r1cs()
        assert len(A) == 1  # one gate -> one constraint
        assert len(B) == 1
        assert len(C) == 1

        # Verify witness: w = [1, a, b, prod]
        a_val, b_val = 3, 7
        result = circuit.evaluate({w_a: a_val, w_b: b_val})
        witness = [1, a_val, b_val, result[w_prod]]
        assert ArithmeticCircuit.verify_r1cs(A, B, C, witness)

    def test_r1cs_add_gate(self) -> None:
        """R1CS for ADD gate: (left + right) * 1 = output."""
        circuit = ArithmeticCircuit()
        w_a = circuit.add_wire()
        w_b = circuit.add_wire()
        w_sum = circuit.add_gate(Gate.ADD, [w_a, w_b])

        A, B, C = circuit.to_r1cs()
        result = circuit.evaluate({w_a: 4, w_b: 5})
        witness = [1, 4, 5, result[w_sum]]
        assert ArithmeticCircuit.verify_r1cs(A, B, C, witness)

    def test_range_check_circuit(self) -> None:
        """range_check(lo, hi) produces a valid circuit for in-range values."""
        circuit = ArithmeticCircuit.range_check(0, 10)
        result = circuit.evaluate({0: 5})
        # The circuit evaluates; the final product (diff_lo * diff_hi) should be >= 0
        # for in-range values.  We verify the circuit runs without error and
        # produces expected intermediate values.
        wire_values = list(result.values())
        # x=5: diff_lo = 5-0 = 5, diff_hi = 10-5 = 5, product = 25
        assert 5 in wire_values   # diff_lo or diff_hi
        assert 25 in wire_values  # product

    def test_sum_check_circuit(self) -> None:
        """sum_check(n) computes the sum of n inputs."""
        circuit = ArithmeticCircuit.sum_check(3)
        result = circuit.evaluate({0: 10, 1: 20, 2: 30})
        # The last wire contains the sum
        wire_values = list(result.values())
        assert 60 in wire_values

    def test_no_gates_r1cs_raises(self) -> None:
        """R1CS conversion on empty circuit raises RuntimeError."""
        circuit = ArithmeticCircuit()
        circuit.add_wire()
        with pytest.raises(RuntimeError, match="no gates"):
            circuit.to_r1cs()

    def test_invalid_input_raises(self) -> None:
        """Evaluating with nonexistent wire ID raises ValueError."""
        circuit = ArithmeticCircuit()
        circuit.add_wire()
        with pytest.raises(ValueError, match="does not exist"):
            circuit.evaluate({999: 5})

    def test_add_gate_wrong_input_count_raises(self) -> None:
        """ADD gate requires exactly 2 inputs."""
        circuit = ArithmeticCircuit()
        w_a = circuit.add_wire()
        with pytest.raises(ValueError, match="exactly 2"):
            circuit.add_gate(Gate.ADD, [w_a])

    def test_const_gate_no_constant_raises(self) -> None:
        """CONST gate requires a constant value."""
        circuit = ArithmeticCircuit()
        with pytest.raises(ValueError, match="constant value"):
            circuit.add_gate(Gate.CONST, [])
