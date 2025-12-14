"""Tests for the monitoring module.

Tests cover:
- StructuredFormatter and ConsoleFormatter
- MetricsCollector (counters, gauges, histograms, timers)
- Decorators (log_call, timed, count_calls)
- Health check functionality
- Thread safety
"""

import json
import logging
import time
import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from sdk.monitoring import (
    StructuredFormatter,
    ConsoleFormatter,
    setup_logging,
    get_logger,
    MetricPoint,
    MetricsCollector,
    get_metrics,
    log_call,
    timed,
    count_calls,
    HealthStatus,
    get_health_status,
    Metrics,
)


# ========== StructuredFormatter Tests ==========

class TestStructuredFormatter:
    """Tests for StructuredFormatter."""

    def test_format_basic_record(self):
        """Test formatting a basic log record."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test_logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data
        assert data["timestamp"].endswith("Z")

    def test_format_with_exception(self):
        """Test formatting a log record with exception info."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "ERROR"
        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_format_with_extra_fields(self):
        """Test formatting a log record with extra fields."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.user_id = "123"
        record.action = "login"

        output = formatter.format(record)
        data = json.loads(output)

        assert "extra" in data
        assert data["extra"]["user_id"] == "123"
        assert data["extra"]["action"] == "login"


# ========== ConsoleFormatter Tests ==========

class TestConsoleFormatter:
    """Tests for ConsoleFormatter."""

    def test_format_basic_record(self):
        """Test formatting a basic log record for console."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "INFO" in output
        assert "Test message" in output
        # Should contain color codes
        assert "\033[" in output

    def test_format_different_levels(self):
        """Test different log levels have different colors."""
        formatter = ConsoleFormatter()
        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
        outputs = []

        for level in levels:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=10,
                msg="Test",
                args=(),
                exc_info=None,
            )
            outputs.append(formatter.format(record))

        # Each level should produce different output (different colors)
        assert len(set(outputs)) == len(outputs)

    def test_format_with_extra_fields(self):
        """Test formatting with extra fields shows them."""
        formatter = ConsoleFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"

        output = formatter.format(record)

        assert "custom_field" in output
        assert "custom_value" in output


# ========== setup_logging Tests ==========

