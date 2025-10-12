# Model Serving Comparison - README

## Overview

This directory contains a complete comparison framework for evaluating different model serving approaches:

1. **Custom FastAPI System** - Your existing PyTorch-based FastAPI application running on Kubernetes
2. **KServe** - Using TorchServe format for PyTorch model serving (ready for future setup)
3. **TensorFlow Serving** - Using TensorFlow's native serving infrastructure with proxy

## Current Status

✅ **Working Systems:**
- Custom FastAPI (Kubernetes deployment on port 8081)
- TensorFlow Serving (MobileNetV3-Large on port 8082)

⏳ **Future Setup:**
- KServe (files ready, operator installation needed)

## Quick Start

### Prerequisites

1. **Kubernetes cluster** with kubectl access
2. **Metrics-server** installed (for resource monitoring):
   ```bash
   kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
   kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'
   ```
3. **Python dependencies**:
   ```bash
   pip install torch torchvision tensorflow pillow requests aiohttp numpy
   ```

### Run Current Comparison

```bash
# Run benchmark for working systems (Custom + TensorFlow Serving)
python benchmark_comparison.py
```

**Note**: Both systems are currently deployed and running:
- Custom FastAPI: `http://localhost:8081`
- TensorFlow Serving: `http://localhost:8082`

### Manual Setup (if needed)

1. **Deploy Custom System** (if not already running):
   ```bash
   kubectl apply -f ../k8s/
   kubectl port-forward -n image-classifier service/image-classifier-service 8081:80
   ```

2. **Deploy TensorFlow Serving** (if not already running):
   ```bash
   cd tensorflow-serving
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/pvc.yaml
   kubectl apply -f k8s/deployment-mobilenet.yaml
   kubectl apply -f k8s/service-mobilenet.yaml
   kubectl port-forward -n tfserving-simple svc/tensorflow-serving-mobilenet-service 8082:8080
   ```

3. **Run Benchmarks**:
   ```bash
   python benchmark_comparison.py
   ```

## Directory Structure

```
comparisons/
├── kserve/                          # KServe deployment (ready for future setup)
│   ├── model_converter.py           # PyTorch → TorchServe converter
│   ├── test_deployment.py           # KServe validation script
│   ├── namespace.yaml               # KServe namespace
│   ├── inferenceservice.yaml        # KServe InferenceService
│   ├── pvc.yaml                     # Persistent volume claim
│   └── model-store/                 # Generated TorchServe models
├── tensorflow-serving/              # TensorFlow Serving deployment (working)
│   ├── deployment-proxy.yaml        # TF Serving with Nginx proxy
│   ├── service-proxy.yaml           # Service for proxy
│   ├── namespace.yaml               # Namespace
│   └── test_deployment.py           # Validation script
├── test_images/                     # Test images for validation
│   ├── create_test_images.py        # Image generator script
│   └── test_images/                 # Synthetic and real test images
├── benchmark_comparison.py          # Unified benchmark script
├── run_full_comparison.py           # End-to-end orchestration (legacy)
├── deployment_analysis.md           # Complexity analysis
└── results/                         # Generated results
    ├── comparison_results_*.json   # Detailed benchmark results
    └── comparison_report_*.md       # Markdown comparison report
```

## Test Scenarios

The benchmark script tests all systems with identical workloads:

1. **Warmup**: 10 requests to each system
2. **Single Request Latency**: 100 sequential requests
3. **Sustained Load**: 500 requests at 10 RPS
4. **Burst Load**: 200 requests at 50 RPS
5. **Resource Monitoring**: Real CPU/memory metrics via kubectl top pods

## Metrics Collected

- **Response Times**: avg, p50, p95, p99, max (milliseconds)
- **Throughput**: requests per second
- **Success Rate**: percentage of successful requests
- **Resource Usage**: Real CPU% and Memory MB from metrics-server
- **Model Detection**: Automatic fallback for TensorFlow Serving models

## Current Results

Based on the latest benchmark run:

