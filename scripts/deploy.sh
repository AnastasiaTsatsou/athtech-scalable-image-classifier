#!/bin/bash

# Deployment script for Scalable Image Classifier on Kubernetes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="image-classifier"
IMAGE_NAME="scalable-image-classifier"
TAG="latest"

echo -e "${BLUE}Deploying Scalable Image Classifier to Kubernetes...${NC}"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Kubernetes cluster is accessible${NC}"

# Build and push Docker image (if needed)
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:${TAG} .

# Apply Kubernetes manifests
echo -e "${YELLOW}Applying Kubernetes manifests...${NC}"

# Apply using kustomize
kubectl apply -k k8s/

# Wait for deployment to be ready
echo -e "${YELLOW}Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/image-classifier -n ${NAMESPACE}

# Check deployment status
echo -e "${YELLOW}Checking deployment status...${NC}"
kubectl get pods -n ${NAMESPACE}
kubectl get services -n ${NAMESPACE}
kubectl get ingress -n ${NAMESPACE}

# Get service URL
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}Service endpoints:${NC}"
kubectl get service image-classifier-service -n ${NAMESPACE} -o wide

echo -e "${YELLOW}To access the service:${NC}"
echo "1. Port forward: kubectl port-forward service/image-classifier-service 8000:80 -n ${NAMESPACE}"
echo "2. Then visit: http://localhost:8000"
echo "3. API docs: http://localhost:8000/docs"

echo -e "${YELLOW}To check logs:${NC}"
echo "kubectl logs -f deployment/image-classifier -n ${NAMESPACE}"

echo -e "${YELLOW}To scale the deployment:${NC}"
echo "kubectl scale deployment image-classifier --replicas=5 -n ${NAMESPACE}"
