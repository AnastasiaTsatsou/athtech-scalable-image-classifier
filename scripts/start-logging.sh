#!/bin/bash

# Start logging stack script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Logging Stack...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Start the main application first
echo -e "${YELLOW}Starting main application...${NC}"
docker-compose up -d

# Wait for application to be ready
echo -e "${YELLOW}Waiting for application to be ready...${NC}"
sleep 10

# Start logging stack
echo -e "${YELLOW}Starting logging stack...${NC}"
docker-compose -f docker-compose.logging.yml up -d

# Wait for logging services to be ready
echo -e "${YELLOW}Waiting for logging services to be ready...${NC}"
sleep 30

# Check service status
echo -e "${YELLOW}Checking service status...${NC}"
docker-compose ps
docker-compose -f docker-compose.logging.yml ps

echo -e "${GREEN}Logging stack started successfully!${NC}"
echo -e "${YELLOW}Access URLs:${NC}"
echo "  Application: http://localhost"
echo "  Kibana:      http://localhost:5601"
echo "  Elasticsearch: http://localhost:9200"
echo "  Logstash:    http://localhost:9600"

echo -e "${YELLOW}To view logs:${NC}"
echo "  docker-compose logs -f"
echo "  docker-compose -f docker-compose.logging.yml logs -f"

echo -e "${YELLOW}To stop logging:${NC}"
echo "  docker-compose -f docker-compose.logging.yml down"

echo -e "${YELLOW}To view application logs in Kibana:${NC}"
echo "  1. Go to http://localhost:5601"
echo "  2. Create index pattern: image-classifier-logs-*"
echo "  3. Go to Discover to view logs"
