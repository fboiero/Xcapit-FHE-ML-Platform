# Xcapit FHE-ML Platform - Guia de Onboarding Paso a Paso

## Resumen del Flujo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUJO COMPLETO DE ONBOARDING                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. REGISTRO         2. API KEY        3. SANDBOX         4. PRUEBAS       │
│   ┌─────────┐        ┌─────────┐       ┌─────────┐       ┌─────────┐       │
│   │ Company │  ───►  │ Generate│  ───► │ Create  │  ───► │ Run     │       │
│   │ + Email │        │ API Key │       │ Sandbox │       │ Expts   │       │
│   └─────────┘        └─────────┘       └─────────┘       └─────────┘       │
│        │                  │                  │                  │           │
│        ▼                  ▼                  ▼                  ▼           │
│   ┌─────────┐        ┌─────────┐       ┌─────────┐       ┌─────────┐       │
│   │  User   │        │  JWT    │       │ Datasets│       │ Results │       │
│   │ Created │        │ Tokens  │       │ Synth.  │       │ + Model │       │
│   └─────────┘        └─────────┘       └─────────┘       └─────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Paso 1: Registro de Empresa

### 1.1 Acceder a la Pagina de Registro

**URL**: `https://xcapit-privacy.vercel.app/register`

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──┐                                            ES | EN      │
│  │🔒│ Xcapit Privacy                           [Iniciar sesion]│
├────────────────────────────────────────────────────────────────┤
│                                                                │
│                    Crea tu cuenta                              │
│                                                                │
│         Empieza a explorar el machine learning                 │
│              preservando la privacidad                         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Nombre de la empresa                                     │  │
│  │ [Banco Digital LATAM                                  ]  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Correo corporativo                                       │  │
│  │ [admin@bancodigital.com                               ]  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│             ┌────────────────────────────┐                     │
│             │     Registrar Empresa      │                     │
│             └────────────────────────────┘                     │
│                                                                │
│              Ya tienes cuenta? Iniciar sesion                  │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Obtener API Key (Una sola vez)

**IMPORTANTE**: La API Key solo se muestra una vez. Guardarla de forma segura.

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│                    ✅ Registro Exitoso!                        │
│                                                                │
│         Tu empresa ha sido registrada correctamente            │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │   Tu API Key (guardar - solo se muestra una vez):        │  │
│  │                                                          │  │
│  │   fheml_a7x9k2m4p6q8r0s3t5u7v9w1y3z5b7c9d1e3f5g7h9     │  │
│  │                                                          │  │
│  │                      [📋 Copiar]                         │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│         Redirigiendo al login en 3 segundos...                 │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Backend: Que sucede internamente

```python
# POST /api/v2/auth/register/
{
    "company_name": "Banco Digital LATAM",
    "email": "admin@bancodigital.com"
}

# Response 201 Created
{
    "user_id": "uuid-...",
    "email": "admin@bancodigital.com",
    "company": {
        "id": "uuid-...",
        "name": "Banco Digital LATAM"
    },
    "api_key": "fheml_a7x9k2m4p6q8r0s3t5u7v9w1y3z5b7c9d1e3f5g7h9",
    "tokens": {
        "access": "eyJ...",
        "refresh": "eyJ..."
    }
}
```

---

## Paso 2: Login y Autenticacion

### 2.1 Iniciar Sesion con API Key

**URL**: `https://xcapit-privacy.vercel.app/login`

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──┐                                            ES | EN      │
│  │🔒│ Xcapit Privacy                                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│                    Iniciar Sesion                              │
│                                                                │
│         Ingresa tu API Key para acceder                        │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ API Key                                                  │  │
│  │ [fheml_a7x9k2m4p6q8r0s3t5u7v9w1y3z5b7c9d1e3f5...     ]  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│             ┌────────────────────────────────┐                 │
│             │        Iniciar Sesion          │                 │
│             └────────────────────────────────┘                 │
│                                                                │
│              No tienes cuenta? Registrate                      │
│                                                                │
│  ─────────────────── O ────────────────────                    │
│                                                                │
│              [🎮 Probar Demo sin Registro]                     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Dashboard Principal

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──┐                                 [🔔] [👤 Banco Digital] │
│  │🔒│ Xcapit Privacy                                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Bienvenido, Banco Digital LATAM                               │
│                                                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ Consorcios   │ │ Modelos      │ │ Experimentos │           │
│  │     3        │ │     2        │ │     5        │           │
│  │   activos    │ │  entrenados  │ │  ejecutados  │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Acciones Rapidas                                        │  │
│  │                                                          │  │
│  │  [🧪 Crear Sandbox]  [➕ Nuevo Consorcio]  [📊 Subir]    │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Actividad Reciente                                            │
│  ─────────────────                                             │
│  • Modelo entrenado - hace 2 horas                             │
│  • Nuevo miembro en consorcio - hace 5 horas                   │
│  • Dataset encriptado subido - hace 1 dia                      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Paso 3: Crear Ambiente Sandbox

