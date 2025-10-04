"""
Performance benchmarking script for the image classifier service
"""

import argparse
import time
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from performance.load_tests import LoadTester, ImageGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Performance benchmarking suite"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.tester = LoadTester(base_url)
        self.results_dir = "performance/results"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def run_health_benchmark(self, duration: int = 60, rps: int = 10) -> Dict[str, Any]:
        """Benchmark health endpoint"""
        logger.info(f"Running health endpoint benchmark: {duration}s at {rps} RPS")
        
        results = self.tester.run_load_test(
            test_type="health",
            duration_seconds=duration,
            requests_per_second=rps
        )
        
        analysis = self.tester.analyze_results(results)
        self._save_benchmark_results("health", results, analysis)
        
        return analysis
    
    def run_model_info_benchmark(self, duration: int = 60, rps: int = 10) -> Dict[str, Any]:
        """Benchmark model info endpoint"""
        logger.info(f"Running model info endpoint benchmark: {duration}s at {rps} RPS")
        
        results = self.tester.run_load_test(
            test_type="model_info",
            duration_seconds=duration,
            requests_per_second=rps
        )
        
        analysis = self.tester.analyze_results(results)
        self._save_benchmark_results("model_info", results, analysis)
        
        return analysis
    
    def run_classification_benchmark(self, duration: int = 60, rps: int = 5, 
                                   image_sizes: List[tuple] = None) -> Dict[str, Any]:
        """Benchmark image classification endpoint"""
        logger.info(f"Running classification benchmark: {duration}s at {rps} RPS")
        
        if image_sizes is None:
            image_sizes = [(224, 224), (256, 256), (512, 512)]
        
        # Generate test images
        test_images = ImageGenerator.create_test_images(len(image_sizes), image_sizes)
        
        results = []
        start_time = time.time()
        request_interval = 1.0 / rps
        
        while time.time() - start_time < duration:
            test_start = time.time()
            
            # Select random image and top_k
            image_bytes = test_images[time.time() % len(test_images)]
            top_k = 5
            
            result = self.tester.test_classify_endpoint(image_bytes, top_k)
            results.append(result)
            
            # Maintain RPS
            elapsed = time.time() - test_start
            sleep_time = max(0, request_interval - elapsed)
            time.sleep(sleep_time)
        
        analysis = self.tester.analyze_results(results)
        self._save_benchmark_results("classification", results, analysis)
        
        return analysis
    
    def run_stress_test(self, max_workers: int = 50, duration: int = 300) -> Dict[str, Any]:
        """Run stress test with increasing load"""
        logger.info(f"Running stress test: {max_workers} workers for {duration}s")
        
        # Generate test images
        test_images = ImageGenerator.create_test_images(10)
        
        results = self.tester.run_stress_test(
            test_type="classify",
            max_workers=max_workers,
            duration_seconds=duration,
            image_bytes=test_images[0],
            top_k=5
        )
        
        analysis = self.tester.analyze_results(results)
        self._save_benchmark_results("stress", results, analysis)
        
        return analysis
    
    def run_memory_benchmark(self, iterations: int = 100) -> Dict[str, Any]:
        """Benchmark memory usage during classification"""
        logger.info(f"Running memory benchmark: {iterations} iterations")
        
        # Generate test images of different sizes
        test_images = []
        for size in [(224, 224), (512, 512), (1024, 1024)]:
            test_images.extend(ImageGenerator.create_test_images(10, [size]))
        
        results = []
        start_time = time.time()
        
        for i in range(iterations):
            image_bytes = test_images[i % len(test_images)]
            result = self.tester.test_classify_endpoint(image_bytes, 5)
            results.append(result)
            
            if i % 10 == 0:
                logger.info(f"Memory benchmark progress: {i}/{iterations}")
        
        analysis = self.tester.analyze_results(results)
        analysis['total_time'] = time.time() - start_time
        analysis['iterations'] = iterations
        
        self._save_benchmark_results("memory", results, analysis)
        
        return analysis
    
    def run_latency_benchmark(self, iterations: int = 1000) -> Dict[str, Any]:
        """Benchmark latency with single requests"""
        logger.info(f"Running latency benchmark: {iterations} iterations")
        
        # Generate small test images for fast processing
        test_images = ImageGenerator.create_test_images(5, [(224, 224)])
        
        results = []
        start_time = time.time()
        
        for i in range(iterations):
            image_bytes = test_images[i % len(test_images)]
            result = self.tester.test_classify_endpoint(image_bytes, 5)
            results.append(result)
            
            if i % 100 == 0:
                logger.info(f"Latency benchmark progress: {i}/{iterations}")
        
        analysis = self.tester.analyze_results(results)
        analysis['total_time'] = time.time() - start_time
        analysis['iterations'] = iterations
        
        self._save_benchmark_results("latency", results, analysis)
        
        return analysis
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark suite"""
        logger.info("Starting comprehensive benchmark suite")
        
        benchmark_results = {}
        
        # 1. Health endpoint benchmark
        benchmark_results['health'] = self.run_health_benchmark(duration=30, rps=20)
        
        # 2. Model info benchmark
        benchmark_results['model_info'] = self.run_model_info_benchmark(duration=30, rps=20)
        
        # 3. Classification benchmark
        benchmark_results['classification'] = self.run_classification_benchmark(
            duration=60, rps=5
        )
        
        # 4. Latency benchmark
        benchmark_results['latency'] = self.run_latency_benchmark(iterations=100)
        
        # 5. Memory benchmark
        benchmark_results['memory'] = self.run_memory_benchmark(iterations=50)
        
        # 6. Stress test
        benchmark_results['stress'] = self.run_stress_test(max_workers=20, duration=120)
        
        # Generate comprehensive report
        self._generate_comprehensive_report(benchmark_results)
        
        return benchmark_results
    
    def _save_benchmark_results(self, test_name: str, results: List, analysis: Dict[str, Any]):
        """Save benchmark results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw results
        results_file = os.path.join(
            self.results_dir, 
            f"{test_name}_results_{timestamp}.json"
        )
        
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
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        # Save analysis
        analysis_file = os.path.join(
            self.results_dir, 
            f"{test_name}_analysis_{timestamp}.json"
        )
        
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Results saved: {results_file}, {analysis_file}")
    
    def _generate_comprehensive_report(self, benchmark_results: Dict[str, Any]):
        """Generate comprehensive benchmark report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.results_dir, f"comprehensive_report_{timestamp}.md")
        
        with open(report_file, 'w') as f:
            f.write("# Comprehensive Performance Benchmark Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            for test_name, results in benchmark_results.items():
                f.write(f"## {test_name.title()} Benchmark\n\n")
                f.write(f"- **Total Requests**: {results['total_requests']}\n")
                f.write(f"- **Success Rate**: {results['success_rate']:.2%}\n")
                f.write(f"- **Average Response Time**: {results['avg_response_time']:.3f}s\n")
                f.write(f"- **95th Percentile**: {results['p95_response_time']:.3f}s\n")
                f.write(f"- **99th Percentile**: {results['p99_response_time']:.3f}s\n")
                f.write(f"- **Requests per Second**: {results['requests_per_second']:.2f}\n\n")
                
                if 'error_breakdown' in results and results['error_breakdown']:
                    f.write("### Error Breakdown\n\n")
                    for error_type, count in results['error_breakdown'].items():
                        f.write(f"- {error_type}: {count}\n")
                    f.write("\n")
            
            f.write("## Summary\n\n")
            f.write("This comprehensive benchmark provides insights into the performance ")
            f.write("characteristics of the image classifier service under various load conditions.\n")
        
        logger.info(f"Comprehensive report saved: {report_file}")


def main():
    """Main function for running benchmarks"""
    parser = argparse.ArgumentParser(description="Image Classifier Performance Benchmark")
    parser.add_argument("--url", default="http://localhost", help="Base URL of the service")
    parser.add_argument("--test", choices=[
        "health", "model_info", "classification", "stress", "memory", "latency", "comprehensive"
    ], default="comprehensive", help="Test to run")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--rps", type=int, default=10, help="Requests per second")
    parser.add_argument("--workers", type=int, default=50, help="Number of workers for stress test")
    parser.add_argument("--iterations", type=int, default=100, help="Number of iterations for latency/memory tests")
    
    args = parser.parse_args()
    
    # Create benchmark instance
    benchmark = PerformanceBenchmark(args.url)
    
    # Run selected test
    if args.test == "health":
        results = benchmark.run_health_benchmark(args.duration, args.rps)
    elif args.test == "model_info":
        results = benchmark.run_model_info_benchmark(args.duration, args.rps)
    elif args.test == "classification":
        results = benchmark.run_classification_benchmark(args.duration, args.rps)
    elif args.test == "stress":
        results = benchmark.run_stress_test(args.workers, args.duration)
    elif args.test == "memory":
        results = benchmark.run_memory_benchmark(args.iterations)
    elif args.test == "latency":
        results = benchmark.run_latency_benchmark(args.iterations)
    elif args.test == "comprehensive":
        results = benchmark.run_comprehensive_benchmark()
    
    # Print summary
    print("\n" + "="*50)
    print("BENCHMARK SUMMARY")
    print("="*50)
    print(f"Test: {args.test}")
    print(f"Total Requests: {results.get('total_requests', 'N/A')}")
    print(f"Success Rate: {results.get('success_rate', 0):.2%}")
    print(f"Average Response Time: {results.get('avg_response_time', 0):.3f}s")
    print(f"95th Percentile: {results.get('p95_response_time', 0):.3f}s")
    print(f"Requests per Second: {results.get('requests_per_second', 0):.2f}")
    print("="*50)


if __name__ == "__main__":
    main()
