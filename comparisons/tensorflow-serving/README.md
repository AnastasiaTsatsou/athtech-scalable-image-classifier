# MobileNetV3-Large TensorFlow Serving Deployment

This directory contains everything needed to deploy MobileNetV3-Large to TensorFlow Serving on Kubernetes for fair comparison with the PyTorch-based system.

## 📁 Files Overview

```
tensorflow-serving/
├── export_mobilenet_to_tensorflow.py    # Export MobileNetV3-Large to SavedModel
├── test_tfserving_mobilenet.py          # Validation and testing script
├── k8s/                                 # Kubernetes configuration files
│   ├── pvc.yaml                         # PersistentVolumeClaim for model storage
│   ├── model-config.yaml                # TensorFlow Serving model configuration
│   ├── deployment-mobilenet.yaml        # Kubernetes deployment with init container
│   ├── service-mobilenet.yaml           # Kubernetes service
│   └── namespace.yaml                   # Kubernetes namespace
└── README.md                            # This file
```

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (Docker Desktop, minikube, or cloud)
- `kubectl` configured and connected
- Python 3.7+ with TensorFlow 2.x

### 1. Export Model

```bash
# Export MobileNetV3-Large to SavedModel format
python export_mobilenet_to_tensorflow.py --output-dir models --model-name mobilenet_v3_large --validate
```

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create PVC for model storage
kubectl apply -f k8s/pvc.yaml

# Wait for PVC to be bound
kubectl wait --for=condition=Bound pvc/mobilenet-model-pvc -n tfserving-simple --timeout=120s

# Create ConfigMap
kubectl apply -f k8s/model-config.yaml

# Deploy TensorFlow Serving
kubectl apply -f k8s/deployment-mobilenet.yaml

# Create service
kubectl apply -f k8s/service-mobilenet.yaml
```

### 3. Wait for Ready

```bash
# Wait for deployment
kubectl wait --for=condition=Available deployment/tensorflow-serving-mobilenet -n tfserving-simple --timeout=300s

# Wait for pod ready
kubectl wait --for=condition=Ready pod -l app=tensorflow-serving-mobilenet -n tfserving-simple --timeout=300s
```

### 4. Setup Port Forward

```bash
# Forward local port 8082 to service
kubectl port-forward -n tfserving-simple svc/tensorflow-serving-mobilenet-service 8082:8080
```

**Note**: This will run in the foreground. For background operation, add `&` at the end or run in a separate terminal.

### 5. Test Deployment

```bash
# Test the deployed model
python test_tfserving_mobilenet.py

# Test with verbose output
python test_tfserving_mobilenet.py --verbose

# Test with custom images
python test_tfserving_mobilenet.py --test-images ../test_images/test_images
```

### 6. Run Benchmark

```bash
# Run the comparison benchmark
python ../benchmark_comparison.py
```

## 📋 Detailed Instructions

### Step-by-Step Deployment

#### 1. Export Model

```bash
# Export MobileNetV3-Large to SavedModel format
python export_mobilenet_to_tensorflow.py --output-dir models --model-name mobilenet_v3_large --validate
```

#### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create PVC for model storage
kubectl apply -f k8s/pvc.yaml

# Wait for PVC to be bound
kubectl wait --for=condition=Bound pvc/mobilenet-model-pvc -n tfserving-simple --timeout=120s

# Create ConfigMap
kubectl apply -f k8s/model-config.yaml

# Deploy TensorFlow Serving
kubectl apply -f k8s/deployment-mobilenet.yaml

# Create service
kubectl apply -f k8s/service-mobilenet.yaml
```

#### 3. Wait for Ready

```bash
# Wait for deployment
kubectl wait --for=condition=Available deployment/tensorflow-serving-mobilenet -n tfserving-simple --timeout=300s

# Wait for pod ready
kubectl wait --for=condition=Ready pod -l app=tensorflow-serving-mobilenet -n tfserving-simple --timeout=300s
```

#### 4. Setup Port Forward

```bash
# Forward local port 8082 to service
kubectl port-forward -n tfserving-simple svc/tensorflow-serving-mobilenet-service 8082:8080
```

