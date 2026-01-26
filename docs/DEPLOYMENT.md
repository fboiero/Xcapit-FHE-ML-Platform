# Xcapit FHE-ML Platform - Deployment Guide

This guide covers deploying the Xcapit FHE-ML Platform to production environments.

## Architecture Overview

```
                                    ┌─────────────────┐
                                    │   CloudFlare    │
                                    │   (CDN/WAF)     │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │     Nginx       │
                                    │  (TLS, Rate     │
                                    │   Limiting)     │
                                    └────────┬────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
           ┌────────▼────────┐     ┌────────▼────────┐     ┌────────▼────────┐
           │  Django/Gunicorn │     │  Django/Gunicorn │     │  Django/Gunicorn │
           │   (Instance 1)   │     │   (Instance 2)   │     │   (Instance N)   │
           └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
                    │                        │                        │
                    └────────────────────────┼────────────────────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────────────┐
              │                              │                              │
     ┌────────▼────────┐          ┌─────────▼─────────┐          ┌────────▼────────┐
     │   PostgreSQL    │          │      Redis        │          │     OpenBao     │
     │   (Primary)     │          │  (Cache/Queue)    │          │   (Secrets)     │
     └─────────────────┘          └───────────────────┘          └─────────────────┘
```

## Pre-Deployment Checklist

### Environment Validation

Run the environment validation script before deploying:

```bash
cd backend_django
python scripts/validate_env.py
```

This validates:
- Required environment variables are set
- Secret key has sufficient entropy
- Security settings are configured correctly

### Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DJANGO_SECRET_KEY` | Yes | Secret key (min 50 chars, high entropy) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Recommended | Redis connection string |
| `DJANGO_ALLOWED_HOSTS` | Yes | Comma-separated list of allowed hosts |
| `CORS_ALLOWED_ORIGINS` | Yes | Comma-separated list of allowed origins |
| `CSRF_TRUSTED_ORIGINS` | Yes | Comma-separated list of trusted origins |
| `JWT_SIGNING_KEY` | Recommended | Separate key for JWT signing |
| `SENTRY_DSN` | Recommended | Sentry error tracking DSN |

### Generate Secrets

```bash
# Generate Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Or with OpenSSL
openssl rand -hex 50

# Generate JWT signing key
openssl rand -hex 32
```

## Deployment Methods

### Docker Compose (Recommended for Small Deployments)

1. **Clone and configure**:
   ```bash
   git clone https://github.com/xcapit/fhe-ml-platform.git
   cd fhe-ml-platform
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Validate environment**:
   ```bash
   cd backend_django
   python scripts/validate_env.py
   ```

3. **Deploy**:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d
   ```

4. **Verify deployment**:
   ```bash
   docker compose exec django python scripts/verify_production.py
   curl -f https://your-domain.com/health/
   ```

### Kubernetes (Recommended for Scale)

1. **Create namespace**:
   ```bash
   kubectl create namespace xcapit-fhe
   ```

2. **Create secrets**:
   ```bash
   kubectl create secret generic xcapit-fhe-secrets \
     --namespace xcapit-fhe \
     --from-literal=DJANGO_SECRET_KEY='your-secret-key' \
     --from-literal=DATABASE_URL='postgresql://...' \
     --from-literal=REDIS_URL='redis://...'
   ```

3. **Apply manifests**:
   ```bash
   kubectl apply -f deploy/k8s/ --namespace xcapit-fhe
   ```

4. **Check status**:
   ```bash
   kubectl get pods --namespace xcapit-fhe
   kubectl logs -f deployment/django --namespace xcapit-fhe
   ```

### AWS ECS

1. **Build and push image**:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY
   docker build -t xcapit-fhe-django:latest ./backend_django
   docker tag xcapit-fhe-django:latest $ECR_REGISTRY/xcapit-fhe-django:latest
   docker push $ECR_REGISTRY/xcapit-fhe-django:latest
   ```

2. **Create task definition** with environment variables from Secrets Manager

3. **Create ECS service** with ALB and auto-scaling

### Google Cloud Run

1. **Build and push**:
   ```bash
   gcloud builds submit --tag gcr.io/$PROJECT_ID/xcapit-fhe-django ./backend_django
   ```

2. **Deploy**:
   ```bash
   gcloud run deploy xcapit-fhe-django \
     --image gcr.io/$PROJECT_ID/xcapit-fhe-django \
     --platform managed \
     --region us-central1 \
     --set-env-vars DJANGO_SETTINGS_MODULE=config.settings \
     --set-secrets DJANGO_SECRET_KEY=django-secret:latest
   ```

## Post-Deployment Verification

### Health Checks

```bash
# Basic health check
curl -f https://api.your-domain.com/health/

