"""
Load balancing algorithm comparison script
"""

import argparse
import time
import json
import os
import subprocess
import shutil
from datetime import datetime
from typing import Dict, Any, List
import logging
import requests
import io
from PIL import Image
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadBalancingComparison:
    """Compare different load balancing algorithms"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url.rstrip('/')
        self.results_dir = "performance/results"
        os.makedirs(self.results_dir, exist_ok=True)
        self.nginx_configs = {
            'round_robin': 'nginx/nginx-round-robin.conf',
            'least_conn': 'nginx/nginx.conf',
            'ip_hash': 'nginx/nginx-ip-hash.conf'
        }
    
    def create_test_image(self, width: int = 224, height: int = 224) -> bytes:
        """Create a test image"""
        img_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        image = Image.fromarray(img_array, mode='RGB')
        
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='JPEG')
        return img_buffer.getvalue()
    
    def switch_nginx_config(self, algorithm: str) -> bool:
        """Switch nginx configuration"""
        if algorithm not in self.nginx_configs:
            logger.error(f"Unknown algorithm: {algorithm}")
            return False
        
        config_file = self.nginx_configs[algorithm]
        
        try:
            # Copy the config file
            shutil.copy(config_file, 'nginx/nginx.conf')
            
            # Restart nginx container
            result = subprocess.run([
                'docker-compose', 'restart', 'nginx-lb'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"Switched to {algorithm} load balancing")
                # Wait for nginx to restart
                time.sleep(5)
                return True
            else:
                logger.error(f"Failed to restart nginx: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error switching nginx config: {e}")
            return False
    
    def test_load_balancing_performance(self, algorithm: str, iterations: int = 100) -> Dict[str, Any]:
        """Test performance with specific load balancing algorithm"""
        logger.info(f"Testing {algorithm} load balancing with {iterations} iterations")
        
        # Switch to the algorithm
        if not self.switch_nginx_config(algorithm):
            return {}
        
        # Create test image
        test_image = self.create_test_image()
        
        # Test health endpoint
        health_times = []
        health_success = 0
        
        for i in range(20):  # Test health endpoint 20 times
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/v1/health", timeout=10)
                response_time = time.time() - start_time
                health_times.append(response_time)
                if response.status_code == 200:
                    health_success += 1
            except Exception as e:
                health_times.append(time.time() - start_time)
                logger.error(f"Health check failed: {e}")
        
        # Test classification endpoint
        classification_times = []
        classification_success = 0
        
        for i in range(iterations):
            start_time = time.time()
            try:
                files = {'file': ('test_image.jpg', test_image, 'image/jpeg')}
                data = {'top_k': 5}
                
                response = requests.post(
                    f"{self.base_url}/api/v1/classify",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                response_time = time.time() - start_time
                classification_times.append(response_time)
                
                if response.status_code == 200:
                    classification_success += 1
                else:
                    logger.warning(f"Classification failed: {response.status_code}")
                    
            except Exception as e:
                classification_times.append(time.time() - start_time)
                logger.error(f"Classification error: {e}")
            
            if i % 20 == 0:
                logger.info(f"Progress for {algorithm}: {i}/{iterations}")
        
        # Calculate statistics
        def calculate_stats(times):
            if not times:
                return {}
            sorted_times = sorted(times)
            return {
                'avg': sum(times) / len(times),
                'min': min(times),
                'max': max(times),
                'p95': sorted_times[int(0.95 * len(sorted_times))],
                'p99': sorted_times[int(0.99 * len(sorted_times))]
            }
        
        health_stats = calculate_stats(health_times)
        classification_stats = calculate_stats(classification_times)
        
        return {
            'algorithm': algorithm,
            'health': {
                'success_rate': health_success / 20 if health_success > 0 else 0,
                'stats': health_stats
            },
            'classification': {
                'success_rate': classification_success / iterations if classification_success > 0 else 0,
                'stats': classification_stats,
                'iterations': iterations
            }
        }
    
    def compare_algorithms(self, algorithms: List[str], iterations: int = 100) -> Dict[str, Any]:
        """Compare multiple load balancing algorithms"""
        logger.info(f"Comparing load balancing algorithms: {algorithms}")
        
        results = {}
        
        for algorithm in algorithms:
            if algorithm not in self.nginx_configs:
                logger.warning(f"Skipping unknown algorithm: {algorithm}")
                continue
            
            result = self.test_load_balancing_performance(algorithm, iterations)
            if result:
                results[algorithm] = result
        
        # Generate comparison report
        self._generate_comparison_report(results)
        
        return results
    
    def _generate_comparison_report(self, results: Dict[str, Any]):
        """Generate load balancing comparison report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.results_dir, f"load_balancing_comparison_{timestamp}.md")
        
        with open(report_file, 'w') as f:
            f.write("# Load Balancing Algorithm Comparison Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            f.write("## Performance Summary\n\n")
            f.write("| Algorithm | Health Success Rate | Classification Success Rate | Avg Classification Time | P95 Classification Time |\n")
            f.write("|-----------|---------------------|----------------------------|------------------------|--------------------------|\n")
            
            for algorithm, result in results.items():
                health_sr = result['health']['success_rate']
                classification_sr = result['classification']['success_rate']
                avg_time = result['classification']['stats'].get('avg', 0)
                p95_time = result['classification']['stats'].get('p95', 0)
                
                f.write(f"| {algorithm.replace('_', ' ').title()} | {health_sr:.2%} | "
                       f"{classification_sr:.2%} | {avg_time:.3f}s | {p95_time:.3f}s |\n")
            
            f.write("\n## Detailed Results\n\n")
            
            for algorithm, result in results.items():
                f.write(f"### {algorithm.replace('_', ' ').title()}\n\n")
                
                # Health endpoint results
                f.write("#### Health Endpoint\n")
                health = result['health']
                f.write(f"- **Success Rate**: {health['success_rate']:.2%}\n")
                if health['stats']:
                    f.write(f"- **Average Response Time**: {health['stats']['avg']:.3f}s\n")
                    f.write(f"- **95th Percentile**: {health['stats']['p95']:.3f}s\n")
                f.write("\n")
                
                # Classification endpoint results
                f.write("#### Classification Endpoint\n")
                classification = result['classification']
                f.write(f"- **Success Rate**: {classification['success_rate']:.2%}\n")
                f.write(f"- **Iterations**: {classification['iterations']}\n")
                if classification['stats']:
                    f.write(f"- **Average Response Time**: {classification['stats']['avg']:.3f}s\n")
                    f.write(f"- **Min Response Time**: {classification['stats']['min']:.3f}s\n")
                    f.write(f"- **Max Response Time**: {classification['stats']['max']:.3f}s\n")
                    f.write(f"- **95th Percentile**: {classification['stats']['p95']:.3f}s\n")
                    f.write(f"- **99th Percentile**: {classification['stats']['p99']:.3f}s\n")
                f.write("\n")
            
            f.write("## Analysis\n\n")
            f.write("This comparison provides insights into the performance characteristics ")
            f.write("of different load balancing algorithms for ML workloads.\n\n")
            
            f.write("### Key Findings\n\n")
            f.write("1. **Algorithm Selection**: Different algorithms show varying performance ")
            f.write("characteristics under different load patterns.\n\n")
            
            f.write("2. **Health Check Performance**: All algorithms should maintain high ")
            f.write("success rates for health checks.\n\n")
            
            f.write("3. **Classification Performance**: The choice of algorithm can impact ")
            f.write("classification response times and success rates.\n\n")
        
        logger.info(f"Load balancing comparison report saved: {report_file}")
        
        # Also save raw data
        data_file = os.path.join(self.results_dir, f"load_balancing_data_{timestamp}.json")
        with open(data_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Raw data saved: {data_file}")


def main():
    """Main function for load balancing comparison"""
    parser = argparse.ArgumentParser(description="Load Balancing Algorithm Comparison")
    parser.add_argument("--url", default="http://localhost", help="Base URL of the service")
    parser.add_argument("--algorithms", nargs="+", 
                       default=["round_robin", "least_conn", "ip_hash"],
                       help="Load balancing algorithms to compare")
    parser.add_argument("--iterations", type=int, default=100, 
                       help="Number of test iterations per algorithm")
    
    args = parser.parse_args()
    
    # Create comparison instance
    comparison = LoadBalancingComparison(args.url)
    
    # Run comparison
    results = comparison.compare_algorithms(args.algorithms, args.iterations)
    
    # Print summary
    print("\n" + "="*70)
    print("LOAD BALANCING COMPARISON SUMMARY")
    print("="*70)
    
    for algorithm, result in results.items():
        print(f"\n{algorithm.replace('_', ' ').title()}:")
        print(f"  Health Success Rate: {result['health']['success_rate']:.2%}")
        print(f"  Classification Success Rate: {result['classification']['success_rate']:.2%}")
        if result['classification']['stats']:
            print(f"  Avg Classification Time: {result['classification']['stats']['avg']:.3f}s")
            print(f"  P95 Classification Time: {result['classification']['stats']['p95']:.3f}s")
    
    print("="*70)


if __name__ == "__main__":
    main()
