# Performance Testing

This directory contains comprehensive performance testing tools and utilities for the Scalable Image Classifier service.

## Overview

The performance testing suite includes:
- **Load Testing**: HTTP load testing with configurable RPS and duration
- **Stress Testing**: Testing system limits with increasing load
- **Latency Testing**: Measuring response times under various conditions
- **Memory Testing**: Monitoring memory usage during operations
- **Locust Integration**: Web-based load testing with real-time monitoring

## Quick Start

### Using Scripts

```bash
# Run comprehensive benchmark
./scripts/run-performance-tests.sh

# Run specific test
./scripts/run-performance-tests.sh --test classification --duration 120 --rps 20

# Run Locust web interface
./scripts/run-locust-tests.sh --web-ui

# Run Locust headless
./scripts/run-locust-tests.sh --users 50 --run-time 300s
```

### Using Python Directly

```bash
# Run comprehensive benchmark
python performance/benchmark.py --test comprehensive

# Run specific tests
python performance/benchmark.py --test health --duration 60 --rps 20
python performance/benchmark.py --test classification --duration 120 --rps 10
python performance/benchmark.py --test stress --workers 50 --duration 300
python performance/benchmark.py --test latency --iterations 1000
python performance/benchmark.py --test memory --iterations 100
```

### Using Docker Compose

```bash
# Start performance testing environment
docker-compose -f docker-compose.performance.yml up -d

# View Locust web interface
open http://localhost:8089

# View results
ls performance/results/
```

## Test Types

### 1. Health Endpoint Test
Tests the `/api/v1/health` endpoint for basic functionality and response times.

```bash
python performance/benchmark.py --test health --duration 60 --rps 20
```

**Metrics:**
- Response time distribution
- Success rate
- Throughput (requests per second)

### 2. Model Info Test
Tests the `/api/v1/model/info` endpoint for model information retrieval.

```bash
python performance/benchmark.py --test model_info --duration 60 --rps 20
```

**Metrics:**
- Response time distribution
- Success rate
- Throughput

### 3. Classification Test
Tests the `/api/v1/classify` endpoint with various image sizes and parameters.

```bash
python performance/benchmark.py --test classification --duration 120 --rps 10
```

**Metrics:**
- Classification response time
- Confidence score distribution
- Image size impact on performance
- Success rate by image size

### 4. Stress Test
Tests system limits with increasing concurrent load.

```bash
python performance/benchmark.py --test stress --workers 50 --duration 300
```

**Metrics:**
- Performance degradation under load
- Maximum concurrent users
- System resource usage
- Error rates under stress

### 5. Latency Test
Measures response times for single requests.

```bash
python performance/benchmark.py --test latency --iterations 1000
```

**Metrics:**
- P50, P95, P99 response times
- Response time distribution
- Outlier detection

### 6. Memory Test
Monitors memory usage during classification operations.

```bash
python performance/benchmark.py --test memory --iterations 100
```

**Metrics:**
- Memory usage patterns
- Memory leaks detection
- Peak memory consumption

## Locust Load Testing

### Web Interface
Start the Locust web interface for interactive load testing:

```bash
./scripts/run-locust-tests.sh --web-ui
```

Then open http://localhost:8089 in your browser.

### Headless Mode
Run Locust tests without the web interface:

```bash
./scripts/run-locust-tests.sh --users 50 --run-time 300s --spawn-rate 5
```

### Test Scenarios

#### 1. ImageClassifierUser
- **Health checks**: 30% of requests
- **Model info**: 20% of requests
- **Image classification**: 50% of requests
- **Wait time**: 1-3 seconds between requests

#### 2. HighLoadUser
- **Image classification**: 80% of requests
- **Health checks**: 20% of requests
- **Wait time**: 0.1-0.5 seconds between requests

#### 3. ErrorTestingUser
- **Invalid images**: Tests error handling
- **Missing parameters**: Tests validation
- **Large images**: Tests resource limits

## Performance Metrics

### Response Time Metrics
- **Average**: Mean response time
- **Median**: 50th percentile response time
- **P95**: 95th percentile response time
- **P99**: 99th percentile response time
- **Max**: Maximum response time

### Throughput Metrics
- **RPS**: Requests per second
- **Concurrent Users**: Number of simultaneous users
- **Total Requests**: Total number of requests processed

### Error Metrics
- **Success Rate**: Percentage of successful requests
- **Error Rate**: Percentage of failed requests
- **Error Types**: Breakdown of error types

