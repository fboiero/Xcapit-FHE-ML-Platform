# Xcapit FHE-ML Platform - Demos por Vertical

Esta carpeta contiene notebooks de demostracion organizados por caso de uso/vertical, cada uno con datasets sinteticos generados especificamente para testing.

## Estructura

```
demos/
├── README.md                           # Este archivo
├── test_datasets.py                    # Generador de datasets sinteticos
├── 01_fintech_fraud_detection.ipynb    # Demo: Deteccion de fraude bancario
├── 02_healthcare_patient_risk.ipynb    # Demo: Prediccion de diabetes T2
├── 03_government_resource_allocation.ipynb  # Demo: Asignacion de recursos
└── test_data/                          # Datasets generados (opcional)
    ├── fintech_fraud_transactions.csv
    ├── healthcare_diabetes_risk.csv
    └── ...
```

## Notebooks Disponibles

### 1. Fintech: Deteccion de Fraude (`01_fintech_fraud_detection.ipynb`)

**Escenario**: Consorcio de 3 bancos latinoamericanos colaboran para detectar fraude sin compartir datos de clientes.

**Features**:
- Generacion de 10,000 transacciones sinteticas
- Encriptacion FHE con CKKS
- Votacion commit-reveal para gobernanza
- Modelo de clasificacion con 94%+ accuracy
- Predicciones en tiempo real

**Organizaciones simuladas**:
- Banco Alpha (Argentina) - 4,000 transacciones
- Banco Beta (Chile) - 3,000 transacciones
- Banco Gamma (Mexico) - 3,000 transacciones

---

### 2. Healthcare: Prediccion de Diabetes (`02_healthcare_patient_risk.ipynb`)

**Escenario**: Consorcio de hospitales para predecir riesgo de diabetes tipo 2 manteniendo privacidad de pacientes (HIPAA compliant).

**Features**:
- 5,000 registros de pacientes (PHI protegida)
- 14 features clinicas (glucosa, HbA1c, BMI, etc.)
- Cumplimiento HIPAA, GDPR, Ley 25.326
- Recomendaciones clinicas automatizadas
- Feature importance para interpretabilidad

**Organizaciones simuladas**:
- Hospital Central (Buenos Aires) - 2,000 pacientes
- Clinica del Norte (Mendoza) - 1,500 pacientes
- Hospital Regional (Cordoba) - 1,500 pacientes

---

### 3. Government: Asignacion de Recursos (`03_government_resource_allocation.ipynb`)

**Escenario**: Consorcio inter-provincial para optimizar asignacion de recursos de servicios publicos.

**Features**:
- 20,000 registros de ciudadanos (anonimizados)
- Segmentacion de poblacion con K-Means
- Prediccion de demanda de servicios
- Optimizacion de presupuesto por provincia
- Dashboard de indicadores

**Organizaciones simuladas**:
- Buenos Aires - 10,000 registros, $500M presupuesto
- Cordoba - 5,000 registros, $250M presupuesto
- Santa Fe - 5,000 registros, $250M presupuesto

---

## Generador de Datasets

El archivo `test_datasets.py` proporciona funciones para generar datasets de testing:

```python
from test_datasets import (
    generate_dataset,
    generate_consortium_split,
    get_sample_data,
    export_all_datasets,
    # Configuraciones pre-definidas
    FINTECH_FRAUD_CONFIG,
    FINTECH_CREDIT_CONFIG,
    HEALTHCARE_DIABETES_CONFIG,
    HEALTHCARE_READMISSION_CONFIG,
    INSURANCE_CLAIMS_CONFIG,
    GOVERNMENT_SERVICES_CONFIG,
    RETAIL_CHURN_CONFIG,
)

# Generar dataset completo
df = generate_dataset(FINTECH_FRAUD_CONFIG)

# Obtener muestra rapida
df_sample = get_sample_data('fintech', n_samples=100)

# Dividir para consorcio
splits = generate_consortium_split(df, n_members=3, member_names=['Bank A', 'Bank B', 'Bank C'])

# Exportar todos los datasets
export_all_datasets(output_dir='test_data')
```

