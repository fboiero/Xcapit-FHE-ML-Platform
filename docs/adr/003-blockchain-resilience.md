# ADR-003: Blockchain Resilience Patterns

## Status
Accepted

## Date
2026-01-24

## Context

The platform integrates with Arbitrum blockchain for:
- Consortium governance on-chain
- Model registry verification
- Computation proof storage

Blockchain RPC calls are inherently unreliable:
1. **Network latency**: 100-5000ms response times
2. **Transient failures**: Connection resets, timeouts
3. **Rate limiting**: Public RPCs have request limits
4. **Node issues**: RPC providers have downtime

### Impact of Failures
- User operations fail silently
- Inconsistent state between DB and blockchain
- No visibility into failure patterns
- Cascading failures in dependent services

## Decision

Implement **resilience patterns** for all blockchain interactions:

### 1. Circuit Breaker
Prevents cascading failures when RPC is down.

```python
from apps.blockchain.resilience import CircuitBreaker

blockchain_circuit = CircuitBreaker(
    "blockchain_rpc",
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=30,      # Try again after 30s
    success_threshold=2,      # Close after 2 successes
)
```

**States:**
- `CLOSED`: Normal operation
- `OPEN`: Failing fast, reject immediately
- `HALF_OPEN`: Testing recovery

### 2. Retry with Exponential Backoff
Handles transient failures automatically.

```python
from apps.blockchain.resilience import with_retry

@with_retry(
    max_attempts=3,
    backoff_base=1.0,      # Start with 1s delay
    backoff_factor=2.0,    # Double each retry
    backoff_max=60.0,      # Cap at 60s
    retryable_exceptions=(ConnectionError, TimeoutError),
)
def send_transaction(tx):
    return web3.eth.send_raw_transaction(tx)
```

### 3. Timeout Handling
All RPC calls have explicit timeouts.

```python
Web3(Web3.HTTPProvider(
    rpc_url,
    request_kwargs={"timeout": 10},  # 10 second timeout
))
```

## Implementation

### Module Structure
```
apps/blockchain/
├── resilience.py     # CircuitBreaker, retry decorators
├── services.py       # Updated with resilience
└── secrets.py        # Vault integration (unchanged)
```

### Integration Points

```python
class BlockchainService:
    RPC_EXCEPTIONS = (ConnectionError, TimeoutError, OSError)

    @with_retry(max_attempts=3, backoff_base=1.0)
    def _connect(self):
        if self._circuit.is_open:
            raise CircuitBreakerOpen(self._circuit.name)

        try:
            # Connection logic
            self._circuit.record_success()
        except self.RPC_EXCEPTIONS as e:
            self._circuit.record_failure(e)
            raise
```

### Health Check Integration

```python
def _check_blockchain_rpc(self) -> ComponentHealth:
    if blockchain_circuit.is_open:
        return ComponentHealth(
            name="blockchain",
            status=HealthStatus.DEGRADED,
            message="Circuit breaker open",
        )
    # Normal health check...
```

## Consequences

### Positive
- **Graceful degradation**: App works when blockchain is down
- **Automatic recovery**: No manual intervention needed
- **Visibility**: Circuit state visible in health checks
- **User experience**: Fast failures instead of timeouts

### Negative
- **Complexity**: Additional failure modes to understand
- **Eventual consistency**: Operations may be delayed
- **State management**: Circuit breaker state is per-process

### Neutral
- **Dependency**: No external dependencies (pure Python)
- **Performance**: Minimal overhead when healthy

## Configuration

Environment variables for tuning:

```bash
# Circuit breaker thresholds
BLOCKCHAIN_FAILURE_THRESHOLD=5
BLOCKCHAIN_RECOVERY_TIMEOUT=30

# Retry configuration
BLOCKCHAIN_MAX_RETRIES=3
BLOCKCHAIN_RETRY_BACKOFF=1.0
```

## Monitoring

Metrics to track:
- Circuit state transitions
- Retry counts
- Failure reasons
- RPC latency percentiles

```python
logger.warning(
    f"Circuit {self.name}: CLOSED -> OPEN (failures={count})"
)
```

## Redis Fallback Cache

Similar pattern for Redis:

```python
class ResilientCache:
    """Cache with automatic fallback to memory."""

    def get(self, key):
        if not self._circuit.is_open:
            try:
                return self._primary.get(key)
            except Exception:
                pass
        return self._fallback.get(key)
```

## Related Decisions
- ADR-002: Service Layer Pattern (services use resilience)
- ADR-004: Observability Stack (logs circuit events)
