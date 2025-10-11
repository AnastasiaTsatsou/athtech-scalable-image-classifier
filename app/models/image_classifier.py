"""
Image Classification Model Implementation
Uses pretrained ResNet model for image classification
"""

import torch
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
            else:
                raise ValueError(f"Unsupported model: {self.model_name}")

            self.model.eval()
            self.model.to(self.device)
            logger.info(f"Loaded {self.model_name} model on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def _setup_transforms(self):
        """Setup image preprocessing transforms"""
        self.transform = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

    def _load_class_names(self):
        """Load ImageNet class names"""
        try:
            # Load ImageNet class names
            import requests  # type: ignore

            url = (
                "https://raw.githubusercontent.com/pytorch/hub/master/"
                "imagenet_classes.txt"
            )
            response = requests.get(url)
            self.class_names = response.text.strip().split("\n")
            logger.info(
                f"Loaded {len(self.class_names) if self.class_names else 0} "
                f"class names"
            )
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
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Apply transforms
            if self.transform is None:
                raise ValueError("Model transforms not initialized")
            tensor = self.transform(image)

            # Add batch dimension
            tensor = tensor.unsqueeze(0)

            return tensor.to(self.device)

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

                # Get top-k predictions
                top_probs, top_indices = torch.topk(probabilities, top_k)

                # Convert to list of dictionaries
                predictions = []
                for i in range(top_k):
                    class_idx = top_indices[0][i].item()
                    prob = top_probs[0][i].item()
                    class_name = (
                        self.class_names[class_idx]
                        if self.class_names is not None
                        else f"Class_{class_idx}"
                    )

                    predictions.append(
                        {
                            "class_name": class_name,
                            "probability": prob,
                            "class_id": class_idx,
                        }
                    )

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
        }
