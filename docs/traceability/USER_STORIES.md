# User Stories - Xcapit FHE-ML Platform

> 20 historias de usuario organizadas en 6 sprints (Dic 2025 - Feb 2026).
> Convenciones: **Tipo** = desarrollador infraestructura/blockchain, **Fernando Boiero** = desarrollador backend/fullstack, **Rukia (Euge)** = QA.

---

## Sprint 1 (Dec 1-14, 2025) -- Foundation

---

## HU-01: Core FHE Encryption (CKKS)
**Como** data scientist, **quiero** encriptar datos con el esquema CKKS a 128/192/256-bit de seguridad, **para** garantizar la privacidad criptografica de los datos antes de procesarlos con modelos de ML.

| Campo | Valor |
|-------|-------|
| Sprint | 1 |
| Asignado a | Tipo |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-01): implement core FHE encryption layer with CKKS scheme (128/192/256-bit)` |
| Commit test | `test(HU-01): add unit tests for CKKS encryption wrapper and context manager` |

**Criterios de aceptacion:**
- [ ] Se puede crear un contexto CKKS con nivel de seguridad 128, 192 o 256 bits
- [ ] Los datos numericos se encriptan y desencriptan correctamente con error menor a 1e-5
- [ ] El context manager gestiona correctamente el ciclo de vida de las claves (publica, privada, relinearizacion)
- [ ] Las operaciones de suma y multiplicacion sobre datos encriptados producen resultados correctos
- [ ] Se generan claves serializables para transporte entre cliente y servidor

**Archivos fuente clave:**
- `sdk/encryption/ckks_wrapper.py`
- `sdk/encryption/context_manager.py`

**Archivos de test:**
- `tests/test_encryption.py`

**Analisis OWASP:** A04 (Cryptographic Failures) -- Se utiliza CKKS con parametros seguros de TenSEAL; los niveles de seguridad siguen las recomendaciones del Homomorphic Encryption Standard.

---

## HU-02: FHE ML Models (4 algorithms)
**Como** data scientist, **quiero** entrenar y predecir con 4 modelos de ML sobre datos encriptados (Linear Regression, Logistic Regression, Decision Tree, KMeans), **para** obtener resultados analiticos sin exponer los datos originales.

| Campo | Valor |
|-------|-------|
| Sprint | 1 |
| Asignado a | Fernando Boiero |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-02): implement 4 FHE-compatible ML models (LinearReg, LogisticReg, DecisionTree, KMeans)` |
| Commit test | `test(HU-02): add unit tests for all FHE ML models including polynomial approximations` |

**Criterios de aceptacion:**
- [ ] LinearRegression entrena y predice sobre vectores encriptados con precision aceptable
- [ ] LogisticRegression utiliza aproximacion polinomial de sigmoid para operar sobre datos encriptados
- [ ] DecisionTree implementa evaluacion de nodos compatible con FHE
- [ ] KMeans realiza clustering sobre datos encriptados con convergencia verificable
- [ ] Todos los modelos heredan de una clase base comun con interfaz fit/predict
- [ ] Los resultados encriptados se desencriptan correctamente en el cliente

**Archivos fuente clave:**
- `sdk/models/base.py`
- `sdk/models/linear_regression.py`
- `sdk/models/logistic_regression.py`
- `sdk/models/decision_tree.py`
- `sdk/models/kmeans.py`

**Archivos de test:**
- `tests/test_models.py`

**Analisis OWASP:** A04 (Cryptographic Failures) -- Las aproximaciones polinomiales mantienen la seguridad del esquema CKKS. A06 (Insecure Design) -- La interfaz base previene errores de implementacion en modelos derivados.

---

## HU-03: Blockchain & Smart Contracts
**Como** platform admin, **quiero** registrar audit trails en la blockchain de Arbitrum mediante smart contracts, **para** garantizar la trazabilidad e integridad de las operaciones de la plataforma.