### System Metrics
- **CPU Usage**: CPU utilization percentage
- **Memory Usage**: Memory consumption
- **Network I/O**: Network traffic
- **Disk I/O**: Disk read/write operations

## Optimization Strategies

### 1. Connection Pooling
Use connection pooling to reduce connection overhead:

```python
from performance.optimization import ConnectionPool

pool = ConnectionPool(max_connections=100)
session = pool.get_session()
# Use session for requests
pool.return_session(session)
```

### 2. Caching
Implement caching for frequently accessed data:

```python
from performance.optimization import CachingLayer

cache = CachingLayer(max_size=1000, ttl=300)
result = cache.get(key)
if result is None:
    result = expensive_operation()
    cache.set(key, result)
```

### 3. Performance Monitoring
Monitor system performance during tests:

```python
from performance.optimization import PerformanceMonitor

monitor = PerformanceMonitor(interval=1.0)
monitor.start_monitoring()
# Run tests
monitor.stop_monitoring()
summary = monitor.get_metrics_summary()
```

### 4. System Optimization
Optimize system settings for better performance:

```python
from performance.optimization import PerformanceOptimizer

PerformanceOptimizer.optimize_python_gc()
PerformanceOptimizer.optimize_system_limits()
PerformanceOptimizer.optimize_environment()
```

## Results Analysis

### JSON Results
Test results are saved in JSON format with detailed metrics:

```json
{
  "total_requests": 1000,
  "successful_requests": 995,
  "failed_requests": 5,
  "success_rate": 0.995,
  "avg_response_time": 0.234,
  "p95_response_time": 0.456,
  "p99_response_time": 0.789,
  "requests_per_second": 16.67
}
```

### CSV Results (Locust)
Locust generates CSV files with detailed statistics:

- `locust_stats.csv`: Request statistics
- `locust_failures.csv`: Failure details
- `locust_exceptions.csv`: Exception details

### HTML Reports
Locust generates HTML reports with charts and graphs:

- `locust_stats.html`: Interactive statistics dashboard

## Best Practices

### 1. Test Planning
- Start with low load and gradually increase
- Test different scenarios (normal, peak, stress)
- Monitor system resources during tests
- Document baseline performance

### 2. Test Execution
- Run tests in isolated environments
- Use realistic test data
- Monitor system resources
- Record detailed logs

### 3. Results Analysis
- Compare results across different test runs
- Identify performance bottlenecks
- Set performance baselines
- Track performance trends

### 4. Optimization
- Focus on the biggest performance impacts
- Test optimizations thoroughly
- Monitor for regressions
- Document optimization results

## Troubleshooting

### Common Issues

1. **High Response Times**
   - Check system resources (CPU, memory)
   - Optimize database queries
   - Implement caching
   - Scale horizontally

2. **High Error Rates**
   - Check system limits
   - Review error logs
   - Test error handling
   - Implement retry logic

3. **Memory Issues**
   - Monitor memory usage
   - Check for memory leaks
   - Optimize data structures
   - Implement garbage collection

4. **Connection Issues**
   - Check connection limits
   - Implement connection pooling
   - Monitor network usage
   - Optimize connection settings

### Performance Tuning

1. **Application Level**
   - Optimize algorithms
   - Implement caching
   - Use async operations
   - Optimize data structures

2. **System Level**
   - Tune kernel parameters
   - Optimize memory settings
   - Configure network settings
   - Use SSD storage

3. **Infrastructure Level**
   - Use load balancers
   - Implement auto-scaling
   - Optimize container settings
   - Use CDN for static content

## Integration with Monitoring

The performance testing suite integrates with the monitoring stack:

- **Prometheus**: Collects performance metrics
- **Grafana**: Visualizes performance data
- **ELK Stack**: Logs performance test results

## Continuous Performance Testing

Set up automated performance testing in CI/CD:

1. **Baseline Tests**: Run on every commit
2. **Regression Tests**: Run on pull requests
3. **Load Tests**: Run on releases
4. **Stress Tests**: Run weekly

## Performance Targets

### Response Time Targets
- **Health endpoint**: < 100ms (P95)
- **Model info**: < 200ms (P95)
- **Classification**: < 500ms (P95)

### Throughput Targets
- **Health endpoint**: > 1000 RPS
- **Model info**: > 500 RPS
- **Classification**: > 100 RPS

### Availability Targets
- **Success rate**: > 99.9%
- **Uptime**: > 99.95%
- **Error rate**: < 0.1%
