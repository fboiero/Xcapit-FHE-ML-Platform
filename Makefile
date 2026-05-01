# =============================================================================
# Xcapit FHE-ML Platform — Makefile
# =============================================================================
#
# Punto de entrada unico para todas las operaciones de la plataforma.
#
# Uso rapido:
#   make setup        → Configura todo por primera vez
#   make dev          → Levanta entorno de desarrollo
#   make prod         → Levanta entorno de produccion
#   make test         → Ejecuta tests
#   make status       → Verifica estado de servicios
#   make help         → Muestra todos los comandos
#
# =============================================================================

.PHONY: help setup dev prod stop test lint coverage \
        logs status health clean \
        db-migrate db-shell \
        docker-build docker-clean \
        sdk-test dashboard-dev dashboard-build \
        validate-env generate-secrets

# Colores
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
CYAN   := \033[0;36m
RESET  := \033[0m

# Variables
COMPOSE := docker compose
COMPOSE_DEV := $(COMPOSE) --profile dev
COMPOSE_PROD := $(COMPOSE) -f docker-compose.yml -f docker-compose.prod.yml --profile production
BACKEND := backend_django
DASHBOARD := dashboard
VENV := $(BACKEND)/.venv/bin

# =============================================================================
# AYUDA
# =============================================================================

help: ## Muestra esta ayuda
	@echo ""
	@echo "$(CYAN)╔══════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(CYAN)║     Xcapit FHE-ML Platform — Comandos Disponibles      ║$(RESET)"
	@echo "$(CYAN)╚══════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# SETUP INICIAL
# =============================================================================

setup: ## Configuracion inicial completa (primera vez)
	@echo "$(CYAN)▶ Configurando Xcapit FHE-ML Platform...$(RESET)"
	@echo ""
	@# 1. Verificar dependencias
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)✗ Docker no instalado$(RESET)"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)✗ Python3 no instalado$(RESET)"; exit 1; }
	@echo "$(GREEN)✓ Dependencias verificadas$(RESET)"
	@# 2. Crear .env si no existe
	@if [ ! -f .env ]; then \
		cp .env.example .env 2>/dev/null || true; \
		echo "$(YELLOW)⚠ Archivo .env creado desde .env.example — revisa las variables$(RESET)"; \
	else \
		echo "$(GREEN)✓ Archivo .env existente$(RESET)"; \
	fi
	@# 3. Backend Python
	@echo "$(CYAN)▶ Configurando backend...$(RESET)"
	@cd $(BACKEND) && python3 -m venv .venv 2>/dev/null || true
	@cd $(BACKEND) && . .venv/bin/activate && pip install -q -r requirements.txt
	@echo "$(GREEN)✓ Backend configurado$(RESET)"
	@# 4. Dashboard Node
	@if [ -d $(DASHBOARD) ] && command -v npm >/dev/null 2>&1; then \
		echo "$(CYAN)▶ Configurando dashboard...$(RESET)"; \
		cd $(DASHBOARD) && npm install --silent; \
		echo "$(GREEN)✓ Dashboard configurado$(RESET)"; \
	fi
	@echo ""
	@echo "$(GREEN)═══════════════════════════════════════════$(RESET)"
	@echo "$(GREEN)  ✓ Setup completo. Comandos disponibles:$(RESET)"
	@echo "$(GREEN)    make dev    → Desarrollo local$(RESET)"
	@echo "$(GREEN)    make test   → Ejecutar tests$(RESET)"
	@echo "$(GREEN)    make help   → Ver todos los comandos$(RESET)"
	@echo "$(GREEN)═══════════════════════════════════════════$(RESET)"

generate-secrets: ## Genera secretos para produccion
	@echo "$(CYAN)▶ Generando secretos...$(RESET)"
	@echo ""
	@echo "DJANGO_SECRET_KEY=$$(openssl rand -hex 32)"
	@echo "POSTGRES_PASSWORD=$$(openssl rand -hex 16)"
	@echo "REDIS_PASSWORD=$$(openssl rand -hex 16)"
	@echo "JWT_SIGNING_KEY=$$(openssl rand -hex 32)"
	@echo "FIELD_ENCRYPTION_KEY=$$(openssl rand -base64 32)"
	@echo ""
	@echo "$(YELLOW)⚠ Copia estos valores a tu archivo .env$(RESET)"

