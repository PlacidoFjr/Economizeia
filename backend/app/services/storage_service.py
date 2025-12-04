from minio import Minio
from minio.error import S3Error
import logging
from typing import Optional
from app.core.config import settings
import io

logger = logging.getLogger(__name__)


class StorageService:
    """Service for S3-compatible storage using MinIO."""
    
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Ensure the bucket exists."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket: {e}")
    
    def upload_file(self, file_bytes: bytes, object_name: str, content_type: str) -> str:
        """
        Upload file to storage.
        Returns: S3 path
        """
        try:
            file_obj = io.BytesIO(file_bytes)
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_obj,
                length=len(file_bytes),
                content_type=content_type
            )
            return f"{self.bucket_name}/{object_name}"
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def get_file(self, object_name: str) -> bytes:
        """Download file from storage."""
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """Get presigned URL for temporary access."""
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires_seconds)
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    def delete_file(self, object_name: str):
        """Delete file from storage."""
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            logger.error(f"Error deleting file: {e}")
            raise


storage_service = StorageService()