| System | P95 Latency | Throughput | CPU % | Memory | Success Rate |
|--------|-------------|------------|-------|--------|-------------|
| **Custom FastAPI** | 45.0ms | 9.6 RPS | 0.5% | 723.0MB | 100.0% |
| **TensorFlow Serving** | 47.0ms | 9.7 RPS | 1.3% | 103.0MB | 100.0% |

### Key Findings

- **Custom FastAPI**: More CPU efficient (0.5% vs 1.3%), higher memory usage (723MB vs 103MB)
- **TensorFlow Serving**: More memory efficient, slightly higher CPU usage
- **Both Systems**: 100% success rates on Kubernetes (no nginx rate limiting issues)
- **Fair Comparison**: All systems running on Kubernetes with identical resource limits

## Port Configuration

The systems use these ports:
- **Custom System**: `localhost:8081` (Kubernetes deployment)
- **TensorFlow Serving**: `localhost:8082` (MobileNetV3-Large service)
- **KServe**: `localhost:8083` (KServe InferenceService - when deployed)

## Model Support

- **Custom FastAPI**: MobileNetV3-Large (PyTorch)
- **TensorFlow Serving**: MobileNetV3-Large (TensorFlow/Keras)
- **KServe**: MobileNetV3-Large (PyTorch via TorchServe)

## Troubleshooting

### Common Issues

1. **Metrics-server not working**:
   ```bash
   kubectl get pods -n kube-system | grep metrics-server
   kubectl logs -n kube-system deployment/metrics-server
   ```

2. **Port-forward conflicts**:
   ```bash
   pkill -f 'kubectl port-forward'
   ```

3. **TensorFlow Serving model issues**:
   - Current deployment uses MobileNetV3-Large model
   - Check model status: `curl http://localhost:8082/v1/models/mobilenet_v3_large`

4. **Custom system not accessible**:
   ```bash
   kubectl get pods -n image-classifier
   kubectl logs -n image-classifier deployment/image-classifier
   ```

### Debug Commands

```bash
# Check system status
kubectl get pods -n image-classifier
kubectl get pods -n tfserving-simple

# Check services
kubectl get svc -n image-classifier
kubectl get svc -n tfserving-simple

# Check resource usage
kubectl top pods -n image-classifier
kubectl top pods -n tfserving-simple

# View logs
kubectl logs -n image-classifier deployment/image-classifier
kubectl logs -n tfserving-simple deployment/tensorflow-serving-mobilenet -c tensorflow-serving
```

## Future KServe Setup

To set up KServe for complete comparison:

1. **Install KServe operator**:
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.2/cert-manager.yaml
   kubectl apply -k "https://github.com/kserve/kserve/config/default?ref=v0.12.0"
   ```

2. **Deploy KServe**:
   ```bash
   cd kserve
   python model_converter.py
   kubectl apply -f namespace.yaml
   kubectl apply -f pvc.yaml
   kubectl apply -f inferenceservice.yaml
   kubectl port-forward -n kserve-comparison service/mobilenet-v3-large-predictor-default 8083:80
   ```

3. **Run full comparison**:
   ```bash
   python benchmark_comparison.py
   ```

## Cleanup

To clean up deployments:

```bash
# Clean up TensorFlow Serving
kubectl delete namespace tfserving-simple

# Clean up KServe (when set up)
kubectl delete namespace kserve-comparison

# Stop port-forwards
pkill -f 'kubectl port-forward'
```

## Next Steps

1. **Review Current Results**: Check `results/` directory for latest comparison
2. **Set up KServe**: Follow the future setup section above
3. **Deploy MobileNetV3-Large**: Use TensorFlow Serving model export for fair comparison
4. **Analyze Performance**: Compare all three systems with identical models

## Contributing

To extend the comparison:

1. **Add New Systems**: Create new directories with deployment scripts
2. **Modify Benchmarks**: Update `benchmark_comparison.py` for new test scenarios
3. **Improve Analysis**: Enhance `deployment_analysis.md` with new metrics
4. **Add Tests**: Include more realistic test images and scenarios

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the deployment analysis document
3. Check Kubernetes cluster logs
4. Verify all prerequisites are installed