#!/usr/bin/env python3
"""
Ray Serve deployment script for YOLOv8 model inference.
This script deploys a YOLOv8 model using Ray Serve for production serving.
"""

import os
import yaml
import base64
import numpy as np
import cv2
from io import BytesIO
from PIL import Image
from typing import Dict, List, Any, Union
from dotenv import load_dotenv

import ray
from ray import serve
from ultralytics import YOLO

# Load environment variables from .env file
load_dotenv()

# WANDB configuration (optional for serving)
WANDB_API_KEY = os.getenv("WANDB_API_KEY")
WANDB_PROJECT = os.getenv("WANDB_PROJECT", "yolo-ray-serve")


@serve.deployment(
    num_replicas=1,
    ray_actor_options={"num_cpus": 1, "num_gpus": 0},
    health_check_period_s=30,
    health_check_timeout_s=30
)
class YOLOPredictor:
    def __init__(self, model_path: str, conf_threshold: float = 0.25):
        """
        Initialize the YOLO predictor with a trained model.
        
        Args:
            model_path: Path to the YOLOv8 model weights
            conf_threshold: Confidence threshold for predictions
        """
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        print(f"✅ Loaded YOLO model from {model_path}")
        
        # Get class names
        self.class_names = self.model.names
        print(f"📊 Model has {len(self.class_names)} classes")
        
    async def __call__(self, request) -> Dict[str, Any]:
        """
        Process prediction request and return results.
        
        Args:
            request: Ray Serve/Starlette request object
        
        Returns:
            Dict with prediction results
        """
        try:
            # Parse JSON from the request body
            try:
                request_dict = await request.json()
                print(f"📥 Received request: {str(request_dict.keys())[:100]}")
            except Exception as e:
                print(f"⚠️ Error parsing request JSON: {e}")
                return {"error": f"Invalid JSON in request: {str(e)}"}
            
            # Set confidence threshold from request or use default
            conf = request_dict.get("conf", self.conf_threshold)
            
            # Process image from base64 string
            if "image_base64" in request_dict:
                print(f"📸 Processing base64 image, length: {len(request_dict['image_base64'])}...")
                image_data = base64.b64decode(request_dict["image_base64"])
                img = Image.open(BytesIO(image_data))
                img = np.array(img)
                
            # Process image from URL
            elif "image_url" in request_dict:
                import requests
                url = request_dict["image_url"]
                print(f"📸 Processing image from URL: {url}")
                response = requests.get(url)
                img = Image.open(BytesIO(response.content))
                img = np.array(img)
            else:
                return {"error": "No image provided. Include either 'image_base64' or 'image_url' in the request."}

            # Convert to RGB if needed
            if len(img.shape) == 2:  # Grayscale image
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            elif img.shape[2] == 4:  # RGBA image
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                
            # Run inference
            results = self.model.predict(img, conf=conf, verbose=False)[0]
            
            # Extract and format results
            boxes = []
            for box in results.boxes:
                x1, y1, x2, y2 = [float(coord) for coord in box.xyxy[0]]
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = self.class_names[class_id]
                
                boxes.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": confidence,
                    "class_id": class_id,
                    "class_name": class_name
                })
            
            # Create JSON response
            response = {
                "success": True,
                "inference_time": float(results.speed["inference"]),
                "predictions": boxes,
                "image_shape": img.shape[:2],  # height, width
            }
            return response
            
        except Exception as e:
            import traceback
            return {
                "success": False, 
                "error": str(e),
                "traceback": traceback.format_exc()
            }


def get_model_path() -> str:
    """
    Get the path to the trained YOLO model.
    Searches for model in standard locations.
    """
    # Try to load from environment variable
    model_path = os.getenv("YOLO_MODEL_PATH", "")
    if model_path and os.path.exists(model_path):
        return model_path
    
    # Check config file for model path
    try:
        with open("./config.yaml", "r") as f:
            config = yaml.safe_load(f)
            model_name = config.get("model", "yolov8n.pt")
            
        # Check runs directory for trained model
        runs_dir = "../runs/detect"
        if os.path.exists(runs_dir):
            # Find the most recent weights directory
            weight_dirs = [d for d in os.listdir(runs_dir) if os.path.isdir(os.path.join(runs_dir, d))]
            if weight_dirs:
                latest_dir = max(weight_dirs)
                weights_file = os.path.join(runs_dir, latest_dir, "weights/best.pt")
                if os.path.exists(weights_file):
                    return weights_file
    except Exception as e:
        print(f"⚠️ Error finding model from config: {e}")
    
    # Fallback to default model
    return "yolov8n.pt"  # Will download from Ultralytics if not available


def create_deployment():
    """Create and deploy the YOLO model serving app"""
    # Get model path
    model_path = get_model_path()
    print(f"🔍 Using model: {model_path}")
    
    # Deploy the predictor
    app = YOLOPredictor.bind(model_path=model_path)
    
    return app


if __name__ == "__main__":
    # Start Ray if not initialized
    if not ray.is_initialized():
        ray.init()
    
    # Deploy the application
    serve.run(create_deployment, host="0.0.0.0", port=8000)
    
    print("✅ YOLO model serving is running on http://localhost:8000")
    print("📊 Health check endpoint: http://localhost:8000/-/healthz")
    import time
    while True:
        time.sleep(1)
