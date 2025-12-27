# Image Storage Architecture

## Overview

StylistAI uses a **multi-layer storage approach** for outfit images, combining local file storage, vector embeddings, and structured metadata.

## Storage Layers

### 1. **Local File Storage** (Primary for POC)
```
📁 project_root/
  📁 uploads/
    📁 outfits/
      📁 user_firebase_uid_1/
        📄 image_id_1_photo1.jpg
        📄 image_id_2_photo2.jpg
      📁 user_firebase_uid_2/
        📄 image_id_3_photo1.jpg
```

**Location**: `uploads/outfits/{user_id}/{image_id}_{filename}`

**Access URL**: `http://localhost:8000/uploads/outfits/{user_id}/{image_id}_{filename}`

**Example**:
- File path: `uploads/outfits/yCVT46fVV7RWJ0IynQ1UHffYRMl1/user123_abc123_blazer.jpg`
- Access URL: `http://localhost:8000/uploads/outfits/yCVT46fVV7RWJ0IynQ1UHffYRMl1/user123_abc123_blazer.jpg`

**Why Local Storage?**
- ✅ Perfect for POC/Demo
- ✅ No cloud setup required
- ✅ Zero cost
- ✅ Fast development
- ✅ Easy debugging (can see files directly)

**Storage Service**: `app/services/local_storage_service.py`

---

### 2. **ChromaDB** (Vector Embeddings + Minimal Metadata)

**Purpose**: Semantic similarity search

**What's Stored**:
```json
{
  "id": "user123_abc123",
  "embedding": [512-dimensional vector from CLIP],
  "metadata": {
    "filename": "blazer.jpg",
    "user_id": "user123",
    "local_path": "uploads/outfits/user123/user123_abc123_blazer.jpg",
    "gcs_url": null,
    "source": "onboarding"
  }
}
```

**Why ChromaDB?**
- Fast vector similarity search
- Find visually similar outfits
- Search by text queries (CLIP text embeddings)

**Service**: `app/services/vectordb_service.py`

---

### 3. **PostgreSQL** (Structured Metadata)

**Table**: `outfits`

**What's Stored**:
```sql
id                  | UUID (primary key)
user_uid            | VARCHAR (FK to users.uid)
image_id            | VARCHAR (unique, matches ChromaDB ID)
filename            | VARCHAR (original filename)
gcs_url             | TEXT (Google Cloud Storage URL, nullable)
local_path          | TEXT (local file path, nullable)
file_size           | INT (bytes)
mime_type           | VARCHAR (image/jpeg, image/png, etc.)
width, height       | INT (dimensions in pixels)
tags                | JSON (["casual", "work", "summer"])
description         | TEXT (user-provided description)
occasion            | VARCHAR ("work", "casual", "formal")
season              | VARCHAR ("spring", "summer", "fall", "winter")
ai_description      | TEXT (AI-generated description)
ai_tags             | JSON (AI-detected tags)
dominant_colors     | JSON (["navy", "white"])
embedding_stored    | BOOLEAN (true if vector exists in ChromaDB)
embedding_dimensions| INT (512 for CLIP)
source              | VARCHAR ("onboarding", "upload", "camera")
uploaded_at         | TIMESTAMP
is_deleted          | BOOLEAN (soft delete)
```

**Why PostgreSQL?**
- Queryable metadata for frontend
- Filtering (by occasion, season, tags)
- Pagination for gallery views
- Relationships (user → outfits)

**Service**: Uses SQLAlchemy ORM (`app/models/db_models.py`)

---

