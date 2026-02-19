# Analisis de Seguridad OWASP Top 10 2025 — Xcapit FHE-ML Platform

## Referencia

Basado en **OWASP Top 10:2025** (publicado 2025).

| # | Categoria | Estado |
|---|-----------|--------|
| A01 | Broken Access Control | Mitigado |
| A02 | Security Misconfiguration | Mitigado |
| A03 | Software Supply Chain Failures | Mitigado |
| A04 | Cryptographic Failures | Mitigado |
| A05 | Injection | Mitigado |
| A06 | Insecure Design | Mitigado |
| A07 | Authentication Failures | Mitigado |
| A08 | Software and Data Integrity Failures | Mitigado |
| A09 | Logging and Alerting Failures | Mitigado |
| A10 | Mishandling Exceptional Conditions | Mitigado |

---

## A01: Broken Access Control

**Riesgo**: Usuarios acceden a recursos de otros usuarios/empresas sin autorizacion.

**Controles implementados**:

1. **Multi-tenancy por Company**: Todos los QuerySets filtran por `company=request.user.company`. Ningun endpoint expone datos cross-tenant.
   - `apps/core/permissions.py`: 9 clases de permisos (`IsCompanyMember`, `IsConsortiumMember`, `IsContributor`, etc.)
   - `apps/core/mixins.py`: `CompanyFilterMixin` aplica filtro automatico en `get_queryset()`

2. **Permission classes por ViewSet**: Cada ViewSet declara `permission_classes` explicitas.
   ```python
   permission_classes = [IsAuthenticated, IsCompanyMember]
   ```

3. **Object-level permissions**: `IsConsortiumMember` y `IsContributor` validan pertenencia al consorcio en cada objeto.

4. **Rate limiting**: `django-ratelimit` limita requests por usuario (1000/hora).

5. **Django-axes**: Bloquea IPs despues de 5 intentos fallidos de login.

**HU relacionadas**: HU-08 (JWT Auth), HU-09 (Consortiums), HU-18 (Security Hardening)

**Evidencia**:
- `backend_django/apps/core/permissions.py` — 9 permission classes
- `backend_django/apps/core/mixins.py` — CompanyFilterMixin
- `backend_django/tests/test_coverage_modules.py` — 8 permission class tests
- `backend_django/tests/test_coverage_95.py` — Auth views tests

---

## A02: Security Misconfiguration

**Riesgo**: Headers de seguridad ausentes, DEBUG habilitado en produccion, CORS abierto.

**Controles implementados**:

