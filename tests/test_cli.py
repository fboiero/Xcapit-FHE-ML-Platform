"""Tests for the CLI module.

Tests cover:
- get_version function
- cmd_version command
- cmd_info command
- Argument parsing
- Error handling
"""

import argparse
import pickle

import pytest

from sdk.cli import (
    cmd_info,
    cmd_version,
    create_parser,
    get_version,
)

# ========== get_version Tests ==========


class TestGetVersion:
    """Tests for get_version function."""

    def test_returns_string(self):
        """Test that get_version returns a string."""
        version = get_version()
        assert isinstance(version, str)

    def test_version_format(self):
        """Test that version has valid format."""
        version = get_version()
        # Should be like "0.1.0" or similar
        parts = version.split(".")
        assert len(parts) >= 2


# ========== cmd_version Tests ==========


class TestCmdVersion:
    """Tests for cmd_version command."""

    def test_version_prints_info(self, capsys):
        """Test that version command prints version info."""
        args = argparse.Namespace()
        result = cmd_version(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Xcapit FHE-ML SDK" in captured.out
        assert "Python:" in captured.out

    def test_version_shows_tenseal_status(self, capsys):
        """Test that version shows TenSEAL status."""
        args = argparse.Namespace()
        cmd_version(args)

        captured = capsys.readouterr()
        assert "TenSEAL:" in captured.out


# ========== cmd_info Tests ==========


class TestCmdInfo:
    """Tests for cmd_info command."""

    def test_info_model_file(self, tmp_path, capsys):
        """Test info command with model file."""
        # Create a mock model file
        model_path = tmp_path / "model.pkl"
        model_data = {
            "version": "1.0",
            "model_type": "LinearRegression",
            "params": {
                "weights": [1.0, 2.0, 3.0],
                "bias": 0.5,
                "n_features": 3,
                "state": "fitted",
            },
            "saved_at": "2024-01-01T00:00:00",
            "weights_hash": "abc123",
        }
        with open(model_path, "wb") as f:
            pickle.dump(model_data, f)

        args = argparse.Namespace(path=str(model_path), verbose=False)
        result = cmd_info(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "LinearRegression" in captured.out
        assert "3 features" in captured.out or "weights" in captured.out.lower()

    def test_info_encrypted_file(self, tmp_path, capsys):
        """Test info command with encrypted data file."""
        # Create a mock encrypted file
        encrypted_path = tmp_path / "encrypted.bin"
        encrypted_data = {
            "type": "encrypted_dataset",
            "encryption_scheme": "CKKS",
            "n_samples": 100,
            "n_features": 5,
            "keys_path": str(tmp_path / "keys"),
        }
        with open(encrypted_path, "wb") as f:
            pickle.dump(encrypted_data, f)

        args = argparse.Namespace(path=str(encrypted_path), verbose=False)
        result = cmd_info(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "100" in captured.out or "samples" in captured.out.lower()

    def test_info_nonexistent_file(self, tmp_path, capsys):
        """Test info command with nonexistent file."""
        args = argparse.Namespace(path=str(tmp_path / "nonexistent.pkl"), verbose=False)
        result = cmd_info(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out or "not found" in captured.out.lower()

    def test_info_verbose(self, tmp_path, capsys):
        """Test info command with verbose flag."""
        model_path = tmp_path / "model.pkl"
        model_data = {
            "version": "1.0",
            "model_type": "LogisticRegression",
            "params": {
                "weights": [0.5] * 10,
                "bias": 0.1,
                "n_features": 10,
            },
            "config": {
                "learning_rate": 0.01,
                "n_epochs": 100,
            },
        }
        with open(model_path, "wb") as f:
            pickle.dump(model_data, f)

        args = argparse.Namespace(path=str(model_path), verbose=True)
        result = cmd_info(args)

        assert result == 0


# ========== create_parser Tests ==========


class TestCreateParser:
    """Tests for argument parser creation."""

    def test_parser_creation(self):
        """Test that parser is created successfully."""
        parser = create_parser()
        assert parser is not None
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_has_subcommands(self):
        """Test that parser has expected subcommands."""
        parser = create_parser()

        # Test parsing various commands
        args = parser.parse_args(["version"])
        assert hasattr(args, "func")

    def test_parser_init_command(self):
        """Test parsing init command."""
        parser = create_parser()
        args = parser.parse_args(["init", "-o", "./workspace"])

        assert args.output == "./workspace"

    def test_parser_encrypt_command(self):
        """Test parsing encrypt command."""
        parser = create_parser()
        args = parser.parse_args(
            ["encrypt", "-i", "data.csv", "-o", "encrypted.bin", "-t", "target_col"]
        )

        assert args.input == "data.csv"
        assert args.output == "encrypted.bin"
        assert args.target == "target_col"

    def test_parser_train_command(self):
        """Test parsing train command."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "train",
                "-m",
                "linear-regression",
                "-d",
                "data.bin",
                "-o",
                "model.bin",
                "--epochs",
                "50",
                "--learning-rate",
                "0.1",
            ]
        )

        assert args.model == "linear-regression"
        assert args.data == "data.bin"
        assert args.output == "model.bin"
        assert args.epochs == 50
        assert args.learning_rate == 0.1

    def test_parser_predict_command(self):
        """Test parsing predict command."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "predict",
                "-m",
                "model.bin",
                "-i",
                "input.bin",
                "-o",
                "predictions.csv",
                "--format",
                "json",
            ]
        )

        assert args.model == "model.bin"
        assert args.input == "input.bin"
        assert args.output == "predictions.csv"
        assert args.format == "json"

    def test_parser_decrypt_command(self):
        """Test parsing decrypt command."""
        parser = create_parser()
        args = parser.parse_args(["decrypt", "-i", "encrypted.bin", "-o", "output.csv"])

        assert args.input == "encrypted.bin"
        assert args.output == "output.csv"

    def test_parser_info_command(self):
        """Test parsing info command."""
        parser = create_parser()
        args = parser.parse_args(["info", "model.pkl", "--verbose"])

        assert args.path == "model.pkl"
        assert args.verbose is True

    def test_parser_benchmark_command(self):
        """Test parsing benchmark command."""
        parser = create_parser()
        args = parser.parse_args(
            ["benchmark", "--poly-degree", "16384", "--vector-size", "500", "--iterations", "5"]
        )

        assert args.poly_degree == 16384
        assert args.vector_size == 500
        assert args.iterations == 5

    def test_parser_model_choices(self):
        """Test that model choices are validated."""
        parser = create_parser()

        # Valid model choice
        args = parser.parse_args(["train", "-m", "kmeans", "-d", "d", "-o", "o"])
        assert args.model == "kmeans"

        # Invalid model choice should raise
        with pytest.raises(SystemExit):
            parser.parse_args(["train", "-m", "invalid-model", "-d", "d", "-o", "o"])

    def test_parser_poly_degree_choices(self):
        """Test that poly-degree choices are validated."""
        parser = create_parser()

        # Valid choice
        args = parser.parse_args(["benchmark", "--poly-degree", "8192"])
        assert args.poly_degree == 8192

        # Invalid choice should raise
        with pytest.raises(SystemExit):
            parser.parse_args(["benchmark", "--poly-degree", "1024"])


# ========== Command Error Handling Tests ==========


class TestCommandErrorHandling:
    """Tests for error handling in commands."""

    def test_encrypt_missing_input(self, capsys):
        """Test encrypt command with missing input file."""
        from sdk.cli import cmd_encrypt

        args = argparse.Namespace(
            input="nonexistent.csv",
            output="output.bin",
            target=None,
            keys="./keys",
            no_normalize=False,
        )

        result = cmd_encrypt(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out or "not found" in captured.out.lower()

    def test_train_missing_data(self, capsys):
        """Test train command with missing data file."""
        from sdk.cli import cmd_train

        args = argparse.Namespace(
            model="linear-regression",
            data="nonexistent.bin",
            output="model.bin",
            keys="./keys",
            epochs=100,
            learning_rate=0.01,
            n_clusters=3,
            max_depth=4,
            task="classification",
            verbose=False,
        )

        result = cmd_train(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out or "not found" in captured.out.lower()

    def test_predict_missing_model(self, capsys):
        """Test predict command with missing model file."""
        from sdk.cli import cmd_predict

        args = argparse.Namespace(
            model="nonexistent_model.bin",
            input="data.bin",
            output=None,
            keys="./keys",
            format="csv",
            encrypted=False,
            verbose=False,
        )

        result = cmd_predict(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out or "not found" in captured.out.lower()

    def test_decrypt_missing_input(self, capsys):
        """Test decrypt command with missing input file."""
        from sdk.cli import cmd_decrypt

        args = argparse.Namespace(
            input="nonexistent.bin",
            output="output.csv",
            keys="./keys",
            no_denormalize=False,
        )

        result = cmd_decrypt(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out or "not found" in captured.out.lower()


# ========== Integration Tests ==========


class TestCliIntegration:
    """Integration tests for CLI module."""

    def test_full_parser_workflow(self):
        """Test creating parser and parsing various commands."""
        parser = create_parser()

        # Test multiple commands in sequence
        commands = [
            ["version"],
            ["info", "file.pkl"],
            ["init", "-o", "./test"],
        ]

        for cmd in commands:
            args = parser.parse_args(cmd)
            assert hasattr(args, "func")

    def test_help_text(self, capsys):
        """Test that help text is generated."""
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "encrypt" in captured.out
        assert "train" in captured.out
        assert "predict" in captured.out

    def test_subcommand_help(self, capsys):
        """Test subcommand help text."""
        parser = create_parser()

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["train", "--help"])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "linear-regression" in captured.out
        assert "epochs" in captured.out


# ========== Security Tests ==========


class TestCliSecurity:
    """Security-related tests for CLI."""

    def test_keys_directory_default(self):
        """Test that keys directory has sensible default."""
        parser = create_parser()
        args = parser.parse_args(["encrypt", "-i", "data.csv", "-o", "out.bin"])

        # Should have a default or be None
        assert hasattr(args, "keys")

    def test_private_key_not_logged(self, capsys):
        """Test that private keys are not printed in output."""
        from sdk.cli import cmd_version

        args = argparse.Namespace()
        cmd_version(args)

        captured = capsys.readouterr()
        # Ensure no sensitive patterns are leaked
        assert "private_key" not in captured.out.lower()
        assert "secret" not in captured.out.lower() or "secret key" not in captured.out.lower()
