#!/usr/bin/env python3
"""
Test Image Generator
Creates synthetic test images and downloads sample real images for validation
"""

import os
import sys
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pathlib import Path
import json

def create_synthetic_images():
    """Create synthetic test images"""
    print("Creating synthetic test images...")
    
    images_dir = Path("test_images")
    images_dir.mkdir(exist_ok=True)
    
    # Create different colored images
    colors = [
        ('red', (255, 0, 0)),
        ('green', (0, 255, 0)),
        ('blue', (0, 0, 255)),
        ('yellow', (255, 255, 0)),
        ('purple', (128, 0, 128)),
        ('orange', (255, 165, 0)),
        ('pink', (255, 192, 203)),
        ('cyan', (0, 255, 255))
    ]
    
    for color_name, color_rgb in colors:
        # Create solid color image
        image = Image.new('RGB', (224, 224), color_rgb)
        image.save(images_dir / f"synthetic_{color_name}.jpg")
        
        # Create gradient image
        gradient = Image.new('RGB', (224, 224))
        draw = ImageDraw.Draw(gradient)
        
        for y in range(224):
            # Create vertical gradient
            r = int(color_rgb[0] * (y / 224))
            g = int(color_rgb[1] * (y / 224))
            b = int(color_rgb[2] * (y / 224))
            draw.line([(0, y), (224, y)], fill=(r, g, b))
        
        gradient.save(images_dir / f"gradient_{color_name}.jpg")
    
    print(f"✓ Created {len(colors) * 2} synthetic images")
    return len(colors) * 2

def create_pattern_images():
    """Create images with geometric patterns"""
    print("Creating pattern images...")
    
    images_dir = Path("test_images")
    
    # Create checkerboard pattern
    checkerboard = Image.new('RGB', (224, 224))
    draw = ImageDraw.Draw(checkerboard)
    
    square_size = 28  # 224 / 8 = 28
    for y in range(0, 224, square_size):
        for x in range(0, 224, square_size):
            if (x // square_size + y // square_size) % 2 == 0:
                draw.rectangle([x, y, x + square_size, y + square_size], fill='black')
            else:
                draw.rectangle([x, y, x + square_size, y + square_size], fill='white')
    
    checkerboard.save(images_dir / "checkerboard.jpg")
    
    # Create concentric circles
    circles = Image.new('RGB', (224, 224), 'white')
    draw = ImageDraw.Draw(circles)
    
    center = (112, 112)
    for radius in range(20, 112, 20):
        draw.ellipse([center[0] - radius, center[1] - radius, 
                     center[0] + radius, center[1] + radius], 
                     outline='black', width=2)
    
    circles.save(images_dir / "concentric_circles.jpg")
    
    # Create diagonal stripes
    stripes = Image.new('RGB', (224, 224), 'white')
    draw = ImageDraw.Draw(stripes)
    
    for i in range(0, 224, 10):
        draw.line([(i, 0), (i + 224, 224)], fill='red', width=2)
    
    stripes.save(images_dir / "diagonal_stripes.jpg")
    
    print("✓ Created 3 pattern images")
    return 3

def download_sample_images():
    """Download sample real images from public sources"""
    print("Downloading sample real images...")
    
    images_dir = Path("test_images")
    
    # Sample images from Unsplash (free to use)
    sample_images = [
        {
            "name": "cat.jpg",
            "url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=224&h=224&fit=crop",
            "description": "Cat"
        },
        {
            "name": "dog.jpg", 
            "url": "https://images.unsplash.com/photo-1552053831-71594a27632d?w=224&h=224&fit=crop",
            "description": "Dog"
        },
        {
            "name": "car.jpg",
            "url": "https://images.unsplash.com/photo-1549317336-206569e8475c?w=224&h=224&fit=crop", 
            "description": "Car"
        },
        {
            "name": "airplane.jpg",
            "url": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=224&h=224&fit=crop",
            "description": "Airplane"
        },
        {
            "name": "bird.jpg",
            "url": "https://images.unsplash.com/photo-1444464666168-49d633b86797?w=224&h=224&fit=crop",
            "description": "Bird"
        }
    ]
    
    downloaded_count = 0
    
    for img_info in sample_images:
        try:
            response = requests.get(img_info["url"], timeout=10)
            if response.status_code == 200:
                # Save image
                with open(images_dir / img_info["name"], 'wb') as f:
                    f.write(response.content)
                
                # Resize to 224x224 if needed
                image = Image.open(images_dir / img_info["name"])
                if image.size != (224, 224):
                    image = image.resize((224, 224), Image.Resampling.BILINEAR)
                    image.save(images_dir / img_info["name"])
                
                downloaded_count += 1
                print(f"✓ Downloaded {img_info['name']} ({img_info['description']})")
            else:
                print(f"⚠ Failed to download {img_info['name']}: {response.status_code}")
                
        except Exception as e:
            print(f"⚠ Failed to download {img_info['name']}: {e}")
    
    print(f"✓ Downloaded {downloaded_count} real images")
    return downloaded_count

def create_image_manifest():
    """Create a manifest file describing all test images"""
    print("Creating image manifest...")
    
    images_dir = Path("test_images")
    manifest = {
        "synthetic_images": [],
        "pattern_images": [],
        "real_images": [],
        "total_count": 0
    }
    
    # List all images
    for img_file in images_dir.glob("*.jpg"):
        img_info = {
            "filename": img_file.name,
            "size": img_file.stat().st_size,
            "type": "unknown"
        }
        
        if img_file.name.startswith("synthetic_"):
            img_info["type"] = "synthetic"
            img_info["color"] = img_file.stem.split("_", 1)[1]
            manifest["synthetic_images"].append(img_info)
        elif img_file.name.startswith("gradient_"):
            img_info["type"] = "gradient"
            img_info["color"] = img_file.stem.split("_", 1)[1]
            manifest["synthetic_images"].append(img_info)
        elif img_file.name in ["checkerboard.jpg", "concentric_circles.jpg", "diagonal_stripes.jpg"]:
            img_info["type"] = "pattern"
            img_info["pattern"] = img_file.stem
            manifest["pattern_images"].append(img_info)
        else:
            img_info["type"] = "real"
            manifest["real_images"].append(img_info)
    
    manifest["total_count"] = len(manifest["synthetic_images"]) + len(manifest["pattern_images"]) + len(manifest["real_images"])
    
    # Save manifest
    with open(images_dir / "manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✓ Created manifest with {manifest['total_count']} images")
    return manifest

def main():
    """Main function"""
    print("=== Test Image Generator ===")
    print("Creating synthetic and real test images for validation")
    
    # Change to comparisons directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    try:
        # Create synthetic images
        synthetic_count = create_synthetic_images()
        
        # Create pattern images
        pattern_count = create_pattern_images()
        
        # Download real images
        real_count = download_sample_images()
        
        # Create manifest
        manifest = create_image_manifest()
        
        print(f"\n✅ Success! Created {manifest['total_count']} test images:")
        print(f"  - {len(manifest['synthetic_images'])} synthetic images")
        print(f"  - {len(manifest['pattern_images'])} pattern images") 
        print(f"  - {len(manifest['real_images'])} real images")
        
        print(f"\n📁 Images saved to: {script_dir / 'test_images'}")
        print("📋 Manifest saved to: test_images/manifest.json")
        
        print("\nNext steps:")
        print("1. Use these images for validation testing")
        print("2. Run benchmark_comparison.py to test all systems")
        
    except Exception as e:
        print(f"\n❌ Failed to create test images: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

