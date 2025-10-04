#!/bin/bash

# Locust load testing script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BASE_URL="http://localhost"
USERS=10
SPAWN_RATE=2
RUN_TIME="60s"
HEADLESS=true
WEB_UI=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            BASE_URL="$2"
            shift 2
            ;;
        --users)
            USERS="$2"
            shift 2
            ;;
        --spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        --run-time)
            RUN_TIME="$2"
            shift 2
            ;;
        --web-ui)
            WEB_UI=true
            HEADLESS=false
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --url URL          Base URL of the service (default: http://localhost)"
            echo "  --users COUNT      Number of concurrent users (default: 10)"
            echo "  --spawn-rate RATE  User spawn rate per second (default: 2)"
            echo "  --run-time TIME    Test run time (default: 60s)"
            echo "  --web-ui           Start Locust web interface instead of headless mode"
            echo "  --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --web-ui                    # Start web interface"
            echo "  $0 --users 50 --run-time 300s  # 50 users for 5 minutes"
            echo "  $0 --users 100 --spawn-rate 5  # 100 users spawning at 5/sec"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}Starting Locust Load Tests${NC}"
echo "Base URL: $BASE_URL"
echo "Users: $USERS"
echo "Spawn Rate: $SPAWN_RATE per second"
echo "Run Time: $RUN_TIME"
echo "Mode: $([ "$WEB_UI" = true ] && echo "Web UI" || echo "Headless")"
echo ""

# Check if service is running
echo -e "${YELLOW}Checking if service is running...${NC}"
if ! curl -s "$BASE_URL/api/v1/health" > /dev/null; then
    echo -e "${RED}Error: Service is not running at $BASE_URL${NC}"
    echo "Please start the service first:"
    echo "  docker-compose up -d"
    echo "  or"
    echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo -e "${GREEN}Service is running!${NC}"
echo ""

# Create results directory
mkdir -p performance/results

# Run Locust tests
echo -e "${YELLOW}Starting Locust tests...${NC}"

if [ "$WEB_UI" = true ]; then
    echo -e "${BLUE}Starting Locust web interface${NC}"
    echo "Open your browser and go to: http://localhost:8089"
    echo "Press Ctrl+C to stop"
    echo ""
    locust -f performance/locustfile.py --host="$BASE_URL"
else
    echo -e "${BLUE}Running Locust in headless mode${NC}"
    timestamp=$(date +"%Y%m%d_%H%M%S")
    results_file="performance/results/locust_results_${timestamp}.csv"
    
    locust -f performance/locustfile.py \
           --host="$BASE_URL" \
           --users="$USERS" \
           --spawn-rate="$SPAWN_RATE" \
           --run-time="$RUN_TIME" \
           --headless \
           --csv="performance/results/locust_${timestamp}"
    
    echo ""
    echo -e "${GREEN}Locust tests completed!${NC}"
    echo ""
    echo -e "${YELLOW}Results saved:${NC}"
    echo "  CSV: performance/results/locust_${timestamp}_stats.csv"
    echo "  HTML: performance/results/locust_${timestamp}_stats.html"
    echo ""
    echo -e "${YELLOW}To view results:${NC}"
    echo "  cat performance/results/locust_${timestamp}_stats.csv"
    echo "  open performance/results/locust_${timestamp}_stats.html"
fi
