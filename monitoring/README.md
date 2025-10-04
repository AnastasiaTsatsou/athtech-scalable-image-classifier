# 📊 Monitoring Setup

This directory contains the complete monitoring infrastructure for the Image Classifier application using Prometheus and Grafana.

## 🚀 Quick Start

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Check status
docker-compose -f docker-compose.monitoring.yml ps
```

## 🔗 Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Node Exporter** | http://localhost:9100 | - |
| **cAdvisor** | http://localhost:8080 | - |
| **Nginx Exporter** | http://localhost:9113 | - |

## 📁 Directory Structure

```
monitoring/
├── prometheus.yml              # Prometheus configuration
├── alert_rules.yml             # Alert rules for Prometheus
├── grafana/
│   ├── dashboards/
│   │   ├── comprehensive-dashboard.json    # Main dashboard
│   │   └── image-classifier-dashboard.json # Legacy dashboard
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml             # Prometheus datasource
│       └── dashboards/
│           └── dashboard.yml              # Dashboard provisioning
└── README.md
```

## 🎯 Features

### **Comprehensive Dashboard**
- **Service Overview**: Real-time status of all services
- **Request Metrics**: Rate, response time, error rate
- **Classification Metrics**: Model performance, confidence, duration
- **System Resources**: CPU, memory usage
- **Quick Links**: Direct access to related services

### **Alerting**
- **High Error Rate**: >5% error rate for 2 minutes
- **High Response Time**: >2s 95th percentile for 5 minutes
- **Service Down**: Service unavailable for 1 minute
- **Resource Alerts**: High CPU/memory usage
- **Low Confidence**: Classification confidence <30%

### **Data Sources**
- **Prometheus**: Metrics collection and storage
- **Node Exporter**: System-level metrics
- **cAdvisor**: Container metrics
- **Nginx Exporter**: Load balancer metrics

## 🔧 Configuration

### **Prometheus Scraping**
- **Image Classifier**: All Docker Compose and Kubernetes instances
- **System Metrics**: Node exporter for host metrics
- **Container Metrics**: cAdvisor for container performance
- **Load Balancer**: Nginx exporter for traffic metrics

### **Grafana Dashboards**
- **Auto-provisioned**: Dashboards loaded automatically
- **Templated**: Variables for instance and model selection
- **Linked**: Direct links to Prometheus, Kibana, and API docs

## 📊 Key Metrics

### **Application Metrics**
- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request duration histogram
- `image_classifications_total`: Classification events
- `image_classification_duration_seconds`: Classification time
- `image_classification_confidence`: Classification confidence

### **System Metrics**
- `container_cpu_usage_seconds_total`: CPU usage
- `container_memory_usage_bytes`: Memory usage
- `node_filesystem_avail_bytes`: Disk space
- `up`: Service availability

## 🚨 Alerting

### **Critical Alerts**
- Service down
- High error rate (>5%)
- Elasticsearch cluster red

### **Warning Alerts**
- High response time (>2s)
- High resource usage (>80%)
- Low classification confidence (<30%)

## 🔗 Integration

### **Cross-Service Links**
- **Grafana → Prometheus**: Direct query links
- **Grafana → Kibana**: Log analysis links
- **Grafana → API Docs**: Application documentation
- **Prometheus → Grafana**: Dashboard links

### **External Links**
- **API Documentation**: http://localhost:80/docs
- **Health Check**: http://localhost:80/health
- **Performance Testing**: http://localhost:8089

## 🛠️ Troubleshooting

### **Common Issues**

1. **No metrics appearing**
   ```bash
   # Check Prometheus targets
   curl http://localhost:9090/api/v1/targets
   
   # Check service health
   docker-compose -f docker-compose.monitoring.yml ps
   ```

2. **Dashboard not loading**
   ```bash
   # Restart Grafana
   docker-compose -f docker-compose.monitoring.yml restart grafana
   
   # Check logs
   docker logs grafana
   ```

3. **Alerts not firing**
   ```bash
   # Check alert rules
   curl http://localhost:9090/api/v1/rules
   
   # Check alertmanager (if configured)
   curl http://localhost:9093/api/v1/alerts
   ```

### **Useful Queries**

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# Response time 95th percentile
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Classification rate
rate(image_classifications_total[5m])

# Memory usage
container_memory_usage_bytes{name=~".*image-classifier.*"}
```

## 📈 Performance Optimization

### **Retention Policies**
- **Prometheus**: 200 hours (8.3 days)
- **Grafana**: Unlimited (uses Prometheus data)

### **Scrape Intervals**
- **Application metrics**: 10s
- **System metrics**: 15s
- **Infrastructure metrics**: 30s

## 🔒 Security

### **Access Control**
- **Grafana**: Basic auth (admin/admin)
- **Prometheus**: No authentication (internal network)
- **Exporters**: No authentication (internal network)

### **Network Isolation**
- All services run in `monitoring` network
- No external access except configured ports
- Internal service discovery via Docker DNS

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Node Exporter](https://github.com/prometheus/node_exporter)
- [cAdvisor](https://github.com/google/cadvisor)