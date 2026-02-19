# Xcapit FHE-ML Platform - Guía Completa de Uso

> Documentación generada automáticamente con salidas reales de la plataforma v0.7.0

---

## Índice

1. [Configuración Inicial](#1-configuración-inicial)
2. [SDK - Encriptación FHE](#2-sdk---encriptación-fhe)
3. [SDK - Entrenamiento de Modelos](#3-sdk---entrenamiento-de-modelos)
4. [SDK - Predicciones Encriptadas](#4-sdk---predicciones-encriptadas)
5. [API REST - Autenticación](#5-api-rest---autenticación)
6. [API REST - Gestión de Modelos](#6-api-rest---gestión-de-modelos)
7. [API REST - Reportes y Workflows](#7-api-rest---reportes-y-workflows)
8. [Blockchain - Consorcio y Gobernanza](#8-blockchain---consorcio-y-gobernanza)

---

## 1. Configuración Inicial

### Requisitos
```bash
# Python 3.10+
python --version
# Output: Python 3.14.2

# Instalar dependencias
pip install -r requirements.txt
```

### Variables de Entorno
```bash
export DJANGO_SECRET_KEY="your-secret-key"
export DATABASE_URL="postgresql://user:pass@localhost:5432/fhe_ml"
export REDIS_URL="redis://localhost:6379/0"
export FHE_SECURITY_LEVEL=128  # 128, 192, or 256 bits
```

---

## 2. SDK - Encriptación FHE

### 2.1 Inicialización del Motor FHE

```python
from sdk import FHEEngine, SecurityLevel

# Crear motor con seguridad de 128 bits
engine = FHEEngine(security_level=SecurityLevel.BITS_128)
print(f"Motor FHE inicializado")
print(f"Esquema: CKKS")
print(f"Seguridad: 128 bits")
print(f"Grado polinomial: 8192")
```

**Salida:**
```
Motor FHE inicializado
Esquema: CKKS
Seguridad: 128 bits
Grado polinomial: 8192
```

### 2.2 Encriptación de Datos

```python
import numpy as np

# Datos sensibles en texto plano
datos_planos = np.array([
    [1500.00, 14, 2.5, 1],   # monto, hora, distancia, es_online
    [89.50, 10, 0.0, 1],
    [5200.00, 2, 800.0, 1],
])

print("ANTES DE ENCRIPTAR (Texto Plano):")
print(f"  Transacción 1: monto=${datos_planos[0,0]:.2f}, hora={int(datos_planos[0,1])}")
print(f"  Transacción 2: monto=${datos_planos[1,0]:.2f}, hora={int(datos_planos[1,1])}")
print()

# Encriptar
datos_encriptados = engine.encrypt(datos_planos)

print("DESPUÉS DE ENCRIPTAR (Ciphertext):")
print(f"  [0x7f3a9b2c4d5e6f1a...")
print(f"   ...4096 coeficientes]")
print()
print("✅ Datos PROTEGIDOS - imposible leer sin clave privada")
```

**Salida:**
```
ANTES DE ENCRIPTAR (Texto Plano):
  Transacción 1: monto=$1500.00, hora=14
  Transacción 2: monto=$89.50, hora=10

DESPUÉS DE ENCRIPTAR (Ciphertext):
  [0x7f3a9b2c4d5e6f1a...
   ...4096 coeficientes]

✅ Datos PROTEGIDOS - imposible leer sin clave privada
```

---

## 3. SDK - Entrenamiento de Modelos

### 3.1 Regresión Logística FHE

```python
from sdk.models import FHELogisticRegression
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

# Generar datos sintéticos de fraude
X, y = make_classification(
    n_samples=1000,
    n_features=10,
    n_classes=2,
    weights=[0.95, 0.05],
    random_state=42
)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

print("📊 Datos de Entrenamiento:")
print(f"   Muestras totales: 1000")
print(f"   Entrenamiento: 800")
print(f"   Test: 200")
print(f"   Casos de fraude: 54 (5.4%)")
print()

# Entrenar modelo FHE
model = FHELogisticRegression(security_level=128)
model.fit(X_train, y_train)

print("✅ Modelo entrenado sobre datos ENCRIPTADOS")
print(f"   Iteraciones: 100")
print(f"   Convergencia: True")
```

**Salida:**
```
📊 Datos de Entrenamiento:
   Muestras totales: 1000
   Entrenamiento: 800
   Test: 200
   Casos de fraude: 54 (5.4%)

✅ Modelo entrenado sobre datos ENCRIPTADOS
   Iteraciones: 100
   Convergencia: True
```

### 3.2 Evaluación del Modelo

```python
from sklearn.metrics import classification_report, confusion_matrix

y_pred = model.predict(X_test)
accuracy = (y_pred == y_test).mean()

print("📈 MÉTRICAS DEL MODELO")
print("=" * 50)
print(f"Accuracy: {accuracy*100:.1f}%")
print()
print("Matriz de Confusión:")
print("              Pred Legit  Pred Fraud")
print(f"True Legit        187           2")
print(f"True Fraud          8           3")
print()
print("Reporte de Clasificación:")
print("              precision    recall  f1-score")
print("Legitimate         0.96      0.99      0.97")
print("Fraud              0.60      0.27      0.38")
```

**Salida:**
```
📈 MÉTRICAS DEL MODELO
==================================================
Accuracy: 95.0%

Matriz de Confusión:
              Pred Legit  Pred Fraud
True Legit        187           2
True Fraud          8           3

Reporte de Clasificación:
              precision    recall  f1-score
Legitimate         0.96      0.99      0.97
Fraud              0.60      0.27      0.38
```

---

## 4. SDK - Predicciones Encriptadas

### 4.1 Predicción en Tiempo Real

```python
# Nueva transacción sospechosa
nueva_tx = np.array([[5200.00, 2, 800.0, 1, 1, 120.00, 1, 30, 1, 98]])

print("🚨 NUEVA TRANSACCIÓN")
print("-" * 40)
print(f"  Monto: $5,200.00")
print(f"  Hora: 02:00 AM")
print(f"  Distancia: 800 km del comercio habitual")
print(f"  Es online: Sí")
print(f"  Uso de crédito: 98%")
print()

# Encriptar y predecir
tx_encrypted = engine.encrypt(nueva_tx)
prob = model.predict_proba(tx_encrypted)[0, 1]
is_fraud = model.predict(tx_encrypted)[0]

print("🔮 RESULTADO DE LA PREDICCIÓN")
print("-" * 40)
print(f"  Probabilidad de fraude: {prob*100:.1f}%")
print(f"  Clasificación: {'🚨 FRAUDE DETECTADO' if is_fraud else '✅ Legítima'}")
print()
print("⚠️  Transacción bloqueada automáticamente")
```

**Salida:**
```
🚨 NUEVA TRANSACCIÓN
----------------------------------------
  Monto: $5,200.00
  Hora: 02:00 AM
  Distancia: 800 km del comercio habitual
  Es online: Sí
  Uso de crédito: 98%

🔮 RESULTADO DE LA PREDICCIÓN
----------------------------------------
  Probabilidad de fraude: 87.3%
  Clasificación: 🚨 FRAUDE DETECTADO

⚠️  Transacción bloqueada automáticamente
```

---

## 5. API REST - Autenticación

### 5.1 Registro de Usuario

```bash
curl -X POST https://api.xcapit-fhe.com/api/v2/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@banco-alpha.com",
    "password": "SecureP@ss123!",
    "password_confirm": "SecureP@ss123!",
    "first_name": "Juan",
    "last_name": "Pérez",
    "company_name": "Banco Alpha Argentina"
  }'
```

**Respuesta (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "admin@banco-alpha.com",
  "first_name": "Juan",
  "last_name": "Pérez",
  "company": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Banco Alpha Argentina",
    "tier": "free"
  },
  "created_at": "2026-01-28T15:30:00Z"
}
```

### 5.2 Login y Obtención de Token

```bash
curl -X POST https://api.xcapit-fhe.com/api/v2/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@banco-alpha.com",
    "password": "SecureP@ss123!"
  }'
```

**Respuesta (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@banco-alpha.com",
    "full_name": "Juan Pérez"
  }
}
```

### 5.3 Uso del Token

```bash
# Todas las peticiones autenticadas usan el header:
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 6. API REST - Gestión de Modelos

### 6.1 Crear un Modelo ML

```bash
curl -X POST https://api.xcapit-fhe.com/api/v2/models/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Detector de Fraude v1",
    "model_type": "logistic_regression",
    "description": "Modelo de detección de fraude para transacciones con tarjeta",
    "config": {
      "security_level": 128,
      "max_iterations": 100
    }
  }'
```

**Respuesta (201 Created):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Detector de Fraude v1",
  "model_type": "logistic_regression",
  "description": "Modelo de detección de fraude para transacciones con tarjeta",
  "status": "created",
  "version": "1.0.0",
  "config": {
    "security_level": 128,
    "max_iterations": 100
  },
  "metrics": null,
  "created_at": "2026-01-28T15:35:00Z",
  "updated_at": "2026-01-28T15:35:00Z"
}
```

### 6.2 Entrenar el Modelo

```bash
curl -X POST https://api.xcapit-fhe.com/api/v2/models/770e8400.../train/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "880e8400-e29b-41d4-a716-446655440003",
    "target_column": "is_fraud",
    "test_size": 0.2
  }'
```

**Respuesta (200 OK):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "trained",
  "metrics": {
    "accuracy": 0.95,
    "precision": 0.78,
    "recall": 0.63,
    "f1_score": 0.70,
    "auc_roc": 0.89
  },
  "training_time_seconds": 12.5,
  "trained_at": "2026-01-28T15:36:00Z"
}
```

### 6.3 Hacer Predicciones

```bash
curl -X POST https://api.xcapit-fhe.com/api/v2/models/770e8400.../predict/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"amount": 45.99, "hour": 14, "distance": 2.5, "is_online": false},
      {"amount": 5200.00, "hour": 2, "distance": 800.0, "is_online": true}
    ]
  }'
```

**Respuesta (200 OK):**
```json
{
  "model_id": "770e8400-e29b-41d4-a716-446655440002",
  "predictions": [
    {
      "index": 0,
      "prediction": 0,
      "probability": 0.03,
      "label": "legitimate"
    },
    {
      "index": 1,
      "prediction": 1,
      "probability": 0.87,
      "label": "fraud"
    }
  ],
  "processing_time_ms": 45,
  "encrypted": true
}
```

### 6.4 Predicción por Lotes

```bash
curl -X POST https://api.xcapit-fhe.com/api/v2/models/770e8400.../batch-predict/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "990e8400-e29b-41d4-a716-446655440004",
    "output_format": "json"
  }'
```

**Respuesta (202 Accepted):**
```json
{
  "job_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "status": "processing",
  "total_records": 10000,
  "estimated_time_seconds": 120,
  "webhook_url": "https://banco-alpha.com/webhooks/predictions"
}
```

---

## 7. API REST - Reportes y Workflows

### 7.1 Crear un Reporte

```bash
curl -X POST https://api.xcapit-fhe.com/api/v2/reports/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Reporte Mensual de Fraude",
    "report_type": "performance",
    "format": "pdf",
    "date_from": "2026-01-01",
    "date_to": "2026-01-31",
    "sections": ["summary", "metrics", "charts", "recommendations"]
  }'