validate-env: ## Verifica variables de entorno
	@cd $(BACKEND) && python3 scripts/validate_env.py

# =============================================================================
# DESARROLLO LOCAL
# =============================================================================

dev: ## Levanta entorno de desarrollo completo (Docker)
	@echo "$(CYAN)▶ Levantando entorno de desarrollo...$(RESET)"
	$(COMPOSE_DEV) up -d
	@echo ""
	@echo "$(GREEN)✓ Servicios levantados:$(RESET)"
	@echo "  API:       http://localhost:8000"
	@echo "  API Docs:  http://localhost:8000/api/v2/"
	@echo "  Health:    http://localhost:8000/health/"
	@echo "  Postgres:  localhost:5432"
	@echo "  Redis:     localhost:6379"

dev-local: ## Levanta backend sin Docker (desarrollo rapido)
	@echo "$(CYAN)▶ Levantando backend local...$(RESET)"
	cd $(BACKEND) && . .venv/bin/activate && python manage.py migrate --run-syncdb
	cd $(BACKEND) && . .venv/bin/activate && python manage.py runserver

dashboard-dev: ## Levanta dashboard en modo desarrollo
	@echo "$(CYAN)▶ Levantando dashboard...$(RESET)"
	cd $(DASHBOARD) && npm run dev

dashboard-build: ## Construye dashboard para produccion
	cd $(DASHBOARD) && npm run build
	@echo "$(GREEN)✓ Dashboard compilado en $(DASHBOARD)/dist/$(RESET)"

# =============================================================================
# PRODUCCION
# =============================================================================

prod: validate-env ## Levanta entorno de produccion (Docker)
	@echo "$(CYAN)▶ Levantando entorno de produccion...$(RESET)"
	$(COMPOSE_PROD) up -d
	@echo "$(GREEN)✓ Produccion levantada$(RESET)"

prod-logs: ## Ver logs de produccion
	$(COMPOSE_PROD) logs -f --tail=100

# =============================================================================
# TESTING
# =============================================================================

test: ## Ejecuta todos los tests del backend
	@echo "$(CYAN)▶ Ejecutando tests...$(RESET)"
	cd $(BACKEND) && . .venv/bin/activate && \
		DJANGO_SETTINGS_MODULE=config.settings_test pytest --tb=short -q

test-verbose: ## Ejecuta tests con output detallado
	cd $(BACKEND) && . .venv/bin/activate && \
		DJANGO_SETTINGS_MODULE=config.settings_test pytest -v --tb=long

coverage: ## Ejecuta tests con reporte de cobertura
	@echo "$(CYAN)▶ Ejecutando tests con cobertura...$(RESET)"
	cd $(BACKEND) && . .venv/bin/activate && \
		DJANGO_SETTINGS_MODULE=config.settings_test pytest \
		--cov=apps --cov-config=setup.cfg --cov-fail-under=90 --tb=short -q

test-security: ## Ejecuta tests de seguridad
	cd $(BACKEND) && . .venv/bin/activate && \
		DJANGO_SETTINGS_MODULE=config.settings_test pytest tests/test_security_idor.py -v

sdk-test: ## Ejecuta tests del SDK
	cd sdk && pytest tests/ -v --tb=short

# =============================================================================
# PERFORMANCE TESTING (Locust)
# =============================================================================

perf-install: ## Instala dependencias de perf testing (Locust)
	@echo "$(CYAN)▶ Instalando Locust...$(RESET)"
	cd $(BACKEND) && . .venv/bin/activate && \
		pip install -q -r requirements-perf.txt
	@echo "$(GREEN)✓ Locust instalado$(RESET)"

