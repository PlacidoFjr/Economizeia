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
        self.enabled = settings.MINIO_ENABLED if hasattr(settings, 'MINIO_ENABLED') else False
        self.client = None
        self.bucket_name = settings.MINIO_BUCKET_NAME
        
        if self.enabled:
            try:
                self.client = Minio(
                    settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_USE_SSL
                )
                self._ensure_bucket()
            except Exception as e:
                logger.warning(f"MinIO not available, storage will be disabled: {e}")
                self.enabled = False
        else:
            logger.info("MinIO storage is disabled")
    
    def _ensure_bucket(self):
        """Ensure the bucket exists."""
        if not self.enabled or not self.client:
            return
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except Exception as e:
            logger.warning(f"Could not ensure bucket (MinIO may not be available): {e}")
            self.enabled = False
    
    def upload_file(self, file_bytes: bytes, object_name: str, content_type: str) -> str:
        """
        Upload file to storage.
        Returns: S3 path
        """
        if not self.enabled or not self.client:
            logger.warning(f"Storage disabled, returning mock path for: {object_name}")
            return f"mock/{object_name}"
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
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            # Retornar path mock em vez de quebrar
            return f"mock/{object_name}"
    
    def get_file(self, object_name: str) -> bytes:
        """Download file from storage."""
        if not self.enabled or not self.client:
            logger.warning(f"Storage disabled, cannot get file: {object_name}")
            raise FileNotFoundError(f"Storage is disabled, file not available: {object_name}")
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """Get presigned URL for temporary access."""
        if not self.enabled or not self.client:
            logger.warning(f"Storage disabled, returning mock URL for: {object_name}")
            return f"#storage-disabled/{object_name}"
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires_seconds)
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return f"#error/{object_name}"
    
    def delete_file(self, object_name: str):
        """Delete file from storage."""
        if not self.enabled or not self.client:
            logger.warning(f"Storage disabled, cannot delete file: {object_name}")
            return
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            # Não quebrar se não conseguir deletar


# Inicializar storage_service de forma segura
try:
    storage_service = StorageService()
except Exception as e:
    logger.error(f"Failed to initialize storage service: {e}")
    # Criar um objeto mock que não quebra
    class MockStorage:
        enabled = False
        def upload_file(self, file_bytes, object_name, content_type):
            return f"mock/{object_name}"
        def get_file(self, object_name):
            raise FileNotFoundError("Storage is disabled, file not available")
        def get_presigned_url(self, object_name, expires_seconds=3600):
            return "#storage-disabled"
        def delete_file(self, object_name):
            pass
    storage_service = MockStorage()