### Datasets Disponibles

| Vertical | Dataset | Samples | Target | Description |
|----------|---------|---------|--------|-------------|
| Fintech | `fintech_fraud_transactions` | 10,000 | `is_fraud` (binary) | Deteccion de fraude |
| Fintech | `fintech_credit_scoring` | 5,000 | `default` (binary) | Credit scoring |
| Healthcare | `healthcare_diabetes_risk` | 5,000 | `has_diabetes` (binary) | Prediccion diabetes |
| Healthcare | `healthcare_readmission` | 8,000 | `readmitted_30d` (binary) | Readmision 30 dias |
| Insurance | `insurance_claims_fraud` | 15,000 | `is_fraudulent` (binary) | Fraude en reclamos |
| Government | `government_service_demand` | 20,000 | `service_demand_score` (regression) | Demanda servicios |
| Retail | `retail_customer_churn` | 10,000 | `churned` (binary) | Churn prediction |

---

## Uso con LLMs/Agentes

Los notebooks estan disenados para ser ejecutables por agentes de IA:

### Para Agentes (Claude, GPT, etc.)

1. **Lectura del notebook**: Cada celda tiene markdown explicativo
2. **Ejecucion secuencial**: Las celdas son independientes y ejecutables en orden
3. **Outputs predecibles**: Metricas y resultados estructurados
4. **Sin dependencias externas**: Todo auto-contenido (excepto SDK)

### Ejemplo de Prompt para Agente

```
Ejecuta el notebook 01_fintech_fraud_detection.ipynb:
1. Carga las librerias
2. Genera el dataset de transacciones
3. Encripta los datos con FHE
4. Entrena el modelo de deteccion de fraude
5. Reporta las metricas (accuracy, AUC-ROC)
6. Ejecuta predicciones sobre nuevas transacciones
```

---

## Integracion con la Plataforma

### SDK (Python)

```python
from sdk.encryption import CKKSEncryptor, SecurityLevel
from sdk.models import LogisticRegression
from sdk.utils import SecureDataLoader

# Cargar dataset generado
loader = SecureDataLoader()
X_enc, y_enc = loader.load_and_encrypt('test_data/fintech_fraud_transactions.csv')

# Entrenar modelo
model = LogisticRegression()
model.fit(X_enc, y_enc)
```

### REST API

```bash
# Crear sandbox
curl -X POST https://apifhe.xcapit.com/api/v2/sandbox/sandboxes/ \
  -H "Authorization: ApiKey $API_KEY" \
  -d '{"name": "Test Fintech", "industry": "finance"}'

# Generar datos
curl -X POST https://apifhe.xcapit.com/api/v2/sandbox/datasets/generate/ \
  -H "Authorization: ApiKey $API_KEY" \
  -d '{"sandbox_id": "...", "dataset_type": "transactions", "record_count": 1000}'
```

### Frontend

1. Ir a https://xcapit-privacy.vercel.app/sandbox-demo
2. Seleccionar vertical (Fintech, Healthcare, etc.)
3. Entrar al Dashboard Demo
4. Crear experimentos con datos generados

---

## Requisitos

```bash
# Python dependencies
pip install numpy pandas scikit-learn

# Para notebooks completos
pip install jupyter matplotlib seaborn

# Para SDK (opcional)
pip install tenseal web3
```

---

## Contribuir

Para agregar un nuevo vertical:

1. Crear `DatasetConfig` en `test_datasets.py`
2. Crear notebook `XX_vertical_usecase.ipynb`
3. Agregar a este README
4. Probar ejecucion completa

---

## Contacto

- **Documentacion API**: https://apifhe.xcapit.com/api/v2/docs/
- **Demo interactiva**: https://xcapit-privacy.vercel.app/sandbox-demo
- **GitHub**: https://github.com/xcapit/fhe-ml-platform
