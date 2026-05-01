# Terraform — AWS Deployment

Infrastructure as Code for deploying Xcapit FHE-ML Platform on AWS.

## Architecture

```
Internet
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  VPC (10.0.0.0/16)                                              │
│                                                                  │
│  ┌─── Public Subnets (2 AZs) ───────────────────────┐          │
│  │                                                    │          │
│  │  ALB (Application Load Balancer)                   │          │
│  │    ├─ /api/* /health/* /admin/* → API (8000)       │          │
│  │    └─ /* → Dashboard (3000)                        │          │
│  │                                                    │          │
│  └────────────────────────────────────────────────────┘          │
│       │ (NAT Gateway)                                            │
│       ▼                                                          │
│  ┌─── Private Subnets (2 AZs) ──────────────────────┐          │
│  │                                                    │          │
│  │  ECS Fargate                                       │          │
│  │    ├─ API (Django + Gunicorn)                      │          │
│  │    └─ Dashboard (React + Nginx)                    │          │
│  │                                                    │          │
│  │  RDS Aurora Serverless v2 (PostgreSQL 16)          │          │
│  │  ElastiCache (Redis 7.1)                           │          │
│  │                                                    │          │
│  └────────────────────────────────────────────────────┘          │
│                                                                  │
│  ECR: xcapit-fhe-ml-{env}-api                                   │
│  ECR: xcapit-fhe-ml-{env}-dashboard                             │
│  Secrets Manager: xcapit-fhe-ml-{env}/django                    │
│  CloudWatch Logs: /ecs/xcapit-fhe-ml-{env}/*                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start (15 minutes)

### Prerequisites

- AWS CLI configured (`aws configure`)
- Terraform >= 1.5 (`brew install terraform`)
- Docker (for building images)

### 1. Configure

```bash
cd deploy/terraform
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars — at minimum set:
#   db_password       (openssl rand -hex 16)
#   django_secret_key (openssl rand -hex 32)
```

### 2. Deploy infrastructure

```bash
terraform init
terraform plan    # review what will be created
terraform apply   # create everything (~5 min)
```

### 3. Build and push images

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $(terraform output -raw ecr_api_repository | cut -d'/' -f1)

# Build and push API
docker build -t $(terraform output -raw ecr_api_repository):latest \
  --target production ../../backend_django
docker push $(terraform output -raw ecr_api_repository):latest

# Build and push Dashboard
docker build -t $(terraform output -raw ecr_dashboard_repository):latest \
  ../../dashboard
docker push $(terraform output -raw ecr_dashboard_repository):latest
```

### 4. Run migrations

```bash
# ECS exec into running API container
aws ecs execute-command \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --task $(aws ecs list-tasks --cluster $(terraform output -raw ecs_cluster_name) --service-name xcapit-fhe-ml-dev-api --query 'taskArns[0]' --output text) \
  --container api \
  --interactive \
  --command "python manage.py migrate"
```

### 5. Access the platform

```bash
terraform output
# alb_dns_name   = "xcapit-fhe-ml-dev-alb-123456.us-east-1.elb.amazonaws.com"
# api_url        = "http://xcapit-fhe-ml-dev-alb-123456.../api/v2/"
# docs_url       = "http://xcapit-fhe-ml-dev-alb-123456.../api/v2/docs/"
# dashboard_url  = "http://xcapit-fhe-ml-dev-alb-123456.../"
```

## Cost Estimates

| Environment | Monthly Cost | Notes |
|-------------|-------------|-------|
| **Dev** | ~$60-90 | Aurora Serverless min, t3.micro Redis, 1 Fargate task |
| **Staging** | ~$120-180 | Same as dev but 2 API replicas |
| **Production** | ~$300-500 | Aurora scaled, r6g Redis, 2+ Fargate tasks, NAT Gateway |

Biggest cost drivers: NAT Gateway (~$32/mo), RDS Aurora (~$30-200/mo), Fargate (~$15-50/service/mo).

## Environments

Use different `environment` values and separate state files:

```bash
# Dev
terraform workspace new dev
terraform apply -var="environment=dev"

# Production
terraform workspace new production
terraform apply -var="environment=production" \
  -var="api_desired_count=2" \
  -var="api_cpu=1024" \
  -var="api_memory=2048"
```

## Custom Domain + HTTPS

1. Create an ACM certificate in the same region
2. Add to terraform.tfvars:
   ```
   domain_name         = "platform.xcapit.com"
   acm_certificate_arn = "arn:aws:acm:us-east-1:..."
   ```
3. `terraform apply`
4. Point your DNS CNAME to the ALB DNS name

## Destroy

```bash
terraform destroy  # removes EVERYTHING — use with caution
```

For production, `deletion_protection` is enabled on ALB and RDS. Remove it first:
```bash
terraform apply -var="environment=dev"  # temporarily override
terraform destroy
```

## Files

| File | Purpose |
|------|---------|
| `main.tf` | All AWS resources (VPC, ECS, RDS, Redis, ALB, ECR, IAM) |
| `variables.tf` | Input variables with defaults and validation |
| `outputs.tf` | URLs and connection info after apply |
| `terraform.tfvars.example` | Template for your values (copy, don't commit original) |
