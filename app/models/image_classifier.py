"""
Image Classification Model Implementation
Uses pretrained ResNet model for image classification
"""

import torch
# CPU threading optimization (must be before any model operations)
torch.set_num_threads(4)
torch.set_flush_denormal(True)

import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
from typing import List, Dict
import time

from app.logging.config import get_logger, log_classification, log_error

logger = get_logger(__name__)


class ImageClassifier:
    """
    Image classifier using pretrained ResNet model
    """

    def __init__(self, model_name: str = "resnet50", device: str = "cpu"):
        """
        Initialize the image classifier

        Args:
            model_name: Name of the pretrained model to use
            device: Device to run the model on ('cpu' or 'cuda')
        """
        self.device = torch.device(
            device if torch.cuda.is_available() else "cpu"
        )
        self.model_name = model_name
        self.model = None
        self.transform = None
        self.class_names = None
        
        # Track optimization status
        self.is_quantized = False
        self.is_torchscript = False
        self.model_parameters = 0
        self.model_size_mb = 0.0

        # Set inference mode optimizations
        torch.set_grad_enabled(False)

        start_time = time.time()
        self._load_model()
        self._setup_transforms()
        self._load_class_names()

        # Record model loading time
        load_time = time.time() - start_time
        try:
            from app.monitoring.metrics import metrics_collector

            metrics_collector.record_model_load_time(load_time)
            metrics_collector.record_model_info(
                model_name=self.model_name,
                device=str(self.device),
                num_classes=(
                    len(self.class_names)  # type: ignore
                    if self.class_names is not None
                    else 1000
                ),
                framework="PyTorch",
            )
        except ImportError:
            # Metrics not available, continue without recording
            pass

    def _load_model(self):
        """Load the pretrained model"""
        try:
            if self.model_name == "resnet50":
                self.model = models.resnet50(
                    weights=models.ResNet50_Weights.IMAGENET1K_V1
                )
            elif self.model_name == "resnet101":
                self.model = models.resnet101(
                    weights=models.ResNet101_Weights.IMAGENET1K_V1
                )
            elif self.model_name == "resnet152":
                self.model = models.resnet152(
                    weights=models.ResNet152_Weights.IMAGENET1K_V1
                )
            elif self.model_name == "efficientnet_b0":
                self.model = models.efficientnet_b0(
                    weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1
                )
            elif self.model_name == "efficientnet_b1":
                self.model = models.efficientnet_b1(
                    weights=models.EfficientNet_B1_Weights.IMAGENET1K_V1
                )
            elif self.model_name == "efficientnet_b2":
                self.model = models.efficientnet_b2(
                    weights=models.EfficientNet_B2_Weights.IMAGENET1K_V1
                )
            elif self.model_name == "mobilenet_v3_small":
                self.model = models.mobilenet_v3_small(
                    weights=models.MobileNet_V3_Small_Weights.IMAGENET1K_V1
                )
            elif self.model_name == "mobilenet_v3_large":
                self.model = models.mobilenet_v3_large(
                    weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V1
                )
            else:
                raise ValueError(f"Unsupported model: {self.model_name}")

            self.model.eval()
            self.model.to(self.device)
            
            # Apply dynamic quantization for CPU optimization (INT8)
            try:
                self.model = torch.quantization.quantize_dynamic(
                    self.model,
                    {torch.nn.Linear, torch.nn.Conv2d},  # Quantize these layers
                    dtype=torch.qint8
                )
                self.is_quantized = True
                logger.info(f"Applied dynamic quantization to {self.model_name}")
            except Exception as e:
                logger.warning(f"Quantization failed, using regular model: {e}")
            
            # Calculate model parameters and size BEFORE TorchScript
            self.model_parameters = sum(p.numel() for p in self.model.parameters())
            
            # Estimate model size in MB (rough approximation)
            param_size = sum(p.numel() * p.element_size() for p in self.model.parameters())
            buffer_size = sum(b.numel() * b.element_size() for b in self.model.buffers())
            self.model_size_mb = (param_size + buffer_size) / (1024 * 1024)
            
            # Apply TorchScript optimization for faster inference
            try:
                self.model = torch.jit.freeze(torch.jit.script(self.model))
                self.is_torchscript = True
                logger.info(f"Applied TorchScript optimization to {self.model_name}")
            except Exception as e:
                logger.warning(f"TorchScript optimization failed, using regular model: {e}")
            
            logger.info(f"Loaded {self.model_name} model on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _setup_transforms(self):
        """Setup image preprocessing transforms"""
        self.transform = transforms.Compose(
            [
                transforms.Resize(256, interpolation=transforms.InterpolationMode.BILINEAR),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

    def _load_class_names(self):
        """Load ImageNet class names from cached file"""
        try:
            # Load from cached file instead of network request
            import os
            class_file = os.path.join(os.path.dirname(__file__), "imagenet_classes.txt")
            
            if os.path.exists(class_file):
                with open(class_file, 'r', encoding='utf-8') as f:
                    self.class_names = [line.strip() for line in f.readlines()]
                logger.info(f"Loaded {len(self.class_names)} class names from cache")
            else:
                # Fallback to network request if cache doesn't exist
                import requests
                url = (
                    "https://raw.githubusercontent.com/pytorch/hub/master/"
                    "imagenet_classes.txt"
                )
                response = requests.get(url)
                self.class_names = response.text.strip().split("\n")
                logger.info(f"Loaded {len(self.class_names)} class names from network")
        except Exception as e:
            logger.warning(f"Failed to load class names: {e}")
            self.class_names = [f"class_{i}" for i in range(1000)]

    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """
        Preprocess image for model input

        Args:
            image: PIL Image object

        Returns:
            Preprocessed tensor
        """
        try:
            # Convert to RGB only if needed (skip check if already RGB)
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Apply transforms
            if self.transform is None:
                raise ValueError("Model transforms not initialized")
            tensor = self.transform(image)

            # Add batch dimension and move to device with non-blocking transfer
            tensor = tensor.unsqueeze(0).to(self.device, non_blocking=True)

            return tensor

        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise

    def predict(
        self, image: Image.Image, top_k: int = 5
    ) -> List[Dict[str, float]]:
        """
        Predict image class

        Args:
            image: PIL Image object
            top_k: Number of top predictions to return

        Returns:
            List of predictions with class names and probabilities
        """
        start_time = time.time()
        try:
            # Preprocess image
            input_tensor = self.preprocess_image(image)

            # Make prediction
            if self.model is None:
                raise ValueError("Model not loaded")
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = F.softmax(outputs, dim=1)

                # Get top-k predictions (optimize with batch CPU conversion)
                top_probs, top_indices = torch.topk(probabilities[0], top_k)
                top_probs_list = top_probs.cpu().tolist()  # Batch conversion
                top_indices_list = top_indices.cpu().tolist()

                # Convert to list of dictionaries
                predictions = [
                    {
                        "class_name": self.class_names[idx] if self.class_names else f"Class_{idx}",
                        "probability": prob,
                        "class_id": idx,
                    }
                    for prob, idx in zip(top_probs_list, top_indices_list)
                ]

                # Record metrics and logs
                duration = time.time() - start_time
                confidence = (
                    predictions[0]["probability"] if predictions else 0.0
                )
                image_size = len(image.tobytes())

                # Log classification
                log_classification(
                    logger=logger,
                    model_name=self.model_name,
                    confidence=confidence,
                    processing_time=duration,
                    top_k=top_k,
                    image_size=image_size,
                    status="success",
                )

                try:
                    from app.monitoring.metrics import metrics_collector

                    metrics_collector.record_classification(
                        model_name=self.model_name,
                        duration=duration,
                        confidence=confidence,
                        status="success",
                    )
                    metrics_collector.record_prediction_params(
                        top_k=top_k, image_size=image_size
                    )
                except ImportError:
                    # Metrics not available, continue without recording
                    pass

                return predictions

        except Exception as e:
            # Record failed prediction
            duration = time.time() - start_time
            image_size = len(image.tobytes()) if image else 0

            # Log error
            log_error(
                logger=logger,
                error=e,
                context={
                    "model_name": self.model_name,
                    "processing_time": duration,
                    "top_k": top_k,
                    "image_size": image_size,
                    "status": "error",
                },
            )

            try:
                from app.monitoring.metrics import metrics_collector

                metrics_collector.record_classification(
                    model_name=self.model_name,
                    duration=duration,
                    confidence=0.0,
                    status="error",
                )
            except ImportError:
                pass

            raise

    def get_model_info(self) -> Dict[str, str]:
        """
        Get model information

        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "device": str(self.device),
            "num_classes": str(
                len(self.class_names)  # type: ignore
                if self.class_names is not None
                else 1000
            ),
            "framework": "PyTorch",
            "quantized": str(self.is_quantized),
            "torchscript": str(self.is_torchscript),
            "parameters": str(self.model_parameters),
            "model_size_mb": f"{self.model_size_mb:.1f}",
        }
