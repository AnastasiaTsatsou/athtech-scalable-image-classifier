"""
Unit tests for the image classifier model
"""

import pytest
import torch
from PIL import Image
import numpy as np
from app.models.image_classifier import ImageClassifier


class TestImageClassifier:
    """Test cases for ImageClassifier"""
    
    @pytest.fixture
    def classifier(self):
        """Create a classifier instance for testing"""
        return ImageClassifier(model_name="resnet50", device="cpu")
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image"""
        # Create a random RGB image
        image_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        return Image.fromarray(image_array)
    
    def test_classifier_initialization(self, classifier):
        """Test classifier initialization"""
        assert classifier.model is not None
        assert classifier.transform is not None
        assert classifier.class_names is not None
        assert len(classifier.class_names) == 1000
    
    def test_model_info(self, classifier):
        """Test model info retrieval"""
        info = classifier.get_model_info()
        assert "model_name" in info
        assert "device" in info
        assert "num_classes" in info
        assert "framework" in info
        assert info["model_name"] == "resnet50"
        assert info["framework"] == "PyTorch"
    
    def test_image_preprocessing(self, classifier, sample_image):
        """Test image preprocessing"""
        tensor = classifier.preprocess_image(sample_image)
        
        # Check tensor shape
        assert tensor.shape == (1, 3, 224, 224)
        assert tensor.dtype == torch.float32
        
        # Check tensor values are normalized
        assert tensor.min() >= -3.0  # Allow for some variance in normalization
        assert tensor.max() <= 3.0
    
    def test_prediction(self, classifier, sample_image):
        """Test image prediction"""
        predictions = classifier.predict(sample_image, top_k=5)
        
        # Check prediction structure
        assert len(predictions) == 5
        for pred in predictions:
            assert "class_name" in pred
            assert "probability" in pred
            assert "class_id" in pred
            assert 0.0 <= pred["probability"] <= 1.0
            assert isinstance(pred["class_id"], int)
            assert 0 <= pred["class_id"] < 1000
    
    def test_prediction_probabilities_sum(self, classifier, sample_image):
        """Test that prediction probabilities are reasonable"""
        predictions = classifier.predict(sample_image, top_k=10)
        
        # Check that probabilities are sorted in descending order
        probs = [pred["probability"] for pred in predictions]
        assert probs == sorted(probs, reverse=True)
        
        # Check that top probability is reasonable (not too low)
        assert predictions[0]["probability"] > 0.001
    
    def test_different_top_k_values(self, classifier, sample_image):
        """Test prediction with different top_k values"""
        for k in [1, 3, 5, 10]:
            predictions = classifier.predict(sample_image, top_k=k)
            assert len(predictions) == k
    
    def test_invalid_image_format(self, classifier):
        """Test handling of invalid image formats"""
        # Create a grayscale image
        gray_array = np.random.randint(0, 255, (224, 224), dtype=np.uint8)
        gray_image = Image.fromarray(gray_array, mode='L')
        
        # Should convert to RGB automatically
        predictions = classifier.predict(gray_image)
        assert len(predictions) > 0
    
    def test_model_types(self):
        """Test different model types"""
        for model_name in ["resnet50", "resnet101", "resnet152"]:
            classifier = ImageClassifier(model_name=model_name, device="cpu")
            info = classifier.get_model_info()
            assert info["model_name"] == model_name