# Detailed health check
curl -f https://api.your-domain.com/api/v2/health/

# Check response headers
curl -I https://api.your-domain.com/api/v2/health/
```

### Run Production Verification

```bash
# Via Docker
docker compose exec django python scripts/verify_production.py

# Via kubectl
kubectl exec -it deployment/django -- python scripts/verify_production.py
```

### Expected Headers

Verify these security headers are present:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Content-Security-Policy: default-src 'none'; frame-ancestors 'none'
```

## Monitoring Setup

### Prometheus Metrics

The application exposes metrics at `/metrics/` (if enabled):

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'xcapit-fhe-django'
    static_configs:
      - targets: ['django:8000']
    metrics_path: /metrics/
```

### Sentry Integration

Set `SENTRY_DSN` environment variable to enable error tracking:

```bash
SENTRY_DSN=https://xxx@sentry.io/yyy
```

### Log Aggregation

Logs are output in JSON format. Configure your log aggregator:

```bash
# View logs
docker compose logs -f django

# Filter errors
docker compose logs django 2>&1 | jq 'select(.level == "ERROR")'
```

## Security Checklist

### Before Going Live

- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_SECRET_KEY` is unique and strong (50+ chars)
- [ ] `ALLOWED_HOSTS` does not contain `*`
- [ ] TLS certificates are valid and not self-signed
- [ ] Database credentials are not default
- [ ] Rate limiting is configured
- [ ] CORS origins are explicitly listed
- [ ] Admin panel is restricted or disabled
- [ ] Container runs as non-root user
- [ ] Container filesystem is read-only

### Network Security

- [ ] Database not exposed to internet
- [ ] Redis not exposed to internet
- [ ] Only ports 80/443 exposed publicly
- [ ] Firewall rules in place
- [ ] VPC/private network for internal services

### Monitoring

- [ ] Health check endpoints accessible
- [ ] Error tracking configured (Sentry)
- [ ] Log aggregation configured
- [ ] Alerting rules defined
- [ ] Uptime monitoring configured

## Rollback Procedure

### Docker Compose

```bash
# List available images
docker images xcapit-fhe-django

# Rollback to previous version
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
docker tag xcapit-fhe-django:previous xcapit-fhe-django:latest
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d
```

### Kubernetes

```bash
# Check rollout history
kubectl rollout history deployment/django --namespace xcapit-fhe

# Rollback to previous revision
kubectl rollout undo deployment/django --namespace xcapit-fhe

# Rollback to specific revision
kubectl rollout undo deployment/django --to-revision=2 --namespace xcapit-fhe
```

### Database Migrations

If a migration needs to be reverted:

```bash
# List migrations
python manage.py showmigrations

# Revert to specific migration
python manage.py migrate app_name 0005_previous_migration

# Check current state
python manage.py showmigrations
```

## Scaling

### Horizontal Scaling

```bash
# Docker Compose (with Docker Swarm)
docker service scale xcapit-fhe_django=3

# Kubernetes
kubectl scale deployment django --replicas=3 --namespace xcapit-fhe
```

### Vertical Scaling

Adjust resource limits in `docker-compose.prod.yml`:

```yaml
services:
  django:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
```

### Database Connection Pooling

For high-traffic scenarios, use PgBouncer:

```bash
docker run -d \
  -e DATABASE_URL=postgres://user:pass@postgres:5432/db \
  -e POOL_MODE=transaction \
  -e MAX_CLIENT_CONN=1000 \
  -e DEFAULT_POOL_SIZE=20 \
  -p 6432:6432 \
  edoburu/pgbouncer
```

## Troubleshooting

### Common Issues

**Container won't start**:
```bash
# Check logs
docker compose logs django

# Check if migrations are pending
docker compose exec django python manage.py showmigrations
```

**Database connection refused**:
```bash
# Check database is running
docker compose ps postgres

# Test connection
docker compose exec django python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection()"
```

**Static files not loading**:
```bash
# Collect static files
docker compose exec django python manage.py collectstatic --noinput

# Check static volume
docker compose exec nginx ls -la /var/www/static/
```

### Debug Mode (Temporary)

If you need to debug in production (use with extreme caution):

```bash
# Enable debug temporarily
docker compose exec -e DJANGO_DEBUG=True django python manage.py shell
```

## Support

- GitHub Issues: https://github.com/xcapit/fhe-ml-platform/issues
- Documentation: https://docs.xcapit.io
- Email: support@xcapit.com
