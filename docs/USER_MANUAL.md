# Manual de Usuario — Xcapit FHE-ML Platform v1.0.0-rc1

## Tabla de Contenidos

1. [Introduccion](#1-introduccion)
2. [Primeros Pasos](#2-primeros-pasos)
3. [Dashboard](#3-dashboard)
4. [Consorcios de Datos](#4-consorcios-de-datos)
5. [Modelos de Machine Learning](#5-modelos-de-machine-learning)
6. [Las 4 Capas Criptograficas](#6-las-4-capas-criptograficas)
7. [Gobernanza On-Chain](#7-gobernanza-on-chain)
8. [Marketplace de Modelos](#8-marketplace-de-modelos)
9. [Cumplimiento Regulatorio](#9-cumplimiento-regulatorio)
10. [Calidad de Datos](#10-calidad-de-datos)
11. [Explicabilidad](#11-explicabilidad)
12. [Sandbox y Demos](#12-sandbox-y-demos)
13. [SDK Python](#13-sdk-python)
14. [CLI](#14-cli)
15. [API REST](#15-api-rest)
16. [Smart Contracts](#16-smart-contracts)
17. [Planes y Precios](#17-planes-y-precios)
18. [Seguridad](#18-seguridad)
19. [Glosario](#19-glosario)

---

## 1. Introduccion

Xcapit FHE-ML es una plataforma donde multiples empresas pueden colaborar en datos sin compartirlos. A traves de consorcios de datos, las organizaciones entrenan modelos de ML conjuntos manteniendo privacidad total gracias a 4 capas criptograficas:

| Capa | Tecnologia | Funcion |
|------|-----------|---------|
| **FHE** | TenSEAL CKKS | Computacion sobre datos cifrados sin descifrarlos |
| **ZKP** | Pedersen/Schnorr | Probar propiedades sin revelar los datos |
| **MPC** | Shamir/Pairwise | Computacion distribuida sin centralizar datos |
| **DP** | Laplace/Gaussian | Ruido calibrado para privacidad diferencial |

### Casos de Uso

- **Banca**: Deteccion de fraude entre multiples bancos sin compartir datos de clientes
- **Salud**: Modelos de diagnostico entrenados con datos de multiples hospitales
- **Seguros**: Prediccion de siniestros con datos de toda la industria
- **Retail**: Prediccion de churn combinando datos de distintas cadenas

---

## 2. Primeros Pasos

### 2.1 Registro

1. Accede a [https://xcapit-privacy.vercel.app](https://xcapit-privacy.vercel.app)
2. Haz clic en **Registrarse**
3. Completa el formulario con email, contrasena (minimo 12 caracteres) y datos de tu empresa
4. Al registrarte se crea automaticamente tu empresa en el tier **free**

### 2.2 Login

```
POST /api/v2/auth/login/
{
  "email": "tu@email.com",
  "password": "tu-contrasena-segura"
}
```

Respuesta:
```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

Usa el token `access` en todas las peticiones:
```
Authorization: Bearer eyJ...
```

### 2.3 Prueba con Sandbox (sin registro)

1. Ve a la pagina de Sandbox
2. Ingresa tu email para recibir un token de 7 dias
3. Explora las demos interactivas sin compromiso

---

## 3. Dashboard

El dashboard principal muestra un resumen de tu actividad:

- **Consorcios**: Cantidad de consorcios donde participas
- **Modelos**: Modelos entrenados y desplegados
- **Uploads**: Datos subidos al consorcio
- **Training Runs**: Entrenamientos ejecutados hoy

### Navegacion

| Seccion | Descripcion |
|---------|-------------|
| Dashboard | Vista general con metricas |
| Consorcios | Gestionar y unirte a consorcios |
| Modelos | Crear, entrenar y desplegar modelos |
| Gobernanza | Propuestas, votaciones y auditoria |
| Marketplace | Explorar y adquirir modelos |
| Cumplimiento | Estado regulatorio |
| Calidad de Datos | Metricas de calidad |
| Explicabilidad | Interpretacion de modelos |
| Monitoreo | Monitoreo en tiempo real |
| Configuracion | Perfil, equipo, facturacion |

---

## 4. Consorcios de Datos

Un consorcio es un grupo de empresas que colaboran en un objetivo de ML compartido sin revelar sus datos individuales.

### 4.1 Crear un Consorcio

```
POST /api/v2/consortiums/
{
  "name": "Consorcio de Deteccion de Fraude",
  "description": "ML colaborativo para deteccion de fraude bancario",
  "model_type": "logistic_regression"
}
```

Al crearlo, tu empresa es automaticamente el **propietario** con todos los permisos.

### 4.2 Invitar Miembros

```
POST /api/v2/invitations/
{
  "consortium": "<consortium_id>",
  "company": "<company_id>",
  "role": "member"
}
```

El invitado puede aceptar o rechazar:
```
POST /api/v2/invitations/{id}/accept/
POST /api/v2/invitations/{id}/reject/
```

### 4.3 Contribuir Datos

```
POST /api/v2/sandbox/trial/upload-data/
{
  "consortium_id": "<consortium_id>",
  "data": [...],
  "record_count": 1000
}
```

Cada contribucion genera un **ContributionProof** verificable que se registra on-chain.

### 4.4 Roles y Permisos

| Rol | Crear Propuestas | Votar | Subir Datos | Gestionar Miembros | Disolver |
|-----|:---:|:---:|:---:|:---:|:---:|
| **Owner** | Si | Si | Si | Si | Si |
| **Member** | Si | Si | Si | No | No |
| **Viewer** | No | No | No | No | No |

---

## 5. Modelos de Machine Learning

### 5.1 Modelos Soportados

| Modelo | Tarea | Soporte FHE | Descripcion |
|--------|-------|:---:|-------------|
| LinearRegression | Regresion | Completo | Multiplicacion matricial CKKS |
| LogisticRegression | Clasificacion | Parcial | Aproximacion polinomial de sigmoid |
| DecisionTree | Clasificacion/Regresion | Transporte | Cifrado en entrada/salida |
| KMeans | Clustering | Transporte | Asignacion de clusters cifrada |
| RandomForest | Clasificacion | Transporte | Ensemble de arboles |
| GradientBoosting | Clasificacion | Transporte | Boosting secuencial |
| NeuralNetwork | General | Transporte | Red feedforward |
| SVM | Clasificacion | Transporte | Maquina de soporte vectorial |

### 5.2 Crear un Modelo

Desde el **Model Builder** en el dashboard:

1. Selecciona el tipo de modelo
2. Configura hiperparametros (learning rate, epochs, regularizacion)
3. Elige el nivel de seguridad FHE (128/192/256-bit)
4. Selecciona features del dataset
5. Inicia el entrenamiento

O via API:
```
POST /api/v2/federated/models/
{
  "consortium_id": "<consortium_id>",
  "name": "Modelo de Fraude v1",
  "model_type": "logistic_regression",
  "config": {
    "learning_rate": 0.01,
    "n_epochs": 100,
    "security_level": 128
  }
}
```

### 5.3 Entrenar

```
POST /api/v2/federated/models/{id}/start_round/
```

El entrenamiento federado ejecuta rondas donde cada miembro contribuye gradientes cifrados que se agregan via MPC.

### 5.4 Evaluar

La pagina **Model Metrics** muestra:
- Accuracy, Precision, Recall, F1-Score
- Curva ROC y AUC
- Matriz de confusion
- Comparacion entre versiones

### 5.5 Desplegar

```
POST /api/v2/federated/models/{id}/deploy/
```

Cambia el estado del modelo de `ready` a `deployed`, habilitandolo para inferencia.

---

## 6. Las 4 Capas Criptograficas

### 6.1 FHE — Cifrado Homomorfico Completo

Permite computar directamente sobre datos cifrados sin descifrarlos.

```python
from sdk import CKKSEncryptor, CKKSParameters, SecurityLevel

# Configurar parametros
params = CKKSParameters(
    poly_modulus_degree=8192,
    security_level=SecurityLevel.BITS_128,
)

# Cifrar datos
encryptor = CKKSEncryptor(params)
encrypted = encryptor.encrypt_vector([1.0, 2.0, 3.0])

# Operar sobre datos cifrados
result = encrypted + encrypted  # Suma homomorfica
result = encrypted * 2.5        # Multiplicacion por escalar
```

**Niveles de seguridad:**

| Nivel | Grado Polinomial | Seguridad Equivalente |
|-------|------------------|-----------------------|
| 128-bit | 8192 | AES-128 |
| 192-bit | 16384 | AES-192 |
| 256-bit | 32768 | AES-256 |

### 6.2 ZKP — Pruebas de Conocimiento Cero

Permiten probar que tus datos cumplen ciertas propiedades sin revelar los datos.

```python
from sdk import PedersenCommitment, SchnorrProof

# Comprometerse con un valor sin revelarlo
commitment = PedersenCommitment()
C, r = commitment.commit(42)

# Probar conocimiento del valor
proof = commitment.prove(42, r)
assert commitment.verify(C, proof)  # True, sin revelar 42
```

**Endpoints API:**
```
POST /api/v2/consortiums/{id}/zkp/verify-contribution/
POST /api/v2/consortiums/{id}/zkp/verify-accuracy/
```

### 6.3 MPC — Computacion Multi-Parte

Permite a multiples partes computar una funcion conjunta sin revelar sus inputs individuales.

```python
from sdk import SecretSharer, SecureAggregator

# Dividir un secreto entre N partes (threshold t de n)
sharer = SecretSharer()
shares = sharer.split(secret=42, threshold=3, num_shares=5)

# Reconstruir con cualquier 3 de 5 shares
recovered = sharer.reconstruct(shares[:3])
assert recovered == 42
```

**Endpoints API:**
```
POST /api/v2/consortiums/{id}/mpc/setup-keys/
POST /api/v2/consortiums/{id}/mpc/aggregate/
```

### 6.4 DP — Privacidad Diferencial

Agrega ruido calibrado para garantizar que ningun individuo pueda ser identificado.

```python
from sdk import LaplaceMechanism, PrivacyAccountant

# Configurar presupuesto de privacidad
accountant = PrivacyAccountant(epsilon=1.0, delta=1e-5)

# Privatizar datos
mechanism = LaplaceMechanism(epsilon=0.5, sensitivity=1.0)
noisy_value = mechanism.privatize(true_value)

# Verificar presupuesto restante
remaining = accountant.remaining_budget
```

**Endpoints API:**
```
POST /api/v2/consortiums/{id}/dp/privatize/
POST /api/v2/consortiums/{id}/dp/budget-check/
```

---

## 7. Gobernanza On-Chain

El modulo de gobernanza permite tomar decisiones de forma descentralizada con registro en blockchain.

### 7.1 Crear una Propuesta

```
POST /api/v2/governance/proposals/
{
  "consortium": "<consortium_id>",
  "proposal_type": "change_params",
  "title": "Aumentar umbral de votacion a 60%",
  "description": "Propuesta para requerir 60% de aprobacion",
  "data": {"threshold": 0.6},
  "voting_days": 7
}
```

### 7.2 Votar

```
POST /api/v2/governance/proposals/{id}/vote/
{
  "support": "for",
  "comment": "De acuerdo con el cambio"
}
```

Opciones de voto: `for`, `against`, `abstain`.

El **peso del voto** se calcula automaticamente segun las contribuciones verificadas de tu empresa al consorcio.

### 7.3 Ejecutar Propuesta

Una vez terminado el periodo de votacion:
```
POST /api/v2/governance/proposals/{id}/execute/
```

El sistema calcula si se alcanzo el umbral de aprobacion y ejecuta la accion.

### 7.4 Auditoria

Cada accion genera un evento de auditoria encadenado criptograficamente (hash chain):

```
GET /api/v2/governance/audit-events/?consortium_id=<id>
```

Verificar integridad de la cadena:
```
GET /api/v2/governance/audit-events/verify/?consortium_id=<id>
```

### 7.5 Distribucion de Recompensas

Las recompensas se distribuyen proporcionalmente a las contribuciones:
```
POST /api/v2/governance/rewards/distribute/
{
  "consortium_id": "<consortium_id>",
  "amount": "100.0"
}
```

---

## 8. Marketplace de Modelos

### 8.1 Explorar Modelos

```
GET /api/v2/marketplace/listings/
GET /api/v2/marketplace/listings/featured/
GET /api/v2/marketplace/listings/popular/
GET /api/v2/marketplace/listings/top_rated/
```

**Filtros disponibles**: `model_type`, `pricing_type`, `tags`, `search`

### 8.2 Buscar

```
POST /api/v2/marketplace/listings/search/
{
  "query": "deteccion fraude",
  "model_type": "logistic_regression",
  "pricing_type": "free",
  "min_accuracy": 0.85
}
```

### 8.3 Comprar/Desplegar

```
POST /api/v2/marketplace/listings/{id}/purchase/
{
  "consortium_id": "<consortium_id>",
  "config": {}
}
```

Requiere ser miembro del consorcio destino.

### 8.4 Escribir Resena

```
POST /api/v2/marketplace/listings/{id}/review/
{
  "rating": 5,
  "title": "Excelente modelo",
  "comment": "Muy buena precision en nuestro dataset"
}
```

Requiere haber desplegado el modelo previamente.

---

## 9. Cumplimiento Regulatorio

### 9.1 Frameworks Soportados

| Framework | Region | Industria |
|-----------|--------|-----------|
| GDPR | EU | General |
| HIPAA | US | Salud |
| SOC2 | Global | Tecnologia |
| PCI-DSS | Global | Finanzas |
| ISO 27001 | Global | General |
| LGPD | Brasil | General |

### 9.2 Verificar Cumplimiento

```
GET /api/v2/compliance/frameworks/
GET /api/v2/compliance/frameworks/{id}/controls/
```

### 9.3 Crear Evaluacion

```
POST /api/v2/compliance/assessments/
{
  "consortium_id": "<consortium_id>",
  "framework_id": "<framework_id>"
}
```

### 9.4 Ejecutar Verificaciones Automaticas

```
POST /api/v2/compliance/assessments/{id}/run_check/
```

### 9.5 Generar Reportes

```
POST /api/v2/compliance/reports/
{
  "consortium_id": "<consortium_id>",
  "framework_id": "<framework_id>"
}
```

### 9.6 Registro de Procesamiento de Datos (GDPR)

```
POST /api/v2/compliance/dpr/
{
  "consortium_id": "<consortium_id>",
  "purpose": "fraud_detection",
  "legal_basis": "legitimate_interest",
  "data_categories": ["financial", "behavioral"]
}
```

---

## 10. Calidad de Datos

### 10.1 Crear Evaluacion de Calidad

```
POST /api/v2/data-quality/assessments/
{
  "consortium": "<consortium_id>",
  "record_count": 10000,
  "feature_count": 25
}
```

### 10.2 Ejecutar Verificaciones

```
POST /api/v2/data-quality/assessments/{id}/run/
```

### 10.3 Reglas de Validacion

```
POST /api/v2/data-quality/rules/
{
  "consortium": "<consortium_id>",
  "name": "Rango de edad valido",
  "rule_type": "range",
  "conditions": {"min": 18, "max": 120, "field": "age"}
}
```

### 10.4 Alertas

Las alertas se generan automaticamente cuando se detectan anomalias:
```
GET /api/v2/data-quality/alerts/?consortium=<id>
POST /api/v2/data-quality/alerts/{id}/acknowledge/
POST /api/v2/data-quality/alerts/{id}/resolve/
```

---

## 11. Explicabilidad

### 11.1 Solicitar Explicacion

```
POST /api/v2/explainability/requests/
{
  "consortium": "<consortium_id>",
  "explanation_type": "feature_importance",
  "input_data": {"features": [1, 2, 3, 4, 5]}
}
```

**Tipos de explicacion:**
- `feature_importance` — Importancia de cada feature
- `shap` — Valores SHAP (contribucion de cada feature a la prediccion)
- `decision_path` — Camino de decision del modelo
- `summary` — Resumen general del modelo

### 11.2 Feature Importance

```
GET /api/v2/explainability/features/?consortium=<id>
GET /api/v2/explainability/features/top/?n=10
```

### 11.3 Model Insights

```
GET /api/v2/explainability/insights/?consortium=<id>
GET /api/v2/explainability/insights/summary/
POST /api/v2/explainability/insights/{id}/acknowledge/
```

---

## 12. Sandbox y Demos

### 12.1 Acceso al Sandbox

Sin registro:
```
POST /api/v2/sandbox/leads/
{
  "email": "tu@email.com",
  "company_name": "Tu Empresa"
}
```

Devuelve un token de 7 dias para explorar la plataforma.

### 12.2 Templates

```
GET /api/v2/sandbox/templates/
GET /api/v2/sandbox/templates/?industry=fintech
```

### 12.3 Crear Sandbox

```
POST /api/v2/sandbox/sandboxes/
{
  "name": "Mi Sandbox de Prueba",
  "template": "fintech-fraud",
  "industry": "fintech"
}
```

### 12.4 Datasets Sinteticos

```
POST /api/v2/sandbox/datasets/generate/
{
  "sandbox": "<sandbox_id>",
  "name": "Datos de prueba",
  "record_count": 1000,
  "feature_count": 10
}
```

### 12.5 Experimentos

```
POST /api/v2/sandbox/experiments/
{
  "sandbox": "<sandbox_id>",
  "name": "Experimento LR",
  "model_type": "logistic_regression",
  "config": {"learning_rate": 0.01}
}

POST /api/v2/sandbox/experiments/{id}/run/
```

### 12.6 Demo de Consorcio

Demo interactiva sin autenticacion:
```
POST /api/v2/sandbox/consortium-demo/
{
  "members": [
    {"name": "Banco A", "records": 5000},
    {"name": "Banco B", "records": 3000},
    {"name": "Banco C", "records": 7000}
  ]
}
```

---

## 13. SDK Python

### 13.1 Instalacion

```bash
pip install xcapit-fhe-ml

# Con FHE (TenSEAL)
pip install xcapit-fhe-ml tenseal

# Con blockchain (Web3)
pip install xcapit-fhe-ml web3
```

### 13.2 Uso Basico

```python
from sdk import LinearRegression, ModelConfig

# Configurar modelo
config = ModelConfig(learning_rate=0.01, n_epochs=100)
model = LinearRegression(config=config)

# Entrenar (plaintext)
model._fit_plaintext(X_train, y_train)

# Predecir
predictions = model._predict_plaintext(X_test)
```

### 13.3 Pipeline de ML

```python
from sdk.pipeline import Pipeline
from sdk.preprocessing import StandardScaler, OneHotEncoder
from sdk import LogisticRegression

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("encoder", OneHotEncoder()),
    ("model", LogisticRegression()),
])

pipeline.fit(X_train, y_train)
predictions = pipeline.predict(X_test)
```

### 13.4 Evaluacion

```python
from sdk.evaluation import MetricCalculator

calc = MetricCalculator()
metrics = calc.classification_report(y_true, y_pred)
print(metrics.accuracy, metrics.f1_score)
```

### 13.5 Feature Engineering

```python
from sdk.feature_engineering import FeatureEngineer

engineer = FeatureEngineer()
X_new = engineer.create_polynomial_features(X, degree=2)
X_new = engineer.create_interaction_features(X)
```

### 13.6 Blockchain

```python
from sdk.blockchain import BlockchainConnector, Network

connector = BlockchainConnector(
    network=Network.ARBITRUM_ONE,
    private_key="0x...",
)

# Registrar modelo on-chain
tx = connector.register_model(
    model_id="model-001",
    weights_hash="0xabc...",
    model_type="logistic_regression",
)
```

---

## 14. CLI

### 14.1 Comandos Disponibles

```bash
# Inicializar contexto FHE
xcapit-fhe init --output ./workspace --security-level 128

# Cifrar dataset
xcapit-fhe encrypt -i datos.csv -o cifrado.bin -t columna_target

# Entrenar modelo
xcapit-fhe train -m logistic-regression -d cifrado.bin -o modelo.bin

# Predecir
xcapit-fhe predict -m modelo.bin -i test_cifrado.bin -o predicciones.npy

# Benchmark
xcapit-fhe benchmark --models linear-regression logistic-regression --sizes 100 1000

# Blockchain: registrar modelo
xcapit-fhe blockchain register --model-id abc --hash 0x123

# Info del SDK
xcapit-fhe info
```

---

## 15. API REST

### 15.1 Autenticacion

**JWT (por defecto):**
```
Authorization: Bearer <access_token>
```

**API Key (para integraciones):**
```
Authorization: ApiKey <api_key>
```

**Sandbox Token (sin registro):**
```
Authorization: SandboxToken <token>
```

### 15.2 Endpoints por Modulo

| Modulo | Base Path | Endpoints |
|--------|-----------|-----------|
| Auth | `/api/v2/auth/` | register, login, logout, me, change-password, api-keys |
| Companies | `/api/v2/companies/` | CRUD |
| Consortiums | `/api/v2/consortiums/` | CRUD, members, contributions, training-results |
| Invitations | `/api/v2/invitations/` | CRUD, accept, reject |
| Governance | `/api/v2/governance/` | config, proposals, vote, execute, audit-events, rewards |
| Marketplace | `/api/v2/marketplace/` | listings, categories, deployments, reviews |
| Compliance | `/api/v2/compliance/` | frameworks, assessments, reports, attestations, dpr |
| Data Quality | `/api/v2/data-quality/` | assessments, rules, alerts, dashboard |
| Federated | `/api/v2/federated/` | models, endpoints, requests, nodes |
| Blockchain | `/api/v2/blockchain/` | transactions, contracts, status, consortium, model |
| Sandbox | `/api/v2/sandbox/` | leads, templates, sandboxes, datasets, experiments, trial |
| Explainability | `/api/v2/explainability/` | requests, features, insights, dashboard |
| Crypto | `/api/v2/consortiums/{id}/` | zkp, mpc, dp, crypto/status |

### 15.3 Paginacion

Todas las listas usan paginacion:
```json
{
  "count": 150,
  "next": "/api/v2/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

Parametros: `page` (default: 1), `page_size` (default: 20, max: 100)

### 15.4 Errores

Formato RFC 7807:
```json
{
  "detail": "Mensaje de error",
  "error_code": "CODIGO_ERROR"
}
```

Codigos HTTP:
- `400` — Datos invalidos
- `401` — No autenticado
- `403` — Sin permisos
- `404` — Recurso no encontrado
- `429` — Rate limit excedido

---

## 16. Smart Contracts

### 16.1 Contratos Desplegados

| Contrato | Funcion | Red |
|----------|---------|-----|
| ModelRegistryV2 | Registro y verificacion de modelos | Arbitrum |
| ConsortiumGovernanceV2 | Gobernanza multi-parte con votacion | Arbitrum |
| ComputationVerifierV2 | Verificacion de computaciones FHE | Arbitrum |

### 16.2 Operaciones On-Chain via API

```bash
# Crear consorcio on-chain
POST /api/v2/blockchain/consortium/create/

# Registrar modelo
POST /api/v2/blockchain/model/register/

# Verificar computacion
POST /api/v2/blockchain/computation/verify/

# Consultar estado
GET /api/v2/blockchain/status/
```

### 16.3 Redes Soportadas

| Red | Chain ID | Uso |
|-----|----------|-----|
| Arbitrum One | 42161 | Produccion |
| Arbitrum Sepolia | 421614 | Testing |
| Ethereum Mainnet | 1 | Alternativa |
| Ethereum Sepolia | 11155111 | Testing |

---

## 17. Planes y Precios

| Caracteristica | Free | Starter | Professional | Enterprise |
|---------------|:----:|:-------:|:------------:|:----------:|
| **Precio** | $0 | Consultar | Consultar | Consultar |
| **Rate limit** | 10 req/min | 100 req/min | 500 req/min | 2,000 req/min |
| **Peticiones/dia** | 100 | 5,000 | 50,000 | Ilimitado |
| **Modelos** | 2 | 10 | 50 | Ilimitado |
| **Consorcios** | 1 | 5 | 20 | Ilimitado |
| **Subida de datos** | 50 MB | 1 GB | 10 GB | Ilimitado |
| **Training runs/dia** | 5 | 50 | 500 | Ilimitado |
| **Sandboxes** | 1 | 3 | 10 | Ilimitado |
| **Soporte** | Comunidad | Email | Prioritario | Dedicado |

### Upgrade

```
POST /api/v2/sandbox/trial/upgrade/
{
  "target_tier": "starter"
}
```

El upgrade crea una solicitud pendiente que requiere verificacion de pago.

---

## 18. Seguridad

### 18.1 Autenticacion

- JWT con token blacklist y refresh tokens
- API Keys de larga duracion por empresa
- Proteccion contra fuerza bruta (django-axes)
- Rate limiting por tier (django-ratelimit)
- Contrasenas: minimo 12 caracteres

### 18.2 Autorizacion

- Aislamiento multi-tenant por empresa
- Validacion de membresia a consorcio en cada operacion
- Control de acceso basado en tier (free/starter/professional/enterprise)
- Permisos: IsAuthenticated, IsCompanyMember, IsConsortiumMember, IsTrialActive

### 18.3 Protecciones Implementadas

| Amenaza | Mitigacion |
|---------|-----------|
| IDOR | Validacion de membresia en serializers y querysets |
| SSRF | Validacion de URLs de webhook (bloqueo de IPs internas) |
| Timing attacks | `hmac.compare_digest()` en verificacion criptografica |
| Escalacion de privilegios | Upgrade de tier requiere verificacion de pago |
| PRNG inseguro | CSPRNG (`secrets`) para mecanismos de DP |
| Inyeccion SQL | ORM Django (queries parametrizadas) |
| XSS | CSP headers + escape automatico |
| CSRF | Django CSRF middleware + SameSite cookies |

### 18.4 Cifrado

- FHE: CKKS con seguridad equivalente a AES-128/192/256
- TLS: HTTPS obligatorio en produccion
- Datos en reposo: cifrado a nivel de campo (django-encrypted-model-fields)
- Secretos: OpenBao para gestion de secretos

---

## 19. Glosario

| Termino | Definicion |
|---------|-----------|
| **CKKS** | Esquema de cifrado homomorfico para numeros reales aproximados |
| **Consorcio** | Grupo de empresas que colaboran en ML sin compartir datos |
| **Contribution Proof** | Prueba verificable de que una empresa aporto datos al consorcio |
| **DP (Privacidad Diferencial)** | Garantia matematica de que ningun individuo es identificable |
| **Epsilon (ε)** | Presupuesto de privacidad — menor epsilon = mayor privacidad |
| **FHE** | Cifrado Totalmente Homomorfico — permite computar sobre datos cifrados |
| **Fiat-Shamir** | Transformacion que convierte pruebas interactivas en no-interactivas |
| **Hash Chain** | Cadena de hashes que garantiza integridad de eventos de auditoria |
| **MPC** | Computacion Multi-Parte — multiples partes computan sin revelar inputs |
| **Pedersen Commitment** | Compromiso criptografico que oculta un valor pero permite verificarlo |
| **Pull-over-push** | Patron donde los beneficiarios retiran fondos en vez de recibirlos automaticamente |
| **Schnorr Proof** | Prueba de conocimiento de un logaritmo discreto |
| **Shamir Secret Sharing** | Esquema que divide un secreto en N partes con threshold t |
| **SHAP** | Valores de Shapley para explicar la contribucion de cada feature |
| **Tier** | Nivel de suscripcion que determina los limites de uso |
| **ZKP** | Prueba de Conocimiento Cero — probar algo sin revelar informacion |

---

*Xcapit FHE-ML Platform v1.0.0-rc1 — Marzo 2026*
*Construido por el equipo de [Xcapit](https://xcapit.com) / [QuarkID](https://quarkid.org)*
