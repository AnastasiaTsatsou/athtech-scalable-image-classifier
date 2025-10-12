#!/usr/bin/env python3
"""
Unified Benchmark Script
Tests all three systems (Custom, KServe, TensorFlow Serving) with identical workloads

IMPORTANT: All systems now running on Kubernetes for fair comparison!
- Custom system: Kubernetes deployment (no nginx rate limiting)
- TensorFlow Serving: Kubernetes with proxy
- KServe: Kubernetes InferenceService

TensorFlow Serving tests MobileNetV3-Large model with proper 224x224 RGB image input.
Resource monitoring uses real kubectl top pods data.

NOTE: Current TensorFlow Serving deployment uses half_plus_two model. For proper comparison,
deploy MobileNetV3-Large model using the tensorflow-serving/export_model.py script.
"""

import os
import sys
import time
import asyncio
import aiohttp
import requests
import json
import base64
import numpy as np
from PIL import Image
import io
from pathlib import Path
from typing import Dict, List, Any
import statistics
from datetime import datetime
import subprocess

class BenchmarkResult:
    """Container for benchmark results"""
    def __init__(self, system_name: str):
        self.system_name = system_name
        self.endpoint = ""
        self.results = {
            "warmup": {"success": False, "avg_time_ms": 0},
            "single_request": {"success": False, "times_ms": [], "avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0, "max_ms": 0},
            "sustained_load": {"success": False, "times_ms": [], "avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0, "max_ms": 0, "throughput_rps": 0, "success_rate": 0},
            "burst_load": {"success": False, "times_ms": [], "avg_ms": 0, "p50_ms": 0, "p95_ms": 0, "p99_ms": 0, "max_ms": 0, "throughput_rps": 0, "success_rate": 0},
            "resource_usage": {"avg_cpu_percent": 0, "avg_memory_mb": 0}
        }

class BenchmarkRunner:
    """Main benchmark runner"""
    
    def __init__(self):
        self.results = {}
        self.test_image = self.create_test_image()
        self.resource_monitoring = False
        
    def create_test_image(self) -> bytes:
        """Create a synthetic test image"""
        # Create a red 224x224 RGB image
        image = Image.new('RGB', (224, 224), color='red')
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='JPEG')
        return img_buffer.getvalue()
    
    def create_test_image_numpy(self) -> np.ndarray:
        """Create a test image as numpy array for TF Serving"""
        # Create a red 224x224 RGB image
        image = Image.new('RGB', (224, 224), color='red')
        return np.array(image)
    
    def prepare_custom_request(self) -> Dict[str, Any]:
        """Prepare request for custom FastAPI system"""
        return {
            "files": {"file": ("test.jpg", self.test_image, "image/jpeg")},
            "data": {"top_k": 5}
        }
    
    def prepare_kserve_request(self) -> Dict[str, Any]:
        """Prepare request for KServe"""
        image_b64 = base64.b64encode(self.test_image).decode('utf-8')
        return {
            "instances": [{"body": image_b64}]
        }
    
    def prepare_tfserving_request(self) -> Dict[str, Any]:
        """Prepare request for TensorFlow Serving"""
        # Check if MobileNetV3-Large model is available, otherwise use simple test data
        try:
            response = requests.get("http://localhost:8082/v1/models/mobilenet_v3_large", timeout=2)
            if response.status_code == 200:
                # MobileNetV3-Large model available - send proper 224x224 RGB image array
                test_image_np = self.create_test_image_numpy()
                # Normalize to [0, 1] range as expected by MobileNetV3-Large
                normalized_image = test_image_np.astype(np.float32) / 255.0
                return {
                    "instances": [normalized_image.tolist()]
                }
        except:
            pass
        
        # Fallback to simple test data for half_plus_two model
        print("WARNING: MobileNetV3-Large model not found, using simple test data for half_plus_two model")
        test_data = [1.0, 2.0, 3.0, 4.0, 5.0]  # Simple test array
        return {
            "instances": [test_data]
        }
    
    def send_request(self, endpoint: str, payload: Dict[str, Any], timeout: int = 30) -> tuple[bool, float, Dict]:
        """Send a single request and measure time"""
        start_time = time.time()
        
        try:
            if endpoint.startswith("http://localhost:8082"):
                # TensorFlow Serving - determine model name dynamically
                model_name = "mobilenet_v3_large"  # Try MobileNetV3-Large first
                try:
                    response = requests.get(f"{endpoint}/v1/models/{model_name}", timeout=2)
                    if response.status_code != 200:
                        model_name = "half_plus_two"  # Fallback to simple model
                except:
                    model_name = "half_plus_two"
                
                response = requests.post(
                    f"{endpoint}/v1/models/{model_name}:predict",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=timeout
                )
            elif endpoint == "http://localhost:8081":
                # Custom FastAPI system
                response = requests.post(
                    f"{endpoint}/api/v1/classify",
                    files=payload["files"],
                    data=payload["data"],
                    timeout=timeout
                )
            elif endpoint == "http://localhost:8083":
                # KServe
                response = requests.post(
                    f"{endpoint}/v2/models/mobilenet_v3_large/infer",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=timeout
                )
            else:
                return False, 0, {"error": "Unknown endpoint"}
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                return True, response_time_ms, response.json()
            else:
                return False, response_time_ms, {"error": response.text}
                
        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            return False, response_time_ms, {"error": str(e)}
    
    async def send_request_async(self, session: aiohttp.ClientSession, endpoint: str, payload: Dict[str, Any]) -> tuple[bool, float]:
        """Send async request for load testing"""
        start_time = time.time()
        
        try:
            if endpoint.startswith("http://localhost:8082"):
                # TensorFlow Serving - determine model name dynamically
                model_name = "mobilenet_v3_large"  # Try MobileNetV3-Large first
                try:
                    async with session.get(f"{endpoint}/v1/models/{model_name}", timeout=2) as resp:
                        if resp.status != 200:
                            model_name = "half_plus_two"  # Fallback to simple model
                except:
                    model_name = "half_plus_two"
                
                async with session.post(
                    f"{endpoint}/v1/models/{model_name}:predict",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    await response.text()
                    success = response.status == 200
            elif endpoint == "http://localhost:8081":
                # Custom FastAPI system
                data = aiohttp.FormData()
                data.add_field('file', payload["files"]["file"][1], filename=payload["files"]["file"][0], content_type=payload["files"]["file"][2])
                data.add_field('top_k', str(payload["data"]["top_k"]))
                
                async with session.post(f"{endpoint}/api/v1/classify", data=data) as response:
                    await response.text()
                    success = response.status == 200
            elif endpoint == "http://localhost:8083":
                # KServe
                async with session.post(
                    f"{endpoint}/v2/models/mobilenet_v3_large/infer",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    await response.text()
                    success = response.status == 200
            else:
                success = False
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            return success, response_time_ms
            
        except Exception as e:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            return False, response_time_ms
    
    def calculate_percentiles(self, times: List[float]) -> Dict[str, float]:
        """Calculate percentiles from response times"""
        if not times:
            return {"p50": 0, "p95": 0, "p99": 0}
        
        sorted_times = sorted(times)
        n = len(sorted_times)
        
        return {
            "p50": sorted_times[int(n * 0.5)],
            "p95": sorted_times[int(n * 0.95)],
            "p99": sorted_times[int(n * 0.99)]
        }
    
    def run_warmup(self, system_name: str, endpoint: str, payload: Dict[str, Any]) -> bool:
        """Run warmup requests"""
        print(f"Warming up {system_name}...")
        
        success_count = 0
        total_time = 0
        
        for i in range(10):
            success, response_time, _ = self.send_request(endpoint, payload)
            if success:
                success_count += 1
                total_time += response_time
            
            time.sleep(0.1)  # Small delay between requests
        
        avg_time = total_time / max(success_count, 1)
        
        self.results[system_name].results["warmup"] = {
            "success": success_count >= 8,  # At least 80% success
            "avg_time_ms": avg_time
        }
        
        print(f"SUCCESS: Warmup completed: {success_count}/10 successful, avg {avg_time:.1f}ms")
        return success_count >= 8
    
    def run_single_request_test(self, system_name: str, endpoint: str, payload: Dict[str, Any]) -> bool:
        """Run single request latency test"""
        print(f"Running single request test for {system_name}...")
        
        times = []
        success_count = 0
        
        for i in range(100):
            success, response_time, _ = self.send_request(endpoint, payload)
            if success:
                times.append(response_time)
                success_count += 1
            
            time.sleep(0.01)  # Small delay
        
        if times:
            avg_time = statistics.mean(times)
            percentiles = self.calculate_percentiles(times)
            max_time = max(times)
            
            self.results[system_name].results["single_request"] = {
                "success": True,
                "times_ms": times,
                "avg_ms": avg_time,
                "p50_ms": percentiles["p50"],
                "p95_ms": percentiles["p95"],
                "p99_ms": percentiles["p99"],
                "max_ms": max_time
            }
            
            print(f"SUCCESS: Single request test: {success_count}/100 successful")
            print(f"  Avg: {avg_time:.1f}ms, P95: {percentiles['p95']:.1f}ms")
            return True
        else:
            print(f"ERROR: Single request test failed: no successful requests")
            return False
    
    async def run_load_test(self, system_name: str, endpoint: str, payload: Dict[str, Any], 
                           num_requests: int, target_rps: float, test_name: str) -> bool:
        """Run load test with specified RPS"""
        print(f"Running {test_name} for {system_name}...")
        
        times = []
        success_count = 0
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            request_interval = 1.0 / target_rps
            
            for i in range(num_requests):
                task = asyncio.create_task(self.send_request_async(session, endpoint, payload))
                tasks.append(task)
                
                if i < num_requests - 1:  # Don't sleep after the last request
                    await asyncio.sleep(request_interval)
            
            # Collect results
            for task in tasks:
                success, response_time = await task
                if success:
                    times.append(response_time)
                    success_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        actual_rps = num_requests / total_time
        success_rate = (success_count / num_requests) * 100
        
        if times:
            avg_time = statistics.mean(times)
            percentiles = self.calculate_percentiles(times)
            max_time = max(times)
            
            # Map test names to result keys
            result_key = test_name.replace(" ", "_").lower()
            if "sustained" in result_key:
                result_key = "sustained_load"
            elif "burst" in result_key:
                result_key = "burst_load"
            
            self.results[system_name].results[result_key] = {
                "success": True,
                "times_ms": times,
                "avg_ms": avg_time,
                "p50_ms": percentiles["p50"],
                "p95_ms": percentiles["p95"],
                "p99_ms": percentiles["p99"],
                "max_ms": max_time,
                "throughput_rps": actual_rps,
                "success_rate": success_rate
            }
            
            print(f"SUCCESS: {test_name}: {success_count}/{num_requests} successful")
            print(f"  Avg: {avg_time:.1f}ms, P95: {percentiles['p95']:.1f}ms")
            print(f"  Throughput: {actual_rps:.1f} RPS, Success rate: {success_rate:.1f}%")
            return True
        else:
            print(f"ERROR: {test_name} failed: no successful requests")
            return False
    
    def run_sustained_load_test(self, system_name: str, endpoint: str, payload: Dict[str, Any]) -> bool:
        """Run sustained load test"""
        return asyncio.run(self.run_load_test(system_name, endpoint, payload, 500, 10.0, "sustained load test"))
    
    def run_burst_load_test(self, system_name: str, endpoint: str, payload: Dict[str, Any]) -> bool:
        """Run burst load test"""
        return asyncio.run(self.run_load_test(system_name, endpoint, payload, 200, 50.0, "burst load test"))
    
    def monitor_resources(self, system_name: str) -> Dict[str, float]:
        """Monitor resource usage during tests using kubectl top pods"""
        print(f"Monitoring resources for {system_name}...")
        
        try:
            # Determine namespace based on system
            if system_name == "Custom":
                namespace = "image-classifier"  # Kubernetes custom system namespace
                pod_selector = "app=scalable-image-classifier"
            elif system_name == "KServe":
                namespace = "kserve-comparison"
                pod_selector = "serving.kserve.io/inferenceservice=mobilenet-v3-large"
            elif system_name == "TensorFlow Serving":
                namespace = "tfserving-simple"
                pod_selector = "app=tensorflow-serving-proxy"
            else:
                return {"avg_cpu_percent": 0.0, "avg_memory_mb": 0.0}
            
            # Get pod resource usage
            cmd = f"kubectl top pods -n {namespace} --selector={pod_selector} --no-headers"
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                if "Metrics API not available" in result.stderr:
                    print(f"WARNING: Metrics API not available - install metrics-server for resource monitoring")
                else:
                    print(f"WARNING: Could not get resource metrics: {result.stderr}")
                return {"avg_cpu_percent": 0.0, "avg_memory_mb": 0.0}
            
            lines = result.stdout.strip().split('\n')
            if not lines or lines == ['']:
                print(f"WARNING: No pods found for {system_name}")
                return {"avg_cpu_percent": 0.0, "avg_memory_mb": 0.0}
            
            total_cpu_millicores = 0
            total_memory_mb = 0
            pod_count = 0
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        cpu_str = parts[1]
                        memory_str = parts[2]
                        
                        # Parse CPU (convert from millicores to percentage)
                        if cpu_str.endswith('m'):
                            cpu_millicores = float(cpu_str[:-1])
                            total_cpu_millicores += cpu_millicores
                        elif cpu_str.endswith('n'):
                            cpu_nanocores = float(cpu_str[:-1])
                            total_cpu_millicores += cpu_nanocores / 1000000
                        else:
                            cpu_cores = float(cpu_str)
                            total_cpu_millicores += cpu_cores * 1000
                        
                        # Parse Memory (convert to MB)
                        if memory_str.endswith('Mi'):
                            memory_mb = float(memory_str[:-2])
                        elif memory_str.endswith('Gi'):
                            memory_mb = float(memory_str[:-2]) * 1024
                        elif memory_str.endswith('Ki'):
                            memory_mb = float(memory_str[:-2]) / 1024
                        else:
                            memory_mb = float(memory_str) / (1024 * 1024)  # Assume bytes
                        
                        total_memory_mb += memory_mb
                        pod_count += 1
            
            if pod_count == 0:
                return {"avg_cpu_percent": 0.0, "avg_memory_mb": 0.0}
            
            # Convert millicores to percentage (assuming 1 CPU = 1000m = 100%)
            avg_cpu_percent = (total_cpu_millicores / pod_count) / 10.0  # Convert millicores to percentage
            avg_memory_mb = total_memory_mb / pod_count
            
            print(f"Resource usage: CPU {avg_cpu_percent:.1f}%, Memory {avg_memory_mb:.1f}MB")
            return {
                "avg_cpu_percent": avg_cpu_percent,
                "avg_memory_mb": avg_memory_mb
            }
            
        except Exception as e:
            print(f"WARNING: Error monitoring resources: {e}")
            return {"avg_cpu_percent": 0.0, "avg_memory_mb": 0.0}
    
    def run_benchmark(self, system_name: str, endpoint: str) -> bool:
        """Run complete benchmark for a system"""
        print(f"\nStarting benchmark for {system_name}")
        print(f"Endpoint: {endpoint}")
        
        # Initialize result
        self.results[system_name] = BenchmarkResult(system_name)
        self.results[system_name].endpoint = endpoint
        
        # Prepare payload
        if system_name == "Custom":
            payload = self.prepare_custom_request()
        elif system_name == "KServe":
            payload = self.prepare_kserve_request()
        elif system_name == "TensorFlow Serving":
            payload = self.prepare_tfserving_request()
        else:
            print(f"ERROR: Unknown system: {system_name}")
            return False
        
        try:
            # Run tests
            if not self.run_warmup(system_name, endpoint, payload):
                print(f"WARNING: Warmup failed for {system_name}, continuing...")
            
            if not self.run_single_request_test(system_name, endpoint, payload):
                print(f"ERROR: Single request test failed for {system_name}")
                return False
            
            if not self.run_sustained_load_test(system_name, endpoint, payload):
                print(f"WARNING: Sustained load test failed for {system_name}, continuing...")
            
            if not self.run_burst_load_test(system_name, endpoint, payload):
                print(f"WARNING: Burst load test failed for {system_name}, continuing...")
            
            # Monitor resources
            resource_usage = self.monitor_resources(system_name)
            self.results[system_name].results["resource_usage"] = resource_usage
            
            print(f"SUCCESS: Benchmark completed for {system_name}")
            return True
            
        except Exception as e:
            print(f"ERROR: Benchmark failed for {system_name}: {e}")
            return False
    
    def generate_report(self) -> str:
        """Generate markdown report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = f"""# Model Serving Comparison Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Performance Summary

| System | P95 Latency | Throughput | CPU % | Memory | Success Rate |
|--------|-------------|------------|-------|--------|-------------|
"""
        
        for system_name, result in self.results.items():
            sustained = result.results["sustained_load"]
            resources = result.results["resource_usage"]
            
            report += f"| {system_name} | {sustained.get('p95_ms', 0):.1f}ms | {sustained.get('throughput_rps', 0):.1f} RPS | {resources.get('avg_cpu_percent', 0):.1f}% | {resources.get('avg_memory_mb', 0):.1f}MB | {sustained.get('success_rate', 0):.1f}% |\n"
        
        report += "\n## Detailed Results\n\n"
        
        for system_name, result in self.results.items():
            report += f"### {system_name}\n\n"
            report += f"**Endpoint:** {result.endpoint}\n\n"
            
            # Single request test
            single = result.results["single_request"]
            if single["success"]:
                report += f"**Single Request Test:**\n"
                report += f"- Average: {single['avg_ms']:.1f}ms\n"
                report += f"- P95: {single['p95_ms']:.1f}ms\n"
                report += f"- P99: {single['p99_ms']:.1f}ms\n"
                report += f"- Max: {single['max_ms']:.1f}ms\n\n"
            
            # Sustained load test
            sustained = result.results["sustained_load"]
            if sustained["success"]:
                report += f"**Sustained Load Test:**\n"
                report += f"- Average: {sustained['avg_ms']:.1f}ms\n"
                report += f"- P95: {sustained['p95_ms']:.1f}ms\n"
                report += f"- Throughput: {sustained['throughput_rps']:.1f} RPS\n"
                report += f"- Success Rate: {sustained['success_rate']:.1f}%\n\n"
            
            # Burst load test
            burst = result.results["burst_load"]
            if burst["success"]:
                report += f"**Burst Load Test:**\n"
                report += f"- Average: {burst['avg_ms']:.1f}ms\n"
                report += f"- P95: {burst['p95_ms']:.1f}ms\n"
                report += f"- Throughput: {burst['throughput_rps']:.1f} RPS\n"
                report += f"- Success Rate: {burst['success_rate']:.1f}%\n\n"
            
            # Resource usage
            resources = result.results["resource_usage"]
            report += f"**Resource Usage:**\n"
            report += f"- CPU: {resources['avg_cpu_percent']:.1f}%\n"
            report += f"- Memory: {resources['avg_memory_mb']:.1f}MB\n\n"
        
        return report
    
    def save_results(self):
        """Save results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        # Save JSON results
        json_file = results_dir / f"comparison_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "results": {name: {
                    "endpoint": result.endpoint,
                    "results": result.results
                } for name, result in self.results.items()}
            }, f, indent=2)
        
        # Save markdown report
        report_file = results_dir / f"comparison_report_{timestamp}.md"
        with open(report_file, 'w') as f:
            f.write(self.generate_report())
        
        print(f"Results saved to {json_file}")
        print(f"Report saved to {report_file}")

