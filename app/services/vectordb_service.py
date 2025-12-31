"""
ChromaDB Vector Database Service for StylistAI
Handles vector embeddings storage and similarity search
"""

import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

logger = logging.getLogger(__name__)

# Global ChromaDB client
_chroma_client = None
_outfit_collection = None


def get_chroma_client():
    """Get or create ChromaDB client"""
    global _chroma_client

    if _chroma_client is None:
        try:
            # Use HTTP client for Docker/Cloud ChromaDB
            if settings.CHROMA_HOST:
                # Parse host and port
                host_url = settings.CHROMA_HOST.replace("http://", "").replace("https://", "")
                if ":" in host_url:
                    host, port = host_url.split(":")
                else:
                    host = host_url
                    port = "8000"

                _chroma_client = chromadb.HttpClient(
                    host=host,
                    port=int(port)
                )
                logger.info(f"ChromaDB HTTP client initialized: {host}:{port}")
            else:
                # Use persistent local storage
                _chroma_client = chromadb.PersistentClient(
                    path=settings.CHROMA_PERSIST_DIR
                )
                logger.info(f"ChromaDB local client initialized: {settings.CHROMA_PERSIST_DIR}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
            raise

    return _chroma_client


def get_outfit_collection():
    """Get or create outfit embeddings collection"""
    global _outfit_collection

    if _outfit_collection is None:
        try:
            client = get_chroma_client()

            # Get or create collection
            _outfit_collection = client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"description": "User outfit image embeddings"}
            )
            logger.info(f"ChromaDB collection ready: {settings.CHROMA_COLLECTION_NAME}")

        except Exception as e:
            logger.error(f"Failed to get/create collection: {str(e)}")
            raise

    return _outfit_collection


class VectorDBService:
    """Service for vector database operations"""

    @staticmethod
    async def add_outfit_image(
        image_id: str,
        embedding: List[float],
        user_id: str,
        metadata: Dict
    ) -> bool:
        """
        Add outfit image embedding to ChromaDB

        Args:
            image_id: Unique image ID
            embedding: CLIP embedding vector (512 dimensions)
            user_id: User ID
            metadata: Image metadata (filename, URL, etc.)

        Returns:
            True if successful
        """
        try:
            collection = get_outfit_collection()

            # Add to collection
            collection.add(
                ids=[image_id],
                embeddings=[embedding],
                metadatas=[{
                    "user_id": user_id,
                    **metadata
                }]
            )

            logger.info(f"Added embedding to ChromaDB: {image_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding to ChromaDB: {str(e)}")
            return False

    @staticmethod
    async def search_similar_outfits(
        query_embedding: List[float],
        user_id: str,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Search for similar outfits using embedding

        Args:
            query_embedding: Query embedding vector
            user_id: User ID to filter results
            n_results: Number of results to return

        Returns:
            List of similar outfits with metadata and distances
        """
        try:
            collection = get_outfit_collection()

            # Search with user filter
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where={"user_id": user_id}  # Filter by user
            )

            # Format results
            outfits = []
            if results['ids'] and len(results['ids']) > 0:
                for i, image_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 0

                    # Convert distance to similarity score (0-1 range)
                    # For L2 distance on high-dimensional CLIP embeddings (512-768 dims):
                    # Distances can be very large (150-200+), so we need a larger scale factor
                    # e^(-distance/100) gives reasonable percentages for these large distances
                    import math
                    similarity = math.exp(-distance / 100.0)

                    logger.info(f"Image {i}: distance={distance:.4f}, similarity={similarity:.4f} ({similarity*100:.1f}%)")

                    outfits.append({
                        "image_id": image_id,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": distance,
                        "similarity": similarity
                    })

            logger.info(f"Found {len(outfits)} similar outfits for user: {user_id}")
            return outfits

        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            return []

    @staticmethod
    async def get_all_user_outfits(user_id: str) -> List[Dict]:
        """
        Get all outfits for a user

        Args:
            user_id: User ID

        Returns:
            List of all user's outfits
        """
        try:
            collection = get_outfit_collection()

            # Query with filter
            results = collection.get(
                where={"user_id": user_id}
            )

            # Format results
            outfits = []
            if results['ids']:
                for i, image_id in enumerate(results['ids']):
                    outfits.append({
                        "image_id": image_id,
                        "metadata": results['metadatas'][i] if results['metadatas'] else {}
                    })

            logger.info(f"Retrieved {len(outfits)} outfits for user: {user_id}")
            return outfits

        except Exception as e:
            logger.error(f"Error getting user outfits: {str(e)}")
            return []

    @staticmethod
    async def delete_outfit(image_id: str) -> bool:
        """
        Delete outfit from ChromaDB

        Args:
            image_id: Image ID to delete

        Returns:
            True if successful
        """
        try:
            collection = get_outfit_collection()
            collection.delete(ids=[image_id])

            logger.info(f"Deleted embedding from ChromaDB: {image_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting from ChromaDB: {str(e)}")
            return False

    @staticmethod
    async def get_collection_stats() -> Dict:
        """
        Get collection statistics

        Returns:
            Dict with collection stats
        """
        try:
            collection = get_outfit_collection()
            count = collection.count()

            return {
                "collection_name": settings.CHROMA_COLLECTION_NAME,
                "total_embeddings": count,
                "status": "healthy"
            }

        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                "collection_name": settings.CHROMA_COLLECTION_NAME,
                "status": "error",
                "error": str(e)
            }
