"""Tests for FHE-ML REST API client."""

from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from sdk.api.client import (
    FHEMLClient,
    FHEMLClientError,
    APIError,
    ConnectionError,
    connect,
)


class TestFHEMLClientErrors:
    """Tests for client error classes."""

    def test_fheml_client_error_base(self):
        """Test base client error."""
        error = FHEMLClientError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_api_error(self):
        """Test API error with status code."""
        error = APIError(404, "Not found", "Model not found")
        assert error.status_code == 404
        assert error.message == "Not found"
        assert error.detail == "Model not found"
        assert "404" in str(error)
        assert "Not found" in str(error)

    def test_api_error_without_detail(self):
        """Test API error without detail."""
        error = APIError(500, "Server error")
        assert error.status_code == 500
        assert error.detail is None

    def test_connection_error(self):
        """Test connection error."""
        error = ConnectionError("Failed to connect")
        assert isinstance(error, FHEMLClientError)
        assert "Failed to connect" in str(error)


class TestFHEMLClientInit:
    """Tests for client initialization."""

    def test_init_default_values(self):
        """Test client initialization with defaults."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = MagicMock()
                client = FHEMLClient()

                assert client.base_url == "http://localhost:8000"
                assert client.timeout == 30.0
                assert client.api_key is None

    def test_init_custom_values(self):
        """Test client initialization with custom values."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = MagicMock()
                client = FHEMLClient(
                    base_url="http://custom:9000",
                    timeout=60.0,
                    api_key="test_key",
                )

                assert client.base_url == "http://custom:9000"
                assert client.timeout == 60.0
                assert client.api_key == "test_key"

    def test_init_strips_trailing_slash(self):
        """Test client strips trailing slash from URL."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = MagicMock()
                client = FHEMLClient(base_url="http://localhost:8000/")

                assert client.base_url == "http://localhost:8000"

    def test_init_no_http_library(self):
        """Test client raises error when no HTTP library available."""
        with patch("sdk.api.client.HAS_HTTPX", False):
            with patch("sdk.api.client.HAS_REQUESTS", False):
                with pytest.raises(ImportError) as exc_info:
                    FHEMLClient()

                assert "httpx" in str(exc_info.value)


class TestFHEMLClientHeaders:
    """Tests for client header generation."""

    def test_get_headers_no_api_key(self):
        """Test headers without API key."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = MagicMock()
                client = FHEMLClient()
                headers = client._get_headers()

                assert headers["Content-Type"] == "application/json"
                assert "Authorization" not in headers

    def test_get_headers_with_api_key(self):
        """Test headers with API key."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = MagicMock()
                client = FHEMLClient(api_key="my_api_key")
                headers = client._get_headers()

                assert headers["Authorization"] == "Bearer my_api_key"


class TestFHEMLClientRequest:
    """Tests for client HTTP request method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.content = b'{"result": "success"}'
        self.mock_response.json.return_value = {"result": "success"}

    def test_request_get_success(self):
        """Test successful GET request."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_client.request.return_value = self.mock_response
                mock_httpx.Client.return_value = mock_client

                client = FHEMLClient()
                result = client._request("GET", "/test")

                assert result == {"result": "success"}
                mock_client.request.assert_called_once()

    def test_request_post_with_data(self):
        """Test POST request with data."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_client.request.return_value = self.mock_response
                mock_httpx.Client.return_value = mock_client

                client = FHEMLClient()
                result = client._request("POST", "/test", {"key": "value"})

                assert result == {"result": "success"}
                call_args = mock_client.request.call_args
                assert call_args[1]["json"] == {"key": "value"}

    def test_request_error_response(self):
        """Test request handles error response."""
        error_response = MagicMock()
        error_response.status_code = 404
        error_response.content = b'{"detail": "Not found"}'
        error_response.json.return_value = {"detail": "Not found"}

        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_client.request.return_value = error_response
                mock_httpx.Client.return_value = mock_client
                mock_httpx.ConnectError = Exception  # Mock the exception class

                client = FHEMLClient()

                with pytest.raises(APIError) as exc_info:
                    client._request("GET", "/nonexistent")

                assert exc_info.value.status_code == 404

    def test_request_empty_response(self):
        """Test request handles empty response."""
        empty_response = MagicMock()
        empty_response.status_code = 200
        empty_response.content = b""

        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_client.request.return_value = empty_response
                mock_httpx.Client.return_value = mock_client

                client = FHEMLClient()
                result = client._request("DELETE", "/test")

                assert result == {}