class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_basic_logging(self):
        """Test basic logging setup."""
        logger = setup_logging(level="DEBUG", console=True)

        assert logger.name == "fheml"
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) >= 1

    def test_setup_logging_with_file(self, tmp_path):
        """Test logging setup with file output."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(level="INFO", log_file=log_file, console=False)

        logger.info("Test message")

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_setup_logging_json_format(self, tmp_path):
        """Test logging setup with JSON format."""
        log_file = tmp_path / "test.json"
        logger = setup_logging(level="INFO", log_file=log_file, json_format=True, console=False)

        logger.info("JSON test")

        content = log_file.read_text()
        data = json.loads(content.strip())
        assert data["message"] == "JSON test"


# ========== get_logger Tests ==========

class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_default_logger(self):
        """Test getting default logger."""
        logger = get_logger()
        assert logger.name == "fheml"

    def test_get_named_logger(self):
        """Test getting named logger."""
        logger = get_logger("fheml.api.server")
        assert logger.name == "fheml.api.server"

    def test_logger_hierarchy(self):
        """Test logger hierarchy."""
        parent = get_logger("fheml")
        child = get_logger("fheml.child")

        assert child.parent.name == "fheml"


# ========== MetricPoint Tests ==========

class TestMetricPoint:
    """Tests for MetricPoint dataclass."""

    def test_create_metric_point(self):
        """Test creating a metric point."""
        point = MetricPoint(name="test_metric", value=42.0)

        assert point.name == "test_metric"
        assert point.value == 42.0
        assert isinstance(point.timestamp, datetime)
        assert point.tags == {}

    def test_metric_point_with_tags(self):
        """Test creating a metric point with tags."""
        point = MetricPoint(
            name="test_metric",
            value=100.0,
            tags={"env": "prod", "region": "us-east"}
        )

        assert point.tags["env"] == "prod"
        assert point.tags["region"] == "us-east"


# ========== MetricsCollector Tests ==========

class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_increment_counter(self):
        """Test incrementing a counter."""
        collector = MetricsCollector()

        collector.increment("requests")
        collector.increment("requests")
        collector.increment("requests", value=3)

        assert collector.get_counter("requests") == 5

    def test_counter_with_tags(self):
        """Test counter with tags."""
        collector = MetricsCollector()

        collector.increment("api.requests", tags={"method": "GET"})
        collector.increment("api.requests", tags={"method": "POST"})
        collector.increment("api.requests", tags={"method": "GET"})

        assert collector.get_counter("api.requests", tags={"method": "GET"}) == 2
        assert collector.get_counter("api.requests", tags={"method": "POST"}) == 1

    def test_gauge(self):
        """Test setting a gauge value."""
        collector = MetricsCollector()

        collector.gauge("temperature", 25.5)
        assert collector.get_gauge("temperature") == 25.5

        collector.gauge("temperature", 30.0)
        assert collector.get_gauge("temperature") == 30.0

    def test_gauge_with_tags(self):
        """Test gauge with tags."""
        collector = MetricsCollector()

        collector.gauge("memory", 1024, tags={"host": "server1"})
        collector.gauge("memory", 2048, tags={"host": "server2"})

        assert collector.get_gauge("memory", tags={"host": "server1"}) == 1024
        assert collector.get_gauge("memory", tags={"host": "server2"}) == 2048

    def test_histogram(self):
        """Test recording histogram values."""
        collector = MetricsCollector()

        for value in [10, 20, 30, 40, 50]:
            collector.histogram("latency", value)

        stats = collector.get_histogram_stats("latency")

        assert stats["count"] == 5
        assert stats["sum"] == 150
        assert stats["min"] == 10
        assert stats["max"] == 50
        assert stats["avg"] == 30

    def test_histogram_percentiles(self):
        """Test histogram percentile calculations."""
        collector = MetricsCollector()

        # Add 100 values from 1 to 100
        for i in range(1, 101):
            collector.histogram("response_time", i)

        stats = collector.get_histogram_stats("response_time")

        assert stats["count"] == 100
        # Percentiles are approximate due to integer indexing
        assert 49 <= stats["p50"] <= 51
        assert 94 <= stats["p95"] <= 96
        assert 98 <= stats["p99"] <= 100

    def test_empty_histogram(self):
        """Test getting stats for empty histogram."""
        collector = MetricsCollector()

        stats = collector.get_histogram_stats("nonexistent")

        assert stats == {"count": 0}

    def test_timer_context_manager(self):
        """Test timer context manager."""
        collector = MetricsCollector()

        with collector.timer("operation_time"):
            time.sleep(0.01)  # 10ms

        stats = collector.get_histogram_stats("operation_time")

        assert stats["count"] == 1
        assert stats["min"] >= 10  # At least 10ms

    def test_get_all_metrics(self):
        """Test getting all metrics."""
        collector = MetricsCollector()

        collector.increment("requests", value=5)
        collector.gauge("active_connections", 10)
        collector.histogram("latency", 100)

        metrics = collector.get_all_metrics()

        assert "uptime_seconds" in metrics
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "histograms" in metrics
        assert metrics["counters"]["requests"] == 5
        assert metrics["gauges"]["active_connections"] == 10

    def test_reset(self):
        """Test resetting all metrics."""
        collector = MetricsCollector()

        collector.increment("counter")
        collector.gauge("gauge", 100)
        collector.histogram("histogram", 50)

        collector.reset()

        assert collector.get_counter("counter") == 0
        assert collector.get_gauge("gauge") == 0
        assert collector.get_histogram_stats("histogram") == {"count": 0}

    def test_thread_safety(self):
        """Test thread-safe metric collection."""
        collector = MetricsCollector()
        errors = []

        def increment_many():
            try:
                for _ in range(1000):
                    collector.increment("concurrent_counter")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=increment_many) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert collector.get_counter("concurrent_counter") == 10000

    def test_make_key_without_tags(self):
        """Test key generation without tags."""
        collector = MetricsCollector()
        key = collector._make_key("metric_name")
        assert key == "metric_name"

    def test_make_key_with_tags(self):
        """Test key generation with tags."""
        collector = MetricsCollector()
        key = collector._make_key("metric_name", {"b": "2", "a": "1"})
        # Tags should be sorted
        assert key == "metric_name[a=1,b=2]"


# ========== get_metrics Tests ==========

class TestGetMetrics:
    """Tests for get_metrics singleton."""

    def test_get_metrics_returns_collector(self):
        """Test that get_metrics returns a MetricsCollector."""
        metrics = get_metrics()
        assert isinstance(metrics, MetricsCollector)

    def test_get_metrics_singleton(self):
        """Test that get_metrics returns the same instance."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()
        assert metrics1 is metrics2


# ========== Decorator Tests ==========

class TestLogCallDecorator:
    """Tests for log_call decorator."""

    def test_log_call_logs_function(self):
        """Test that log_call logs function calls."""
        mock_logger = MagicMock()

        @log_call(logger=mock_logger, level="INFO")
        def test_func(x, y):
            return x + y

        result = test_func(1, 2)

        assert result == 3
        assert mock_logger.log.called

    def test_log_call_logs_error(self):
        """Test that log_call logs errors."""
        mock_logger = MagicMock()

        @log_call(logger=mock_logger)
        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_func()

        mock_logger.error.assert_called()


class TestTimedDecorator:
    """Tests for timed decorator."""

    def test_timed_records_time(self):
        """Test that timed decorator records execution time."""
        # Reset metrics
        metrics = get_metrics()
        metrics.reset()

        @timed(metric_name="test_operation")
        def slow_func():
            time.sleep(0.01)
            return "done"

        result = slow_func()

        assert result == "done"
        stats = metrics.get_histogram_stats("test_operation")
        assert stats["count"] == 1
        assert stats["min"] >= 10  # At least 10ms

    def test_timed_default_name(self):
        """Test timed decorator with default metric name."""
        metrics = get_metrics()
        metrics.reset()

        @timed()
        def my_function():
            pass

        my_function()

        all_metrics = metrics.get_all_metrics()
        # Should contain a metric with the function name
        assert any("my_function" in k for k in all_metrics["histograms"].keys())


