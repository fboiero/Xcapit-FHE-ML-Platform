"""Integration tests with real TenSEAL FHE operations.

These tests verify end-to-end functionality with actual encryption,
not mocks. They are slower but validate real FHE behavior.

Run with: pytest tests/test_fhe_integration.py -v
"""

import numpy as np
import pytest

# Check if TenSEAL is available
try:
    import tenseal as ts

    TENSEAL_AVAILABLE = True
except ImportError:
    TENSEAL_AVAILABLE = False

pytestmark = pytest.mark.skipif(not TENSEAL_AVAILABLE, reason="TenSEAL not installed")


# ========== Fixtures ==========


@pytest.fixture(scope="module")
def ckks_context():
    """Create a CKKS context for testing."""
    context = ts.context(
        ts.SCHEME_TYPE.CKKS, poly_modulus_degree=8192, coeff_mod_bit_sizes=[60, 40, 40, 60]
    )
    context.generate_galois_keys()
    context.global_scale = 2**40
    return context


@pytest.fixture
def sample_data():
    """Generate sample data for testing."""
    np.random.seed(42)
    X = np.random.randn(50, 5)
    y = X @ np.array([1.5, -0.5, 2.0, -1.0, 0.5]) + np.random.randn(50) * 0.1
    return X, y


@pytest.fixture
def classification_data():
    """Generate classification data for testing."""
    np.random.seed(42)
    X = np.random.randn(100, 4)
    y = (X[:, 0] + X[:, 1] > 0).astype(float)
    return X, y


# ========== Basic Encryption Tests ==========


class TestBasicEncryption:
    """Test basic CKKS encryption operations."""

    def test_encrypt_vector(self, ckks_context):
        """Test encrypting a vector."""
        plain = [1.0, 2.0, 3.0, 4.0, 5.0]
        encrypted = ts.ckks_vector(ckks_context, plain)

        decrypted = encrypted.decrypt()
        assert len(decrypted) == len(plain)
        for i in range(len(plain)):
            assert abs(decrypted[i] - plain[i]) < 1e-3

    def test_encrypted_addition(self, ckks_context):
        """Test addition on encrypted vectors."""
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        expected = [5.0, 7.0, 9.0]

        enc_a = ts.ckks_vector(ckks_context, a)
        enc_b = ts.ckks_vector(ckks_context, b)

        result = enc_a + enc_b
        decrypted = result.decrypt()

        for i in range(len(expected)):
            assert abs(decrypted[i] - expected[i]) < 1e-3

    def test_encrypted_multiplication(self, ckks_context):
        """Test element-wise multiplication on encrypted vectors."""
        a = [1.0, 2.0, 3.0]
        b = [2.0, 3.0, 4.0]
        expected = [2.0, 6.0, 12.0]

        enc_a = ts.ckks_vector(ckks_context, a)
        enc_b = ts.ckks_vector(ckks_context, b)

        result = enc_a * enc_b
        decrypted = result.decrypt()

        for i in range(len(expected)):
            assert abs(decrypted[i] - expected[i]) < 1e-2

    def test_scalar_multiplication(self, ckks_context):
        """Test scalar multiplication on encrypted vector."""
        plain = [1.0, 2.0, 3.0]
        scalar = 2.5
        expected = [2.5, 5.0, 7.5]

        encrypted = ts.ckks_vector(ckks_context, plain)
        result = encrypted * scalar
        decrypted = result.decrypt()

        for i in range(len(expected)):
            assert abs(decrypted[i] - expected[i]) < 1e-3

    def test_dot_product(self, ckks_context):
        """Test dot product on encrypted vectors."""
        a = [1.0, 2.0, 3.0, 4.0]
        b = [0.5, 0.5, 0.5, 0.5]
        expected = 5.0  # 1*0.5 + 2*0.5 + 3*0.5 + 4*0.5

        enc_a = ts.ckks_vector(ckks_context, a)

        # Dot product with plaintext weights
        result = enc_a.dot(b)
        decrypted = result.decrypt()

        assert abs(decrypted[0] - expected) < 1e-2


# ========== SDK Encryption Layer Tests ==========