## Image Upload Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. User uploads image via /onboarding/upload-photos       │
│     - Frontend sends multipart/form-data                    │
│     - Backend receives bytes + filename                     │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Generate CLIP Embedding (512-D vector)                  │
│     - app/services/image_service.py:generate_image_embedding│
│     - Uses openai/clip-vit-base-patch32 model              │
│     - Takes ~0.5-1s per image (CPU)                         │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Try Google Cloud Storage Upload                         │
│     - app/services/storage_service.py                       │
│     - IF configured: Upload to GCS bucket                   │
│     - IF NOT configured: Skip (POC doesn't need this)       │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Fallback to Local Storage                               │
│     - app/services/local_storage_service.py                 │
│     - Save to: uploads/outfits/{user_id}/{image_id}_{filename}│
│     - Create user directory if doesn't exist                │
│     - Returns local_path string                             │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  5. Store in ChromaDB                                       │
│     - ID: image_id                                          │
│     - Embedding: 512-D vector                               │
│     - Metadata: {filename, user_id, local_path, gcs_url}   │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  6. Store in PostgreSQL                                     │
│     - INSERT INTO outfits (...)                             │
│     - Saves all metadata, paths, dimensions                 │
│     - Links to user via user_uid                            │
└─────────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│  7. Return Success Response                                 │
│     {                                                       │
│       "image_id": "user123_abc123",                         │
│       "filename": "blazer.jpg",                             │
│       "gcs_url": null,                                      │
│       "local_path": "uploads/outfits/...",                  │
│       "embedding_dims": 512                                 │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Image Retrieval Flow

### **Scenario 1: Search Similar Outfits**
```
User asks: "Show me business casual outfits"
    ↓
1. Generate text embedding with CLIP
   embedding = clip.encode_text("business casual outfits")
    ↓
2. Query ChromaDB for similar vectors
   results = chromadb.query(embedding, where={"user_id": user_id}, n=5)
   → Returns: [image_id_1, image_id_2, ...]
    ↓
3. Get full metadata from PostgreSQL
   SELECT * FROM outfits WHERE image_id IN (...)
   → Returns: local_path, gcs_url, tags, etc.
    ↓
4. Build image URLs for frontend
   - If gcs_url exists: use gcs_url
   - Else: http://localhost:8000/{local_path}
    ↓
5. Return to frontend with image URLs
```

### **Scenario 2: Display User Gallery**
```
User wants to see all their outfits
    ↓
1. Query PostgreSQL
   SELECT * FROM outfits
   WHERE user_uid = ? AND is_deleted = false
   ORDER BY uploaded_at DESC
   LIMIT 20 OFFSET 0
    ↓
2. Build image URLs from local_path or gcs_url
    ↓
3. Return gallery with pagination
```

---

## Storage Service Implementations

### **LocalStorageService** (`app/services/local_storage_service.py`)

**Methods**:
```python
# Save image to local filesystem
save_image(image_bytes, filename, user_id, folder="outfits") -> str
  └─ Returns: "uploads/outfits/user123/image.jpg"

# Delete image from filesystem
delete_image(file_path) -> bool

# Get URL for accessing image
get_image_url(file_path, base_url) -> str
  └─ Returns: "http://localhost:8000/uploads/outfits/user123/image.jpg"

# Check if image exists
image_exists(file_path) -> bool

# List all images for a user
get_user_images(user_id, folder="outfits") -> List[str]

# Get storage statistics
get_storage_info() -> dict
```

### **StorageService** (`app/services/storage_service.py`)

**Methods** (for GCS, when configured):
```python
# Upload to Google Cloud Storage
upload_image(image_bytes, filename, user_id, folder) -> str
  └─ Returns: "https://storage.googleapis.com/bucket/path/image.jpg"

# Delete from GCS
delete_image(blob_path) -> bool

# Get public URL
get_image_url(blob_path) -> str
```

---

## Configuration

### **Local Storage** (Current - POC)
```bash
# .env - No configuration needed!
# Local storage works out of the box
```

### **Google Cloud Storage** (Future - Production)
```bash
# .env
GCS_BUCKET_NAME=stylistai-outfits
GCS_CREDENTIALS_PATH=./gcs-credentials.json
GCS_PROJECT_ID=stylistai-db968
```

---

## File Structure

```
StylistAI/
├── uploads/                          # Created automatically
│   └── outfits/                      # Outfit images
│       ├── user_id_1/
│       │   ├── img_1.jpg
│       │   └── img_2.jpg
│       └── user_id_2/
│           └── img_1.jpg
├── app/
│   ├── services/
│   │   ├── local_storage_service.py  # Local file storage
│   │   ├── storage_service.py        # GCS storage
│   │   ├── image_service.py          # Image processing + CLIP
│   │   └── vectordb_service.py       # ChromaDB operations
│   └── models/
│       └── db_models.py              # Outfit SQLAlchemy model
└── .env
```

---

## Access Images in Frontend

### **Example: Display User's Outfits**

```javascript
// Fetch user's outfits
const response = await fetch('/api/outfits', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const outfits = await response.json();

// Display images
outfits.forEach(outfit => {
  const imageUrl = outfit.gcs_url ||
                   `http://localhost:8000/${outfit.local_path}`;

  // Create img element
  const img = document.createElement('img');
  img.src = imageUrl;
  img.alt = outfit.description;
});
```

### **Example: Search Results**

```javascript
// Search for outfits
const response = await fetch('/styling/query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ query: "business casual outfit" })
});

const results = await response.json();

// results.similar_outfits contains metadata with local_path/gcs_url
results.similar_outfits.forEach(outfit => {
  const imageUrl = `http://localhost:8000/${outfit.local_path}`;
  // Display image
});
```

---

## Migration Path: Local → Cloud

When ready to move to production:

1. **Set up GCS** (or AWS S3, Azure Blob):
   ```bash
   # Create bucket
   gsutil mb gs://stylistai-outfits

   # Configure .env
   GCS_BUCKET_NAME=stylistai-outfits
   GCS_CREDENTIALS_PATH=./gcs-credentials.json
   GCS_PROJECT_ID=stylistai-db968
   ```

2. **Upload existing files to cloud**:
   ```python
   # Migration script
   for outfit in db.query(Outfit).all():
       if outfit.local_path and not outfit.gcs_url:
           with open(outfit.local_path, 'rb') as f:
               gcs_url = await StorageService.upload_image(...)
           outfit.gcs_url = gcs_url
           db.commit()
   ```

3. **Update frontend to prefer GCS URLs**:
   ```javascript
   const imageUrl = outfit.gcs_url || outfit.local_path;
   ```

4. **Keep local storage as backup/fallback**

---

## Summary

| Storage Type | What's Stored | Primary Use |
|--------------|---------------|-------------|
| **Local Files** | JPG/PNG image bytes | POC, Development, Image display |
| **ChromaDB** | 512-D vectors + minimal metadata | Semantic similarity search |
| **PostgreSQL** | Image metadata, paths, tags | Queries, filtering, frontend data |
| **GCS** (future) | JPG/PNG image bytes | Production, scalability, CDN |

**Current Architecture**: ✅ Ready for POC
**Migration Path**: ✅ Easy upgrade to cloud when needed

**Images are accessible at**: `http://localhost:8000/uploads/outfits/{user_id}/{image_id}_{filename}`
