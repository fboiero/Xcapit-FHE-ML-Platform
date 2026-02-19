# Contributing to Xcapit FHE-ML Platform

Thank you for your interest in contributing to the Xcapit FHE-ML Platform! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Security](#security)
- [Community](#community)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to security@xcapit.com.

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+ (for dashboard and TypeScript SDK)
- Docker & Docker Compose (optional, for containerized development)
- Git

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/Xcapit-FHE-ML-Platform.git
cd Xcapit-FHE-ML-Platform
git remote add upstream https://github.com/xcapit/Xcapit-FHE-ML-Platform.git
```

## Development Setup

### Python SDK

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Verify installation
pytest tests/ -v --tb=short
```

### Dashboard

```bash
cd dashboard
npm install
npm run dev
```

### TypeScript SDK

```bash
cd sdk-typescript
npm install
npm run build
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## Project Structure

```
Xcapit-FHE-ML-Platform/
├── sdk/                    # Python SDK (core library)
│   ├── models/            # ML models (LinearRegression, DecisionTree, KMeans)
│   ├── api/               # FastAPI REST endpoints
│   ├── fhe/               # FHE encryption (CKKS scheme)
│   ├── blockchain/        # Smart contract integrations
│   └── cli.py             # Command-line interface
├── sdk-ts/                 # TypeScript SDK
├── dashboard/              # React + Vite frontend
├── contracts/              # Solidity smart contracts
├── docs/                   # Documentation
├── tests/                  # Test suite
└── docker/                 # Docker configurations
```

## Coding Standards

### Python

We follow [PEP 8](https://pep8.org/) with these specific guidelines:

```python
# Use type hints
def train_model(
    X: np.ndarray,
    y: np.ndarray,
    *,
    learning_rate: float = 0.01,
    n_epochs: int = 100
) -> TrainingHistory:
    """Train the model with given data.

    Args:
        X: Feature matrix of shape (n_samples, n_features).
        y: Target vector of shape (n_samples,).
        learning_rate: Learning rate for gradient descent.
        n_epochs: Number of training epochs.

    Returns:
        Training history with loss and metrics.

    Raises:
        ValueError: If X and y have incompatible shapes.
    """
    ...
```

**Key conventions:**
- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Use `UPPER_SNAKE_CASE` for constants
- Maximum line length: 88 characters (Black formatter)
- Use Google-style docstrings
- Prefer composition over inheritance

### TypeScript

```typescript
// Use strict TypeScript
interface ModelConfig {
  readonly learningRate: number;
  readonly nEpochs: number;
  readonly optimizer?: OptimizerType;
}

// Use async/await over raw promises
async function trainModel(config: ModelConfig): Promise<TrainingResult> {
  // Implementation
}
```

**Key conventions:**
- Use `camelCase` for functions and variables
- Use `PascalCase` for types, interfaces, and classes
- Use `UPPER_SNAKE_CASE` for constants
- Prefer `interface` over `type` for object shapes
- Always use strict mode

### Solidity

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title ModelRegistry
/// @author Xcapit Team
/// @notice Manages ML model registrations on-chain
contract ModelRegistry is Ownable2Step, ReentrancyGuard {
    // State variables
    mapping(bytes32 => Model) private _models;

    // Events
    event ModelRegistered(bytes32 indexed modelId, address indexed owner);

    // Custom errors (gas efficient)
    error ModelNotFound(bytes32 modelId);
    error UnauthorizedAccess();
}
```

**Key conventions:**
- Follow [Solidity Style Guide](https://docs.soliditylang.org/en/latest/style-guide.html)
- Use custom errors instead of require strings
- Use NatSpec comments for public functions
- Prefix private variables with underscore

### React/Dashboard

```tsx
// Use functional components with TypeScript
interface ModelCardProps {
  model: Model;
  onSelect: (id: string) => void;
}

export function ModelCard({ model, onSelect }: ModelCardProps): JSX.Element {
  const { t } = useTranslation();

  return (
    <Card onClick={() => onSelect(model.id)}>
      <CardTitle>{model.name}</CardTitle>
    </Card>
  );
}
```

**Key conventions:**
- Use functional components with hooks
- Export named components (not default)
- Colocate styles with components
- Use i18n for all user-facing text

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, semicolons) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `build` | Build system or dependencies |
| `ci` | CI/CD configuration |
| `chore` | Other changes (tooling, etc.) |

### Scopes

- `sdk` - Python SDK
- `sdk-ts` - TypeScript SDK
- `dashboard` - React dashboard
- `contracts` - Smart contracts
- `api` - REST API
- `cli` - Command-line interface
- `docs` - Documentation
- `fhe` - FHE encryption

### Examples

```bash
feat(sdk): add support for random forest classifier
fix(api): resolve authentication token expiration issue
docs(readme): update installation instructions
perf(fhe): optimize CKKS encryption for batch operations
test(models): add unit tests for decision tree
```

### Breaking Changes

For breaking changes, add `BREAKING CHANGE:` in the footer:

```
feat(api)!: change authentication from API key to JWT

BREAKING CHANGE: API key authentication is no longer supported.
Migrate to JWT tokens as described in docs/migration/v2.md
```

## Pull Request Process

### Before Opening a PR

1. **Sync with upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all tests:**
   ```bash
   pytest tests/ -v
   cd dashboard && npm test
   cd sdk-typescript && npm test
   ```

3. **Run linters:**
   ```bash
   # Python
   black sdk/ tests/
   ruff check sdk/ tests/
   mypy sdk/

   # TypeScript
   cd sdk-typescript && npm run lint
   cd dashboard && npm run lint
   ```

### PR Requirements

- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Linting passes
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG.md updated (for user-facing changes)
- [ ] Commit messages follow conventions
- [ ] PR description explains the "why"

### PR Template

```markdown
## Summary
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how this was tested.

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### Review Process

1. At least one maintainer approval required
2. CI pipeline must pass
3. No unresolved conversations
4. Squash and merge preferred

## Testing Requirements

### Python SDK

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=sdk --cov-report=html

# Run specific test file
pytest tests/test_models.py -v

# Run specific test
pytest tests/test_models.py::test_linear_regression_fit -v
```

**Coverage requirements:**
- Minimum 80% coverage for new code
- All public APIs must have tests
- Edge cases and error conditions must be tested

### Test Structure

```python
import pytest
import numpy as np
from sdk.models import LinearRegression

class TestLinearRegression:
    """Tests for LinearRegression model."""

    @pytest.fixture
    def sample_data(self):
        """Generate sample training data."""
        np.random.seed(42)
        X = np.random.randn(100, 3)
        y = X @ [2, 3, -1] + 1
        return X, y

    def test_fit_returns_history(self, sample_data):
        """Fit should return training history."""
        X, y = sample_data
        model = LinearRegression()
        history = model.fit(X, y)
        assert hasattr(history, 'losses')

    def test_predict_shape(self, sample_data):
        """Predictions should have correct shape."""
        X, y = sample_data
        model = LinearRegression()
        model.fit(X, y)
        predictions = model.predict(X)
        assert predictions.shape == y.shape
```

### Dashboard Tests

```bash
cd dashboard
npm test              # Run tests
npm run test:coverage # With coverage
```

## Documentation

### Docstrings

All public modules, classes, and functions must have docstrings:

```python
def encrypt_data(
    data: np.ndarray,
    public_key: PublicKey,
    *,
    precision: int = 40
) -> EncryptedArray:
    """Encrypt data using CKKS scheme.

    Encrypts the input array using fully homomorphic encryption,
    enabling secure computation on encrypted data.

    Args:
        data: Input array to encrypt. Shape: (n_samples, n_features).
        public_key: CKKS public key for encryption.
        precision: Bit precision for encoding. Higher values give
            more accurate results but slower computation.

    Returns:
        Encrypted array that supports homomorphic operations.

    Raises:
        EncryptionError: If encryption fails due to invalid parameters.
        ValueError: If data contains NaN or infinite values.

    Example:
        >>> key_pair = generate_keys()
        >>> encrypted = encrypt_data(X, key_pair.public)
        >>> result = model.predict_encrypted(encrypted)
    """
```

### README Updates

When adding features:
1. Update feature list in README.md
2. Update README_ES.md (Spanish)
3. Add usage examples

### API Documentation

- OpenAPI spec: `docs/openapi.yaml`
- Update for any API changes
- Include request/response examples

## Security

### Reporting Vulnerabilities

**DO NOT** open public issues for security vulnerabilities.

See [SECURITY.md](SECURITY.md) for:
- Reporting process
- Supported versions
- Security update policy

### Security Guidelines

- Never commit secrets, keys, or credentials
- Use environment variables for configuration
- Validate all user inputs
- Follow OWASP guidelines
- FHE keys must never be logged

## Community

### Getting Help

- **Discussions:** GitHub Discussions for questions
- **Issues:** Bug reports and feature requests
- **Discord:** Real-time chat (link in README)

### Recognition

Contributors are recognized in:
- CHANGELOG.md (for significant contributions)
- README.md Contributors section
- Release notes

### Maintainers

Current maintainers:
- @xcapit-team

---

Thank you for contributing to privacy-preserving machine learning!
