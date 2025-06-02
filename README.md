# Yacht Detection Dataset Annotation Project

## Project Structure

```
mlops/
├── docker-compose.yml
├── mydata/                # Label Studio data (annotations, projects)
├── minio-data/            # MinIO S3-compatible storage data
├── postgres-data/         # PostgreSQL database data
├── docs/
└── README.md
```

## Annotation Tool

We use **Label Studio** ([heartexlabs/label-studio](https://github.com/heartexlabs/label-studio)) for image annotation.  
Label Studio is a flexible, open-source data labeling tool that supports a wide range of data types and integrates seamlessly with cloud storage.

![Label Studio Interface](docs/images/label-studio-interface.png)

## How to Launch the Annotation Platform

1. **Clone the repository and enter the project directory:**
   ```sh
   git clone https://github.com/voa/mlops.git
   cd mlops
   ```

2. **Start the annotation stack with Docker Compose:**
   ```sh
   docker-compose up -d
   ```

3. **Access services:**
   - **Label Studio:** [http://localhost:8080](http://localhost:8080)
   - **MinIO Console:** [http://localhost:9009](http://localhost:9009)  
     (default login: `minioadmin` / `minioadmin`)

4. **Cloud Storage Buckets:**
   - `yacht-dataset` — Source images for annotation
   - `yacht-labeled-dataset` — Target bucket for labeled data

## Dataset Versioning

- **MinIO** acts as an S3-compatible object storage, allowing you to organize and version datasets using buckets.
- **Source bucket:** `yacht-dataset` contains the raw images to be annotated.
- **Target bucket:** `yacht-labeled-dataset` stores the resulting annotated data.
- You can use MinIO’s versioning features or external tools (like DVC or custom scripts) to manage dataset snapshots and history.

## Future Use of the Data

The annotated data will be used for:
- Training and validating **machine learning models** for yacht detection and classification.
- Research and development of computer vision algorithms in maritime environments.
- Potential deployment in real-time detection systems or analytics dashboards.

## Additional Notes

- All annotation and storage services run locally via Docker Compose for easy setup and reproducibility.
- To stop the stack:  
  ```sh
  docker-compose down
  ```
- Make sure to back up your `mydata/`, `minio-data/`, and `postgres-data/` folders to preserve your work.
