# Infrastructure Setup Guide

Complete guide for setting up GCS, ChromaDB, and PostgreSQL for StylistAI.

---

## 1. Google Cloud Storage (GCS) Configuration

### **Purpose**
Store uploaded wardrobe images persistently in the cloud.

### **Current Status**
⚠️ **Not configured** - Running without GCS (images stored in ChromaDB metadata only)

### **Setup Steps**

#### **Step 1: Create GCS Bucket**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Cloud Storage > Buckets**
3. Click **Create Bucket**
4. Configure:
   - **Name**: `stylistai-wardrobe-images` (must be globally unique)
   - **Location type**: Region (choose closest to your users)
   - **Storage class**: Standard
   - **Access control**: Uniform (recommended)
   - **Public access**: Prevent public access (we'll use signed URLs)

#### **Step 2: Create Service Account**

1. Navigate to **IAM & Admin > Service Accounts**
2. Click **Create Service Account**
3. Configure:
   - **Name**: `stylistai-storage`
   - **Role**: `Storage Object Admin`
4. Click **Create Key** → JSON format
5. Save the JSON file as `gcs-credentials.json` in your project root

#### **Step 3: Update .env Configuration**

```bash
# Google Cloud Storage
GCS_BUCKET_NAME=stylistai-wardrobe-images
GCS_CREDENTIALS_PATH=./gcs-credentials.json
GCS_PROJECT_ID=your-gcp-project-id
```

#### **Step 4: Test GCS Connection**

```bash
venv/bin/python -c "
from app.services.storage_service import StorageService
import asyncio

async def test():
    url = await StorageService.upload_image(
        image_bytes=b'test',
        filename='test.jpg',
        user_id='test_user'
    )
    print(f'Upload successful: {url}')

asyncio.run(test())
"
```

### **GCS Implementation Details**

**File**: `app/services/storage_service.py`

```python
class StorageService:
    @staticmethod
    async def upload_image(
        image_bytes: bytes,
        filename: str,
        user_id: str,
        folder: str = "outfits"
    ) -> str:
        """
        Upload to: gs://bucket-name/outfits/user_id/filename
        Returns: https://storage.googleapis.com/bucket-name/outfits/user_id/filename
        """
```

**Storage Structure**:
```
stylistai-wardrobe-images/
├── outfits/
│   ├── user_123/
│   │   ├── user_123_abc123_navy_blazer.jpg
│   │   ├── user_123_def456_white_shirt.jpg
│   │   └── user_123_ghi789_grey_pants.jpg
│   └── user_456/
│       └── user_456_xyz123_red_dress.jpg
```

**Cost Estimate**:
- Storage: ~$0.02/GB/month
- Operations: ~$0.05 per 10,000 operations
- For POC with 100 users, ~500 images: **~$0.10/month**

---

## 2. ChromaDB Configuration

### **Purpose**
Store CLIP vector embeddings (512 dimensions) for similarity search.

### **Current Status**
✅ **Configured and running** via Docker

### **Connection Details**

#### **Local Development**
```bash
# ChromaDB runs in Docker container
docker-compose up -d chromadb

# Connection URL
CHROMA_HOST=http://localhost:8001

# Data persisted to Docker volume: chroma_data
```

#### **Docker Compose Configuration**

**File**: `docker-compose.yml`

```yaml
chromadb:
  image: chromadb/chroma:latest
  container_name: stylistai_chromadb
  ports:
    - "8001:8000"  # Map internal 8000 to external 8001
  volumes:
    - chroma_data:/chroma/chroma  # Persistent storage
  environment:
    - IS_PERSISTENT=TRUE
    - ANONYMIZED_TELEMETRY=FALSE
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
```

#### **Environment Variables**

```bash
# .env file
CHROMA_HOST=http://localhost:8001
CHROMA_PERSIST_DIR=./chroma_db  # Fallback for local client
CHROMA_COLLECTION_NAME=outfits
```

### **ChromaDB Implementation**

**File**: `app/services/vectordb_service.py`

```python
def get_chroma_client():
    """Initialize ChromaDB HTTP client"""
    if settings.CHROMA_HOST:
        host, port = parse_host(settings.CHROMA_HOST)
        return chromadb.HttpClient(host=host, port=int(port))
    else:
        # Fallback to local persistent client
        return chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR
        )

def get_outfit_collection():
    """Get or create 'outfits' collection"""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="outfits",
        metadata={"description": "User outfit image embeddings"}
    )
```

### **ChromaDB Operations**

#### **Add Embedding**
```python
await VectorDBService.add_outfit_image(
    image_id="user_123_abc123",
    embedding=[0.23, -0.45, ...],  # 512 floats
    user_id="user_123",
    metadata={
        "filename": "navy_blazer.jpg",
        "color": "navy",
        "category": "jacket"
    }
)
```

#### **Search Similar**
```python
results = await VectorDBService.search_similar_outfits(
    query_embedding=[0.25, -0.43, ...],  # From CLIP
    user_id="user_123",
    n_results=5
)
# Returns: [{image_id, metadata, similarity}, ...]
```

#### **Get Stats**
```python
stats = await VectorDBService.get_collection_stats()
# {collection_name: "outfits", total_embeddings: 150, status: "healthy"}
```

### **Data Structure in ChromaDB**

| Field | Type | Example | Description |
|-------|------|---------|-------------|
| `id` | string | `user_123_abc123` | Unique image ID |
| `embedding` | float[512] | `[0.23, -0.45, ...]` | CLIP vector |
| `metadata.user_id` | string | `user_123` | Owner |
| `metadata.filename` | string | `navy_blazer.jpg` | Original name |
| `metadata.gcs_url` | string | `https://storage...` | Image URL |
| `metadata.color` | string | `navy` | Optional tag |
| `metadata.category` | string | `jacket` | Optional tag |

### **Testing ChromaDB**

```bash
# Check container status
docker-compose ps chromadb

# View logs
docker logs stylistai_chromadb

# Test connection
curl http://localhost:8001/api/v1/heartbeat
# Returns: {"nanosecond heartbeat": 1234567890}

# Check collection
venv/bin/python -c "
from app.services.vectordb_service import VectorDBService
import asyncio
stats = asyncio.run(VectorDBService.get_collection_stats())
print(stats)
"
```

### **ChromaDB Production Options**

#### **Option 1: Keep Docker Container on VM**
- ✅ Simple, same setup as dev
- ✅ No external dependencies
- ✅ Free
- ⚠️ Need to backup Docker volume

#### **Option 2: ChromaDB Cloud**
- ✅ Managed service
- ✅ Automatic backups
- ✅ Better for scale
- 💰 Paid service

**For POC**: Stick with Docker container

---

## 3. PostgreSQL Database

### **Purpose**
Store user data, preferences, and onboarding state.

### **Current Status**
✅ **Configured** (Docker available, using local file storage for now)

### **Connection Details**

#### **Local Development**

**Option A: Docker Container (Recommended)**
```bash
# Start PostgreSQL in Docker
docker-compose up -d postgres

# Connection string
DATABASE_URL=postgresql://stylistai_user:stylistai_password@localhost:5432/stylistai
```

**Option B: System PostgreSQL**
```bash
# If you have PostgreSQL installed locally
DATABASE_URL=postgresql://username:password@localhost:5432/stylistai
```

#### **Docker Compose Configuration**

**File**: `docker-compose.yml`

```yaml
postgres:
  image: postgres:15-alpine
  container_name: stylistai_postgres
  environment:
    POSTGRES_DB: stylistai
    POSTGRES_USER: stylistai_user
    POSTGRES_PASSWORD: stylistai_password
  ports:
    - "5432:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U stylistai_user -d stylistai"]
  networks:
    - stylistai_network

volumes:
  postgres_data:
```

### **Database Schema**

#### **Current Implementation**
Currently using **file-based storage** (JSON files) via `user_service.py`.

**File**: `app/services/user_service.py`

```python
# Data stored in: data/users/{user_id}.json
{
    "user_id": "user_123",
    "email": "user@example.com",
    "preferences": {
        "style_aesthetics": ["modern", "minimalist"],
        "colors": ["navy", "grey", "white"],
        "occasions": ["work", "casual"],
        "fit_preferences": "fitted",
        "budget": "mid-range",
        "body_type": "average",
        "style_goals": ["look professional"],
        "onboarding_completed": true
    },
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T11:00:00"
}
```

#### **Recommended Database Schema** (for production migration)

**Table: users**
```sql
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Table: user_preferences**
```sql
CREATE TABLE user_preferences (
    user_id VARCHAR(255) PRIMARY KEY REFERENCES users(id),
    style_aesthetics JSONB,  -- ["modern", "minimalist"]
    colors JSONB,             -- ["navy", "grey"]
    occasions JSONB,          -- ["work", "casual"]
    fit_preferences VARCHAR(50),
    budget VARCHAR(50),
    body_type VARCHAR(50),
    style_goals JSONB,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_skipped BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Table: onboarding_sessions** (optional)
```sql
CREATE TABLE onboarding_sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    current_step VARCHAR(50),
    collected_data JSONB,
    is_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Table: wardrobe_images** (optional - metadata only, embeddings in ChromaDB)
```sql
CREATE TABLE wardrobe_images (
    image_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    filename VARCHAR(255),
    gcs_url TEXT,
    upload_date TIMESTAMP DEFAULT NOW(),
    metadata JSONB,  -- {color, category, etc}
    INDEX idx_user_images (user_id)
);
```

### **Database Migration Script**

**File**: `scripts/init_db.sql`

```sql
-- Create database
CREATE DATABASE stylistai;

\c stylistai;

-- Create tables
CREATE TABLE users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_preferences (
    user_id VARCHAR(255) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    style_aesthetics JSONB DEFAULT '[]',
    colors JSONB DEFAULT '[]',
    occasions JSONB DEFAULT '[]',
    fit_preferences VARCHAR(50),
    budget VARCHAR(50),
    body_type VARCHAR(50),
    style_goals JSONB DEFAULT '[]',
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_skipped BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_onboarding_status ON user_preferences(onboarding_completed);
```

### **Setup PostgreSQL Database**

#### **Step 1: Start PostgreSQL Container**

```bash
# Start PostgreSQL
docker-compose up -d postgres

# Wait for it to be healthy
docker-compose ps postgres
```

#### **Step 2: Initialize Database**

```bash
# Connect to PostgreSQL
docker exec -it stylistai_postgres psql -U stylistai_user -d stylistai

# Or from host (if psql installed)
psql -h localhost -U stylistai_user -d stylistai

# Run migration script
\i scripts/init_db.sql
```

#### **Step 3: Update .env**

```bash
# .env file
DATABASE_URL=postgresql://stylistai_user:stylistai_password@localhost:5432/stylistai
```

### **Testing PostgreSQL Connection**

```bash
# Test connection
docker exec -it stylistai_postgres psql -U stylistai_user -d stylistai -c "SELECT version();"

# Check tables
docker exec -it stylistai_postgres psql -U stylistai_user -d stylistai -c "\dt"

# Test from Python
venv/bin/python -c "
from sqlalchemy import create_engine
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('✓ Database connected:', result.fetchone())
"
```

### **Current Storage vs Database**

| Feature | Current (File) | With PostgreSQL |
|---------|---------------|-----------------|
| User preferences | ✅ JSON files | ✅ Database table |
| Onboarding state | ✅ In-memory dict | ✅ Database table |
| Queries | ⚠️ Load all files | ✅ SQL queries |
| Concurrent access | ⚠️ File locks | ✅ ACID transactions |
| Backup | ⚠️ Manual | ✅ Automated |
| Production ready | ❌ No | ✅ Yes |

**For POC**: File-based storage works fine
**For Production**: Migrate to PostgreSQL

---

## 4. Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    StylistAI Application                     │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
             ↓                            ↓
    ┌────────────────┐          ┌────────────────┐
    │  User Service  │          │  Image Service │
    │  (app/services)│          │  (app/services)│
    └────────┬───────┘          └────────┬───────┘
             │                            │
             ↓                            ↓
    ┌────────────────┐          ┌────────────────┐
    │  PostgreSQL    │          │  CLIP Model    │
    │  (User Data)   │          │  (Embeddings)  │
    │                │          └────────┬───────┘
    │ Host: localhost│                   │
    │ Port: 5432     │          ┌────────▼───────┐
    │                │          │   ChromaDB     │
    └────────────────┘          │   (Vectors)    │
                                │                │
             ┌──────────────────┤ Host: localhost│
             │                  │ Port: 8001     │
             ↓                  └────────────────┘
    ┌────────────────┐
    │  GCS Bucket    │
    │  (Images)      │
    │                │
    │ gs://stylistai │
    └────────────────┘
```

---

## 5. Environment Configuration Summary

### **.env File (Complete)**

```bash
# Application
APP_NAME=StylistAI
DEBUG=True

# Server
HOST=0.0.0.0
PORT=8000

# Firebase Auth
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
FIREBASE_PROJECT_ID=stylistai
FIREBASE_WEB_API_KEY=AIzaSyD3MNmvWbokkuB180gkGrxxQReZx_8_uHc

# PostgreSQL Database
DATABASE_URL=postgresql://stylistai_user:stylistai_password@localhost:5432/stylistai

# ChromaDB Vector Database
CHROMA_HOST=http://localhost:8001
CHROMA_COLLECTION_NAME=outfits

# Google Cloud Storage
GCS_BUCKET_NAME=stylistai-wardrobe-images
GCS_CREDENTIALS_PATH=./gcs-credentials.json
GCS_PROJECT_ID=your-gcp-project-id

# OpenAI API
OPENAI_API_KEY=sk-proj-...
OPENAI_LLM_MODEL=gpt-4-turbo-preview

# Image Processing
MAX_IMAGE_SIZE_MB=10
```

---

## 6. Quick Start Commands

### **Start All Services**

```bash
# 1. Start infrastructure
docker-compose up -d postgres chromadb

# 2. Check status
docker-compose ps

# 3. Initialize database (first time only)
docker exec -it stylistai_postgres psql -U stylistai_user -d stylistai -f /path/to/init_db.sql

# 4. Start application
venv/bin/uvicorn app.main:app --reload
```

### **Check All Connections**

```bash
# PostgreSQL
docker exec -it stylistai_postgres psql -U stylistai_user -d stylistai -c "SELECT version();"

# ChromaDB
curl http://localhost:8001/api/v1/heartbeat

# Application health
curl http://localhost:8000/health
```

### **View Logs**

```bash
# PostgreSQL logs
docker logs stylistai_postgres

# ChromaDB logs
docker logs stylistai_chromadb

# Application logs
# (in terminal where uvicorn is running)
```

---

## 7. Production Deployment

### **GCP VM Deployment**

```bash
# 1. Copy docker-compose.yml to VM
scp docker-compose.yml user@vm-ip:/app/

# 2. Copy .env with production values
scp .env user@vm-ip:/app/

# 3. SSH to VM and start
ssh user@vm-ip
cd /app
docker-compose up -d

# 4. Access via VM external IP
http://VM-EXTERNAL-IP:8000
```

### **Production .env Updates**

```bash
# Update for containerized deployment
DATABASE_URL=postgresql://stylistai_user:stylistai_password@postgres:5432/stylistai
CHROMA_HOST=http://chromadb:8000

# Add production CORS origins
CORS_ORIGINS=https://yourdomain.com

# Disable debug
DEBUG=False
```

---

## 8. Troubleshooting

### **PostgreSQL Issues**

```bash
# Can't connect
docker-compose restart postgres
docker logs stylistai_postgres

# Reset database
docker-compose down -v  # Warning: deletes data
docker-compose up -d postgres
```

### **ChromaDB Issues**

```bash
# Connection refused
docker-compose restart chromadb
docker logs stylistai_chromadb

# Clear all embeddings
docker-compose down -v chroma_data
docker-compose up -d chromadb
```

### **GCS Issues**

```bash
# Test credentials
export GOOGLE_APPLICATION_CREDENTIALS=./gcs-credentials.json
gcloud auth application-default print-access-token

# List buckets
gsutil ls
```

---

## Summary

| Service | Status | Local URL | Production |
|---------|--------|-----------|------------|
| **PostgreSQL** | ✅ Ready | `localhost:5432` | Use Cloud SQL |
| **ChromaDB** | ✅ Running | `localhost:8001` | Keep in Docker |
| **GCS** | ⏳ Not setup | N/A | Need credentials |
| **Application** | ✅ Running | `localhost:8000` | Cloud Run or VM |

**For POC**: Current setup works (no GCS needed)
**For Production**: Add GCS credentials and migrate to PostgreSQL tables
