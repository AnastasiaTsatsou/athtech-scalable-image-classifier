# Model Serving Comparison Report

**Generated:** 2025-10-19 17:40:24

## Performance Summary

| System | P95 Latency | Throughput | CPU % | Memory | Success Rate |
|--------|-------------|------------|-------|--------|-------------|
| Custom | 47.1ms | 9.6 RPS | 0.0% | 0.0MB | 100.0% |
| TensorFlow Serving | 139.0ms | 9.6 RPS | 0.0% | 0.0MB | 100.0% |

## Detailed Results

### Custom

**Endpoint:** http://localhost:8081

**Single Request Test:**
- Average: 17.4ms
- P95: 28.8ms
- P99: 30.3ms
- Max: 30.3ms

**Sustained Load Test:**
- Average: 7.9ms
- P95: 47.1ms
- Throughput: 9.6 RPS
- Success Rate: 100.0%

**Burst Load Test:**
- Average: 9.2ms
- P95: 46.2ms
- Throughput: 40.6 RPS
- Success Rate: 98.5%

**Resource Usage:**
- CPU: 0.0%
- Memory: 0.0MB

### TensorFlow Serving

**Endpoint:** http://localhost:8082

**Single Request Test:**
- Average: 104.8ms
- P95: 153.9ms
- P99: 162.3ms
- Max: 162.3ms

**Sustained Load Test:**
- Average: 111.8ms
- P95: 139.0ms
- Throughput: 9.6 RPS
- Success Rate: 100.0%

**Burst Load Test:**
- Average: 295.1ms
- P95: 402.8ms
- Throughput: 27.6 RPS
- Success Rate: 100.0%

**Resource Usage:**
- CPU: 0.0%
- Memory: 0.0MB