| Campo | Valor |
|-------|-------|
| Sprint | 1 |
| Asignado a | Tipo |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-03): implement Arbitrum blockchain integration with smart contracts and Foundry setup` |
| Commit test | `test(HU-03): add unit tests for blockchain connector, registry, and governance client` |

**Criterios de aceptacion:**
- [ ] ConsortiumGovernance.sol permite crear y votar propuestas de gobernanza
- [ ] ModelRegistry.sol registra versiones de modelos con hashes de verificacion
- [ ] ComputationVerifier.sol verifica pruebas de computacion
- [ ] El conector blockchain (Web3.py) se conecta a Arbitrum y ejecuta transacciones
- [ ] Los contratos se despliegan con Foundry y pasan todas las pruebas on-chain
- [ ] El script de deploy configura correctamente los contratos en la red

**Archivos fuente clave:**
- `sdk/blockchain/`
- `contracts/src/v2/ConsortiumGovernance.sol`
- `contracts/src/v2/ModelRegistry.sol`
- `contracts/src/v2/ComputationVerifier.sol`
- `scripts/deploy_contracts.py`

**Archivos de test:**
- `tests/test_blockchain.py`
- `tests/test_connector.py`
- `tests/test_registry.py`
- `tests/test_governance_client.py`
- `contracts/test/`

**Analisis OWASP:** A01 (Broken Access Control) -- Los contratos implementan control de roles (owner, member). A08 (Software and Data Integrity) -- Los hashes en blockchain garantizan la integridad de los registros.

---

## HU-04: SDK CLI & API Layer
**Como** developer, **quiero** una herramienta CLI y una capa REST API para interactuar con el SDK, **para** integrar las capacidades FHE en flujos de trabajo existentes sin escribir codigo Python.

| Campo | Valor |
|-------|-------|
| Sprint | 1 |
| Asignado a | Fernando Boiero |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-04): implement SDK CLI tool with modular commands and REST API layer` |
| Commit test | `test(HU-04): add unit tests for CLI commands, monitoring, and SDK utilities` |

**Criterios de aceptacion:**
- [ ] El CLI ofrece comandos para encriptacion, entrenamiento y prediccion
- [ ] El modulo de monitoring expone metricas de uso y rendimiento
- [ ] Los quality calculators evaluan la calidad de los datos de entrada
- [ ] Las utilidades del SDK manejan serializacion y configuracion
- [ ] El benchmarking mide tiempos de encriptacion y prediccion por modelo

**Archivos fuente clave:**
- `sdk/cli/`
- `sdk/quality/`
- `sdk/monitoring.py`
- `sdk/utils/`
- `benchmarks/`

**Archivos de test:**
- `tests/test_cli.py`
- `tests/test_cli_commands.py`
- `tests/test_monitoring.py`
- `tests/test_utils.py`

**Analisis OWASP:** A05 (Injection) -- Los comandos CLI validan y sanitizan inputs. A07 (Identification and Authentication Failures) -- La gestion de API keys sigue mejores practicas.

---

## Sprint 2 (Dec 15-28, 2025) -- Platform

---

## HU-05: React Dashboard Core
**Como** end user, **quiero** un dashboard web con autenticacion, gestion de consorcios y demos interactivas, **para** operar la plataforma FHE desde una interfaz grafica accesible.

| Campo | Valor |
|-------|-------|
| Sprint | 2 |
| Asignado a | Tipo |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-05): implement React dashboard with auth, consortium management, and demo views` |
| Commit test | `test(HU-05): add sandbox environment and demo verification for dashboard components` |

**Criterios de aceptacion:**
- [ ] Login y registro funcionan con JWT tokens
- [ ] El dashboard muestra metricas principales del usuario y su organizacion
- [ ] La gestion de consorcios permite crear, ver y administrar consorcios
- [ ] Las demos interactivas muestran el flujo encrypt-train-predict en tiempo real
- [ ] La navegacion es responsive y funciona en desktop y mobile
- [ ] El contexto de React (DemoContext) gestiona el estado global correctamente

**Archivos fuente clave:**
- `dashboard/src/App.jsx`
- `dashboard/src/pages/Dashboard.jsx`
- `dashboard/src/pages/Login.jsx`
- `dashboard/src/components/`
- `dashboard/src/context/`
- `dashboard/src/api/`
- `dashboard/src/i18n/`

**Archivos de test:**
- Dashboard build validation
- Sandbox pages verification

**Analisis OWASP:** A01 (Broken Access Control) -- Rutas protegidas con verificacion de JWT. A07 (Identification and Authentication Failures) -- Tokens almacenados de forma segura, refresh automatico.

---

## HU-06: Dashboard Feature Pages
**Como** compliance officer, **quiero** paginas de gobernanza, compliance, calidad de datos y mas en el dashboard, **para** monitorear y gestionar todos los aspectos regulatorios y operativos de la plataforma.

| Campo | Valor |
|-------|-------|
| Sprint | 2 |
| Asignado a | Fernando Boiero |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-06): implement governance, compliance, data quality, and advanced dashboard pages` |
| Commit test | `test(HU-06): add visual regression checks and component integration validation` |

