# Xcapit FHE-ML Platform - Backend Deployment Guide

Django 5.2 LTS API for privacy-preserving machine learning using Fully Homomorphic Encryption.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Environment Variables](#environment-variables)
- [Security Checklist](#security-checklist)
- [Monitoring & Health](#monitoring--health)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Docker & Docker Compose v2+
- Python 3.12+ (for local development)
- PostgreSQL 15+ (production)
- Redis 7+ (caching & Celery)

### 1. Clone and Configure

```bash
cd backend_django

# Copy environment template
cp .env.example .env

# Generate secrets
echo "DJANGO_SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "POSTGRES_PASSWORD=$(openssl rand -hex 16)" >> .env
```

### 2. Run with Docker

```bash
# Development (with hot-reload)
docker compose --profile dev up

# Production
docker compose up django

# Run tests
docker compose --profile test up django-test
```

### 3. Access

- API: http://localhost:8000/api/v2/
- Health: http://localhost:8000/health/
- Docs: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/admin/

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Load Balancer                         │
│                    (nginx / cloud LB)                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Django + Gunicorn                       │
│                    (4 workers, 2 threads)                    │
│                         Port 8000                            │
└─────────────────────────────────────────────────────────────┘
                    │                   │
          ┌────────┘                   └────────┐
          ▼                                     ▼
┌──────────────────┐                 ┌──────────────────┐
│   PostgreSQL 16  │                 │     Redis 7      │
│   (Primary DB)   │                 │ (Cache/Sessions) │
│    Port 5432     │                 │    Port 6379     │
└──────────────────┘                 └──────────────────┘
                                              │
                                              ▼
                                   ┌──────────────────┐
                                   │  Celery Workers  │
                                   │  (Async Tasks)   │
                                   └──────────────────┘
```

### Docker Images

| Image | Size | Purpose |
|-------|------|---------|
| `xcapit-fhe-django:latest` | ~200MB | Production |
| `xcapit-fhe-django:dev` | ~250MB | Development |

---

## Local Development

### Without Docker

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment
export DJANGO_SECRET_KEY="dev-secret-key-not-for-production"
export DJANGO_DEBUG=True

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=apps --cov-report=html

# Specific app
pytest tests/test_core.py -v
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Fix linting issues
ruff check --fix .
```

---

## Docker Deployment

### Build Images

```bash
# Production image
docker build -t xcapit-fhe-django:latest .

# Development image
docker build --target development -t xcapit-fhe-django:dev .

# With build args
docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t xcapit-fhe-django:latest .
```

### Docker Compose Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| (default) | django, postgres, redis | Production |
| `dev` | django-dev, postgres-dev, redis-dev | Development |
| `test` | django-test | Run tests |
| `celery` | celery, celery-beat | Async tasks |

```bash
# Development with exposed DB ports
docker compose --profile dev up

# Production with Celery
docker compose --profile celery up

# Run tests
docker compose --profile test run --rm django-test
```

### Useful Commands

```bash
# View logs
docker compose logs -f django

# Shell into container
docker compose exec django bash

# Django shell
docker compose exec django python manage.py shell

# Run migrations manually
docker compose exec django python manage.py migrate

# Create superuser
docker compose exec django python manage.py createsuperuser

# Collect static files
docker compose exec django python manage.py collectstatic --noinput
```

---

## Production Deployment

### Pre-deployment Checklist

- [ ] Set strong `DJANGO_SECRET_KEY` (min 50 chars)
- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Configure `DJANGO_ALLOWED_HOSTS`
- [ ] Configure `CORS_ALLOWED_ORIGINS`
- [ ] Configure `CSRF_TRUSTED_ORIGINS`
- [ ] Set up SSL/TLS termination
- [ ] Configure Sentry for error tracking
- [ ] Set up log aggregation
- [ ] Configure backup strategy

### Deploy to Cloud

#### AWS ECS / Fargate

```bash
# Build and push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
docker build -t $ECR_REGISTRY/xcapit-fhe-django:latest .
docker push $ECR_REGISTRY/xcapit-fhe-django:latest
```

#### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/$PROJECT_ID/xcapit-fhe-django

# Deploy
gcloud run deploy xcapit-fhe-api \
  --image gcr.io/$PROJECT_ID/xcapit-fhe-django \
  --platform managed \
  --port 8000 \
  --set-env-vars "DJANGO_SECRET_KEY=$SECRET"
```

#### DigitalOcean App Platform

```yaml
# app.yaml
name: xcapit-fhe-api
services:
  - name: api
    dockerfile_path: backend_django/Dockerfile
    http_port: 8000
    instance_size_slug: professional-xs
    envs:
      - key: DJANGO_SECRET_KEY
        scope: RUN_TIME
        type: SECRET
```

### Nginx Reverse Proxy

```nginx
upstream django {
    server django:8000;
}

server {
    listen 80;
    server_name api.xcapit.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.xcapit.com;

    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/privkey.pem;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | Database password | `openssl rand -hex 16` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_DEBUG` | `False` | Enable debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |
| `DATABASE_URL` | - | PostgreSQL connection URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `CORS_ALLOWED_ORIGINS` | - | CORS allowed origins |
| `CSRF_TRUSTED_ORIGINS` | - | CSRF trusted origins |
| `JWT_SIGNING_KEY` | `DJANGO_SECRET_KEY` | Separate JWT signing key |
| `SENTRY_DSN` | - | Sentry error tracking |
| `FHE_SECURITY_LEVEL` | `128` | FHE security level (128/192/256) |

### Generate Secrets

```bash
# Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Or with openssl
openssl rand -hex 32

# Strong password
openssl rand -base64 24
```

---

## Security Checklist

### Application Security

- [x] HTTPS enforced (`SECURE_SSL_REDIRECT`)
- [x] HSTS enabled (`SECURE_HSTS_SECONDS`)
- [x] XSS protection (`SECURE_BROWSER_XSS_FILTER`)
- [x] Content-Type sniffing disabled
- [x] X-Frame-Options: DENY
- [x] CSRF protection enabled
- [x] Session cookies secure & httpOnly
- [x] Password minimum 12 characters
- [x] Brute-force protection (django-axes)
- [x] Rate limiting enabled
- [x] JWT token blacklist enabled

### Infrastructure Security

- [x] Non-root container user
- [x] Read-only filesystem (production)
- [x] Database not exposed to host
- [x] Redis not exposed to host
- [x] Secrets via environment variables
- [x] Multi-stage Docker build
- [x] Health checks configured

### Production Hardening

```bash
# Verify security settings
python manage.py check --deploy
```

---

## Monitoring & Health

### Health Check Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health/` | Full health check (DB, cache) |
| `GET /api/v2/` | API root |

### Prometheus Metrics (optional)

```bash
pip install django-prometheus
```

### Logging

Logs are written to stdout/stderr for container log aggregation.

```bash
# View logs
docker compose logs -f django

# Filter errors
docker compose logs django 2>&1 | grep ERROR
```

### Sentry Integration

```bash
# Set in environment
SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Test connection
docker compose exec django python -c "
import django
django.setup()
from django.db import connection
connection.ensure_connection()
print('Database connected!')
"
```

#### Migrations Failed

```bash
# Check migration status
docker compose exec django python manage.py showmigrations

# Reset migrations (DANGER: data loss)
docker compose exec django python manage.py migrate --fake-initial
```

#### Static Files Not Found

```bash
# Collect static files
docker compose exec django python manage.py collectstatic --noinput

# Check static directory
docker compose exec django ls -la /app/staticfiles/
```

#### Permission Denied

```bash
# Fix file permissions
docker compose exec -u root django chown -R django:django /app
```

### Performance Tuning

#### Gunicorn Workers

```
Workers = (2 × CPU cores) + 1
Threads = 2-4 per worker
```

For 2-core server: 4-5 workers, 2 threads each.

#### Database Connections

```python
# settings.py
DATABASES = {
    "default": {
        ...
        "CONN_MAX_AGE": 600,  # Keep connections open for 10 min
        "CONN_HEALTH_CHECKS": True,
    }
}
```

#### Redis Connection Pool

```python
CACHES = {
    "default": {
        ...
        "OPTIONS": {
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
        }
    }
}
```

---

## API Documentation

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

---

## Support

- Issues: https://github.com/xcapit/privacy-platform/issues
- Documentation: https://docs.xcapit.com/fhe-ml
