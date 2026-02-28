# Trazabilidad de Tablero Kanban — Xcapit FHE-ML Platform

> Documento de trazabilidad que vincula cada historia de usuario (HU) con sus transiciones en el tablero Kanban y los commits correspondientes en el repositorio.

## Equipo

| Miembro | Rol | Email |
|---------|-----|-------|
| Franco Schillage (Tipo) | Developer | tipo@xcapit.com |
| Fernando Boiero | Developer | fer@xcapit.com |
| Maria Eugenia Cáceres (Rukia) | QA | euge@xcapit.com |

## Convenciones

- **Por hacer**: La historia fue planificada en el Sprint Planning.
- **En curso**: El desarrollador asignado comienza la implementación (sincronizado con el commit `feat`).
- **En revisión**: La implementación fue completada y se sometió a code review.
- **Pruebas**: QA ejecuta los tests y validaciones (sincronizado con el commit `test`).
- **Listo**: Los tests pasan y la historia se da por terminada.

---

## Sprint 1: Foundation (1–14 Dic 2025)

### HU-01 — Core FHE Encryption (CKKS)

**Como** data scientist, **quiero** encriptar datos con el esquema CKKS a 128/192/256-bit de seguridad, **para** garantizar la privacidad criptográfica de los datos antes de procesarlos con modelos de ML.

**Responsable**: Franco Schillage (Tipo) | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- Se puede crear un contexto CKKS con nivel de seguridad 128, 192 o 256 bits
- Los datos numéricos se encriptan y desencriptan correctamente con error menor a 1e-5
- El context manager gestiona correctamente el ciclo de vida de las claves
- Las operaciones de suma y multiplicación sobre datos encriptados producen resultados correctos
- Se generan claves serializables para transporte entre cliente y servidor

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2025-12-01 09:00 | Sprint Planning (equipo) |
| En curso | 2025-12-03 10:17 | Franco Schillage |
| En revisión | 2025-12-03 16:30 | Franco Schillage |
| Pruebas | 2025-12-04 14:23 | Maria Eugenia Cáceres |
| Listo | 2025-12-04 17:45 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-01)` — 2025-12-03 10:17:43 — Franco Schillage
- `test(HU-01)` — 2025-12-04 14:23:18 — Maria Eugenia Cáceres

---

### HU-02 — FHE ML Models (4 algoritmos)

**Como** data scientist, **quiero** entrenar y predecir con 4 modelos de ML sobre datos encriptados (Linear Regression, Logistic Regression, Decision Tree, KMeans), **para** obtener resultados analíticos sin exponer los datos originales.

**Responsable**: Fernando Boiero | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- LinearRegression entrena y predice sobre vectores encriptados con precisión aceptable
- LogisticRegression utiliza aproximación polinomial de sigmoid para operar sobre datos encriptados
- DecisionTree implementa evaluación de nodos compatible con FHE
- KMeans realiza clustering sobre datos encriptados con convergencia verificable
- Todos los modelos heredan de una clase base común con interfaz fit/predict
- Los resultados encriptados se desencriptan correctamente en el cliente

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2025-12-01 09:00 | Sprint Planning (equipo) |
| En curso | 2025-12-05 09:42 | Fernando Boiero |
| En revisión | 2025-12-05 17:15 | Fernando Boiero |
| Pruebas | 2025-12-08 10:08 | Maria Eugenia Cáceres |
| Listo | 2025-12-08 14:30 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-02)` — 2025-12-05 09:42:11 — Fernando Boiero
- `test(HU-02)` — 2025-12-08 10:08:34 — Maria Eugenia Cáceres

---

### HU-03 — Blockchain & Smart Contracts

**Como** platform admin, **quiero** registrar audit trails en la blockchain de Arbitrum mediante smart contracts, **para** garantizar la trazabilidad e integridad de las operaciones de la plataforma.