**Criterios de aceptacion:**
- [ ] La pagina de Governance muestra propuestas activas y permite votar
- [ ] La pagina de Compliance muestra el estado de cumplimiento regulatorio
- [ ] La pagina de Data Quality muestra scores y recomendaciones de mejora
- [ ] Competitive Insights muestra benchmarks de industria
- [ ] Model Explainability visualiza explicaciones SHAP de los modelos
- [ ] Marketplace permite explorar y compartir modelos
- [ ] Data Explorer permite explorar datasets de forma visual
- [ ] Model Deployment muestra el estado de los endpoints desplegados
- [ ] Audit Log Viewer muestra el historial de acciones
- [ ] API Playground permite probar endpoints interactivamente
- [ ] Model Metrics muestra metricas de rendimiento de los modelos

**Archivos fuente clave:**
- `dashboard/src/pages/Governance.jsx`
- `dashboard/src/pages/Compliance.jsx`
- `dashboard/src/pages/DataQuality.jsx`
- `dashboard/src/pages/CompetitiveInsights.jsx`
- `dashboard/src/pages/ModelExplainability.jsx`
- `dashboard/src/pages/Marketplace.jsx`
- `dashboard/src/pages/DataExplorer.jsx`
- `dashboard/src/pages/ModelDeployment.jsx`
- `dashboard/src/pages/AuditLogViewer.jsx`
- `dashboard/src/pages/ApiPlayground.jsx`
- `dashboard/src/pages/ModelMetrics.jsx`

**Archivos de test:**
- Component integration validation

**Analisis OWASP:** A01 (Broken Access Control) -- Cada pagina verifica permisos del usuario. A06 (Insecure Design) -- Las paginas siguen patrones de diseno seguro con validacion de datos.

---

## HU-07: Landing Pages (Verticals)
**Como** marketing stakeholder, **quiero** landing pages por vertical de industria con soporte i18n (ES/EN/DE), **para** comunicar la propuesta de valor de la plataforma a cada segmento de mercado.

| Campo | Valor |
|-------|-------|
| Sprint | 2 |
| Asignado a | Tipo |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-07): implement 5 industry vertical landing pages with animations and i18n (ES/EN/DE)` |
| Commit test | `test(HU-07): add build validation and i18n coverage tests for landing pages` |

**Criterios de aceptacion:**
- [ ] Landing Hub muestra la propuesta general de la plataforma con gradiente purple/blue
- [ ] Landing Fintech usa tema blue/indigo con casos de uso financieros
- [ ] Landing Healthcare usa tema emerald/teal con casos de uso de salud
- [ ] Landing Gobierno usa tema slate/gray con casos de uso gubernamentales
- [ ] Landing Otros usa tema purple/indigo con casos de uso generales
- [ ] Todas las paginas soportan ES, EN y DE con react-i18next
- [ ] Las animaciones SVG del hero section funcionan correctamente
- [ ] El formulario de contacto envia datos via Web3Forms API
- [ ] Cada landing sigue la estructura: Hero, Stats, How It Works, Use Cases, Compliance Badges, Contact Form

**Archivos fuente clave:**
- `dashboard/src/pages/LandingHub.jsx`
- `dashboard/src/pages/LandingFintech.jsx`
- `dashboard/src/pages/LandingHealthcare.jsx`
- `dashboard/src/pages/LandingGobierno.jsx`
- `dashboard/src/pages/LandingOtros.jsx`

**Archivos de test:**
- Build validation
- i18n coverage tests

**Analisis OWASP:** A02 (Security Misconfiguration) -- Headers de seguridad configurados en Vercel. A05 (Injection) -- Los formularios de contacto sanitizan inputs antes de enviar a Web3Forms.

---

## Sprint 3 (Dec 29 - Jan 11, 2026) -- Backend Migration

---

## HU-08: Django Core & Auth (JWT)
**Como** backend developer, **quiero** migrar el backend a Django 5.2 LTS con autenticacion JWT y service layer, **para** tener una base solida, mantenible y segura para la API de la plataforma.

| Campo | Valor |
|-------|-------|
| Sprint | 3 |
| Asignado a | Fernando Boiero |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-08): migrate backend to Django 5.2 LTS with JWT auth, service layer, and core models` |
| Commit test | `test(HU-08): add unit tests for authentication, core views, and service layer` |

**Criterios de aceptacion:**
- [ ] Django 5.2 LTS configurado con settings de produccion y test
- [ ] Autenticacion JWT con access/refresh tokens y blacklist
- [ ] Modelos core: User, Company, APIKey, AuditLog creados y migrados
- [ ] Service layer base (BaseService, ServiceResult) implementado
- [ ] AuditService registra todas las acciones criticas
- [ ] Permissions personalizados controlan acceso por rol y compania
- [ ] Exception handler devuelve errores en formato RFC 7807
- [ ] URLs configuradas bajo /api/v2/