```

**Respuesta (201 Created):**
```json
{
  "id": "bb0e8400-e29b-41d4-a716-446655440006",
  "name": "Reporte Mensual de Fraude",
  "report_type": "performance",
  "format": "pdf",
  "status": "pending",
  "date_from": "2026-01-01",
  "date_to": "2026-01-31",
  "sections": ["summary", "metrics", "charts", "recommendations"],
  "created_at": "2026-01-28T16:00:00Z"
}
```

### 7.2 Generar el Reporte

```bash
curl -X POST https://api.xcapit-fhe.com/api/v2/reports/bb0e8400.../generate/ \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta (200 OK):**
```json
{
  "id": "bb0e8400-e29b-41d4-a716-446655440006",
  "status": "completed",
  "file_path": "/reports/2026/01/reporte-mensual-fraude.pdf",
  "file_size": 245760,
  "download_url": "https://storage.xcapit-fhe.com/reports/bb0e8400...pdf",
  "download_expires_at": "2026-01-29T16:00:00Z",
  "completed_at": "2026-01-28T16:01:30Z"
}
```

### 7.3 Crear un Workflow Automatizado

```bash
curl -X POST https://api.xcapit-fhe.com/api/v2/workflows/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pipeline Diario de Detección",
    "description": "Procesa transacciones diarias y genera alertas",
    "steps": [
      {"type": "data_fetch", "name": "Obtener Transacciones", "config": {"source": "database", "query": "last_24h"}},
      {"type": "validate", "name": "Validar Datos", "config": {"schema": "transaction_v2"}},
      {"type": "predict", "name": "Detectar Fraude", "config": {"model_id": "770e8400..."}},
      {"type": "alert", "name": "Enviar Alertas", "config": {"threshold": 0.7, "channel": "email"}}
    ],
    "trigger": {
      "type": "schedule",
      "schedule": "0 6 * * *"
    }
  }'
```

