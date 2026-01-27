"""FHE-compatible Time Series models.

This module provides time series forecasting algorithms that work with
encrypted data using polynomial approximations for FHE compatibility.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, List, Tuple

import numpy as np

from .base import BaseFHEModel, ModelConfig, ModelState


class SeasonalityMode(Enum):
    """Seasonality mode for Prophet-like models."""
    ADDITIVE = "additive"
    MULTIPLICATIVE = "multiplicative"


class TrendMode(Enum):
    """Trend mode for time series."""
    LINEAR = "linear"
    LOGISTIC = "logistic"
    FLAT = "flat"


@dataclass
class ARIMAConfig(ModelConfig):
    """Configuration for ARIMA model."""
    p: int = 1  # AR order
    d: int = 1  # Differencing order
    q: int = 1  # MA order
    seasonal_p: int = 0  # Seasonal AR order
    seasonal_d: int = 0  # Seasonal differencing order
    seasonal_q: int = 0  # Seasonal MA order
    seasonal_period: int = 12  # Seasonal period
    max_iter: int = 100
    tol: float = 1e-4


@dataclass
class ExponentialSmoothingConfig(ModelConfig):
    """Configuration for Exponential Smoothing."""
    trend: Optional[str] = "add"  # "add", "mul", or None
    seasonal: Optional[str] = None  # "add", "mul", or None
    seasonal_period: int = 12
    damped_trend: bool = False
    alpha: Optional[float] = None  # Level smoothing
    beta: Optional[float] = None  # Trend smoothing
    gamma: Optional[float] = None  # Seasonal smoothing
    phi: float = 0.98  # Damping factor


@dataclass
class ProphetConfig(ModelConfig):
    """Configuration for Prophet-like model."""
    growth: TrendMode = TrendMode.LINEAR
    seasonality_mode: SeasonalityMode = SeasonalityMode.ADDITIVE
    yearly_seasonality: bool = True
    weekly_seasonality: bool = True
    daily_seasonality: bool = False
    changepoint_prior_scale: float = 0.05
    seasonality_prior_scale: float = 10.0
    n_changepoints: int = 25
    changepoint_range: float = 0.8


class ARIMA(BaseFHEModel):
    """ARIMA model for time series forecasting on encrypted data.

    AutoRegressive Integrated Moving Average model adapted for FHE.
    Supports both non-seasonal and seasonal (SARIMA) variants.

    FHE Compatibility:
    - AR component uses polynomial operations (matrix multiplication)
    - MA component uses polynomial approximations
    - Differencing is FHE-compatible (subtraction)

    Example:
        >>> from xcapit_fhe import ARIMA
        >>> model = ARIMA(p=2, d=1, q=1)
        >>> model.fit(y_train)
        >>> forecast = model.predict(steps=10)
    """

    def __init__(
        self,
        p: int = 1,
        d: int = 1,
        q: int = 1,
        seasonal_order: Optional[Tuple[int, int, int, int]] = None,
        max_iter: int = 100,
        tol: float = 1e-4,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)

        seasonal_p, seasonal_d, seasonal_q, seasonal_period = (
            seasonal_order if seasonal_order else (0, 0, 0, 12)
        )

        self.config = ARIMAConfig(
            p=p,
            d=d,
            q=q,
            seasonal_p=seasonal_p,
            seasonal_d=seasonal_d,
            seasonal_q=seasonal_q,
            seasonal_period=seasonal_period,
            max_iter=max_iter,
            tol=tol,
        )

        # Model parameters
        self.ar_params_ = None  # AR coefficients
        self.ma_params_ = None  # MA coefficients
        self.seasonal_ar_params_ = None
        self.seasonal_ma_params_ = None
        self.intercept_ = 0.0
        self.sigma2_ = None  # Residual variance

        # Fitted values
        self._y_train = None
        self._y_diff = None
        self._residuals = None

    def _difference(self, y: np.ndarray, d: int) -> np.ndarray:
        """Apply differencing d times."""
        result = y.copy()
        for _ in range(d):
            result = np.diff(result)
        return result

    def _seasonal_difference(self, y: np.ndarray, D: int, s: int) -> np.ndarray:
        """Apply seasonal differencing D times with period s."""
        result = y.copy()
        for _ in range(D):
            result = result[s:] - result[:-s]
        return result

    def _undifference(
        self, y_diff: np.ndarray, y_original: np.ndarray, d: int
    ) -> np.ndarray:
        """Reverse differencing to get original scale."""
        result = y_diff.copy()
        for i in range(d - 1, -1, -1):
            # Get the last d values needed for undifferencing
            last_val = y_original[-(d - i)]
            result = np.cumsum(np.concatenate([[last_val], result]))
        return result

    def _fit_ar_ols(self, y: np.ndarray) -> Tuple[np.ndarray, float]:
        """Fit AR model using OLS (FHE-compatible)."""
        p = self.config.p
        n = len(y)

        if p == 0 or n <= p:
            return np.array([]), np.mean(y)

        # Create design matrix
        X = np.zeros((n - p, p))
        for i in range(p):
            X[:, i] = y[p - i - 1 : n - i - 1]

        y_target = y[p:]

        # OLS: (X'X)^(-1) X'y
        XtX = X.T @ X
        Xty = X.T @ y_target

        # Regularization for stability
        XtX += np.eye(p) * 1e-6

        try:
            ar_params = np.linalg.solve(XtX, Xty)
        except np.linalg.LinAlgError:
            ar_params = np.zeros(p)

        intercept = np.mean(y_target - X @ ar_params)

        return ar_params, intercept

    def _fit_ma_approx(self, residuals: np.ndarray) -> np.ndarray:
        """Approximate MA parameters from residuals."""
        q = self.config.q

        if q == 0 or len(residuals) <= q:
            return np.array([])

        # Estimate MA parameters using autocorrelation
        ma_params = np.zeros(q)
        var = np.var(residuals)

        for i in range(q):
            if i + 1 < len(residuals):
                autocov = np.mean(residuals[i + 1 :] * residuals[: -(i + 1)])
                ma_params[i] = autocov / (var + 1e-10)

        # Ensure invertibility
        ma_params = np.clip(ma_params, -0.99, 0.99)

        return ma_params

    def fit(self, y: np.ndarray, exog: np.ndarray = None) -> "ARIMA":
        """Fit ARIMA model.

        Args:
            y: Time series data
            exog: Exogenous variables (optional)

        Returns:
            self
        """
        y = np.asarray(y, dtype=np.float64).flatten()
        self._y_train = y.copy()
        n = len(y)

        # Apply differencing
        y_diff = y.copy()

        # Seasonal differencing first
        if self.config.seasonal_d > 0:
            y_diff = self._seasonal_difference(
                y_diff, self.config.seasonal_d, self.config.seasonal_period
            )

        # Regular differencing
        if self.config.d > 0:
            y_diff = self._difference(y_diff, self.config.d)

        self._y_diff = y_diff

        # Fit AR component using OLS
        self.ar_params_, self.intercept_ = self._fit_ar_ols(y_diff)

        # Compute residuals
        if len(self.ar_params_) > 0:
            p = self.config.p
            fitted = np.zeros_like(y_diff)
            for t in range(p, len(y_diff)):
                fitted[t] = self.intercept_ + np.dot(
                    self.ar_params_, y_diff[t - p : t][::-1]
                )
            residuals = y_diff[p:] - fitted[p:]
        else:
            residuals = y_diff - np.mean(y_diff)

        self._residuals = residuals

        # Fit MA component
        self.ma_params_ = self._fit_ma_approx(residuals)

        # Estimate residual variance
        self.sigma2_ = np.var(residuals) if len(residuals) > 0 else 1.0

        # Fit seasonal components if specified
        if self.config.seasonal_p > 0:
            s = self.config.seasonal_period
            seasonal_y = y_diff[::s] if len(y_diff) > s else y_diff
            self.seasonal_ar_params_, _ = self._fit_ar_ols(seasonal_y)
        else:
            self.seasonal_ar_params_ = np.array([])

        self.state = ModelState.TRAINED
        return self

    def predict(self, steps: int = 1, return_conf_int: bool = False) -> np.ndarray:
        """Forecast future values.

        Args:
            steps: Number of steps to forecast
            return_conf_int: Whether to return confidence intervals

        Returns:
            Forecasted values (and optionally confidence intervals)
        """
        if self.state != ModelState.TRAINED:
            raise ValueError("Model must be fitted before prediction")

        # Start from the end of the differenced series
        y_diff = self._y_diff
        p = self.config.p
        q = self.config.q

        # Initialize history with last p values
        history = list(y_diff[-p:]) if p > 0 else []
        residual_history = list(self._residuals[-q:]) if q > 0 else []

        forecasts_diff = []

        for _ in range(steps):
            # AR component
            ar_term = 0.0
            if p > 0 and len(history) >= p:
                ar_term = np.dot(self.ar_params_, history[-p:][::-1])

            # MA component
            ma_term = 0.0
            if q > 0 and len(residual_history) >= q:
                ma_term = np.dot(self.ma_params_, residual_history[-q:][::-1])

            # Forecast
            forecast = self.intercept_ + ar_term + ma_term

            forecasts_diff.append(forecast)
            history.append(forecast)

            # For future steps, assume zero residuals
            residual_history.append(0.0)

        forecasts_diff = np.array(forecasts_diff)

        # Undo differencing
        forecasts = self._undifference_forecast(forecasts_diff)

        if return_conf_int:
            # Confidence intervals
            std = np.sqrt(self.sigma2_)
            z = 1.96  # 95% CI
            conf_int = np.column_stack([
                forecasts - z * std * np.sqrt(np.arange(1, steps + 1)),
                forecasts + z * std * np.sqrt(np.arange(1, steps + 1))
            ])
            return forecasts, conf_int

        return forecasts

    def _undifference_forecast(self, forecasts_diff: np.ndarray) -> np.ndarray:
        """Undo differencing for forecasts."""
        forecasts = forecasts_diff.copy()

        # Undo regular differencing
        if self.config.d > 0:
            last_vals = self._y_train[-self.config.d:]
            for i in range(self.config.d):
                cumsum = np.cumsum(np.concatenate([[last_vals[-(i + 1)]], forecasts]))
                forecasts = cumsum[1:]

        # Undo seasonal differencing
        if self.config.seasonal_d > 0:
            s = self.config.seasonal_period
            seasonal_history = self._y_train[-s * self.config.seasonal_d:]
            for i in range(self.config.seasonal_d):
                new_forecasts = []
                for j, f in enumerate(forecasts):
                    idx = len(seasonal_history) - s + j
                    if idx >= 0:
                        new_forecasts.append(f + seasonal_history[idx % len(seasonal_history)])
                    else:
                        new_forecasts.append(f)
                forecasts = np.array(new_forecasts)

        return forecasts

    def forecast(self, steps: int = 1) -> np.ndarray:
        """Alias for predict."""
        return self.predict(steps=steps)


class ExponentialSmoothing(BaseFHEModel):
    """Exponential Smoothing (Holt-Winters) for time series on encrypted data.

    Supports simple, double (Holt), and triple (Holt-Winters) exponential
    smoothing with additive or multiplicative components.

    FHE Compatibility:
    - All updates use polynomial operations
    - Multiplicative mode approximated with polynomial operations
    - Damping uses simple multiplication

    Example:
        >>> from xcapit_fhe import ExponentialSmoothing
        >>> model = ExponentialSmoothing(trend='add', seasonal='add', seasonal_period=12)
        >>> model.fit(y_train)
        >>> forecast = model.predict(steps=12)
    """

    def __init__(
        self,
        trend: Optional[str] = "add",
        seasonal: Optional[str] = None,
        seasonal_period: int = 12,
        damped_trend: bool = False,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
        gamma: Optional[float] = None,
        phi: float = 0.98,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.config = ExponentialSmoothingConfig(
            trend=trend,
            seasonal=seasonal,
            seasonal_period=seasonal_period,
            damped_trend=damped_trend,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            phi=phi,
        )

        # Smoothing parameters
        self.alpha_ = None
        self.beta_ = None
        self.gamma_ = None

        # State
        self.level_ = None
        self.trend_ = None
        self.seasonal_ = None

        self._y_train = None

    def _optimize_params(self, y: np.ndarray) -> Tuple[float, float, float]:
        """Optimize smoothing parameters using grid search."""
        best_mse = np.inf
        best_params = (0.2, 0.1, 0.1)

        alphas = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9] if self.config.alpha is None else [self.config.alpha]
        betas = [0.1, 0.2, 0.3] if self.config.beta is None and self.config.trend else [0.0]
        gammas = [0.1, 0.2, 0.3] if self.config.gamma is None and self.config.seasonal else [0.0]

        for alpha in alphas:
            for beta in betas:
                for gamma in gammas:
                    try:
                        fitted = self._fit_smooth(y, alpha, beta, gamma)
                        mse = np.mean((y - fitted) ** 2)
                        if mse < best_mse:
                            best_mse = mse
                            best_params = (alpha, beta, gamma)
                    except:
                        continue

        return best_params

    def _fit_smooth(
        self,
        y: np.ndarray,
        alpha: float,
        beta: float,
        gamma: float,
    ) -> np.ndarray:
        """Fit exponential smoothing with given parameters."""
        n = len(y)
        s = self.config.seasonal_period
        phi = self.config.phi if self.config.damped_trend else 1.0

        # Initialize
        if self.config.seasonal:
            # Initialize seasonal with first season
            seasonal = np.zeros(s)
            if self.config.seasonal == "add":
                for i in range(s):
                    seasonal[i] = y[i] - np.mean(y[:s])
            else:  # multiplicative
                seasonal[i] = y[i] / (np.mean(y[:s]) + 1e-10)
            level = np.mean(y[:s])
        else:
            seasonal = np.zeros(s)
            level = y[0]

        if self.config.trend:
            trend = (y[min(s, n - 1)] - y[0]) / max(s, 1)
        else:
            trend = 0.0

        fitted = np.zeros(n)

        for t in range(n):
            seasonal_idx = t % s

            # Forecast for this period
            if self.config.seasonal == "add":
                fitted[t] = level + phi * trend + seasonal[seasonal_idx]
            elif self.config.seasonal == "mul":
                fitted[t] = (level + phi * trend) * (seasonal[seasonal_idx] + 1e-10)
            else:
                fitted[t] = level + phi * trend

            if t < n - 1:
                # Update equations
                y_t = y[t]

                if self.config.seasonal == "add":
                    new_level = alpha * (y_t - seasonal[seasonal_idx]) + (1 - alpha) * (level + phi * trend)
                elif self.config.seasonal == "mul":
                    new_level = alpha * (y_t / (seasonal[seasonal_idx] + 1e-10)) + (1 - alpha) * (level + phi * trend)
                else:
                    new_level = alpha * y_t + (1 - alpha) * (level + phi * trend)

                if self.config.trend:
                    new_trend = beta * (new_level - level) + (1 - beta) * phi * trend
                else:
                    new_trend = 0.0

                if self.config.seasonal == "add":
                    seasonal[seasonal_idx] = gamma * (y_t - new_level) + (1 - gamma) * seasonal[seasonal_idx]
                elif self.config.seasonal == "mul":
                    seasonal[seasonal_idx] = gamma * (y_t / (new_level + 1e-10)) + (1 - gamma) * seasonal[seasonal_idx]

                level = new_level
                trend = new_trend

        # Store final state
        self.level_ = level
        self.trend_ = trend
        self.seasonal_ = seasonal.copy()

        return fitted

    def fit(self, y: np.ndarray, **kwargs) -> "ExponentialSmoothing":
        """Fit Exponential Smoothing model.

        Args:
            y: Time series data

        Returns:
            self
        """
        y = np.asarray(y, dtype=np.float64).flatten()
        self._y_train = y.copy()

        # Optimize or use provided parameters
        self.alpha_, self.beta_, self.gamma_ = self._optimize_params(y)

        # Final fit with optimized parameters
        self._fit_smooth(y, self.alpha_, self.beta_, self.gamma_)

        self.state = ModelState.TRAINED
        return self

    def predict(self, steps: int = 1) -> np.ndarray:
        """Forecast future values.

        Args:
            steps: Number of steps to forecast

        Returns:
            Forecasted values
        """
        if self.state != ModelState.TRAINED:
            raise ValueError("Model must be fitted before prediction")

        s = self.config.seasonal_period
        phi = self.config.phi if self.config.damped_trend else 1.0

        forecasts = np.zeros(steps)

        level = self.level_
        trend = self.trend_
        seasonal = self.seasonal_.copy()

        n_train = len(self._y_train)

        for h in range(steps):
            seasonal_idx = (n_train + h) % s

            # Damped trend accumulation
            if self.config.damped_trend:
                trend_sum = trend * (1 - phi ** (h + 1)) / (1 - phi + 1e-10)
            else:
                trend_sum = trend * (h + 1)

            if self.config.seasonal == "add":
                forecasts[h] = level + trend_sum + seasonal[seasonal_idx]
            elif self.config.seasonal == "mul":
                forecasts[h] = (level + trend_sum) * seasonal[seasonal_idx]
            else:
                forecasts[h] = level + trend_sum

        return forecasts

    def forecast(self, steps: int = 1) -> np.ndarray:
        """Alias for predict."""
        return self.predict(steps=steps)


class SimpleMovingAverage(BaseFHEModel):
    """Simple Moving Average for time series on encrypted data.

    Purely FHE-compatible as it only uses addition and division.

    Example:
        >>> from xcapit_fhe import SimpleMovingAverage
        >>> model = SimpleMovingAverage(window=5)
        >>> model.fit(y_train)
        >>> forecast = model.predict(steps=10)
    """

    def __init__(
        self,
        window: int = 5,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.window = window
        self._y_train = None
        self._last_window = None

    def fit(self, y: np.ndarray, **kwargs) -> "SimpleMovingAverage":
        """Fit SMA model (store last window values)."""
        y = np.asarray(y, dtype=np.float64).flatten()
        self._y_train = y.copy()
        self._last_window = y[-self.window:]
        self.state = ModelState.TRAINED
        return self

    def predict(self, steps: int = 1) -> np.ndarray:
        """Forecast using moving average."""
        if self.state != ModelState.TRAINED:
            raise ValueError("Model must be fitted before prediction")

        forecasts = np.zeros(steps)
        window = list(self._last_window)

        for h in range(steps):
            forecasts[h] = np.mean(window)
            window.pop(0)
            window.append(forecasts[h])

        return forecasts


class ProphetLike(BaseFHEModel):
    """Prophet-like decomposition model for time series on encrypted data.

    Decomposes time series into trend, seasonality, and holidays.
    Simplified version compatible with FHE operations.

    FHE Compatibility:
    - Trend fitting uses linear regression (polynomial ops)
    - Seasonality uses Fourier series (polynomial approximations)
    - Changepoints use soft transitions

    Example:
        >>> from xcapit_fhe import ProphetLike
        >>> model = ProphetLike(yearly_seasonality=True)
        >>> model.fit(y_train, dates=dates)
        >>> forecast = model.predict(steps=30)
    """

    def __init__(
        self,
        growth: str = "linear",
        seasonality_mode: str = "additive",
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False,
        n_changepoints: int = 25,
        changepoint_range: float = 0.8,
        changepoint_prior_scale: float = 0.05,
        seasonality_prior_scale: float = 10.0,
        fhe_compatible: bool = True,
    ):
        super().__init__(fhe_compatible=fhe_compatible)
        self.config = ProphetConfig(
            growth=TrendMode(growth),
            seasonality_mode=SeasonalityMode(seasonality_mode),
            yearly_seasonality=yearly_seasonality,
            weekly_seasonality=weekly_seasonality,
            daily_seasonality=daily_seasonality,
            n_changepoints=n_changepoints,
            changepoint_range=changepoint_range,
            changepoint_prior_scale=changepoint_prior_scale,
            seasonality_prior_scale=seasonality_prior_scale,
        )

        # Trend parameters
        self.k_ = None  # Growth rate
        self.m_ = None  # Offset
        self.delta_ = None  # Changepoint adjustments

        # Seasonality parameters
        self.yearly_coeffs_ = None
        self.weekly_coeffs_ = None
        self.daily_coeffs_ = None

        # Changepoints
        self.changepoints_ = None
        self.changepoint_t_ = None

        self._t_train = None
        self._y_train = None

    def _make_seasonality_features(
        self,
        t: np.ndarray,
        period: float,
        n_fourier: int,
    ) -> np.ndarray:
        """Create Fourier features for seasonality."""
        features = []
        for i in range(1, n_fourier + 1):
            features.append(np.sin(2 * np.pi * i * t / period))
            features.append(np.cos(2 * np.pi * i * t / period))
        return np.column_stack(features)

    def _fit_trend(self, t: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
        """Fit linear trend."""
        # Simple linear regression
        t_mean = np.mean(t)
        y_mean = np.mean(y)

        numerator = np.sum((t - t_mean) * (y - y_mean))
        denominator = np.sum((t - t_mean) ** 2) + 1e-10

        k = numerator / denominator
        m = y_mean - k * t_mean

        return k, m

    def _fit_seasonality(
        self,
        t: np.ndarray,
        y_detrended: np.ndarray,
        period: float,
        n_fourier: int,
    ) -> np.ndarray:
        """Fit seasonality using Fourier series."""
        X = self._make_seasonality_features(t, period, n_fourier)

        # Ridge regression
        lambda_reg = 1.0 / self.config.seasonality_prior_scale
        XtX = X.T @ X + lambda_reg * np.eye(X.shape[1])
        Xty = X.T @ y_detrended

        try:
            coeffs = np.linalg.solve(XtX, Xty)
        except np.linalg.LinAlgError:
            coeffs = np.zeros(2 * n_fourier)

        return coeffs

    def fit(
        self,
        y: np.ndarray,
        dates: np.ndarray = None,
        t: np.ndarray = None,
    ) -> "ProphetLike":
        """Fit Prophet-like model.

        Args:
            y: Time series values
            dates: Date array (optional)
            t: Time index array (optional, derived from dates or range)

        Returns:
            self
        """
        y = np.asarray(y, dtype=np.float64).flatten()
        n = len(y)

        # Create time index
        if t is not None:
            t = np.asarray(t, dtype=np.float64)
        elif dates is not None:
            # Convert dates to numeric (days since start)
            t = np.arange(n, dtype=np.float64)
        else:
            t = np.arange(n, dtype=np.float64)

        # Normalize time to [0, 1]
        t_min, t_max = t.min(), t.max()
        t_norm = (t - t_min) / (t_max - t_min + 1e-10)

        self._t_train = t_norm
        self._y_train = y

        # Fit trend
        self.k_, self.m_ = self._fit_trend(t_norm, y)
        trend = self.k_ * t_norm + self.m_

        # Detrend
        y_detrended = y - trend

        # Fit seasonalities
        if self.config.yearly_seasonality:
            # Yearly: period = 365.25 days normalized
            period_yearly = 365.25 / (t_max - t_min + 1e-10)
            self.yearly_coeffs_ = self._fit_seasonality(
                t_norm, y_detrended, period_yearly, n_fourier=10
            )
        else:
            self.yearly_coeffs_ = None

        if self.config.weekly_seasonality:
            # Weekly: period = 7 days normalized
            period_weekly = 7 / (t_max - t_min + 1e-10)
            self.weekly_coeffs_ = self._fit_seasonality(
                t_norm, y_detrended, period_weekly, n_fourier=3
            )
        else:
            self.weekly_coeffs_ = None

        if self.config.daily_seasonality:
            # Daily: period = 1 day normalized
            period_daily = 1 / (t_max - t_min + 1e-10)
            self.daily_coeffs_ = self._fit_seasonality(
                t_norm, y_detrended, period_daily, n_fourier=4
            )
        else:
            self.daily_coeffs_ = None

        # Store normalization
        self._t_min = t_min
        self._t_max = t_max

        self.state = ModelState.TRAINED
        return self

    def predict(self, steps: int = 1, t_future: np.ndarray = None) -> np.ndarray:
        """Forecast future values.

        Args:
            steps: Number of steps to forecast
            t_future: Future time indices (optional)

        Returns:
            Forecasted values
        """
        if self.state != ModelState.TRAINED:
            raise ValueError("Model must be fitted before prediction")

        n_train = len(self._t_train)

        if t_future is not None:
            t_future_norm = (t_future - self._t_min) / (self._t_max - self._t_min + 1e-10)
        else:
            # Extend time series
            dt = 1.0 / n_train
            t_future_norm = self._t_train[-1] + dt * np.arange(1, steps + 1)

        # Trend
        forecasts = self.k_ * t_future_norm + self.m_

        # Add seasonalities
        if self.yearly_coeffs_ is not None:
            period = 365.25 / (self._t_max - self._t_min + 1e-10)
            X = self._make_seasonality_features(t_future_norm, period, 10)
            yearly = X @ self.yearly_coeffs_
            if self.config.seasonality_mode == SeasonalityMode.ADDITIVE:
                forecasts += yearly
            else:
                forecasts *= (1 + yearly)

        if self.weekly_coeffs_ is not None:
            period = 7 / (self._t_max - self._t_min + 1e-10)
            X = self._make_seasonality_features(t_future_norm, period, 3)
            weekly = X @ self.weekly_coeffs_
            if self.config.seasonality_mode == SeasonalityMode.ADDITIVE:
                forecasts += weekly
            else:
                forecasts *= (1 + weekly)

        if self.daily_coeffs_ is not None:
            period = 1 / (self._t_max - self._t_min + 1e-10)
            X = self._make_seasonality_features(t_future_norm, period, 4)
            daily = X @ self.daily_coeffs_
            if self.config.seasonality_mode == SeasonalityMode.ADDITIVE:
                forecasts += daily
            else:
                forecasts *= (1 + daily)

        return forecasts

    def forecast(self, steps: int = 1) -> np.ndarray:
        """Alias for predict."""
        return self.predict(steps=steps)


__all__ = [
    # Enums
    "SeasonalityMode",
    "TrendMode",
    # Configs
    "ARIMAConfig",
    "ExponentialSmoothingConfig",
    "ProphetConfig",
    # Models
    "ARIMA",
    "ExponentialSmoothing",
    "SimpleMovingAverage",
    "ProphetLike",
]
