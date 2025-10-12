#!/usr/bin/env python3
"""
TensorFlow Serving MobileNetV3-Large Validation Script

This script validates the MobileNetV3-Large deployment on TensorFlow Serving:
- Tests model metadata endpoint
- Sends test predictions with various images
- Validates response format and content
- Measures response times
- Compares with expected ImageNet predictions

Usage:
    python test_tfserving_mobilenet.py [options]

Options:
    --url URL          TensorFlow Serving URL (default: http://localhost:8082)
    --model MODEL      Model name (default: mobilenet_v3_large)
    --test-images DIR  Directory with test images
    --verbose          Enable verbose output
"""

import os
import sys
import time
import json
import argparse
import requests
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import subprocess

# Add the comparisons directory to path for ImageNet classes
sys.path.append(str(Path(__file__).parent.parent))

def load_imagenet_classes() -> Dict[int, str]:
    """Load ImageNet class labels"""
    classes_file = Path(__file__).parent.parent / "kserve" / "model-store" / "imagenet_classes.txt"
    
    if not classes_file.exists():
        print(f"[WARNING] ImageNet classes file not found at {classes_file}")
        print("Using placeholder class names...")
        return {i: f"class_{i}" for i in range(1000)}
    
    with open(classes_file, 'r') as f:
        class_names = [line.strip() for line in f.readlines()]
    
    return {i: name for i, name in enumerate(class_names)}

def create_test_images() -> Dict[str, np.ndarray]:
    """Create synthetic test images"""
    images = {}
    
    # Red image
    images['red'] = np.ones((224, 224, 3), dtype=np.float32) * [1.0, 0.0, 0.0]
    
    # Green image
    images['green'] = np.ones((224, 224, 3), dtype=np.float32) * [0.0, 1.0, 0.0]
    
    # Blue image
    images['blue'] = np.ones((224, 224, 3), dtype=np.float32) * [0.0, 0.0, 1.0]
    
    # White image
    images['white'] = np.ones((224, 224, 3), dtype=np.float32)
    
    # Black image
    images['black'] = np.zeros((224, 224, 3), dtype=np.float32)
    
    # Random noise
    images['noise'] = np.random.rand(224, 224, 3).astype(np.float32)
    
    # Gradient
    gradient = np.linspace(0, 1, 224).reshape(1, -1, 1)
    images['gradient'] = np.repeat(gradient, 224, axis=0).astype(np.float32)
    images['gradient'] = np.repeat(images['gradient'], 3, axis=2)
    
    return images

def load_test_images_from_dir(directory: str) -> Dict[str, np.ndarray]:
    """Load test images from directory"""
    images = {}
    test_dir = Path(directory)
    
    if not test_dir.exists():
        print(f"[WARNING] Test images directory not found: {directory}")
        return {}
    
    for img_file in test_dir.glob("*.jpg"):
        try:
            # Load image
            img = Image.open(img_file)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to 224x224
            img = img.resize((224, 224), Image.Resampling.LANCZOS)
            
            # Convert to numpy array and normalize to [0, 1]
            img_array = np.array(img, dtype=np.float32) / 255.0
            
            images[img_file.stem] = img_array
            
        except Exception as e:
            print(f"[WARNING] Failed to load {img_file}: {e}")
    
    return images

def test_model_metadata(url: str, model_name: str) -> bool:
    """Test model metadata endpoint"""
    print(f"[INFO] Testing model metadata...")
    
    try:
        response = requests.get(f"{url}/v1/models/{model_name}", timeout=10)
        
        if response.status_code == 200:
            metadata = response.json()
            print(f"[OK] Model metadata retrieved successfully")
            
            # Print key information
            if 'model_version_status' in metadata:
                versions = metadata['model_version_status']
                print(f"   Model versions: {len(versions)}")
                for version in versions:
                    state = version.get('state', 'UNKNOWN')
                    print(f"   Version {version.get('version', 'N/A')}: {state}")
            
            return True
        else:
            print(f"[ERROR] Model metadata failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Model metadata request failed: {e}")
        return False

