# =============================================================================
# Xcapit FHE-ML Platform — Terraform Variables
# =============================================================================
# Copy terraform.tfvars.example → terraform.tfvars and fill in your values.

# --- Project ---

variable "project" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "xcapit-fhe-ml"
}

variable "environment" {
  description = "Deployment environment (dev, staging, production)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

# --- Networking ---

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of AZs (minimum 2 for ALB)"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# --- Database (RDS PostgreSQL) ---

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro" # dev: micro, prod: db.r6g.large
}

variable "db_allocated_storage" {
  description = "RDS storage in GB"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "xcapit_fhe_ml"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "xcapit"
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL master password (generate with: openssl rand -hex 16)"
  type        = string
  sensitive   = true
}

# --- Cache (ElastiCache Redis) ---

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro" # dev: micro, prod: cache.r6g.large
}

# --- ECS (Fargate) ---

variable "api_cpu" {
  description = "API task CPU units (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "API task memory in MB"
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "Number of API task replicas"
  type        = number
  default     = 1 # dev: 1, prod: 2+
}

variable "dashboard_cpu" {
  description = "Dashboard task CPU units"
  type        = number
  default     = 256
}

variable "dashboard_memory" {
  description = "Dashboard task memory in MB"
  type        = number
  default     = 512
}

# --- Application ---

variable "django_secret_key" {
  description = "Django SECRET_KEY (generate with: openssl rand -hex 32)"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Domain name for the platform (optional — skip for dev, use ALB DNS)"
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS (required if domain_name is set)"
  type        = string
  default     = ""
}

# --- Blockchain ---

variable "arbitrum_rpc_url" {
  description = "Arbitrum RPC endpoint (Sepolia for dev, One for prod)"
  type        = string
  default     = "https://sepolia-rollup.arbitrum.io/rpc"
}

# --- Tags ---

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}
