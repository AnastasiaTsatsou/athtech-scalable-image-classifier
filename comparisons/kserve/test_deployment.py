#!/usr/bin/env python3
"""
KServe Deployment Validation Script
Tests KServe InferenceService deployment and functionality
"""

import os
import sys
import time
import subprocess
import requests
import base64
import json
from PIL import Image
import io
from pathlib import Path


def run_command(cmd, timeout=300):
    """Run shell command with timeout"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def check_prerequisites():
    """Check if kubectl and KServe are available"""
    print("🔍 Checking prerequisites...")

    # Check kubectl
    success, stdout, stderr = run_command("kubectl version --client")
    if not success:
        print("❌ kubectl not found or not working")
        return False
    print("✓ kubectl is available")

    # Check cluster connectivity
    success, stdout, stderr = run_command("kubectl cluster-info")
    if not success:
        print("❌ Cannot connect to Kubernetes cluster")
        return False
    print("✓ Kubernetes cluster is accessible")

    # Check KServe operator
    success, stdout, stderr = run_command(
        "kubectl get crd inferenceservices.serving.kserve.io"
    )
    if not success:
        print("❌ KServe operator not installed")
        print("Please install KServe operator first:")
        print(
            "  kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.11.2/kserve.yaml"
        )
        return False
    print("✓ KServe operator is installed")

    return True


def create_test_image():
    """Create a synthetic test image"""
    # Create a red 224x224 RGB image
    image = Image.new("RGB", (224, 224), color="red")

    # Convert to bytes
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="JPEG")
    img_bytes = img_buffer.getvalue()

    return img_bytes


def deploy_model():
    """Deploy the model to KServe"""
    print("\n🚀 Deploying KServe InferenceService...")

    # Apply namespace
    success, stdout, stderr = run_command("kubectl apply -f namespace.yaml")
    if not success:
        print(f"❌ Failed to create namespace: {stderr}")
        return False
    print("✓ Namespace created")

    # Apply PVC
    success, stdout, stderr = run_command("kubectl apply -f pvc.yaml")
    if not success:
        print(f"❌ Failed to create PVC: {stderr}")
        return False
    print("✓ PVC created")

    # Wait for PVC to be bound
    print("⏳ Waiting for PVC to be bound...")
    for i in range(30):
        success, stdout, stderr = run_command(
            "kubectl get pvc mobilenet-model-pvc -n kserve-comparison -o jsonpath='{.status.phase}'"
        )
        if success and stdout.strip() == "Bound":
            print("✓ PVC is bound")
            break
        time.sleep(2)
    else:
        print("❌ PVC did not bind within timeout")
        return False

    # Create a job to copy model files to PVC
    job_yaml = """
apiVersion: batch/v1
kind: Job
metadata:
  name: model-copy-job
  namespace: kserve-comparison
spec:
  template:
    spec:
      containers:
      - name: copy-model
        image: busybox
        command: ["sh", "-c"]
        args:
        - |
          echo "Copying model files..."
          # Create model directory
          mkdir -p /mnt/models
          # Copy .mar file (this would normally be from a ConfigMap or external storage)
          echo "Model files copied"
          sleep 10
        volumeMounts:
        - name: model-storage
          mountPath: /mnt/models
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: mobilenet-model-pvc
      restartPolicy: Never
