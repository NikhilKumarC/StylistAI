#!/usr/bin/env python3
"""
Database Status Checker for StylistAI

This script checks the status of both PostgreSQL and ChromaDB databases,
showing counts, sample data, and verifying that the system is working correctly.

Usage:
    python utils/check_database.py

    Or from project root:
    python -m utils.check_database
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from app.config import settings
from app.services.vectordb_service import get_outfit_collection


def print_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")


def check_postgresql():
    """Check PostgreSQL database status"""
    print_header("POSTGRESQL DATABASE")

    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()

        # Get all tables
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()

        print(f"📊 Found {len(tables)} tables:\n")

        total_rows = 0
        for table in tables:
            table_name = table[0]

            # Count rows in each table
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cur.fetchone()[0]
            total_rows += count

            print(f"   ✓ {table_name}: {count} rows")

        print(f"\n   Total rows across all tables: {total_rows}")

        # User preferences details
        print_header("USER PREFERENCES")

        cur.execute("""
            SELECT
                user_uid,
                style_aesthetics,
                colors,
                occasions,
                budget,
                CASE WHEN style_aesthetics IS NOT NULL THEN 'Complete' ELSE 'Incomplete' END as status
            FROM user_preferences
            ORDER BY updated_at DESC;
        """)

        prefs = cur.fetchall()

        if prefs:
            for i, pref in enumerate(prefs, 1):
                user_id = pref[0][:30]
                status = pref[5]
                print(f"{i}. User: {user_id}")
                print(f"   Status: {status}")
                if pref[1]:
                    print(f"   Style: {pref[1]}")
                    print(f"   Colors: {pref[2]}")
                    print(f"   Occasions: {pref[3]}")
                    print(f"   Budget: {pref[4]}")
                print()

        # Outfit images details
        print_header("OUTFIT IMAGES")

        cur.execute("""
            SELECT
                user_uid,
                filename,
                embedding_stored,
                uploaded_at
            FROM outfits
            ORDER BY uploaded_at DESC
            LIMIT 10;
        """)

        outfits = cur.fetchall()

        if outfits:
            print(f"Showing 10 most recent images:\n")
            for i, outfit in enumerate(outfits, 1):
                user_id = outfit[0][:30]
                filename = outfit[1]
                embedding = "✅" if outfit[2] else "❌"
                uploaded = outfit[3].strftime('%Y-%m-%d %H:%M')

                print(f"{i}. {filename}")
                print(f"   User: {user_id} | Embedding: {embedding} | Uploaded: {uploaded}")
        else:
            print("⚠️  No outfit images found")

        # Photos by user
        print_header("PHOTOS BY USER")

        cur.execute("""
            SELECT user_uid, COUNT(*) as photo_count
            FROM outfits
            GROUP BY user_uid
            ORDER BY photo_count DESC;
        """)

        user_counts = cur.fetchall()
        if user_counts:
            for user_uid, count in user_counts:
                print(f"   {user_uid[:40]}: {count} photos")
        else:
            print("   No photos uploaded yet")

        # Embedding stats
        print_header("EMBEDDING STATISTICS")

        cur.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN embedding_stored THEN 1 ELSE 0 END) as with_embeddings,
                SUM(CASE WHEN NOT embedding_stored THEN 1 ELSE 0 END) as without_embeddings
            FROM outfits;
        """)

        stats = cur.fetchone()
        if stats and stats[0] > 0:
            print(f"   Total images: {stats[0]}")
            print(f"   With embeddings: {stats[1]} ✅")
            print(f"   Without embeddings: {stats[2]} {'⚠️' if stats[2] > 0 else '✅'}")

            percentage = (stats[1] / stats[0] * 100) if stats[0] > 0 else 0
            print(f"   Completion rate: {percentage:.1f}%")
        else:
            print("   No images uploaded yet")

        cur.close()
        conn.close()

        return True

    except Exception as e:
        print(f"❌ Error accessing PostgreSQL: {str(e)}")
        return False


def check_chromadb():
    """Check ChromaDB vector database status"""
    print_header("CHROMADB (VECTOR DATABASE)")

    try:
        collection = get_outfit_collection()

        # Get collection stats
        count = collection.count()
        print(f"✅ Collection Name: 'outfit_images'")
        print(f"   Total vector embeddings: {count}\n")

        if count > 0:
            # Get sample data
            results = collection.get(limit=5, include=['metadatas'])

            print(f"📊 Sample entries:\n")

            for i, (img_id, metadata) in enumerate(zip(results['ids'], results['metadatas']), 1):
                user_id = metadata.get('user_id', 'Unknown')[:30]
                filename = metadata.get('filename', 'Unknown')
                source = metadata.get('source', 'Unknown')

                print(f"{i}. {filename}")
                print(f"   User: {user_id}")
                print(f"   Image ID: {img_id[:50]}")
                print(f"   Source: {source}")
                print()

            # Count by user
            print_header("EMBEDDINGS BY USER")

            all_results = collection.get(include=['metadatas'])
            user_counts = {}
            for metadata in all_results['metadatas']:
                user_id = metadata.get('user_id', 'Unknown')
                user_counts[user_id] = user_counts.get(user_id, 0) + 1

            for user_id, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   {user_id[:40]}: {count} embeddings")

            print(f"\n   Embedding dimensions: 512 (CLIP)")
            print(f"   Distance metric: Cosine similarity")
        else:
            print("⚠️  No embeddings found in ChromaDB")
            print("   Upload some wardrobe photos to populate the vector database")

        return True

    except Exception as e:
        print(f"❌ Error accessing ChromaDB: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_system_health():
    """Overall system health check"""
    print_header("SYSTEM HEALTH CHECK")

    postgres_ok = False
    chromadb_ok = False

    print("Checking databases...")

    try:
        # Check PostgreSQL connection
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()
        postgres_ok = True
        print("   ✅ PostgreSQL: Connected")
    except Exception as e:
        print(f"   ❌ PostgreSQL: Failed - {str(e)}")

    try:
        # Check ChromaDB connection
        collection = get_outfit_collection()
        collection.count()
        chromadb_ok = True
        print("   ✅ ChromaDB: Connected")
    except Exception as e:
        print(f"   ❌ ChromaDB: Failed - {str(e)}")

    print()

    if postgres_ok and chromadb_ok:
        print("   🎉 All systems operational!")
        return True
    else:
        print("   ⚠️  Some systems are not working correctly")
        return False


def main():
    """Main function"""
    print("\n" + "🔍 STYLISTAI DATABASE STATUS CHECKER 🔍".center(80))

    # System health check
    health_ok = check_system_health()

    if health_ok:
        # PostgreSQL check
        check_postgresql()

        # ChromaDB check
        check_chromadb()

        # Summary
        print_header("SUMMARY")
        print("✅ Database check complete!")
        print("\nWhat this means:")
        print("   • PostgreSQL stores user data, preferences, and image metadata")
        print("   • ChromaDB stores 512-dimensional CLIP embeddings for similarity search")
        print("   • When users ask for outfit recommendations, the system:")
        print("     1. Converts their query to a CLIP embedding")
        print("     2. Searches ChromaDB for similar wardrobe items")
        print("     3. Returns the most relevant outfits based on semantic similarity")
        print("\n" + "=" * 80 + "\n")
    else:
        print("\n" + "=" * 80)
        print("⚠️  Please fix database connection issues before proceeding")
        print("=" * 80 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
