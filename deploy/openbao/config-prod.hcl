# =============================================================================
# OpenBao Server Configuration - PRODUCTION
# =============================================================================
# Xcapit FHE-ML Platform - Secret Management
# =============================================================================

# Storage backend - PostgreSQL for production HA
storage "postgresql" {
  connection_url = "postgres://openbao:${OPENBAO_DB_PASSWORD}@postgres:5432/openbao?sslmode=require"
  table          = "vault_kv_store"
  ha_enabled     = true
  ha_table       = "vault_ha_locks"
}

# Alternative: Consul for HA (if using Consul)
# storage "consul" {
#   address = "consul:8500"
#   path    = "openbao/"
#   token   = "${CONSUL_TOKEN}"
# }

# HTTPS Listener with TLS
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/openbao/tls/server.crt"
  tls_key_file  = "/openbao/tls/server.key"

  # TLS configuration
  tls_min_version = "tls12"
  tls_cipher_suites = [
    "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
    "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
  ]
}

# API address
api_addr = "https://vault.xcapit.com:8200"

# Cluster address for HA
cluster_addr = "https://vault.xcapit.com:8201"

# UI enabled (consider disabling in highly secure environments)
ui = true

# Memory lock - enable in production for security
disable_mlock = false

# Logging
log_level = "warn"
log_format = "json"

# Telemetry for monitoring
telemetry {
  disable_hostname          = true
  prometheus_retention_time = "24h"
  statsd_address           = "statsd:8125"
}

# Seal configuration - Auto-unseal with cloud KMS (recommended for production)
# AWS KMS example:
# seal "awskms" {
#   region     = "us-east-1"
#   kms_key_id = "alias/openbao-unseal"
# }

# GCP Cloud KMS example:
# seal "gcpckms" {
#   project     = "xcapit-prod"
#   region      = "global"
#   key_ring    = "openbao"
#   crypto_key  = "unseal"
# }

# Azure Key Vault example:
# seal "azurekeyvault" {
#   tenant_id  = "${AZURE_TENANT_ID}"
#   vault_name = "xcapit-openbao"
#   key_name   = "unseal"
# }
