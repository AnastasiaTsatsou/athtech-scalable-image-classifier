"""
Unit tests for the FastAPI endpoints
"""

import pytest
import io
from fastapi.testclient import TestClient
from PIL import Image
import numpy as np

from app.main import app

client = TestClient(app)


class TestAPIEndpoints:
    """Test cases for API endpoints"""
    
    @pytest.fixture
    def sample_image_file(self):
        """Create a sample image file for testing"""
        # Create a random RGB image
        image_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        image = Image.fromarray(image_array)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        return img_byte_arr.getvalue()
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert data["message"] == "Scalable Image Classifier API"
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "model_info" in data
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
    
    def test_model_info_endpoint(self):
        """Test model info endpoint"""
        response = client.get("/api/v1/model/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "model_name" in data
        assert "device" in data
        assert "num_classes" in data
        assert "framework" in data
    
    def test_classify_endpoint_success(self, sample_image_file):
        """Test successful image classification"""
        response = client.post(
            "/api/v1/classify",
            files={"file": ("test.jpg", sample_image_file, "image/jpeg")},
            data={"top_k": "5"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "predictions" in data
        assert "model_info" in data
        assert "processing_time_ms" in data
        
        # Check predictions structure
        predictions = data["predictions"]
        assert len(predictions) == 5
        for pred in predictions:
            assert "class_name" in pred
            assert "probability" in pred
            assert "class_id" in pred
            assert 0.0 <= pred["probability"] <= 1.0
    
    def test_classify_endpoint_different_top_k(self, sample_image_file):
        """Test classification with different top_k values"""
        for k in [1, 3, 5, 10]:
            response = client.post(
                "/api/v1/classify",
                files={"file": ("test.jpg", sample_image_file, "image/jpeg")},
                data={"top_k": str(k)}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["predictions"]) == k
    
    def test_classify_endpoint_invalid_file_type(self):
        """Test classification with invalid file type"""
        response = client.post(
            "/api/v1/classify",
            files={"file": ("test.txt", b"not an image", "text/plain")},
            data={"top_k": "5"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "image" in data["detail"].lower()
    
    def test_classify_endpoint_no_file(self):
        """Test classification without file"""
        response = client.post(
            "/api/v1/classify",
            data={"top_k": "5"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_classify_endpoint_invalid_top_k(self, sample_image_file):
        """Test classification with invalid top_k values"""
        # Test top_k = 0
        response = client.post(
            "/api/v1/classify",
            files={"file": ("test.jpg", sample_image_file, "image/jpeg")},
            data={"top_k": "0"}
        )
        assert response.status_code == 422
        
        # Test top_k > 10
        response = client.post(
            "/api/v1/classify",
            files={"file": ("test.jpg", sample_image_file, "image/jpeg")},
            data={"top_k": "15"}
        )
        assert response.status_code == 422
    
    def test_docs_endpoint(self):
        """Test API documentation endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_endpoint(self):
        """Test ReDoc documentation endpoint"""
        response = client.get("/redoc")
        assert response.status_code == 200
