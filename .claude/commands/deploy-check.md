Run a comprehensive pre-deployment checklist to verify the project is ready for production.

Execute each check and report pass/fail:

### 1. Tests & Coverage
```bash
cd backend_django && DJANGO_SETTINGS_MODULE=config.settings_test pytest --cov=apps --cov-fail-under=90 -q
```
- [ ] All tests pass
- [ ] Coverage >= 90%

### 2. Linting
```bash
cd backend_django && ruff check apps/ && ruff format --check apps/
```
- [ ] No lint errors
- [ ] Formatting clean

### 3. Security Scan
```bash
git diff --cached --name-only | grep -E '\.(env|key|pem|secret|credentials)' || echo "OK"
grep -r "SECRET_KEY\|password\|token" backend_django/apps/ --include="*.py" -l | grep -v test | grep -v __pycache__
```
- [ ] No secrets in staged files
- [ ] No hardcoded credentials in source

### 4. Migrations
```bash
cd backend_django && python manage.py showmigrations --list 2>/dev/null | grep "\[ \]" || echo "All applied"
cd backend_django && python manage.py makemigrations --check --dry-run 2>/dev/null || echo "Pending migrations detected"
```
- [ ] All migrations applied
- [ ] No pending migrations

### 5. Docker Build
```bash
cd backend_django && docker build --target production -t xcapit-fhe-test . 2>&1 | tail -5
```
- [ ] Docker build succeeds

### 6. Smart Contract Tests
```bash
cd contracts && forge test 2>&1 | tail -5
```
- [ ] Contract tests pass

### 7. Dashboard Build
```bash
cd dashboard && npm run build 2>&1 | tail -5
```
- [ ] Dashboard builds without errors

### 8. Final Summary
Present a deployment readiness scorecard:
| Check | Status | Notes |
|-------|--------|-------|
| Tests | ✅/❌ | |
| Coverage | ✅/❌ | X% |
| Lint | ✅/❌ | |
| Security | ✅/❌ | |
| Migrations | ✅/❌ | |
| Docker | ✅/❌ | |
| Contracts | ✅/❌ | |
| Dashboard | ✅/❌ | |
