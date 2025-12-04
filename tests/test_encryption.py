"""Tests for encryption module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from sdk.encryption import (
    CKKSEncryptor,
    CKKSParameters,
    EncryptedMatrix,
    EncryptedVector,
    FHEContextManager,
    SecurityLevel,
)
from sdk.utils import (
    EncryptedDataset,
    SecureDataLoader,
    ValidationError,
    check_fhe_compatibility,
    validate_numeric_data,
)


class TestCKKSParameters:
    """Tests for CKKSParameters dataclass."""

    def test_default_parameters(self):
        """Test default parameter values."""
        params = CKKSParameters()
        assert params.poly_modulus_degree == 8192
        assert params.coeff_mod_bit_sizes == (60, 40, 40, 60)
        assert params.scale == 2**40
        assert params.security_level == SecurityLevel.TC128

    def test_custom_parameters(self):
        """Test custom parameter values."""
        params = CKKSParameters(
            poly_modulus_degree=4096,
            coeff_mod_bit_sizes=(40, 20, 40),
            scale=2**20,
        )
        assert params.poly_modulus_degree == 4096
        assert params.coeff_mod_bit_sizes == (40, 20, 40)

    def test_invalid_poly_degree_raises(self):
        """Test that invalid poly_modulus_degree raises ValueError."""
        with pytest.raises(ValueError, match="poly_modulus_degree"):
            CKKSParameters(poly_modulus_degree=1000)

    def test_empty_coeff_mod_raises(self):
        """Test that empty coeff_mod_bit_sizes raises ValueError."""
        with pytest.raises(ValueError, match="coeff_mod_bit_sizes"):
            CKKSParameters(coeff_mod_bit_sizes=())

    def test_negative_scale_raises(self):
        """Test that negative scale raises ValueError."""
        with pytest.raises(ValueError, match="scale"):
            CKKSParameters(scale=-1)


class TestFHEContextManager:
    """Tests for FHEContextManager."""

    def test_create_context(self):
        """Test context creation."""
        manager = FHEContextManager()
        context = manager.create_context()
        assert context is not None
        assert manager.is_initialized

    def test_context_not_initialized_before_create(self):
        """Test that context is None before creation."""
        manager = FHEContextManager()
        assert not manager.is_initialized
        assert manager.context is None

    def test_max_slots(self):
        """Test max slots calculation."""
        manager = FHEContextManager()
        manager.create_context()
        # For poly_modulus_degree=8192, max_slots = 4096
        assert manager.get_max_slots() == 4096

    def test_serialize_without_init_raises(self):
        """Test that serializing without init raises RuntimeError."""
        manager = FHEContextManager()
        with pytest.raises(RuntimeError, match="not initialized"):
            manager.serialize()

    def test_serialize_deserialize(self):
        """Test context serialization and deserialization."""
        manager = FHEContextManager()
        manager.create_context()
        serialized = manager.serialize()

        # Load into new manager
        manager2 = FHEContextManager()
        manager2.load(serialized)
        assert manager2.is_initialized

    def test_repr(self):
        """Test string representation."""
        manager = FHEContextManager()
        repr_str = repr(manager)
        assert "not initialized" in repr_str

        manager.create_context()
        repr_str = repr(manager)
        assert "initialized" in repr_str


class TestCKKSEncryptor:
    """Tests for CKKSEncryptor."""

    @pytest.fixture
    def encryptor(self):
        """Create encryptor fixture."""
        return CKKSEncryptor()

    def test_encrypt_decrypt_vector(self, encryptor):
        """Test vector encryption and decryption."""
        original = [1.0, 2.0, 3.0, 4.0, 5.0]
        encrypted = encryptor.encrypt_vector(original)

        assert isinstance(encrypted, EncryptedVector)
        assert encrypted.shape == (5,)

        decrypted = encryptor.decrypt_vector(encrypted)
        np.testing.assert_array_almost_equal(decrypted, original, decimal=3)

    def test_encrypt_decrypt_numpy_array(self, encryptor):
        """Test numpy array encryption."""
        original = np.array([1.5, 2.5, 3.5])
        encrypted = encryptor.encrypt_vector(original)
        decrypted = encryptor.decrypt_vector(encrypted)
        np.testing.assert_array_almost_equal(decrypted, original, decimal=3)

    def test_encrypt_decrypt_matrix(self, encryptor):
        """Test matrix encryption and decryption."""
        original = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        encrypted = encryptor.encrypt_matrix(original)

        assert isinstance(encrypted, EncryptedMatrix)
        assert encrypted.shape == (3, 2)
        assert len(encrypted) == 3

        decrypted = encryptor.decrypt_matrix(encrypted)
        np.testing.assert_array_almost_equal(decrypted, original, decimal=3)

    def test_encrypt_scalar(self, encryptor):
        """Test scalar encryption."""
        original = 42.5
        encrypted = encryptor.encrypt_scalar(original)
        decrypted = encryptor.decrypt_scalar(encrypted)
        assert abs(decrypted - original) < 0.01

    def test_vector_exceeds_slots_raises(self, encryptor):
        """Test that vector exceeding max slots raises ValueError."""
        # Create vector larger than max_slots (4096)
        large_vector = list(range(5000))
        with pytest.raises(ValueError, match="exceeds max slots"):
            encryptor.encrypt_vector(large_vector)

    def test_encrypted_vector_operations(self, encryptor):
        """Test arithmetic operations on encrypted vectors."""
        v1 = encryptor.encrypt_vector([1.0, 2.0, 3.0])
        v2 = encryptor.encrypt_vector([4.0, 5.0, 6.0])

        # Addition
        result = v1 + v2
        decrypted = encryptor.decrypt_vector(result)
        np.testing.assert_array_almost_equal(decrypted, [5.0, 7.0, 9.0], decimal=2)

        # Subtraction
        result = v2 - v1
        decrypted = encryptor.decrypt_vector(result)
        np.testing.assert_array_almost_equal(decrypted, [3.0, 3.0, 3.0], decimal=2)

        # Scalar multiplication
        result = v1 * 2.0
        decrypted = encryptor.decrypt_vector(result)
        np.testing.assert_array_almost_equal(decrypted, [2.0, 4.0, 6.0], decimal=2)


class TestSecureDataLoader:
    """Tests for SecureDataLoader."""

    @pytest.fixture
    def loader(self):
        """Create loader fixture."""
        return SecureDataLoader()

    def test_encrypt_numpy_array(self, loader):
        """Test encrypting numpy array."""
        data = np.array([[1.0, 2.0], [3.0, 4.0]])
        encrypted = loader.encrypt(data)

        assert isinstance(encrypted, EncryptedDataset)
        assert encrypted.n_samples == 2
        assert encrypted.n_features == 2
        assert encrypted.y is None

    def test_encrypt_dataframe(self, loader):
        """Test encrypting pandas DataFrame."""
        df = pd.DataFrame(
            {
                "feature_a": [1.0, 2.0, 3.0],
                "feature_b": [4.0, 5.0, 6.0],
            }
        )
        encrypted = loader.encrypt(df)

        assert encrypted.n_samples == 3
        assert encrypted.n_features == 2
        assert encrypted.feature_names == ["feature_a", "feature_b"]

    def test_encrypt_with_target(self, loader):
        """Test encrypting DataFrame with target column."""
        df = pd.DataFrame(
            {
                "feature_a": [1.0, 2.0, 3.0],
                "target": [0.0, 1.0, 0.0],
            }
        )
        encrypted = loader.encrypt(df, target_column="target")

        assert encrypted.n_features == 1
        assert encrypted.y is not None
        assert "target" not in encrypted.feature_names

    def test_encrypt_decrypt_roundtrip(self, loader):
        """Test full encrypt/decrypt cycle."""
        original = np.array([[1.0, 2.0], [3.0, 4.0]])
        encrypted = loader.encrypt(original)
        decrypted = loader.decrypt(encrypted.X)

        # After normalization and denormalization, values should be close
        np.testing.assert_array_almost_equal(decrypted, original, decimal=2)

    def test_invalid_target_column_raises(self, loader):
        """Test that invalid target column raises ValueError."""
        df = pd.DataFrame({"a": [1.0], "b": [2.0]})
        with pytest.raises(ValueError, match="not found"):
            loader.encrypt(df, target_column="nonexistent")

    def test_empty_data_raises(self, loader):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            loader.encrypt(np.array([]))

    def test_normalization_disabled(self):
        """Test loader without normalization."""
        loader = SecureDataLoader(normalize=False)
        data = np.array([[100.0, 200.0]])
        encrypted = loader.encrypt(data)
        decrypted = loader.decrypt(encrypted.X, denormalize=False)
        np.testing.assert_array_almost_equal(decrypted, data, decimal=1)

    def test_unsupported_scheme_raises(self):
        """Test that unsupported encryption scheme raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported"):
            SecureDataLoader(encryption_scheme="BFV")


class TestValidators:
    """Tests for validation utilities."""

    def test_validate_numeric_with_nan(self):
        """Test NaN validation."""
        data = np.array([1.0, np.nan, 3.0])
        with pytest.raises(ValidationError, match="NaN"):
            validate_numeric_data(data)

        # Should pass with allow_nan=True
        validate_numeric_data(data, allow_nan=True)

    def test_validate_numeric_with_inf(self):
        """Test infinity validation."""
        data = np.array([1.0, np.inf, 3.0])
        with pytest.raises(ValidationError, match="infinite"):
            validate_numeric_data(data)

    def test_check_fhe_compatibility(self):
        """Test FHE compatibility check."""
        # Valid data
        data = np.array([[1.0, 2.0], [3.0, 4.0]])
        result = check_fhe_compatibility(data)
        assert result["compatible"]
        assert result["stats"]["n_samples"] == 2
        assert result["stats"]["n_features"] == 2

    def test_check_fhe_compatibility_with_nan(self):
        """Test compatibility check catches NaN."""
        data = np.array([[1.0, np.nan]])
        result = check_fhe_compatibility(data)
        assert not result["compatible"]
        assert any("NaN" in w for w in result["warnings"])
