import uuid

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.config import settings

_scheme = "https" if settings.minio_use_ssl else "http"

s3_client = boto3.client(
    "s3",
    endpoint_url=f"{_scheme}://{settings.minio_endpoint}",
    aws_access_key_id=settings.minio_root_user,
    aws_secret_access_key=settings.minio_root_password,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)


def ensure_bucket_exists():
    try:
        s3_client.head_bucket(Bucket=settings.minio_bucket)
    except ClientError:
        s3_client.create_bucket(Bucket=settings.minio_bucket)


def upload_recipe_image(file: UploadFile, recipe_id: str) -> str:
    """Uploads an image to MinIO and returns a URL the frontend can use to fetch it."""
    ensure_bucket_exists()

    extension = (file.filename or "").split(".")[-1] or "jpg"
    object_key = f"recipes/{recipe_id}/{uuid.uuid4()}.{extension}"

    s3_client.upload_fileobj(
        file.file,
        settings.minio_bucket,
        object_key,
        ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
    )

    # Presigned GET URL — simplest way to serve images from a private bucket.
    # For production you'd likely put a CDN/reverse proxy in front instead.
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.minio_bucket, "Key": object_key},
        ExpiresIn=60 * 60 * 24 * 7,  # 7 days
    )
    return url