**Archivos fuente clave:**
- `backend_django/config/settings.py`
- `backend_django/config/urls.py`
- `backend_django/apps/core/models.py`
- `backend_django/apps/core/views.py`
- `backend_django/apps/core/serializers.py`
- `backend_django/apps/core/authentication.py`
- `backend_django/apps/core/permissions.py`
- `backend_django/apps/core/exceptions.py`
- `backend_django/apps/core/services/base.py`
- `backend_django/apps/core/services/audit.py`

**Archivos de test:**
- `backend_django/tests/conftest.py`
- `backend_django/tests/test_auth.py`
- `backend_django/tests/test_core.py`

**Analisis OWASP:** A01 (Broken Access Control) -- Permisos granulares por rol y compania. A02 (Security Misconfiguration) -- Settings de produccion con DEBUG=False, ALLOWED_HOSTS, SECURE headers. A07 (Identification and Authentication Failures) -- JWT con blacklist, proteccion brute-force con django-axes.

---

## HU-09: Consortiums & Governance
**Como** consortium admin, **quiero** APIs para gestionar consorcios, miembros, contribuciones y propuestas de gobernanza, **para** coordinar el aprendizaje colaborativo entre multiples organizaciones.

| Campo | Valor |
|-------|-------|
| Sprint | 3 |
| Asignado a | Tipo |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-09): implement consortium management and governance APIs with service layer` |
| Commit test | `test(HU-09): add unit tests for consortium services, member management, and governance` |

**Criterios de aceptacion:**
- [ ] CRUD completo de consorcios con filtros y paginacion
- [ ] Gestion de miembros: invitacion, aceptacion, rechazo, expulsion
- [ ] Registro y verificacion de contribuciones (ContributionProof)
- [ ] Propuestas de gobernanza con flujo de votacion
- [ ] Estadisticas del consorcio (stats endpoint) con metricas agregadas
- [ ] Rankings de miembros por contribuciones verificadas
- [ ] Service layer (ConsortiumService, MemberService, InvitationService, ContributionService) encapsula la logica

**Archivos fuente clave:**
- `backend_django/apps/consortiums/models.py`
- `backend_django/apps/consortiums/views.py`
- `backend_django/apps/consortiums/serializers.py`
- `backend_django/apps/consortiums/services/`
- `backend_django/apps/governance/models.py`
- `backend_django/apps/governance/views.py`

**Archivos de test:**
- `backend_django/tests/test_consortiums.py`
- `backend_django/tests/test_consortium_services.py`

**Analisis OWASP:** A01 (Broken Access Control) -- Solo admins del consorcio pueden gestionar miembros. A06 (Insecure Design) -- Validaciones de estado en transiciones de miembros e invitaciones. A08 (Software and Data Integrity) -- Contribuciones verificadas con pruebas criptograficas.

---

## HU-10: Compliance, Marketplace, Sandbox
**Como** organizacion regulada, **quiero** APIs de compliance checking, marketplace de modelos y sandbox de pruebas, **para** cumplir requisitos regulatorios, compartir modelos y probar en ambientes seguros.

| Campo | Valor |
|-------|-------|
| Sprint | 3 |
| Asignado a | Fernando Boiero |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-10): implement compliance, marketplace, and sandbox Django apps with APIs` |
| Commit test | `test(HU-10): add unit tests for compliance checks, marketplace listings, and sandbox environments` |

**Criterios de aceptacion:**
- [ ] Compliance app verifica cumplimiento de regulaciones (GDPR, HIPAA, SOX, etc.)
- [ ] Marketplace permite listar, buscar y compartir modelos entre organizaciones
- [ ] Sandbox proporciona ambientes aislados para pruebas sin afectar produccion
- [ ] Cada app tiene modelos, serializers, views y URLs configurados
- [ ] Las APIs siguen los estandares REST de la plataforma (paginacion, filtros, formato de error)

**Archivos fuente clave:**
- `backend_django/apps/compliance/`
- `backend_django/apps/marketplace/`
- `backend_django/apps/sandbox/`

**Archivos de test:**
- `backend_django/tests/test_compliance.py`
- `backend_django/tests/test_marketplace.py`
- `backend_django/tests/test_sandbox.py`

**Analisis OWASP:** A01 (Broken Access Control) -- Acceso a compliance limitado a usuarios autorizados. A06 (Insecure Design) -- El sandbox aisla datos de prueba de datos de produccion.

---

## HU-11: SDK Route Tests (Legacy)
**Como** QA engineer, **quiero** tests comprehensivos para todas las rutas del SDK API, **para** asegurar la calidad y estabilidad de la capa de API antes de deprecarla.

