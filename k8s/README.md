# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Scalable Image Classifier.

## Files

- `namespace.yaml` - Creates the image-classifier namespace
- `configmap.yaml` - Application configuration
- `deployment.yaml` - Main application deployment with 3 replicas
- `service.yaml` - ClusterIP service for internal communication
- `hpa.yaml` - Horizontal Pod Autoscaler for automatic scaling
- `ingress.yaml` - Ingress configuration for external access
- `network-policy.yaml` - Network security policies
- `kustomization.yaml` - Kustomize configuration for easy deployment

## Prerequisites

1. Kubernetes cluster (v1.19+)
2. kubectl configured to access the cluster
3. Docker image built and available
4. Ingress controller (nginx-ingress recommended)

## Quick Deployment

### Using the deployment script:
```bash
# Make scripts executable
chmod +x scripts/deploy.sh scripts/undeploy.sh

# Deploy to Kubernetes
./scripts/deploy.sh

# Undeploy from Kubernetes
./scripts/undeploy.sh
```

### Manual deployment:
```bash
# Apply all manifests
kubectl apply -k k8s/

# Check deployment status
kubectl get pods -n image-classifier
kubectl get services -n image-classifier
kubectl get ingress -n image-classifier
```

## Accessing the Service

### Port Forward (for testing):
```bash
kubectl port-forward service/image-classifier-service 8000:80 -n image-classifier
```

Then visit:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

### Using Ingress:
If you have an ingress controller configured, the service will be available at:
- http://image-classifier.local (add to /etc/hosts)

## Scaling

### Manual scaling:
```bash
# Scale to 5 replicas
kubectl scale deployment image-classifier --replicas=5 -n image-classifier
```

### Automatic scaling:
The HPA (Horizontal Pod Autoscaler) is configured to:
- Scale between 3-10 replicas
- Scale based on CPU (70%) and memory (80%) utilization
- Use intelligent scaling policies

## Monitoring

### Check logs:
```bash
# All pods
kubectl logs -f deployment/image-classifier -n image-classifier

# Specific pod
kubectl logs -f <pod-name> -n image-classifier
```

### Check resource usage:
```bash
kubectl top pods -n image-classifier
kubectl top nodes
```

### Check HPA status:
```bash
kubectl get hpa -n image-classifier
kubectl describe hpa image-classifier-hpa -n image-classifier
```

## Configuration

Edit `configmap.yaml` to modify:
- Model configuration (MODEL_NAME, DEVICE)
- API settings (API_HOST, API_PORT)
- Logging level (LOG_LEVEL)

After changes, restart the deployment:
```bash
kubectl rollout restart deployment/image-classifier -n image-classifier
```

## Security

The deployment includes:
- Non-root user execution
- Read-only root filesystem (where possible)
- Dropped capabilities
- Network policies for traffic isolation
- Resource limits and requests

## Troubleshooting

### Common issues:

1. **Pods not starting:**
   ```bash
   kubectl describe pod <pod-name> -n image-classifier
   kubectl logs <pod-name> -n image-classifier
   ```

2. **Service not accessible:**
   ```bash
   kubectl get endpoints -n image-classifier
   kubectl describe service image-classifier-service -n image-classifier
   ```

3. **HPA not scaling:**
   ```bash
   kubectl describe hpa image-classifier-hpa -n image-classifier
   kubectl get events -n image-classifier
   ```

4. **Image pull errors:**
   - Ensure Docker image is built and tagged correctly
   - Check if image is accessible from the cluster
   - Verify imagePullPolicy in deployment.yaml
