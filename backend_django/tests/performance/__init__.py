"""Performance testing suite for Xcapit FHE-ML Platform.

Uses Locust for load testing critical API endpoints. See locustfile.py.

Run from project root:
    make perf-test              # Headless, default SLO targets
    make perf-test-ui           # Interactive web UI at :8089
    make perf-test-fhe          # FHE-specific load test (lower concurrency, longer duration)
"""