**Responsable**: Franco Schillage (Tipo) | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- ConsortiumGovernance.sol permite crear y votar propuestas de gobernanza
- ModelRegistry.sol registra versiones de modelos con hashes de verificación
- ComputationVerifier.sol verifica pruebas de computación
- El conector blockchain (Web3.py) se conecta a Arbitrum y ejecuta transacciones
- Los contratos se despliegan con Foundry y pasan todas las pruebas on-chain

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2025-12-01 09:00 | Sprint Planning (equipo) |
| En curso | 2025-12-09 09:51 | Franco Schillage |
| En revisión | 2025-12-09 17:40 | Franco Schillage |
| Pruebas | 2025-12-10 11:34 | Maria Eugenia Cáceres |
| Listo | 2025-12-10 15:20 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-03)` — 2025-12-09 09:51:27 — Franco Schillage
- `test(HU-03)` — 2025-12-10 11:34:52 — Maria Eugenia Cáceres

---

### HU-04 — SDK CLI & API Layer

**Como** developer, **quiero** una herramienta CLI y una capa REST API para interactuar con el SDK, **para** integrar las capacidades FHE en flujos de trabajo existentes sin escribir código Python.

**Responsable**: Fernando Boiero | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- El CLI ofrece comandos para encriptación, entrenamiento y predicción
- El módulo de monitoring expone métricas de uso y rendimiento
- Los quality calculators evalúan la calidad de los datos de entrada
- Las utilidades del SDK manejan serialización y configuración
- El benchmarking mide tiempos de encriptación y predicción por modelo

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2025-12-01 09:00 | Sprint Planning (equipo) |
| En curso | 2025-12-11 10:26 | Fernando Boiero |
| En revisión | 2025-12-11 18:05 | Fernando Boiero |
| Pruebas | 2025-12-12 14:47 | Maria Eugenia Cáceres |
| Listo | 2025-12-12 17:30 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-04)` — 2025-12-11 10:26:09 — Fernando Boiero
- `test(HU-04)` — 2025-12-12 14:47:33 — Maria Eugenia Cáceres

---

## Sprint 2: Platform (15–28 Dic 2025)

### HU-05 — React Dashboard Core

**Como** end user, **quiero** un dashboard web con autenticación, gestión de consorcios y demos interactivas, **para** operar la plataforma FHE desde una interfaz gráfica accesible.

**Responsable**: Franco Schillage (Tipo) | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- Login y registro funcionan con JWT tokens
- El dashboard muestra métricas principales del usuario y su organización
- La gestión de consorcios permite crear, ver y administrar consorcios
- Las demos interactivas muestran el flujo encrypt-train-predict en tiempo real
- La navegación es responsive y funciona en desktop y mobile

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2025-12-15 09:00 | Sprint Planning (equipo) |
| En curso | 2025-12-15 09:14 | Franco Schillage |
| En revisión | 2025-12-15 18:20 | Franco Schillage |
| Pruebas | 2025-12-16 15:38 | Maria Eugenia Cáceres |
| Listo | 2025-12-16 18:10 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-05)` — 2025-12-15 09:14:26 — Franco Schillage
- `test(HU-05)` — 2025-12-16 15:38:51 — Maria Eugenia Cáceres

---

### HU-06 — Dashboard Feature Pages

**Como** compliance officer, **quiero** páginas de gobernanza, compliance, calidad de datos y más en el dashboard, **para** monitorear y gestionar todos los aspectos regulatorios y operativos de la plataforma.

**Responsable**: Fernando Boiero | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- La página de Governance muestra propuestas activas y permite votar
- La página de Compliance muestra el estado de cumplimiento regulatorio
- La página de Data Quality muestra scores y recomendaciones de mejora
- Competitive Insights, Model Explainability, Marketplace, Data Explorer, Model Deployment, Audit Log Viewer, API Playground, y Model Metrics implementados
- 15+ páginas funcionales en total

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2025-12-15 09:00 | Sprint Planning (equipo) |
| En curso | 2025-12-17 10:05 | Fernando Boiero |
| En revisión | 2025-12-17 18:30 | Fernando Boiero |
| Pruebas | 2025-12-18 11:52 | Maria Eugenia Cáceres |
| Listo | 2025-12-18 16:15 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-06)` — 2025-12-17 10:05:42 — Fernando Boiero
- `test(HU-06)` — 2025-12-18 11:52:17 — Maria Eugenia Cáceres

---

### HU-07 — Landing Pages (Verticals)

**Como** marketing stakeholder, **quiero** landing pages por vertical de industria con soporte i18n (ES/EN/DE), **para** comunicar la propuesta de valor de la plataforma a cada segmento de mercado.

