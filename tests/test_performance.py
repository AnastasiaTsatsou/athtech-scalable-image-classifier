"""
Performance testing suite for the image classification service.

This module contains comprehensive performance tests to validate
the optimization targets and measure improvements.
"""

import requests
from PIL import Image
import io
import time
import statistics
from typing import List, Dict


class PerformanceTester:
    """Performance testing utility for image classification service."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_image = self._create_test_image()

    def _create_test_image(self) -> Image.Image:
        """Create a standard test image for performance testing."""
        return Image.new("RGB", (224, 224), color="red")

    def _get_image_bytes(self) -> io.BytesIO:
        """Get image as bytes for API requests."""
        img_bytes = io.BytesIO()
        self.test_image.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        return img_bytes

    def test_single_request(self) -> Dict[str, float]:
        """Test a single classification request."""
        img_bytes = self._get_image_bytes()

        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/api/v1/classify",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"top_k": 5},
            timeout=30,
        )
        end_time = time.time()

        if response.status_code == 200:
            data = response.json()
            return {
                "response_time_ms": (end_time - start_time) * 1000,
                "processing_time_ms": data.get("processing_time_ms", 0),
                "status_code": response.status_code,
            }
        else:
            return {
                "response_time_ms": (end_time - start_time) * 1000,
                "processing_time_ms": 0,
                "status_code": response.status_code,
                "error": response.text,
            }

    def test_multiple_requests(
        self, num_requests: int = 10
    ) -> Dict[str, List[float]]:
        """Test multiple requests and return performance statistics."""
        response_times = []
        processing_times = []

        for i in range(num_requests):
            result = self.test_single_request()
            response_times.append(result["response_time_ms"])
            processing_times.append(result["processing_time_ms"])

            # Small delay between requests
            time.sleep(0.1)

        return {
            "response_times": response_times,
            "processing_times": processing_times,
            "num_requests": num_requests,
        }

    def test_cache_performance(
        self, num_requests: int = 10
    ) -> Dict[str, float]:
        """Test cache performance with repeated identical requests."""
        # Use identical image for all requests to ensure cache hits
        img_bytes = self._get_image_bytes()

        # First request (cache miss)
        start_time = time.time()
        requests.post(
            f"{self.base_url}/api/v1/classify",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            data={"top_k": 5},
            timeout=30,
        )
        cache_miss_time = (time.time() - start_time) * 1000

        # Subsequent requests (cache hits)
        cache_hit_times = []
        for i in range(num_requests - 1):
            img_bytes.seek(0)  # Reset file pointer
            start_time = time.time()
            requests.post(
                f"{self.base_url}/api/v1/classify",
                files={"file": ("test.jpg", img_bytes, "image/jpeg")},
                data={"top_k": 5},
                timeout=30,
            )
            cache_hit_time = (time.time() - start_time) * 1000
            cache_hit_times.append(cache_hit_time)

            # Small delay between requests
            time.sleep(0.1)

        return {
            "cache_miss_time_ms": cache_miss_time,
            "avg_cache_hit_time_ms": statistics.mean(cache_hit_times)
            if cache_hit_times
            else 0,
            "cache_hit_count": len(cache_hit_times),
            "cache_miss_count": 1,
            "cache_hit_times": cache_hit_times,  # Include individual times for debugging
        }

    def test_batch_requests(self, batch_size: int = 2) -> Dict[str, float]:
        """Test batch classification endpoint."""
        img_bytes = self._get_image_bytes()

        # Create multiple files for batch request
        files = []
        for i in range(batch_size):
            img_bytes.seek(0)
            files.append(("files", (f"test{i}.jpg", img_bytes, "image/jpeg")))

        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/api/v1/classify-batch",
            files=files,
            data={"top_k": 5},
            timeout=60,
        )
        end_time = time.time()

        if response.status_code == 200:
            data = response.json()
            return {
                "batch_response_time_ms": (end_time - start_time) * 1000,
                "batch_processing_time_ms": data.get("processing_time_ms", 0),
                "batch_size": batch_size,
                "avg_per_image_ms": ((end_time - start_time) * 1000)
                / batch_size,
            }
        else:
            return {
                "batch_response_time_ms": (end_time - start_time) * 1000,
                "batch_processing_time_ms": 0,
                "batch_size": batch_size,
                "error": response.text,
            }


def test_performance_targets():
    """Test that performance meets the <200ms P95 target."""
    tester = PerformanceTester()

    # Get model info for verification
    try:
        response = requests.get(
            f"{tester.base_url}/api/v1/model/info", timeout=10
        )
        model_info = response.json() if response.status_code == 200 else {}
        print("\nModel Info:")
        print(f"Model: {model_info.get('model_name', 'Unknown')}")
        print(f"Quantized: {model_info.get('quantized', 'Unknown')}")
        print(f"TorchScript: {model_info.get('torchscript', 'Unknown')}")
        print(f"Parameters: {model_info.get('parameters', 'Unknown')}")
        print(f"Size: {model_info.get('model_size_mb', 'Unknown')} MB")
    except Exception as e:
        print(f"Failed to get model info: {e}")
        model_info = {}

    # Test multiple requests to get P95
    results = tester.test_multiple_requests(10)

    # Calculate P95
    p95_processing = sorted(results["processing_times"])[
        int(0.95 * len(results["processing_times"]))
    ]
    p95_response = sorted(results["response_times"])[
        int(0.95 * len(results["response_times"]))
    ]

    print("\nPerformance Test Results:")
    print(f"P95 Processing Time: {p95_processing:.1f}ms")
    print(f"P95 Response Time: {p95_response:.1f}ms")
    print(
        f"Average Processing Time: {statistics.mean(results['processing_times']):.1f}ms"
    )
    print(
        f"Average Response Time: {statistics.mean(results['response_times']):.1f}ms"
    )

    # Assert target is met
    assert (
        p95_processing < 200
    ), f"P95 processing time {p95_processing:.1f}ms exceeds 200ms target"

    # Cache performance test
    cache_results = tester.test_cache_performance(10)
    print("\nCache Performance:")
    print(f"Cache Miss Time: {cache_results['cache_miss_time_ms']:.1f}ms")
    print(
        f"Average Cache Hit Time: {cache_results['avg_cache_hit_time_ms']:.1f}ms"
    )

    # Assert cache hits are very fast
    assert (
        cache_results["avg_cache_hit_time_ms"] < 10
    ), f"Cache hit time {cache_results['avg_cache_hit_time_ms']:.1f}ms too slow"


def test_batch_performance():
    """Test batch classification performance."""
    tester = PerformanceTester()

    # Test batch requests
    batch_results = tester.test_batch_requests(2)

    print("Batch Performance Results:")
    print(
        f"Batch Response Time: {batch_results['batch_response_time_ms']:.1f}ms"
    )
    print(
        f"Batch Processing Time: {batch_results['batch_processing_time_ms']:.1f}ms"
    )
    print(f"Average per Image: {batch_results['avg_per_image_ms']:.1f}ms")

    # Assert batch processing is efficient
    assert (
        batch_results["avg_per_image_ms"] < 500
    ), f"Batch processing {batch_results['avg_per_image_ms']:.1f}ms per image too slow"


def test_health_endpoint():
    """Test health endpoint response time."""
    tester = PerformanceTester()

    start_time = time.time()
    response = requests.get(f"{tester.base_url}/api/v1/health", timeout=10)
    end_time = time.time()

    response_time = (end_time - start_time) * 1000

    print(f"Health Endpoint Response Time: {response_time:.1f}ms")

    assert (
        response.status_code == 200
    ), f"Health check failed with status {response.status_code}"
    assert (
        response_time < 100
    ), f"Health endpoint too slow: {response_time:.1f}ms"


if __name__ == "__main__":
    # Run performance tests
    print("Running Performance Tests...")
    print("=" * 50)

    try:
        test_health_endpoint()
        test_performance_targets()
        test_batch_performance()
        print("\nAll performance tests passed!")
    except Exception as e:
        print(f"\nPerformance test failed: {e}")
        raise
