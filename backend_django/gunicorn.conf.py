"""
Gunicorn configuration for Xcapit FHE-ML Platform.

All settings are configurable via environment variables with sensible defaults.
"""

import os

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
workers = int(os.environ.get("GUNICORN_WORKERS", "4"))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))

# Timeouts
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
graceful_timeout = 10

# Worker recycling to prevent memory leaks
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
capture_output = True
enable_stdio_inheritance = True
