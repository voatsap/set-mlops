# YOLO Model Serving with Ray Serve

This directory contains scripts for deploying and testing a YOLOv8 object detection model with Ray Serve on a restricted Kubernetes environment.

## Overview

### Key Files
- `serve_yolo.py`: The main Ray Serve deployment script that serves the YOLOv8 model through a REST API
- `simple_deploy.py`: Script to deploy the YOLO model to a Ray cluster using Ray Client
- `client.py`: Test client that sends images to the deployed model and visualizes results
- `.env`: Optional environment configuration file for W&B credentials
- `test.jpg`: Sample test image for validating the model

### Infrastructure Components
- **Ray Cluster**: Running on Kubernetes in the `shalb-mlops` namespace with KubeRay operator
- **Ray Head Node**: Provides Ray API on port 10001 and Dashboard on 8265
- **Ray Worker Nodes**: Handle distributed processing tasks
- **Kubernetes Services**: LoadBalancer services expose Ray Client (10001), Dashboard (8265), and Serve API (8000) 

## Prerequisites

- Ray 2.41.0 (cluster is running with Python 3.10.16)
- Python 3.10+ (client should match cluster Python version)
- Ultralytics YOLOv8 package
- Access to the `shalb-mlops` Kubernetes namespace

## Ray Cluster Infrastructure

The Ray cluster is deployed using Helm in the `shalb-mlops` namespace with these key configurations:

```yaml
# Ray cluster configuration highlights from ray-cluster-values.yaml
rayVersion: 2.41.0  # Matches client Ray version
image:
  repository: rayproject/ray
  tag: 2.41.0-py310  # Python 3.10 container image

head:
  rayStartParams:
    dashboard-host: 0.0.0.0
    port: 6379
    ray-client-server-port: "10001"  # Ray Client port
  resources: 
    limits: {cpu: 2, memory: 4Gi}  # Increased for stability
  
worker:
  replicas: 1
  resources:
    limits: {cpu: 4, memory: 8Gi}  # Increased for YOLO training
```

Kubernetes LoadBalancer services expose:
- Ray Client: 167.235.85.116:10001
- Ray Dashboard: 167.235.85.116:8265
- Ray Serve API: 167.235.85.117:8000

## Setup

1. Make sure your environment has all necessary packages:

```bash
pip install ray[serve]==2.41.0 ultralytics pillow requests python-dotenv matplotlib pyyaml opencv-python
```

2. Optional: Create an `.env` file in the parent directory with your W&B credentials:

```
WANDB_API_KEY=your_wandb_api_key
WANDB_PROJECT=your_wandb_project
```

## Deployment Process

### Deploy to Ray Cluster

```bash
# Deploy the model to Ray Serve
python simple_deploy.py --ray-address ray://167.235.85.116:10001

# Optionally specify a custom YOLO model path
python simple_deploy.py --ray-address ray://167.235.85.116:10001 --model-path ../runs/detect/train/weights/best.pt
```

The deployment script:
1. Connects to the Ray cluster via Ray Client on port 10001
2. Initializes Ray Serve on the cluster
3. Deploys the YOLO model using the Ray Serve API
4. Configures HTTP routes and health checks

### Kubernetes Service Integration

The Ray Serve API runs on port 8000 on the Ray head node and is exposed through a LoadBalancer service:

```bash
# Service is already applied and available at 167.235.85.117:8000
kubectl get svc ray-serve-service-lb -n shalb-mlops
```

Service definition in `infra/ray-serve-service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ray-serve-service-lb
  namespace: shalb-mlops
spec:
  type: LoadBalancer
  selector:
    ray.io/cluster: raycluster-raycluster-kuberay
    ray.io/node-type: head
    app.kubernetes.io/name: kuberay
  ports:
  - name: ray-serve
    protocol: TCP
    port: 8000
    targetPort: 8000
```

## Testing the Model

### Using the Provided Client

```bash
# Test with the sample image
python client.py --url http://167.235.85.117:8000 --image test.jpg

# Adjust confidence threshold (default: 0.25)
python client.py --url http://167.235.85.117:8000 --image test.jpg --conf 0.5

# Save output to a file
python client.py --url http://167.235.85.117:8000 --image test.jpg --output result.jpg
```

### Using Direct API Calls

```python
import requests
import base64

# Encode image to base64
with open("test.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# Prepare request
url = "http://167.235.85.117:8000"
data = {
    "image_base64": image_data,
    "conf": 0.25  # Optional confidence threshold
}

# Send request
response = requests.post(url, json=data)
results = response.json()

# Process results
for pred in results["predictions"]:
    print(f"{pred['class_name']}: {pred['confidence']:.2f}")
```

## API Reference

### Endpoint

`POST http://167.235.85.117:8000`

### Request Format

JSON body with one of these fields:

```json
{
  "image_base64": "<base64-encoded-image-data>",
  "conf": 0.25  # Optional confidence threshold (0-1)
}
```

OR

```json
{
  "image_url": "https://example.com/image.jpg",
  "conf": 0.25  # Optional confidence threshold (0-1)
}
```

### Response Format

```json
{
  "success": true,
  "inference_time": 345.67,  # Milliseconds
  "predictions": [
    {
      "bbox": [x1, y1, x2, y2],  # Pixel coordinates
      "confidence": 0.92,
      "class_id": 0,
      "class_name": "person"
    }
  ],
  "image_shape": [height, width]  # Original image dimensions
}
```

### Error Response

```json
{
  "success": false,
  "error": "Error message",
  "traceback": "Detailed error information"
}
```

## Implementation Details

### Model Loading Logic

The YOLO model is loaded from one of these locations (in order of priority):

1. Path specified by the `YOLO_MODEL_PATH` environment variable
2. Path specified in the config.yaml file
3. Latest model in the training runs directory (`../runs/detect/*/weights/best.pt`)
4. Default `yolov8n.pt` from Ultralytics (downloaded automatically if not present)

### Ray Serve Configuration

The Ray Serve deployment is configured with:

- 1 replica for processing requests
- CPU-only inference (no GPUs)
- Health checks every 30 seconds
- Model loaded at startup to minimize prediction latency

## Troubleshooting

### Common Issues

- **Python Version Mismatch**: Make sure your client Python version (3.10.x) is compatible with the Ray cluster (3.10.16)
- **Ray Version Mismatch**: Both client and cluster should use Ray 2.41.0
- **404 Errors**: Check URL format (remove trailing slash) and verify the Ray Serve app is deployed correctly
- **Memory Issues**: Check Ray dashboard for OOM errors and adjust Ray worker memory in the cluster config

### Debugging Tools

- View Ray Serve status: http://167.235.85.116:8265/#/serve
- Monitor Ray logs: http://167.235.85.116:8265/#/log
- Check Ray Serve API health: `curl http://167.235.85.117:8000/-/healthz`

### Kubernetes Resources

The Ray cluster is configured with these resource limits:

- Head Node: 2 CPUs, 4GB memory
- Worker Node: 4 CPUs, 8GB memory

Be aware of resource constraints, as the cluster is running in a limited Kubernetes namespace with restricted permissions.
