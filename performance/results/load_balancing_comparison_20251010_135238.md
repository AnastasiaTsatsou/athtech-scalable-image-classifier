# Load Balancing Algorithm Comparison Report

Generated: 2025-10-10T13:52:38.266948

## Performance Summary

| Algorithm | Health Success Rate | Classification Success Rate | Avg Classification Time | P95 Classification Time |
|-----------|---------------------|----------------------------|------------------------|--------------------------|
| Round Robin | 100.00% | 100.00% | 10.424s | 19.127s |
| Ip Hash | 100.00% | 100.00% | 10.465s | 21.209s |

## Detailed Results

### Round Robin

#### Health Endpoint
- **Success Rate**: 100.00%
- **Average Response Time**: 0.011s
- **95th Percentile**: 0.027s

#### Classification Endpoint
- **Success Rate**: 100.00%
- **Iterations**: 50
- **Average Response Time**: 10.424s
- **Min Response Time**: 3.335s
- **Max Response Time**: 26.255s
- **95th Percentile**: 19.127s
- **99th Percentile**: 26.255s

### Ip Hash

#### Health Endpoint
- **Success Rate**: 100.00%
- **Average Response Time**: 0.012s
- **95th Percentile**: 0.026s

#### Classification Endpoint
- **Success Rate**: 100.00%
- **Iterations**: 50
- **Average Response Time**: 10.465s
- **Min Response Time**: 2.630s
- **Max Response Time**: 21.539s
- **95th Percentile**: 21.209s
- **99th Percentile**: 21.539s

## Analysis

This comparison provides insights into the performance characteristics of different load balancing algorithms for ML workloads.

### Key Findings

1. **Algorithm Selection**: Different algorithms show varying performance characteristics under different load patterns.

2. **Health Check Performance**: All algorithms should maintain high success rates for health checks.

3. **Classification Performance**: The choice of algorithm can impact classification response times and success rates.

