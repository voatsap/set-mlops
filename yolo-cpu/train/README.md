# YOLO Model Training with Ray

This directory contains scripts for training YOLOv8 object detection models using Ray on a Kubernetes cluster.

## Overview

### Key Files
- `train_yolo.py`: Main training script for YOLOv8 model with Weights & Biases integration
- `ray_job.py`: Ray job definition for distributed training
- `submit_job.py`: Script to submit training jobs to a Ray cluster
- `config.yaml`: Configuration file for training parameters and paths

### Infrastructure Integration
- **Ray Cluster**: Submits training jobs to Ray running in the `shalb-mlops` Kubernetes namespace
- **W&B Integration**: Tracks training metrics and model performance
- **Model Storage**: Saves models to local filesystem, accessible for serving

## Prerequisites

- Ray 2.41.0 (compatible with cluster running Python 3.10.16)
- Python 3.10+ environment
- Ultralytics YOLOv8 package
- Weights & Biases account (optional, for tracking experiments)
- Access to the `shalb-mlops` Kubernetes namespace

## Setup

1. Install the required packages:

```bash
pip install -r ../requirements.txt
```

2. Create a `.env` file in the parent directory with your W&B credentials (optional):

```
WANDB_API_KEY=your_wandb_api_key
WANDB_PROJECT=your_wandb_project
```

## Configuration

Edit `config.yaml` to configure training parameters:

```yaml
# Sample configuration
data:
  path: "../data/dataset.yaml"  # Path to YOLO dataset config
  val: "test"  # Validation set name

model:
  name: "yolov8n.pt"  # Base model to use
  img_size: 640  # Image size for training

training:
  epochs: 50
  batch_size: 16
  workers: 2
  device: "cpu"  # Use "0" for GPU if available
  project: "yolo-detection"  # Project name for W&B
```

## Usage

### Local Training

To train locally without Ray:

```bash
python train_yolo.py
```

### Submitting to Ray Cluster

To submit a training job to a Ray cluster:

```bash
python submit_job.py --ray-address ray://167.235.85.116:10001
```

### Using the Ray Job API

For programmatic job control:

```bash
python ray_job.py --ray-address ray://167.235.85.116:10001
```

## Model Output

Trained models are saved to:

```
../runs/detect/{project_name}/weights/
```

The best model is available at `../runs/detect/{project_name}/weights/best.pt`

## Integration with Serving

After training, the resulting model can be deployed with Ray Serve using the scripts in the `../serve` directory. The model path can be specified in the deployment:

```bash
python ../serve/simple_deploy.py --ray-address ray://167.235.85.116:10001 --model-path ../runs/detect/{project_name}/weights/best.pt
```

## Troubleshooting

- **Memory Issues**: Adjust batch size in config.yaml
- **Ray Connection Errors**: Verify Ray cluster is running and accessible
- **W&B Authentication**: Check WANDB_API_KEY environment variable or .env file
- **Python Version Mismatch**: Ensure your environment uses Python 3.10.x

## Monitoring

- Monitor training progress in W&B dashboard
- View Ray job status at http://167.235.85.116:8265/#/job