**Responsable**: Franco Schillage (Tipo) | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- Landing Hub, Fintech, Healthcare, Gobierno y Otros implementados
- Todas las páginas soportan ES, EN y DE con react-i18next
- Las animaciones SVG del hero section funcionan correctamente
- El formulario de contacto envía datos vía Web3Forms API
- Cada landing sigue la estructura: Hero, Stats, How It Works, Use Cases, Compliance, Contact

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2025-12-15 09:00 | Sprint Planning (equipo) |
| En curso | 2025-12-22 09:33 | Franco Schillage |
| En revisión | 2025-12-22 17:45 | Franco Schillage |
| Pruebas | 2025-12-23 10:41 | Maria Eugenia Cáceres |
| Listo | 2025-12-23 14:50 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-07)` — 2025-12-22 09:33:08 — Franco Schillage
- `test(HU-07)` — 2025-12-23 10:41:55 — Maria Eugenia Cáceres

---

## Sprint 3: Backend Migration (29 Dic 2025 – 11 Ene 2026)

### HU-08 — Django Core & Auth (JWT)

**Como** backend developer, **quiero** migrar el backend a Django 5.2 LTS con autenticación JWT y service layer, **para** tener una base sólida, mantenible y segura para la API de la plataforma.

**Responsable**: Fernando Boiero | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- Django 5.2 LTS configurado con settings de producción y test
- Autenticación JWT con access/refresh tokens y blacklist
- Modelos core: User, Company, APIKey, AuditLog creados y migrados
- Service layer base (BaseService, ServiceResult) implementado
- Exception handler devuelve errores en formato RFC 7807

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2025-12-29 09:00 | Sprint Planning (equipo) |
| En curso | 2025-12-29 09:22 | Fernando Boiero |
| En revisión | 2025-12-29 18:10 | Fernando Boiero |
| Pruebas | 2025-12-30 14:16 | Maria Eugenia Cáceres |
| Listo | 2025-12-30 17:40 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-08)` — 2025-12-29 09:22:47 — Fernando Boiero
- `test(HU-08)` — 2025-12-30 14:16:03 — Maria Eugenia Cáceres

---

### HU-09 — Consortiums & Governance

**Como** consortium admin, **quiero** APIs para gestionar consorcios, miembros, contribuciones y propuestas de gobernanza, **para** coordinar el aprendizaje colaborativo entre múltiples organizaciones.

**Responsable**: Franco Schillage (Tipo) | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- CRUD completo de consorcios con filtros y paginación
- Gestión de miembros: invitación, aceptación, rechazo, expulsión
- Registro y verificación de contribuciones (ContributionProof)
- Propuestas de gobernanza con flujo de votación
- Service layer (ConsortiumService, MemberService, InvitationService, ContributionService)

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2025-12-29 09:00 | Sprint Planning (equipo) |
| En curso | 2026-01-02 10:43 | Franco Schillage |
| En revisión | 2026-01-02 18:25 | Franco Schillage |
| Pruebas | 2026-01-03 11:27 | Maria Eugenia Cáceres |
| Listo | 2026-01-03 15:50 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-09)` — 2026-01-02 10:43:29 — Franco Schillage
- `test(HU-09)` — 2026-01-03 11:27:14 — Maria Eugenia Cáceres

---

### HU-10 — Compliance, Marketplace, Sandbox

**Como** organización regulada, **quiero** APIs de compliance checking, marketplace de modelos y sandbox de pruebas, **para** cumplir requisitos regulatorios, compartir modelos y probar en ambientes seguros.

**Responsable**: Fernando Boiero | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- Compliance app verifica cumplimiento de regulaciones (GDPR, HIPAA, SOX, etc.)
- Marketplace permite listar, buscar y compartir modelos entre organizaciones
- Sandbox proporciona ambientes aislados para pruebas sin afectar producción
- Las APIs siguen los estándares REST de la plataforma

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2025-12-29 09:00 | Sprint Planning (equipo) |
| En curso | 2026-01-05 09:18 | Fernando Boiero |
| En revisión | 2026-01-05 17:55 | Fernando Boiero |
| Pruebas | 2026-01-06 15:42 | Maria Eugenia Cáceres |
| Listo | 2026-01-06 18:20 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-10)` — 2026-01-05 09:18:36 — Fernando Boiero
- `test(HU-10)` — 2026-01-06 15:42:58 — Maria Eugenia Cáceres

---

### HU-11 — SDK Route Tests (Legacy)

