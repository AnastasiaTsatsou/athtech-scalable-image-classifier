# OpenSearch Logging Stack

This directory contains the OpenSearch-based logging stack setup with preloaded dashboards.

## What's Different from ELK Stack

- **Fully Open Source**: No licensing restrictions on any features
- **Preloaded Dashboards**: Comes with working dashboards out of the box
- **Better Compatibility**: OpenSearch Dashboards 2.11.0 has better dashboard support
- **No Security Restrictions**: All features available without authentication

## Components

- **OpenSearch 2.11.0**: Open-source search and analytics engine
- **OpenSearch Dashboards 2.11.0**: Open-source data visualization platform
- **Logstash 8.11.0**: Log processing pipeline
- **Filebeat 8.11.0**: Log collection agent

## Quick Start

1. **Start the OpenSearch stack:**
   ```bash
   docker-compose -f docker-compose.opensearch.yml up -d
   ```

2. **Access the services:**
   - **OpenSearch Dashboards**: http://localhost:5601
   - **OpenSearch**: http://localhost:9200

3. **The dashboard will be automatically imported** and available at:
   - Dashboard: "Image Classifier Monitoring"

## Features

### Preloaded Dashboard
- **Log Count Over Time**: Shows log volume trends
- **Error Count Over Time**: Tracks error rates
- **Recent Logs Table**: Displays latest log entries

### No Licensing Issues
- All visualizations work without restrictions
- No "upgrade to default distribution" errors
- Full feature access for all users

## Troubleshooting

If the dashboard doesn't appear:
1. Wait 2-3 minutes for full initialization
2. Check container logs: `docker logs opensearch-dashboards`
3. Manually import: Go to Stack Management → Saved Objects → Import

## Migration from ELK

To switch from ELK to OpenSearch:
1. Stop ELK stack: `docker-compose -f docker-compose.logging.yml down`
2. Start OpenSearch: `docker-compose -f docker-compose.opensearch.yml up -d`
3. Access at http://localhost:5601

The data format is compatible, so your existing logs will work seamlessly.