| Campo | Valor |
|-------|-------|
| Sprint | 3 |
| Asignado a | Tipo |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-11): finalize SDK API route layer with ruff linting and modular structure` |
| Commit test | `test(HU-11): add comprehensive tests for all SDK API routes (~620 tests)` |

**Criterios de aceptacion:**
- [ ] Todas las rutas del SDK API tienen tests unitarios
- [ ] Los tests cubren casos de exito, error y edge cases
- [ ] El linting con ruff pasa sin errores
- [ ] Los tests del cliente API validan la comunicacion HTTP
- [ ] Los tests de database validan las operaciones CRUD
- [ ] Los tests de rutas de consorcio validan el flujo completo
- [ ] Los tests de rutas de sandbox validan el aislamiento
- [ ] Se alcanzan ~620 tests en el SDK

**Archivos fuente clave:**
- `sdk/` (route layer, linting fixes)

**Archivos de test:**
- `tests/test_api.py`
- `tests/test_client.py`
- `tests/test_database.py`
- `tests/test_consortium_routes.py`
- `tests/test_sandbox_routes.py`
- 10+ additional route test files

**Analisis OWASP:** A05 (Injection) -- Los tests validan sanitizacion de inputs en todas las rutas. A07 (Identification and Authentication Failures) -- Los tests verifican autenticacion en cada endpoint.

---

## Sprint 4 (Jan 12-25, 2026) -- Advanced Features

---

## HU-12: Federated Learning & ML Models
**Como** data scientist, **quiero** APIs de federated learning y gestion de modelos ML, **para** entrenar modelos distribuidos entre multiples nodos sin compartir datos.

| Campo | Valor |
|-------|-------|
| Sprint | 4 |
| Asignado a | Fernando Boiero |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-12): implement federated learning, ML model management, rate limiting, and webhooks` |
| Commit test | `test(HU-12): add unit tests for federated endpoints, model CRUD, and rate limiting` |

**Criterios de aceptacion:**
- [ ] CRUD completo de modelos ML con versionado
- [ ] Federated learning endpoints: crear sesion, unir nodos, agregar actualizaciones
- [ ] Inference endpoints para prediccion en tiempo real
- [ ] Rate limiting configurado para proteger la API
- [ ] Webhooks para notificar eventos de entrenamiento y prediccion
- [ ] Gestion de training runs con estados y metricas
- [ ] Batch prediction jobs para procesamiento masivo
- [ ] Model sharing entre organizaciones

**Archivos fuente clave:**
- `backend_django/apps/federated/models.py`
- `backend_django/apps/federated/views.py`
- `backend_django/apps/models/models.py`
- `backend_django/apps/models/views.py`
- `backend_django/apps/models/serializers.py`

**Archivos de test:**
- `backend_django/tests/test_federated.py`
- `backend_django/tests/test_models.py`

**Analisis OWASP:** A01 (Broken Access Control) -- Solo miembros autorizados pueden participar en sesiones federadas. A04 (Cryptographic Failures) -- Los datos se transmiten encriptados con FHE entre nodos.

---

## HU-13: Data Quality, Explainability, Ensemble
**Como** ML engineer, **quiero** APIs de data quality scoring, explicabilidad SHAP y metodos de ensemble, **para** evaluar la calidad de los datos, entender las predicciones y combinar multiples modelos.

| Campo | Valor |
|-------|-------|
| Sprint | 4 |
| Asignado a | Tipo |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-13): implement data quality, explainability, ensemble, and competitive insights apps` |
| Commit test | `test(HU-13): add unit tests for data quality scoring, SHAP explainability, and ensemble methods` |

**Criterios de aceptacion:**
- [ ] Data Quality evalua completeness, consistency, accuracy y timeliness de datasets
- [ ] Quality rules configurables con condiciones y umbrales
- [ ] Explainability genera explicaciones SHAP para predicciones de modelos
- [ ] Model Insights almacena y sirve insights sobre el comportamiento del modelo
- [ ] Explainability Dashboard agrega metricas de explicabilidad
- [ ] Ensemble permite combinar multiples modelos con diferentes estrategias
- [ ] Competitive Insights ofrece benchmarks de industria y reportes comparativos
- [ ] Company Metrics y Industry Benchmarks permiten analisis competitivo

**Archivos fuente clave:**
- `backend_django/apps/data_quality/`
- `backend_django/apps/explainability/`
- `backend_django/apps/ensemble/`
- `backend_django/apps/competitive_insights/`

**Archivos de test:**
- `backend_django/tests/test_data_quality.py`
- `backend_django/tests/test_explainability.py`
- `backend_django/tests/test_ensemble.py`
- `backend_django/tests/test_competitive_insights.py`

**Analisis OWASP:** A06 (Insecure Design) -- Las quality rules validan datos antes de procesarlos. A10 (Server-Side Request Forgery) -- Los servicios de datos validan URLs y origenes de datos.

---

## HU-14: Blockchain Backend & Secrets
**Como** security engineer, **quiero** servicios blockchain en el backend Django con gestion de secretos via Vault/OpenBao y conexiones resilientes, **para** asegurar la integridad de las transacciones y proteger las claves privadas.

| Campo | Valor |
|-------|-------|
| Sprint | 4 |
| Asignado a | Fernando Boiero |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-14): implement blockchain services, OpenBao secret management, and resilient connections` |
| Commit test | `test(HU-14): add unit tests for blockchain services, secret management, and resilience patterns` |

