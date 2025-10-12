"""
Performance test utilities and helpers.

This module provides utility functions and classes for performance testing
across different deployment environments.
"""

import requests
from PIL import Image
import io
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class PerformanceResult:
    """Data class for performance test results."""

    environment: str
    base_url: str
    num_requests: int
    successful_requests: int
    response_times: List[float]
    processing_times: List[float]
    errors: List[str]
    timestamp: str


class PerformanceTestHelper:
    """Helper class for performance testing utilities."""

    @staticmethod
    def create_test_image(
        size: tuple = (224, 224), color: str = "red"
    ) -> Image.Image:
        """Create a test image for performance testing."""
        return Image.new("RGB", size, color=color)

    @staticmethod
    def image_to_bytes(image: Image.Image, format: str = "JPEG") -> io.BytesIO:
        """Convert PIL Image to bytes for API requests."""
        img_bytes = io.BytesIO()
        image.save(img_bytes, format=format)
        img_bytes.seek(0)
        return img_bytes

    @staticmethod
    def calculate_percentiles(values: List[float]) -> Dict[str, float]:
        """Calculate percentile statistics for a list of values."""
        if not values:
            return {}

        sorted_values = sorted(values)
        n = len(sorted_values)

        return {
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": sorted_values[n // 2],
            "p90": sorted_values[int(0.90 * n)],
            "p95": sorted_values[int(0.95 * n)],
            "p99": sorted_values[int(0.99 * n)],
        }

    @staticmethod
    def test_endpoint_availability(
        base_url: str, endpoint: str = "/api/v1/health"
    ) -> bool:
        """Test if an endpoint is available."""
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def format_performance_summary(result: PerformanceResult) -> str:
        """Format performance result as a readable string."""
        if not result.response_times or not result.processing_times:
            return f"{result.environment}: No successful requests"

        response_stats = PerformanceTestHelper.calculate_percentiles(
            result.response_times
        )
        processing_stats = PerformanceTestHelper.calculate_percentiles(
            result.processing_times
        )

        summary = f"""
{result.environment} Performance Summary:
  Base URL: {result.base_url}
  Requests: {result.successful_requests}/{result.num_requests} successful
  
  Response Times:
    P95: {response_stats['p95']:.1f}ms
    Avg: {response_stats['avg']:.1f}ms
    Min: {response_stats['min']:.1f}ms
    Max: {response_stats['max']:.1f}ms
  
  Processing Times:
    P95: {processing_stats['p95']:.1f}ms
    Avg: {processing_stats['avg']:.1f}ms
    Min: {processing_stats['min']:.1f}ms
    Max: {processing_stats['max']:.1f}ms
  
  Target Achievement: {'✅ ACHIEVED' if processing_stats['p95'] < 200 else '❌ NOT MET'} (<200ms P95)
"""

        if result.errors:
            summary += f"  Errors: {len(result.errors)}\n"

        return summary


class LoadTestRunner:
    """Class for running load tests with different patterns."""

    def __init__(self, base_url: str, test_image: Image.Image):
        self.base_url = base_url
        self.test_image = test_image

    def run_single_request(self) -> Dict[str, Any]:
        """Run a single classification request."""
        img_bytes = PerformanceTestHelper.image_to_bytes(self.test_image)

        start_time = time.time()
        try:
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
                    "success": True,
                    "response_time_ms": (end_time - start_time) * 1000,
                    "processing_time_ms": data.get("processing_time_ms", 0),
                    "status_code": response.status_code,
                }
            else:
                return {
                    "success": False,
                    "response_time_ms": (end_time - start_time) * 1000,
                    "processing_time_ms": 0,
                    "status_code": response.status_code,
                    "error": response.text,
                }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "response_time_ms": (end_time - start_time) * 1000,
                "processing_time_ms": 0,
                "error": str(e),
            }

    def run_burst_test(
        self, burst_size: int = 5, delay: float = 0.1
    ) -> List[Dict[str, Any]]:
        """Run burst test with multiple rapid requests."""
        results = []

        for i in range(burst_size):
            result = self.run_single_request()
            results.append(result)
            time.sleep(delay)

        return results

    def run_sustained_test(
        self, duration_seconds: int = 30, interval: float = 1.0
    ) -> List[Dict[str, Any]]:
        """Run sustained test for a specified duration."""
        results = []
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            result = self.run_single_request()
            results.append(result)
            time.sleep(interval)

        return results

    def run_cache_test(self, num_requests: int = 10) -> Dict[str, Any]:
        """Run cache performance test."""
        results = []

        for i in range(num_requests):
            result = self.run_single_request()
            results.append(result)
            time.sleep(0.1)

        if results and results[0]["success"]:
            # First request is cache miss, rest are cache hits
            cache_miss_time = results[0]["processing_time_ms"]
            cache_hit_times = [
                r["processing_time_ms"] for r in results[1:] if r["success"]
            ]

            return {
                "cache_miss_time_ms": cache_miss_time,
                "avg_cache_hit_time_ms": statistics.mean(cache_hit_times)
                if cache_hit_times
                else 0,
                "cache_hit_count": len(cache_hit_times),
                "cache_miss_count": 1,
                "total_requests": len(results),
            }
        else:
            return {
                "cache_miss_time_ms": 0,
                "avg_cache_hit_time_ms": 0,
                "cache_hit_count": 0,
                "cache_miss_count": 0,
                "total_requests": len(results),
            }


def run_quick_performance_check(
    base_url: str = "http://localhost:8000",
) -> Dict[str, Any]:
    """Run a quick performance check for a given URL."""
    print(f"Running quick performance check for {base_url}...")

    # Check if service is available
    if not PerformanceTestHelper.test_endpoint_availability(base_url):
        return {"available": False, "error": "Service not available"}

    # Create test image and runner
    test_image = PerformanceTestHelper.create_test_image()
    runner = LoadTestRunner(base_url, test_image)

    # Run cache test
    cache_results = runner.run_cache_test(5)

    # Run burst test
    burst_results = runner.run_burst_test(3, 0.1)

    # Calculate statistics
    successful_results = [r for r in burst_results if r["success"]]
    if successful_results:
        response_times = [r["response_time_ms"] for r in successful_results]
        processing_times = [
            r["processing_time_ms"] for r in successful_results
        ]

        response_stats = PerformanceTestHelper.calculate_percentiles(
            response_times
        )
        processing_stats = PerformanceTestHelper.calculate_percentiles(
            processing_times
        )

        return {
            "available": True,
            "response_stats": response_stats,
            "processing_stats": processing_stats,
            "cache_performance": cache_results,
            "target_achieved": processing_stats["p95"] < 200,
            "successful_requests": len(successful_results),
            "total_requests": len(burst_results),
        }
    else:
        return {
            "available": True,
            "error": "No successful requests",
            "total_requests": len(burst_results),
        }


if __name__ == "__main__":
    # Run quick check for local development
    result = run_quick_performance_check()

    if result["available"]:
        print("✅ Service is available")
        if "processing_stats" in result:
            print(
                f"📊 P95 Processing Time: {result['processing_stats']['p95']:.1f}ms"
            )
            print(
                f"🎯 Target Achievement: {'✅ ACHIEVED' if result['target_achieved'] else '❌ NOT MET'}"
            )
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
    else:
        print(
            f"❌ Service not available: {result.get('error', 'Unknown error')}"
        )