class TestCountCallsDecorator:
    """Tests for count_calls decorator."""

    def test_count_calls_increments(self):
        """Test that count_calls increments counter."""
        metrics = get_metrics()
        metrics.reset()

        @count_calls(metric_name="my_func_calls")
        def my_func():
            return "result"

        my_func()
        my_func()
        my_func()

        assert metrics.get_counter("my_func_calls") == 3

    def test_count_calls_with_tags(self):
        """Test count_calls with tags."""
        metrics = get_metrics()
        metrics.reset()

        @count_calls(metric_name="api_calls", tags={"endpoint": "/users"})
        def api_handler():
            pass

        api_handler()
        api_handler()

        assert metrics.get_counter("api_calls", tags={"endpoint": "/users"}) == 2


# ========== Health Check Tests ==========

class TestHealthStatus:
    """Tests for HealthStatus dataclass."""

    def test_create_health_status(self):
        """Test creating a HealthStatus."""
        status = HealthStatus(
            status="healthy",
            checks={"db": True, "cache": True},
            metrics={"requests": 100},
            uptime_seconds=3600.0,
        )

        assert status.status == "healthy"
        assert status.checks["db"] is True
        assert status.uptime_seconds == 3600.0


class TestGetHealthStatus:
    """Tests for get_health_status function."""

    def test_get_health_status(self):
        """Test getting health status."""
        status = get_health_status()

        assert isinstance(status, HealthStatus)
        assert status.status in ["healthy", "degraded", "unhealthy"]
        assert "metrics_collecting" in status.checks
        assert status.uptime_seconds >= 0

    def test_health_status_includes_metrics(self):
        """Test that health status includes metrics."""
        # Add some metrics
        metrics = get_metrics()
        metrics.increment("test_health_counter")

        status = get_health_status()

        assert "counters" in status.metrics
        assert "gauges" in status.metrics


# ========== Metrics Constants Tests ==========

class TestMetricsConstants:
    """Tests for Metrics constants class."""

    def test_api_metrics_defined(self):
        """Test that API metrics are defined."""
        assert Metrics.API_REQUESTS == "api.requests"
        assert Metrics.API_LATENCY == "api.latency_ms"
        assert Metrics.API_ERRORS == "api.errors"

    def test_model_metrics_defined(self):
        """Test that model metrics are defined."""
        assert Metrics.MODEL_TRAININGS == "model.trainings"
        assert Metrics.MODEL_PREDICTIONS == "model.predictions"

    def test_encryption_metrics_defined(self):
        """Test that encryption metrics are defined."""
        assert Metrics.ENCRYPTION_OPS == "encryption.operations"
        assert Metrics.ENCRYPTION_TIME == "encryption.time_ms"

    def test_blockchain_metrics_defined(self):
        """Test that blockchain metrics are defined."""
        assert Metrics.BLOCKCHAIN_TXS == "blockchain.transactions"
        assert Metrics.BLOCKCHAIN_TX_TIME == "blockchain.tx_time_ms"


# ========== Integration Tests ==========

class TestMonitoringIntegration:
    """Integration tests for monitoring module."""

    def test_full_monitoring_workflow(self, tmp_path):
        """Test a complete monitoring workflow."""
        # Setup logging
        log_file = tmp_path / "app.log"
        logger = setup_logging(level="DEBUG", log_file=log_file, json_format=True, console=False)

        # Get metrics collector
        metrics = get_metrics()
        metrics.reset()

        # Simulate application activity
        logger.info("Starting application", extra={"version": "1.0.0"})

        # Record some metrics
        for i in range(5):
            with metrics.timer(Metrics.API_LATENCY):
                time.sleep(0.001)
            metrics.increment(Metrics.API_REQUESTS)

        metrics.gauge("active_users", 42)

        # Check health
        health = get_health_status()

        # Assertions
        assert health.status == "healthy"
        assert metrics.get_counter(Metrics.API_REQUESTS) == 5
        assert metrics.get_gauge("active_users") == 42

        stats = metrics.get_histogram_stats(Metrics.API_LATENCY)
        assert stats["count"] == 5

    def test_decorated_function_monitoring(self):
        """Test using decorators together."""
        metrics = get_metrics()
        metrics.reset()
        mock_logger = MagicMock()

        @log_call(logger=mock_logger)
        @timed(metric_name="decorated_op")
        @count_calls(metric_name="decorated_calls")
        def monitored_operation(x):
            time.sleep(0.001)
            return x * 2

        result = monitored_operation(5)

        assert result == 10
        assert metrics.get_counter("decorated_calls") == 1
        assert metrics.get_histogram_stats("decorated_op")["count"] == 1
        mock_logger.log.assert_called()
