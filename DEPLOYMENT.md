# Deployment Guide

This guide covers different deployment options for the Scalable Image Classifier.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Virtual environment (recommended)

## Deployment Options

### 1. Local Development

```bash
# Set up virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Access**: http://localhost:8000

### 2. Docker Single Container

```bash
# Build image
docker build -t scalable-image-classifier .

# Run container
docker run -p 8000:8000 scalable-image-classifier
```

**Access**: http://localhost:8000

### 3. Docker Compose with Load Balancer

```bash
# Start all services (3 replicas + Nginx load balancer)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access**: http://localhost (through load balancer)

### 4. Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -k k8s/

# Check deployment
kubectl get pods -n image-classifier

# Port forward for testing
kubectl port-forward service/image-classifier-service 8000:80 -n image-classifier
```

**Access**: http://localhost:8000 (after port forward)

### 5. Performance Testing Container

```bash
# Build performance testing image
docker build -f Dockerfile.performance -t image-classifier-performance .

# Run comprehensive performance tests
docker run --rm image-classifier-performance

# Run specific performance tests
docker run --rm image-classifier-performance python performance/benchmark.py --test=load

# Run with Docker Compose (includes load testing with Locust)
docker-compose -f docker-compose.performance.yml up
```

**Features**:
- Comprehensive benchmark suite (health, model info, classification, latency, memory, stress tests)
- Locust load testing with web UI (http://localhost:8089)
- Performance monitoring and visualization
- Results saved to `performance/results/` directory

## Configuration

### Environment Variables

- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FORMAT`: Log format (json or text, default: json)
- `CONTAINER`: Set to "true" to disable file logging in containers

### Docker Compose Configuration

The `docker-compose.yml` includes:
- 3 replicas of the image classifier
- Nginx load balancer with rate limiting
- Health checks for all services
- Resource limits and reservations

### Kubernetes Configuration

The `k8s/` directory includes:
- Namespace and ConfigMap
- Deployment with 3 replicas
- Service and Ingress
- Horizontal Pod Autoscaler (HPA)
- Network policies for security

## Monitoring

### Health Checks

- **Application**: `/api/v1/health`
- **Nginx**: `/nginx-health`

### Logs

```bash
# Docker Compose
docker-compose logs -f image-classifier
docker-compose logs -f nginx-lb

# Kubernetes
kubectl logs -f deployment/image-classifier -n image-classifier
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port
   netstat -ano | findstr :8000
   # Kill process
   taskkill /PID <PID> /F
   ```

2. **Docker build fails**
   ```bash
   # Clean Docker cache
   docker system prune -a
   # Rebuild
   docker-compose up --build -d
   ```

3. **Kubernetes deployment fails**
   ```bash
   # Check pod status
   kubectl describe pod <pod-name> -n image-classifier
   # Check logs
   kubectl logs <pod-name> -n image-classifier
   ```

### Performance Tuning

- **Memory**: Adjust resource limits in Docker Compose or Kubernetes
- **Replicas**: Scale up/down based on load
- **Rate Limiting**: Modify Nginx configuration for different limits

## Security Considerations

- All containers run as non-root users
- Security headers are configured in Nginx
- Network policies restrict traffic in Kubernetes
- Rate limiting prevents abuse
- CORS is properly configured

## Additional Features

- **Monitoring**: Prometheus and Grafana integration available
- **Logging**: ELK stack (Elasticsearch, Logstash, Kibana) for centralized logging
- **Performance Testing**: Comprehensive benchmarking and load testing tools
- **Security**: Network policies, rate limiting, and security headers configured
