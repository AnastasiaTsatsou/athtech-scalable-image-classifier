import requests
import json

# Test the custom system
url = "http://localhost:8081/api/v1/classify"

# Test with a simple image
with open("test_images/test_images/synthetic_red.jpg", "rb") as f:
    files = {"file": ("synthetic_red.jpg", f, "image/jpeg")}
    data = {"top_k": "5"}
    
    response = requests.post(url, files=files, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