**Criterios de aceptacion:**
- [ ] BlockchainService se conecta a la red Arbitrum y ejecuta transacciones
- [ ] ModelRegistryService registra modelos en el smart contract
- [ ] ComputationVerifierService verifica pruebas de computacion on-chain
- [ ] Secrets management via OpenBao/Vault almacena claves privadas de forma segura
- [ ] Resilience patterns: circuit breaker, retry con backoff exponencial, fallback
- [ ] Views REST para consultar estado de blockchain y transacciones
- [ ] Las claves privadas nunca se exponen en logs ni respuestas API

**Archivos fuente clave:**
- `backend_django/apps/blockchain/services.py`
- `backend_django/apps/blockchain/secrets.py`
- `backend_django/apps/blockchain/resilience.py`
- `backend_django/apps/blockchain/views.py`

**Archivos de test:**
- `backend_django/tests/test_blockchain_services_views.py`

**Analisis OWASP:** A01 (Broken Access Control) -- Solo admins acceden a blockchain views. A04 (Cryptographic Failures) -- Claves privadas gestionadas via Vault, nunca en texto plano. A08 (Software and Data Integrity) -- Transacciones firmadas criptograficamente.

---

## HU-15: SDK Advanced Models
**Como** data scientist, **quiero** modelos avanzados de ML compatibles con FHE (Neural Network, Random Forest, GBM, SVM, TimeSeries, PCA), **para** aplicar tecnicas sofisticadas de ML sobre datos encriptados.

| Campo | Valor |
|-------|-------|
| Sprint | 4 |
| Asignado a | Tipo |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-15): implement advanced FHE-compatible ML models (NN, RF, GBM, SVM, TimeSeries, PCA)` |
| Commit test | `test(HU-15): add unit tests for all advanced SDK models and preprocessing pipeline` |

**Criterios de aceptacion:**
- [ ] Neural Network implementa forward pass con activaciones polinomiales sobre datos encriptados
- [ ] Random Forest combina multiples arboles de decision FHE
- [ ] Gradient Boosting implementa boosting secuencial compatible con FHE
- [ ] SVM utiliza kernel polinomial para clasificacion sobre datos encriptados
- [ ] TimeSeries implementa prediccion temporal con ventanas deslizantes
- [ ] PCA reduce dimensionalidad sobre datos encriptados
- [ ] Anomaly Detection identifica outliers en datos encriptados
- [ ] Ensemble combina predicciones de multiples modelos
- [ ] Pipeline de preprocessing normaliza y transforma datos antes de encriptar

**Archivos fuente clave:**
- `sdk/models/neural_network.py`
- `sdk/models/random_forest.py`
- `sdk/models/gradient_boosting.py`
- `sdk/models/svm.py`
- `sdk/models/time_series.py`
- `sdk/models/pca.py`
- `sdk/models/anomaly_detection.py`
- `sdk/models/ensemble.py`
- `sdk/preprocessing/`
- `sdk/evaluation/`

**Archivos de test:**
- `sdk/tests/test_neural_network.py`
- `sdk/tests/test_random_forest.py`
- `sdk/tests/test_gradient_boosting.py`
- `sdk/tests/test_preprocessing.py`

**Analisis OWASP:** A04 (Cryptographic Failures) -- Las aproximaciones polinomiales preservan la seguridad FHE. A06 (Insecure Design) -- Los modelos validan parametros y previenen overflow numerico.

---

## Sprint 5 (Jan 26 - Feb 8, 2026) -- Hardening

---

## HU-16: Docker & Deployment
**Como** DevOps engineer, **quiero** contenedores Docker y orquestacion con docker-compose, **para** desplegar la plataforma de forma reproducible y escalable en cualquier ambiente.

| Campo | Valor |
|-------|-------|
| Sprint | 5 |
| Asignado a | Fernando Boiero |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-16): implement Docker containerization, docker-compose orchestration, and deployment docs` |
| Commit test | `test(HU-16): add Docker build validation, health check tests, and middleware tests` |