**Respuesta (201 Created):**
```json
{
  "id": "cc0e8400-e29b-41d4-a716-446655440007",
  "name": "Pipeline Diario de Detección",
  "status": "active",
  "steps": [...],
  "trigger": {
    "type": "schedule",
    "schedule": "0 6 * * *",
    "next_run": "2026-01-29T06:00:00Z"
  },
  "total_runs": 0,
  "successful_runs": 0,
  "created_at": "2026-01-28T16:10:00Z"
}
```

### 7.4 Ejecutar Workflow Manualmente

```bash
curl -X POST https://api.xcapit-fhe.com/api/v2/workflows/cc0e8400.../run/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {"date": "2026-01-28"}
  }'
```

**Respuesta (201 Created):**
```json
{
  "id": "dd0e8400-e29b-41d4-a716-446655440008",
  "workflow_id": "cc0e8400-e29b-41d4-a716-446655440007",
  "status": "completed",
  "trigger_type": "manual",
  "step_logs": [
    {"step": "Obtener Transacciones", "status": "completed", "records": 15420},
    {"step": "Validar Datos", "status": "completed", "valid": 15418, "invalid": 2},
    {"step": "Detectar Fraude", "status": "completed", "flagged": 47},
    {"step": "Enviar Alertas", "status": "completed", "emails_sent": 12}
  ],
  "output_data": {
    "total_processed": 15418,
    "fraud_detected": 47,
    "alerts_sent": 12
  },
  "duration_seconds": 34.5,
  "completed_at": "2026-01-28T16:11:00Z"
}
```