**Como** QA engineer, **quiero** tests comprehensivos para todas las rutas del SDK API, **para** asegurar la calidad y estabilidad de la capa de API antes de deprecarla.

**Responsable**: Franco Schillage (Tipo) | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- Todas las rutas del SDK API tienen tests unitarios
- Los tests cubren casos de éxito, error y edge cases
- El linting con ruff pasa sin errores
- Se alcanzan ~620 tests en el SDK

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2025-12-29 09:00 | Sprint Planning (equipo) |
| En curso | 2026-01-07 10:11 | Franco Schillage |
| En revisión | 2026-01-07 18:35 | Franco Schillage |
| Pruebas | 2026-01-08 14:35 | Maria Eugenia Cáceres |
| Listo | 2026-01-08 17:55 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-11)` — 2026-01-07 10:11:23 — Franco Schillage
- `test(HU-11)` — 2026-01-08 14:35:47 — Maria Eugenia Cáceres

---

## Sprint 4: Advanced Features (12–25 Ene 2026)

### HU-12 — Federated Learning & ML Models

**Como** data scientist, **quiero** APIs de federated learning y gestión de modelos ML, **para** entrenar modelos distribuidos entre múltiples nodos sin compartir datos.

**Responsable**: Fernando Boiero | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- CRUD completo de modelos ML con versionado
- Federated learning endpoints: crear sesión, unir nodos, agregar actualizaciones
- Inference endpoints para predicción en tiempo real
- Rate limiting, webhooks, batch prediction y model sharing

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2026-01-12 09:00 | Sprint Planning (equipo) |
| En curso | 2026-01-12 09:07 | Fernando Boiero |
| En revisión | 2026-01-12 18:40 | Fernando Boiero |
| Pruebas | 2026-01-13 11:49 | Maria Eugenia Cáceres |
| Listo | 2026-01-13 16:25 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-12)` — 2026-01-12 09:07:52 — Fernando Boiero
- `test(HU-12)` — 2026-01-13 11:49:06 — Maria Eugenia Cáceres

---

### HU-13 — Data Quality, Explainability, Ensemble

**Como** ML engineer, **quiero** APIs de data quality scoring, explicabilidad SHAP y métodos de ensemble, **para** evaluar la calidad de los datos, entender las predicciones y combinar múltiples modelos.

**Responsable**: Franco Schillage (Tipo) | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- Data Quality evalúa completeness, consistency, accuracy y timeliness
- Quality rules configurables con condiciones y umbrales
- Explainability genera explicaciones SHAP para predicciones
- Ensemble permite combinar múltiples modelos con diferentes estrategias
- Competitive Insights ofrece benchmarks de industria

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2026-01-12 09:00 | Sprint Planning (equipo) |
| En curso | 2026-01-14 10:22 | Franco Schillage |
| En revisión | 2026-01-14 18:15 | Franco Schillage |
| Pruebas | 2026-01-15 14:53 | Maria Eugenia Cáceres |
| Listo | 2026-01-15 18:10 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-13)` — 2026-01-14 10:22:38 — Franco Schillage
- `test(HU-13)` — 2026-01-15 14:53:21 — Maria Eugenia Cáceres

---

### HU-14 — Blockchain Backend & Secrets

**Como** security engineer, **quiero** servicios blockchain en el backend Django con gestión de secretos vía Vault/OpenBao y conexiones resilientes, **para** asegurar la integridad de las transacciones y proteger las claves privadas.

**Responsable**: Fernando Boiero | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- BlockchainService se conecta a Arbitrum y ejecuta transacciones
- ModelRegistryService registra modelos en el smart contract
- Secrets management vía OpenBao/Vault almacena claves privadas de forma segura
- Resilience patterns: circuit breaker, retry con backoff exponencial, fallback
- Las claves privadas nunca se exponen en logs ni respuestas API

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2026-01-12 09:00 | Sprint Planning (equipo) |
| En curso | 2026-01-19 09:36 | Fernando Boiero |
| En revisión | 2026-01-19 18:05 | Fernando Boiero |
| Pruebas | 2026-01-20 15:12 | Maria Eugenia Cáceres |
| Listo | 2026-01-20 18:30 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-14)` — 2026-01-19 09:36:14 — Fernando Boiero
- `test(HU-14)` — 2026-01-20 15:12:47 — Maria Eugenia Cáceres

---

### HU-15 — SDK Advanced Models (NN, RF, GBM, SVM, TimeSeries, PCA)

