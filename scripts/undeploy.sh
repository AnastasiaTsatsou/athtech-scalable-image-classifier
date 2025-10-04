#!/bin/bash

# Undeployment script for Scalable Image Classifier from Kubernetes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="image-classifier"

echo -e "${YELLOW}Undeploying Scalable Image Classifier from Kubernetes...${NC}"

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

# Delete resources using kustomize
echo -e "${YELLOW}Deleting Kubernetes resources...${NC}"
kubectl delete -k k8s/

# Wait for resources to be deleted
echo -e "${YELLOW}Waiting for resources to be deleted...${NC}"
kubectl wait --for=delete deployment/image-classifier -n ${NAMESPACE} --timeout=60s || true

# Check if namespace still exists
if kubectl get namespace ${NAMESPACE} &> /dev/null; then
    echo -e "${YELLOW}Deleting namespace...${NC}"
    kubectl delete namespace ${NAMESPACE}
fi

echo -e "${GREEN}Undeployment completed successfully!${NC}"
