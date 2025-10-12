"""
Docker Compose performance testing suite.

This module contains tests specifically for Docker Compose deployment
with nginx load balancer.
"""

import requests
from PIL import Image
import io
import time
import statistics
import pytest
from typing import List, Dict


class DockerComposePerformanceTester:
    """Performance testing utility for Docker Compose deployment."""
    
    def __init__(self, base_url: str = "http://localhost"):
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
    
    def test_load_balancer_health(self) -> Dict[str, float]:
        """Test nginx load balancer health endpoint."""
        start_time = time.time()
        response = requests.get(f'{self.base_url}/nginx-health', timeout=10)
        end_time = time.time()
        
        return {
            'response_time_ms': (end_time - start_time) * 1000,
            'status_code': response.status_code
        }
    
    def test_api_through_load_balancer(self, num_requests: int = 10) -> Dict[str, List[float]]:
        """Test API performance through nginx load balancer."""
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
    
    def test_batch_through_load_balancer(self, batch_size: int = 2) -> Dict[str, float]:
        """Test batch endpoint through nginx load balancer."""
        img_bytes = self._get_image_bytes()
        
        files = []
        for i in range(batch_size):
            img_bytes.seek(0)
            files.append(('files', (f'test{i}.jpg', img_bytes, 'image/jpeg')))
        
        start_time = time.time()
        response = requests.post(
            f'{self.base_url}/api/v1/classify-batch',
            files=files,
            data={'top_k': 5},
            timeout=60
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            return {
                'batch_response_time_ms': (end_time - start_time) * 1000,
                'batch_processing_time_ms': data.get('processing_time_ms', 0),
                'batch_size': batch_size,
                'avg_per_image_ms': ((end_time - start_time) * 1000) / batch_size
            }
        else:
            return {
                'batch_response_time_ms': (end_time - start_time) * 1000,
                'batch_processing_time_ms': 0,
                'batch_size': batch_size,
                'error': response.text
            }


def test_docker_compose_performance():
    """Test Docker Compose deployment performance."""
    tester = DockerComposePerformanceTester()
    
    # Test load balancer health
    health_result = tester.test_load_balancer_health()
    print(f"Nginx Load Balancer Health: {health_result['response_time_ms']:.1f}ms")
    assert health_result['status_code'] == 200, "Load balancer health check failed"
    
    # Test API performance through load balancer
    results = tester.test_api_through_load_balancer(10)
    
    if results['response_times'] and results['processing_times']:
        p95_processing = sorted(results['processing_times'])[int(0.95 * len(results['processing_times']))]
        p95_response = sorted(results['response_times'])[int(0.95 * len(results['response_times']))]
        
        print(f"\nDocker Compose Performance Results:")
        print(f"P95 Processing Time: {p95_processing:.1f}ms")
        print(f"P95 Response Time: {p95_response:.1f}ms")
        print(f"Average Processing Time: {statistics.mean(results['processing_times']):.1f}ms")
        print(f"Average Response Time: {statistics.mean(results['response_times']):.1f}ms")
        
        # Docker Compose may have higher latency due to network overhead
        # But processing time should still be reasonable
        assert p95_processing < 1000, f"Docker Compose processing time {p95_processing:.1f}ms too slow"
    
    # Test batch performance
    batch_results = tester.test_batch_through_load_balancer(2)
    print(f"\nBatch Performance:")
    print(f"Batch Response Time: {batch_results['batch_response_time_ms']:.1f}ms")
    print(f"Average per Image: {batch_results['avg_per_image_ms']:.1f}ms")


if __name__ == "__main__":
    print("Running Docker Compose Performance Tests...")
    print("=" * 50)
    
    try:
        test_docker_compose_performance()
        print("\nDocker Compose performance tests passed!")
    except Exception as e:
        print(f"\nDocker Compose performance test failed: {e}")
        raise
