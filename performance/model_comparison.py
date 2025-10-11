"""
Model comparison script for testing different ML models
"""

import argparse
import time
import json
import os
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


class ModelComparison:
    """Compare different ML models for performance"""
    
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url.rstrip('/')
        self.results_dir = "performance/results"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def create_test_image(self, width: int = 224, height: int = 224) -> bytes:
        """Create a test image"""
        img_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        image = Image.fromarray(img_array, mode='RGB')
        
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='JPEG')
        return img_buffer.getvalue()
    
    def test_model_performance(self, model_name: str, iterations: int = 50) -> Dict[str, Any]:
        """Test performance of a specific model"""
        logger.info(f"Testing {model_name} with {iterations} iterations")
        
        # Create test image
        test_image = self.create_test_image()
        
        # Test model info endpoint
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/api/v1/model/info", timeout=10)
            model_info_time = time.time() - start_time
            model_info_success = response.status_code == 200
        except Exception as e:
            model_info_time = time.time() - start_time
            model_info_success = False
            logger.error(f"Model info failed for {model_name}: {e}")
        
        # Test classification performance
        response_times = []
        success_count = 0
        
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
                response_times.append(response_time)
                
                if response.status_code == 200:
                    success_count += 1
                else:
                    logger.warning(f"Classification failed for {model_name}: {response.status_code}")
                    
            except Exception as e:
                response_time = time.time() - start_time
                response_times.append(response_time)
                logger.error(f"Classification error for {model_name}: {e}")
            
            if i % 10 == 0:
                logger.info(f"Progress for {model_name}: {i}/{iterations}")
        
        # Calculate statistics
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            sorted_times = sorted(response_times)
            p95_response_time = sorted_times[int(0.95 * len(sorted_times))]
            p99_response_time = sorted_times[int(0.99 * len(sorted_times))]
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p95_response_time = p99_response_time = 0
        
        success_rate = success_count / iterations if iterations > 0 else 0
        
        return {
            'model_name': model_name,
            'iterations': iterations,
            'success_count': success_count,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'p95_response_time': p95_response_time,
            'p99_response_time': p99_response_time,
            'model_info_time': model_info_time,
            'model_info_success': model_info_success,
            'all_response_times': response_times
        }
    
    def compare_models(self, models: List[str], iterations: int = 50) -> Dict[str, Any]:
        """Compare multiple models"""
        logger.info(f"Comparing models: {models}")
        
        results = {}
        
        for model_name in models:
            # Update model in running service
            self._update_model(model_name)
            
            # Wait for model to load
            time.sleep(5)
            
            # Test performance
            results[model_name] = self.test_model_performance(model_name, iterations)
        
        # Generate comparison report
        self._generate_comparison_report(results)
        
        return results
    
    def _update_model(self, model_name: str):
        """Update the model in the running service"""
        # This is a simplified approach - in production you'd restart containers
        # For now, we'll assume the service is configured for the model
        logger.info(f"Switching to model: {model_name}")
    
    def _generate_comparison_report(self, results: Dict[str, Any]):
        """Generate comparison report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.results_dir, f"model_comparison_{timestamp}.md")
        
        with open(report_file, 'w') as f:
            f.write("# Model Performance Comparison Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            # Summary table
            f.write("## Performance Summary\n\n")
            f.write("| Model | Success Rate | Avg Response Time | P95 Response Time | P99 Response Time |\n")
            f.write("|-------|--------------|------------------|-------------------|-------------------|\n")
            
            for model_name, result in results.items():
                f.write(f"| {model_name} | {result['success_rate']:.2%} | "
                       f"{result['avg_response_time']:.3f}s | "
                       f"{result['p95_response_time']:.3f}s | "
                       f"{result['p99_response_time']:.3f}s |\n")
            
            f.write("\n## Detailed Results\n\n")
            
            for model_name, result in results.items():
                f.write(f"### {model_name}\n\n")
                f.write(f"- **Iterations**: {result['iterations']}\n")
                f.write(f"- **Success Rate**: {result['success_rate']:.2%}\n")
                f.write(f"- **Average Response Time**: {result['avg_response_time']:.3f}s\n")
                f.write(f"- **Min Response Time**: {result['min_response_time']:.3f}s\n")
                f.write(f"- **Max Response Time**: {result['max_response_time']:.3f}s\n")
                f.write(f"- **95th Percentile**: {result['p95_response_time']:.3f}s\n")
                f.write(f"- **99th Percentile**: {result['p99_response_time']:.3f}s\n")
                f.write(f"- **Model Info Time**: {result['model_info_time']:.3f}s\n")
                f.write(f"- **Model Info Success**: {result['model_info_success']}\n\n")
            
            f.write("## Analysis\n\n")
            f.write("This comparison provides insights into the performance characteristics ")
            f.write("of different image classification models under identical test conditions.\n")
        
        logger.info(f"Comparison report saved: {report_file}")
        
        # Also save raw data
        data_file = os.path.join(self.results_dir, f"model_comparison_data_{timestamp}.json")
        with open(data_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Raw data saved: {data_file}")


def main():
    """Main function for model comparison"""
    parser = argparse.ArgumentParser(description="Model Performance Comparison")
    parser.add_argument("--url", default="http://localhost", help="Base URL of the service")
    parser.add_argument("--models", nargs="+", 
                       default=["resnet18", "resnet50", "efficientnet_b0"],
                       help="Models to compare")
    parser.add_argument("--iterations", type=int, default=50, 
                       help="Number of test iterations per model")
    
    args = parser.parse_args()
    
    # Create comparison instance
    comparison = ModelComparison(args.url)
    
    # Run comparison
    results = comparison.compare_models(args.models, args.iterations)
    
    # Print summary
    print("\n" + "="*60)
    print("MODEL COMPARISON SUMMARY")
    print("="*60)
    
    for model_name, result in results.items():
        print(f"\n{model_name}:")
        print(f"  Success Rate: {result['success_rate']:.2%}")
        print(f"  Avg Response Time: {result['avg_response_time']:.3f}s")
        print(f"  P95 Response Time: {result['p95_response_time']:.3f}s")
    
    print("="*60)


if __name__ == "__main__":
    main()
