#!/usr/bin/env python3
"""
Simplified KServe Model Converter
Creates a basic model setup for KServe without complex TorchServe conversion
"""

import os
import sys
import torch
import torchvision
from torchvision import models, transforms
from PIL import Image
import json
from pathlib import Path


def export_pytorch_model():
    """Export PyTorch MobileNetV3-Large model to TorchScript"""
    print("Loading MobileNetV3-Large model...")

    # Load pretrained model
    model = models.mobilenet_v3_large(
        weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V1
    )
    model.eval()

    # Apply optimizations
    print("Applying optimizations...")

    # Dynamic quantization
    try:
        model = torch.quantization.quantize_dynamic(
            model, {torch.nn.Linear, torch.nn.Conv2d}, dtype=torch.qint8
        )
        print("SUCCESS: Applied dynamic quantization")
    except Exception as e:
        print(f"WARNING: Quantization failed: {e}")

    # Convert to TorchScript
    try:
        model = torch.jit.freeze(torch.jit.script(model))
        print("SUCCESS: Applied TorchScript optimization")
    except Exception as e:
        print(f"WARNING: TorchScript failed: {e}")
        # Fallback to traced model
        dummy_input = torch.randn(1, 3, 224, 224)
        model = torch.jit.trace(model, dummy_input)
        model = torch.jit.freeze(model)
        print("SUCCESS: Applied TorchScript tracing")

    return model


def download_imagenet_classes():
    """Download ImageNet class names"""
    import requests

    url = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
    try:
        response = requests.get(url)
        return response.text.strip().split("\n")
    except:
        # Fallback to local file if available
        local_file = (
            Path(__file__).parent.parent.parent
            / "app"
            / "models"
            / "imagenet_classes.txt"
        )
        if local_file.exists():
            with open(local_file, "r") as f:
                return [line.strip() for line in f.readlines()]
        else:
            return [f"class_{i}" for i in range(1000)]


def create_simple_model_setup():
    """Create a simple model setup for KServe"""
    print("Creating simple model setup...")

    # Create model store directory
    model_store_dir = Path("model-store")
    model_store_dir.mkdir(exist_ok=True)

    # Export PyTorch model
    model = export_pytorch_model()

    # Save model
    model_path = model_store_dir / "model.pt"
    torch.jit.save(model, model_path)
    print(f"SUCCESS: Model saved to {model_path}")

    # Save class names
    class_names = download_imagenet_classes()
    classes_path = model_store_dir / "imagenet_classes.txt"
    with open(classes_path, "w") as f:
        f.write("\n".join(class_names))
    print(f"SUCCESS: Class names saved to {classes_path}")

    # Create a simple handler
    handler_code = '''
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import json
import logging
import io
import base64

logger = logging.getLogger(__name__)

class ImageClassifierHandler:
    """Simple handler for image classification"""
    
    def __init__(self):
        self.model = None
        self.transform = None
        self.class_names = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    def initialize(self, context):
        """Initialize model and transforms"""
        properties = context.system_properties
        model_dir = properties.get("model_dir")
        
        # Load model
        self.model = torch.jit.load(f"{model_dir}/model.pt", map_location=self.device)
        self.model.eval()
        
        # Setup transforms
        self.transform = transforms.Compose([
            transforms.Resize(256, interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Load class names
        try:
            with open(f"{model_dir}/imagenet_classes.txt", 'r') as f:
                self.class_names = [line.strip() for line in f.readlines()]
        except:
            self.class_names = [f"class_{i}" for i in range(1000)]
            
        logger.info(f"Model loaded on {self.device}")
        
    def preprocess(self, data):
        """Preprocess input data"""
        images = []
        
        for row in data:
            # Handle different input formats
            if isinstance(row, dict):
                if "body" in row:
                    # Base64 encoded image
                    image_data = base64.b64decode(row["body"])
                elif "data" in row:
                    image_data = row["data"]
                else:
                    raise ValueError("Invalid input format")
            else:
                image_data = row
                
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_data))
            if image.mode != "RGB":
                image = image.convert("RGB")
                
            # Apply transforms
            tensor = self.transform(image)
            images.append(tensor)
            
        return torch.stack(images)
        
    def inference(self, data, *args, **kwargs):
        """Run inference"""
        with torch.no_grad():
            outputs = self.model(data)
            probabilities = F.softmax(outputs, dim=1)
        return probabilities
        
    def postprocess(self, data):
        """Postprocess predictions"""
        results = []
        
        for probs in data:
            # Get top-5 predictions
            top_probs, top_indices = torch.topk(probs, 5)
            
            predictions = []
            for prob, idx in zip(top_probs, top_indices):
                predictions.append({
                    "class_name": self.class_names[idx.item()],
                    "probability": prob.item(),
                    "class_id": idx.item()
                })
                
            results.append({
                "predictions": predictions,
                "model_info": {
                    "model_name": "mobilenet_v3_large",
                    "framework": "PyTorch",
                    "device": str(self.device)
                }
            })
            
        return results
'''

    handler_path = model_store_dir / "image_classifier_handler.py"
    with open(handler_path, "w") as f:
        f.write(handler_code)
    print(f"SUCCESS: Handler created at {handler_path}")

    # Create requirements.txt
    requirements = [
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "pillow>=9.0.0",
        "numpy>=1.21.0",
    ]

    req_path = model_store_dir / "requirements.txt"
    with open(req_path, "w") as f:
        f.write("\n".join(requirements))
    print(f"SUCCESS: Requirements saved to {req_path}")

    print(f"\nSUCCESS! Simple model setup created in {model_store_dir}")
    print(
        "Note: This is a simplified setup. For production, use proper TorchServe .mar files."
    )

    return model_store_dir


def main():
    """Main function"""
    print("=== Simplified KServe Model Converter ===")
    print("Creating basic model setup for KServe")

    # Change to comparisons/kserve directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    try:
        # Create simple model setup
        model_store_dir = create_simple_model_setup()

        print(f"\nSUCCESS! Model setup created in {model_store_dir}")
        print("\nNext steps:")
        print("1. Deploy KServe InferenceService using the generated files")
        print("2. Run test_deployment.py to validate the deployment")

    except Exception as e:
        print(f"\nERROR: Failed to create model setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
