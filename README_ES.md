# Xcapit FHE-ML Platform

Plataforma de machine learning con preservacion de privacidad usando Cifrado Totalmente Homomorfico (FHE).

[![CI](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml)
[![CodeQL](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6.svg)](https://www.typescriptlang.org/)
[![Licencia: AGPL v3](https://img.shields.io/badge/Licencia-AGPL%20v3-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-566%20pasando-brightgreen.svg)](#testing)
[![Auditoria de Seguridad](https://img.shields.io/badge/seguridad-auditado-blue.svg)](docs/SECURITY_AUDIT_REPORT.md)
[![PRs Bienvenidos](https://img.shields.io/badge/PRs-bienvenidos-brightgreen.svg)](CONTRIBUTING.md)
[![DCO](https://img.shields.io/badge/DCO-requerido-blue.svg)](DCO)

[English Version](README.md)

## Descripcion General

Xcapit FHE-ML permite el aprendizaje automatico sobre datos cifrados. Entrena modelos y realiza predicciones sin exponer nunca los datos subyacentes - perfecto para salud, finanzas y cualquier aplicacion con datos sensibles.

```python
from sdk import FHEModel, SecureDataLoader, FHEContextManager

# Configurar cifrado
context = FHEContextManager()
context.generate_context(poly_modulus_degree=8192)

# Cifrar datos
loader = SecureDataLoader(context)
encrypted_data = loader.encrypt_dataset(X, y)

# Entrenar sobre datos cifrados
model = FHEModel.LogisticRegression()
model.fit(encrypted_data)

# Predecir sobre entradas cifradas
predictions = model.predict(encrypted_test)
```

## Caracteristicas Principales

- **4 Modelos ML**: LinearRegression, LogisticRegression, DecisionTree, KMeans
- **Cifrado CKKS**: Niveles de seguridad 128/192/256-bit con motor FHE optimizado
- **Auditoria Blockchain**: Integracion con Arbitrum para verificacion de modelos y gobernanza
- **Aprendizaje Multi-Parte**: Aprendizaje federado basado en consorcios con seguimiento de contribuciones
- **API REST**: Servidor FastAPI con documentacion OpenAPI 3.1
- **SDK TypeScript**: SDK completo para aplicaciones web
- **Herramienta CLI**: Interfaz de linea de comandos para todas las operaciones
- **Docker Ready**: Builds multi-etapa para dev/prod/fhe
- **Cumplimiento**: Verificacion integrada de GDPR, HIPAA, SOC2, PCI-DSS

## Demo en Vivo

Prueba la plataforma en vivo en **[https://xcapit-privacy.vercel.app](https://xcapit-privacy.vercel.app)**

El dashboard incluye:
- **Demos Interactivas**: Observa el cifrado FHE y colaboracion ML multi-parte
- **Dashboard de Gobernanza**: Trazabilidad blockchain, sistema de votacion, seguimiento de contribuciones
- **Dashboard de Cumplimiento**: Verificacion regulatoria automatizada
- **Puntuacion de Calidad de Datos**: Metricas de calidad sin acceder a los datos subyacentes
- **Soporte Multi-idioma**: Espanol e Ingles

## Instalacion

### SDK Python

```bash
# Instalacion basica
pip install xcapit-fhe-ml

# Con soporte API
pip install xcapit-fhe-ml[api]

# Con soporte FHE (TenSEAL)
pip install xcapit-fhe-ml tenseal

# Desarrollo
pip install xcapit-fhe-ml[dev]
```

### SDK TypeScript

```bash
npm install @xcapit/fhe-ml-sdk
# o
yarn add @xcapit/fhe-ml-sdk
```

## Inicio Rapido

### SDK Python

```python
from sdk import (
    LinearRegression,
    LogisticRegression,
    DecisionTreeClassifier,
    KMeans,
    ModelConfig,
)

# Configurar y entrenar
config = ModelConfig(learning_rate=0.1, n_epochs=100)
model = LinearRegression(config=config)
model._fit_plaintext(X_train, y_train)

# Evaluar
predictions = model._predict_plaintext(X_test)
```

### SDK TypeScript

```typescript
import { createClient, ModelType } from '@xcapit/fhe-ml-sdk';

const client = createClient({
  apiUrl: 'https://api.xcapit.io',
  apiKey: process.env.XCAPIT_API_KEY,
});

// Crear un modelo
const model = await client.models.create({
  name: 'Modelo de Credit Scoring',
  type: ModelType.LogisticRegression,
});

// Entrenar el modelo
const result = await client.models.train({
  modelId: model.id,
  encryptedData: myEncryptedTrainingData,
  epochs: 100,
});

// Hacer predicciones
const prediction = await client.predictions.predict({
  modelId: model.id,
  encryptedInput: encryptedFeatures,
});
```

### Uso del CLI

```bash
# Inicializar contexto FHE
xcapit-fhe init --output ./workspace

# Cifrar datos
xcapit-fhe encrypt -i data.csv -o encrypted.bin -t target_column

# Entrenar modelo
xcapit-fhe train -m logistic-regression -d encrypted.bin -o model.bin

# Predecir
xcapit-fhe predict -m model.bin -i test_encrypted.bin -o predictions.npy
```

### API REST

```bash
# Iniciar servidor
uvicorn sdk.api.server:app --reload

# O con Docker
docker-compose up api
```

```bash
# Crear modelo
curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{"model_type": "logistic_regression"}'

# Entrenar
curl -X POST http://localhost:8000/models/{model_id}/train \
  -H "Content-Type: application/json" \
  -d '{"X": [[1,2,3], [4,5,6]], "y": [0, 1]}'

# Predecir
curl -X POST http://localhost:8000/models/{model_id}/predict \
  -H "Content-Type: application/json" \
  -d '{"X": [[1,2,3]]}'
```

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Plataforma Xcapit FHE-ML                         │
├─────────────────────────────────────────────────────────────────────────┤
│   CLI (xcapit-fhe)  │  API REST (FastAPI)  │  SDK TypeScript  │ Python │
├─────────────────────────────────────────────────────────────────────────┤
│                           Modelos ML                                     │
│    LinearRegression │ LogisticRegression │ DecisionTree │ KMeans        │
├─────────────────────────────────────────────────────────────────────────┤
│                       Motor FHE Optimizado                               │
│   CKKS (TenSEAL) │ Pool de Contextos │ Batch Paralelo │ Eval. Perezosa  │
├─────────────────────────────────────────────────────────────────────────┤
│                      Integracion Blockchain                              │
│  ModelRegistry │ ComputationVerifier │ ConsortiumGovernance (Arbitrum)  │
├─────────────────────────────────────────────────────────────────────────┤
│                        Capa de Cumplimiento                              │
│              GDPR │ HIPAA │ SOC2 │ PCI-DSS │ LGPD                        │
└─────────────────────────────────────────────────────────────────────────┘
```

## Modelos

| Modelo | Tarea | Compatible FHE | Estado |
|--------|-------|----------------|--------|
| LinearRegression | Regresion | ✅ | Produccion |
| LogisticRegression | Clasificacion Binaria | ✅ | Produccion |
| DecisionTreeClassifier | Clasificacion | ✅ | Produccion |
| DecisionTreeRegressor | Regresion | ✅ | Produccion |
| KMeans | Clustering | ✅ | Produccion |
| MiniBatchKMeans | Clustering a Gran Escala | ✅ | Produccion |

## Documentacion

| Documento | Descripcion |
|-----------|-------------|
| [Referencia API](docs/openapi.yaml) | Especificacion OpenAPI 3.1 |
| [Auditoria de Seguridad](docs/SECURITY_AUDIT_REPORT.md) | Auditoria de seguridad de smart contracts |
| [Inicio Rapido](docs/getting-started.md) | Guia de inicio rapido |
| [Arquitectura](docs/guides/01-architecture.md) | Arquitectura del sistema |
| [Modelos ML](docs/guides/03-ml-models.md) | Documentacion de modelos |
| [Teoria FHE](docs/theory/) | Teoria del cifrado homomorfico |

## Smart Contracts

Contratos V2 listos para produccion con correcciones de seguridad:

| Contrato | Proposito | Caracteristicas |
|----------|-----------|-----------------|
| [ModelRegistryV2](contracts/v2/ModelRegistryV2.sol) | Registro de modelos | Verificadores confiables, checkpoints |
| [ComputationVerifierV2](contracts/v2/ComputationVerifierV2.sol) | Trazabilidad | Pruebas Merkle, verificacion por lotes |
| [ConsortiumGovernanceV2](contracts/v2/ConsortiumGovernanceV2.sol) | Gobernanza multi-parte | Recompensas pull-over-push, proteccion DoS |

```bash
# Desplegar en testnet
export DEPLOYER_PRIVATE_KEY=0x...
python scripts/deploy_contracts.py --network arbitrum-sepolia

# Desplegar en mainnet (despues de auditoria)
python scripts/deploy_contracts.py --network arbitrum-one
```

## Docker

```bash
# API de produccion
docker-compose up api

# Desarrollo con recarga automatica
docker-compose --profile dev up

# Con soporte FHE completo
docker-compose --profile fhe up

# Ejecutar tests
docker-compose --profile test up

# Notebooks Jupyter
docker-compose --profile jupyter up
```

## Testing

```bash
# Ejecutar todos los tests (566 pasando)
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=sdk --cov-report=html

# Categorias especificas de tests
pytest tests/test_models.py -v
pytest tests/test_api/ -v
pytest tests/test_blockchain/ -v
```

## Ejecutar el Dashboard

```bash
cd dashboard
npm install
npm run dev
```

## Benchmarks

```bash
# Ejecutar todos los benchmarks
python benchmarks/benchmark_models.py

# Modelos especificos
python benchmarks/benchmark_models.py --models linear-regression logistic-regression

# Tamanos de dataset personalizados
python benchmarks/benchmark_models.py --sizes 100 500 1000 5000
```

## Seguridad

- **Cifrado**: Esquema CKKS con niveles de seguridad configurables (128/192/256-bit)
- **Gestion de Claves**: Claves publicas/privadas separadas, almacenamiento seguro
- **Trazabilidad**: Verificacion de computaciones basada en blockchain
- **Smart Contracts**: [Auditoria de seguridad completada](docs/SECURITY_AUDIT_REPORT.md) con contratos V2 seguros
- **Cumplimiento**: Preparado para HIPAA, GDPR, SOC2, PCI-DSS, LGPD por diseno

## Estructura del Proyecto

```
xcapit-fhe-ml/
├── sdk/                    # SDK Python
│   ├── models/             # Implementaciones de modelos ML
│   ├── encryption/         # Capa de cifrado FHE
│   ├── api/                # Servidor FastAPI
│   └── blockchain/         # Integracion con smart contracts
├── sdk-typescript/         # SDK TypeScript
│   └── src/
│       ├── client.ts       # Cliente API
│       └── types.ts        # Definiciones de tipos
├── contracts/              # Smart contracts Solidity
│   ├── v2/                 # Contratos V2 seguros
│   └── *.sol               # Contratos originales
├── dashboard/              # Dashboard React
├── docs/                   # Documentacion
├── tests/                  # Suite de tests (566 tests)
├── examples/               # Notebooks Jupyter
└── benchmarks/             # Benchmarks de rendimiento
```

## Contribuir

1. Hacer fork del repositorio
2. Crear una rama de feature
3. Realizar los cambios
4. Ejecutar tests: `pytest tests/ -v`
5. Enviar un pull request

## Licencia

Apache 2.0 - Ver [LICENSE](LICENSE) para detalles.

## Acerca de Xcapit

Construido por el equipo detras de [QuarkID](https://quarkid.org) (3.6M+ usuarios), llevando privacidad de nivel empresarial al machine learning.

---

**Enlaces**: [Documentacion](docs/) | [Ejemplos](examples/) | [Docs API](docs/openapi.yaml) | [Demo en Vivo](https://xcapit-privacy.vercel.app)