def main():
    """Main function"""
    print("=== Unified Benchmark Script ===")
    print("Testing all three systems with identical workloads")
    print("\nWARNING: All systems now running on Kubernetes for fair comparison!")
    print("   Custom system: Kubernetes deployment on port 8080 (no nginx rate limiting)")
    print("   KServe: Kubernetes InferenceService on port 8081")
    print("   TensorFlow Serving: Kubernetes with proxy on port 8082")
    
    systems = {
        "Custom": "http://localhost:8081",  # Kubernetes custom system (currently on 8081)
        "KServe": "http://localhost:8083",  # KServe InferenceService (will be on 8083)
        "TensorFlow Serving": "http://localhost:8082"
    }
    
    runner = BenchmarkRunner()
    
    # Test each system
    for system_name, endpoint in systems.items():
        print(f"\n{'='*50}")
        print(f"Testing {system_name}")
        print(f"{'='*50}")
        
        # Check if endpoint is accessible
        try:
            if system_name == "TensorFlow Serving":
                # Try MobileNetV3-Large first, fallback to half_plus_two
                try:
                    response = requests.get(f"{endpoint}/v1/models/mobilenet_v3_large", timeout=5)
                    if response.status_code == 200:
                        print("SUCCESS: MobileNetV3-Large model detected")
                    else:
                        print("WARNING: MobileNetV3-Large not found, will use half_plus_two model")
                except:
                    print("WARNING: MobileNetV3-Large not found, will use half_plus_two model")
            elif system_name == "KServe":
                # KServe uses /ping endpoint for health checks
                response = requests.get(f"{endpoint}/ping", timeout=5)
                if response.status_code != 200:
                    print(f"WARNING: {system_name} health check failed, continuing...")
            else:
                # Custom FastAPI system
                response = requests.get(f"{endpoint}/api/v1/health", timeout=5)
                if response.status_code != 200:
                    print(f"WARNING: {system_name} health check failed, continuing...")
        except:
            print(f"WARNING: {system_name} not accessible, skipping...")
            continue
        
        # Run benchmark
        success = runner.run_benchmark(system_name, endpoint)
        if not success:
            print(f"ERROR: Benchmark failed for {system_name}")
    
    # Save results
    runner.save_results()
    
    print(f"\nSUCCESS: Benchmark completed for {len(runner.results)} systems")

if __name__ == "__main__":
    main()