**Como** data scientist, **quiero** modelos avanzados de ML compatibles con FHE, **para** aplicar técnicas sofisticadas de ML sobre datos encriptados.

**Responsable**: Franco Schillage (Tipo) | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- Neural Network implementa forward pass con activaciones polinomiales
- Random Forest combina múltiples árboles de decisión FHE
- Gradient Boosting implementa boosting secuencial compatible con FHE
- SVM utiliza kernel polinomial, TimeSeries con ventanas deslizantes, PCA reduce dimensionalidad
- Pipeline de preprocessing normaliza y transforma datos antes de encriptar

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2026-01-12 09:00 | Sprint Planning (equipo) |
| En curso | 2026-01-21 10:31 | Franco Schillage |
| En revisión | 2026-01-21 18:20 | Franco Schillage |
| Pruebas | 2026-01-22 14:18 | Maria Eugenia Cáceres |
| Listo | 2026-01-22 17:45 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-15)` — 2026-01-21 10:31:55 — Franco Schillage
- `test(HU-15)` — 2026-01-22 14:18:39 — Maria Eugenia Cáceres

---

## Sprint 5: Hardening (26 Ene – 8 Feb 2026)

### HU-16 — Docker & Deployment

**Como** DevOps engineer, **quiero** contenedores Docker y orquestación con docker-compose, **para** desplegar la plataforma de forma reproducible y escalable en cualquier ambiente.

**Responsable**: Fernando Boiero | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- Dockerfile multi-stage produce imagen de ~654MB con Python 3.12
- docker-compose.yml orquesta backend, PostgreSQL y Redis
- Health checks configurados para todos los servicios
- Gunicorn configurado como servidor WSGI de producción
- Build completo en ~3 minutos

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2026-01-26 09:00 | Sprint Planning (equipo) |
| En curso | 2026-01-26 09:45 | Fernando Boiero |
| En revisión | 2026-01-26 17:30 | Fernando Boiero |
| Pruebas | 2026-01-27 10:08 | Maria Eugenia Cáceres |
| Listo | 2026-01-27 14:55 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-16)` — 2026-01-26 09:45:12 — Fernando Boiero
- `test(HU-16)` — 2026-01-27 10:08:47 — Maria Eugenia Cáceres

---

### HU-17 — CI/CD Pipelines (GitHub Actions + GitLab CI)

**Como** DevOps engineer, **quiero** pipelines CI/CD en GitHub Actions y GitLab CI, **para** automatizar tests, linting, security scanning y deployment en cada push.

**Responsable**: Franco Schillage (Tipo) | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- GitHub Actions pipeline verde con 10/10 jobs
- GitLab CI pipeline verde con 9/9 jobs
- Coverage threshold configurado en 90%
- CodeQL v4 para análisis de seguridad estático
- Pre-commit hooks configurados
- 341 errores de ruff corregidos

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2026-01-26 09:00 | Sprint Planning (equipo) |
| En curso | 2026-01-28 10:24 | Franco Schillage |
| En revisión | 2026-01-28 18:40 | Franco Schillage |
| Pruebas | 2026-01-29 14:37 | Maria Eugenia Cáceres |
| Listo | 2026-01-29 17:50 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-17)` — 2026-01-28 10:24:31 — Franco Schillage
- `test(HU-17)` — 2026-01-29 14:37:05 — Maria Eugenia Cáceres

---

### HU-18 — Security Hardening

**Como** security engineer, **quiero** security headers, protección contra brute-force, CORS correctamente configurado y bugs de seguridad corregidos, **para** proteger la plataforma contra las vulnerabilidades más comunes.

**Responsable**: Fernando Boiero | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- Security headers configurados: HSTS, X-Content-Type-Options, X-Frame-Options, CSP
- django-axes protege contra brute-force en login
- django-ratelimit limita requests por IP y por usuario
- CORS configurado con whitelist de orígenes permitidos
- Bugs de autenticación corregidos

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2026-01-26 09:00 | Sprint Planning (equipo) |
| En curso | 2026-02-03 09:28 | Fernando Boiero |
| En revisión | 2026-02-03 17:50 | Fernando Boiero |
| Pruebas | 2026-02-04 11:15 | Maria Eugenia Cáceres |
| Listo | 2026-02-04 15:40 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-18)` — 2026-02-03 09:28:43 — Fernando Boiero
- `test(HU-18)` — 2026-02-04 11:15:29 — Maria Eugenia Cáceres

