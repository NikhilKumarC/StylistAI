"""
Image Processing Service for StylistAI
Handles image upload, CLIP embeddings generation, and storage
"""

import logging
import io
import uuid
from typing import List, Dict, Optional
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from app.config import settings

logger = logging.getLogger(__name__)

# Global CLIP model (loaded once)
_clip_model = None
_clip_processor = None


def get_clip_model():
    """Load CLIP model (lazy loading)"""
    global _clip_model, _clip_processor

    if _clip_model is None:
        logger.info("Loading CLIP model...")
        _clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        _clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        logger.info("CLIP model loaded successfully")

    return _clip_model, _clip_processor


def generate_image_embedding(image_bytes: bytes) -> List[float]:
    """
    Generate CLIP embedding for an image

    Args:
        image_bytes: Image file bytes

    Returns:
        List of floats representing the image embedding (512 dimensions)
    """
    try:
        # Load CLIP model
        model, processor = get_clip_model()

        # Open image
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Process image
        inputs = processor(images=image, return_tensors="pt")

        # Generate embedding
        with torch.no_grad():
            image_features = model.get_image_features(**inputs)

        # Convert to list and normalize
        embedding = image_features[0].cpu().numpy().tolist()

        logger.info(f"Generated CLIP embedding with {len(embedding)} dimensions")
        return embedding

    except Exception as e:
        logger.error(f"Error generating image embedding: {str(e)}")
        raise


def generate_text_embedding(text: str) -> List[float]:
    """
    Generate CLIP embedding for text query

    Args:
        text: Text query (e.g., "business casual outfit")

    Returns:
        List of floats representing the text embedding (512 dimensions)
    """
    try:
        # Load CLIP model
        model, processor = get_clip_model()

        # Process text
        inputs = processor(text=[text], return_tensors="pt", padding=True)

        # Generate embedding
        with torch.no_grad():
            text_features = model.get_text_features(**inputs)

        # Convert to list and normalize
        embedding = text_features[0].cpu().numpy().tolist()

        logger.info(f"Generated text embedding for: {text}")
        return embedding

    except Exception as e:
        logger.error(f"Error generating text embedding: {str(e)}")
        raise