**Criterios de aceptacion:**
- [ ] Dockerfile multi-stage produce imagen de ~654MB con Python 3.12
- [ ] docker-compose.yml orquesta backend, PostgreSQL y Redis
- [ ] docker-entrypoint.sh ejecuta migraciones automaticamente al iniciar
- [ ] Health checks configurados para todos los servicios
- [ ] Gunicorn configurado como servidor WSGI de produccion
- [ ] WhiteNoise sirve archivos estaticos sin servidor web adicional
- [ ] Variables de entorno documentadas y configurables
- [ ] Build completo en ~3 minutos

**Archivos fuente clave:**
- `backend_django/Dockerfile`
- `docker-compose.yml`
- `backend_django/docker-entrypoint.sh`
- `deploy/`

**Archivos de test:**
- Docker build validation
- Health check endpoint tests

**Analisis OWASP:** A02 (Security Misconfiguration) -- Imagen Docker sin paquetes innecesarios, usuario non-root. A03 (Injection) -- Dependencias pinned en requirements.txt para prevenir supply chain attacks.

---

## HU-17: CI/CD Pipelines
**Como** DevOps engineer, **quiero** pipelines CI/CD en GitHub Actions y GitLab CI, **para** automatizar tests, linting, security scanning y deployment en cada push.

| Campo | Valor |
|-------|-------|
| Sprint | 5 |
| Asignado a | Tipo |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-17): implement CI/CD pipelines for GitHub Actions and GitLab CI with security scanning` |
| Commit test | `test(HU-17): validate CI pipelines with lint fixes, TypeScript SDK build, and ruff error resolutions` |

**Criterios de aceptacion:**
- [ ] GitHub Actions pipeline verde con 10/10 jobs (lint, test, build, security)
- [ ] GitLab CI pipeline verde con 9/9 jobs
- [ ] Coverage threshold configurado en 90% (--cov-fail-under=90)
- [ ] CodeQL v4 para analisis de seguridad estatico
- [ ] Pre-commit hooks configurados (.pre-commit-config.yaml)
- [ ] TypeScript SDK build y lint en CI
- [ ] 341 errores de ruff corregidos
- [ ] SARIF upload a GitHub Security con permisos correctos

**Archivos fuente clave:**
- `.github/workflows/ci.yml`
- `.github/workflows/codeql.yml`
- `.gitlab-ci.yml`
- `.pre-commit-config.yaml`
- `sdk-typescript/`

**Archivos de test:**
- Pipeline green validation
- TypeScript SDK build verification

**Analisis OWASP:** A02 (Security Misconfiguration) -- Los pipelines validan configuracion de seguridad en cada push. A03 (Injection) -- CodeQL detecta vulnerabilidades de inyeccion en el codigo.

---

## HU-18: Security Hardening
**Como** security engineer, **quiero** security headers, proteccion contra brute-force, CORS correctamente configurado y bugs de seguridad corregidos, **para** proteger la plataforma contra las vulnerabilidades mas comunes.

| Campo | Valor |
|-------|-------|
| Sprint | 5 |
| Asignado a | Fernando Boiero |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-18): implement security hardening, bug fixes, and production readiness measures` |
| Commit test | `test(HU-18): add security tests for rate limiting, middleware, and authentication fixes` |

**Criterios de aceptacion:**
- [ ] Security headers configurados: HSTS, X-Content-Type-Options, X-Frame-Options, CSP
- [ ] django-axes protege contra brute-force en login (lockout despues de N intentos)
- [ ] django-ratelimit limita requests por IP y por usuario
- [ ] CORS configurado con whitelist de origenes permitidos
- [ ] Bugs de autenticacion corregidos (RegisterSerializer, APIKey, authentication)
- [ ] Bug federated/views.py corregido (endpoint.model.version -> current_version)
- [ ] Middleware de logging registra requests y responses sin datos sensibles

**Archivos fuente clave:**
- `backend_django/apps/core/authentication.py`
- `backend_django/config/settings.py`
- `backend_django/apps/federated/views.py`

**Archivos de test:**
- `backend_django/tests/test_middleware.py`

**Analisis OWASP:** A01 (Broken Access Control), A02 (Security Misconfiguration), A03 (Injection), A04 (Cryptographic Failures), A05 (Security Misconfiguration), A06 (Insecure Design), A07 (Identification and Authentication Failures), A08 (Software and Data Integrity), A09 (Security Logging and Monitoring Failures), A10 (Server-Side Request Forgery) -- Revision integral de seguridad cubriendo todos los riesgos OWASP Top 10.

