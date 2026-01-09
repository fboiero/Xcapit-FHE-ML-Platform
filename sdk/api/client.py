"""Python client for Xcapit FHE-ML REST API.

Provides a convenient interface to interact with the FHE-ML API server.

Usage:
    from sdk.api.client import FHEMLClient

    client = FHEMLClient("http://localhost:8000")

    # Create and train model
    model_id = client.create_model("logistic_regression")
    client.train(model_id, X_train, y_train)

    # Make predictions
    predictions = client.predict(model_id, X_test)
"""

from typing import Any, Optional, Union

import numpy as np

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class FHEMLClientError(Exception):
    """Base exception for FHE-ML client errors."""

    pass


class APIError(FHEMLClientError):
    """API returned an error response."""

    def __init__(self, status_code: int, message: str, detail: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(f"API Error {status_code}: {message}")


class ConnectionError(FHEMLClientError):
    """Failed to connect to API server."""

    pass


class FHEMLClient:
    """Client for Xcapit FHE-ML REST API.

    Args:
        base_url: API server URL (e.g., "http://localhost:8000").
        timeout: Request timeout in seconds.
        api_key: Optional API key for authentication.

    Example:
        >>> client = FHEMLClient("http://localhost:8000")
        >>> model_id = client.create_model("linear_regression")
        >>> client.train(model_id, [[1,2], [3,4]], [0.5, 1.5])
        >>> predictions = client.predict(model_id, [[2,3]])
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key

        # Determine which HTTP library to use
        if HAS_HTTPX:
            self._client = httpx.Client(timeout=timeout)
            self._use_httpx = True
        elif HAS_REQUESTS:
            self._session = requests.Session()
            self._use_httpx = False
        else:
            raise ImportError(
                "Either 'httpx' or 'requests' is required. Install with: pip install httpx"
            )

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, DELETE).
            endpoint: API endpoint path.
            data: Request body data.

        Returns:
            Response JSON.

        Raises:
            APIError: If API returns error response.
            ConnectionError: If connection fails.
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        try:
            if self._use_httpx:
                response = self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                status_code = response.status_code
                response_data = response.json() if response.content else {}
            else:
                response = self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout,
                )
                status_code = response.status_code
                response_data = response.json() if response.content else {}

            if status_code >= 400:
                raise APIError(
                    status_code=status_code,
                    message=response_data.get("detail", "Unknown error"),
                    detail=response_data.get("error"),
                )

            return response_data

        except httpx.ConnectError if HAS_HTTPX else Exception as e:
            if "ConnectError" in str(type(e).__name__) or "Connection" in str(e):
                raise ConnectionError(f"Failed to connect to {url}: {e}")
            raise

    def health(self) -> dict[str, Any]:
        """Check API health.

        Returns:
            Health status dict with 'status', 'version', 'timestamp'.
        """
        return self._request("GET", "/health")

    def get_model_types(self) -> list[dict[str, Any]]:
        """Get available model types.

        Returns:
            List of model type configurations.
        """
        response = self._request("GET", "/model-types")
        return response.get("model_types", [])

    def create_model(
        self,
        model_type: str,
        config: Optional[dict[str, Any]] = None,
    ) -> str:
        """Create a new model.

        Args:
            model_type: Type of model ('linear_regression', 'logistic_regression',
                       'decision_tree', 'kmeans').
            config: Model configuration parameters.

        Returns:
            Model ID.

        Example:
            >>> model_id = client.create_model(
            ...     "logistic_regression",
            ...     config={"learning_rate": 0.1, "n_epochs": 100}
            ... )
        """
        response = self._request(
            "POST",
            "/models",
            {
                "model_type": model_type,
                "config": config,
            },
        )
        return response["model_id"]

    def get_model(self, model_id: str) -> dict[str, Any]:
        """Get model details.

        Args:
            model_id: Model identifier.

        Returns:
            Model info dict.
        """
        return self._request("GET", f"/models/{model_id}")

    def list_models(self) -> list[dict[str, Any]]:
        """List all models.

        Returns:
            List of model info dicts.
        """
        return self._request("GET", "/models")

    def delete_model(self, model_id: str) -> bool:
        """Delete a model.

        Args:
            model_id: Model identifier.

        Returns:
            True if deleted successfully.
        """
        self._request("DELETE", f"/models/{model_id}")
        return True

    def get_params(self, model_id: str) -> dict[str, Any]:
        """Get model parameters.

        Args:
            model_id: Model identifier.

        Returns:
            Model parameters dict.
        """
        return self._request("GET", f"/models/{model_id}/params")

    def train(
        self,
        model_id: str,
        X: Union[list[list[float]], np.ndarray],
        y: Optional[Union[list[float], np.ndarray]] = None,
    ) -> dict[str, Any]:
        """Train a model.

        Args:
            model_id: Model identifier.
            X: Feature matrix.
            y: Target vector (optional for clustering models).

        Returns:
            Training result dict with 'status', 'epochs', 'final_loss'.

        Example:
            >>> result = client.train(model_id, X_train, y_train)
            >>> print(f"Trained for {result['epochs']} epochs")
        """
        # Convert numpy arrays to lists
        if isinstance(X, np.ndarray):
            X = X.tolist()
        if isinstance(y, np.ndarray):
            y = y.tolist()

        data = {"X": X}
        if y is not None:
            data["y"] = y

        return self._request("POST", f"/models/{model_id}/train", data)

    def predict(
        self,
        model_id: str,
        X: Union[list[list[float]], np.ndarray],
    ) -> np.ndarray:
        """Make predictions.

        Args:
            model_id: Model identifier.
            X: Feature matrix.

        Returns:
            Predictions as numpy array.

        Example:
            >>> predictions = client.predict(model_id, X_test)
        """
        # Convert numpy arrays to lists
        if isinstance(X, np.ndarray):
            X = X.tolist()

        response = self._request("POST", f"/models/{model_id}/predict", {"X": X})
        return np.array(response["predictions"])

    def predict_proba(
        self,
        model_id: str,
        X: Union[list[list[float]], np.ndarray],
    ) -> Optional[np.ndarray]:
        """Get prediction probabilities (for classification models).

        Args:
            model_id: Model identifier.
            X: Feature matrix.

        Returns:
            Probability matrix as numpy array, or None if not available.
        """
        if isinstance(X, np.ndarray):
            X = X.tolist()

        response = self._request("POST", f"/models/{model_id}/predict", {"X": X})

        if response.get("probabilities"):
            return np.array(response["probabilities"])
        return None

    def fit_predict(
        self,
        model_type: str,
        X: Union[list[list[float]], np.ndarray],
        y: Optional[Union[list[float], np.ndarray]] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> tuple:
        """Create model, train, and predict in one call.

        Args:
            model_type: Type of model.
            X: Feature matrix for training.
            y: Target vector for training.
            config: Model configuration.

        Returns:
            Tuple of (model_id, predictions).

        Example:
            >>> model_id, preds = client.fit_predict(
            ...     "linear_regression", X_train, y_train
            ... )
        """
        model_id = self.create_model(model_type, config)
        self.train(model_id, X, y)
        predictions = self.predict(model_id, X)
        return model_id, predictions

    def close(self):
        """Close the client connection."""
        if self._use_httpx:
            self._client.close()
        elif hasattr(self, "_session"):
            self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self) -> str:
        return f"FHEMLClient(base_url='{self.base_url}')"


# Convenience function
def connect(
    base_url: str = "http://localhost:8000",
    **kwargs,
) -> FHEMLClient:
    """Create a connected FHE-ML client.

    Args:
        base_url: API server URL.
        **kwargs: Additional arguments passed to FHEMLClient.

    Returns:
        Connected FHEMLClient instance.
    """
    client = FHEMLClient(base_url, **kwargs)
    # Verify connection
    client.health()
    return client
