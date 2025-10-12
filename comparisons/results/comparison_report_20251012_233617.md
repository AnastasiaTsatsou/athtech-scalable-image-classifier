# Model Serving Comparison Report

**Generated:** 2025-10-12 23:36:17

## Performance Summary

| System | P95 Latency | Throughput | CPU % | Memory | Success Rate |
|--------|-------------|------------|-------|--------|-------------|
| Custom | 45.9ms | 9.6 RPS | 0.5% | 724.2MB | 100.0% |
| KServe | 0.0ms | 0.0 RPS | 0.0% | 0.0MB | 0.0% |
| TensorFlow Serving | 124.9ms | 10.1 RPS | 0.1% | 103.0MB | 100.0% |

## Detailed Results

### Custom

**Endpoint:** http://localhost:8081

**Single Request Test:**
- Average: 16.2ms
- P95: 25.9ms
- P99: 28.6ms
- Max: 28.6ms

**Sustained Load Test:**
- Average: 7.1ms
- P95: 45.9ms
- Throughput: 9.6 RPS
- Success Rate: 100.0%

**Burst Load Test:**
- Average: 27.8ms
- P95: 221.5ms
- Throughput: 40.2 RPS
- Success Rate: 100.0%

**Resource Usage:**
- CPU: 0.5%
- Memory: 724.2MB

### KServe

**Endpoint:** http://localhost:8081

**Resource Usage:**
- CPU: 0.0%
- Memory: 0.0MB

### TensorFlow Serving

**Endpoint:** http://localhost:8082

**Single Request Test:**
- Average: 93.6ms
- P95: 132.3ms
- P99: 151.6ms
- Max: 151.6ms

**Sustained Load Test:**
- Average: 98.5ms
- P95: 124.9ms
- Throughput: 10.1 RPS
- Success Rate: 100.0%

**Burst Load Test:**
- Average: 290.3ms
- P95: 394.8ms
- Throughput: 26.6 RPS
- Success Rate: 100.0%

**Resource Usage:**
- CPU: 0.1%
- Memory: 103.0MB