**Note**: This will run in the foreground. For background operation, add `&` at the end or run in a separate terminal.

#### 5. Test Endpoints

```bash
# Test model metadata
curl http://localhost:8082/v1/models/mobilenet_v3_large

# Test prediction
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"instances": [[[[1.0, 0.0, 0.0] for _ in range(224)] for _ in range(224)]]}' \
  http://localhost:8082/v1/models/mobilenet_v3_large:predict
```

## 🚀 Running Services

### Background Operation

To run TensorFlow Serving in the background while using other terminals:

```bash
# Start port-forward in background
kubectl port-forward -n tfserving-simple svc/tensorflow-serving-mobilenet-service 8082:8080 &

# Check if it's running
ps aux | grep "kubectl port-forward"

# Stop background port-forward when done
pkill -f "kubectl port-forward.*8082"
```

### Service Management

```bash
# Check service status
kubectl get pods -n tfserving-simple
kubectl get services -n tfserving-simple

# Restart deployment if needed
kubectl rollout restart deployment/tensorflow-serving-mobilenet -n tfserving-simple

# View logs
kubectl logs -n tfserving-simple deployment/tensorflow-serving-mobilenet -c tensorflow-serving -f
```

## 🔧 Configuration

### Model Specifications

- **Architecture**: MobileNetV3-Large
- **Weights**: ImageNet pretrained
- **Input**: `[batch_size, 224, 224, 3]` RGB images, float32, range `[0, 1]`
- **Output**: `[batch_size, 1000]` logits for ImageNet classes
- **Preprocessing**: ImageNet normalization (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

### Resource Limits

- **Requests**: 512Mi memory, 500m CPU
- **Limits**: 2Gi memory, 2000m CPU
- **Storage**: 1Gi PVC for model files

### Endpoints

- **Model Metadata**: `http://localhost:8082/v1/models/mobilenet_v3_large`
- **Predictions**: `http://localhost:8082/v1/models/mobilenet_v3_large:predict`
- **Health Check**: `http://localhost:8082/v1/models`

## 🧪 Testing

### Test Script Features

The `test_tfserving_mobilenet.py` script provides comprehensive testing:

- **Health Check**: Verifies TensorFlow Serving is running
- **Model Metadata**: Tests model information endpoint
- **Synthetic Images**: Tests with red, green, blue, white, black, noise, gradient images
- **Custom Images**: Loads and tests with real images from directory
- **Performance**: Measures response times
- **Validation**: Verifies prediction format and content

### Test Examples

```bash
# Basic test
python test_tfserving_mobilenet.py

# Verbose output
python test_tfserving_mobilenet.py --verbose

# Custom URL
python test_tfserving_mobilenet.py --url http://localhost:8082

# Custom model name
python test_tfserving_mobilenet.py --model mobilenet_v3_large

# Test with custom images
python test_tfserving_mobilenet.py --test-images ../test_images/test_images
```

### Expected Output

```
=== TensorFlow Serving MobileNetV3-Large Validation ===
URL: http://localhost:8082
Model: mobilenet_v3_large
Namespace: tfserving-simple

📚 Loaded 1000 ImageNet classes
✅ Port-forward is running (PID: 12345)
🏥 Testing model health...
✅ Health check passed
   Available models: ['mobilenet_v3_large']
📋 Testing model metadata...
✅ Model metadata retrieved successfully
   Model versions: 1
   Version 1: AVAILABLE
🔮 Testing predictions...
✅ Predictions completed: 7/7 successful
📊 Average response time: 0.245s

📈 Top predictions summary:
   red: 0.234s
      → class_123 (123): 0.1234
   green: 0.251s
      → class_456 (456): 0.0987
   ...

✅ All tests passed!

🚀 TensorFlow Serving MobileNetV3-Large is working correctly!
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Port Forward Not Working

```bash
# Check if port-forward is running
ps aux | grep "kubectl port-forward"

# Kill existing port-forwards
pkill -f "kubectl port-forward.*8082"

# Restart port-forward
kubectl port-forward -n tfserving-simple svc/tensorflow-serving-mobilenet-service 8082:8080
```

#### 2. Model Not Loading

```bash
# Check pod logs
kubectl logs -n tfserving-simple deployment/tensorflow-serving-mobilenet -c tensorflow-serving

# Check init container logs (if using init container)
kubectl logs -n tfserving-simple deployment/tensorflow-serving-mobilenet -c model-setup
```

#### 3. PVC Not Binding

```bash
# Check PVC status
kubectl get pvc -n tfserving-simple

# Check storage class
kubectl get storageclass

# Update PVC with correct storage class
kubectl patch pvc mobilenet-model-pvc -n tfserving-simple -p '{"spec":{"storageClassName":"standard"}}'
```

#### 4. Out of Memory

```bash
# Check resource usage
kubectl top pods -n tfserving-simple

# Increase memory limits in deployment-mobilenet.yaml
# Update resources.limits.memory to "4Gi"
```

### Debug Commands

```bash
# Check deployment status
kubectl get deployment -n tfserving-simple

# Check pod status
kubectl get pods -n tfserving-simple

# Check service
kubectl get service -n tfserving-simple

# Check PVC
kubectl get pvc -n tfserving-simple

# Describe pod for detailed info
kubectl describe pod -n tfserving-simple -l app=tensorflow-serving-mobilenet

# Check events
kubectl get events -n tfserving-simple --sort-by='.lastTimestamp'
```

## 🧹 Cleanup

### Remove Deployment

```bash
# Remove all resources at once
kubectl delete -f k8s/ -n tfserving-simple

# Or remove individually
kubectl delete service tensorflow-serving-mobilenet-service -n tfserving-simple
kubectl delete deployment tensorflow-serving-mobilenet -n tfserving-simple
kubectl delete pvc mobilenet-model-pvc -n tfserving-simple
kubectl delete namespace tfserving-simple

# Stop port-forward if running
pkill -f "kubectl port-forward.*8082"
```

### Clean Up Local Files

```bash
# Remove exported model files
rm -rf models/

# Remove temporary files
rm -f temp_job.yaml
```

## 📊 Performance Expectations

### Model Loading
- **Init Container**: 30-60 seconds (model download and export)
- **TensorFlow Serving**: 10-30 seconds (model loading)

### Inference Performance
- **First Request**: 1-3 seconds (cold start)
- **Subsequent Requests**: 50-200ms (warm)
- **Memory Usage**: 300-500MB (model + serving)

### Resource Usage
- **CPU**: 200-500m during inference
- **Memory**: 400-800MB total
- **Storage**: ~50MB (model files)

## 🔗 Integration

### With Benchmark Script

The deployment integrates seamlessly with the existing benchmark:

```bash
# Run benchmark comparison
python ../benchmark_comparison.py

# The script will automatically detect:
# - TensorFlow Serving at localhost:8082
# - MobileNetV3-Large model
# - Correct input format [0,1] normalized images
```

### With Custom Applications

```python
import requests
import numpy as np

# Prepare image (224x224x3, range [0,1])
image = np.random.rand(224, 224, 3).astype(np.float32)

# Send prediction request
payload = {"instances": [image.tolist()]}
response = requests.post(
    "http://localhost:8082/v1/models/mobilenet_v3_large:predict",
    json=payload
)

# Parse response
result = response.json()
predictions = result['predictions'][0]  # 1000 ImageNet logits
```

## 📝 Notes

- The model uses TensorFlow/Keras native MobileNetV3-Large for optimal TF Serving performance
- ImageNet preprocessing is handled automatically (normalization)
- The deployment includes an init container that exports the model during startup
- All resources are configured for the `tfserving-simple` namespace
- Port-forward maps localhost:8082 to the service for easy testing

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review pod logs: `kubectl logs -n tfserving-simple deployment/tensorflow-serving-mobilenet -f`
3. Verify prerequisites are met
4. Ensure Kubernetes cluster has sufficient resources

For additional help, check the main project documentation or create an issue.
