#!/bin/bash

# Wait for OpenSearch Dashboards to be ready
until curl -s http://localhost:5601/api/status | grep -q "green\|401"; do
  echo "Waiting for OpenSearch Dashboards to be ready..."
  sleep 5
done

echo "OpenSearch Dashboards is ready! Waiting additional 30 seconds for full initialization..."
sleep 30

echo "Importing saved objects..."

# Import saved objects
curl -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
  -H "osd-xsrf: true" \
  -F file=@/usr/share/opensearch-dashboards/saved_objects/image-classifier-dashboard.ndjson

if [ $? -eq 0 ]; then
  echo "✅ Dashboard import completed successfully!"
else
  echo "❌ Dashboard import failed!"
fi