1. **Security headers** (Django SecurityMiddleware):
   - `SECURE_HSTS_SECONDS = 31536000` (1 anio)
   - `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
   - `SECURE_CONTENT_TYPE_NOSNIFF = True`
   - `SECURE_BROWSER_XSS_FILTER = True`
   - `X_FRAME_OPTIONS = "DENY"`

2. **CORS whitelist**: Solo dominios especificos permitidos via `CORS_ALLOWED_ORIGINS`.

3. **DEBUG = False** en produccion (controlado por `DJANGO_DEBUG` env var).

4. **settings_test.py** separado: Configuracion de test no afecta produccion.

5. **Docker**: Imagen multi-stage sin herramientas de desarrollo.

**HU relacionadas**: HU-08 (Django Config), HU-16 (Docker), HU-18 (Security Hardening)

**Evidencia**:
- `backend_django/config/settings.py` — Security settings
- `backend_django/Dockerfile` — Multi-stage build
- `.github/workflows/ci.yml` — Security scanning jobs

---

## A03: Software Supply Chain Failures

**Riesgo**: Dependencias con vulnerabilidades conocidas, imagenes Docker comprometidas.

**Controles implementados**:

1. **pip-audit**: Escaneo de dependencias Python en CI (GitHub Actions + GitLab CI).
   ```yaml
   - name: Security Audit
     run: pip-audit --strict
   ```

2. **Trivy container scanning**: Escaneo de imagen Docker en CI.
   ```yaml
   - name: Container Security Scan
     uses: aquasecurity/trivy-action@master
   ```

3. **Grype** (GitLab CI): Scanner alternativo para validacion cruzada.

4. **CodeQL**: Analisis estatico de seguridad (GitHub Actions).

5. **Dependabot**: Actualizaciones automaticas de dependencias.

6. **requirements.txt con versiones fijadas**: Todas las dependencias tienen version exacta.

**HU relacionadas**: HU-17 (CI/CD), HU-18 (Security Hardening)

**Evidencia**:
- `.github/workflows/ci.yml` — pip-audit, Trivy, CodeQL jobs
- `.gitlab-ci.yml` — pip-audit, Grype jobs
- `backend_django/requirements.txt` — Versiones fijadas

---

## A04: Cryptographic Failures

**Riesgo**: Cifrado debil, claves expuestas, datos sensibles en texto plano.

**Controles implementados**:

1. **FHE/CKKS** (TenSEAL):
   - Niveles de seguridad: 128, 192, 256 bits (NIST compliant)
   - Datos nunca descifrados en el servidor (arquitectura zero-knowledge)
   - Parametros CKKS validados antes de crear contexto

2. **JWT signing**: Clave separada `JWT_SIGNING_KEY` (no usa `SECRET_KEY`).
   - Access token: 30 minutos
   - Refresh token: 7 dias con rotacion y blacklist

3. **Secrets management**: HashiCorp Vault / OpenBao para API keys blockchain.
   - `apps/blockchain/secrets.py` — VaultSecretManager con retry y circuit breaker

4. **HTTPS enforced**: `SECURE_SSL_REDIRECT = True` en produccion.

**HU relacionadas**: HU-01 (CKKS), HU-08 (JWT), HU-14 (Vault/Secrets)

**Evidencia**:
- `sdk/encryption/ckks_wrapper.py` — Implementacion CKKS
- `backend_django/apps/blockchain/secrets.py` — VaultSecretManager
- `backend_django/config/settings.py` — JWT config
- `tests/test_encryption.py` — Tests de cifrado

---

## A05: Injection

**Riesgo**: SQL injection, command injection, template injection.

**Controles implementados**:

1. **Django ORM exclusivo**: No se usa `raw()` ni SQL directo en ningun punto.
   - Todos los queries via QuerySet API con parametros escapados automaticamente.

2. **DRF Serializers**: Validacion y sanitizacion de input en todas las vistas.
   ```python
   serializer = ExampleSerializer(data=request.data)
   serializer.is_valid(raise_exception=True)
   ```

3. **JSONSchemaValidator**: Validacion de campos JSON con esquemas definidos.
   - `apps/core/validators/json_schemas.py`

4. **No uso de `eval()`, `exec()`, o `subprocess` con input de usuario**.

5. **Template autoescaping**: Django templates escapan HTML por defecto.

**HU relacionadas**: HU-08 (Django Core), HU-10 (Compliance), HU-13 (Data Quality)

**Evidencia**:
- `backend_django/apps/*/views.py` — Todos usan serializers
- `backend_django/apps/core/validators/` — JSON schema validation
- `backend_django/tests/test_coverage_modules.py` — JSONSchemaValidator tests

---

## A06: Insecure Design

**Riesgo**: Arquitectura sin separacion de responsabilidades, sin validacion de negocio.

**Controles implementados**:

1. **Service Layer Pattern**:
   - `BaseService` → `ServiceResult[T]` → separacion de logica de negocio de vistas
   - Cada servicio valida reglas de negocio antes de ejecutar operaciones
   ```python
   class ConsortiumService(BaseService):
       def create(self, data) -> ServiceResult[Consortium]:
           # Validacion de negocio aqui
   ```

2. **RFC 7807 Error Format**: Errores estructurados sin exponer internals.
   ```json
   {"error": {"code": "validation_error", "message": "...", "status": 400}}
   ```

3. **Audit Trail**: Todas las operaciones significativas se registran.
   - `AuditService.log_from_request()` en cada servicio

4. **Multi-tenancy by design**: Aislamiento de datos desde el modelo de datos.

5. **Proposal/Voting governance**: Decisiones de consorcio requieren quorum.

**HU relacionadas**: HU-08 (Service Layer), HU-09 (Governance), HU-10 (Compliance)

**Evidencia**:
- `backend_django/apps/core/services/base.py` — BaseService, ServiceResult
- `backend_django/apps/core/exceptions.py` — RFC 7807 handler
- `backend_django/apps/core/services/audit.py` — AuditService

---

## A07: Authentication Failures

**Riesgo**: Credenciales debiles, sesiones no invalidadas, brute force.

**Controles implementados**:

1. **JWT con rotacion**: Refresh tokens rotan en cada uso y los viejos se blacklistan.
   ```python
   SIMPLE_JWT = {
       "ROTATE_REFRESH_TOKENS": True,
       "BLACKLIST_AFTER_ROTATION": True,
   }
   ```

2. **django-axes**: Bloquea despues de 5 intentos fallidos.
   ```python
   AXES_FAILURE_LIMIT = 5
   AXES_COOLOFF_TIME = timedelta(minutes=30)
   ```

3. **Rate limiting**: 1000 requests/hora por usuario autenticado.

4. **Logout con blacklist**: `POST /api/v2/auth/logout/` invalida el refresh token.

5. **Password validation**: Django password validators activos (min length, common passwords, numeric-only).

**HU relacionadas**: HU-08 (JWT Auth), HU-18 (Security Hardening)

**Evidencia**:
- `backend_django/config/settings.py` — SIMPLE_JWT, AXES config
- `backend_django/apps/core/authentication.py` — Custom JWT auth
- `backend_django/tests/test_coverage_95.py` — Auth view tests

---

## A08: Software and Data Integrity Failures

**Riesgo**: Datos alterados sin deteccion, deployments no verificados.

**Controles implementados**:

1. **Blockchain audit trail**: Operaciones criticas se registran en Arbitrum.
   - `ConsortiumGovernance.sol` — Votaciones inmutables
   - `ModelRegistry.sol` — Versiones de modelos verificables
   - `ComputationVerifier.sol` — Pruebas de computacion

2. **Container scanning**: Trivy y Grype verifican integridad de imagenes Docker.

3. **CI/CD con checks obligatorios**: PRs requieren CI verde para merge.

4. **Contribution verification**: Contribuciones a consorcios requieren prueba verificable.
   - `ContributionProof` model con `verification_status` y `proof_hash`

**HU relacionadas**: HU-03 (Smart Contracts), HU-14 (Blockchain Backend), HU-17 (CI/CD)

**Evidencia**:
- `contracts/ConsortiumGovernance.sol` — Smart contract
- `backend_django/apps/consortiums/models.py` — ContributionProof
- `.github/workflows/ci.yml` — Container scanning

---

## A09: Logging and Alerting Failures

**Riesgo**: Eventos de seguridad no registrados, logs insuficientes para forense.

**Controles implementados**:

1. **Structured JSON logging**: Middleware de logging con correlation ID.
   - `apps/core/logging.py` — `CorrelationIdMiddleware`
   - Cada request tiene un UUID unico para trazabilidad

2. **AuditService**: Registro de todas las operaciones CRUD significativas.
   ```python
   AuditService.log_from_request(request, action="created", resource_type="model", resource_id=id)
   ```

3. **Sentry integration**: Error tracking en produccion (`SENTRY_DSN`).

4. **Django-axes logging**: Intentos de login fallidos registrados.

5. **Health checks**: `/health/` endpoints para monitoreo (liveness + readiness).

**HU relacionadas**: HU-08 (Logging), HU-16 (Health Checks), HU-18 (Security)

**Evidencia**:
- `backend_django/apps/core/logging.py` — CorrelationIdMiddleware
- `backend_django/apps/core/services/audit.py` — AuditService
- `backend_django/apps/core/healthchecks.py` — Health endpoints
- `backend_django/tests/test_coverage_95.py` — Logging middleware tests

---

## A10: Mishandling Exceptional Conditions

**Riesgo**: Excepciones no manejadas exponen stack traces o dejan el sistema en estado inconsistente.

**Controles implementados**:

1. **Custom exception handler**: `custom_exception_handler` en DRF que convierte todas las excepciones a RFC 7807 sin exponer detalles internos.
   ```python
   # apps/core/exceptions.py
   def custom_exception_handler(exc, context):
       # Nunca expone stack trace al cliente
       return Response({"error": {...}}, status=status_code)
   ```

2. **ServiceResult pattern**: Operaciones de servicio retornan `ServiceResult.ok()` o `ServiceResult.fail()` — sin excepciones para flujos de negocio.

3. **Circuit breaker** (blockchain): `apps/blockchain/resilience.py` implementa retry con backoff y circuit breaker para servicios externos.

4. **Celery error handling**: Tasks con retry automatico y dead letter queue.

5. **ResilientCache**: Cache con fallback a operacion sin cache si Redis falla.
   - `apps/core/cache.py` — `ResilientCache` class

**HU relacionadas**: HU-08 (Exception Handler), HU-14 (Resilience), HU-18 (Hardening)

**Evidencia**:
- `backend_django/apps/core/exceptions.py` — custom_exception_handler
- `backend_django/apps/blockchain/resilience.py` — Circuit breaker
- `backend_django/apps/core/cache.py` — ResilientCache
- `backend_django/tests/test_coverage_modules.py` — ResilientCache tests, exception handler tests

---

## Matriz de Cobertura OWASP por HU

| HU | A01 | A02 | A03 | A04 | A05 | A06 | A07 | A08 | A09 | A10 |
|----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| HU-01 | | | | X | | | | | | |
| HU-02 | | | | X | | | | | | |
| HU-03 | | | | | | | | X | | |
| HU-04 | | | | | X | | | | | |
| HU-05 | X | | | | | | | | | |
| HU-06 | X | | | | | X | | | | |
| HU-07 | | | | | | | | | | |
| HU-08 | X | X | | X | X | X | X | | X | X |
| HU-09 | X | | | | | X | | X | X | |
| HU-10 | X | | | | X | X | | | | |
| HU-11 | | | | | X | | | | | |
| HU-12 | X | | | X | | X | | | | |
| HU-13 | | | | | X | X | | | | X |
| HU-14 | | | | X | | | | X | | X |
| HU-15 | | | | X | | | | | | |
| HU-16 | | X | X | | | | | X | X | |
| HU-17 | | X | X | | | | | X | | |
| HU-18 | X | X | X | | | | X | | X | |
| HU-19 | | | | | | | | | | |
| HU-20 | | | | | | | | | | |
