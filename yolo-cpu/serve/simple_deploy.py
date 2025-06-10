#!/usr/bin/env python3
"""
Simplified Ray Serve deployment script that connects to Ray cluster
and starts the serve application directly
"""
import os
import ray
import argparse
import sys
import time
from pathlib import Path

# Parse arguments
parser = argparse.ArgumentParser(description="Deploy YOLO Ray Serve")
parser.add_argument("--ray-address", default="ray://167.235.85.116:10001", 
                    help="Ray cluster address")
parser.add_argument("--model-path", default=None,
                    help="Path to YOLO model weights (optional)")
args = parser.parse_args()

# Print banner
print("🚀 Deploying YOLO Model to Ray Serve")
print("="*50)
print(f"📡 Connecting to Ray cluster at {args.ray_address}...")

# Connect to the Ray cluster
try:
    ray.init(address=args.ray_address)
except Exception as e:
    print(f"❌ Failed to connect to Ray cluster: {e}")
    sys.exit(1)

# Print connection info
print(f"✅ Connected to Ray cluster")
print(f"   Nodes: {len(ray.nodes())}")

# Start Ray Serve
print("📤 Starting Ray Serve...")
try:
    # Import Ray Serve
    from ray import serve
    
    # Create environment variable dictionary
    env_vars = {}
    if args.model_path:
        env_vars["YOLO_MODEL_PATH"] = args.model_path
    
    # Start serve
    serve.start(detached=True, http_options={"host": "0.0.0.0", "port": 8000})
    
    # Import the YOLO Predictor deployment
    from serve_yolo import YOLOPredictor, get_model_path
    
    # Get model path
    model_path = get_model_path()
    print(f"🔍 Using model: {model_path}")
    
    # Deploy using the correct API for Ray 2.41.0
    # Create and deploy the app with explicit route
    serve.run(YOLOPredictor.bind(model_path=model_path), name="YOLOPredictor", route_prefix="/")
    
    # Deploy the application
    print(f"✅ Deployment successful!")
    print(f"🌐 YOLO model service should be available at:")
    print(f"   http://167.235.85.117:8000")
    print(f"\n📝 Test with: python client.py --url http://167.235.85.117:8000 --image <image_path>")
    
except Exception as e:
    print(f"❌ Deployment failed: {e}")
    import traceback
    print(traceback.format_exc())