class TestFHEMLClientMethods:
    """Tests for client API methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()

    def test_health(self):
        """Test health endpoint."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {"status": "healthy"}
                    result = client.health()

                    mock_request.assert_called_once_with("GET", "/health")
                    assert result["status"] == "healthy"

    def test_get_model_types(self):
        """Test get model types endpoint."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {
                        "model_types": [
                            {"name": "linear_regression"},
                            {"name": "logistic_regression"},
                        ]
                    }
                    result = client.get_model_types()

                    assert len(result) == 2
                    assert result[0]["name"] == "linear_regression"

    def test_create_model(self):
        """Test create model endpoint."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {"model_id": "model_123"}
                    result = client.create_model(
                        "linear_regression",
                        config={"learning_rate": 0.01},
                    )

                    assert result == "model_123"
                    call_args = mock_request.call_args
                    assert call_args[0][1] == "/models"
                    assert call_args[0][2]["model_type"] == "linear_regression"

    def test_get_model(self):
        """Test get model endpoint."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {
                        "model_id": "model_123",
                        "model_type": "linear_regression",
                    }
                    result = client.get_model("model_123")

                    mock_request.assert_called_once_with("GET", "/models/model_123")
                    assert result["model_id"] == "model_123"

    def test_list_models(self):
        """Test list models endpoint."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = [
                        {"model_id": "model_1"},
                        {"model_id": "model_2"},
                    ]
                    result = client.list_models()

                    assert len(result) == 2

    def test_delete_model(self):
        """Test delete model endpoint."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {}
                    result = client.delete_model("model_123")

                    mock_request.assert_called_once_with("DELETE", "/models/model_123")
                    assert result is True

    def test_get_params(self):
        """Test get params endpoint."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {"weights": [0.1, 0.2]}
                    result = client.get_params("model_123")

                    mock_request.assert_called_once_with("GET", "/models/model_123/params")
                    assert result["weights"] == [0.1, 0.2]


class TestFHEMLClientTraining:
    """Tests for client training methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()

    def test_train_with_lists(self):
        """Test train with list inputs."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {"status": "trained", "epochs": 100}
                    result = client.train(
                        "model_123",
                        X=[[1, 2], [3, 4]],
                        y=[0, 1],
                    )

                    assert result["status"] == "trained"
                    call_data = mock_request.call_args[0][2]
                    assert call_data["X"] == [[1, 2], [3, 4]]
                    assert call_data["y"] == [0, 1]

    def test_train_with_numpy(self):
        """Test train with numpy array inputs."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {"status": "trained"}
                    X = np.array([[1, 2], [3, 4]])
                    y = np.array([0, 1])

                    client.train("model_123", X=X, y=y)

                    call_data = mock_request.call_args[0][2]
                    assert call_data["X"] == [[1, 2], [3, 4]]
                    assert call_data["y"] == [0, 1]

    def test_train_without_y(self):
        """Test train without y (for clustering)."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {"status": "trained"}
                    client.train("model_123", X=[[1, 2], [3, 4]])

                    call_data = mock_request.call_args[0][2]
                    assert "y" not in call_data


