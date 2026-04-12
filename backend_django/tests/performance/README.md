# Performance Tests

Load tests for the Xcapit FHE-ML Platform backend using [Locust](https://locust.io).

## Quick start

```bash
# 1. Install deps (one time)
cd backend_django && source .venv/bin/activate
pip install -r requirements-perf.txt

# 2. Make sure the stack is running
make dev  # from project root — starts postgres, redis, django, celery

# 3. Seed a perf test user (one time)
make perf-test-seed

# 4. Run the load test
make perf-test          # headless, 3min, 50 users
make perf-test-ui       # interactive web UI at http://localhost:8089
make perf-test-fhe      # FHE stress test: 5 users for 10min
```

## SLO targets

Exit code is non-zero if ANY of these thresholds are breached:

| Endpoint group | p50 | p95 | p99 | Failure rate |
|----------------|-----|-----|-----|--------------|
| Health checks | <20ms | <200ms | <500ms | <0.1% |
| Auth (login/register) | <100ms | <500ms | <1s | <0.5% |
| Standard API | <100ms | <500ms | <1s | <0.5% |
| FHE / MPC operations | <2s | <5s | <10s | <1% |

Thresholds are enforced via the `locust.quitting` event in `locustfile.py`.

## User classes and weights

The test uses three user classes to simulate realistic traffic patterns:

- **AnonymousUser** (weight 3): public traffic — health checks, sandbox email capture, registration attempts
- **AuthenticatedUser** (weight 6): the majority workload — dashboard hits, consortium CRUD, marketplace browse
- **FHEHeavyUser** (weight 1): FHE predictions and MPC aggregation — run separately for stress testing

Ratio chosen based on expected production traffic: 60% authenticated, 30% anonymous, 10% heavy compute.

## Test scenarios

### Scenario 1 — Baseline (dev validation)

```bash
locust -f tests/performance/locustfile.py \
    --host http://localhost:8000 \
    --users 10 --spawn-rate 1 --run-time 1m --headless
```

Validates the endpoints are responding. Good for local dev iteration.

### Scenario 2 — Production-like load (pre-deploy)

```bash
locust -f tests/performance/locustfile.py \
    --host http://staging.xcapit.com \
    --users 200 --spawn-rate 10 --run-time 10m --headless \
    --html perf-report.html
```

Simulates a medium-traffic production day. Run against staging before releases.

### Scenario 3 — FHE stress (release gating)

```bash
locust -f tests/performance/locustfile.py \
    --host http://staging.xcapit.com \
    --users 20 --spawn-rate 2 --run-time 15m --headless \
    FHEHeavyUser \
    --html fhe-stress-report.html
```

Low-concurrency, long-duration stress test for FHE paths. Required for GA.

### Scenario 4 — Soak test

```bash
locust -f tests/performance/locustfile.py \
    --host http://staging.xcapit.com \
    --users 50 --spawn-rate 2 --run-time 2h --headless
```

Detects memory leaks, slow degradation, connection pool exhaustion.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PERF_TEST_EMAIL` | `perf@xcapit.test` | Authenticated user for login flows |
| `PERF_TEST_PASSWORD` | `perf-test-password` | Password for that user |
| `PERF_TEST_COMPANY` | `Xcapit Perf Test` | Company name for creation flows |

## Interpreting results

Locust outputs:
- **Request count**: total requests issued
- **Failures**: `ConnectionError`, HTTP 5xx, custom `response.failure()` calls
- **Median / 95% / 99% response time**: percentile latencies
- **RPS**: requests per second

Watch for:
- **Rising p95 over time** = memory leak or connection leak
- **Cliff in RPS at N users** = connection pool exhausted or DB lock contention
- **5xx spikes correlated with specific endpoints** = endpoint bottleneck to profile

## CI integration

See `.github/workflows/ci.yml` — the `perf-tests` job runs on `main` branch pushes
and on PRs labeled `perf-test`. It expects the dev stack to be up via `make dev-ci`
and enforces the SLO thresholds defined in `locustfile.py`.

## Known gaps (as of 2026-04-12)

- No GPU-accelerated FHE path yet — FHE predictions use CPU TenSEAL and hit
  the 5s p95 threshold under load. Tracked for Ola 3 (v1.2).
- MPC aggregation endpoint is synthetic — does not actually perform secret
  sharing protocol in this test (would require coordinated multi-party setup).
- No JavaScript dashboard rendering in perf tests — use Playwright E2E for
  that (see `dashboard/e2e/`).
