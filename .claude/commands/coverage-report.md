Generate a quick coverage report and identify improvement areas.

Steps:

1. **Run coverage analysis**:
   ```bash
   cd backend_django && DJANGO_SETTINGS_MODULE=config.settings_test pytest --cov=apps --cov-report=term-missing --cov-fail-under=90 -q
   ```

2. **Identify modules below 95%** — List any module with coverage < 95% and the specific uncovered lines.

3. **Prioritize by risk** — Rank uncovered areas by:
   - Business logic (services, views) > Models > Serializers > Admin
   - Security-critical code > Regular code

4. **Suggest specific tests** — For each gap, suggest what test cases would cover the missing lines.

5. **Summary table** — Present results as:
   | Module | Coverage | Missing Lines | Priority | Suggested Test |
   |--------|----------|---------------|----------|----------------|

6. **Compare with previous** — Note if coverage improved or regressed from the 95.12% baseline.
