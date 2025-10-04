#!/bin/bash

# Stop monitoring stack script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping Monitoring Stack...${NC}"

# Stop monitoring stack
echo -e "${YELLOW}Stopping monitoring services...${NC}"
docker-compose -f docker-compose.monitoring.yml down

# Optionally stop main application
read -p "Do you want to stop the main application as well? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Stopping main application...${NC}"
    docker-compose down
fi

echo -e "${GREEN}Monitoring stack stopped successfully!${NC}"
