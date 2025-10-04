#!/bin/bash

# Load balancer testing script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LB_URL="http://localhost"
API_URL="${LB_URL}/api/v1"

echo -e "${BLUE}Testing Load Balancer Configuration...${NC}"

# Test 1: Health check
echo -e "${YELLOW}1. Testing Nginx health check...${NC}"
if curl -f -s "${LB_URL}/nginx-health" > /dev/null; then
    echo -e "${GREEN}✓ Nginx health check passed${NC}"
else
    echo -e "${RED}✗ Nginx health check failed${NC}"
    exit 1
fi

# Test 2: API health check
echo -e "${YELLOW}2. Testing API health check...${NC}"
if curl -f -s "${API_URL}/health" > /dev/null; then
    echo -e "${GREEN}✓ API health check passed${NC}"
else
    echo -e "${RED}✗ API health check failed${NC}"
    exit 1
fi

# Test 3: Root endpoint
echo -e "${YELLOW}3. Testing root endpoint...${NC}"
if curl -f -s "${LB_URL}/" > /dev/null; then
    echo -e "${GREEN}✓ Root endpoint accessible${NC}"
else
    echo -e "${RED}✗ Root endpoint failed${NC}"
    exit 1
fi

# Test 4: Documentation endpoints
echo -e "${YELLOW}4. Testing documentation endpoints...${NC}"
if curl -f -s "${LB_URL}/docs" > /dev/null; then
    echo -e "${GREEN}✓ Swagger docs accessible${NC}"
else
    echo -e "${RED}✗ Swagger docs failed${NC}"
fi

if curl -f -s "${LB_URL}/redoc" > /dev/null; then
    echo -e "${GREEN}✓ ReDoc accessible${NC}"
else
    echo -e "${RED}✗ ReDoc failed${NC}"
fi

# Test 5: Rate limiting
echo -e "${YELLOW}5. Testing rate limiting...${NC}"
echo "Sending 15 requests to test rate limiting (limit: 10r/s)..."
for i in {1..15}; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health")
    if [ "$response" = "200" ]; then
        echo -n "."
    else
        echo -e "\n${YELLOW}Request $i returned status: $response${NC}"
    fi
    sleep 0.1
done
echo -e "\n${GREEN}✓ Rate limiting test completed${NC}"

# Test 6: Load balancing (if multiple replicas)
echo -e "${YELLOW}6. Testing load balancing...${NC}"
echo "Sending multiple requests to check load distribution..."
for i in {1..10}; do
    response=$(curl -s "${API_URL}/model/info" | jq -r '.device' 2>/dev/null || echo "unknown")
    echo "Request $i: $response"
    sleep 0.5
done

# Test 7: CORS headers
echo -e "${YELLOW}7. Testing CORS headers...${NC}"
cors_response=$(curl -s -I -X OPTIONS "${API_URL}/classify" -H "Origin: http://localhost:3000")
if echo "$cors_response" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✓ CORS headers present${NC}"
else
    echo -e "${RED}✗ CORS headers missing${NC}"
fi

# Test 8: Large file upload (if test image available)
echo -e "${YELLOW}8. Testing large file upload...${NC}"
if [ -f "test-image.jpg" ]; then
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
        -F "file=@test-image.jpg" \
        -F "top_k=5" \
        "${API_URL}/classify")
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ Large file upload test passed${NC}"
    else
        echo -e "${RED}✗ Large file upload test failed (status: $response)${NC}"
    fi
else
    echo -e "${YELLOW}No test image found, skipping upload test${NC}"
fi

echo -e "${GREEN}Load balancer testing completed!${NC}"
echo -e "${YELLOW}Load balancer URL: ${LB_URL}${NC}"
echo -e "${YELLOW}API URL: ${API_URL}${NC}"
echo -e "${YELLOW}Documentation: ${LB_URL}/docs${NC}"
