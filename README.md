# Scalable Image Classifier

A scalable image classification service built with FastAPI, PyTorch, and containerization technologies.

## Features

### Core Features
- **FastAPI-based REST API** for image classification
- **Pretrained MobileNetV3-Large model** optimized for performance
- **Docker containerization** with multi-stage builds
- **Comprehensive testing** with pytest
- **API documentation** with automatic OpenAPI/Swagger docs
- **Health checks** and monitoring endpoints

### Additional Features
- **Load balancing** with Nginx for high availability
- **Monitoring** with Prometheus metrics and Grafana dashboards
- **Logging** with ELK stack (Elasticsearch, Logstash, Kibana) for centralized log management
- **Performance testing** with Locust for load testing
- **Kubernetes deployment** manifests for cloud deployment
- **Docker Hub images** - ready-to-deploy with preloaded dashboards
- **Code quality tools** (black, flake8, mypy) for maintainable code

## Project Structure

```
├── app/                       # Main application code
│   ├── __init__.py
│   ├── main.py               # FastAPI application
│   ├── api/                  # API layer
│   │   ├── __init__.py
│   │   ├── endpoints.py      # API endpoints
│   │   └── schemas.py        # Pydantic models
│   ├── models/               # ML models
│   │   ├── __init__.py
│   │   ├── image_classifier.py
│   │   └── mock_classifier.py
│   ├── logging/              # Logging configuration
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── middleware.py
│   └── monitoring/           # Monitoring and metrics
│       ├── __init__.py
│       ├── metrics.py
│       └── middleware.py
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_model.py
│   └── test_api.py
├── k8s/                      # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── hpa.yaml
│   ├── ingress.yaml
│   ├── network-policy.yaml
│   └── namespace.yaml
├── monitoring/               # Monitoring stack
│   ├── prometheus.yml
│   ├── alert_rules.yml
│   └── grafana/
├── logging/                  # Logging stack
│   ├── kibana/              # Kibana configuration
│   ├── logstash/            # Logstash configuration
│   └── filebeat/            # Filebeat configuration
├── nginx/                    # Load balancer config
│   └── nginx.conf
├── performance/              # Performance testing
│   ├── benchmark.py
│   └── load_tests.py
├── requirements.txt          # Python dependencies
├── pytest.ini              # Test configuration
├── docker-compose.yml       # Complete deployment (ELK + App + Monitoring)
├── docker-compose.monitoring.yml  # Monitoring stack only
├── docker-compose.performance.yml  # Performance testing
├── Dockerfile               # Main application image
├── Dockerfile.performance   # Performance testing image
└── README.md               # This file
```

## Prerequisites

### Required Software
- **Docker Desktop** (for Kubernetes deployment)
- **kubectl** (Kubernetes command-line tool)
- **Python 3.8+** (for local development)

### For Kubernetes Deployment
- **Docker images must be built locally** before deployment
- **Docker Desktop required** - Kubernetes will use locally built images
- **Custom images included**: Kibana (with dashboard preloading), Nginx Load Balancer
- For other Kubernetes environments (Minikube, cloud), images need to be pushed to a container registry

## Quick Start

### Option 1: Docker Deployment (Recommended)

```bash
# Complete deployment (ELK + App + Monitoring)
docker-compose up -d --build

# Monitoring only (if you want to run separately)
docker-compose -f docker-compose.monitoring.yml up -d

# Performance testing
docker-compose -f docker-compose.performance.yml up -d
```

**Access points:**
- **Main API**: http://localhost (through nginx load balancer)
- **API Documentation**: http://localhost/docs
- **Kibana Dashboard**: http://localhost:5601
- **Elasticsearch**: http://localhost:9200
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### Option 2: Kubernetes Deployment

**Ready to Deploy:** All Docker images are available on Docker Hub - no local building required!

```bash
# Deploy all components (single namespace: image-classifier)
kubectl apply -k k8s/

# Port forwarding for services (run in separate terminals)
kubectl port-forward svc/nginx-load-balancer-service 8080:80 -n image-classifier
kubectl port-forward svc/grafana 3000:3000 -n image-classifier
kubectl port-forward svc/prometheus 9090:9090 -n image-classifier
kubectl port-forward svc/elasticsearch 9200:9200 -n image-classifier
kubectl port-forward svc/kibana 5601:5601 -n image-classifier
```

