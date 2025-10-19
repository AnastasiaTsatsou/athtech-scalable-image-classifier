# Clean Kubernetes Deployment

This directory contains a complete, clean Kubernetes deployment for the scalable image classifier with monitoring and logging.

## Architecture

- **Base Stack**: Image classifier service with HPA and Nginx load balancer
- **Monitoring Stack**: Prometheus and Grafana with preloaded dashboard
- **Logging Stack**: ELK stack (Elasticsearch, Logstash, Kibana) with preloaded dashboard

## Prerequisites

1. **Docker Desktop** with Kubernetes enabled (or any Kubernetes cluster)
2. **kubectl** configured to use your Kubernetes cluster
3. **Internet access** to pull Docker images from Docker Hub

## Docker Images

All custom images are available on Docker Hub - **no local building required!**

### Custom Images
- **Main Application**: `anastasiatsatsou/athtech-scalable-image-classifier:latest`
- **Grafana**: `anastasiatsatsou/image-classifier-grafana:latest` (with preloaded dashboard)
- **Kibana**: `anastasiatsatsou/image-classifier-kibana:latest` (with preloaded dashboard)

### Public Images
- **Nginx**: `nginx:1.25-alpine`
- **Prometheus**: `prom/prometheus:latest`
- **Node Exporter**: `prom/node-exporter:latest`
- **Elasticsearch**: `docker.elastic.co/elasticsearch/elasticsearch:8.11.0`
- **Logstash**: `docker.elastic.co/logstash/logstash:8.11.0`
- **Filebeat**: `docker.elastic.co/beats/filebeat:8.11.0`

## Deployment

### Quick Start (Recommended)
```bash
# Deploy everything with one command - no building required!
kubectl apply -k k8s/
```

**That's it!** All images will be pulled from Docker Hub automatically.

### Benefits of Docker Hub Deployment
- ✅ **No local building** required
- ✅ **Consistent images** across all environments
- ✅ **Faster deployment** - just pull and run
- ✅ **Version control** - images are tagged and versioned
- ✅ **Easy sharing** - anyone can deploy your stack
- ✅ **Preloaded dashboards** - Grafana and Kibana come ready to use

### Deploy Individual Stacks
```bash
# Base application only
kubectl apply -k k8s/base/

# With monitoring
kubectl apply -k k8s/base/
kubectl apply -k k8s/monitoring/

# With logging
kubectl apply -k k8s/base/
kubectl apply -k k8s/logging/

# Full stack (all components)
kubectl apply -k k8s/
```

## Access Services

### Port Forwarding
```bash
# Main API (through Nginx load balancer)
kubectl port-forward svc/nginx-load-balancer-service 8080:80 -n image-classifier

# Grafana Dashboard
kubectl port-forward svc/grafana 3000:3000 -n image-classifier

# Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n image-classifier

# Kibana Dashboard
kubectl port-forward svc/kibana 5601:5601 -n image-classifier

# Elasticsearch
kubectl port-forward svc/elasticsearch 9200:9200 -n image-classifier
```

### Access URLs
- **Main API**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200

## Key Features

### Service Discovery
- Prometheus uses **pod-based discovery** with annotations
- Job name: `image-classifier-docker` (matches existing Grafana dashboard)
- No changes needed to dashboard queries

### Preloaded Dashboards
- **Grafana**: Scalability monitoring dashboard with metrics from Prometheus
- **Kibana**: Complete logging dashboard with log analysis

### RBAC Permissions
- Prometheus: Full cluster access for service discovery
- Filebeat: Pod and namespace access for log collection

### Storage
- Prometheus: 10Gi PVC for metrics storage
- Grafana: 5Gi PVC for dashboard data
- Elasticsearch: 10Gi PVC for log storage

## Troubleshooting

### Check Pod Status
```bash
kubectl get pods -n image-classifier
```

### View Logs
```bash
# Application logs
kubectl logs -l app=image-classifier -n image-classifier

# Prometheus logs
kubectl logs -l app=prometheus -n image-classifier

# Grafana logs
kubectl logs -l app=grafana -n image-classifier

# Elasticsearch logs
kubectl logs -l app=elasticsearch -n image-classifier
```

### Check Service Discovery
```bash
# Check Prometheus targets
kubectl port-forward svc/prometheus 9090:9090 -n image-classifier
# Then visit http://localhost:9090/targets
```

### Verify Metrics
```bash
# Check if metrics endpoint is working
kubectl port-forward svc/image-classifier-service 8000:80 -n image-classifier
curl http://localhost:8000/metrics
```

## Cleanup

```bash
# Remove all resources
kubectl delete -k k8s/

# Or remove individual stacks
kubectl delete -k k8s/base/
kubectl delete -k k8s/monitoring/
kubectl delete -k k8s/logging/
```

## Configuration Files

- `base/` - Core application deployment
- `monitoring/` - Prometheus and Grafana
- `logging/` - ELK stack
- `kustomization.yaml` - Main kustomization file

All configurations use the `image-classifier` namespace for simplicity.