class TestSDKEncryption:
    """Test SDK encryption wrapper with real TenSEAL."""

    def test_context_manager_creation(self):
        """Test FHEContextManager creates valid context."""
        from sdk.encryption import FHEContextManager

        ctx_mgr = FHEContextManager()
        ctx_mgr.create_context()

        assert ctx_mgr.context is not None
        assert ctx_mgr.is_initialized

    def test_ckks_encryptor_basic(self):
        """Test CKKSEncryptor basic operations."""
        from sdk.encryption import CKKSEncryptor, FHEContextManager

        ctx_mgr = FHEContextManager()
        ctx_mgr.create_context()

        encryptor = CKKSEncryptor(ctx_mgr)

        # Encrypt and decrypt
        plain = [1.0, 2.0, 3.0, 4.0, 5.0]
        encrypted = encryptor.encrypt_vector(plain)
        decrypted = encryptor.decrypt_vector(encrypted)

        for i in range(len(plain)):
            assert abs(decrypted[i] - plain[i]) < 1e-3

    def test_encrypt_matrix(self):
        """Test matrix encryption with row-wise encoding."""
        from sdk.encryption import CKKSEncryptor, FHEContextManager

        ctx_mgr = FHEContextManager()
        ctx_mgr.create_context()

        encryptor = CKKSEncryptor(ctx_mgr)

        matrix = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        encrypted = encryptor.encrypt_matrix(matrix)

        assert len(encrypted) == 3  # 3 rows

        # Decrypt each row
        for i, enc_row in enumerate(encrypted):
            dec_row = encryptor.decrypt_vector(enc_row)
            for j in range(2):
                assert abs(dec_row[j] - matrix[i, j]) < 1e-3


# ========== Linear Regression FHE Tests ==========


class TestLinearRegressionFHE:
    """Test LinearRegression with real FHE operations."""

    def test_fit_and_predict_encrypted(self, sample_data):
        """Test training and prediction with encryption."""
        import pandas as pd

        from sdk.models import LinearRegression
        from sdk.utils.data_loader import SecureDataLoader

        X, y = sample_data
        X_train, X_test = X[:40], X[40:]
        y_train, _y_test = y[:40], y[40:]

        # Create DataFrame with target column for encryption
        df_train = pd.DataFrame(X_train, columns=[f"feature_{i}" for i in range(X_train.shape[1])])
        df_train["target"] = y_train

        # Create SecureDataLoader (creates its own context and encryptor)
        loader = SecureDataLoader(encryption_scheme="CKKS")

        # Encrypt training data with target column
        encrypted_dataset = loader.encrypt(df_train, target_column="target")

        # Train model on encrypted data (using loader's encryptor)
        model = LinearRegression(learning_rate=0.01, n_epochs=50, encryptor=loader.encryptor)
        model.fit(encrypted_dataset)

        # Verify model is trained (has weights)
        assert model._weights is not None
        assert model._bias is not None
        assert len(model._weights) == X_train.shape[1]

        # Predict on plaintext test data (model internally uses weights)
        plaintext_preds = model.predict_plaintext(X_test)
        assert len(plaintext_preds) == len(X_test)

        # Verify predictions are reasonable (not NaN or Inf)
        assert not np.any(np.isnan(plaintext_preds))
        assert not np.any(np.isinf(plaintext_preds))

    def test_encrypted_gradient_computation(self, sample_data, ckks_context):
        """Test gradient computation on encrypted data."""
        X, y = sample_data
        X_small = X[:5]  # Use small batch for speed
        y[:5]

        # Initialize random weights
        n_features = X_small.shape[1]
        weights = np.random.randn(n_features) * 0.1

        # Encrypt data and compute dot products using TenSEAL directly
        encrypted_preds = []
        for row in X_small:
            enc_row = ts.ckks_vector(ckks_context, row.tolist())
            pred = enc_row.dot(weights.tolist())
            encrypted_preds.append(pred)

        # Decrypt predictions
        decrypted_preds = [p.decrypt()[0] for p in encrypted_preds]

        # Compare with plaintext computation
        plaintext_preds = X_small @ weights

        for i in range(len(decrypted_preds)):
            assert abs(decrypted_preds[i] - plaintext_preds[i]) < 0.1


# ========== Logistic Regression FHE Tests ==========