class TestFHEMLClientPrediction:
    """Tests for client prediction methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = MagicMock()

    def test_predict_returns_numpy(self):
        """Test predict returns numpy array."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {"predictions": [0.5, 0.8]}
                    result = client.predict("model_123", [[1, 2], [3, 4]])

                    assert isinstance(result, np.ndarray)
                    assert list(result) == [0.5, 0.8]

    def test_predict_with_numpy_input(self):
        """Test predict converts numpy input to list."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {"predictions": [0.5]}
                    X = np.array([[1, 2]])
                    client.predict("model_123", X)

                    call_data = mock_request.call_args[0][2]
                    assert call_data["X"] == [[1, 2]]

    def test_predict_proba_with_probabilities(self):
        """Test predict_proba returns probabilities."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {
                        "predictions": [1, 0],
                        "probabilities": [[0.2, 0.8], [0.9, 0.1]],
                    }
                    result = client.predict_proba("model_123", [[1, 2], [3, 4]])

                    assert isinstance(result, np.ndarray)
                    assert result.shape == (2, 2)

    def test_predict_proba_without_probabilities(self):
        """Test predict_proba returns None when not available."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = self.mock_client
                client = FHEMLClient()

                with patch.object(client, "_request") as mock_request:
                    mock_request.return_value = {"predictions": [1, 0]}
                    result = client.predict_proba("model_123", [[1, 2], [3, 4]])

                    assert result is None


class TestFHEMLClientFitPredict:
    """Tests for fit_predict convenience method."""

    def test_fit_predict(self):
        """Test fit_predict creates, trains, and predicts."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = MagicMock()
                client = FHEMLClient()

                with patch.object(client, "create_model") as mock_create:
                    with patch.object(client, "train") as mock_train:
                        with patch.object(client, "predict") as mock_predict:
                            mock_create.return_value = "model_123"
                            mock_train.return_value = {"status": "trained"}
                            mock_predict.return_value = np.array([0.5, 0.8])

                            model_id, predictions = client.fit_predict(
                                "linear_regression",
                                X=[[1, 2], [3, 4]],
                                y=[0.5, 0.8],
                            )

                            assert model_id == "model_123"
                            assert list(predictions) == [0.5, 0.8]
                            mock_create.assert_called_once()
                            mock_train.assert_called_once()
                            mock_predict.assert_called_once()


class TestFHEMLClientContextManager:
    """Tests for client context manager."""

    def test_context_manager(self):
        """Test client as context manager."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_client_instance = MagicMock()
                mock_httpx.Client.return_value = mock_client_instance

                with FHEMLClient() as client:
                    assert client is not None

                mock_client_instance.close.assert_called_once()

    def test_close_httpx(self):
        """Test close with httpx client."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_client_instance = MagicMock()
                mock_httpx.Client.return_value = mock_client_instance

                client = FHEMLClient()
                client.close()

                mock_client_instance.close.assert_called_once()

    def test_repr(self):
        """Test client string representation."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = MagicMock()
                client = FHEMLClient(base_url="http://test:8000")

                assert "FHEMLClient" in repr(client)
                assert "http://test:8000" in repr(client)


class TestConnectFunction:
    """Tests for connect convenience function."""

    def test_connect_success(self):
        """Test connect creates and verifies client."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = MagicMock()

                with patch.object(FHEMLClient, "health") as mock_health:
                    mock_health.return_value = {"status": "healthy"}
                    client = connect("http://localhost:8000")

                    assert isinstance(client, FHEMLClient)
                    mock_health.assert_called_once()

    def test_connect_with_kwargs(self):
        """Test connect passes kwargs to client."""
        with patch("sdk.api.client.HAS_HTTPX", True):
            with patch("sdk.api.client.httpx") as mock_httpx:
                mock_httpx.Client.return_value = MagicMock()

                with patch.object(FHEMLClient, "health") as mock_health:
                    mock_health.return_value = {"status": "healthy"}
                    client = connect(
                        "http://localhost:8000",
                        timeout=60.0,
                        api_key="test_key",
                    )

                    assert client.timeout == 60.0
                    assert client.api_key == "test_key"
