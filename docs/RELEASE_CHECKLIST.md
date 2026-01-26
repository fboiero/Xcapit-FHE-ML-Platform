# Xcapit FHE-ML Platform - Release Checklist

Use this checklist for every production release. Copy this checklist to your release issue/PR.

## Pre-Release

### Code Quality

- [ ] All tests passing locally
  ```bash
  cd backend_django && pytest --cov=apps
  ```

- [ ] Test coverage meets threshold (>90%)
  ```bash
  pytest --cov=apps --cov-report=term-missing --cov-fail-under=90
  ```

- [ ] Linting passes
  ```bash
  ruff check sdk/ backend_django/apps/
  ruff format --check sdk/ backend_django/apps/
  ```

- [ ] Type checking passes (if applicable)
  ```bash
  mypy backend_django/apps/
  ```

- [ ] No new security vulnerabilities
  ```bash
  pip-audit
  ```

### Documentation

- [ ] CHANGELOG.md updated with version and date
- [ ] API documentation updated if endpoints changed
- [ ] Migration notes added if breaking changes

### Version Bump

- [ ] Version updated in:
  - [ ] `sdk/__init__.py`
  - [ ] `backend_django/config/settings.py` (if applicable)
  - [ ] `package.json` files

### Git

- [ ] All changes committed and pushed
- [ ] PR approved by at least one reviewer
- [ ] CI pipeline passing (all green)
- [ ] No merge conflicts with main branch

---

## Staging Deployment

### Deploy to Staging

- [ ] Create release candidate tag
  ```bash
  git tag -a v0.x.x-rc1 -m "Release candidate 1"
  git push origin v0.x.x-rc1
  ```

- [ ] Deploy to staging environment
  ```bash
  # Example for Docker Compose staging
  docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d
  ```

- [ ] Run database migrations
  ```bash
  docker compose exec django python manage.py migrate
  ```

### Staging Verification

- [ ] Health check passing
  ```bash
  curl -f https://staging-api.xcapit.com/health/
  ```

- [ ] Smoke tests passing
  - [ ] Authentication (login, logout, refresh token)
  - [ ] Core API endpoints functional
  - [ ] FHE operations working

- [ ] No new errors in logs
  ```bash
  docker compose logs --since 10m django | grep -i error
  ```

- [ ] Performance acceptable (response times < 500ms for standard endpoints)

- [ ] Run production verification script
  ```bash
  docker compose exec django python scripts/verify_production.py
  ```

### Staging Sign-off

- [ ] QA approval received
- [ ] Product owner approval received
- [ ] No blocking issues identified

---

## Production Deployment

### Pre-Deployment

- [ ] Notify team of upcoming deployment
- [ ] Verify backup completed (last 24 hours)
  ```bash
  ls -la /backups/postgres/
  ```

- [ ] Document current version for rollback
  ```bash
  git describe --tags --abbrev=0
  ```

- [ ] Verify environment variables are set
  ```bash
  python scripts/validate_env.py
  ```

### Deployment

- [ ] Create release tag
  ```bash
  git tag -a v0.x.x -m "Release v0.x.x"
  git push origin v0.x.x
  ```

- [ ] Deploy to production
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production pull
  docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d
  ```

- [ ] Run database migrations
  ```bash
  docker compose exec django python manage.py migrate
  ```

- [ ] Collect static files (if needed)
  ```bash
  docker compose exec django python manage.py collectstatic --noinput
  ```

### Post-Deployment Verification

- [ ] Health check passing
  ```bash
  curl -f https://api.xcapit.com/health/
  ```

- [ ] All containers running
  ```bash
  docker compose ps
  ```

- [ ] No errors in logs (first 5 minutes)
  ```bash
  docker compose logs --since 5m django | grep -i error
  ```

- [ ] API endpoints responding correctly
  ```bash
  curl https://api.xcapit.com/api/v2/health/
  ```

- [ ] SSL certificate valid
  ```bash
  echo | openssl s_client -servername api.xcapit.com -connect api.xcapit.com:443 2>/dev/null | openssl x509 -noout -dates
  ```

- [ ] Security headers present
  ```bash
  curl -I https://api.xcapit.com/api/v2/health/ | grep -E "(Strict-Transport|X-Frame|X-Content-Type)"
  ```

### Monitoring

- [ ] Error rate normal in monitoring dashboard
- [ ] Response times normal
- [ ] No alerts triggered

### Communication

- [ ] Team notified of successful deployment
- [ ] Release notes published (GitHub Release)
- [ ] External changelog updated (if applicable)

---

## Rollback Procedure

### When to Rollback

Rollback immediately if:
- Error rate > 1% after deployment
- Response times > 2x normal
- Core functionality broken
- Security vulnerability discovered

### Rollback Steps

1. **Notify team**
   ```
   @channel Rolling back to v0.x.x due to [reason]
   ```

2. **Rollback containers**
   ```bash
   # Pull previous version
   docker compose pull django:v0.x.x

   # Deploy previous version
   docker compose up -d
   ```

3. **Rollback database (if needed)**
   ```bash
   # Revert last migration
   docker compose exec django python manage.py migrate app_name 0005_previous
   ```

4. **Verify rollback**
   ```bash
   curl -f https://api.xcapit.com/health/
   docker compose logs --tail=50 django
   ```

5. **Post-mortem**
   - Document what went wrong
   - Create issue for fix
   - Schedule re-deployment

---

## Emergency Contacts

| Role | Contact | When to Contact |
|------|---------|-----------------|
| On-Call Engineer | PagerDuty | Service down, data loss |
| Engineering Lead | Slack | Major issues, rollback decisions |
| Security Team | security@xcapit.com | Security incidents |

---

## Release Notes Template

```markdown
## v0.x.x (YYYY-MM-DD)

### Added
- New feature description

### Changed
- Change description

### Fixed
- Bug fix description

### Security
- Security improvement description

### Breaking Changes
- Breaking change description and migration steps

### Upgrade Notes
- Any special steps needed for upgrade
```

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-29 | 1.0.0 | Initial version |
