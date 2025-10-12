"""
Locust load testing scenarios for the image classifier service
"""

from locust import HttpUser, task, between
import random
import io
from PIL import Image
import json


class ImageClassifierUser(HttpUser):
    """Locust user class for image classifier load testing"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Called when a user starts"""
        # Generate test images once
        self.test_images = self._generate_test_images()
        self.current_image_index = 0

    def _generate_test_images(self, count: int = 10):
        """Generate test images for load testing"""
        images = []
        sizes = [(224, 224), (256, 256), (512, 512)]

        for _ in range(count):
            # Create random image
            width, height = random.choice(sizes)
            image = Image.new("RGB", (width, height))
            pixels = image.load()

            # Fill with random colors
            for i in range(width):
                for j in range(height):
                    pixels[i, j] = (
                        random.randint(0, 255),
                        random.randint(0, 255),
                        random.randint(0, 255),
                    )

            # Convert to bytes
            img_buffer = io.BytesIO()
            image.save(img_buffer, format="JPEG")
            images.append(img_buffer.getvalue())

        return images

    @task(3)
    def test_health_endpoint(self):
        """Test health endpoint (30% of requests)"""
        with self.client.get(
            "/api/v1/health", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Health check failed with status {response.status_code}"
                )

    @task(2)
    def test_model_info_endpoint(self):
        """Test model info endpoint (20% of requests)"""
        with self.client.get(
            "/api/v1/model/info", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Model info failed with status {response.status_code}"
                )

    @task(5)
    def test_classify_endpoint(self):
        """Test image classification endpoint (50% of requests)"""
        # Select a random test image
        image_bytes = random.choice(self.test_images)

        # Random top_k value
        top_k = random.choice([1, 3, 5, 10])

        # Prepare request
        files = {"image": ("test_image.jpg", image_bytes, "image/jpeg")}
        data = {"top_k": top_k}

        with self.client.post(
            "/api/v1/classify", files=files, data=data, catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if (
                        "predictions" in result
                        and len(result["predictions"]) > 0
                    ):
                        response.success()
                    else:
                        response.failure("Invalid response format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(
                    f"Classification failed with status {response.status_code}"
                )

    @task(1)
    def test_root_endpoint(self):
        """Test root endpoint (10% of requests)"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Root endpoint failed with status {response.status_code}"
                )


class HighLoadUser(HttpUser):
    """High load user for stress testing"""

    wait_time = between(0.1, 0.5)  # Very short wait time

    def on_start(self):
        """Called when a user starts"""
        self.test_images = self._generate_test_images()

    def _generate_test_images(self, count: int = 5):
        """Generate test images for load testing"""
        images = []

        for _ in range(count):
            # Create small random image for faster processing
            image = Image.new("RGB", (224, 224))
            pixels = image.load()

            for i in range(224):
                for j in range(224):
                    pixels[i, j] = (
                        random.randint(0, 255),
                        random.randint(0, 255),
                        random.randint(0, 255),
                    )

            img_buffer = io.BytesIO()
            image.save(img_buffer, format="JPEG")
            images.append(img_buffer.getvalue())

        return images

    @task(8)
    def test_classify_endpoint(self):
        """Test image classification endpoint (80% of requests)"""
        image_bytes = random.choice(self.test_images)
        files = {"image": ("test_image.jpg", image_bytes, "image/jpeg")}
        data = {"top_k": 5}

        with self.client.post(
            "/api/v1/classify", files=files, data=data, catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Classification failed with status {response.status_code}"
                )

    @task(2)
    def test_health_endpoint(self):
        """Test health endpoint (20% of requests)"""
        with self.client.get(
            "/api/v1/health", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Health check failed with status {response.status_code}"
                )


class ErrorTestingUser(HttpUser):
    """User for testing error scenarios"""

    wait_time = between(2, 5)

    @task(1)
    def test_invalid_image(self):
        """Test with invalid image data"""
        invalid_data = b"not an image"
        files = {"image": ("invalid.jpg", invalid_data, "image/jpeg")}
        data = {"top_k": 5}

        with self.client.post(
            "/api/v1/classify", files=files, data=data, catch_response=True
        ) as response:
            if response.status_code == 400:
                response.success()
            else:
                response.failure(
                    f"Expected 400 error, got {response.status_code}"
                )

    @task(1)
    def test_missing_image(self):
        """Test with missing image file"""
        data = {"top_k": 5}

        with self.client.post(
            "/api/v1/classify", data=data, catch_response=True
        ) as response:
            if response.status_code == 400:
                response.success()
            else:
                response.failure(
                    f"Expected 400 error, got {response.status_code}"
                )

    @task(1)
    def test_invalid_top_k(self):
        """Test with invalid top_k parameter"""
        image_bytes = b"fake image data"
        files = {"image": ("test.jpg", image_bytes, "image/jpeg")}
        data = {"top_k": -1}

        with self.client.post(
            "/api/v1/classify", files=files, data=data, catch_response=True
        ) as response:
            if response.status_code == 400:
                response.success()
            else:
                response.failure(
                    f"Expected 400 error, got {response.status_code}"
                )

    @task(1)
    def test_large_image(self):
        """Test with very large image"""
        # Create a large image (this might cause memory issues)
        large_image = Image.new("RGB", (4000, 4000))
        img_buffer = io.BytesIO()
        large_image.save(img_buffer, format="JPEG")
        image_bytes = img_buffer.getvalue()

        files = {"image": ("large_image.jpg", image_bytes, "image/jpeg")}
        data = {"top_k": 5}

        with self.client.post(
            "/api/v1/classify", files=files, data=data, catch_response=True
        ) as response:
            # This might succeed or fail depending on system resources
            if response.status_code in [200, 400, 413, 500]:
                response.success()
            else:
                response.failure(
                    f"Unexpected status code: {response.status_code}"
                )