### 3.1 Iniciar Sandbox

```
┌────────────────────────────────────────────────────────────────┐
│  Sandbox de Pruebas                                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Selecciona tu industria:                                      │
│                                                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐ │
│  │   🏦        │ │   🏥        │ │   🛒        │ │   🛡️     │ │
│  │ Finanzas    │ │   Salud     │ │  Retail     │ │ Seguros  │ │
│  │ ✓ Selec.   │ │             │ │             │ │          │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Configuracion del Sandbox                               │  │
│  │                                                          │  │
│  │  Nombre: [Sandbox Fraude Q1 2025                      ]  │  │
│  │                                                          │  │
│  │  Template: [Deteccion de Fraude - LATAM            ▼]   │  │
│  │                                                          │  │
│  │  Duracion: [7 dias ▼]  (max 30 dias)                     │  │
│  │                                                          │  │
│  │              [🚀 Crear Sandbox]                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Backend: Crear Sandbox

```python
# POST /api/v2/sandbox/sandboxes/
{
    "name": "Sandbox Fraude Q1 2025",
    "industry": "finance",
    "template_id": "uuid-template-fraud-detection"  # opcional
}

# Response 201 Created
{
    "id": "uuid-sandbox-...",
    "name": "Sandbox Fraude Q1 2025",
    "industry": "finance",
    "status": "active",
    "created_at": "2025-01-24T10:00:00Z",
    "expires_at": "2025-01-31T10:00:00Z",
    "datasets": [],
    "experiments": []
}
```

---

## Paso 4: Generar Datos Sinteticos

### 4.1 Configurar Dataset

```
┌────────────────────────────────────────────────────────────────┐
│  Generar Dataset Sintetico                                     │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Tipo de datos:                                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ [●] Transacciones (fraude financiero)                  │    │
│  │ [ ] Pacientes (datos medicos)                          │    │
│  │ [ ] Clientes (retail)                                  │    │
│  │ [ ] Reclamos (seguros)                                 │    │
│  │ [ ] Personalizado                                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                │
│  Cantidad de registros: [10,000    ]  (max 100,000)            │
│                                                                │
│  Features incluidas:                                           │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ✅ amount        (float)   $10 - $10,000              │    │
│  │  ✅ hour          (int)     0 - 23                     │    │
│  │  ✅ merchant_cat  (category) retail/food/travel/online │    │
│  │  ✅ distance_km   (float)   0 - 500                    │    │
│  │  ✅ is_fraud      (bool)    2% true ratio              │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                │
│              [📊 Generar Dataset]                              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Backend: Generar Datos

```python
# POST /api/v2/sandbox/datasets/generate/
{
    "sandbox_id": "uuid-sandbox-...",
    "dataset_type": "transactions",
    "record_count": 10000,
    "features": [
        {"name": "amount", "type": "float", "min": 10, "max": 10000},
        {"name": "hour", "type": "int", "min": 0, "max": 23},
        {"name": "merchant_category", "type": "category",
         "values": ["retail", "food", "travel", "online"]},
        {"name": "distance_km", "type": "float", "min": 0, "max": 500},
        {"name": "is_fraud", "type": "bool", "true_ratio": 0.02}
    ]
}

# Response 201 Created
{
    "id": "uuid-dataset-...",
    "name": "Synthetic transactions Dataset",
    "record_count": 10000,
    "feature_count": 5,
    "data_preview": [
        {"amount": 523.45, "hour": 14, "merchant_category": "retail",
         "distance_km": 12.3, "is_fraud": false},
        // ... 9 more rows
    ],
    "statistics": {
        "record_count": 10000,
        "features": {
            "amount": {"type": "float", "min": 10, "max": 10000, "mean": 5005},
            "is_fraud": {"type": "bool", "true_ratio": 0.02, "false_ratio": 0.98}
        }
    }
}
```

---

## Paso 5: Crear y Ejecutar Experimentos

### 5.1 Configurar Experimento

