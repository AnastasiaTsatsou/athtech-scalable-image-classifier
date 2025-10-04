# Logging Stack

This directory contains the logging configuration for the Scalable Image Classifier service using the ELK stack (Elasticsearch, Logstash, Kibana).

## Components

### Elasticsearch
- **Purpose**: Log storage and search engine
- **Port**: 9200
- **Data**: Stored in persistent volume
- **Index**: `image-classifier-logs-*` (daily rotation)

### Logstash
- **Purpose**: Log processing and transformation
- **Ports**: 5044 (Beats), 5000 (TCP/UDP)
- **Configuration**: `logstash/pipeline/logstash.conf`
- **Templates**: Custom index templates for structured logging

### Kibana
- **Purpose**: Log visualization and analysis
- **Port**: 5601
- **Dashboards**: Pre-configured image classifier dashboards
- **Features**: Search, filtering, visualization, alerting

### Filebeat
- **Purpose**: Log collection from files and containers
- **Configuration**: `filebeat/filebeat.yml`
- **Sources**: Application logs, Docker container logs

## Quick Start

### Using Docker Compose

```bash
# Start main application
docker-compose up -d

# Start logging stack
docker-compose -f docker-compose.logging.yml up -d

# Or use the convenience script
./scripts/start-logging.sh
```

### Using Kubernetes

```bash
# Deploy logging stack
kubectl apply -f k8s/logging/

# Check status
kubectl get pods -n logging

# Port forward for access
kubectl port-forward service/elasticsearch 9200:9200 -n logging
kubectl port-forward service/kibana 5601:5601 -n logging
```

## Access URLs

- **Application**: http://localhost
- **Kibana**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200
- **Logstash**: http://localhost:9600

## Log Structure

### Application Logs
All logs are structured in JSON format with the following fields:

```json
{
  "timestamp": "2025-10-04T18:30:00.000Z",
  "level": "INFO",
  "logger": "app.models.image_classifier",
  "message": "Image classification - resnet50 - 0.923 - 0.156s",
  "module": "image_classifier",
  "function": "predict",
  "line": 175,
  "thread": 12345,
  "process": 6789,
  "service": "image-classifier",
  "request_type": "classification",
  "model_name": "resnet50",
  "confidence": 0.923,
  "processing_time": 0.156,
  "top_k": 5,
  "image_size": 1024000,
  "status": "success"
}
```

### Request Logs
HTTP request logs include:

```json
{
  "timestamp": "2025-10-04T18:30:00.000Z",
  "level": "INFO",
  "logger": "app.logging.middleware",
  "message": "Request completed: POST /api/v1/classify - 200",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "url": "http://localhost:8000/api/v1/classify",
  "endpoint": "classify",
  "status_code": 200,
  "response_time": 0.234,
  "client_ip": "192.168.1.100",
  "user_agent": "curl/7.68.0"
}
```

### Error Logs
Error logs include exception details:

```json
{
  "timestamp": "2025-10-04T18:30:00.000Z",
  "level": "ERROR",
  "logger": "app.models.image_classifier",
  "message": "Error occurred: CUDA out of memory",
  "error_type": "RuntimeError",
  "error_message": "CUDA out of memory",
  "exception": {
    "type": "RuntimeError",
    "message": "CUDA out of memory",
    "traceback": ["Traceback (most recent call last):", "..."]
  },
  "model_name": "resnet50",
  "processing_time": 0.001,
  "status": "error"
}
```

## Kibana Dashboards

### Image Classifier Logs Overview
- **Log Level Distribution**: Pie chart of log levels
- **Request Timeline**: Timeline of API requests
- **Error Analysis**: Table of errors by type and endpoint
- **Performance Metrics**: Response time and processing time analysis

### Pre-configured Visualizations
1. **Log Level Distribution**: Distribution of INFO, WARNING, ERROR logs
2. **Request Timeline**: API requests over time
3. **Error Analysis**: Error breakdown by type and endpoint
4. **Classification Metrics**: Model performance and confidence scores
5. **Response Time Analysis**: API response time distribution
6. **Image Size Analysis**: Distribution of uploaded image sizes
7. **Model Usage**: Usage statistics by model type
8. **Error Trends**: Error rate trends over time