---

## Sprint 6 (Feb 9-23, 2026) -- Quality & Docs

---

## HU-19: Test Coverage 95%+
**Como** QA lead, **quiero** alcanzar 95%+ de coverage en los tests de Django, **para** asegurar la calidad y confiabilidad de todo el backend de la plataforma.

| Campo | Valor |
|-------|-------|
| Sprint | 6 |
| Asignado a | Tipo (infra) / Rukia (tests) |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-19): add test infrastructure and fixtures for comprehensive Django coverage` |
| Commit test | `test(HU-19): add 1,100+ tests to reach 95% Django coverage (views, services, models)` |

**Criterios de aceptacion:**
- [ ] Coverage total de Django alcanza 95%+ (medido con pytest-cov)
- [ ] models/views.py: 37% -> 96%
- [ ] core/views.py: 66% -> 91%
- [ ] ensemble/views.py: 49% -> 94%
- [ ] competitive_insights/views.py: 53% -> 90%
- [ ] consortiums/views.py: 67% -> 97%
- [ ] consortiums/services/training.py: 38% -> 99%
- [ ] core/cache.py: 56% -> 97%
- [ ] core/permissions.py: 63% -> ~100%
- [ ] core/services/audit.py: 58% -> ~100%
- [ ] 1,442+ tests pasando en total
- [ ] Fixtures y conftest.py proporcionan infraestructura de test reutilizable

**Archivos fuente clave:**
- `backend_django/tests/conftest.py`

**Archivos de test:**
- `backend_django/tests/test_coverage_95.py` (179 tests)
- `backend_django/tests/test_coverage_modules.py` (103 tests)
- `backend_django/tests/test_models_views.py` (124 tests)
- `backend_django/tests/test_views_extended.py` (67 tests)
- `backend_django/tests/test_consortium_tasks_training.py` (49 tests)
- `backend_django/tests/test_competitive_emails.py` (16 tests)
- `backend_django/tests/test_quality_assessment_service.py` (30 tests)
- `backend_django/tests/test_coverage_boost.py` (16 tests)
- `backend_django/tests/test_blockchain_services_views.py` (67 tests)
- `backend_django/tests/test_proposal_execution.py`

**Analisis OWASP:** A06 (Insecure Design) -- Los tests cubren edge cases y flujos de error que podrian exponer vulnerabilidades. A10 (Server-Side Request Forgery) -- Los tests verifican validacion de inputs en todos los endpoints.

---

## HU-20: E2E Tests & Documentation
**Como** product owner, **quiero** tests end-to-end de flujos completos y documentacion comprehensiva, **para** validar que la plataforma funciona correctamente de extremo a extremo y facilitar el onboarding de nuevos desarrolladores.

| Campo | Valor |
|-------|-------|
| Sprint | 6 |
| Asignado a | Fernando Boiero |
| QA | Rukia (Euge) |
| Commit impl | `feat(HU-20): add comprehensive documentation, architecture diagrams, and skills architecture` |
| Commit test | `test(HU-20): add 5 E2E integration tests (ML lifecycle, marketplace, federated, governance)` |

**Criterios de aceptacion:**
- [ ] E2E test: ML model lifecycle (create -> train -> predict -> export)
- [ ] E2E test: Model sharing & marketplace (share -> list -> request -> approve)
- [ ] E2E test: Federated learning (create session -> join nodes -> aggregate -> evaluate)
- [ ] E2E test: Data quality -> consortium -> training (assess quality -> create consortium -> train model)
- [ ] E2E test: Governance proposal -> vote -> execute (create proposal -> vote -> execute -> verify)
- [ ] CLAUDE.md actualizado con estadisticas y estado del proyecto
- [ ] README.md actualizado con instrucciones de Django (en lugar de FastAPI)
- [ ] CHANGELOG.md con version 2.0.0 documentando la migracion completa
- [ ] Documentacion de arquitectura en docs/
- [ ] Skills de Claude Code configurados en .claude/skills/

**Archivos fuente clave:**
- `CLAUDE.md`
- `README.md`
- `CHANGELOG.md`
- `docs/`
- `.claude/skills/`

**Archivos de test:**
- `backend_django/tests/integration/test_e2e_flows.py` (5 tests)

**Analisis OWASP:** A06 (Insecure Design) -- Los tests E2E validan flujos completos incluyendo controles de acceso. A09 (Security Logging and Monitoring Failures) -- La documentacion incluye guias de logging y monitoreo para operaciones.