```
┌────────────────────────────────────────────────────────────────┐
│  Nuevo Experimento                                             │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Nombre: [Entrenamiento Modelo Fraude v1                   ]   │
│                                                                │
│  Tipo de experimento:                                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ [●] Training      - Entrenar modelo con FHE            │    │
│  │ [ ] Evaluation    - Evaluar modelo existente           │    │
│  │ [ ] Clustering    - K-Means sobre datos encriptados    │    │
│  │ [ ] Benchmark     - Medir rendimiento de encriptacion  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                │
│  Dataset: [Synthetic transactions Dataset (10K)        ▼]      │
│                                                                │
│  Configuracion:                                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Modelo: [Logistic Regression ▼]                       │    │
│  │  Epochs: [10  ]                                        │    │
│  │  Learning Rate: [0.01]                                 │    │
│  │  ✅ Usar FHE (encriptar datos)                         │    │
│  │  Seguridad: [128-bit ▼]                                │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                │
│              [🚀 Ejecutar Experimento]                         │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 Resultados del Experimento

```
┌────────────────────────────────────────────────────────────────┐
│  Experimento: Entrenamiento Modelo Fraude v1                   │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Estado: ✅ Completado                                         │
│  Duracion: 45 segundos                                         │
│                                                                │
│  Metricas:                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                          │  │
│  │    Accuracy        Precision       Recall       F1       │  │
│  │   ┌────────┐      ┌────────┐     ┌────────┐  ┌────────┐ │  │
│  │   │ 94.2%  │      │ 91.5%  │     │ 87.3%  │  │ 89.3%  │ │  │
│  │   └────────┘      └────────┘     └────────┘  └────────┘ │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Comparacion: Plaintext vs FHE                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Metrica         Plaintext       FHE         Diferencia  │  │
│  │  ─────────────────────────────────────────────────────── │  │
│  │  Accuracy        94.5%           94.2%       -0.3%       │  │
│  │  Tiempo (s)      2.1             45.0        +21x        │  │
│  │  Privacidad      ❌ Expuesta     ✅ Protegida            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  [📥 Descargar Modelo]  [📊 Ver Detalles]  [🔄 Re-ejecutar]   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Flujo Completo via API (Notebook/SDK)

### Usando el SDK de Python

```python
# 1. Configuracion inicial
from sdk.encryption import CKKSEncryptor, SecurityLevel
from sdk.models import LogisticRegression
from sdk.utils import SecureDataLoader
from sdk.blockchain import BlockchainConnector, Network

# 2. Conectar a blockchain (opcional)
connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
connector.connect()

# 3. Crear encriptador
encryptor = CKKSEncryptor(security_level=SecurityLevel.BITS_128)

# 4. Cargar y encriptar datos
loader = SecureDataLoader(encryption_scheme="CKKS")
X_enc, y_enc = loader.load_and_encrypt("transactions.csv")

# 5. Entrenar modelo
model = LogisticRegression(encryptor=encryptor)
model.fit(X_enc, y_enc, epochs=10)

# 6. Hacer predicciones
predictions = model.predict(X_test_enc)

# 7. Desencriptar resultados (solo el cliente)
results = encryptor.decrypt(predictions)
```

### Usando la REST API directamente

```bash
# 1. Autenticacion
export API_KEY="fheml_tu_api_key_aqui"

# 2. Crear sandbox
curl -X POST https://apifhe.xcapit.com/api/v2/sandbox/sandboxes/ \
  -H "Authorization: ApiKey $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Sandbox", "industry": "finance"}'

# 3. Generar datos
curl -X POST https://apifhe.xcapit.com/api/v2/sandbox/datasets/generate/ \
  -H "Authorization: ApiKey $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sandbox_id": "uuid-del-sandbox",
    "dataset_type": "transactions",
    "record_count": 1000
  }'

# 4. Crear experimento
curl -X POST https://apifhe.xcapit.com/api/v2/sandbox/experiments/ \
  -H "Authorization: ApiKey $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "sandbox_id": "uuid-del-sandbox",
    "name": "Training Test",
    "experiment_type": "training",
    "dataset_id": "uuid-del-dataset",
    "config": {"model_type": "logistic_regression", "epochs": 10}
  }'

# 5. Ejecutar experimento
curl -X POST https://apifhe.xcapit.com/api/v2/sandbox/experiments/{id}/run/ \
  -H "Authorization: ApiKey $API_KEY"
```

---

## Verticales Soportadas

| Vertical | Dataset Type | Features Predeterminadas | Casos de Uso |
|----------|--------------|-------------------------|--------------|
| **Fintech** | `transactions` | amount, hour, merchant, distance, is_fraud | Fraude, Credit Scoring |
| **Healthcare** | `patients` | age, blood_pressure, cholesterol, diagnosis | Prediccion, Investigacion |
| **Retail** | `customers` | recency, frequency, monetary, churn | Churn, Segmentacion |
| **Insurance** | `claims` | amount, type, age, history, is_fraudulent | Fraude en reclamos |
| **Government** | `citizens` | age, income_bracket, region, service_usage | Asignacion recursos |

---

## Proximos Pasos

1. **Ver notebooks por vertical**: `/docs/notebooks/`
2. **Unirse a un consorcio**: Dashboard > Consorcios > Buscar
3. **Contribuir datos reales**: Dashboard > Subir Dataset
4. **Integrar via API**: Ver documentacion en `/api/v2/docs/`

---

## Contacto y Soporte

- **Documentacion API**: https://apifhe.xcapit.com/api/v2/docs/
- **Demo interactiva**: https://xcapit-privacy.vercel.app/sandbox-demo
- **Email**: soporte@xcapit.com
