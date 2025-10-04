# Monitoring Stack

This directory contains the monitoring configuration for the Scalable Image Classifier service using Prometheus and Grafana.

## Components

### Prometheus
- **Purpose**: Metrics collection and storage
- **Port**: 9090
- **Configuration**: `prometheus.yml`
- **Data**: Stored in persistent volume

### Grafana
- **Purpose**: Metrics visualization and dashboards
- **Port**: 3000
- **Default Credentials**: admin/admin
- **Dashboards**: Pre-configured image classifier dashboard

### Node Exporter
- **Purpose**: System metrics collection
- **Port**: 9100
- **Metrics**: CPU, memory, disk, network usage

### cAdvisor
- **Purpose**: Container metrics collection
- **Port**: 8080
- **Metrics**: Container resource usage, performance

## Quick Start

### Using Docker Compose

```bash
# Start main application
docker-compose up -d

# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Or use the convenience script
./scripts/start-monitoring.sh
```

### Using Kubernetes

```bash
# Deploy monitoring stack
kubectl apply -f k8s/monitoring/

# Check status
kubectl get pods -n monitoring

# Port forward for access
kubectl port-forward service/prometheus 9090:9090 -n monitoring
kubectl port-forward service/grafana 3000:3000 -n monitoring
```

## Access URLs

- **Application**: http://localhost
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Node Exporter**: http://localhost:9100
- **cAdvisor**: http://localhost:8080

## Metrics Collected

### Application Metrics
- HTTP request count and duration
- Image classification count and duration
- Classification confidence scores
- Model loading time
- Error rates

### System Metrics
- CPU usage
- Memory usage
- Disk I/O
- Network I/O
- Container resource usage

### Custom Metrics
- Image size distribution
- Top-k prediction distribution
- Model information
- Active connections

## Grafana Dashboards

### Image Classifier Service Dashboard
- Request rate and response time
- Classification metrics
- Error rates
- System resource usage
- Custom application metrics

### Pre-configured Panels
1. **Request Rate**: HTTP requests per second
2. **Response Time**: 95th percentile response time
3. **HTTP Requests**: Request distribution by endpoint
4. **Image Classifications**: Classification rate by model
5. **Classification Duration**: Processing time distribution
6. **Classification Confidence**: Confidence score distribution
7. **Image Size Distribution**: Uploaded image size metrics
8. **Error Rate**: HTTP error percentage
9. **Active Connections**: Current active connections
10. **Memory Usage**: Application memory consumption

## Configuration

### Prometheus Configuration
Edit `prometheus.yml` to modify:
- Scrape intervals
- Target endpoints
- Retention policies
- Alert rules

### Grafana Configuration
- Default admin password: `admin`
- Dashboard auto-provisioning from `grafana/dashboards/`
- Plugin installation configured

## Monitoring Best Practices

### Alerting
Set up alerts for:
- High error rates (>5%)
- High response times (>1s)
- Low classification confidence (<0.5)
- High memory usage (>80%)
- Service down

### Dashboard Usage
1. **Real-time Monitoring**: Use 5-minute refresh for live monitoring
2. **Historical Analysis**: Use longer time ranges for trend analysis
3. **Troubleshooting**: Filter by specific endpoints or time ranges
4. **Performance Tuning**: Monitor metrics during load testing

### Metrics Interpretation
- **Request Rate**: Should be stable under normal load
- **Response Time**: Should be <500ms for 95th percentile
- **Error Rate**: Should be <1% under normal conditions
- **Memory Usage**: Should be stable, not continuously growing
- **Classification Duration**: Should be consistent for same model

## Troubleshooting

### Common Issues

1. **Prometheus not scraping metrics**
   ```bash
   # Check Prometheus targets
   curl http://localhost:9090/api/v1/targets
   
   # Check application metrics endpoint
   curl http://localhost/metrics
   ```

2. **Grafana not loading dashboards**
   ```bash
   # Check Grafana logs
   docker-compose -f docker-compose.monitoring.yml logs grafana
   
   # Verify Prometheus data source
   # Go to Grafana > Configuration > Data Sources
   ```

3. **Missing metrics**
   ```bash
   # Check if metrics endpoint is accessible
   curl http://localhost/metrics | grep image_classification
   
   # Verify Prometheus configuration
   docker-compose -f docker-compose.monitoring.yml exec prometheus cat /etc/prometheus/prometheus.yml
   ```

### Performance Tuning

1. **Prometheus Storage**
   - Adjust retention time in `prometheus.yml`
   - Monitor disk usage
   - Consider external storage for production

2. **Grafana Performance**
   - Limit dashboard refresh rates
   - Use query optimization
   - Monitor Grafana resource usage

3. **Metrics Collection**
   - Adjust scrape intervals based on needs
   - Filter unnecessary metrics
   - Use recording rules for complex queries

## Security Considerations

- Change default Grafana admin password
- Use HTTPS in production
- Restrict network access to monitoring ports
- Use authentication for Prometheus
- Encrypt sensitive configuration data

## Integration with CI/CD

- Include monitoring in deployment pipeline
- Validate metrics collection after deployment
- Set up automated alerting
- Monitor deployment success metrics
