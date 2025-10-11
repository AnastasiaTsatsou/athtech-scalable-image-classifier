# Scalable Image Classifier

A scalable image classification service built with FastAPI, PyTorch, and containerization technologies.

## Features

### Core Features
- **FastAPI-based REST API** for image classification
- **Pretrained ResNet models** (ResNet50, ResNet101, ResNet152)
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

```bash
# Basic deployment (image classifier only)
kubectl apply -f k8s/

# With monitoring (Prometheus + Grafana)
kubectl apply -f k8s/monitoring/

# With logging (ELK Stack)
kubectl apply -f k8s/logging/

# Full stack (deploy all components)
kubectl apply -f k8s/
kubectl apply -f k8s/monitoring/
kubectl apply -f k8s/logging/

# Port forwarding for local access (run in separate terminals)
kubectl port-forward svc/image-classifier-service 80:80
kubectl port-forward svc/grafana-service 3000:3000 -n monitoring
kubectl port-forward svc/prometheus-service 9090:9090 -n monitoring
kubectl port-forward svc/kibana-service 5601:5601 -n logging
kubectl port-forward svc/elasticsearch-service 9200:9200 -n logging
```

**Access points:**
- **Main API**: http://localhost (through ingress or port-forward)
- **API Documentation**: http://localhost/docs
- **Grafana**: http://localhost:3000 (admin/admin) - when monitoring is deployed
- **Prometheus**: http://localhost:9090 - when monitoring is deployed
- **Kibana Dashboard**: http://localhost:5601 - when logging is deployed
- **Elasticsearch**: http://localhost:9200 - when logging is deployed

**Note:** For Kubernetes deployment, you may need to set up port forwarding or ingress rules to access services locally.

### Stopping Services

```bash
# Stop Docker services
docker-compose down
docker-compose -f docker-compose.monitoring.yml down

# Stop Kubernetes services
kubectl delete -f k8s/
kubectl delete -f k8s/monitoring/
kubectl delete -f k8s/logging/
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
- Main API: http://localhost (through ingress)
- API Documentation: http://localhost/docs
- Grafana: http://localhost:3000 (admin/admin) - when monitoring deployed
- Prometheus: http://localhost:9090 - when monitoring deployed
- Kibana Dashboard: http://localhost:5601 - when logging deployed
- Elasticsearch: http://localhost:9200 - when logging deployed

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
```

## License

This project is part of a dissertation research project.