perf-test-seed: ## Crea usuario de prueba para perf tests
	@echo "$(CYAN)▶ Creando usuario perf@xcapit.test...$(RESET)"
	cd $(BACKEND) && . .venv/bin/activate && \
		DJANGO_SETTINGS_MODULE=config.settings python manage.py shell -c "\
from apps.core.models import User, Company; \
c, _ = Company.objects.get_or_create(name='Xcapit Perf Test', defaults={'email': 'perf@xcapit.test'}); \
u, created = User.objects.get_or_create(email='perf@xcapit.test', defaults={'company': c, 'is_active': True}); \
u.set_password('perf-test-password'); u.save(); \
print('✓ Perf user ready:', u.email)"

perf-test: ## Load test headless (50 users, 3 min) - valida SLOs
	@echo "$(CYAN)▶ Load test (50 users, 3min)...$(RESET)"
	cd $(BACKEND) && . .venv/bin/activate && \
		locust -f tests/performance/locustfile.py \
			--host http://localhost:8000 \
			--users 50 --spawn-rate 5 --run-time 3m \
			--headless --only-summary

perf-test-ui: ## Load test con web UI interactiva (localhost:8089)
	@echo "$(CYAN)▶ Locust UI disponible en http://localhost:8089$(RESET)"
	cd $(BACKEND) && . .venv/bin/activate && \
		locust -f tests/performance/locustfile.py \
			--host http://localhost:8000

perf-test-fhe: ## Stress test específico de FHE (5 users, 10 min)
	@echo "$(CYAN)▶ FHE stress test (5 users, 10min)...$(RESET)"
	cd $(BACKEND) && . .venv/bin/activate && \
		locust -f tests/performance/locustfile.py \
			--host http://localhost:8000 \
			--users 5 --spawn-rate 1 --run-time 10m \
			--headless --only-summary \
			FHEHeavyUser

perf-test-soak: ## Soak test largo (50 users, 2h) - detecta memory leaks
	@echo "$(CYAN)▶ Soak test (50 users, 2h)...$(RESET)"
	cd $(BACKEND) && . .venv/bin/activate && \
		locust -f tests/performance/locustfile.py \
			--host http://localhost:8000 \
			--users 50 --spawn-rate 2 --run-time 2h \
			--headless --only-summary

# =============================================================================
# E2E TESTING (Playwright)
# =============================================================================

e2e-install: ## Instala Playwright y sus browsers
	@echo "$(CYAN)▶ Instalando Playwright...$(RESET)"
	cd $(DASHBOARD) && npm install -D @playwright/test
	cd $(DASHBOARD) && npx playwright install --with-deps chromium
	@echo "$(GREEN)✓ Playwright instalado$(RESET)"

e2e-test: ## E2E tests del dashboard (headless)
	@echo "$(CYAN)▶ E2E tests...$(RESET)"
	cd $(DASHBOARD) && npx playwright test

e2e-test-ui: ## E2E tests con UI mode (interactivo)
	cd $(DASHBOARD) && npx playwright test --ui

e2e-test-debug: ## E2E tests modo debug (headed, inspector)
	cd $(DASHBOARD) && npx playwright test --debug

e2e-test-report: ## Abre el último reporte HTML de E2E
	cd $(DASHBOARD) && npx playwright show-report

# =============================================================================
# API DOCUMENTATION
# =============================================================================

api-schema: ## Genera el schema OpenAPI 3.0 (YAML)
	@echo "$(CYAN)▶ Generando schema OpenAPI...$(RESET)"
	cd $(BACKEND) && . .venv/bin/activate && \
		DJANGO_SETTINGS_MODULE=config.settings python manage.py spectacular \
			--color --file ../docs/api-schema.yaml
	@echo "$(GREEN)✓ Schema generado en docs/api-schema.yaml$(RESET)"

api-schema-json: ## Genera el schema OpenAPI 3.0 (JSON)
	cd $(BACKEND) && . .venv/bin/activate && \
		DJANGO_SETTINGS_MODULE=config.settings python manage.py spectacular \
			--format openapi-json --file ../docs/api-schema.json
	@echo "$(GREEN)✓ Schema JSON generado en docs/api-schema.json$(RESET)"

