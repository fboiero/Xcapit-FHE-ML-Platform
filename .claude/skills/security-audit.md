# Security Audit Checklist

## Security Middleware Chain (from `config/settings.py`)

1. `CorrelationIdMiddleware` — Request tracing (must be first)
2. `SecurityMiddleware` — HSTS, XSS filter, content type nosniff, SSL redirect
3. `CorsMiddleware` — CORS enforcement (explicit origin whitelist)
4. `WhiteNoiseMiddleware` — Static file serving with security headers
5. `AxesMiddleware` — Brute-force protection (after auth)
6. `RequestLoggingMiddleware` — Structured JSON logging

## Authentication Security

| Control | Configuration |
|---------|--------------|
| JWT access token | 30-minute lifetime |
| JWT refresh token | 7-day lifetime, rotation enabled |
| Token blacklist | On rotation (prevents reuse) |
| Brute-force | django-axes: 5 failures = 30-min lockout |
| Rate limiting | Anon: 100/hr, Auth: 1,000/hr |
| Password hashing | Django default (PBKDF2) |

## CORS Configuration

Explicit origin whitelist — NO wildcard (`*`):
```python
CORS_ALLOWED_ORIGINS = [
    "https://xcapit-privacy.vercel.app",
    "https://appfhe.xcapit.com",
    "https://privacy.xcapit.com",
    "http://localhost:5173",
    "http://localhost:3000",
]
```

## Security Headers

- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Referrer-Policy: same-origin`
- `Content-Security-Policy` configured

## API Key Security

- Keys stored as SHA-256 hash (never plaintext)
- Prefix stored for identification (first 8 chars)
- Permission-based access control (read/write/admin)

## FHE-Specific Security

- Server NEVER sees plaintext data
- Encryption/decryption happens client-side only
- Public key transmitted, secret key never leaves client
- Security levels: 128/192/256-bit configurable

## Secret Management

- **Production**: OpenBao/Vault via `hvac` SDK (`apps/blockchain/secrets.py`)
- **Development**: `.env` file (in `.gitignore`)
- **CI**: GitHub/GitLab secret variables
- Private keys for blockchain NEVER in code

## Monitoring

- Sentry integration: `send_default_pii=False` (no PII in error reports)
- Structured JSON logging with correlation IDs
- Audit trail: `AuditService.log_from_request()` for all operations

## Container Security (CI)

- **Trivy**: Container vulnerability scanning
- **Grype**: Secondary vulnerability scanning
- **pip-audit**: Python dependency audit
- **TruffleHog**: Secret detection in code
- **CodeQL**: Static analysis (SAST)

## Review Checklist

When reviewing security-sensitive code:

- [ ] No PII in logs (email, passwords, tokens)
- [ ] No secrets hardcoded (API keys, passwords, private keys)
- [ ] Queries scoped to `request.user.company` (multi-tenancy)
- [ ] Input validation on all user-facing endpoints
- [ ] Rate limiting on public/sensitive endpoints
- [ ] Error responses don't leak internal details
- [ ] CORS origins explicitly listed (no wildcards)
- [ ] `@transaction.atomic` on multi-step operations
- [ ] No raw SQL (use Django ORM with parameterized queries)
