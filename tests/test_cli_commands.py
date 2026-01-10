"""Extended tests for CLI commands.

Tests cover:
- cmd_init (FHE context initialization)
- cmd_encrypt (data encryption)
- cmd_decrypt (data decryption)
- cmd_train (model training)
- cmd_predict (model prediction)
- cmd_benchmark (FHE benchmarks)
- blockchain commands (connect, register, checkpoint, verify)
- api_keys commands (create, list, revoke)
"""

import argparse
import json
import pickle
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

# ========== Init Command Tests ==========


class TestCmdInit:
    """Tests for cmd_init command."""

    def test_init_creates_context(self, tmp_path, capsys):
        """Test that init command creates FHE context."""
        from sdk.cli.commands.encryption import cmd_init

        args = argparse.Namespace(
            output=str(tmp_path / "workspace"),
            poly_degree=8192,  # Must be at least 8192 for valid params
            security="128",
        )

        result = cmd_init(args)

        assert result == 0
        assert (tmp_path / "workspace" / "keys" / "context.bin").exists()
        assert (tmp_path / "workspace" / "keys" / "context_public.bin").exists()
        assert (tmp_path / "workspace" / "config.json").exists()

        captured = capsys.readouterr()
        assert "FHE context initialized" in captured.out

    def test_init_creates_config_json(self, tmp_path):
        """Test that init creates valid config.json."""
        from sdk.cli.commands.encryption import cmd_init

        args = argparse.Namespace(
            output=str(tmp_path / "workspace"),
            poly_degree=8192,
            security="128",
        )

        cmd_init(args)

        config_path = tmp_path / "workspace" / "config.json"
        with open(config_path) as f:
            config = json.load(f)

        assert config["poly_modulus_degree"] == 8192
        assert config["security_level"] == "128"
        assert "version" in config

    def test_init_default_security_level(self, tmp_path):
        """Test that init uses TC128 as default security."""
        from sdk.cli.commands.encryption import cmd_init

        args = argparse.Namespace(
            output=str(tmp_path / "workspace"),
            poly_degree=8192,  # Must be at least 8192 for valid params
            security="invalid",  # Should default to TC128
        )

        result = cmd_init(args)

        assert result == 0


# ========== Encrypt Command Tests ==========


