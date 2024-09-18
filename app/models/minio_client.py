import os

from minio import Minio

# MinIO Client Setup
minio_client = Minio(
    os.getenv('MINIO_ENDPOINT', 'minio-service:9000'),
    access_key=os.getenv('MINIO_ACCESS_KEY'),
    secret_key=os.getenv('MINIO_SECRET_KEY'),
    secure=False
)
