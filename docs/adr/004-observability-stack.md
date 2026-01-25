# ADR-004: Observability Stack

## Status
Accepted

## Date
2026-01-24

## Context

The platform lacked comprehensive observability:

1. **Logging**: Plain text format, no correlation
2. **Tracing**: No distributed tracing across services
3. **Health checks**: Basic django-health-check only
4. **Metrics**: Only Sentry error tracking

### Requirements
- Track requests across service boundaries
- Debug production issues efficiently
- Monitor system health proactively
- Support containerized deployment (stdout logging)

## Decision

Implement a **structured observability stack**:

### 1. Structured JSON Logging

All logs in JSON format for production:

```python
LOGGING = {
    "formatters": {
        "json": {
            "()": "apps.core.logging.CustomJsonFormatter",
            "service_name": "xcapit-fheml",
            "environment": "production",
        },
    },
    ...
}
```

Output format:
```json
{
  "timestamp": "2026-01-24T10:30:00Z",
  "level": "INFO",
  "logger": "apps.api.requests",
  "service": "xcapit-fheml",
  "correlation_id": "abc-123",
  "user_id": "user-456",
  "message": "GET /api/v2/consortiums/ 200 45.2ms",
  "request": {
    "path": "/api/v2/consortiums/",
    "method": "GET"
  }
}
```

### 2. Correlation ID Middleware

Track requests across logs:

```python
MIDDLEWARE = [
    "apps.core.middleware.CorrelationIdMiddleware",  # First
    # ... other middleware
    "apps.core.middleware.RequestLoggingMiddleware", # Last
]
```

Headers supported:
- `X-Correlation-ID` (primary)
- `X-Request-ID` (fallback)
- `X-Trace-ID` (fallback)

### 3. Enhanced Health Checks

Three endpoints for different purposes:

| Endpoint | Purpose | Checks |
|----------|---------|--------|
| `/health/` | Full health | DB, Redis, Blockchain |
| `/health/live/` | Kubernetes liveness | Process alive |
| `/health/ready/` | Kubernetes readiness | DB, Redis |

Response format:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-24T10:30:00Z",
  "version": "2.0.0",
  "components": [
    {"name": "database", "status": "healthy", "latency_ms": 1.5},
    {"name": "redis", "status": "healthy", "latency_ms": 0.8},
    {"name": "blockchain", "status": "degraded", "latency_ms": 2500}
  ]
}
```

### 4. Request Logging

Automatic logging of all API requests:

```
INFO 2026-01-24 10:30:00 GET /api/v2/consortiums/ 200 45.2ms
```

Excluded paths:
- `/health/`
- `/favicon.ico`
- Static files

## Implementation

### Module Structure
```
apps/core/
├── logging.py              # JSON formatter, correlation context
├── healthchecks.py         # Enhanced health checks
└── middleware/
    ├── __init__.py
    ├── correlation.py      # Correlation ID middleware
    └── request_logging.py  # Request logging middleware
```

### Context Variables

Thread-safe correlation tracking:

```python
from contextvars import ContextVar

correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id")

def get_correlation_id() -> str | None:
    return correlation_id_var.get()
```

### Performance Logging

Context manager for timing operations:

```python
from apps.core.logging import PerformanceLogger

with PerformanceLogger("blockchain_tx", logger) as perf:
    result = send_transaction(tx)
    perf.add_metadata(tx_hash=result.hash)

# Logs: "Operation completed: blockchain_tx" with duration_ms
```

## Consequences

### Positive
- **Debuggability**: Trace requests through entire flow
- **Alerting**: JSON logs integrate with log aggregators
- **Kubernetes ready**: Health endpoints follow k8s patterns
- **Performance visibility**: Request timing in logs

### Negative
- **Log volume**: JSON logs are larger than plain text
- **Dependency**: Adds `python-json-logger` package
- **Learning curve**: Team must use correlation IDs

### Neutral
- **Backward compatible**: Existing logging still works
- **Optional**: JSON logging only in production

## Configuration

```bash
# Force JSON logging in development
LOG_FORMAT=json

# Sentry tuning
SENTRY_TRACES_SAMPLE_RATE=0.25
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

## Future Enhancements

1. **OpenTelemetry integration**: Full distributed tracing
2. **Prometheus metrics**: Custom application metrics
3. **Log correlation with Sentry**: Link errors to request traces

## Related Decisions
- ADR-003: Blockchain Resilience (logs circuit events)
- ADR-002: Service Layer (services log operations)
