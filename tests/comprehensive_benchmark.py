"""
Comprehensive performance benchmarking suite.

This module provides comprehensive performance testing across all deployment
environments and generates detailed reports.
"""

import requests
from PIL import Image
import io
import time
import statistics
import json
from datetime import datetime
from typing import List, Dict, Any
import argparse


class ComprehensivePerformanceBenchmark:
    """Comprehensive performance benchmarking across all environments."""

    def __init__(self):
        self.test_image = self._create_test_image()
        self.results = {}

    def _create_test_image(self) -> Image.Image:
        """Create a standard test image for performance testing."""
        return Image.new("RGB", (224, 224), color="red")

    def _get_image_bytes(self) -> io.BytesIO:
        """Get image as bytes for API requests."""
        img_bytes = io.BytesIO()
        self.test_image.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        return img_bytes

    def test_environment(
        self, base_url: str, environment_name: str, num_requests: int = 10
    ) -> Dict[str, Any]:
        """Test performance for a specific environment."""
        print(f"\nTesting {environment_name} at {base_url}...")

        response_times = []
        processing_times = []
        errors = []

        for i in range(num_requests):
            try:
                img_bytes = self._get_image_bytes()

                start_time = time.time()
                response = requests.post(
                    f"{base_url}/api/v1/classify",
                    files={"file": ("test.jpg", img_bytes, "image/jpeg")},
                    data={"top_k": 5},
                    timeout=30,
                )
                end_time = time.time()

                if response.status_code == 200:
                    data = response.json()
                    response_times.append((end_time - start_time) * 1000)
                    processing_times.append(data.get("processing_time_ms", 0))
                else:
                    errors.append(
                        f"HTTP {response.status_code}: {response.text}"
                    )

                time.sleep(0.1)

            except Exception as e:
                errors.append(f"Request {i+1} failed: {str(e)}")

        if response_times and processing_times:
            return {
                "environment": environment_name,
                "base_url": base_url,
                "num_requests": num_requests,
                "successful_requests": len(response_times),
                "errors": errors,
                "response_times": {
                    "min": min(response_times),
                    "max": max(response_times),
                    "avg": statistics.mean(response_times),
                    "p95": sorted(response_times)[
                        int(0.95 * len(response_times))
                    ],
                    "p99": sorted(response_times)[
                        int(0.99 * len(response_times))
                    ],
                },
                "processing_times": {
                    "min": min(processing_times),
                    "max": max(processing_times),
                    "avg": statistics.mean(processing_times),
                    "p95": sorted(processing_times)[
                        int(0.95 * len(processing_times))
                    ],
                    "p99": sorted(processing_times)[
                        int(0.99 * len(processing_times))
                    ],
                },
                "cache_performance": self._analyze_cache_performance(
                    processing_times
                ),
            }
        else:
            return {
                "environment": environment_name,
                "base_url": base_url,
                "num_requests": num_requests,
                "successful_requests": 0,
                "errors": errors,
                "error": "No successful requests",
            }

    def _analyze_cache_performance(
        self, processing_times: List[float]
    ) -> Dict[str, Any]:
        """Analyze cache performance from processing times."""
        if len(processing_times) < 2:
            return {
                "cache_miss_time": 0,
                "cache_hit_time": 0,
                "cache_hit_rate": 0,
            }

        # First request is typically cache miss, rest are cache hits
        cache_miss_time = processing_times[0]
        cache_hit_times = processing_times[1:]

        return {
            "cache_miss_time": cache_miss_time,
            "cache_hit_time": statistics.mean(cache_hit_times)
            if cache_hit_times
            else 0,
            "cache_hit_rate": len(cache_hit_times) / len(processing_times),
            "cache_hit_count": len(cache_hit_times),
            "cache_miss_count": 1,
        }

    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark across all environments."""
        print("Starting Comprehensive Performance Benchmark")
        print("=" * 60)

        environments = [
            ("http://localhost:8000", "Local Development"),
            ("http://localhost", "Docker Compose"),
            ("http://localhost:8080", "Kubernetes (Port Forward)"),
        ]

        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "environments": {},
            "summary": {},
        }

        for base_url, env_name in environments:
            try:
                result = self.test_environment(base_url, env_name, 10)
                benchmark_results["environments"][env_name] = result
            except Exception as e:
                benchmark_results["environments"][env_name] = {
                    "environment": env_name,
                    "base_url": base_url,
                    "error": f"Failed to test environment: {str(e)}",
                }

        # Generate summary
        benchmark_results["summary"] = self._generate_summary(
            benchmark_results["environments"]
        )

        return benchmark_results

    def _generate_summary(
        self, environments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary statistics across all environments."""
        summary = {
            "target_achieved": {},
            "performance_comparison": {},
            "cache_performance": {},
            "recommendations": [],
        }

        for env_name, result in environments.items():
            if "processing_times" in result:
                p95_processing = result["processing_times"]["p95"]
                summary["target_achieved"][env_name] = p95_processing < 200
                summary["performance_comparison"][env_name] = {
                    "p95_processing_ms": p95_processing,
                    "avg_processing_ms": result["processing_times"]["avg"],
                    "p95_response_ms": result["response_times"]["p95"],
                }
                summary["cache_performance"][env_name] = result[
                    "cache_performance"
                ]

        # Generate recommendations
        if summary["target_achieved"]:
            achieved_envs = [
                env
                for env, achieved in summary["target_achieved"].items()
                if achieved
            ]
            if achieved_envs:
                summary["recommendations"].append(
                    f"✅ Target achieved in: {', '.join(achieved_envs)}"
                )

            failed_envs = [
                env
                for env, achieved in summary["target_achieved"].items()
                if not achieved
            ]
            if failed_envs:
                summary["recommendations"].append(
                    f"❌ Target not achieved in: {', '.join(failed_envs)}"
                )

        return summary

    def print_results(self, results: Dict[str, Any]):
        """Print benchmark results in a readable format."""
        print("\n" + "=" * 60)
        print("COMPREHENSIVE PERFORMANCE BENCHMARK RESULTS")
        print("=" * 60)

        for env_name, result in results["environments"].items():
            print(f"\n{env_name}:")
            print("-" * 40)

            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue

            if "processing_times" in result:
                print(
                    f"✅ Successful Requests: {result['successful_requests']}/{result['num_requests']}"
                )
                print(
                    f"📊 Processing Time P95: {result['processing_times']['p95']:.1f}ms"
                )
                print(
                    f"📊 Processing Time Avg: {result['processing_times']['avg']:.1f}ms"
                )
                print(
                    f"📊 Response Time P95: {result['response_times']['p95']:.1f}ms"
                )
                print(
                    f"📊 Response Time Avg: {result['response_times']['avg']:.1f}ms"
                )

                # Cache performance
                cache = result["cache_performance"]
                print(f"💾 Cache Miss Time: {cache['cache_miss_time']:.1f}ms")
                print(f"💾 Cache Hit Time: {cache['cache_hit_time']:.1f}ms")
                print(f"💾 Cache Hit Rate: {cache['cache_hit_rate']:.1%}")

                # Target achievement
                target_met = result["processing_times"]["p95"] < 200
                print(
                    f"🎯 Target (<200ms): {'✅ ACHIEVED' if target_met else '❌ NOT MET'}"
                )

            if result["errors"]:
                print(f"⚠️  Errors: {len(result['errors'])}")
                for error in result["errors"][:3]:  # Show first 3 errors
                    print(f"   - {error}")

        # Summary
        print(f"\n{'=' * 60}")
        print("SUMMARY")
        print("=" * 60)

        summary = results["summary"]
        for recommendation in summary["recommendations"]:
            print(recommendation)

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_benchmark_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\nResults saved to: {filename}")


def main():
    """Main function to run comprehensive benchmark."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive performance benchmark"
    )
    parser.add_argument(
        "--save", action="store_true", help="Save results to JSON file"
    )
    parser.add_argument("--file", type=str, help="Custom filename for results")
    args = parser.parse_args()

    benchmark = ComprehensivePerformanceBenchmark()
    results = benchmark.run_comprehensive_benchmark()

    benchmark.print_results(results)

    if args.save:
        benchmark.save_results(results, args.file)


if __name__ == "__main__":
    main()
