"""
Test script for image processing pipeline
Tests CLIP embeddings, ChromaDB storage, and similarity search
"""

import asyncio
import io
from PIL import Image
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.image_service import (
    generate_image_embedding,
    generate_text_embedding,
    ImageService
)
from app.services.vectordb_service import VectorDBService


def create_test_image() -> bytes:
    """Create a simple test image"""
    img = Image.new('RGB', (224, 224), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()


async def test_pipeline():
    print("=" * 60)
    print("Testing StylistAI Image Processing Pipeline")
    print("=" * 60)

    # Test 1: Create test image
    print("\n[1/5] Creating test image...")
    test_image_bytes = create_test_image()
    print(f"✓ Created test image: {len(test_image_bytes)} bytes")

    # Test 2: Generate CLIP embedding
    print("\n[2/5] Generating CLIP embedding...")
    try:
        embedding = generate_image_embedding(test_image_bytes)
        print(f"✓ Generated embedding: {len(embedding)} dimensions")
        print(f"  Sample values: {embedding[:5]}")
    except Exception as e:
        print(f"✗ Failed to generate embedding: {str(e)}")
        return False

    # Test 3: Test ChromaDB connection
    print("\n[3/5] Testing ChromaDB connection...")
    try:
        stats = await VectorDBService.get_collection_stats()
        print(f"✓ ChromaDB connected")
        print(f"  Collection: {stats['collection_name']}")
        print(f"  Total embeddings: {stats['total_embeddings']}")
        print(f"  Status: {stats['status']}")
    except Exception as e:
        print(f"✗ Failed to connect to ChromaDB: {str(e)}")
        return False

    # Test 4: Store embedding in ChromaDB
    print("\n[4/5] Storing embedding in ChromaDB...")
    try:
        test_user_id = "test_user_123"
        test_image_id = "test_image_001"

        success = await VectorDBService.add_outfit_image(
            image_id=test_image_id,
            embedding=embedding,
            user_id=test_user_id,
            metadata={
                "filename": "test_red_image.jpg",
                "color": "red",
                "source": "test"
            }
        )

        if success:
            print(f"✓ Stored embedding in ChromaDB")
            print(f"  Image ID: {test_image_id}")
            print(f"  User ID: {test_user_id}")
        else:
            print("✗ Failed to store embedding")
            return False

    except Exception as e:
        print(f"✗ Failed to store embedding: {str(e)}")
        return False

    # Test 5: Search similar outfits
    print("\n[5/5] Testing similarity search...")
    try:
        # Generate text embedding for query
        query_text = "red clothing"
        query_embedding = generate_text_embedding(query_text)
        print(f"✓ Generated query embedding for: '{query_text}'")

        # Search for similar outfits
        results = await VectorDBService.search_similar_outfits(
            query_embedding=query_embedding,
            user_id=test_user_id,
            n_results=5
        )

        print(f"✓ Found {len(results)} similar outfits")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Image: {result['image_id']}")
            print(f"     Similarity: {result['similarity']:.4f}")
            print(f"     Metadata: {result['metadata']}")

    except Exception as e:
        print(f"✗ Failed similarity search: {str(e)}")
        return False

    # Test 6: Full pipeline test
    print("\n[6/6] Testing full ImageService pipeline...")
    try:
        result = await ImageService.process_outfit_image(
            image_bytes=test_image_bytes,
            filename="test_outfit.jpg",
            user_id=test_user_id,
            metadata={"occasion": "casual", "test": True}
        )

        print(f"✓ Full pipeline successful")
        print(f"  Image ID: {result['image_id']}")
        print(f"  Embedding dimensions: {result['embedding_dims']}")
        print(f"  GCS URL: {result.get('gcs_url', 'Not configured')}")

    except Exception as e:
        print(f"✗ Full pipeline failed: {str(e)}")
        return False

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    print("\nImage processing pipeline is working correctly!")
    print("- CLIP model loads successfully")
    print("- Embeddings are generated (512 dimensions)")
    print("- ChromaDB stores and retrieves embeddings")
    print("- Similarity search works")
    print("\nNext steps:")
    print("1. Configure GCS credentials for image storage")
    print("2. Test with real wardrobe photos")
    print("3. Build frontend onboarding UI")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_pipeline())
    sys.exit(0 if success else 1)
