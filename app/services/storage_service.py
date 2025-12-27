"""
Google Cloud Storage Service for StylistAI
Handles image upload to GCS bucket
"""

import logging
from typing import Optional
from google.cloud import storage
from app.config import settings
import os

logger = logging.getLogger(__name__)

# Global storage client
_storage_client = None


def get_storage_client():
    """Get or create GCS storage client"""
    global _storage_client

    if _storage_client is None:
        try:
            # Set credentials
            if settings.GCS_CREDENTIALS_PATH and os.path.exists(settings.GCS_CREDENTIALS_PATH):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GCS_CREDENTIALS_PATH

            _storage_client = storage.Client(project=settings.GCS_PROJECT_ID)
            logger.info(f"GCS client initialized for project: {settings.GCS_PROJECT_ID}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {str(e)}")
            raise

    return _storage_client


class StorageService:
    """Service for Google Cloud Storage operations"""

    @staticmethod
    async def upload_image(
        image_bytes: bytes,
        filename: str,
        user_id: str,
        folder: str = "outfits"
    ) -> str:
        """
        Upload image to GCS bucket

        Args:
            image_bytes: Image file bytes
            filename: Filename to use in GCS
            user_id: User ID (used for organizing files)
            folder: Folder/prefix in bucket

        Returns:
            Public URL of uploaded image
        """
        try:
            client = get_storage_client()
            bucket = client.bucket(settings.GCS_BUCKET_NAME)

            # Create blob path: folder/user_id/filename
            blob_path = f"{folder}/{user_id}/{filename}"
            blob = bucket.blob(blob_path)

            # Upload
            blob.upload_from_string(
                image_bytes,
                content_type='image/jpeg'  # Adjust based on actual type
            )

            # Make public (optional - configure based on security needs)
            # blob.make_public()

            # Get public URL
            public_url = f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{blob_path}"

            logger.info(f"Uploaded image to GCS: {blob_path}")
            return public_url

        except Exception as e:
            logger.error(f"Error uploading to GCS: {str(e)}")
            raise

    @staticmethod
    async def delete_image(blob_path: str) -> bool:
        """
        Delete image from GCS

        Args:
            blob_path: Full path to blob in bucket

        Returns:
            True if successful
        """
        try:
            client = get_storage_client()
            bucket = client.bucket(settings.GCS_BUCKET_NAME)
            blob = bucket.blob(blob_path)
            blob.delete()

            logger.info(f"Deleted image from GCS: {blob_path}")
            return True

        except Exception as e:
            logger.error(f"Error deleting from GCS: {str(e)}")
            return False

    @staticmethod
    async def get_image_url(blob_path: str) -> Optional[str]:
        """
        Get public URL for an image

        Args:
            blob_path: Full path to blob in bucket

        Returns:
            Public URL or None if not found
        """
        try:
            return f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{blob_path}"
        except Exception as e:
            logger.error(f"Error getting image URL: {str(e)}")
            return None