---

## Sprint 6: Quality & Documentation (9–23 Feb 2026)

### HU-19 — Test Coverage 95%+

**Como** QA lead, **quiero** alcanzar 95%+ de coverage en los tests de Django, **para** asegurar la calidad y confiabilidad de todo el backend de la plataforma.

**Responsable**: Franco Schillage (Tipo) / Maria Eugenia Cáceres | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- Coverage total de Django alcanza 95.12%
- 1,442+ tests pasando en total
- Módulos críticos superan 90% de coverage individual
- Fixtures y conftest.py proporcionan infraestructura de test reutilizable

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2026-02-09 09:00 | Sprint Planning (equipo) |
| En curso | 2026-02-10 09:53 | Maria Eugenia Cáceres |
| En revisión | 2026-02-10 18:30 | Maria Eugenia Cáceres |
| Pruebas | 2026-02-11 10:41 | Maria Eugenia Cáceres |
| Listo | 2026-02-11 15:20 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-19)` — 2026-02-10 09:53:16 — Maria Eugenia Cáceres
- `test(HU-19)` — 2026-02-11 10:41:08 — Maria Eugenia Cáceres

---

### HU-20 — E2E Tests & Documentation

**Como** product owner, **quiero** tests end-to-end de flujos completos y documentación comprehensiva, **para** validar que la plataforma funciona correctamente de extremo a extremo y facilitar el onboarding de nuevos desarrolladores.

**Responsable**: Fernando Boiero | **QA**: Maria Eugenia Cáceres

**Criterios de aceptación:**
- E2E test: ML model lifecycle (create -> train -> predict -> export)
- E2E test: Model sharing & marketplace
- E2E test: Federated learning
- E2E test: Data quality -> consortium -> training
- E2E test: Governance proposal -> vote -> execute
- CLAUDE.md, README.md y CHANGELOG.md actualizados
- Skills de Claude Code configurados en .claude/skills/

| Estado | Fecha | Responsable del movimiento |
|--------|-------|---------------------------|
| Por hacer | 2026-02-09 09:00 | Sprint Planning (equipo) |
| En curso | 2026-02-19 09:12 | Fernando Boiero |
| En revisión | 2026-02-19 17:45 | Fernando Boiero |
| Pruebas | 2026-02-20 14:46 | Maria Eugenia Cáceres |
| Listo | 2026-02-20 17:30 | Maria Eugenia Cáceres |

**Commits vinculados:**
- `feat(HU-20)` — 2026-02-19 09:12:34 — Fernando Boiero
- `test(HU-20)` — 2026-02-20 14:46:22 — Maria Eugenia Cáceres

---

## Resumen de Velocidad por Sprint

| Sprint | Período | HU Completadas | Tests Agregados | Días Laborables |
|--------|---------|----------------|-----------------|-----------------|
| 1 | 1-14 Dic 2025 | HU-01, 02, 03, 04 | ~180 | 10 |
| 2 | 15-28 Dic 2025 | HU-05, 06, 07 | ~68 | 10 |
| 3 | 29 Dic - 11 Ene | HU-08, 09, 10, 11 | ~1,067 | 10 |
| 4 | 12-25 Ene 2026 | HU-12, 13, 14, 15 | ~329 | 10 |
| 5 | 26 Ene - 8 Feb | HU-16, 17, 18 | ~69 | 10 |
| 6 | 9-23 Feb 2026 | HU-19, 20 | ~184 | 10 |

**Totales**: 20 historias, 40 commits, ~2,062 tests, 95.12% coverage, 6 sprints (60 días laborables).

---

## Diagrama de Flujo Kanban

```
Por hacer ──→ En curso ──→ En revisión ──→ Pruebas ──→ Listo
  (Sprint      (Dev          (Code           (QA         (Tests
  Planning)    commit)       review)         commit)     pass)
```

Cada transición queda registrada por:
1. **Fecha del commit `feat(HU-XX)`**: Marca el paso de "Por hacer" a "En curso" y luego a "En revisión".
2. **Fecha del commit `test(HU-XX)`**: Marca el paso de "En revisión" a "Pruebas" y luego a "Listo".
3. **Responsable**: El developer mueve la tarjeta hasta "En revisión"; QA la mueve hasta "Listo".