## Log Analysis Queries

### Common Kibana Queries

1. **View all errors**:
   ```
   level:ERROR
   ```

2. **View classification logs**:
   ```
   request_type:classification
   ```

3. **View API requests**:
   ```
   request_type:api
   ```

4. **View slow requests**:
   ```
   response_time:>1.0
   ```

5. **View high confidence classifications**:
   ```
   confidence:>0.9
   ```

6. **View specific model usage**:
   ```
   model_name:resnet50
   ```

7. **View errors by endpoint**:
   ```
   level:ERROR AND endpoint:classify
   ```

8. **View recent logs**:
   ```
   @timestamp:[now-1h TO now]
   ```

### Advanced Queries

1. **Error rate by endpoint**:
   ```
   level:ERROR | stats count by endpoint
   ```

2. **Average response time by endpoint**:
   ```
   request_type:api | stats avg(response_time) by endpoint
   ```

3. **Classification confidence distribution**:
   ```
   request_type:classification | stats count by confidence
   ```

4. **Image size distribution**:
   ```
   request_type:classification | stats count by image_size
   ```

## Configuration

### Log Levels
Set via environment variable:
```bash
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Log Format
Set via environment variable:
```bash
export LOG_FORMAT=json  # json, text
```

### Log Rotation
- **File size**: 10MB per file
- **Backup count**: 5 files
- **Location**: `logs/app.log`

### Elasticsearch Index
- **Pattern**: `image-classifier-logs-YYYY.MM.DD`
- **Rotation**: Daily
- **Retention**: Configurable (default: 30 days)

## Troubleshooting

### Common Issues

1. **Elasticsearch not starting**
   ```bash
   # Check Elasticsearch logs
   docker-compose -f docker-compose.logging.yml logs elasticsearch
   
   # Check disk space
   df -h
   
   # Check memory usage
   free -h
   ```

2. **Logstash not processing logs**
   ```bash
   # Check Logstash logs
   docker-compose -f docker-compose.logging.yml logs logstash
   
   # Check Logstash pipeline
   curl http://localhost:9600/_node/pipelines
   ```

3. **Kibana not loading dashboards**
   ```bash
   # Check Kibana logs
   docker-compose -f docker-compose.logging.yml logs kibana
   
   # Check Elasticsearch connection
   curl http://localhost:9200/_cluster/health
   ```

4. **No logs appearing in Kibana**
   ```bash
   # Check if logs are being generated
   tail -f logs/app.log
   
   # Check Filebeat status
   docker-compose -f docker-compose.logging.yml logs filebeat
   
   # Check Elasticsearch indices
   curl http://localhost:9200/_cat/indices
   ```

### Performance Tuning

1. **Elasticsearch Performance**
   - Adjust heap size in `ES_JAVA_OPTS`
   - Configure shard and replica settings
   - Monitor disk usage and cleanup old indices

2. **Logstash Performance**
   - Adjust worker threads
   - Optimize filter configurations
   - Monitor pipeline performance

3. **Kibana Performance**
   - Limit dashboard refresh rates
   - Use index patterns efficiently
   - Optimize query performance

## Security Considerations

- **Authentication**: Enable Elasticsearch security in production
- **Network**: Use TLS for inter-service communication
- **Access Control**: Implement role-based access control
- **Data Retention**: Configure appropriate retention policies
- **Sensitive Data**: Avoid logging sensitive information

## Integration with Monitoring

The logging stack integrates with the monitoring stack:

- **Prometheus**: Collects log metrics (log count, error rate)
- **Grafana**: Can display log-based metrics
- **Alerting**: Set up alerts based on log patterns

## Best Practices

1. **Structured Logging**: Always use structured JSON logs
2. **Log Levels**: Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
3. **Context**: Include relevant context in log messages
4. **Performance**: Avoid logging in hot paths
5. **Retention**: Configure appropriate log retention
6. **Monitoring**: Monitor log volume and storage usage
7. **Alerting**: Set up alerts for critical errors
8. **Documentation**: Document log formats and meanings
