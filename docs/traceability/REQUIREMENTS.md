# Requisitos del Sistema — Xcapit FHE-ML Platform

## Requisitos Funcionales

| ID | Requisito | HU | Prioridad |
|----|-----------|-------|-----------|
| RF-01 | El sistema debe permitir cifrar datos usando el esquema CKKS (TenSEAL) con niveles de seguridad de 128, 192 y 256 bits | HU-01 | Alta |
| RF-02 | El sistema debe soportar 4 modelos ML sobre datos cifrados: LinearRegression, LogisticRegression, DecisionTree, KMeans | HU-02 | Alta |
| RF-03 | El sistema debe registrar operaciones en blockchain Arbitrum mediante smart contracts (ConsortiumGovernance, ModelRegistry, ComputationVerifier) | HU-03 | Alta |
| RF-04 | El SDK debe proveer una CLI y una API REST para interactuar con la plataforma programáticamente | HU-04 | Media |
| RF-05 | El sistema debe proveer un dashboard web (React) con autenticación, gestión de consorcios y vistas de demostración | HU-05 | Alta |
| RF-06 | El dashboard debe incluir páginas de governance, compliance, data quality, marketplace, explainability, ensemble, federated inference y API playground | HU-06 | Media |
| RF-07 | El sistema debe proveer landing pages específicas por vertical (Fintech, Healthcare, Government, Others) con i18n (ES/EN/DE) | HU-07 | Media |
| RF-08 | El backend debe usar Django 5.2 LTS con autenticación JWT (access 30min, refresh 7d, rotation + blacklist) y service layer pattern | HU-08 | Alta |
| RF-09 | El sistema debe gestionar consorcios: creación, membresía, contribuciones cifradas, invitaciones, y governance con proposals/voting | HU-09 | Alta |
| RF-10 | El sistema debe proveer compliance regulatorio, marketplace de modelos, y sandbox de testing | HU-10 | Media |
| RF-11 | El SDK debe tener tests completos para todas las rutas API del legacy FastAPI (~620 tests) | HU-11 | Media |
| RF-12 | El sistema debe soportar federated learning con inference endpoints, y gestión de modelos ML (versioning, export, batch prediction, sharing) | HU-12 | Alta |
| RF-13 | El sistema debe evaluar calidad de datos (scoring, reglas, alertas), explicabilidad (SHAP), ensemble methods, y competitive insights | HU-13 | Media |
| RF-14 | Los servicios blockchain del backend deben usar Vault/OpenBao para gestión de secrets y tener resiliencia (retry, circuit breaker) | HU-14 | Alta |
| RF-15 | El SDK debe soportar modelos ML avanzados: Neural Network, Random Forest, Gradient Boosting, SVM, Time Series, PCA, Anomaly Detection | HU-15 | Media |
| RF-16 | El sistema debe estar containerizado con Docker (multi-stage build) y orquestado con docker-compose (postgres, redis, django, celery, openbao) | HU-16 | Alta |
| RF-17 | El sistema debe tener pipelines CI/CD en GitHub Actions (10 jobs) y GitLab CI (9 jobs) con linting, testing, security scanning y container scanning | HU-17 | Alta |
| RF-18 | El sistema debe implementar security hardening: HSTS, CORS whitelist, django-axes (brute-force), rate limiting, y corregir bugs de seguridad | HU-18 | Alta |
| RF-19 | La suite de tests Django debe alcanzar 95%+ de coverage con 1,442+ tests y threshold CI de 90% | HU-19 | Alta |
| RF-20 | El sistema debe tener tests E2E para flujos completos y documentación técnica exhaustiva | HU-20 | Media |

## Requisitos No Funcionales

| ID | Requisito | Categoría | Métrica |
|----|-----------|-----------|---------|
| RNF-01 | El cifrado FHE debe cumplir con niveles de seguridad NIST (128/192/256 bits) | Seguridad | Nivel de bits configurable |
| RNF-02 | El API debe responder en <500ms para operaciones CRUD estándar | Performance | p95 latency |
| RNF-03 | El sistema debe soportar 1,000 requests/hora por usuario autenticado | Escalabilidad | Rate limiting |
| RNF-04 | La cobertura de tests debe ser >=90% (enforced en CI) | Calidad | pytest-cov |
| RNF-05 | Los datos nunca deben ser descifrados en el servidor | Privacidad | Arquitectura FHE |
| RNF-06 | El sistema debe cumplir con GDPR, HIPAA, SOC2 (compliance framework) | Regulatorio | Compliance checks |
| RNF-07 | El build Docker debe completarse en <5 minutos | DevOps | Build time |
| RNF-08 | El sistema debe tener alta disponibilidad con health checks (liveness + readiness) | Disponibilidad | /health/ endpoints |
| RNF-09 | Los errores API deben seguir el formato RFC 7807 sin exponer detalles internos | Seguridad | Error format |
| RNF-10 | Todas las operaciones significativas deben generar audit trail | Auditoría | AuditService logging |
