#!/bin/bash

set -e  # Exit on any error

# Configuration
KIBANA_URL="http://localhost:5601"
DASHBOARD_FILE="/usr/share/kibana/saved_objects/complete-dashboard.ndjson"
MAX_RETRIES=30
RETRY_INTERVAL=10

echo "🚀 Starting Kibana dashboard import process..."

# Function to check if Kibana is ready
check_kibana_ready() {
  local response
  response=$(curl -s -w "%{http_code}" -o /dev/null "$KIBANA_URL/api/status" || echo "000")
  
  if [[ "$response" == "200" ]]; then
    return 0
  else
    return 1
  fi
}

# Wait for Kibana to be ready
echo "⏳ Waiting for Kibana to be ready..."
retry_count=0
while ! check_kibana_ready; do
  retry_count=$((retry_count + 1))
  if [ $retry_count -gt $MAX_RETRIES ]; then
    echo "❌ Kibana failed to start within expected time. Exiting..."
    exit 1
  fi
  echo "   Attempt $retry_count/$MAX_RETRIES - Kibana not ready yet, waiting ${RETRY_INTERVAL}s..."
  sleep $RETRY_INTERVAL
done

echo "✅ Kibana is ready! Waiting additional 30 seconds for full initialization..."
sleep 30

# Check if dashboard file exists
if [ ! -f "$DASHBOARD_FILE" ]; then
  echo "❌ Dashboard file not found at $DASHBOARD_FILE"
  exit 1
fi

echo "📊 Dashboard file found: $DASHBOARD_FILE"

# Import saved objects
echo "📥 Importing image classifier dashboard..."
response=$(curl -s -w "%{http_code}" -X POST "$KIBANA_URL/api/saved_objects/_import?overwrite=true" \
  -H "kbn-xsrf: true" \
  -F file=@"$DASHBOARD_FILE")

http_code="${response: -3}"
response_body="${response%???}"

if [ "$http_code" -eq 200 ]; then
  echo "✅ Image classifier dashboard imported successfully!"
  echo "📋 Import response: $response_body"
else
  echo "❌ Dashboard import failed with HTTP code: $http_code"
  echo "📋 Error response: $response_body"
  exit 1
fi

echo "🎉 Dashboard import process completed successfully!"

