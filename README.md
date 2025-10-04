# Scalable Image Classifier

A scalable image classification service built with FastAPI, PyTorch, and containerization technologies.

## Features

- **FastAPI-based REST API** for image classification
- **Pretrained ResNet models** (ResNet50, ResNet101, ResNet152)
- **Docker containerization** with multi-stage builds
- **Comprehensive testing** with pytest
- **API documentation** with automatic OpenAPI/Swagger docs
- **Health checks** and monitoring endpoints

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints.py        # API endpoints
│   │   └── schemas.py          # Pydantic models
│   └── models/
│       ├── __init__.py
│       └── image_classifier.py # ML model implementation
├── tests/
│   ├── __init__.py
│   ├── test_model.py          # Model unit tests
│   └── test_api.py            # API unit tests
├── requirements.txt           # Python dependencies
├── pytest.ini                # Test configuration
└── README.md                 # This file
```

## Quick Start

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

```bash
# Build and run with Docker Compose (includes load balancer)
docker-compose up -d

# Access through load balancer
curl http://localhost/api/v1/health
```

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
# Health check
curl http://localhost:8000/api/v1/health

# Classify an image
curl -X POST "http://localhost:8000/api/v1/classify" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@path/to/your/image.jpg" \
     -F "top_k=5"
```

### Using Python

```python
import requests

# Classify an image
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/classify',
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

## Deployment Options

This project includes comprehensive deployment options:

1. **Docker containerization** with multi-stage builds ✅
2. **Kubernetes deployment** manifests ✅
3. **Load balancing** with Nginx ✅
4. **Monitoring** with Prometheus and Grafana ✅
5. **Logging** with ELK stack ✅
6. **Performance testing** and optimization ✅

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## License

This project is part of a dissertation research project.