class TestLogisticRegressionFHE:
    """Test LogisticRegression with real FHE operations."""

    def test_sigmoid_approximation_encrypted(self, ckks_context):
        """Test polynomial sigmoid approximation on encrypted data."""
        # Values in sigmoid range
        x_values = [-2.0, -1.0, 0.0, 1.0, 2.0]

        # Encrypt
        encrypted = ts.ckks_vector(ckks_context, x_values)

        # Polynomial sigmoid approximation: 0.5 + 0.25*x (linear)
        # More accurate: 0.5 + 0.197*x + 0.004*x^3
        result = encrypted * 0.197
        result = result + 0.5

        decrypted = result.decrypt()

        # Check outputs are in valid range
        for val in decrypted:
            assert 0 <= val <= 1

    def test_logistic_prediction_pipeline(self, classification_data):
        """Test full logistic regression prediction on encrypted data."""
        import pandas as pd

        from sdk.models import LogisticRegression
        from sdk.utils.data_loader import SecureDataLoader

        X, y = classification_data
        X_train, X_test = X[:80], X[80:]
        y_train, _y_test = y[:80], y[80:]

        # Create DataFrame with target column for encryption
        df_train = pd.DataFrame(X_train, columns=[f"feature_{i}" for i in range(X_train.shape[1])])
        df_train["target"] = y_train

        # Create SecureDataLoader (creates its own context and encryptor)
        loader = SecureDataLoader(encryption_scheme="CKKS")

        # Encrypt training data with target column
        encrypted_dataset = loader.encrypt(df_train, target_column="target")

        # Get encryptor from loader for prediction phase
        encryptor = loader.encryptor

        # Train model on encrypted data
        model = LogisticRegression(learning_rate=0.1, n_epochs=100, encryptor=encryptor)
        model.fit(encrypted_dataset)

        # Verify model is trained (has weights)
        assert model._weights is not None
        assert model._bias is not None
        assert len(model._weights) == X_train.shape[1]

        # Test plaintext predictions work
        plaintext_preds = model.predict_plaintext(X_test)
        assert len(plaintext_preds) == len(X_test)

        # Verify predictions are probabilities (between 0 and 1)
        assert np.all(plaintext_preds >= 0)
        assert np.all(plaintext_preds <= 1)

        # Test FHE-based encrypted prediction on single sample
        # using the ciphertext directly for dot product with plaintext weights
        sample = X_test[0]
        enc_sample = encryptor.encrypt_vector(sample.tolist())

        # Use ciphertext directly to compute dot product with plaintext weights
        w = model._weights.tolist()
        b = float(model._bias)

        # Access underlying ciphertext for dot product
        linear_result = enc_sample.ciphertext.dot(w)
        linear_result = linear_result + b

        # Apply polynomial sigmoid approximation
        sigmoid_result = linear_result * 0.197 + 0.5

        # Decrypt and verify
        decrypted = sigmoid_result.decrypt()
        assert len(decrypted) > 0

        # Prediction should be a valid probability-like value
        pred_value = decrypted[0]
        assert not np.isnan(pred_value)
        assert not np.isinf(pred_value)


# ========== K-Means FHE Tests ==========


class TestKMeansFHE:
    """Test K-Means with real FHE operations."""

    def test_distance_computation_encrypted(self, ckks_context):
        """Test Euclidean distance computation on encrypted data."""
        point = [1.0, 2.0, 3.0]
        centroid = [4.0, 5.0, 6.0]

        # Expected squared distance: (1-4)^2 + (2-5)^2 + (3-6)^2 = 27
        expected_sq_dist = 27.0

        # Encrypt point
        enc_point = ts.ckks_vector(ckks_context, point)

        # Compute difference
        diff = enc_point - centroid

        # Square
        sq_diff = diff * diff

        # Sum (using dot with ones)
        ones = [1.0, 1.0, 1.0]
        sq_dist = sq_diff.dot(ones)

        decrypted = sq_dist.decrypt()
        assert abs(decrypted[0] - expected_sq_dist) < 0.5

    def test_soft_assignment_encrypted(self, ckks_context):
        """Test soft cluster assignment computation."""
        # Distances to 3 centroids
        distances = [1.0, 4.0, 9.0]

        # Soft assignment with negative distances (softmax-like)
        # Lower distance = higher assignment
        neg_dist = [-d for d in distances]

        enc_neg = ts.ckks_vector(ckks_context, neg_dist)

        # Decrypt and apply softmax in plaintext (for testing)
        decrypted = enc_neg.decrypt()

        # Manual softmax
        exp_vals = [np.exp(d) for d in decrypted[:3]]
        sum_exp = sum(exp_vals)
        assignments = [e / sum_exp for e in exp_vals]

        # Closest centroid should have highest assignment
        assert assignments[0] > assignments[1] > assignments[2]