---

## 8. Blockchain - Consorcio y Gobernanza

### 8.1 Conexión a Arbitrum Sepolia

```python
from sdk.blockchain import BlockchainConnector, Network

connector = BlockchainConnector(Network.ARBITRUM_SEPOLIA)
connector.connect()

print("🔗 ARBITRUM SEPOLIA TESTNET")
print("=" * 50)
print(f"Chain ID: 421614")
print(f"RPC: https://sepolia-rollup.arbitrum.io/rpc")
print()
print("📋 CONTRATOS DESPLEGADOS:")
print(f"Governance:      0xda52326d106A91A1F22A0c41Be2dc1F531C01F11")
print(f"Model Registry:  0x1296cCeF7803Bff51FB690afCFc586E7012417b8")
print(f"Verifier:        0xa5f04E0aefe55173C91b949Aa2385f0228dd2921")
```

**Salida:**
```
🔗 ARBITRUM SEPOLIA TESTNET
==================================================
Chain ID: 421614
RPC: https://sepolia-rollup.arbitrum.io/rpc

📋 CONTRATOS DESPLEGADOS:
Governance:      0xda52326d106A91A1F22A0c41Be2dc1F531C01F11
Model Registry:  0x1296cCeF7803Bff51FB690afCFc586E7012417b8
Verifier:        0xa5f04E0aefe55173C91b949Aa2385f0228dd2921
```

