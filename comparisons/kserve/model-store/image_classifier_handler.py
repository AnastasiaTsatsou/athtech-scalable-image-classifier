
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
