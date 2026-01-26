# Xcapit FHE-ML Platform - Operations Runbook

This runbook provides procedures for common operational tasks and incident response.

## Table of Contents

- [Incident Response](#incident-response)
- [Common Issues](#common-issues)
- [Maintenance Tasks](#maintenance-tasks)
- [Backup and Recovery](#backup-and-recovery)
- [Scaling](#scaling)

---

## Incident Response

### Service Down (HTTP 5xx / Connection Refused)

**Severity**: Critical
**Response Time**: Immediate

#### Diagnosis

```bash
# Check if containers are running
docker compose ps

# Check Django container logs
docker compose logs --tail=100 django

# Check health endpoint
curl -f http://localhost:8000/health/ || echo "Health check failed"

# Check database connectivity
docker compose exec django python -c "
import django; django.setup()
from django.db import connection
connection.ensure_connection()
print('Database OK')
"
```

#### Resolution Steps

1. **Container not running**:
   ```bash
   docker compose --profile production up -d
   ```

2. **OOM killed**:
   ```bash
   # Check for OOM events
   dmesg | grep -i "killed process"

   # Increase memory limits in docker-compose.prod.yml
   # Then restart
   docker compose --profile production up -d
   ```

3. **Database connection issues**:
   ```bash
   # Check PostgreSQL
   docker compose exec postgres pg_isready

   # Restart PostgreSQL if needed
   docker compose restart postgres

   # Wait and restart Django
   sleep 10
   docker compose restart django
   ```

4. **Application crash loop**:
   ```bash
   # Check for migration issues
   docker compose exec django python manage.py showmigrations

   # Run migrations if needed
   docker compose exec django python manage.py migrate
   ```

---

### High Latency (Response Time > 5s)

**Severity**: High
**Response Time**: 15 minutes

#### Diagnosis

```bash
# Check container resource usage
docker stats --no-stream

# Check slow queries (if pg_stat_statements enabled)
docker compose exec postgres psql -U xcapit -d fheml -c "
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Check Redis memory
docker compose exec redis redis-cli INFO memory

# Check Celery queue depth
docker compose exec django celery -A config inspect active
```

#### Resolution Steps

1. **Database slow queries**:
   ```bash
   # Analyze and optimize
   docker compose exec postgres psql -U xcapit -d fheml -c "ANALYZE;"

   # Check for missing indexes
   docker compose exec django python manage.py dbshell
   # Then: EXPLAIN ANALYZE <slow query>;
   ```

2. **Redis memory pressure**:
   ```bash
   # Clear expired keys
   docker compose exec redis redis-cli --scan --pattern '*' | head -100

   # If needed, flush cache (affects performance temporarily)
   docker compose exec redis redis-cli FLUSHDB
   ```

3. **High CPU on Django**:
   ```bash
   # Scale horizontally
   docker compose up -d --scale django=3
   ```

---

### Authentication Issues (401/403 Errors)

**Severity**: Medium
**Response Time**: 30 minutes

#### Diagnosis

```bash
# Check token validity
docker compose exec django python manage.py shell << 'EOF'
from rest_framework_simplejwt.tokens import AccessToken
token = "paste-token-here"
try:
    AccessToken(token)
    print("Token is valid")
except Exception as e:
    print(f"Token error: {e}")
EOF

# Check blacklisted tokens
docker compose exec django python manage.py shell << 'EOF'
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
print(f"Blacklisted tokens: {BlacklistedToken.objects.count()}")
EOF

# Check user permissions
docker compose exec django python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(email="user@example.com")
print(f"Active: {user.is_active}")
print(f"Staff: {user.is_staff}")
print(f"Groups: {list(user.groups.values_list('name', flat=True))}")
EOF
```

#### Resolution Steps

1. **Expired tokens**:
   - User should request new token via `/api/v2/auth/token/refresh/`

2. **Blacklisted tokens**:
   - User should log in again to get new tokens

3. **User locked out (django-axes)**:
   ```bash
   docker compose exec django python manage.py axes_reset
   # Or reset specific user:
   docker compose exec django python manage.py axes_reset_user username
   ```

---

## Common Issues

### Database Connection Pool Exhausted

**Symptoms**: `OperationalError: connection pool exhausted`

```bash
# Check active connections
docker compose exec postgres psql -U xcapit -d fheml -c "
SELECT count(*) FROM pg_stat_activity WHERE datname = 'fheml';
"

# Kill idle connections
docker compose exec postgres psql -U xcapit -d fheml -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'fheml'
AND state = 'idle'
AND state_change < NOW() - INTERVAL '10 minutes';
"

# Restart Django to reset connection pool
docker compose restart django
```

### Celery Tasks Not Processing

**Symptoms**: Tasks stuck in queue, no workers available

```bash
# Check worker status
docker compose exec django celery -A config inspect active
docker compose exec django celery -A config inspect reserved

# Check queue length
docker compose exec redis redis-cli LLEN celery

# Restart workers
docker compose restart celery celery-beat

# Purge queue if needed (caution: loses pending tasks)
docker compose exec django celery -A config purge -f
```

### Disk Space Full

**Symptoms**: Write errors, container crashes

```bash
# Check disk usage
df -h

# Find large files
du -sh /var/lib/docker/*

# Clean Docker resources
docker system prune -af --volumes

# Clean old logs
docker compose logs --tail=0  # Truncates logs
```

### Memory Leak

**Symptoms**: Memory usage grows over time until OOM

```bash
# Monitor memory over time
watch -n 5 'docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"'

# Force garbage collection in Python
docker compose exec django python -c "
import gc
gc.collect()
print('GC complete')
"

# Restart container with new memory baseline
docker compose restart django
```

---

## Maintenance Tasks

### Daily

```bash
# Check service health
curl -f https://api.your-domain.com/health/

# Review error logs
docker compose logs --since 24h django | grep -i error

# Check disk usage
df -h /var/lib/docker
```

### Weekly

```bash
# Database maintenance
docker compose exec postgres vacuumdb -U xcapit -d fheml --analyze

# Clean expired sessions
docker compose exec django python manage.py clearsessions

# Clean old blacklisted tokens
docker compose exec django python manage.py flushexpiredtokens

# Review security scans
# Check GitHub Security tab for new vulnerabilities
```

### Monthly

```bash
# Update dependencies (in dev environment first)
pip install --upgrade -r requirements.txt
npm update

# Database backup verification
pg_restore --list backup.dump  # Verify backup integrity

# SSL certificate check
echo | openssl s_client -servername api.your-domain.com -connect api.your-domain.com:443 2>/dev/null | openssl x509 -noout -dates

# Security audit
docker compose exec django pip-audit
docker compose exec django python manage.py check --deploy
```

---

## Backup and Recovery

### Database Backup

#### Automated Backup Script

```bash
#!/bin/bash
# backup_db.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup
docker compose exec -T postgres pg_dump -U xcapit -Fc fheml > "$BACKUP_DIR/fheml_$DATE.dump"

# Compress
gzip "$BACKUP_DIR/fheml_$DATE.dump"

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/fheml_$DATE.dump.gz" s3://your-bucket/backups/

# Clean old backups
find "$BACKUP_DIR" -name "*.dump.gz" -mtime +$RETENTION_DAYS -delete
```

#### Manual Backup

```bash
# Full backup
docker compose exec postgres pg_dump -U xcapit -Fc fheml > backup_$(date +%Y%m%d).dump

# Schema only
docker compose exec postgres pg_dump -U xcapit -s fheml > schema_$(date +%Y%m%d).sql

# Specific table
docker compose exec postgres pg_dump -U xcapit -t users fheml > users_$(date +%Y%m%d).sql
```

### Database Recovery

#### Full Recovery

```bash
# Stop Django to prevent connections
docker compose stop django celery celery-beat

# Drop and recreate database
docker compose exec postgres psql -U xcapit -c "DROP DATABASE IF EXISTS fheml;"
docker compose exec postgres psql -U xcapit -c "CREATE DATABASE fheml;"

# Restore backup
docker compose exec -T postgres pg_restore -U xcapit -d fheml < backup.dump

# Start Django
docker compose start django celery celery-beat

# Verify
docker compose exec django python manage.py check
```

#### Point-in-Time Recovery

Requires WAL archiving to be enabled. Configure in PostgreSQL:

```ini
archive_mode = on
archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'
```

### Redis Backup

```bash
# Trigger RDB snapshot
docker compose exec redis redis-cli BGSAVE

# Copy dump file
docker cp xcapit-fhe-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

---

## Scaling

### Horizontal Scaling (Add More Instances)

```bash
# Scale Django instances
docker compose up -d --scale django=3

# With Docker Swarm
docker service scale xcapit-fhe_django=5

# With Kubernetes
kubectl scale deployment django --replicas=5
```

### Vertical Scaling (Increase Resources)

Edit `docker-compose.prod.yml`:

```yaml
services:
  django:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
```

Then apply:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Database Scaling

#### Read Replicas

```yaml
# docker-compose.prod.yml
services:
  postgres-replica:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: xcapit
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    command: |
      postgres
      -c hot_standby=on
```

#### Connection Pooling with PgBouncer

```yaml
services:
  pgbouncer:
    image: edoburu/pgbouncer
    environment:
      DATABASE_URL: postgres://xcapit:${POSTGRES_PASSWORD}@postgres:5432/fheml
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 1000
      DEFAULT_POOL_SIZE: 20
```

---

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| On-Call Engineer | - | PagerDuty |
| Database Admin | - | - |
| Security Team | - | security@xcapit.com |

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-29 | 1.0.0 | Initial version |
