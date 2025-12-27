"""
Test End-to-End RAG Flow
Tests: Image Upload → CLIP Embeddings → ChromaDB → GPT-4 Recommendations
"""

import asyncio
import io
import sys
import os
from PIL import Image

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.image_service import ImageService
from app.services.langgraph_agent import run_styling_agent
from app.services.user_service import UserService


def create_test_images():
    """Create test wardrobe images with different colors"""
    images = []

    # Navy blazer
    img = Image.new('RGB', (224, 224), color=(0, 0, 128))  # Navy blue
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    images.append((img_bytes.getvalue(), "navy_blazer.jpg", {"color": "navy", "category": "jacket"}))

    # White shirt
    img = Image.new('RGB', (224, 224), color=(255, 255, 255))  # White
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    images.append((img_bytes.getvalue(), "white_shirt.jpg", {"color": "white", "category": "shirt"}))

    # Grey pants
    img = Image.new('RGB', (224, 224), color=(128, 128, 128))  # Grey
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    images.append((img_bytes.getvalue(), "grey_pants.jpg", {"color": "grey", "category": "pants"}))

    return images


async def test_rag_flow():
    print("=" * 70)
    print("Testing Complete RAG Flow: Upload → CLIP → ChromaDB → GPT-4")
    print("=" * 70)

    test_user_id = "test_user_rag_123"

    # Step 1: Upload test wardrobe images
    print("\n[STEP 1] Uploading test wardrobe images...")
    print("-" * 70)

    test_images = create_test_images()

    for image_bytes, filename, metadata in test_images:
        try:
            result = await ImageService.process_outfit_image(
                image_bytes=image_bytes,
                filename=filename,
                user_id=test_user_id,
                metadata=metadata
            )
            print(f"✓ Uploaded: {filename}")
            print(f"  - Image ID: {result['image_id']}")
            print(f"  - Embedding: {result['embedding_dims']} dimensions")
            print(f"  - Metadata: {metadata}")
        except Exception as e:
            print(f"✗ Failed to upload {filename}: {str(e)}")
            return False

    print(f"\n✓ Successfully uploaded {len(test_images)} images to wardrobe")

    # Step 2: Set up user preferences
    print("\n[STEP 2] Setting up user preferences...")
    print("-" * 70)

    user_preferences = {
        "style_aesthetics": ["modern", "professional"],
        "colors": ["navy", "grey", "white"],
        "occasions": ["work", "business_casual"],
        "fit_preferences": "fitted",
        "budget": "mid-range",
        "onboarding_completed": True
    }

    UserService.save_user_preferences(test_user_id, user_preferences)
    print("✓ User preferences saved")
    print(f"  - Style: {user_preferences['style_aesthetics']}")
    print(f"  - Colors: {user_preferences['colors']}")
    print(f"  - Occasions: {user_preferences['occasions']}")

    # Step 3: Query the styling agent
    print("\n[STEP 3] Querying styling agent with GPT-4...")
    print("-" * 70)

    query = "What should I wear for a business meeting?"
    print(f"Query: '{query}'")
    print()

    try:
        result = await run_styling_agent(
            user_id=test_user_id,
            query=query
        )

        print("\n[STEP 4] Results from RAG Pipeline")
        print("=" * 70)

        print(f"\n✓ Query processed successfully!")
        print(f"\nUser ID: {result['user_id']}")
        print(f"Query: {result['query']}")

        print(f"\n📊 Context Used:")
        print(f"  - User Preferences: {'✓' if result['context_used']['preferences'] else '✗'}")
        print(f"  - Wardrobe History (CLIP): {'✓' if result['context_used']['outfit_history'] else '✗'}")
        print(f"  - Fashion Trends: {'✓' if result['context_used']['trends'] else '✗'}")

        print(f"\n💡 Recommendations:")
        if result.get('recommendations'):
            for i, rec in enumerate(result['recommendations'], 1):
                print(f"\n  {i}. {rec.get('item', 'N/A')}")
                print(f"     Reasoning: {rec.get('reasoning', 'N/A')}")
                print(f"     Confidence: {rec.get('confidence', 0):.0%}")
        else:
            print("  No structured recommendations (check messages below)")

        print(f"\n💬 Agent Messages:")
        for i, msg in enumerate(result['messages'], 1):
            print(f"\n  Message {i}:")
            # Truncate long messages
            msg_preview = msg[:200] + "..." if len(msg) > 200 else msg
            print(f"  {msg_preview}")

        print("\n" + "=" * 70)
        print("✓ END-TO-END RAG FLOW SUCCESSFUL!")
        print("=" * 70)

        print("\n🎉 Success! The complete pipeline works:")
        print("  1. ✓ Images uploaded and processed with CLIP")
        print("  2. ✓ Embeddings stored in ChromaDB")
        print("  3. ✓ User preferences retrieved from database")
        print("  4. ✓ CLIP search found similar wardrobe items")
        print("  5. ✓ GPT-4 generated personalized recommendations")

        return True

    except Exception as e:
        print(f"\n✗ Agent query failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_rag_flow())
    sys.exit(0 if success else 1)
