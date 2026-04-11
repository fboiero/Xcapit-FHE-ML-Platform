#!/usr/bin/env bash
# =============================================================================
# Xcapit FHE-ML Platform — Quick Start
# =============================================================================
#
# Levanta la plataforma completa con un solo comando.
#
# Uso:
#   ./scripts/quickstart.sh          → Desarrollo local (sin Docker)
#   ./scripts/quickstart.sh docker   → Desarrollo con Docker
#   ./scripts/quickstart.sh prod     → Produccion con Docker
#
# =============================================================================

set -euo pipefail

# Colores
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# Directorio raiz del proyecto
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

log()  { echo -e "${CYAN}▶ $1${RESET}"; }
ok()   { echo -e "${GREEN}✓ $1${RESET}"; }
warn() { echo -e "${YELLOW}⚠ $1${RESET}"; }
fail() { echo -e "${RED}✗ $1${RESET}"; exit 1; }

header() {
    echo ""
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BOLD}${CYAN}║        Xcapit FHE-ML Platform — Quick Start             ║${RESET}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""
}

# =============================================================================
# Verificaciones
# =============================================================================

check_deps() {
    log "Verificando dependencias..."

    command -v python3 >/dev/null 2>&1 || fail "Python 3.11+ requerido. Instala desde https://python.org"

    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"; then
        ok "Python $PYTHON_VERSION"
    else
        fail "Python 3.11+ requerido (tienes $PYTHON_VERSION)"
    fi

    if [ "${MODE}" = "docker" ] || [ "${MODE}" = "prod" ]; then
        command -v docker >/dev/null 2>&1 || fail "Docker requerido. Instala desde https://docker.com"
        docker info >/dev/null 2>&1 || fail "Docker no esta corriendo. Inicialo primero."
        ok "Docker disponible"
    fi
}

# =============================================================================
# Setup de entorno
# =============================================================================

setup_env() {
    # Crear .env si no existe
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            warn "Archivo .env creado desde .env.example"
        fi
    fi

    # Para desarrollo local, crear .env del backend
    if [ ! -f backend_django/.env ] && [ -f backend_django/.env.example ]; then
        cp backend_django/.env.example backend_django/.env
    fi
}

# =============================================================================
# Modo: Desarrollo local (sin Docker)
# =============================================================================

start_local() {
    log "Configurando entorno de desarrollo local..."

    # Backend Python
    cd "$ROOT/backend_django"

    if [ ! -d .venv ]; then
        log "Creando virtualenv..."
        python3 -m venv .venv
    fi

    log "Instalando dependencias..."
    . .venv/bin/activate
    pip install -q -r requirements.txt

    log "Ejecutando migraciones..."
    python manage.py migrate --run-syncdb 2>/dev/null

    ok "Backend configurado"

    # Dashboard (si npm disponible)
    if command -v npm >/dev/null 2>&1 && [ -d "$ROOT/dashboard" ]; then
        log "Instalando dependencias del dashboard..."
        cd "$ROOT/dashboard"
        npm install --silent 2>/dev/null
        ok "Dashboard configurado"
    fi

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════${RESET}"
    echo -e "${GREEN}  ✓ Plataforma lista para desarrollo${RESET}"
    echo ""
    echo -e "  ${BOLD}Backend:${RESET}"
    echo -e "    cd backend_django"
    echo -e "    source .venv/bin/activate"
    echo -e "    python manage.py runserver"
    echo -e "    → ${CYAN}http://localhost:8000${RESET}"
    echo ""
    echo -e "  ${BOLD}Dashboard:${RESET}"
    echo -e "    cd dashboard"
    echo -e "    npm run dev"
    echo -e "    → ${CYAN}http://localhost:5173${RESET}"
    echo ""
    echo -e "  ${BOLD}Tests:${RESET}"
    echo -e "    make test"
    echo ""
    echo -e "  ${BOLD}API Docs:${RESET}"
    echo -e "    ${CYAN}http://localhost:8000/api/v2/${RESET}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${RESET}"
}

