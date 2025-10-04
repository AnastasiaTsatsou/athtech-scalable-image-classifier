# 📝 Logging Setup

This directory contains the complete logging infrastructure for the Image Classifier application using the ELK stack (Elasticsearch, Logstash, Kibana).

## 🚀 Quick Start

```bash
# Start logging stack
docker-compose -f docker-compose.logging.yml up -d

# Check status
docker-compose -f docker-compose.logging.yml ps
```

## 🔗 Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Kibana** | http://localhost:5601 | Log visualization and analysis |
| **Elasticsearch** | http://localhost:9200 | Log storage and search API |
| **Logstash** | http://localhost:9600 | Log processing status |
| **Filebeat** | - | Log collection (no UI) |

## 📁 Directory Structure

```
logging/
├── filebeat/
│   └── filebeat.yml                    # Filebeat configuration
├── logstash/
│   ├── config/
│   │   └── logstash.yml               # Logstash configuration
│   ├── pipeline/
│   │   └── logstash.conf              # Log processing pipeline
│   └── templates/
│       └── image-classifier-template.json  # Elasticsearch index template
├── kibana/
│   └── dashboards/
│       ├── comprehensive-logs-dashboard.json  # Main logs dashboard
│       └── image-classifier-logs.json        # Legacy dashboard
└── README.md
```

## 🎯 Features

### **Comprehensive Logging Dashboard**
- **Log Level Distribution**: Pie chart of log levels
- **Request Timeline**: Time-series of API requests
- **Error Analysis**: Detailed error breakdown by type and endpoint
- **Classification Metrics**: ML model performance logs
- **Performance Metrics**: Processing time analysis

### **Log Collection**
- **Application Logs**: Structured JSON logs from FastAPI
- **Container Logs**: Docker container stdout/stderr
- **System Logs**: Host system logs (if configured)

### **Log Processing**
- **Structured Parsing**: JSON log parsing and enrichment
- **Field Extraction**: Automatic field extraction from log messages
- **Index Templates**: Optimized Elasticsearch index mapping

## 🔧 Configuration

### **Logstash Pipeline**
```ruby
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][log_type] == "application" {
    json {
      source => "message"
    }
  }
  
  # Add timestamp parsing
  date {
    match => [ "timestamp", "ISO8601" ]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "image-classifier-logs-%{+YYYY.MM.dd}"
  }
}
```

### **Filebeat Configuration**
- **Docker Logs**: Collects from `/var/lib/docker/containers`
- **Application Logs**: Collects from `./logs` directory
- **Log Processing**: Sends to Logstash on port 5044

### **Elasticsearch Index Template**
- **Index Pattern**: `image-classifier-logs-*`
- **Field Mappings**: Optimized for log analysis
- **Retention**: 30 days (configurable)

## 📊 Log Structure

### **Application Logs**
```json
{
  "@timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "logger": "app.models.image_classifier",
  "message": "Classification completed",
  "event_type": "classification",
  "model_name": "resnet50",
  "confidence": 0.95,
  "processing_time": 0.123,
  "image_size": 1024,
  "status": "success"
}
```

### **Request Logs**
```json
{
  "@timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "logger": "app.logging.middleware",
  "message": "Request completed",
  "request_type": "api",
  "method": "POST",
  "endpoint": "/classify",
  "status_code": 200,
  "response_time": 0.456,
  "user_agent": "curl/7.68.0"
}
```

### **Error Logs**
```json
{
  "@timestamp": "2024-01-01T12:00:00.000Z",
  "level": "ERROR",
  "logger": "app.models.image_classifier",
  "message": "Classification failed",
  "event_type": "error",
  "error_type": "ValueError",
  "error_message": "Invalid image format",
  "context": {
    "model_name": "resnet50",
    "processing_time": 0.001,
    "image_size": 0
  }
}
```

## 🔍 Kibana Dashboards

### **Main Dashboard Features**
1. **Log Level Distribution**: Visual breakdown of log levels
2. **Request Timeline**: API request patterns over time
3. **Error Analysis**: Error frequency and types
4. **Classification Metrics**: ML model performance
5. **Performance Metrics**: Processing time trends

### **Search Capabilities**
- **Full-text search**: Search across all log fields
- **Filtered queries**: Filter by log level, time range, service
- **Saved searches**: Save common queries for quick access
- **Alerting**: Set up alerts based on log patterns

## 🚨 Log-based Alerting

### **Error Rate Alerts**
```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-5m"}}}
      ]
    }
  }
}
```

### **Performance Alerts**
```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"event_type": "classification"}},
        {"range": {"processing_time": {"gte": 2.0}}}
      ]
    }
  }
}
```

## 🔗 Integration

### **Cross-Service Links**
- **Kibana → Grafana**: Metrics correlation
- **Kibana → API Docs**: Application documentation
- **Kibana → Prometheus**: Metrics queries

### **External Links**
- **API Documentation**: http://localhost:80/docs
- **Health Check**: http://localhost:80/health
- **Grafana Dashboards**: http://localhost:3000

## 🛠️ Troubleshooting

### **Common Issues**

1. **No logs appearing in Kibana**
   ```bash
   # Check Elasticsearch health
   curl http://localhost:9200/_cluster/health
   
   # Check Logstash status
   curl http://localhost:9600/_node/stats
   
   # Check Filebeat logs
   docker logs filebeat
   ```

2. **Logstash not processing logs**
   ```bash
   # Check Logstash configuration
   docker exec logstash logstash --config.test_and_exit -f /usr/share/logstash/pipeline/logstash.conf
   
   # Check Logstash logs
   docker logs logstash
   ```

3. **Elasticsearch cluster issues**
   ```bash
   # Check cluster health
   curl http://localhost:9200/_cluster/health?pretty
   
   # Check indices
   curl http://localhost:9200/_cat/indices?v
   ```

### **Useful Queries**

```json
# Find all errors in the last hour
{
  "query": {
    "bool": {
      "must": [
        {"match": {"level": "ERROR"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}

# Find slow classifications
{
  "query": {
    "bool": {
      "must": [
        {"match": {"event_type": "classification"}},
        {"range": {"processing_time": {"gte": 1.0}}}
      ]
    }
  }
}

# Find requests by endpoint
{
  "query": {
    "bool": {
      "must": [
        {"match": {"request_type": "api"}},
        {"match": {"endpoint": "/classify"}}
      ]
    }
  }
}
```

## 📈 Performance Optimization

### **Index Management**
- **Index Pattern**: Daily indices (`image-classifier-logs-YYYY.MM.DD`)
- **Shard Count**: 1 primary shard per index
- **Replica Count**: 0 (single node setup)
- **Refresh Interval**: 30 seconds

### **Retention Policy**
- **Default**: 30 days
- **Configurable**: Via Elasticsearch ILM policies
- **Cleanup**: Automatic deletion of old indices

## 🔒 Security

### **Access Control**
- **Kibana**: No authentication (internal network)
- **Elasticsearch**: No authentication (internal network)
- **Logstash**: No authentication (internal network)

### **Network Isolation**
- All services run in `logging` network
- No external access except configured ports
- Internal service discovery via Docker DNS

## 📚 Additional Resources

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
- [Logstash Documentation](https://www.elastic.co/guide/en/logstash/current/)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/)
- [Filebeat Documentation](https://www.elastic.co/guide/en/beats/filebeat/current/)