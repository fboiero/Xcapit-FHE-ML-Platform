# =============================================================================
# OpenBao Server Configuration
# =============================================================================
# Xcapit FHE-ML Platform - Secret Management
# =============================================================================

# Storage backend - File for development, Consul/PostgreSQL for production
storage "file" {
  path = "/openbao/data"
}

# Listener configuration
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true  # Enable TLS in production!
}

# API address for client connections
api_addr = "http://0.0.0.0:8200"

# Cluster address for HA mode
cluster_addr = "http://0.0.0.0:8201"

# UI enabled
ui = true

# Disable memory lock (required for Docker without IPC_LOCK capability)
disable_mlock = true

# Logging
log_level = "info"

# Telemetry (optional - for monitoring)
telemetry {
  disable_hostname = true
  prometheus_retention_time = "12h"
}
