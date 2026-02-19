# Commit Messages

## Format

```
type(scope): description

[optional body]

[optional footer]
```

## Types

| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `chore` | Maintenance, dependencies, config |
| `ci` | CI/CD pipeline changes |
| `perf` | Performance improvement |
| `style` | Formatting, whitespace (no logic change) |

## Scopes (Project-Specific)

### Backend Apps
`core`, `consortiums`, `governance`, `models`, `blockchain`, `compliance`, `marketplace`, `sandbox`, `federated`, `data-quality`, `competitive`, `ensemble`, `explainability`

### Other
`sdk`, `dashboard`, `contracts`, `ci`, `docker`, `deps`

## Rules

- Description starts with lowercase
- No period at end
- Imperative mood ("add feature" not "added feature")
- Max 72 characters for first line
- Body explains "why" not "what"
- Breaking changes: `feat!:` or `BREAKING CHANGE:` in footer

## Examples (from actual git log)

```
fix: correct endpoint.model.version -> current_version in federated views
docs: update CLAUDE.md with current stats (1442 tests, 95.12% coverage)
test: add 5 E2E integration tests for cross-app workflows
fix(core): correct 3 pre-existing bugs in authentication.py
feat(data-quality): add quality assessment scoring service
ci: update CodeQL action from v3 to v4
refactor(consortiums): extract training logic to FHETrainingService
chore(deps): upgrade Django to 5.2 LTS
```
