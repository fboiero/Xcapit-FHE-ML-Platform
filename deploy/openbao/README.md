# OpenBao Secret Management

OpenBao is an open-source fork of HashiCorp Vault, providing secret management for the Xcapit FHE-ML Platform.

## Quick Start (Development)

```bash
# Start OpenBao in dev mode
docker compose --profile vault up -d

# Access UI
open http://localhost:8200/ui

# Login with token: dev-root-token
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenBao Server                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  KV Engine  │  │  Database   │  │   PKI Engine        │ │
│  │  (xcapit/)  │  │  Engine     │  │   (certificates)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
           │                │                    │
           ▼                ▼                    ▼
    ┌──────────────────────────────────────────────────┐
    │              Django Application                   │
    │         (apps/core/secrets.py)                   │
    └──────────────────────────────────────────────────┘
```

## Secret Paths

| Path | Description | Example Keys |
|------|-------------|--------------|
| `xcapit/django/config` | Django configuration | `secret_key`, `debug`, `allowed_hosts` |
| `xcapit/database/postgres` | PostgreSQL credentials | `host`, `port`, `name`, `user`, `password` |
| `xcapit/database/redis` | Redis credentials | `host`, `port`, `password` |
| `xcapit/api-keys/jwt` | JWT signing key | `signing_key` |
| `xcapit/fhe/master` | FHE encryption keys | TenSEAL keys |

## Development Setup

### 1. Start OpenBao

```bash
docker compose --profile vault up -d
```

### 2. Enable Secrets Engine

```bash
# Connect to OpenBao container
docker exec -it xcapit-fhe-openbao-dev sh

# Set environment
export BAO_ADDR=http://127.0.0.1:8200
export BAO_TOKEN=dev-root-token

# Enable KV v2 engine
bao secrets enable -path=xcapit kv-v2

# Create secrets
bao kv put -mount=xcapit django/config \
  secret_key="$(openssl rand -hex 32)" \
  debug="false" \
  allowed_hosts="localhost,127.0.0.1"

bao kv put -mount=xcapit database/postgres \
  host="postgres" \
  port="5432" \
  name="fheml" \
  user="xcapit" \
  password="$(openssl rand -hex 16)"
```

### 3. Configure Django

Set environment variables:

```bash
export VAULT_ENABLED=true
export BAO_ADDR=http://localhost:8200
export BAO_TOKEN=dev-root-token
export VAULT_MOUNT_POINT=xcapit
```

Or add to `.env`:

```env
VAULT_ENABLED=true
BAO_ADDR=http://openbao-dev:8200
BAO_TOKEN=dev-root-token
VAULT_MOUNT_POINT=xcapit
```

### 4. Use in Code

```python
from apps.core.secrets import secrets

# Get a single secret
db_password = secrets.get("database/postgres", "password")

# Get all secrets at a path
db_config = secrets.get_all("database/postgres")

# Helper functions
from apps.core.secrets import get_django_secret_key, get_database_url
secret_key = get_django_secret_key()
db_url = get_database_url()
```

## Production Setup

### 1. Use Production Configuration

```bash
docker compose --profile production up -d
```

### 2. Initialize OpenBao

```bash
# First time only - generates unseal keys and root token
bao operator init -key-shares=5 -key-threshold=3

# Store keys securely (HSM, cloud KMS, or secure storage)
# NEVER store keys in files or environment variables in production!
```

### 3. Configure Auto-Unseal (Recommended)

Edit `deploy/openbao/config-prod.hcl`:

```hcl
# AWS KMS
seal "awskms" {
  region     = "us-east-1"
  kms_key_id = "alias/openbao-unseal"
}

# OR GCP Cloud KMS
seal "gcpckms" {
  project     = "your-project"
  region      = "global"
  key_ring    = "openbao"
  crypto_key  = "unseal"
}

# OR Azure Key Vault
seal "azurekeyvault" {
  tenant_id  = "your-tenant-id"
  vault_name = "your-vault"
  key_name   = "unseal"
}
```

### 4. Configure AppRole Authentication

```bash
# Enable AppRole auth
bao auth enable approle

# Create role for Django
bao write auth/approle/role/django-app \
  token_policies="django-app" \
  token_ttl=1h \
  token_max_ttl=4h \
  secret_id_ttl=24h

# Get role ID and secret ID
bao read auth/approle/role/django-app/role-id
bao write -f auth/approle/role/django-app/secret-id

# Use in Django
export VAULT_ROLE_ID=<role-id>
export VAULT_SECRET_ID=<secret-id>
```

### 5. Create Production Policies

The `django-app` policy (already created in init script):

```hcl
# Read application secrets
path "xcapit/data/django/*" {
  capabilities = ["read", "list"]
}

path "xcapit/data/database/*" {
  capabilities = ["read"]
}

path "xcapit/data/api-keys/*" {
  capabilities = ["read", "list"]
}

path "xcapit/data/fhe/*" {
  capabilities = ["read"]
}
```

## API Reference

### Health Check

```bash
curl http://localhost:8200/v1/sys/health
```

### Read Secret

```bash
curl -H "X-Vault-Token: $BAO_TOKEN" \
  http://localhost:8200/v1/xcapit/data/django/config
```

### Write Secret

```bash
curl -X POST -H "X-Vault-Token: $BAO_TOKEN" \
  -d '{"data": {"key": "value"}}' \
  http://localhost:8200/v1/xcapit/data/path/to/secret
```

### List Secrets

```bash
curl -X LIST -H "X-Vault-Token: $BAO_TOKEN" \
  http://localhost:8200/v1/xcapit/metadata/
```

## Security Best Practices

1. **Never use dev mode in production**
2. **Use auto-unseal with cloud KMS**
3. **Enable audit logging**
4. **Use AppRole authentication for applications**
5. **Rotate secrets regularly**
6. **Use short TTLs for tokens**
7. **Enable TLS for all connections**
8. **Store unseal keys in separate secure locations**

## Troubleshooting

### Cannot connect to OpenBao

```bash
# Check if container is running
docker compose ps

# Check logs
docker logs xcapit-fhe-openbao-dev

# Test connection
curl http://localhost:8200/v1/sys/health
```

### Permission denied

```bash
# Check token
bao token lookup

# Verify policies
bao token capabilities xcapit/data/django/config
```

### Secret not found

```bash
# List available secrets
bao kv list -mount=xcapit django/

# Check if path exists
bao kv get -mount=xcapit django/config
```

## Links

- [OpenBao Documentation](https://openbao.org/docs/)
- [OpenBao GitHub](https://github.com/openbao/openbao)
- [hvac Python Client](https://hvac.readthedocs.io/)
