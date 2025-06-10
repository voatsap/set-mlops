#!/usr/bin/env python3
"""
Test client for the YOLO Ray Serve deployment.
This script demonstrates how to call the deployed YOLO model and visualize results.
"""

import sys
import os
import requests
import base64
import json
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import argparse
import time
import random
import numpy as np
import matplotlib.pyplot as plt


def encode_image(image_path):
    """Encode an image file to base64"""
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        
    return base64.b64encode(image_bytes).decode("utf-8")


def draw_predictions(image_path, predictions):
    """
    Draw bounding boxes and labels on the image based on predictions
    """
    # Open image
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    
    # Try to get a font, use default if not available
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
        
    # Random colors for each class
    np.random.seed(42)  # for reproducibility
    colors = {class_id: tuple(np.random.randint(0, 255, 3).tolist()) 
              for class_id in set(pred["class_id"] for pred in predictions)}
    
    # Draw each prediction
    for pred in predictions:
        # Extract info
        x1, y1, x2, y2 = pred["bbox"]
        class_name = pred["class_name"]
        confidence = pred["confidence"]
        class_id = pred["class_id"]
        color = colors[class_id]
        
        # Draw bounding box
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        
        # Draw label background
        label = f"{class_name}: {confidence:.2f}"
        text_size = draw.textbbox((0, 0), label, font=font)[2:4]
        draw.rectangle(
            [x1, y1, x1 + text_size[0] + 10, y1 + text_size[1] + 10],
            fill=color
        )
        
        # Draw label text
        draw.text((x1 + 5, y1 + 5), label, fill="white", font=font)
    
    return image


def test_prediction(server_url, image_path, output_path=None, conf=0.25):
    """Test the YOLO prediction service with an image"""
    
    # Check if image exists
    if not os.path.isfile(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)
    
    print(f"🖼️  Using image: {image_path}")
    
    # Encode the image
    base64_image = encode_image(image_path)
    
    # Prepare request
    request_data = {
        "image_base64": base64_image,
        "conf": conf
    }
    
    # Call the API
    start_time = time.time()
    try:
        # Ensure URL doesn't end with trailing slash for POST request
        if server_url.endswith('/'):
            server_url = server_url[:-1]
            
        # Debug request data (truncate base64 for readability)
        debug_data = request_data.copy()
        if 'image_base64' in debug_data:
            debug_data['image_base64'] = debug_data['image_base64'][:30] + '...' 
        print(f"📦 Request data: {debug_data}")
        print(f"🚀 Sending POST request to {server_url}...")
        
        # Add headers to ensure proper JSON parsing
        headers = {'Content-Type': 'application/json'}
        response = requests.post(server_url, json=request_data, headers=headers)
        total_time = time.time() - start_time
        
        print(f"📡 Response status: {response.status_code}")
        print(f"📜 Response headers: {dict(response.headers)}")
    
        if response.status_code != 200:
            print(f"❌ Error: Received status code {response.status_code}")
            print(f"Response content: {response.text}")
            return
            
        result = response.json()
        
        if "error" in result:
            print(f"❌ Error in prediction: {result['error']}")
            return
            
        # Print results
        print(f"✅ Prediction successful in {total_time:.2f}s")
        print(f"🔍 Server inference time: {result.get('inference_time', 0):.2f}ms")
        print(f"📊 Found {len(result['predictions'])} objects")
        
        # Draw predictions on image
        if result["predictions"]:
            for i, pred in enumerate(result["predictions"]):
                print(f"  {i+1}. {pred['class_name']} ({pred['confidence']:.2f})")
                
            # Visualize results
            output = draw_predictions(image_path, result["predictions"])
            
            # Save or show results
            if output_path:
                output.save(output_path)
                print(f"✅ Saved annotated image to {output_path}")
            else:
                plt.figure(figsize=(12, 8))
                plt.imshow(np.array(output))
                plt.axis('off')
                plt.show()
        else:
            print("⚠️ No objects detected in the image")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the YOLO Ray Serve deployment")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000/", 
        help="URL of the Ray Serve endpoint"
    )
    parser.add_argument(
        "--image", 
        required=True,
        help="Path to image file to test"
    )
    parser.add_argument(
        "--output", 
        help="Path to save annotated output image (optional)"
    )
    parser.add_argument(
        "--conf", 
        type=float, 
        default=0.25, 
        help="Confidence threshold (0-1)"
    )
    
    args = parser.parse_args()
    test_prediction(args.url, args.image, args.output, args.conf)
