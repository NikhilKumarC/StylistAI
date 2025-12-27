"""
Local File Storage Service for StylistAI
Handles saving images to local filesystem (for POC/development)
"""

import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Base upload directory (relative to project root)
UPLOAD_BASE_DIR = "uploads"


class LocalStorageService:
    """Service for local file system storage operations"""

    @staticmethod
    def save_image(
        image_bytes: bytes,
        filename: str,
        user_id: str,
        folder: str = "outfits"
    ) -> str:
        """
        Save image to local filesystem in user-specific folder

        Args:
            image_bytes: Image file bytes
            filename: Filename to use
            user_id: User ID (creates user-specific folder)
            folder: Category folder (e.g., 'outfits', 'profile')

        Returns:
            Relative path to saved file (e.g., 'uploads/outfits/user_123/image.jpg')
        """
        try:
            # Create directory structure: uploads/outfits/user_id/
            user_dir = os.path.join(UPLOAD_BASE_DIR, folder, user_id)
            os.makedirs(user_dir, exist_ok=True)

            # Full file path
            file_path = os.path.join(user_dir, filename)

            # Save file
            with open(file_path, "wb") as f:
                f.write(image_bytes)

            logger.info(f"Saved image locally: {file_path} ({len(image_bytes)/1024:.1f}KB)")

            return file_path

        except Exception as e:
            logger.error(f"Error saving image locally: {str(e)}")
            raise

    @staticmethod
    def delete_image(file_path: str) -> bool:
        """
        Delete image from local filesystem

        Args:
            file_path: Relative path to file

        Returns:
            True if successful
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted local image: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error deleting local image: {str(e)}")
            return False

    @staticmethod
    def get_image_url(file_path: str, base_url: str = "http://localhost:8000") -> str:
        """
        Get URL to access the image via FastAPI static files

        Args:
            file_path: Relative path to file (e.g., 'uploads/outfits/user_123/image.jpg')
            base_url: Base URL of the API server

        Returns:
            Full URL to access the image (e.g., 'http://localhost:8000/uploads/outfits/user_123/image.jpg')
        """
        # Normalize path (convert backslashes to forward slashes for URLs)
        normalized_path = file_path.replace(os.sep, '/')
        return f"{base_url}/{normalized_path}"

    @staticmethod
    def image_exists(file_path: str) -> bool:
        """
        Check if image file exists

        Args:
            file_path: Relative path to file

        Returns:
            True if file exists
        """
        return os.path.exists(file_path)

    @staticmethod
    def get_user_images(user_id: str, folder: str = "outfits") -> list:
        """
        Get all images for a specific user

        Args:
            user_id: User ID
            folder: Category folder

        Returns:
            List of file paths
        """
        try:
            user_dir = os.path.join(UPLOAD_BASE_DIR, folder, user_id)

            if not os.path.exists(user_dir):
                return []

            # Get all image files
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
            images = []

            for filename in os.listdir(user_dir):
                file_path = os.path.join(user_dir, filename)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in image_extensions:
                        images.append(file_path)

            return images

        except Exception as e:
            logger.error(f"Error listing user images: {str(e)}")
            return []

    @staticmethod
    def get_storage_info() -> dict:
        """
        Get storage statistics

        Returns:
            Dict with storage info (total files, total size, etc.)
        """
        try:
            total_files = 0
            total_size = 0

            if os.path.exists(UPLOAD_BASE_DIR):
                for root, dirs, files in os.walk(UPLOAD_BASE_DIR):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            total_files += 1
                            total_size += os.path.getsize(file_path)

            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "base_directory": UPLOAD_BASE_DIR
            }

        except Exception as e:
            logger.error(f"Error getting storage info: {str(e)}")
            return {"error": str(e)}
