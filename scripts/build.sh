#!/bin/bash

# Build script for Scalable Image Classifier Docker image

set -e

# Configuration
IMAGE_NAME="scalable-image-classifier"
TAG="latest"
REGISTRY=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Scalable Image Classifier Docker image...${NC}"

# Build the Docker image
echo -e "${YELLOW}Building image: ${IMAGE_NAME}:${TAG}${NC}"
docker build -t ${IMAGE_NAME}:${TAG} .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker image built successfully!${NC}"
    
    # Show image size
    echo -e "${YELLOW}Image size:${NC}"
    docker images ${IMAGE_NAME}:${TAG} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
    
    # Optional: Run basic test
    echo -e "${YELLOW}Running basic container test...${NC}"
    docker run --rm -d --name test-container -p 8001:8000 ${IMAGE_NAME}:${TAG}
    
    # Wait for container to start
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost:8001/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Container test passed!${NC}"
    else
        echo -e "${RED}✗ Container test failed!${NC}"
    fi
    
    # Clean up test container
    docker stop test-container > /dev/null 2>&1
    
else
    echo -e "${RED}✗ Docker build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${YELLOW}To run the container:${NC}"
echo "  docker run -p 8000:8000 ${IMAGE_NAME}:${TAG}"
echo -e "${YELLOW}Or use docker-compose:${NC}"
echo "  docker-compose up"