# =============================================================================
# Modo: Docker desarrollo
# =============================================================================

start_docker() {
    log "Levantando plataforma con Docker..."

    setup_env

    docker compose --profile dev up -d --build

    log "Esperando que los servicios esten listos..."
    sleep 5

    # Esperar health check
    for i in $(seq 1 30); do
        if curl -sf http://localhost:8000/health/ >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done

    if curl -sf http://localhost:8000/health/ >/dev/null 2>&1; then
        ok "API lista"
    else
        warn "API tardando en iniciar — revisa: docker compose logs django-dev"
    fi

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════${RESET}"
    echo -e "${GREEN}  ✓ Plataforma corriendo en Docker${RESET}"
    echo ""
    echo -e "  ${BOLD}Servicios:${RESET}"
    echo -e "    API:       ${CYAN}http://localhost:8000${RESET}"
    echo -e "    API Docs:  ${CYAN}http://localhost:8000/api/v2/${RESET}"
    echo -e "    Health:    ${CYAN}http://localhost:8000/health/${RESET}"
    echo -e "    Postgres:  localhost:5432"
    echo -e "    Redis:     localhost:6379"
    echo ""
    echo -e "  ${BOLD}Comandos utiles:${RESET}"
    echo -e "    make logs      → Ver logs"
    echo -e "    make status    → Estado de servicios"
    echo -e "    make stop      → Detener todo"
    echo -e "    make test      → Ejecutar tests"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${RESET}"
}

# =============================================================================
# Modo: Produccion
# =============================================================================

start_prod() {
    log "Validando entorno de produccion..."

    # Verificar variables criticas
    source .env 2>/dev/null || true

    if [ -z "${DJANGO_SECRET_KEY:-}" ]; then
        fail "DJANGO_SECRET_KEY no configurada. Ejecuta: make generate-secrets"
    fi
    if [ -z "${POSTGRES_PASSWORD:-}" ]; then
        fail "POSTGRES_PASSWORD no configurada. Ejecuta: make generate-secrets"
    fi
    if [ -z "${REDIS_PASSWORD:-}" ]; then
        fail "REDIS_PASSWORD no configurada. Ejecuta: make generate-secrets"
    fi

    ok "Variables de entorno verificadas"

    log "Construyendo imagenes de produccion..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production build

    log "Levantando servicios de produccion..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d

    log "Esperando que los servicios esten listos..."
    sleep 10

    for i in $(seq 1 30); do
        if curl -sf http://localhost:8000/health/ >/dev/null 2>&1; then
            break
        fi
        sleep 3
    done

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════${RESET}"
    echo -e "${GREEN}  ✓ Produccion desplegada${RESET}"
    echo ""
    echo -e "  ${BOLD}Servicios activos:${RESET}"
    echo -e "    Django API + Gunicorn"
    echo -e "    Celery Worker (4 workers)"
    echo -e "    Celery Beat (scheduled tasks)"
    echo -e "    PostgreSQL 16 (optimizado)"
    echo -e "    Redis 7 (LRU + AOF)"
    echo -e "    OpenBao (secret management)"
    echo ""
    echo -e "  ${BOLD}Verificacion:${RESET}"
    echo -e "    make health    → Health check"
    echo -e "    make status    → Estado completo"
    echo -e "    make prod-logs → Logs en tiempo real"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${RESET}"
}

# =============================================================================
# Main
# =============================================================================

MODE="${1:-local}"

header
check_deps

case "$MODE" in
    local)   start_local ;;
    docker)  start_docker ;;
    prod)    start_prod ;;
    *)
        echo "Uso: $0 [local|docker|prod]"
        echo ""
        echo "  local   → Desarrollo sin Docker (default)"
        echo "  docker  → Desarrollo con Docker"
        echo "  prod    → Produccion con Docker"
        exit 1
        ;;
esac
