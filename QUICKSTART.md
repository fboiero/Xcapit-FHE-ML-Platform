# Xcapit Privacy — Guia de Inicio Rapido

> Levanta la plataforma completa en minutos. Elige el modo que mejor se adapte a tu caso.

---

## Requisitos Previos

| Herramienta | Version Minima | Para que se usa |
|-------------|---------------|-----------------|
| **Python** | 3.11+ | Backend API y SDK |
| **Docker** | 24+ | Despliegue con contenedores |
| **Node.js** | 18+ | Dashboard (opcional en desarrollo) |
| **Make** | cualquiera | Comandos simplificados |

Verifica tus versiones:

```bash
python3 --version   # Python 3.11+
docker --version    # Docker 24+
node --version      # Node 18+ (opcional)
make --version      # GNU Make
```

---

## Opcion 1 — Desarrollo Local (sin Docker)

**Ideal para**: desarrolladores que quieren iterar rapido sobre el backend.

```bash
# 1. Clonar el repositorio
git clone https://github.com/xcapit/Xcapit-FHE-ML-Platform.git
cd Xcapit-FHE-ML-Platform

# 2. Setup automatico
make setup

# 3. Levantar el backend
make dev-local
```

**Resultado**: API corriendo en `http://localhost:8000`

```
Servicios disponibles:
  API REST      →  http://localhost:8000/api/v2/
  Health Check  →  http://localhost:8000/health/
  Admin         →  http://localhost:8000/admin/
```

Para levantar tambien el dashboard (en otra terminal):

```bash
make dashboard-dev
# Dashboard en http://localhost:5173
```

---

## Opcion 2 — Desarrollo con Docker (recomendado)

**Ideal para**: equipos que quieren levantar todo con un solo comando.

```bash
# 1. Clonar y configurar
git clone https://github.com/xcapit/Xcapit-FHE-ML-Platform.git
cd Xcapit-FHE-ML-Platform

# 2. Un solo comando
./scripts/quickstart.sh docker
```

O usando Make:

```bash
make dev
```

**Resultado**: toda la plataforma corriendo en Docker.

```
Servicios:
  API REST      →  http://localhost:8000/api/v2/
  Dashboard     →  http://localhost:3000
  Health Check  →  http://localhost:8000/health/
  PostgreSQL    →  localhost:5432
  Redis         →  localhost:6379
  OpenBao       →  http://localhost:8200
```

**Que se levanta:**

| Servicio | Puerto | Descripcion |
|----------|--------|-------------|
| Django API | 8000 | REST API con 391 endpoints |
| Dashboard | 3000 | Interfaz web React |
| PostgreSQL | 5432 | Base de datos |
| Redis | 6379 | Cache y cola de tareas |
| OpenBao | 8200 | Gestion de secretos |

---

## Opcion 3 — Produccion

**Ideal para**: despliegue real con seguridad completa.

### Paso 1: Generar secretos

```bash
make generate-secrets
```

Esto genera valores para copiar a tu `.env`:

```
DJANGO_SECRET_KEY=a1b2c3...
POSTGRES_PASSWORD=d4e5f6...
REDIS_PASSWORD=g7h8i9...
JWT_SIGNING_KEY=j0k1l2...
FIELD_ENCRYPTION_KEY=m3n4o5...
```

### Paso 2: Configurar .env

```bash
cp .env.example .env
# Editar .env con los secretos generados y tu configuracion:
nano .env
```

Variables **obligatorias** en produccion:

| Variable | Descripcion |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Clave secreta Django (min 50 caracteres) |
| `POSTGRES_PASSWORD` | Password de PostgreSQL |
| `REDIS_PASSWORD` | Password de Redis |
| `DJANGO_ALLOWED_HOSTS` | Dominios permitidos (ej: `apifhe.tudominio.com`) |
| `CORS_ALLOWED_ORIGINS` | Origenes CORS (ej: `https://app.tudominio.com`) |
| `CSRF_TRUSTED_ORIGINS` | Origenes CSRF confiables |

### Paso 3: Desplegar

```bash
make prod
```

O con el script:

```bash
./scripts/quickstart.sh prod
```

**Servicios en produccion:**

| Servicio | Replicas | Recursos |
|----------|----------|----------|
| Django + Gunicorn | 1 (4 workers) | 2 CPU / 2GB RAM |
| Celery Worker | 1 (4 concurrent) | 1 CPU / 1GB RAM |
| Celery Beat | 1 | 0.25 CPU / 256MB RAM |
| PostgreSQL 16 | 1 | 1 CPU / 1GB RAM |
| Redis 7 | 1 | 0.5 CPU / 512MB RAM |
| Dashboard (Nginx) | 1 | 0.25 CPU / 128MB RAM |
| OpenBao (Vault) | 1 | 0.5 CPU / 512MB RAM |

### Paso 4: Verificar

```bash
make health    # Health check de la API
make status    # Estado de todos los servicios
```

---

## Comandos Utiles

