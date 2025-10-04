#!/bin/bash

# Start monitoring stack script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Monitoring Stack...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Start the main application first
echo -e "${YELLOW}Starting main application...${NC}"
docker-compose up -d

# Wait for application to be ready
echo -e "${YELLOW}Waiting for application to be ready...${NC}"
sleep 10

# Start monitoring stack
echo -e "${YELLOW}Starting monitoring stack...${NC}"
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for monitoring services to be ready
echo -e "${YELLOW}Waiting for monitoring services to be ready...${NC}"
sleep 15

# Check service status
echo -e "${YELLOW}Checking service status...${NC}"
docker-compose ps
docker-compose -f docker-compose.monitoring.yml ps

echo -e "${GREEN}Monitoring stack started successfully!${NC}"
echo -e "${YELLOW}Access URLs:${NC}"
echo "  Application: http://localhost"
echo "  Prometheus:  http://localhost:9090"
echo "  Grafana:     http://localhost:3000 (admin/admin)"
echo "  Node Exporter: http://localhost:9100"
echo "  cAdvisor:    http://localhost:8080"

echo -e "${YELLOW}To view logs:${NC}"
echo "  docker-compose logs -f"
echo "  docker-compose -f docker-compose.monitoring.yml logs -f"

echo -e "${YELLOW}To stop monitoring:${NC}"
echo "  docker-compose -f docker-compose.monitoring.yml down"