# ========== Security Level Tests ==========


class TestSecurityLevels:
    """Test different security levels."""

    @pytest.mark.parametrize("poly_degree", [8192, 16384])
    def test_security_level_configuration(self, poly_degree):
        """Test context creation with different poly modulus degrees."""
        from sdk.encryption import CKKSParameters, FHEContextManager, SecurityLevel

        # Create params with specific poly degree (4096 not supported with these coeff mods)
        params = CKKSParameters(
            poly_modulus_degree=poly_degree,
            coeff_mod_bit_sizes=(60, 40, 40, 60),
            scale=2**40,
            security_level=SecurityLevel.TC128,
        )

        ctx_mgr = FHEContextManager(params=params)
        ctx_mgr.create_context()

        assert ctx_mgr.is_initialized
        assert ctx_mgr.params.poly_modulus_degree == poly_degree


# ========== Serialization Tests ==========


class TestEncryptedSerialization:
    """Test serialization of encrypted data."""

    def test_encrypted_vector_serialization(self, ckks_context):
        """Test serializing and deserializing encrypted vector."""
        plain = [1.0, 2.0, 3.0, 4.0, 5.0]

        encrypted = ts.ckks_vector(ckks_context, plain)

        # Serialize
        serialized = encrypted.serialize()
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0

        # Deserialize (need context with secret key)
        deserialized = ts.ckks_vector_from(ckks_context, serialized)

        # Decrypt and verify
        decrypted = deserialized.decrypt()
        for i in range(len(plain)):
            assert abs(decrypted[i] - plain[i]) < 1e-3

    def test_context_serialization(self):
        """Test context serialization without secret key."""
        from sdk.encryption import FHEContextManager

        ctx_mgr = FHEContextManager()
        ctx_mgr.create_context()

        # Get public context (without secret key)
        public_ctx = ctx_mgr.context.copy()
        public_ctx.make_context_public()

        # Serialize public context
        serialized = public_ctx.serialize()
        assert isinstance(serialized, bytes)

        # Can be shared without exposing secret key
        assert len(serialized) > 0


# ========== Performance Benchmark Tests ==========


class TestPerformanceBenchmarks:
    """Performance benchmarks for FHE operations."""

    def test_encryption_throughput(self, ckks_context):
        """Measure encryption throughput."""
        import time

        n_vectors = 100
        vector_size = 100

        vectors = [np.random.randn(vector_size).tolist() for _ in range(n_vectors)]

        start = time.time()
        for v in vectors:
            ts.ckks_vector(ckks_context, v)
        elapsed = time.time() - start

        throughput = n_vectors / elapsed
        print(f"\nEncryption throughput: {throughput:.2f} vectors/sec")

        # Should be able to encrypt at least 10 vectors per second
        assert throughput > 10

    def test_homomorphic_addition_speed(self, ckks_context):
        """Measure homomorphic addition speed."""
        import time

        n_ops = 1000

        a = ts.ckks_vector(ckks_context, [1.0] * 100)
        b = ts.ckks_vector(ckks_context, [2.0] * 100)

        start = time.time()
        for _ in range(n_ops):
            _ = a + b
        elapsed = time.time() - start

        ops_per_sec = n_ops / elapsed
        print(f"\nHomomorphic additions: {ops_per_sec:.2f} ops/sec")

        # Should handle at least 100 additions per second
        assert ops_per_sec > 100

    def test_dot_product_speed(self, ckks_context):
        """Measure dot product speed."""
        import time

        n_ops = 100
        size = 100

        enc = ts.ckks_vector(ckks_context, np.random.randn(size).tolist())
        weights = np.random.randn(size).tolist()

        start = time.time()
        for _ in range(n_ops):
            _ = enc.dot(weights)
        elapsed = time.time() - start

        ops_per_sec = n_ops / elapsed
        print(f"\nDot products: {ops_per_sec:.2f} ops/sec")

        # Should handle at least 50 dot products per second
        assert ops_per_sec > 50
