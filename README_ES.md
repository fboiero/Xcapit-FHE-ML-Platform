# Xcapit Privacy — Plataforma de Consorcios de Datos

La plataforma donde las empresas colaboran en datos sin compartirlos. Forma consorcios de datos, entrena modelos ML conjuntos y preserva privacidad total con 4 capas criptograficas: FHE, ZKP, MPC y Privacidad Diferencial.

[![CI](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/ci.yml)
[![CodeQL](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml/badge.svg)](https://github.com/xcapit/Xcapit-FHE-ML-Platform/actions/workflows/codeql.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/Django-5.2%20LTS-green.svg)](https://www.djangoproject.com/)
[![Licencia: AGPL v3](https://img.shields.io/badge/Licencia-AGPL%20v3-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-2,116%20pasando-brightgreen.svg)](#testing)
[![Cobertura](https://img.shields.io/badge/cobertura-96.23%25-brightgreen.svg)](#testing)
[![Auditoria](https://img.shields.io/badge/seguridad-auditado-blue.svg)](docs/SECURITY_AUDIT_REPORT.md)

[English Version](README.md)

## Descripcion General

Xcapit Privacy permite a organizaciones formar consorcios de datos donde multiples empresas entrenan modelos ML conjuntos sin exponer sus datos entre si. Con 4 capas criptograficas, la plataforma garantiza privacidad durante todo el ciclo de vida — desde la contribucion de datos hasta el entrenamiento y la prediccion.

```python
from sdk import CKKSEncryptor, CKKSParameters, SecurityLevel

# Configurar cifrado
params = CKKSParameters(
    poly_modulus_degree=8192,
    security_level=SecurityLevel.BITS_128,
)

# Cifrar datos
encryptor = CKKSEncryptor(params)
encrypted = encryptor.encrypt_vector([1.0, 2.0, 3.0])

# Computar sobre datos cifrados (sin descifrar)
result = encrypted + encrypted   # Suma homomorfica
result = encrypted * 2.5         # Multiplicacion escalar
```

## 4 Capas Criptograficas de Privacidad

| Capa | Tecnologia | Funcion |
|------|-----------|---------|
| **FHE** | TenSEAL CKKS (128/192/256-bit) | Computar sobre datos cifrados sin descifrarlos |
| **ZKP** | Pedersen/Schnorr | Probar propiedades sin revelar los datos |
| **MPC** | Shamir/Pairwise Masking | Computacion multi-parte sin centralizar datos |
| **DP** | Laplace/Gaussian/Renyi | Ruido calibrado para privacidad diferencial |

## Caracteristicas Principales

- **Consorcios de Datos**: Colaboracion multi-parte con gobernanza, votacion y seguimiento de contribuciones
- **24+ Modelos ML**: LinearRegression, LogisticRegression, DecisionTree, KMeans, RandomForest, SVM, NeuralNetwork y mas
- **Gobernanza Blockchain**: Smart contracts en Arbitrum para auditoria, propuestas y verificacion
- **Cumplimiento**: GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001 con verificacion automatizada
- **API REST**: Django REST Framework con 391 endpoints y documentacion OpenAPI 3.0
- **Dashboard**: React 18 + Vite 5 con 45+ paginas, bilingue (ES/EN)
- **CLI**: Interfaz de linea de comandos para todas las operaciones
- **Docker**: Builds multi-etapa para dev/prod con health checks
- **Sandbox/Freemium**: Prueba sin registro, 4 niveles de suscripcion

## Demo en Vivo

Prueba la plataforma en **[https://xcapit-privacy.vercel.app](https://xcapit-privacy.vercel.app)**

## Inicio Rapido

### Backend (Django)

```bash
cd backend_django
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Dashboard (React)

```bash
cd dashboard && npm install && npm run dev
```

### SDK

```bash
pip install xcapit-fhe-ml          # Basico
pip install xcapit-fhe-ml tenseal  # Con FHE
pip install xcapit-fhe-ml web3     # Con blockchain
```

### Docker

```bash
docker compose --profile dev up
```

### CLI

```bash
xcapit-fhe init --output ./workspace
xcapit-fhe encrypt -i datos.csv -o cifrado.bin -t columna_target
xcapit-fhe train -m logistic-regression -d cifrado.bin -o modelo.bin
xcapit-fhe predict -m modelo.bin -i test_cifrado.bin -o predicciones.npy
```

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────────────┐
│              Xcapit Privacy — Plataforma de Consorcios de Datos          │
├──────────────────────────────────────────────────────────────────────────┤
│  Dashboard (React)  │  API REST (Django)  │  SDK (Python)  │  CLI       │
├──────────────────────────────────────────────────────────────────────────┤
│                   4 Capas Criptograficas de Privacidad                   │
│   FHE (CKKS)  │  ZKP (Pedersen/Schnorr)  │  MPC (Shamir)  │  DP        │
├──────────────────────────────────────────────────────────────────────────┤
│                            24+ Modelos ML                                │
│  Linear │ Logistic │ DecisionTree │ KMeans │ RF │ SVM │ NN │ Ensemble   │
├──────────────────────────────────────────────────────────────────────────┤
│                    Integracion Blockchain (Arbitrum)                     │
│  ModelRegistry │ ComputationVerifier │ ConsortiumGovernance             │
├──────────────────────────────────────────────────────────────────────────┤
│                      Cumplimiento & Gobernanza                          │
│   GDPR │ HIPAA │ SOC2 │ PCI-DSS │ ISO 27001 │ Votacion │ Auditoria    │
└──────────────────────────────────────────────────────────────────────────┘
```

## Modulos de la Plataforma

| Modulo | Caracteristicas |
|--------|----------------|
| **Core** | Gestion de empresas, auth JWT, API keys, auditoria, webhooks |
| **Consorcios** | CRUD, membresia, invitaciones, pruebas de contribucion |
| **Gobernanza** | Propuestas, votacion ponderada, cadena de auditoria, recompensas |
| **Cumplimiento** | Frameworks GDPR/HIPAA/SOC2/PCI-DSS con verificaciones automaticas |
| **Calidad de Datos** | Evaluaciones, reglas de validacion, alertas, dashboard |
| **Marketplace** | Catalogo de modelos, despliegues, resenas |
| **Sandbox** | Ambientes de prueba, datasets sinteticos, experimentos, demos |
| **Federado** | Endpoints de inferencia, nodos edge, despliegue de modelos |
| **Explicabilidad** | Valores SHAP, importancia de features, decision paths |
| **Insights Competitivos** | Benchmarks de industria, analisis de tendencias |
| **Ensemble** | Modelos multi-modelo (voting, averaging, weighted, stacking) |
| **Blockchain** | Transacciones Arbitrum, smart contracts, verificacion on-chain |

## Planes y Precios

| Caracteristica | Free | Starter | Professional | Enterprise |
|---------------|:----:|:-------:|:------------:|:----------:|
| Rate limit | 10/min | 100/min | 500/min | 2,000/min |
| Peticiones/dia | 100 | 5,000 | 50,000 | Ilimitado |
| Modelos | 2 | 10 | 50 | Ilimitado |
| Consorcios | 1 | 5 | 20 | Ilimitado |
| Subida datos | 50 MB | 1 GB | 10 GB | Ilimitado |

## Testing

```bash
# Tests backend (1,496+ pasando, 96.23% cobertura)
cd backend_django
DJANGO_SETTINGS_MODULE=config.settings_test pytest --cov=apps --cov-fail-under=90

# Tests SDK (620+ pasando)
pytest sdk/tests/ -v

# Tests de seguridad (27 pasando)
pytest tests/test_security_idor.py -v
```

## Documentacion

| Documento | Descripcion |
|-----------|-------------|
| [Manual de Usuario](docs/USER_MANUAL.md) | Manual completo (ES) |
| [Release Notes RC1](docs/RELEASE_NOTES_RC1.md) | Notas de version RC1 |
| [Referencia API](docs/openapi.yaml) | Especificacion OpenAPI 3.0 |
| [Auditoria de Seguridad](docs/SECURITY_AUDIT_REPORT.md) | Reporte de auditoria |
| [Arquitectura](docs/guides/01-architecture.md) | Arquitectura del sistema |
| [Teoria FHE](docs/theory/) | Teoria del cifrado homomorfico (4 capitulos) |
| [Guia de Onboarding](docs/ONBOARDING_PASO_A_PASO.md) | Onboarding paso a paso |
| [ISO 27001](docs/compliance/) | Cumplimiento ISO 27001 |

## Estructura del Proyecto

```
xcapit-fhe-ml/
├── backend_django/         # API REST Django (13 apps, 391 endpoints)
│   ├── apps/               # Aplicaciones Django
│   ├── config/             # Configuracion Django
│   └── tests/              # Tests backend (1,496+)
├── sdk/                    # SDK Python v0.7.0 (24+ modelos, 4 capas crypto)
│   ├── models/             # Implementaciones de modelos ML
│   ├── encryption/         # Capa de cifrado FHE (CKKS/TenSEAL)
│   ├── zkp/                # Pruebas de Conocimiento Cero
│   ├── mpc/                # Computacion Multi-Parte
│   ├── privacy/            # Privacidad Diferencial
│   ├── blockchain/         # Integracion con smart contracts
│   └── cli/                # Interfaz de linea de comandos
├── dashboard/              # Frontend React 18 (45+ paginas, ES/EN)
├── contracts/              # Smart contracts Solidity (Foundry)
│   └── src/v2/             # Contratos V2 seguros
├── docs/                   # Documentacion (43+ archivos)
├── examples/               # Notebooks Jupyter (7)
└── docker-compose.yml      # Setup Docker completo
```

## Contribuir

1. Hacer fork del repositorio
2. Crear una rama de feature
3. Realizar los cambios
4. Ejecutar tests: `pytest --cov=apps`
5. Enviar un pull request

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guias detalladas.

## Licencia

AGPL v3 - Ver [LICENSE](LICENSE) para detalles.

## Acerca de Xcapit

Construido por el equipo detras de [QuarkID](https://quarkid.org) (3.6M+ usuarios), llevando privacidad de nivel empresarial al machine learning.

---

**Enlaces**: [Documentacion](docs/) | [Manual de Usuario](docs/USER_MANUAL.md) | [Ejemplos](examples/) | [API Docs](docs/openapi.yaml) | [Demo en Vivo](https://xcapit-privacy.vercel.app)
