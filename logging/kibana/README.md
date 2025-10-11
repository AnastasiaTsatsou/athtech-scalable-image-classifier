# Kibana Dashboard Preload Setup

This directory contains the configuration for automatically preloading Kibana dashboards when the container starts.

## Files Overview

- `Dockerfile` - Custom Kibana image with dashboard preloading
- `import-dashboards.sh` - Script that imports dashboards after Kibana starts
- `dashboards/complete-dashboard.ndjson` - The dashboard to be preloaded
- `test-setup.sh` - Validation script to test the setup

## How It Works

1. **Custom Dockerfile**: Builds a Kibana image that includes your dashboard file and import script
2. **Import Script**: Runs in the background after Kibana starts, waiting for it to be ready
3. **Automatic Import**: Uses Kibana's REST API to import the dashboard automatically
4. **Error Handling**: Includes robust error handling and retry logic

## Dashboard File

The `complete-dashboard.ndjson` file contains:
- Index pattern for `image-classifier-logs-*`
- Comprehensive monitoring dashboard with multiple visualizations:
  - Request Success Rate (Gauge)
  - Average Response Time (Metric)
  - Requests Per Minute (Line Chart)
  - Log Level Distribution (Pie Chart)
  - Detailed Log Table
  - Endpoint Usage (Bar Chart)
  - Status Code Distribution (Pie Chart)
  - Response Time Over Time (Line Chart)

## Usage

### Test the Setup
```bash
cd logging/kibana
bash test-setup.sh
```

### Build and Run
```bash
# From project root
docker-compose up --build kibana
```

### View Dashboard
1. Wait for Kibana to start (check logs for "Dashboard import process completed successfully!")
2. Open http://localhost:5601
3. Navigate to Dashboards
4. Look for "Image Classifier Monitoring (Preloaded)"

## Troubleshooting

### Dashboard Not Appearing
1. Check Kibana logs for import errors
2. Verify Elasticsearch is running and accessible
3. Ensure the dashboard file is valid JSON

### Import Script Fails
1. Check if Kibana is fully started (wait longer)
2. Verify curl is available in the container
3. Check file permissions

### Common Issues
- **Permission errors**: The script automatically sets executable permissions
- **Network timeouts**: The script includes retry logic with configurable intervals
- **File not found**: The Dockerfile includes verification steps

## Configuration

You can modify these variables in `import-dashboards.sh`:
- `KIBANA_URL`: Kibana endpoint (default: http://localhost:5601)
- `MAX_RETRIES`: Maximum retry attempts (default: 30)
- `RETRY_INTERVAL`: Seconds between retries (default: 10)

## Adding More Dashboards

To add additional dashboards:
1. Place `.ndjson` files in the `dashboards/` directory
2. Modify `import-dashboards.sh` to import additional files
3. Rebuild the Docker image

## Monitoring

The import process provides detailed logging:
- 🚀 Process start
- ⏳ Waiting for Kibana
- ✅ Kibana ready confirmation
- 📊 Dashboard file verification
- 📥 Import progress
- 🎉 Success confirmation

Check the Kibana container logs to monitor the import process.
