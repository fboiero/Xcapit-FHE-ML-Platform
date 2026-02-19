#!/bin/bash
set -e

# ============================================
# Xcapit FHE API - AWS ECS Deployment Script
# ============================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Required environment variables
REQUIRED_VARS=(
    "AWS_ACCOUNT_ID"
    "AWS_REGION"
    "ECR_REPO_NAME"
    "ECS_CLUSTER_NAME"
    "ECS_SERVICE_NAME"
)

# Check required variables
echo -e "${YELLOW}Checking required environment variables...${NC}"
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: $var is not set${NC}"
        exit 1
    fi
done

# Set defaults
IMAGE_TAG=${IMAGE_TAG:-$(git rev-parse --short HEAD)}
ECR_REPO_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

echo -e "${GREEN}=== Xcapit FHE API Deployment ===${NC}"
echo "Region: ${AWS_REGION}"
echo "ECR Repo: ${ECR_REPO_URL}"
echo "Image Tag: ${IMAGE_TAG}"
echo "ECS Cluster: ${ECS_CLUSTER_NAME}"
echo "ECS Service: ${ECS_SERVICE_NAME}"
echo ""

# Step 1: Login to ECR
echo -e "${YELLOW}Step 1: Logging in to ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Step 2: Build Docker image
echo -e "${YELLOW}Step 2: Building Docker image...${NC}"
docker build -t ${ECR_REPO_NAME}:${IMAGE_TAG} -t ${ECR_REPO_NAME}:latest --target production .

# Step 3: Tag image for ECR
echo -e "${YELLOW}Step 3: Tagging image...${NC}"
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${ECR_REPO_URL}:${IMAGE_TAG}
docker tag ${ECR_REPO_NAME}:latest ${ECR_REPO_URL}:latest

# Step 4: Push to ECR
echo -e "${YELLOW}Step 4: Pushing to ECR...${NC}"
docker push ${ECR_REPO_URL}:${IMAGE_TAG}
docker push ${ECR_REPO_URL}:latest

# Step 5: Update ECS Service
echo -e "${YELLOW}Step 5: Updating ECS service...${NC}"
aws ecs update-service \
    --cluster ${ECS_CLUSTER_NAME} \
    --service ${ECS_SERVICE_NAME} \
    --force-new-deployment \
    --region ${AWS_REGION}

# Step 6: Wait for deployment
echo -e "${YELLOW}Step 6: Waiting for deployment to stabilize...${NC}"
aws ecs wait services-stable \
    --cluster ${ECS_CLUSTER_NAME} \
    --services ${ECS_SERVICE_NAME} \
    --region ${AWS_REGION}

echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo "Image: ${ECR_REPO_URL}:${IMAGE_TAG}"