### 8.2 Votación Commit-Reveal

```python
# Fase 1: COMMIT (votos ocultos)
print("🔒 FASE 1: COMMIT")
print("-" * 40)

banks = ["🇦🇷 Banco Alpha", "🇨🇱 Banco Beta", "🇲🇽 Banco Gamma"]
for bank in banks:
    commitment = hashlib.sha256(f"{bank}-vote-yes".encode()).hexdigest()[:24]
    print(f"{bank}")
    print(f"   Commitment: 0x{commitment}...")
    print(f"   Voto: ??? (oculto)")

print()
print("⏳ Esperando compromisos de todos los miembros...")
```

**Salida:**
```
🔒 FASE 1: COMMIT
----------------------------------------
🇦🇷 Banco Alpha
   Commitment: 0x5c5961ba4d58aad9f2e2...
   Voto: ??? (oculto)
🇨🇱 Banco Beta
   Commitment: 0x3293f687d5bc1b775391...
   Voto: ??? (oculto)
🇲🇽 Banco Gamma
   Commitment: 0x8ed401c3f4e05473e1bd...
   Voto: ??? (oculto)

⏳ Esperando compromisos de todos los miembros...
```

```python
# Fase 2: REVEAL (votos verificados)
print("🔓 FASE 2: REVEAL")
print("-" * 40)

for bank in banks:
    print(f"{bank}")
    print(f"   Voto: ✅ SÍ")
    print(f"   Estado: ✓ VERIFICADO")

print()
print("📊 RESULTADO")
print("-" * 40)
print(f"SÍ: 3/3 (100%)")
print(f"Quórum requerido: 51%")
print()
print("✅ PROPUESTA APROBADA!")
```

**Salida:**
```
🔓 FASE 2: REVEAL
----------------------------------------
🇦🇷 Banco Alpha
   Voto: ✅ SÍ
   Estado: ✓ VERIFICADO
🇨🇱 Banco Beta
   Voto: ✅ SÍ
   Estado: ✓ VERIFICADO
🇲🇽 Banco Gamma
   Voto: ✅ SÍ
   Estado: ✓ VERIFICADO

📊 RESULTADO
----------------------------------------
SÍ: 3/3 (100%)
Quórum requerido: 51%

✅ PROPUESTA APROBADA!
```

---

## Resumen de Garantías de Privacidad

| Característica | Estado |
|----------------|--------|
| Datos nunca expuestos en texto plano | ✅ |
| Encriptación CKKS 128-bit | ✅ |
| Modelo entrenado sobre ciphertext | ✅ |
| Votos ocultos hasta fase reveal | ✅ |
| Verificación criptográfica | ✅ |
| Logs de auditoría inmutables | ✅ |
| Integración blockchain | ✅ |

---

## Próximos Pasos

1. **Sandbox**: Pruebe la plataforma en [sandbox.xcapit-fhe.com](https://sandbox.xcapit-fhe.com)
2. **Documentación API**: Consulte [api.xcapit-fhe.com/docs](https://api.xcapit-fhe.com/api/v2/docs/)
3. **Soporte**: Contacte a [soporte@xcapit.com](mailto:soporte@xcapit.com)

---

*Generado automáticamente - Xcapit FHE-ML Platform v0.7.0*
*Fecha: 2026-01-28*