**Docker Images Used:**
- **Main Application**: `anastasiatsatsou/athtech-scalable-image-classifier:latest`
- **Grafana**: `anastasiatsatsou/image-classifier-grafana:latest` (with preloaded dashboard)
- **Kibana**: `anastasiatsatsou/image-classifier-kibana:latest` (with preloaded dashboard)
- **Other Services**: Public images (nginx, prometheus, elasticsearch, etc.)

**Access points:**
- **Main API**: http://localhost:8080 (through port-forward)
- **API Documentation**: http://localhost:8080/docs
- **Grafana**: http://localhost:3000 (admin/admin) - with preloaded dashboard
- **Prometheus**: http://localhost:9090 - with Node Exporter for system metrics
- **Kibana Dashboard**: http://localhost:5601 - with preloaded dashboard
- **Elasticsearch**: http://localhost:9200

**Note:** Access method depends on your Kubernetes environment:
- **Docker Desktop**: LoadBalancer works automatically (http://localhost)
- **Minikube**: Use `minikube service` or port-forwarding
- **Cloud Providers**: LoadBalancer gets real external IP
- **Bare Metal/On-Premises**: Use port-forwarding or install MetalLB

### Stopping Services

```bash
# Stop Docker services
docker-compose down
docker-compose -f docker-compose.monitoring.yml down

# Stop Kubernetes services
kubectl delete -k k8s/
```

## Deployment Options

This project includes comprehensive deployment options:

### Basic Deployment
- **Docker containerization** with multi-stage builds ✅
- **Load balancing** with Nginx ✅
- **Health checks** and monitoring endpoints ✅

### Advanced Deployment
- **Kubernetes deployment** manifests ✅
- **Monitoring** with Prometheus and Grafana ✅
- **Logging** with ELK stack (Elasticsearch, Logstash, Kibana) ✅
- **Performance testing** and optimization ✅
- **Node Exporter** for system metrics (CPU, Memory) ✅
- **Preloaded dashboards** for Grafana and Kibana ✅
- **Single namespace deployment** for simplified management ✅
- **HPA (Horizontal Pod Autoscaler)** for automatic scaling ✅

### Access Points by Deployment Type

**Basic Deployment:**
- Main API: http://localhost
- API Documentation: http://localhost/docs

**With Monitoring:**
- Main API: http://localhost
- API Documentation: http://localhost/docs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

**With Logging:**
- Main API: http://localhost
- API Documentation: http://localhost/docs
- Kibana Dashboard: http://localhost:5601
- Elasticsearch: http://localhost:9200

**Kubernetes Deployment:**
- Main API: http://localhost:8080 (through port-forward)
- API Documentation: http://localhost:8080/docs
- Grafana: http://localhost:3000 (admin/admin) - with preloaded dashboard
- Prometheus: http://localhost:9090 - with Node Exporter for system metrics
- Kibana Dashboard: http://localhost:5601 - with preloaded dashboard
- Elasticsearch: http://localhost:9200

**Full Stack:**
- All of the above services running simultaneously

## Local Development

### 1. Set up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** For performance testing, you may also want to install external tools:
- **wrk**: HTTP benchmarking tool (install separately)
- **vegeta**: HTTP load testing tool (install separately)
- **Locust**: Already included in requirements.txt

### 2. Run Tests

```bash
pytest
```

### 3. Start the API Server

```bash
# Local development
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or using the main module
python -m app.main
```

The API will be available at:
- **API Base**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 4. Docker Deployment

For Docker deployment options, see the [Deployment Options](#deployment-options) section above.

## Performance Targets

The service is optimized to meet the following performance targets:

- **P95 Processing Time**: < 200ms (95th percentile of processing times)
- **Cache Hit Time**: < 10ms (for cached responses)
- **Health Endpoint**: < 100ms response time
- **Batch Processing**: < 500ms per image average

These targets are validated through comprehensive performance testing and represent a 99.1% improvement from the original implementation.

### Performance Optimization

**Memory Management:**
- **Memory Limits**: 4Gi per pod (increased from 1Gi to handle ML workloads)
- **Memory Requests**: 1Gi per pod (increased from 512Mi for better resource allocation)
- **HPA Memory Threshold**: 75% utilization (optimized for ML workloads)
- **Max Replicas**: 20 pods (increased from 10 for better scaling)

**Scaling Behavior:**
- **Aggressive Scale-Up**: 100% increase or 4 pods every 30 seconds
- **Conservative Scale-Down**: 10% decrease every 60 seconds
- **Stabilization Windows**: 30s scale-up, 300s scale-down

**Performance Results:**
- **Light Load**: 100% success rate, <20ms response time
- **Medium Load**: 100% success rate, <50ms response time  
- **High Load**: 38% success rate (improved from previous 11% with memory optimization)
- **Memory Stress**: 22% success rate (improved from previous 11% with increased limits)

## API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Classify Image
```bash
POST /api/v1/classify
Content-Type: multipart/form-data

Parameters:
- file: Image file (JPEG, PNG, etc.)
- top_k: Number of top predictions (1-10, default: 5)
```

### Model Information
```bash
GET /api/v1/model/info
```

## Example Usage

### Using curl

```bash
# Health check (local development)
curl http://localhost:8000/api/v1/health

# Health check (Docker deployment)
curl http://localhost/api/v1/health

# Classify an image (local development)
curl -X POST "http://localhost:8000/api/v1/classify" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@path/to/your/image.jpg" \
     -F "top_k=5"

# Classify an image (Docker deployment)
curl -X POST "http://localhost/api/v1/classify" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@path/to/your/image.jpg" \
     -F "top_k=5"

# Classify an image (Kubernetes deployment)
curl -X POST "http://localhost:8080/api/v1/classify" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@path/to/your/image.jpg" \
     -F "top_k=5"
```

### Using Python

```python
import requests

# Classify an image (local development)
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/classify',
        files={'file': f},
        data={'top_k': 5}
    )

# Classify an image (Docker deployment)
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost/api/v1/classify',
        files={'file': f},
        data={'top_k': 5}
    )

# Classify an image (Kubernetes deployment)
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/api/v1/classify',
        files={'file': f},
        data={'top_k': 5}
    )

result = response.json()
print(f"Top prediction: {result['predictions'][0]['class_name']}")
print(f"Confidence: {result['predictions'][0]['probability']:.2%}")
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_model.py
```

### Code Quality

```bash
# Format code (with 79 character line limit to match flake8)
black app/ tests/ --line-length 79

# Lint code
flake8 app/ tests/

# Type checking (ignore missing imports for external libraries)
mypy app/ --ignore-missing-imports
```

**Note:** The `--line-length 79` option for black ensures compatibility with flake8's default line length limit. The `--ignore-missing-imports` option for mypy prevents errors from external libraries that don't have type stubs.

### Troubleshooting

**Common Issues:**

1. **Port conflicts**: Ensure ports 80, 3000, 5601, 9090, 9200 are available
2. **Memory issues**: Ensure Docker has sufficient memory allocated (recommended: 4GB+)
3. **Container restart loops**: Check logs with `docker logs <container-name>`
4. **Network issues**: Ensure all services are on the same Docker network
5. **Namespace timing issues**: Use Kustomize (kubectl apply -k) instead of individual files to ensure proper resource ordering

**Useful Commands:**

```bash
# Check container status
docker ps -a

# View logs
docker logs <container-name>

# Check resource usage
docker stats

# Clean up unused resources
docker system prune -a

# Check built images
docker images | grep image-classifier

# Rebuild specific service
docker-compose build image-classifier
docker build -t image-classifier-grafana:latest -f k8s/monitoring/grafana-dockerfile ./monitoring/grafana
docker build -t image-classifier-kibana:latest -f k8s/logging/kibana-dockerfile ./logging/kibana
```

**Image Building Issues:**

If you encounter issues building custom images:
1. **Grafana build fails**: Check `k8s/monitoring/grafana-dockerfile` and ensure dashboard files exist in `monitoring/grafana/`
2. **Kibana build fails**: Check `k8s/logging/kibana-dockerfile` and ensure dashboard files exist in `logging/kibana/`
3. **Permission issues**: Run `docker build --no-cache` to rebuild from scratch
4. **Missing files**: Ensure all referenced files in Dockerfiles exist in the correct paths
5. **Namespace issues**: All services deploy to the `image-classifier` namespace

## License

This project is part of a dissertation research project.