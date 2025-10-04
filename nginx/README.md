# Nginx Load Balancer Configuration

This directory contains Nginx configuration for load balancing the Scalable Image Classifier service.

## Files

- `nginx.conf` - Main Nginx configuration with load balancing, rate limiting, and CORS
- `Dockerfile` - Docker configuration for Nginx container
- `README.md` - This documentation

## Features

### Load Balancing
- **Algorithm**: Least connections
- **Health checks**: Automatic failover for unhealthy backends
- **Connection pooling**: Keep-alive connections to backends
- **Failover**: Automatic removal of failed backends

### Rate Limiting
- **API endpoints**: 10 requests/second with burst of 20
- **Classification endpoint**: 5 requests/second with burst of 10
- **IP-based limiting**: Per-client rate limiting

### Security
- **Security headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **CORS support**: Configurable cross-origin resource sharing
- **Request size limits**: 10MB maximum request body size

### Performance
- **Gzip compression**: Automatic compression for text-based responses
- **Caching**: Appropriate cache headers
- **Connection optimization**: TCP optimizations and keep-alive

## Quick Start

### Using Docker Compose
```bash
# Start with load balancer
docker-compose -f docker-compose.nginx.yml up -d

# Check status
docker-compose -f docker-compose.nginx.yml ps

# View logs
docker-compose -f docker-compose.nginx.yml logs -f nginx-lb
```

### Using Kubernetes
```bash
# Apply nginx deployment
kubectl apply -f k8s/nginx-deployment.yaml

# Check status
kubectl get pods -n image-classifier
kubectl get services -n image-classifier

# Port forward for testing
kubectl port-forward service/nginx-load-balancer-service 80:80 -n image-classifier
```

## Configuration

### Upstream Servers
The load balancer is configured to forward requests to the `image-classifier-service` on port 80.

### Rate Limiting Zones
- `api`: 10 requests/second for general API endpoints
- `classify`: 5 requests/second for image classification endpoint

### Timeouts
- **Connection**: 30s (60s for classification)
- **Send**: 300s (600s for classification)
- **Read**: 300s (600s for classification)

## Testing

### Manual Testing
```bash
# Health check
curl http://localhost/nginx-health

# API health
curl http://localhost/api/v1/health

# Load balancer test script
chmod +x scripts/test-load-balancer.sh
./scripts/test-load-balancer.sh
```

### Load Testing
```bash
# Install Apache Bench
# Ubuntu/Debian: sudo apt-get install apache2-utils
# macOS: brew install httpd

# Test API endpoints
ab -n 100 -c 10 http://localhost/api/v1/health

# Test classification endpoint (with image file)
ab -n 50 -c 5 -p test-image.jpg -T 'multipart/form-data' http://localhost/api/v1/classify
```

## Monitoring

### Logs
```bash
# Docker Compose
docker-compose -f docker-compose.nginx.yml logs -f nginx-lb

# Kubernetes
kubectl logs -f deployment/nginx-load-balancer -n image-classifier
```

### Metrics
The configuration includes detailed logging with:
- Request timing information
- Upstream response times
- Client information
- Response status codes

### Health Checks
- **Nginx health**: `/nginx-health`
- **Backend health**: Automatic via upstream health checks

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**
   - Check if backend services are running
   - Verify service discovery configuration
   - Check upstream server configuration

2. **Rate limiting too aggressive**
   - Adjust rate limiting zones in nginx.conf
   - Increase burst values for higher throughput

3. **CORS issues**
   - Verify CORS headers in nginx.conf
   - Check preflight request handling

4. **Large file uploads failing**
   - Increase `client_max_body_size` in nginx.conf
   - Check proxy buffer settings

### Debug Mode
```bash
# Enable debug logging
# Add to nginx.conf:
error_log /var/log/nginx/error.log debug;

# Restart nginx
docker-compose -f docker-compose.nginx.yml restart nginx-lb
```

## Performance Tuning

### Worker Processes
```nginx
worker_processes auto;  # Automatically set based on CPU cores
```

### Worker Connections
```nginx
events {
    worker_connections 1024;  # Adjust based on expected load
}
```

### Buffer Sizes
```nginx
proxy_buffer_size 4k;
proxy_buffers 8 4k;
proxy_busy_buffers_size 8k;
```

### Gzip Compression
```nginx
gzip_comp_level 6;  # 1-9, higher = better compression, more CPU
```

## Security Considerations

1. **Rate Limiting**: Prevents abuse and DoS attacks
2. **Security Headers**: Protects against common web vulnerabilities
3. **Request Size Limits**: Prevents large file upload attacks
4. **CORS Configuration**: Controls cross-origin access
5. **Non-root User**: Nginx runs as non-root user for security

## Integration with Monitoring

The configuration is designed to work with:
- **Prometheus**: For metrics collection
- **Grafana**: For visualization
- **ELK Stack**: For log aggregation and analysis
