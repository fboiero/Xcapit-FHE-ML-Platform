# =============================================================================
# Outputs — URLs and connection info after terraform apply
# =============================================================================

output "alb_dns_name" {
  description = "ALB DNS name — use this to access the platform (or point your domain here)"
  value       = aws_lb.main.dns_name
}

output "api_url" {
  description = "API base URL"
  value       = "http${var.acm_certificate_arn != "" ? "s" : ""}://${var.domain_name != "" ? var.domain_name : aws_lb.main.dns_name}/api/v2/"
}

output "docs_url" {
  description = "Interactive API documentation (Swagger UI)"
  value       = "http${var.acm_certificate_arn != "" ? "s" : ""}://${var.domain_name != "" ? var.domain_name : aws_lb.main.dns_name}/api/v2/docs/"
}

output "dashboard_url" {
  description = "Dashboard URL"
  value       = "http${var.acm_certificate_arn != "" ? "s" : ""}://${var.domain_name != "" ? var.domain_name : aws_lb.main.dns_name}/"
}

output "ecr_api_repository" {
  description = "ECR repository URL for the API image"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_dashboard_repository" {
  description = "ECR repository URL for the dashboard image"
  value       = aws_ecr_repository.dashboard.repository_url
}

output "rds_endpoint" {
  description = "RDS cluster endpoint (for debugging — app uses Secrets Manager)"
  value       = aws_rds_cluster.main.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint (for debugging)"
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
}

output "ecs_cluster_name" {
  description = "ECS cluster name (for ecs exec, logs, etc.)"
  value       = aws_ecs_cluster.main.name
}
