#!/bin/bash

# Performance testing script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BASE_URL="http://localhost"
TEST_TYPE="comprehensive"
DURATION=60
RPS=10
WORKERS=50
ITERATIONS=100

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            BASE_URL="$2"
            shift 2
            ;;
        --test)
            TEST_TYPE="$2"
            shift 2
            ;;
        --duration)
            DURATION="$2"
            shift 2
            ;;
        --rps)
            RPS="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --iterations)
            ITERATIONS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --url URL          Base URL of the service (default: http://localhost)"
            echo "  --test TYPE        Test type: health, model_info, classification, stress, memory, latency, comprehensive (default: comprehensive)"
            echo "  --duration SECONDS Test duration in seconds (default: 60)"
            echo "  --rps RATE         Requests per second (default: 10)"
            echo "  --workers COUNT    Number of workers for stress test (default: 50)"
            echo "  --iterations COUNT Number of iterations for latency/memory tests (default: 100)"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}Starting Performance Tests${NC}"
echo "Base URL: $BASE_URL"
echo "Test Type: $TEST_TYPE"
echo "Duration: $DURATION seconds"
echo "RPS: $RPS"
echo "Workers: $WORKERS"
echo "Iterations: $ITERATIONS"
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

# Run performance tests
echo -e "${YELLOW}Running performance tests...${NC}"

if [ "$TEST_TYPE" = "comprehensive" ]; then
    echo -e "${BLUE}Running comprehensive benchmark suite${NC}"
    python performance/benchmark.py --url "$BASE_URL" --test comprehensive
elif [ "$TEST_TYPE" = "locust" ]; then
    echo -e "${BLUE}Running Locust load tests${NC}"
    locust -f performance/locustfile.py --host="$BASE_URL" --users 10 --spawn-rate 2 --run-time 60s --headless
else
    echo -e "${BLUE}Running $TEST_TYPE benchmark${NC}"
    python performance/benchmark.py --url "$BASE_URL" --test "$TEST_TYPE" --duration "$DURATION" --rps "$RPS" --workers "$WORKERS" --iterations "$ITERATIONS"
fi

echo ""
echo -e "${GREEN}Performance tests completed!${NC}"
echo ""
echo -e "${YELLOW}Results saved in: performance/results/${NC}"
echo ""
echo -e "${YELLOW}To view results:${NC}"
echo "  ls -la performance/results/"
echo "  cat performance/results/*_analysis_*.json"
echo ""
echo -e "${YELLOW}To run Locust web interface:${NC}"
echo "  locust -f performance/locustfile.py --host=$BASE_URL"
