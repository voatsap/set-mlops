# YOLO CPU - Training and Serving

This project provides a complete solution for training and serving YOLOv8 object detection models using Ray on a Kubernetes cluster.

## Project Structure

- **`train/`**: Scripts for training YOLOv8 models with Ray jobs
  - `train_yolo.py`: Core training script with W&B integration
  - `ray_job.py`: Ray job definition for distributed training
  - `submit_job.py`: Job submission script for Ray cluster
  - `config.yaml`: Configuration for training parameters
  
- **`serve/`**: Scripts for serving trained models with Ray Serve
  - `serve_yolo.py`: Ray Serve application for YOLO inference
  - `simple_deploy.py`: Deployment script for Ray cluster
  - `client.py`: Test client for sending images and visualizing predictions
  
- **`requirements.txt`**: Dependencies for both training and serving
- **`.env`**: Environment variables for W&B credentials and model paths

## Getting Started

1. **Setup Environment**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Train a Model**:
   ```bash
   cd train
   python submit_job.py --ray-address ray://167.235.85.116:10001
   ```

3. **Deploy for Inference**:
   ```bash
   cd serve
   python simple_deploy.py --ray-address ray://167.235.85.116:10001
   ```

4. **Test the Deployed Model**:
   ```bash
   cd serve
   python client.py --url http://167.235.85.117:8000 --image test.jpg
   ```

## Infrastructure

This project uses:
- **Ray** for distributed training and serving in Kubernetes
- **Ultralytics YOLOv8** for object detection
- **Weights & Biases** for experiment tracking
- **Kubernetes** with LoadBalancer services for exposing endpoints

See the READMEs in the `train/` and `serve/` directories for detailed information on each component.