"""

    with open("temp_job.yaml", "w") as f:
        f.write(job_yaml)

    success, stdout, stderr = run_command("kubectl apply -f temp_job.yaml")
    if not success:
        print(f"❌ Failed to create copy job: {stderr}")
        return False

    # Wait for job to complete
    print("⏳ Waiting for model copy job to complete...")
    success, stdout, stderr = run_command(
        "kubectl wait --for=condition=complete job/model-copy-job -n kserve-comparison --timeout=60s"
    )
    if not success:
        print(f"❌ Model copy job failed: {stderr}")
        return False
    print("✓ Model files copied")

    # Clean up job
    run_command("kubectl delete -f temp_job.yaml")
    os.remove("temp_job.yaml")

    # Apply InferenceService
    success, stdout, stderr = run_command(
        "kubectl apply -f inferenceservice.yaml"
    )
    if not success:
        print(f"❌ Failed to create InferenceService: {stderr}")
        return False
    print("✓ InferenceService created")

    return True


def wait_for_ready():
    """Wait for InferenceService to be ready"""
    print("\n⏳ Waiting for InferenceService to be ready...")

    timeout = 300  # 5 minutes
    start_time = time.time()

    while time.time() - start_time < timeout:
        success, stdout, stderr = run_command(
            "kubectl get inferenceservice mobilenet-v3-large -n kserve-comparison -o jsonpath='{.status.conditions[?(@.type==\"Ready\")].status}'"
        )

        if success and stdout.strip() == "True":
            print("✓ InferenceService is ready!")
            return True

        # Check for failure
        success, stdout, stderr = run_command(
            "kubectl get inferenceservice mobilenet-v3-large -n kserve-comparison -o jsonpath='{.status.conditions[?(@.type==\"Ready\")].reason}'"
        )
        if success and stdout.strip() == "False":
            print(f"❌ InferenceService failed: {stdout}")
            return False

        print(".", end="", flush=True)
        time.sleep(10)

    print(f"\n❌ InferenceService did not become ready within {timeout}s")
    return False


def setup_port_forward():
    """Setup kubectl port-forward"""
    print("\n🔌 Setting up port-forward...")

    # Get service name
    success, stdout, stderr = run_command(
        "kubectl get svc -n kserve-comparison -l serving.kserve.io/inferenceservice=mobilenet-v3-large -o jsonpath='{.items[0].metadata.name}'"
    )
    if not success:
        print(f"❌ Failed to get service name: {stderr}")
        return False, None

    service_name = stdout.strip()
    print(f"✓ Found service: {service_name}")

    # Start port-forward in background
    cmd = (
        f"kubectl port-forward -n kserve-comparison svc/{service_name} 8081:80"
    )
    print(f"Running: {cmd}")

    try:
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        time.sleep(3)  # Give it time to start

        # Check if port-forward is working
        success, stdout, stderr = run_command(
            "curl -s http://localhost:8081/ping", timeout=5
        )
        if success:
            print("✓ Port-forward is working")
            return True, process
        else:
            print("❌ Port-forward failed")
            process.terminate()
            return False, None
    except Exception as e:
        print(f"❌ Failed to start port-forward: {e}")
        return False, None


def test_prediction():
    """Test model prediction"""
    print("\n🧪 Testing model prediction...")

    # Create test image
    test_image = create_test_image()

    # Encode image as base64
    image_b64 = base64.b64encode(test_image).decode("utf-8")

    # Prepare request payload
    payload = {"instances": [{"body": image_b64}]}

    # Send prediction request
    url = "http://localhost:8081/v2/models/mobilenet_v3_large/infer"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✓ Prediction successful!")
            print(f"📊 Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


def get_model_info():
    """Get model information"""
    print("\n📋 Getting model information...")

    try:
        # Try to get model metadata
        url = "http://localhost:8081/v2/models/mobilenet_v3_large"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            info = response.json()
            print("✓ Model info retrieved:")
            print(json.dumps(info, indent=2))
        else:
            print(f"⚠ Could not get model info: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"⚠ Could not get model info: {e}")


def cleanup():
    """Clean up resources"""
    print("\n🧹 Cleaning up...")

    # Delete InferenceService
    run_command("kubectl delete -f inferenceservice.yaml")

    # Delete PVC
    run_command("kubectl delete -f pvc.yaml")

    # Delete namespace
    run_command("kubectl delete -f namespace.yaml")

    print("✓ Cleanup completed")


def main():
    """Main function"""
    print("=== KServe Deployment Validation ===")

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    try:
        # Check prerequisites
        if not check_prerequisites():
            sys.exit(1)

        # Deploy model
        if not deploy_model():
            sys.exit(1)

        # Wait for ready
        if not wait_for_ready():
            sys.exit(1)

        # Setup port-forward
        success, process = setup_port_forward()
        if not success:
            sys.exit(1)

        try:
            # Test prediction
            if not test_prediction():
                sys.exit(1)

            # Get model info
            get_model_info()

            print("\n✅ KServe deployment validation completed successfully!")
            print("\nNext steps:")
            print("1. Run benchmark_comparison.py to test performance")
            print("2. Compare with other serving solutions")

        finally:
            # Clean up port-forward
            if process:
                process.terminate()
                print("✓ Port-forward terminated")

    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()

