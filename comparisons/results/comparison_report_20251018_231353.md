# Model Serving Comparison Report

**Generated:** 2025-10-18 23:13:53

## Performance Summary

| System | P95 Latency | Throughput | CPU % | Memory | Success Rate |
|--------|-------------|------------|-------|--------|-------------|
| Custom | 47.4ms | 9.7 RPS | 0.0% | 0.0MB | 100.0% |
| TensorFlow Serving | 139.0ms | 9.6 RPS | 0.0% | 0.0MB | 100.0% |

## Detailed Results

### Custom

**Endpoint:** http://localhost:8081

**Single Request Test:**
- Average: 18.3ms
- P95: 30.1ms
- P99: 31.3ms
- Max: 31.3ms

**Sustained Load Test:**
- Average: 8.0ms
- P95: 47.4ms
- Throughput: 9.7 RPS
- Success Rate: 100.0%

**Burst Load Test:**
- Average: 8.2ms
- P95: 47.1ms
- Throughput: 39.1 RPS
- Success Rate: 100.0%

**Resource Usage:**
- CPU: 0.0%
- Memory: 0.0MB

### TensorFlow Serving

**Endpoint:** http://localhost:8082

**Single Request Test:**
- Average: 103.6ms
- P95: 154.3ms
- P99: 167.4ms
- Max: 167.4ms

**Sustained Load Test:**
- Average: 114.4ms
- P95: 139.0ms
- Throughput: 9.6 RPS
- Success Rate: 100.0%

**Burst Load Test:**
- Average: 366.0ms
- P95: 492.1ms
- Throughput: 22.8 RPS
- Success Rate: 100.0%

**Resource Usage:**
- CPU: 0.0%
- Memory: 0.0MB