class ImageService:
    """Service for handling image upload, processing, and storage"""

    @staticmethod
    async def process_outfit_image(
        image_bytes: bytes,
        filename: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Process an outfit image: generate embedding, upload to GCS, store in ChromaDB

        Args:
            image_bytes: Image file bytes
            filename: Original filename
            user_id: User ID
            metadata: Optional metadata (occasion, color, etc.)

        Returns:
            Dict with image info and embedding
        """
        try:
            # Generate unique image ID
            image_id = f"{user_id}_{uuid.uuid4().hex[:8]}"

            logger.info(f"Processing image {filename} for user {user_id}")

            # 1. Generate CLIP embedding
            embedding = generate_image_embedding(image_bytes)

            # 2. Save image file (try GCS first, fallback to local storage)
            gcs_url = None
            local_path = None

            # Try GCS upload (if configured)
            try:
                from app.services.storage_service import StorageService
                gcs_url = await StorageService.upload_image(
                    image_bytes=image_bytes,
                    filename=f"{image_id}_{filename}",
                    user_id=user_id
                )
                logger.info(f"Uploaded to GCS: {gcs_url}")
            except Exception as e:
                logger.warning(f"GCS upload failed, will use local storage: {str(e)}")

            # Fallback to local storage if GCS failed (or use local for POC)
            if gcs_url is None:
                try:
                    from app.services.local_storage_service import LocalStorageService
                    local_path = LocalStorageService.save_image(
                        image_bytes=image_bytes,
                        filename=f"{image_id}_{filename}",
                        user_id=user_id,
                        folder="outfits"
                    )
                    logger.info(f"Saved to local storage: {local_path}")
                except Exception as e:
                    logger.error(f"Local storage also failed: {str(e)}")
                    # Continue without file storage (at least we have embeddings)

            # 3. Store in ChromaDB
            try:
                from app.services.vectordb_service import VectorDBService

                # Build metadata, filtering out None values (ChromaDB doesn't accept None)
                chroma_metadata = {
                    "filename": filename,
                    "user_id": user_id,
                    **(metadata or {})
                }

                # Add storage URLs/paths if available
                if gcs_url is not None:
                    chroma_metadata["gcs_url"] = gcs_url
                if local_path is not None:
                    chroma_metadata["local_path"] = local_path

                await VectorDBService.add_outfit_image(
                    image_id=image_id,
                    embedding=embedding,
                    user_id=user_id,
                    metadata=chroma_metadata
                )
                logger.info(f"Stored in ChromaDB: {image_id}")
            except Exception as e:
                logger.warning(f"ChromaDB storage failed, continuing without it: {str(e)}")

            # 4. Save outfit metadata to PostgreSQL
            try:
                from app.models.db_models import Outfit
                from app.database import SessionLocal
                from datetime import datetime
                from PIL import Image
                import io

                # Get image dimensions
                img = Image.open(io.BytesIO(image_bytes))
                width, height = img.size

                db = SessionLocal()
                outfit = Outfit(
                    id=str(uuid.uuid4()),
                    user_uid=user_id,
                    image_id=image_id,
                    filename=filename,
                    gcs_url=gcs_url,
                    local_path=local_path,  # Add local path
                    file_size=len(image_bytes),
                    mime_type=f"image/{img.format.lower()}" if img.format else "image/jpeg",
                    width=width,
                    height=height,
                    embedding_stored=True,
                    embedding_dimensions=len(embedding),
                    source=metadata.get("source") if metadata else None,
                    tags=metadata.get("tags") if metadata else None,
                    description=metadata.get("description") if metadata else None,
                    occasion=metadata.get("occasion") if metadata else None,
                    season=metadata.get("season") if metadata else None
                )
                db.add(outfit)
                db.commit()
                db.close()
                logger.info(f"Saved outfit to PostgreSQL: {image_id} (gcs_url={gcs_url}, local_path={local_path})")
            except Exception as e:
                logger.warning(f"PostgreSQL save failed, continuing without it: {str(e)}")

            return {
                "image_id": image_id,
                "filename": filename,
                "gcs_url": gcs_url,
                "embedding_dims": len(embedding),
                "user_id": user_id,
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise

    @staticmethod
    async def process_multiple_images(
        images: List[tuple],  # List of (bytes, filename) tuples
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Process multiple outfit images

        Args:
            images: List of (image_bytes, filename) tuples
            user_id: User ID
            metadata: Optional shared metadata

        Returns:
            List of processed image info dicts
        """
        results = []

        for image_bytes, filename in images:
            try:
                result = await ImageService.process_outfit_image(
                    image_bytes=image_bytes,
                    filename=filename,
                    user_id=user_id,
                    metadata=metadata
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                results.append({
                    "filename": filename,
                    "error": str(e),
                    "status": "failed"
                })

        return results

    @staticmethod
    async def search_similar_outfits(
        query: str,
        user_id: str,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Search for similar outfits using text query

        Args:
            query: Text query (e.g., "casual business outfit")
            user_id: User ID to search within their wardrobe
            n_results: Number of results to return

        Returns:
            List of similar outfits with metadata
        """
        try:
            # Generate text embedding
            query_embedding = generate_text_embedding(query)

            # Search in ChromaDB
            from app.services.vectordb_service import VectorDBService
            results = await VectorDBService.search_similar_outfits(
                query_embedding=query_embedding,
                user_id=user_id,
                n_results=n_results
            )

            logger.info(f"Found {len(results)} similar outfits for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error searching similar outfits: {str(e)}")
            return []

    @staticmethod
    def validate_image(image_bytes: bytes) -> tuple[bool, Optional[str]]:
        """
        Validate image file

        Args:
            image_bytes: Image file bytes

        Returns:
            (is_valid, error_message)
        """
        try:
            # Check size
            size_mb = len(image_bytes) / (1024 * 1024)
            if size_mb > settings.MAX_IMAGE_SIZE_MB:
                return False, f"Image too large: {size_mb:.1f}MB (max {settings.MAX_IMAGE_SIZE_MB}MB)"

            # Check if it's a valid image
            try:
                image = Image.open(io.BytesIO(image_bytes))
                image.verify()
            except Exception:
                return False, "Invalid image file"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"