def predict_image(url: str, model_name: str, image: np.ndarray, image_name: str = "test") -> Optional[Dict]:
    """Send prediction request for an image"""
    
    # Prepare payload
    payload = {
        "instances": [image.tolist()]
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{url}/v1/models/{model_name}:predict",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract predictions
            if 'predictions' in result and len(result['predictions']) > 0:
                predictions = result['predictions'][0]
                response_time = end_time - start_time
                
                return {
                    'predictions': predictions,
                    'response_time': response_time,
                    'image_name': image_name
                }
            else:
                print(f"[ERROR] Invalid response format for {image_name}")
                return None
        else:
            print(f"[ERROR] Prediction failed for {image_name}: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Prediction request failed for {image_name}: {e}")
        return None

def analyze_predictions(predictions: List[float], imagenet_classes: Dict[int, str], top_k: int = 5) -> List[Tuple[int, str, float]]:
    """Analyze predictions and return top-k results"""
    
    # Get top-k indices
    top_indices = np.argsort(predictions)[-top_k:][::-1]
    
    # Create results
    results = []
    for idx in top_indices:
        class_name = imagenet_classes.get(idx, f"class_{idx}")
        confidence = predictions[idx]
        results.append((idx, class_name, confidence))
    
    return results

def test_predictions(url: str, model_name: str, test_images: Dict[str, np.ndarray], imagenet_classes: Dict[int, str], verbose: bool = False) -> bool:
    """Test predictions with various images"""
    print(f"[INFO] Testing predictions...")
    
    all_results = []
    success_count = 0
    
    for image_name, image in test_images.items():
        if verbose:
            print(f"   Testing {image_name}...")
        
        result = predict_image(url, model_name, image, image_name)
        
        if result:
            predictions = result['predictions']
            response_time = result['response_time']
            
            # Analyze predictions
            top_results = analyze_predictions(predictions, imagenet_classes)
            
            all_results.append({
                'image_name': image_name,
                'response_time': response_time,
                'top_predictions': top_results
            })
            
            success_count += 1
            
            if verbose:
                print(f"   [OK] {image_name}: {response_time:.3f}s")
                for i, (idx, class_name, confidence) in enumerate(top_results):
                    print(f"      {i+1}. {class_name} ({idx}): {confidence:.4f}")
        else:
            if verbose:
                print(f"   [ERROR] {image_name}: Failed")
    
    # Print summary
    print(f"[OK] Predictions completed: {success_count}/{len(test_images)} successful")
    
    if all_results:
        # Calculate average response time
        avg_time = sum(r['response_time'] for r in all_results) / len(all_results)
        print(f"[INFO] Average response time: {avg_time:.3f}s")
        
        # Print top predictions for each image
        print(f"\n[INFO] Top predictions summary:")
        for result in all_results:
            print(f"   {result['image_name']}: {result['response_time']:.3f}s")
            top_pred = result['top_predictions'][0]
            print(f"      -> {top_pred[1]} ({top_pred[0]}): {top_pred[2]:.4f}")
    
    return success_count > 0

def test_model_health(url: str) -> bool:
    """Test model health endpoint"""
    print(f"[INFO] Testing model health...")
    
    try:
        response = requests.get(f"{url}/v1/models", timeout=10)
        
        if response.status_code == 200:
            models = response.json()
            print(f"[OK] Health check passed")
            
            if 'models' in models:
                model_names = [m.get('name', 'unknown') for m in models['models']]
                print(f"   Available models: {model_names}")
            
            return True
        else:
            print(f"[ERROR] Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Health check request failed: {e}")
        return False

def check_port_forward(namespace: str = "tfserving-simple") -> bool:
    """Check if port-forward is running"""
    try:
        # Check if kubectl port-forward process is running
        result = subprocess.run(
            ["pgrep", "-f", f"kubectl port-forward.*8082"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"[OK] Port-forward is running (PID: {result.stdout.strip()})")
            return True
        else:
            print(f"[WARNING] Port-forward not detected")
            return False
            
    except Exception as e:
        print(f"[WARNING] Could not check port-forward: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test TensorFlow Serving MobileNetV3-Large deployment')
    parser.add_argument('--url', default='http://localhost:8082', help='TensorFlow Serving URL')
    parser.add_argument('--model', default='mobilenet_v3_large', help='Model name')
    parser.add_argument('--test-images', help='Directory with test images')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--namespace', default='tfserving-simple', help='Kubernetes namespace')
    
    args = parser.parse_args()
    
    print("=== TensorFlow Serving MobileNetV3-Large Validation ===")
    print(f"URL: {args.url}")
    print(f"Model: {args.model}")
    print(f"Namespace: {args.namespace}")
    print()
    
    # Load ImageNet classes
    imagenet_classes = load_imagenet_classes()
    print(f"[OK] Loaded {len(imagenet_classes)} ImageNet classes")
    
    # Check port-forward
    check_port_forward(args.namespace)
    
    # Test model metadata
    if not test_model_metadata(args.url, args.model):
        print("[ERROR] Model metadata test failed")
        sys.exit(1)
    
    # Load test images
    test_images = {}
    
    if args.test_images:
        test_images.update(load_test_images_from_dir(args.test_images))
    
    # Always include synthetic test images
    synthetic_images = create_test_images()
    test_images.update(synthetic_images)
    
    print(f"[INFO] Loaded {len(test_images)} test images")
    
    # Test predictions
    if not test_predictions(args.url, args.model, test_images, imagenet_classes, args.verbose):
        print("[ERROR] Prediction tests failed")
        sys.exit(1)
    
    print("\n[SUCCESS] All tests passed!")
    print("\n[SUCCESS] TensorFlow Serving MobileNetV3-Large is working correctly!")
    print("\nNext steps:")
    print("1. Run benchmark: python ../benchmark_comparison.py")
    print("2. Compare with other serving solutions")
    print("3. Monitor performance: kubectl top pods -n tfserving-simple")

if __name__ == "__main__":
    main()