class TestCmdEncrypt:
    """Tests for cmd_encrypt command."""

    def test_encrypt_missing_input(self, tmp_path, capsys):
        """Test encrypt with missing input file."""
        from sdk.cli.commands.encryption import cmd_encrypt

        args = argparse.Namespace(
            input=str(tmp_path / "nonexistent.csv"),
            output=str(tmp_path / "encrypted.bin"),
            target=None,
            keys=str(tmp_path / "keys"),
            no_normalize=False,
        )

        result = cmd_encrypt(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    def test_encrypt_invalid_target_column(self, tmp_path, capsys):
        """Test encrypt with invalid target column."""
        from sdk.cli.commands.encryption import cmd_encrypt

        # Create test CSV
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df.to_csv(csv_path, index=False)

        args = argparse.Namespace(
            input=str(csv_path),
            output=str(tmp_path / "encrypted.bin"),
            target="nonexistent_column",
            keys=str(tmp_path / "keys"),
            no_normalize=False,
        )

        result = cmd_encrypt(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Target column" in captured.out

    def test_encrypt_with_valid_data(self, tmp_path, capsys):
        """Test encrypt with valid CSV data."""
        from sdk.cli.commands.encryption import cmd_encrypt

        # Create test CSV
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame({"feature1": [1.0, 2.0, 3.0], "feature2": [4.0, 5.0, 6.0]})
        df.to_csv(csv_path, index=False)

        args = argparse.Namespace(
            input=str(csv_path),
            output=str(tmp_path / "encrypted.bin"),
            target=None,
            keys=str(tmp_path / "keys"),
            no_normalize=False,
        )

        result = cmd_encrypt(args)

        assert result == 0
        assert (tmp_path / "encrypted.bin").exists()
        captured = capsys.readouterr()
        assert "Encrypted" in captured.out

    def test_encrypt_with_target(self, tmp_path, capsys):
        """Test encrypt with target column."""
        from sdk.cli.commands.encryption import cmd_encrypt

        # Create test CSV
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame(
            {
                "feature1": [1.0, 2.0, 3.0],
                "feature2": [4.0, 5.0, 6.0],
                "target": [0.5, 1.0, 1.5],
            }
        )
        df.to_csv(csv_path, index=False)

        args = argparse.Namespace(
            input=str(csv_path),
            output=str(tmp_path / "encrypted.bin"),
            target="target",
            keys=str(tmp_path / "keys"),
            no_normalize=False,
        )

        result = cmd_encrypt(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "target" in captured.out.lower()


# ========== Decrypt Command Tests ==========


class TestCmdDecrypt:
    """Tests for cmd_decrypt command."""

    def test_decrypt_missing_input(self, tmp_path, capsys):
        """Test decrypt with missing input file."""
        from sdk.cli.commands.encryption import cmd_decrypt

        args = argparse.Namespace(
            input=str(tmp_path / "nonexistent.bin"),
            output=str(tmp_path / "output.csv"),
            keys=str(tmp_path / "keys"),
            no_denormalize=False,
        )

        result = cmd_decrypt(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    def test_decrypt_missing_keys(self, tmp_path, capsys):
        """Test decrypt with missing keys."""
        from sdk.cli.commands.encryption import cmd_decrypt

        # Create a fake encrypted bundle
        bundle_path = tmp_path / "encrypted.bin"
        with open(bundle_path, "wb") as f:
            pickle.dump({"keys_path": str(tmp_path / "keys")}, f)

        args = argparse.Namespace(
            input=str(bundle_path),
            output=str(tmp_path / "output.csv"),
            keys=None,
            no_denormalize=False,
        )

        result = cmd_decrypt(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Secret key not found" in captured.out

    def test_encrypt_decrypt_roundtrip(self, tmp_path):
        """Test full encrypt-decrypt roundtrip."""
        from sdk.cli.commands.encryption import cmd_decrypt, cmd_encrypt

        # Create test CSV
        csv_path = tmp_path / "data.csv"
        df = pd.DataFrame(
            {
                "feature1": [1.0, 2.0, 3.0, 4.0, 5.0],
                "feature2": [10.0, 20.0, 30.0, 40.0, 50.0],
            }
        )
        df.to_csv(csv_path, index=False)

        # Encrypt
        encrypt_args = argparse.Namespace(
            input=str(csv_path),
            output=str(tmp_path / "encrypted.bin"),
            target=None,
            keys=str(tmp_path / "keys"),
            no_normalize=True,  # Skip normalization for easier comparison
        )
        result = cmd_encrypt(encrypt_args)
        assert result == 0

        # Decrypt
        decrypt_args = argparse.Namespace(
            input=str(tmp_path / "encrypted.bin"),
            output=str(tmp_path / "decrypted.csv"),
            keys=str(tmp_path / "keys"),
            no_denormalize=True,
        )
        result = cmd_decrypt(decrypt_args)
        assert result == 0

        # Compare
        decrypted_df = pd.read_csv(tmp_path / "decrypted.csv")
        # Check that values are approximately equal (FHE has some noise)
        np.testing.assert_array_almost_equal(df.values, decrypted_df.values, decimal=3)


# ========== Train Command Tests ==========


class TestCmdTrain:
    """Tests for cmd_train command."""

    def test_train_missing_data(self, tmp_path, capsys):
        """Test train with missing data file."""
        from sdk.cli.commands.training import cmd_train

        args = argparse.Namespace(
            model="linear-regression",
            data=str(tmp_path / "nonexistent.bin"),
            output=str(tmp_path / "model.bin"),
            keys=None,
            epochs=10,
            learning_rate=0.01,
            n_clusters=3,
            max_depth=4,
            task="classification",
            verbose=False,
        )

        result = cmd_train(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    def test_train_missing_keys(self, tmp_path, capsys):
        """Test train with missing keys."""
        from sdk.cli.commands.training import cmd_train

        # Create a fake data bundle
        bundle_path = tmp_path / "data.bin"
        with open(bundle_path, "wb") as f:
            pickle.dump({"keys_path": str(tmp_path / "nonexistent_keys")}, f)

        args = argparse.Namespace(
            model="linear-regression",
            data=str(bundle_path),
            output=str(tmp_path / "model.bin"),
            keys=None,
            epochs=10,
            learning_rate=0.01,
            n_clusters=3,
            max_depth=4,
            task="classification",
            verbose=False,
        )

        result = cmd_train(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Keys not found" in captured.out

    def test_train_linear_regression(self, tmp_path, capsys):
        """Test training linear regression model."""
        from sdk.cli.commands.encryption import cmd_encrypt
        from sdk.cli.commands.training import cmd_train

        # Create test data
        csv_path = tmp_path / "data.csv"
        np.random.seed(42)
        X = np.random.randn(20, 3)
        y = X @ np.array([1.0, 2.0, 3.0]) + 0.5
        df = pd.DataFrame(X, columns=["f1", "f2", "f3"])
        df["target"] = y
        df.to_csv(csv_path, index=False)

        # Encrypt
        encrypt_args = argparse.Namespace(
            input=str(csv_path),
            output=str(tmp_path / "encrypted.bin"),
            target="target",
            keys=str(tmp_path / "keys"),
            no_normalize=False,
        )
        cmd_encrypt(encrypt_args)

        # Train
        train_args = argparse.Namespace(
            model="linear-regression",
            data=str(tmp_path / "encrypted.bin"),
            output=str(tmp_path / "model.bin"),
            keys=str(tmp_path / "keys"),
            epochs=5,
            learning_rate=0.01,
            n_clusters=3,
            max_depth=4,
            task="regression",
            verbose=False,
        )
        result = cmd_train(train_args)

        assert result == 0
        assert (tmp_path / "model.bin").exists()

        captured = capsys.readouterr()
        assert "Training complete" in captured.out


# ========== Predict Command Tests ==========


class TestCmdPredict:
    """Tests for cmd_predict command."""

    def test_predict_missing_model(self, tmp_path, capsys):
        """Test predict with missing model file."""
        from sdk.cli.commands.prediction import cmd_predict

        args = argparse.Namespace(
            model=str(tmp_path / "nonexistent.bin"),
            input=str(tmp_path / "data.bin"),
            output=None,
            keys=None,
            format="csv",
            encrypted=False,
            verbose=False,
        )

        result = cmd_predict(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    def test_predict_missing_input(self, tmp_path, capsys):
        """Test predict with missing input file."""
        from sdk.cli.commands.prediction import cmd_predict

        # Create a fake model
        model_path = tmp_path / "model.bin"
        with open(model_path, "wb") as f:
            pickle.dump({"model_type": "linear-regression"}, f)

        args = argparse.Namespace(
            model=str(model_path),
            input=str(tmp_path / "nonexistent.bin"),
            output=None,
            keys=None,
            format="csv",
            encrypted=False,
            verbose=False,
        )

        result = cmd_predict(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()


# ========== Benchmark Command Tests ==========


class TestCmdBenchmark:
    """Tests for cmd_benchmark command."""

    def test_benchmark_runs(self, capsys):
        """Test that benchmark command runs successfully."""
        from sdk.cli.commands.benchmark import cmd_benchmark

        args = argparse.Namespace(
            poly_degree=8192,  # Must be at least 8192 for valid params
            vector_size=100,
            iterations=2,
        )

        result = cmd_benchmark(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "FHE Benchmarks" in captured.out
        assert "SUMMARY" in captured.out

    def test_benchmark_outputs_metrics(self, capsys):
        """Test that benchmark outputs all expected metrics."""
        from sdk.cli.commands.benchmark import cmd_benchmark

        args = argparse.Namespace(
            poly_degree=8192,  # Must be at least 8192 for valid params
            vector_size=50,
            iterations=1,
        )

        cmd_benchmark(args)

        captured = capsys.readouterr()
        assert "Context Creation" in captured.out
        assert "Vector Encryption" in captured.out
        assert "Vector Decryption" in captured.out
        assert "Encrypted Addition" in captured.out
        assert "Encrypted Multiplication" in captured.out
        assert "Precision Check" in captured.out


# ========== Blockchain Command Tests ==========


class TestBlockchainCommands:
    """Tests for blockchain commands."""

    def test_connect_invalid_network(self, capsys):
        """Test connect command with mocked connector."""
        from sdk.cli.commands.blockchain import cmd_blockchain_connect

        # Mock at sdk.blockchain where it's imported from
        with patch("sdk.blockchain.BlockchainConnector") as MockConnector:
            mock_instance = MagicMock()
            mock_instance.connect.side_effect = Exception("Connection failed")
            MockConnector.return_value = mock_instance

            args = argparse.Namespace(
                network="arbitrum-sepolia",
                rpc=None,
                private_key=None,
            )

            result = cmd_blockchain_connect(args)

            assert result == 1
            captured = capsys.readouterr()
            assert "Error" in captured.out

    def test_connect_success(self, capsys):
        """Test successful blockchain connection."""
        from sdk.cli.commands.blockchain import cmd_blockchain_connect

        with patch("sdk.blockchain.BlockchainConnector") as MockConnector:
            mock_instance = MagicMock()
            mock_instance.config.chain_id = 421614
            mock_instance._rpc_url = "https://example.com"
            MockConnector.return_value = mock_instance

            args = argparse.Namespace(
                network="arbitrum-sepolia",
                rpc=None,
                private_key=None,
            )

            result = cmd_blockchain_connect(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "Connected" in captured.out

    def test_register_missing_model(self, tmp_path, capsys):
        """Test register with missing model file."""
        from sdk.cli.commands.blockchain import cmd_blockchain_register

        args = argparse.Namespace(
            model=str(tmp_path / "nonexistent.bin"),
            network="arbitrum-sepolia",
            rpc=None,
            private_key="0x123",
            contract="0xabc",
            version=None,
        )

        result = cmd_blockchain_register(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    def test_checkpoint_missing_model(self, tmp_path, capsys):
        """Test checkpoint with missing model file."""
        from sdk.cli.commands.blockchain import cmd_blockchain_checkpoint

        args = argparse.Namespace(
            model=str(tmp_path / "nonexistent.bin"),
            network="arbitrum-sepolia",
            rpc=None,
            private_key="0x123",
            contract="0xabc",
            model_id=1,
            epoch=10,
        )

        result = cmd_blockchain_checkpoint(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower()

    def test_verify_model(self, capsys):
        """Test verify command with mocked registry."""
        from sdk.cli.commands.blockchain import cmd_blockchain_verify

        with patch("sdk.blockchain.BlockchainConnector") as MockConnector:
            with patch("sdk.blockchain.ModelRegistryClient") as MockRegistry:
                mock_connector = MagicMock()
                MockConnector.return_value = mock_connector

                mock_model_info = MagicMock()
                mock_model_info.owner = "0x123"
                mock_model_info.model_type = "linear-regression"
                mock_model_info.version = "1.0.0"
                mock_model_info.verified = True
                mock_model_info.active = True
                mock_model_info.created_at = "2024-01-01"
                mock_model_info.updated_at = "2024-01-02"

                mock_registry = MagicMock()
                mock_registry.get_model.return_value = mock_model_info
                mock_registry.get_checkpoint_count.return_value = 0
                MockRegistry.return_value = mock_registry

                args = argparse.Namespace(
                    model_id=1,
                    network="arbitrum-sepolia",
                    rpc=None,
                    contract="0xabc",
                    model=None,
                    epoch=None,
                )

                result = cmd_blockchain_verify(args)

                assert result == 0
                captured = capsys.readouterr()
                assert "linear-regression" in captured.out


# ========== API Keys Command Tests ==========


class TestApiKeysCommands:
    """Tests for API keys commands."""

    def test_create_api_key(self, capsys):
        """Test creating an API key."""
        from sdk.cli.commands.api_keys import cmd_api_key_create

        # Patch at sdk.api.auth where create_api_key is defined
        with patch("sdk.api.auth.create_api_key") as mock_create:
            mock_create.return_value = ("xcapit_abc123", "hash123")

            args = argparse.Namespace(
                name="test-key",
                permissions="read,write",
                rate_limit=100,
            )

            result = cmd_api_key_create(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "API KEY CREATED" in captured.out
            assert "xcapit_abc123" in captured.out

    def test_list_api_keys_empty(self, capsys):
        """Test listing API keys when none exist."""
        from sdk.cli.commands.api_keys import cmd_api_key_list

        with patch("sdk.api.auth.list_api_keys") as mock_list:
            mock_list.return_value = []

            args = argparse.Namespace()

            result = cmd_api_key_list(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "No API keys found" in captured.out

    def test_list_api_keys_with_keys(self, capsys):
        """Test listing API keys when keys exist."""
        from sdk.cli.commands.api_keys import cmd_api_key_list

        with patch("sdk.api.auth.list_api_keys") as mock_list:
            mock_list.return_value = [
                {
                    "name": "test-key",
                    "key_hash": "hash123...",
                    "permissions": "read,write",
                    "is_active": True,
                    "rate_limit": 100,
                }
            ]

            args = argparse.Namespace()

            result = cmd_api_key_list(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "test-key" in captured.out
            assert "1 API key(s)" in captured.out

    def test_revoke_api_key_success(self, capsys):
        """Test revoking an API key successfully."""
        from sdk.cli.commands.api_keys import cmd_api_key_revoke

        with patch("sdk.api.auth.revoke_api_key") as mock_revoke:
            mock_revoke.return_value = True

            args = argparse.Namespace(key_hash="hash123")

            result = cmd_api_key_revoke(args)

            assert result == 0
            captured = capsys.readouterr()
            assert "revoked successfully" in captured.out

    def test_revoke_api_key_not_found(self, capsys):
        """Test revoking a non-existent API key."""
        from sdk.cli.commands.api_keys import cmd_api_key_revoke

        with patch("sdk.api.auth.revoke_api_key") as mock_revoke:
            mock_revoke.return_value = False

            args = argparse.Namespace(key_hash="nonexistent")

            result = cmd_api_key_revoke(args)

            assert result == 1
            captured = capsys.readouterr()
            assert "not found" in captured.out


# ========== Integration Tests ==========


class TestCliFullWorkflow:
    """Full workflow integration tests."""

    def test_init_encrypt_train_predict_workflow(self, tmp_path, capsys):
        """Test complete CLI workflow: init -> encrypt -> train -> predict."""
        from sdk.cli.commands.encryption import cmd_encrypt, cmd_init
        from sdk.cli.commands.prediction import cmd_predict
        from sdk.cli.commands.training import cmd_train

        # 1. Initialize FHE context
        init_args = argparse.Namespace(
            output=str(tmp_path / "workspace"),
            poly_degree=8192,
            security="128",
        )
        assert cmd_init(init_args) == 0

        # 2. Create and encrypt training data
        np.random.seed(42)
        X = np.random.randn(30, 2)
        y = X[:, 0] * 2 + X[:, 1] * 3 + 1
        df = pd.DataFrame({"x1": X[:, 0], "x2": X[:, 1], "y": y})
        df.to_csv(tmp_path / "train.csv", index=False)

        encrypt_args = argparse.Namespace(
            input=str(tmp_path / "train.csv"),
            output=str(tmp_path / "train_encrypted.bin"),
            target="y",
            keys=str(tmp_path / "workspace" / "keys"),
            no_normalize=False,
        )
        assert cmd_encrypt(encrypt_args) == 0

        # 3. Train model
        train_args = argparse.Namespace(
            model="linear-regression",
            data=str(tmp_path / "train_encrypted.bin"),
            output=str(tmp_path / "model.bin"),
            keys=str(tmp_path / "workspace" / "keys"),
            epochs=10,
            learning_rate=0.01,
            n_clusters=3,
            max_depth=4,
            task="regression",
            verbose=False,
        )
        assert cmd_train(train_args) == 0

        # 4. Create and encrypt test data
        X_test = np.array([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
        df_test = pd.DataFrame({"x1": X_test[:, 0], "x2": X_test[:, 1]})
        df_test.to_csv(tmp_path / "test.csv", index=False)

        encrypt_test_args = argparse.Namespace(
            input=str(tmp_path / "test.csv"),
            output=str(tmp_path / "test_encrypted.bin"),
            target=None,
            keys=str(tmp_path / "workspace" / "keys"),
            no_normalize=False,
        )
        assert cmd_encrypt(encrypt_test_args) == 0

        # 5. Make predictions
        predict_args = argparse.Namespace(
            model=str(tmp_path / "model.bin"),
            input=str(tmp_path / "test_encrypted.bin"),
            output=str(tmp_path / "predictions.csv"),
            keys=str(tmp_path / "workspace" / "keys"),
            format="csv",
            encrypted=False,
            verbose=False,
        )
        assert cmd_predict(predict_args) == 0

        # Verify predictions were saved
        assert (tmp_path / "predictions.csv").exists()
        predictions_df = pd.read_csv(tmp_path / "predictions.csv")
        assert len(predictions_df) == 3
