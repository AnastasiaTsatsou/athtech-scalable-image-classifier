"""
Load testing scenarios for the image classifier service
"""

import time
import random
import base64
import io
from typing import Dict, Any, List
from PIL import Image
import requests
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result data structure"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    success: bool
    error_message: str = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ImageGenerator:
    """Generate test images for load testing"""
    
    @staticmethod
    def create_test_image(width: int = 224, height: int = 224, 
                         color: str = "RGB", format: str = "JPEG") -> bytes:
        """Create a test image with random content"""
        # Create a random image
        image = Image.new(color, (width, height))
        pixels = image.load()
        
        # Fill with random colors
        for i in range(width):
            for j in range(height):
                pixels[i, j] = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                )
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        image.save(img_buffer, format=format)
        return img_buffer.getvalue()
    
    @staticmethod
    def create_test_images(count: int, sizes: List[tuple] = None) -> List[bytes]:
        """Create multiple test images"""
        if sizes is None:
            sizes = [(224, 224), (256, 256), (512, 512)]
        
        images = []
        for _ in range(count):
            size = random.choice(sizes)
            images.append(ImageGenerator.create_test_image(*size))
        
        return images


class LoadTester:
    """Load testing framework for the image classifier service"""
    
    def __init__(self, base_url: str = "http://localhost", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.results: List[TestResult] = []
        self.lock = threading.Lock()
    
    def test_health_endpoint(self) -> TestResult:
        """Test health endpoint"""
        start_time = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/health",
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            return TestResult(
                endpoint="/api/v1/health",
                method="GET",
                status_code=response.status_code,
                response_time=response_time,
                success=response.status_code == 200
            )
        except Exception as e:
            return TestResult(
                endpoint="/api/v1/health",
                method="GET",
                status_code=0,
                response_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    def test_model_info_endpoint(self) -> TestResult:
        """Test model info endpoint"""
        start_time = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/model/info",
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            return TestResult(
                endpoint="/api/v1/model/info",
                method="GET",
                status_code=response.status_code,
                response_time=response_time,
                success=response.status_code == 200
            )
        except Exception as e:
            return TestResult(
                endpoint="/api/v1/model/info",
                method="GET",
                status_code=0,
                response_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    def test_classify_endpoint(self, image_bytes: bytes, top_k: int = 5) -> TestResult:
        """Test image classification endpoint"""
        start_time = time.time()
        try:
            files = {'image': ('test_image.jpg', image_bytes, 'image/jpeg')}
            data = {'top_k': top_k}
            
            response = requests.post(
                f"{self.base_url}/api/v1/classify",
                files=files,
                data=data,
                timeout=self.timeout
            )
            response_time = time.time() - start_time
            
            return TestResult(
                endpoint="/api/v1/classify",
                method="POST",
                status_code=response.status_code,
                response_time=response_time,
                success=response.status_code == 200
            )
        except Exception as e:
            return TestResult(
                endpoint="/api/v1/classify",
                method="POST",
                status_code=0,
                response_time=time.time() - start_time,
                success=False,
                error_message=str(e)
            )
    
    def run_single_test(self, test_type: str, **kwargs) -> TestResult:
        """Run a single test"""
        if test_type == "health":
            return self.test_health_endpoint()
        elif test_type == "model_info":
            return self.test_model_info_endpoint()
        elif test_type == "classify":
            image_bytes = kwargs.get('image_bytes')
            top_k = kwargs.get('top_k', 5)
            return self.test_classify_endpoint(image_bytes, top_k)
        else:
            raise ValueError(f"Unknown test type: {test_type}")
    
    def run_concurrent_tests(self, test_configs: List[Dict[str, Any]], 
                           max_workers: int = 10) -> List[TestResult]:
        """Run multiple tests concurrently"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tests
            future_to_config = {}
            for config in test_configs:
                future = executor.submit(self.run_single_test, **config)
                future_to_config[future] = config
            
            # Collect results
            for future in as_completed(future_to_config):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    config = future_to_config[future]
                    results.append(TestResult(
                        endpoint=config.get('test_type', 'unknown'),
                        method="UNKNOWN",
                        status_code=0,
                        response_time=0,
                        success=False,
                        error_message=str(e)
                    ))
        
        return results
    
    def run_load_test(self, test_type: str, duration_seconds: int = 60, 
                     requests_per_second: int = 10, **kwargs) -> List[TestResult]:
        """Run a load test for specified duration"""
        results = []
        start_time = time.time()
        request_interval = 1.0 / requests_per_second
        
        logger.info(f"Starting load test: {test_type} for {duration_seconds}s at {requests_per_second} RPS")
        
        while time.time() - start_time < duration_seconds:
            test_start = time.time()
            
            # Run the test
            result = self.run_single_test(test_type, **kwargs)
            results.append(result)
            
            # Calculate sleep time to maintain RPS
            elapsed = time.time() - test_start
            sleep_time = max(0, request_interval - elapsed)
            time.sleep(sleep_time)
        
        logger.info(f"Load test completed. Total requests: {len(results)}")
        return results
    
    def run_stress_test(self, test_type: str, max_workers: int = 50, 
                       duration_seconds: int = 300, **kwargs) -> List[TestResult]:
        """Run a stress test with increasing load"""
        results = []
        start_time = time.time()
        
        logger.info(f"Starting stress test: {test_type} with {max_workers} workers for {duration_seconds}s")
        
        # Gradually increase load
        for workers in range(1, max_workers + 1, 5):
            if time.time() - start_time >= duration_seconds:
                break
            
            # Run concurrent tests for 10 seconds
            test_configs = []
            for _ in range(workers * 10):  # 10 requests per worker
                config = {'test_type': test_type, **kwargs}
                test_configs.append(config)
            
            batch_results = self.run_concurrent_tests(test_configs, max_workers=workers)
            results.extend(batch_results)
            
            logger.info(f"Completed batch with {workers} workers. Results: {len(batch_results)}")
            time.sleep(1)  # Brief pause between batches
        
        logger.info(f"Stress test completed. Total requests: {len(results)}")
        return results
    
    def analyze_results(self, results: List[TestResult]) -> Dict[str, Any]:
        """Analyze test results and return statistics"""
        if not results:
            return {}
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        response_times = [r.response_time for r in successful_results]
        
        analysis = {
            'total_requests': len(results),
            'successful_requests': len(successful_results),
            'failed_requests': len(failed_results),
            'success_rate': len(successful_results) / len(results) if results else 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'median_response_time': statistics.median(response_times) if response_times else 0,
            'p95_response_time': self._percentile(response_times, 95) if response_times else 0,
            'p99_response_time': self._percentile(response_times, 99) if response_times else 0,
            'requests_per_second': len(results) / (results[-1].timestamp - results[0].timestamp).total_seconds() if len(results) > 1 else 0,
            'error_breakdown': self._get_error_breakdown(failed_results)
        }
        
        return analysis
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _get_error_breakdown(self, failed_results: List[TestResult]) -> Dict[str, int]:
        """Get breakdown of errors by type"""
        error_counts = {}
        for result in failed_results:
            error_type = result.error_message or f"HTTP_{result.status_code}"
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        return error_counts
    
    def save_results(self, results: List[TestResult], filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance/results/load_test_{timestamp}.json"
        
        # Convert results to serializable format
        serializable_results = []
        for result in results:
            serializable_results.append({
                'endpoint': result.endpoint,
                'method': result.method,
                'status_code': result.status_code,
                'response_time': result.response_time,
                'success': result.success,
                'error_message': result.error_message,
                'timestamp': result.timestamp.isoformat()
            })
        
        # Save to file
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"Results saved to {filename}")
    
    def generate_report(self, results: List[TestResult]) -> str:
        """Generate a human-readable test report"""
        analysis = self.analyze_results(results)
        
        report = f"""
Performance Test Report
======================

Test Summary:
- Total Requests: {analysis['total_requests']}
- Successful Requests: {analysis['successful_requests']}
- Failed Requests: {analysis['failed_requests']}
- Success Rate: {analysis['success_rate']:.2%}

Response Time Statistics:
- Average: {analysis['avg_response_time']:.3f}s
- Median: {analysis['median_response_time']:.3f}s
- 95th Percentile: {analysis['p95_response_time']:.3f}s
- 99th Percentile: {analysis['p99_response_time']:.3f}s
- Min: {analysis['min_response_time']:.3f}s
- Max: {analysis['max_response_time']:.3f}s

Performance Metrics:
- Requests per Second: {analysis['requests_per_second']:.2f}

Error Breakdown:
"""
        
        for error_type, count in analysis['error_breakdown'].items():
            report += f"- {error_type}: {count}\n"
        
        return report