api-docs: ## Muestra la URL de la documentación interactiva
	@echo ""
	@echo "$(CYAN)╔════════════════════════════════════════════════════════╗$(RESET)"
	@echo "$(CYAN)║     Xcapit FHE-ML Platform — API Documentation       ║$(RESET)"
	@echo "$(CYAN)╚════════════════════════════════════════════════════════╝$(RESET)"
	@echo ""
	@echo "  $(GREEN)Swagger UI$(RESET):  http://localhost:8000/api/v2/docs/"
	@echo "  $(GREEN)ReDoc$(RESET):       http://localhost:8000/api/v2/redoc/"
	@echo "  $(GREEN)Schema YAML$(RESET): http://localhost:8000/api/v2/schema/"
	@echo ""
	@echo "  Requiere: $(YELLOW)make dev$(RESET) o $(YELLOW)make dev-local$(RESET) corriendo"
	@echo ""

api-validate: ## Valida el schema OpenAPI contra la especificación
	@echo "$(CYAN)▶ Validando schema...$(RESET)"
	cd $(BACKEND) && . .venv/bin/activate && \
		DJANGO_SETTINGS_MODULE=config.settings python manage.py spectacular --validate
	@echo "$(GREEN)✓ Schema válido$(RESET)"

# =============================================================================
# BASE DE DATOS
# =============================================================================

db-migrate: ## Ejecuta migraciones de base de datos
	cd $(BACKEND) && . .venv/bin/activate && python manage.py migrate

db-makemigrations: ## Crea nuevas migraciones
	cd $(BACKEND) && . .venv/bin/activate && python manage.py makemigrations

db-shell: ## Abre shell de base de datos
	cd $(BACKEND) && . .venv/bin/activate && python manage.py dbshell

django-shell: ## Abre shell de Django
	cd $(BACKEND) && . .venv/bin/activate && python manage.py shell

# =============================================================================
# DOCKER
# =============================================================================

docker-build: ## Construye imagenes Docker
	@echo "$(CYAN)▶ Construyendo imagenes...$(RESET)"
	$(COMPOSE) build
	@echo "$(GREEN)✓ Imagenes construidas$(RESET)"

docker-clean: ## Limpia contenedores y volumenes
	@echo "$(YELLOW)⚠ Esto eliminara contenedores, volumenes y datos locales$(RESET)"
	@read -p "Continuar? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(COMPOSE_DEV) down -v
	docker system prune -f
	@echo "$(GREEN)✓ Limpieza completada$(RESET)"

# =============================================================================
# OPERACIONES
# =============================================================================

stop: ## Detiene todos los servicios
	$(COMPOSE_DEV) down 2>/dev/null || true
	$(COMPOSE_PROD) down 2>/dev/null || true
	@echo "$(GREEN)✓ Servicios detenidos$(RESET)"

logs: ## Ver logs de desarrollo
	$(COMPOSE_DEV) logs -f --tail=50

status: ## Verifica estado de servicios
	@echo "$(CYAN)▶ Estado de servicios:$(RESET)"
	@echo ""
	@$(COMPOSE) ps 2>/dev/null || echo "  No hay servicios Docker corriendo"
	@echo ""
	@echo "$(CYAN)▶ Health checks:$(RESET)"
	@curl -sf http://localhost:8000/health/ 2>/dev/null && \
		echo "  $(GREEN)✓ API: OK$(RESET)" || \
		echo "  $(RED)✗ API: No disponible$(RESET)"
	@curl -sf http://localhost:5173/ 2>/dev/null && \
		echo "  $(GREEN)✓ Dashboard: OK$(RESET)" || \
		echo "  $(RED)✗ Dashboard: No disponible$(RESET)"

health: ## Verifica health de la API
	@curl -sf http://localhost:8000/health/ | python3 -m json.tool 2>/dev/null || \
		echo "$(RED)API no disponible en localhost:8000$(RESET)"

lint: ## Ejecuta linting del codigo
	cd $(BACKEND) && . .venv/bin/activate && ruff check apps/
	cd $(BACKEND) && . .venv/bin/activate && ruff format --check apps/

lint-fix: ## Corrige problemas de linting automaticamente
	cd $(BACKEND) && . .venv/bin/activate && ruff check --fix apps/
	cd $(BACKEND) && . .venv/bin/activate && ruff format apps/

clean: ## Limpia archivos temporales
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Archivos temporales eliminados$(RESET)"
