#!/usr/bin/env python3
"""
End-to-End Comparison Orchestration Script
Master script that orchestrates the complete comparison process
"""

import os
import sys
import time
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime
import requests

class ComparisonOrchestrator:
    """Orchestrates the complete comparison process"""
    
    def __init__(self, cleanup: bool = False, skip_kserve: bool = False, skip_tfserving: bool = False):
        self.cleanup = cleanup
        self.skip_kserve = skip_kserve
        self.skip_tfserving = skip_tfserving
        self.start_time = datetime.now()
        self.results = {
            "start_time": self.start_time.isoformat(),
            "deployment_times": {},
            "benchmark_results": {},
            "errors": []
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, cmd: str, timeout: int = 300, cwd: str = None) -> tuple[bool, str, str]:
        """Run shell command with timeout"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)
    
    def check_prerequisites(self) -> bool:
        """Check prerequisites and cluster access"""
        self.log("🔍 Checking prerequisites...")
        
        # Check kubectl
        success, stdout, stderr = self.run_command("kubectl version --client")
        if not success:
            self.log("❌ kubectl not found or not working", "ERROR")
            return False
        self.log("✓ kubectl is available")
        
        # Check cluster connectivity
        success, stdout, stderr = self.run_command("kubectl cluster-info")
        if not success:
            self.log("❌ Cannot connect to Kubernetes cluster", "ERROR")
            return False
        self.log("✓ Kubernetes cluster is accessible")
        
        # Check KServe operator
        success, stdout, stderr = self.run_command("kubectl get crd inferenceservices.serving.kserve.io")
        if not success:
            self.log("❌ KServe operator not installed", "ERROR")
            self.log("Please install KServe operator first:", "ERROR")
            self.log("  kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.11.2/kserve.yaml", "ERROR")
            return False
        self.log("✓ KServe operator is installed")
        
        # Check existing custom deployment
        success, stdout, stderr = self.run_command("kubectl get deployment image-classifier -n image-classifier")
        if not success:
            self.log("⚠ Custom deployment not found, will skip custom system benchmark", "WARNING")
        else:
            self.log("✓ Custom deployment found")
        
        return True
    
    def deploy_kserve(self) -> bool:
        """Deploy KServe with MobileNetV3-Large"""
        self.log("🚀 Deploying KServe...")
        
        start_time = time.time()
        
        try:
            # Change to KServe directory
            kserve_dir = Path("kserve")
            if not kserve_dir.exists():
                self.log("❌ KServe directory not found", "ERROR")
                return False
            
            # Convert model
            self.log("📦 Converting PyTorch model to TorchServe format...")
            success, stdout, stderr = self.run_command("python model_converter.py", cwd=kserve_dir)
            if not success:
                self.log(f"❌ Model conversion failed: {stderr}", "ERROR")
                return False
            self.log("✓ Model converted successfully")
            
            # Deploy KServe
            self.log("🚀 Deploying KServe InferenceService...")
            success, stdout, stderr = self.run_command("kubectl apply -f namespace.yaml", cwd=kserve_dir)
            if not success:
                self.log(f"❌ Failed to create namespace: {stderr}", "ERROR")
                return False
            
            success, stdout, stderr = self.run_command("kubectl apply -f pvc.yaml", cwd=kserve_dir)
            if not success:
                self.log(f"❌ Failed to create PVC: {stderr}", "ERROR")
                return False
            
            success, stdout, stderr = self.run_command("kubectl apply -f inferenceservice.yaml", cwd=kserve_dir)
            if not success:
                self.log(f"❌ Failed to create InferenceService: {stderr}", "ERROR")
                return False
            
            # Wait for deployment
            self.log("⏳ Waiting for KServe to be ready...")
            success, stdout, stderr = self.run_command("kubectl wait --for=condition=ready inferenceservice/mobilenet-v3-large -n kserve-comparison --timeout=300s")
            if not success:
                self.log(f"❌ KServe deployment timeout: {stderr}", "ERROR")
                return False
            
            deployment_time = time.time() - start_time
            self.results["deployment_times"]["kserve"] = deployment_time
            self.log(f"✓ KServe deployed successfully in {deployment_time:.1f}s")
            
            return True
            
        except Exception as e:
            self.log(f"❌ KServe deployment failed: {e}", "ERROR")
            self.results["errors"].append(f"KServe deployment: {e}")
            return False
    
    def deploy_tensorflow_serving(self) -> bool:
        """Deploy TensorFlow Serving with MobileNetV3-Large"""
        self.log("🚀 Deploying TensorFlow Serving...")
        
        start_time = time.time()
        
        try:
            # Change to TensorFlow Serving directory
            tf_dir = Path("tensorflow-serving")
            if not tf_dir.exists():
                self.log("❌ TensorFlow Serving directory not found", "ERROR")
                return False
            
            # Export model
            self.log("📦 Exporting TensorFlow model to SavedModel format...")
            success, stdout, stderr = self.run_command("python export_model.py", cwd=tf_dir)
            
            # Check if model files were created (more reliable than exit code)
            model_path = tf_dir / "models" / "mobilenet-v3-large" / "1"
            if not model_path.exists() or not (model_path / "saved_model.pb").exists():
                self.log(f"❌ Model export failed: {stderr}", "ERROR")
                return False
            self.log("✓ Model exported successfully")
            
            # Deploy TensorFlow Serving
            self.log("🚀 Deploying TensorFlow Serving...")
            success, stdout, stderr = self.run_command("kubectl apply -f namespace.yaml", cwd=tf_dir)
            if not success:
                self.log(f"❌ Failed to create namespace: {stderr}", "ERROR")
                return False
            
            success, stdout, stderr = self.run_command("kubectl apply -f pvc.yaml", cwd=tf_dir)
            if not success:
                self.log(f"❌ Failed to create PVC: {stderr}", "ERROR")
                return False
            
            success, stdout, stderr = self.run_command("kubectl apply -f configmap.yaml", cwd=tf_dir)
            if not success:
                self.log(f"❌ Failed to create ConfigMap: {stderr}", "ERROR")
                return False
            
            success, stdout, stderr = self.run_command("kubectl apply -f deployment-simple.yaml", cwd=tf_dir)
            if not success:
                self.log(f"❌ Failed to create deployment: {stderr}", "ERROR")
                return False
            
            success, stdout, stderr = self.run_command("kubectl apply -f service.yaml", cwd=tf_dir)
            if not success:
                self.log(f"❌ Failed to create service: {stderr}", "ERROR")
                return False
            
            # Wait for deployment
            self.log("⏳ Waiting for TensorFlow Serving to be ready...")
            success, stdout, stderr = self.run_command("kubectl wait --for=condition=ready pod -l app=tensorflow-serving -n tfserving-comparison --timeout=300s")
            if not success:
                self.log(f"❌ TensorFlow Serving deployment timeout: {stderr}", "ERROR")
                return False
            
            deployment_time = time.time() - start_time
            self.results["deployment_times"]["tensorflow_serving"] = deployment_time
            self.log(f"✓ TensorFlow Serving deployed successfully in {deployment_time:.1f}s")
            
            return True
            
        except Exception as e:
            self.log(f"❌ TensorFlow Serving deployment failed: {e}", "ERROR")
            self.results["errors"].append(f"TensorFlow Serving deployment: {e}")
            return False
    
    def setup_port_forwards(self) -> bool:
        """Setup port-forwards for all systems"""
        self.log("🔌 Setting up port-forwards...")
        
        try:
            # Setup KServe port-forward
            self.log("Setting up KServe port-forward (8081)...")
            success, stdout, stderr = self.run_command("kubectl port-forward -n kserve-comparison svc/mobilenet-v3-large-predictor-default 8081:80 &")
            if not success:
                self.log(f"❌ KServe port-forward failed: {stderr}", "ERROR")
                return False
            
            # Setup TensorFlow Serving port-forward
            self.log("Setting up TensorFlow Serving port-forward (8082)...")
            success, stdout, stderr = self.run_command("kubectl port-forward -n tfserving-comparison svc/tensorflow-serving-service 8082:8501 &")
            if not success:
                self.log(f"❌ TensorFlow Serving port-forward failed: {stderr}", "ERROR")
                return False
            
            # Wait for port-forwards to be ready
            time.sleep(5)
            
            # Test port-forwards
            self.log("Testing port-forwards...")
            
            # Test KServe
            try:
                response = requests.get("http://localhost:8081/ping", timeout=5)
                if response.status_code == 200:
                    self.log("✓ KServe port-forward working")
                else:
                    self.log("⚠ KServe port-forward not responding", "WARNING")
            except:
                self.log("⚠ KServe port-forward not accessible", "WARNING")
            
            # Test TensorFlow Serving
            try:
                response = requests.get("http://localhost:8082/v1/models", timeout=5)
                if response.status_code == 200:
                    self.log("✓ TensorFlow Serving port-forward working")
                else:
                    self.log("⚠ TensorFlow Serving port-forward not responding", "WARNING")
            except:
                self.log("⚠ TensorFlow Serving port-forward not accessible", "WARNING")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Port-forward setup failed: {e}", "ERROR")
            self.results["errors"].append(f"Port-forward setup: {e}")
            return False
    
    def run_benchmarks(self) -> bool:
        """Run benchmarks for all systems"""
        self.log("📊 Running benchmarks...")
        
        try:
            # Run unified benchmark script
            success, stdout, stderr = self.run_command("python benchmark_comparison.py", timeout=600)
            if not success:
                self.log(f"❌ Benchmark failed: {stderr}", "ERROR")
                return False
            
            self.log("✓ Benchmarks completed successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Benchmark execution failed: {e}", "ERROR")
            self.results["errors"].append(f"Benchmark execution: {e}")
            return False
    
    def generate_final_report(self):
        """Generate final comparison report"""
        self.log("📋 Generating final report...")
        
        try:
            # Create results directory
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            
            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save orchestration results
            orchestration_file = results_dir / f"orchestration_results_{timestamp}.json"
            with open(orchestration_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            self.log(f"✓ Orchestration results saved to {orchestration_file}")
            
            # Generate summary report
            summary_file = results_dir / f"comparison_summary_{timestamp}.md"
            with open(summary_file, 'w') as f:
                f.write(f"# Model Serving Comparison Summary\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("## Deployment Times\n\n")
                f.write("| System | Deployment Time |\n")
                f.write("|--------|----------------|\n")
                
                for system, time_taken in self.results["deployment_times"].items():
                    f.write(f"| {system.replace('_', ' ').title()} | {time_taken:.1f}s |\n")
                
                f.write("\n## Errors\n\n")
                if self.results["errors"]:
                    for error in self.results["errors"]:
                        f.write(f"- {error}\n")
                else:
                    f.write("No errors encountered.\n")
                
                f.write("\n## Next Steps\n\n")
                f.write("1. Review benchmark results in `comparison_results_*.json`\n")
                f.write("2. Check comparison report in `comparison_report_*.md`\n")
                f.write("3. Analyze deployment complexity in `deployment_analysis.md`\n")
            
            self.log(f"✓ Summary report saved to {summary_file}")
            
        except Exception as e:
            self.log(f"❌ Report generation failed: {e}", "ERROR")
    
    def cleanup_deployments(self):
        """Clean up all deployments"""
        if not self.cleanup:
            return
        
        self.log("🧹 Cleaning up deployments...")
        
        try:
            # Clean up KServe
            self.log("Cleaning up KServe...")
            self.run_command("kubectl delete -f kserve/inferenceservice.yaml")
            self.run_command("kubectl delete -f kserve/pvc.yaml")
            self.run_command("kubectl delete -f kserve/namespace.yaml")
            
            # Clean up TensorFlow Serving
            self.log("Cleaning up TensorFlow Serving...")
            self.run_command("kubectl delete -f tensorflow-serving/deployment.yaml")
            self.run_command("kubectl delete -f tensorflow-serving/service.yaml")
            self.run_command("kubectl delete -f tensorflow-serving/configmap.yaml")
            self.run_command("kubectl delete -f tensorflow-serving/pvc.yaml")
            self.run_command("kubectl delete -f tensorflow-serving/namespace.yaml")
            
            # Kill port-forwards
            self.log("Terminating port-forwards...")
            self.run_command("pkill -f 'kubectl port-forward'")
            
            self.log("✓ Cleanup completed")
            
        except Exception as e:
            self.log(f"⚠ Cleanup failed: {e}", "WARNING")
    
    def run(self):
        """Run the complete comparison process"""
        self.log("🚀 Starting Model Serving Comparison")
        self.log(f"Cleanup enabled: {self.cleanup}")
        
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                self.log("❌ Prerequisites check failed", "ERROR")
                return False
            
            # Deploy KServe
            if not self.skip_kserve:
                if not self.deploy_kserve():
                    self.log("❌ KServe deployment failed", "ERROR")
                    return False
            else:
                self.log("⏭ Skipping KServe deployment")
            
            # Deploy TensorFlow Serving
            if not self.skip_tfserving:
                if not self.deploy_tensorflow_serving():
                    self.log("❌ TensorFlow Serving deployment failed", "ERROR")
                    return False
            else:
                self.log("⏭ Skipping TensorFlow Serving deployment")
            
            # Setup port-forwards
            if not self.setup_port_forwards():
                self.log("❌ Port-forward setup failed", "ERROR")
                return False
            
            # Run benchmarks
            if not self.run_benchmarks():
                self.log("❌ Benchmark execution failed", "ERROR")
                return False
            
            # Generate final report
            self.generate_final_report()
            
            # Cleanup if requested
            self.cleanup_deployments()
            
            # Calculate total time
            total_time = (datetime.now() - self.start_time).total_seconds()
            self.log(f"✅ Comparison completed successfully in {total_time:.1f}s")
            
            return True
            
        except KeyboardInterrupt:
            self.log("⚠ Interrupted by user", "WARNING")
            self.cleanup_deployments()
            return False
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", "ERROR")
            self.cleanup_deployments()
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run complete model serving comparison")
    parser.add_argument("--cleanup", action="store_true", help="Clean up deployments after completion")
    parser.add_argument("--skip-kserve", action="store_true", help="Skip KServe deployment")
    parser.add_argument("--skip-tfserving", action="store_true", help="Skip TensorFlow Serving deployment")
    
    args = parser.parse_args()
    
    print("=== Model Serving Comparison Orchestrator ===")
    print("This script will deploy and benchmark KServe and TensorFlow Serving")
    print("against your existing custom FastAPI system.")
    
    # Change to comparisons directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Create orchestrator
    orchestrator = ComparisonOrchestrator(
        cleanup=args.cleanup,
        skip_kserve=args.skip_kserve,
        skip_tfserving=args.skip_tfserving
    )
    
    # Run comparison
    success = orchestrator.run()
    
    if success:
        print("\n🎉 Comparison completed successfully!")
        print("Check the 'results' directory for detailed reports.")
        sys.exit(0)
    else:
        print("\n❌ Comparison failed!")
        print("Check the logs above for error details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