| Comando | Que hace |
|---------|----------|
| `make setup` | Configuracion inicial (primera vez) |
| `make dev` | Desarrollo con Docker |
| `make dev-local` | Desarrollo sin Docker |
| `make prod` | Produccion |
| `make test` | Ejecutar tests (2,000+) |
| `make coverage` | Tests + reporte de cobertura |
| `make logs` | Ver logs en tiempo real |
| `make status` | Estado de servicios |
| `make health` | Health check de la API |
| `make stop` | Detener todo |
| `make lint` | Verificar estilo de codigo |
| `make lint-fix` | Corregir estilo automaticamente |
| `make db-migrate` | Ejecutar migraciones |
| `make generate-secrets` | Generar secretos para produccion |
| `make help` | Ver todos los comandos |

---

## Estructura del Proyecto

```
Xcapit-FHE-ML-Platform/
├── backend_django/          # API REST (Django 5.2 + DRF)
│   ├── apps/                # 13 aplicaciones Django
│   │   ├── authentication/  #   JWT + API Keys
│   │   ├── consortiums/     #   Consorcios de datos
│   │   ├── fhe/             #   Cifrado homomorfico
│   │   ├── blockchain/      #   Integracion Arbitrum
│   │   ├── governance/      #   Votacion y propuestas
│   │   ├── federated/       #   Aprendizaje federado
│   │   ├── crypto/          #   ZKP + MPC
│   │   ├── privacy/         #   Privacidad diferencial
│   │   └── ...              #   marketplace, compliance, etc.
│   ├── config/              # Configuracion Django
│   └── tests/               # 1,496+ tests
│
├── dashboard/               # Frontend React 18 + Vite
│   ├── src/
│   │   ├── components/      # Componentes reutilizables
│   │   ├── pages/           # 45+ paginas
│   │   └── api/             # Cliente API
│   └── Dockerfile           # Build multi-stage
│
├── sdk/                     # SDK Python (pip install)
│   ├── encryption/          # FHE (TenSEAL CKKS)
│   ├── blockchain/          # Web3 + contratos
│   ├── zkp/                 # Zero-Knowledge Proofs
│   └── cli/                 # Herramienta CLI
│
├── contracts/               # Smart Contracts Solidity
│   └── src/                 # 3 contratos v2
│
├── deploy/                  # Configuraciones de despliegue
│   ├── aws/                 # ECS/ECR
│   ├── nginx/               # Proxy reverso
│   └── openbao/             # Gestion de secretos
│
├── docs/                    # 45+ archivos de documentacion
├── docker-compose.yml       # Orquestacion de servicios
├── docker-compose.prod.yml  # Overrides de produccion
├── Makefile                 # Punto de entrada unico
└── scripts/quickstart.sh    # Setup automatico
```

---

## Verificar que Todo Funciona

### Tests

```bash
make test
# Resultado esperado: 2,000+ tests passing
```

### Coverage

```bash
make coverage
# Resultado esperado: 94%+ cobertura
```

### Health Check

```bash
curl http://localhost:8000/health/
# {"status": "healthy", ...}
```

### API Docs

Abre en tu navegador: `http://localhost:8000/api/v2/`

---

## Primeros Pasos con la API

### 1. Registrar un usuario

```bash
curl -X POST http://localhost:8000/api/v2/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@empresa.com",
    "password": "SecureP@ss123!",
    "first_name": "Admin",
    "last_name": "User",
    "company_name": "Mi Empresa"
  }'
```

### 2. Obtener token JWT

```bash
curl -X POST http://localhost:8000/api/v2/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@empresa.com",
    "password": "SecureP@ss123!"
  }'
# Respuesta: {"access": "eyJ...", "refresh": "eyJ..."}
```

### 3. Crear un consorcio

```bash
curl -X POST http://localhost:8000/api/v2/consortiums/ \
  -H "Authorization: Bearer <tu-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Consorcio Financiero",
    "description": "Analisis conjunto de riesgo crediticio",
    "max_members": 5
  }'
```

### 4. Usar el SDK

```python
from sdk import XcapitClient

client = XcapitClient(
    base_url="http://localhost:8000",
    api_key="tu-api-key"
)

# Crear modelo con cifrado FHE
model = client.models.create(
    name="credit-risk",
    model_type="logistic_regression",
    encryption="ckks_128"
)

# Cifrar y enviar datos
encrypted_data = client.fhe.encrypt(my_data)
client.models.train(model.id, encrypted_data)
```

---

## Soporte

| Recurso | Enlace |
|---------|--------|
| Documentacion completa | `docs/` |
| Manual de usuario | `docs/USER_MANUAL.md` |
| Guia de despliegue | `docs/DEPLOYMENT.md` |
| Arquitectura tecnica | `docs/TECHNICAL_ARCHITECTURE.md` |
| Runbook de operaciones | `docs/OPERATIONS_RUNBOOK.md` |
| Issues | [GitHub Issues](https://github.com/xcapit/Xcapit-FHE-ML-Platform/issues) |

---

## Troubleshooting

### Docker no inicia

```bash
# Verificar que Docker esta corriendo
docker info

# Limpiar y reiniciar
make stop
make docker-clean
make dev
```

### Error de migraciones

```bash
# Ejecutar migraciones manualmente
make db-migrate
```

### Puerto en uso

```bash
# Ver que usa el puerto 8000
lsof -i :8000

# Detener servicios existentes
make stop
```

### Tests fallan

```bash
# Ejecutar con mas detalle
make test-verbose

# Verificar que el entorno esta limpio
make clean
make test
```
