"""
Kubernetes performance testing suite.

This module contains tests specifically for Kubernetes deployment
with port forwarding.
"""

import requests
from PIL import Image
import io
import time
import statistics
import pytest
from typing import List, Dict


class KubernetesPerformanceTester:
    """Performance testing utility for Kubernetes deployment."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.test_image = self._create_test_image()
    
    def _create_test_image(self) -> Image.Image:
        """Create a standard test image for performance testing."""
        return Image.new('RGB', (224, 224), color='red')
    
    def _get_image_bytes(self) -> io.BytesIO:
        """Get image as bytes for API requests."""
        img_bytes = io.BytesIO()
        self.test_image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes
    
    def test_kubernetes_health(self) -> Dict[str, float]:
        """Test Kubernetes service health endpoint."""
        start_time = time.time()
        response = requests.get(f'{self.base_url}/api/v1/health', timeout=10)
        end_time = time.time()
        
        return {
            'response_time_ms': (end_time - start_time) * 1000,
            'status_code': response.status_code,
            'model_loaded': response.json().get('model_loaded', False) if response.status_code == 200 else False
        }
    
    def test_kubernetes_performance(self, num_requests: int = 10) -> Dict[str, List[float]]:
        """Test API performance in Kubernetes environment."""
        response_times = []
        processing_times = []
        
        for i in range(num_requests):
            img_bytes = self._get_image_bytes()
            
            start_time = time.time()
            response = requests.post(
                f'{self.base_url}/api/v1/classify',
                files={'file': ('test.jpg', img_bytes, 'image/jpeg')},
                data={'top_k': 5},
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                response_times.append((end_time - start_time) * 1000)
                processing_times.append(data.get('processing_time_ms', 0))
            
            time.sleep(0.1)
        
        return {
            'response_times': response_times,
            'processing_times': processing_times,
            'num_requests': num_requests
        }
    
    def test_kubernetes_cache_performance(self, num_requests: int = 10) -> Dict[str, float]:
        """Test cache performance in Kubernetes."""
        results = self.test_kubernetes_performance(num_requests)
        
        if results['processing_times']:
            # First request should be cache miss, rest should be cache hits
            cache_miss_time = results['processing_times'][0]
            cache_hit_times = results['processing_times'][1:]
            
            return {
                'cache_miss_time_ms': cache_miss_time,
                'avg_cache_hit_time_ms': statistics.mean(cache_hit_times) if cache_hit_times else 0,
                'cache_hit_count': len(cache_hit_times),
                'cache_miss_count': 1,
                'total_requests': len(results['processing_times'])
            }
        else:
            return {
                'cache_miss_time_ms': 0,
                'avg_cache_hit_time_ms': 0,
                'cache_hit_count': 0,
                'cache_miss_count': 0,
                'total_requests': 0
            }


def test_kubernetes_performance():
    """Test Kubernetes deployment performance."""
    tester = KubernetesPerformanceTester()
    
    # Test health endpoint
    health_result = tester.test_kubernetes_health()
    print(f"Kubernetes Health Check: {health_result['response_time_ms']:.1f}ms")
    print(f"Model Loaded: {health_result['model_loaded']}")
    
    assert health_result['status_code'] == 200, "Kubernetes health check failed"
    assert health_result['model_loaded'], "Model not loaded in Kubernetes"
    
    # Test performance
    results = tester.test_kubernetes_performance(10)
    
    if results['response_times'] and results['processing_times']:
        p95_processing = sorted(results['processing_times'])[int(0.95 * len(results['processing_times']))]
        p95_response = sorted(results['response_times'])[int(0.95 * len(results['response_times']))]
        
        print(f"\nKubernetes Performance Results:")
        print(f"P95 Processing Time: {p95_processing:.1f}ms")
        print(f"P95 Response Time: {p95_response:.1f}ms")
        print(f"Average Processing Time: {statistics.mean(results['processing_times']):.1f}ms")
        print(f"Average Response Time: {statistics.mean(results['response_times']):.1f}ms")
        
        # Kubernetes should meet the <200ms target
        assert p95_processing < 200, f"Kubernetes processing time {p95_processing:.1f}ms exceeds 200ms target"
    
    # Test cache performance
    cache_results = tester.test_kubernetes_cache_performance(10)
    print(f"\nKubernetes Cache Performance:")
    print(f"Cache Miss Time: {cache_results['cache_miss_time_ms']:.1f}ms")
    print(f"Average Cache Hit Time: {cache_results['avg_cache_hit_time_ms']:.1f}ms")
    print(f"Cache Hit Rate: {cache_results['cache_hit_count']}/{cache_results['total_requests']}")
    
    # Cache hits should be very fast
    assert cache_results['avg_cache_hit_time_ms'] < 10, f"Kubernetes cache hit time {cache_results['avg_cache_hit_time_ms']:.1f}ms too slow"


if __name__ == "__main__":
    print("Running Kubernetes Performance Tests...")
    print("=" * 50)
    
    try:
        test_kubernetes_performance()
        print("\nKubernetes performance tests passed!")
    except Exception as e:
        print(f"\nKubernetes performance test failed: {e}")
        raise
