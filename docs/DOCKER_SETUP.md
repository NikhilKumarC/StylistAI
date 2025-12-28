# Docker Setup Guide for StylistAI

This guide explains how to run StylistAI with containerized PostgreSQL and ChromaDB, with options for both local development and full containerization.

## Architecture Overview

We support two development modes:

### Mode 1: Hybrid (Recommended for Development)
- **PostgreSQL** runs in Docker
- **ChromaDB** runs in Docker
- **FastAPI app** runs locally in venv (faster development/debugging)

### Mode 2: Fully Containerized
- **PostgreSQL** runs in Docker
- **ChromaDB** runs in Docker
- **FastAPI app** runs in Docker (closer to production)

---

## Prerequisites

- Docker installed and running
- Docker Compose installed
- Python 3.9+ (for Mode 1)

---

## Quick Start

### 1. Start Database Services

```bash
# Start only PostgreSQL and ChromaDB (Mode 1)
docker-compose up -d postgres chromadb

# OR start all services including app (Mode 2)
docker-compose up -d
```

### 2. Verify Services are Running

```bash
docker-compose ps

# You should see:
# stylistai_postgres   Up (healthy)
# stylistai_chromadb   Up (healthy)
# stylistai_app        Up (only if Mode 2)
```

### 3. Run the FastAPI App

**Mode 1 (Local venv):**
```bash
# Activate virtual environment
source venv/bin/activate

# Run the app
python app/main.py
# OR
uvicorn app.main:app --reload
```

**Mode 2 (Fully containerized):**
```bash
# Already running if you did docker-compose up -d
# View logs:
docker-compose logs -f app
```

### 4. Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **ChromaDB API**: http://localhost:8001

---

## Configuration

### Environment Variables

The `.env` file is configured for both modes:

**Mode 1 (Hybrid - Default):**
```bash
DATABASE_URL=postgresql://stylistai_user:stylistai_password@localhost:5432/stylistai
CHROMA_HOST=http://localhost:8001
```

**Mode 2 (Fully Containerized):**
Update `.env` to use Docker network hostnames:
```bash
DATABASE_URL=postgresql://stylistai_user:stylistai_password@postgres:5432/stylistai
CHROMA_HOST=http://chromadb:8000
```

---

## docker-compose.yml Services

### PostgreSQL
```yaml
- Container: stylistai_postgres
- Port: 5432
- Database: stylistai
- User: stylistai_user
- Password: stylistai_password
- Volume: postgres_data (persists data)
```

### ChromaDB
```yaml
- Container: stylistai_chromadb
- Port: 8001 (mapped from 8000)
- Volume: chroma_data (persists vectors)
- Persistent: TRUE
```

### FastAPI App (Optional)
```yaml
- Container: stylistai_app
- Port: 8000
- Hot reload: Enabled
- Depends on: postgres, chromadb
```

---

## Common Commands

### Start Services
```bash
# Start all services in background
docker-compose up -d

# Start with logs
docker-compose up

# Start specific services only
docker-compose up -d postgres chromadb
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f chromadb
docker-compose logs -f app
```

### Rebuild Containers
```bash
# Rebuild app after code changes
docker-compose build app

# Rebuild and restart
docker-compose up -d --build app
```

### Access Database
```bash
# Connect to PostgreSQL
docker exec -it stylistai_postgres psql -U stylistai_user -d stylistai

# PostgreSQL commands:
# \dt - list tables
# \d users - describe users table
# \q - quit
```

### Reset Everything
```bash
# Stop containers, remove volumes, and start fresh
docker-compose down -v
docker-compose up -d postgres chromadb
```

---

## Database Management

### Initialize Database

The database will be created automatically when you first start the app with SQLAlchemy models. If you need to manually initialize:

```bash
# Connect to database
docker exec -it stylistai_postgres psql -U stylistai_user -d stylistai

# Create tables (if using migrations)
python -m alembic upgrade head
```

### Backup Database

```bash
# Export PostgreSQL database
docker exec stylistai_postgres pg_dump -U stylistai_user stylistai > backup.sql

# Restore database
docker exec -i stylistai_postgres psql -U stylistai_user stylistai < backup.sql
```

### View ChromaDB Collections

```bash
# ChromaDB exposes HTTP API on port 8001
curl http://localhost:8001/api/v1/collections

# List all items in a collection
curl http://localhost:8001/api/v1/collections/outfits/get
```

---

## Development Workflow

### Recommended Workflow (Mode 1)

1. **Start Docker services:**
   ```bash
   docker-compose up -d postgres chromadb
   ```

2. **Activate venv and run app locally:**
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

3. **Make code changes** - App auto-reloads

4. **Stop when done:**
   ```bash
   docker-compose down
   ```

### Production-like Testing (Mode 2)

1. **Build and start all containers:**
   ```bash
   docker-compose up -d --build
   ```

2. **Test the app:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f app
   ```

---

## Deployment to GCP

### Option 1: Cloud Run (Recommended for Serverless)

```bash
# Build and push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT/stylistai

# Deploy to Cloud Run
gcloud run deploy stylistai \
  --image gcr.io/YOUR_PROJECT/stylistai \
  --platform managed \
  --region us-central1 \
  --set-env-vars="DATABASE_URL=postgresql://..." \
  --allow-unauthenticated
```

**For databases:**
- Use **Cloud SQL for PostgreSQL**
- Use **ChromaDB Cloud** or self-host on Compute Engine

### Option 2: Google Kubernetes Engine (GKE)

```bash
# Build image
docker build -t gcr.io/YOUR_PROJECT/stylistai .

# Push to GCR
docker push gcr.io/YOUR_PROJECT/stylistai

# Deploy to GKE (create k8s manifests)
kubectl apply -f k8s/
```

### Option 3: Compute Engine (VM)

```bash
# SSH into VM
gcloud compute ssh your-vm-name

# Clone repo and run docker-compose
git clone <your-repo>
cd stylistai
docker-compose up -d
```

---

## Troubleshooting

### PostgreSQL Connection Refused

**Problem:** `connection refused` or `could not connect to server`

**Solution:**
```bash
# Check if container is running
docker-compose ps

# Check logs
docker-compose logs postgres

# Wait for health check
docker-compose up -d postgres
docker exec stylistai_postgres pg_isready -U stylistai_user
```

### ChromaDB Not Accessible

**Problem:** `Connection refused` to ChromaDB

**Solution:**
```bash
# Verify ChromaDB is running
curl http://localhost:8001/api/v1/heartbeat

# Check logs
docker-compose logs chromadb

# Restart
docker-compose restart chromadb
```

### App Can't Connect to Services

**Problem:** App says services unavailable

**Mode 1 Solution** (venv):
- Use `localhost` in `.env`
- Make sure ports 5432 and 8001 are accessible

**Mode 2 Solution** (containerized):
- Use service names (`postgres`, `chromadb`) in `.env`
- Ensure all containers are on the same network

### Port Already in Use

**Problem:** `Port 5432 is already in use`

**Solution:**
```bash
# Change port in docker-compose.yml
ports:
  - "5433:5432"  # Changed from 5432:5432

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://stylistai_user:stylistai_password@localhost:5433/stylistai
```

### Containers Keep Restarting

**Solution:**
```bash
# Check logs for errors
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Performance Tips

1. **Volume Mounts** (Mode 2): Use bind mounts for fast code changes
2. **Health Checks**: Wait for services to be healthy before connecting
3. **Connection Pooling**: Configure SQLAlchemy pool size appropriately
4. **ChromaDB Persistence**: Ensure `IS_PERSISTENT=TRUE` for data retention

---

## Security Notes

**For Development:**
- Default credentials are fine
- Services exposed on localhost only

**For Production:**
- Change all default passwords
- Use secrets management (GCP Secret Manager)
- Enable SSL for PostgreSQL
- Restrict network access
- Use Cloud SQL proxy for database connections
- Enable authentication for ChromaDB

---

## Next Steps

1. ✅ Docker services are set up
2. ✅ Virtual environment is ready
3. 🔄 Complete Firebase authentication setup
4. 🔄 Implement database models and migrations
5. 🔄 Build API endpoints for outfit upload/management
6. 🔄 Integrate ChromaDB for vector search
7. 🔄 Deploy to GCP

---

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [GCP Cloud Run](https://cloud.google.com/run/docs)
- [GCP Cloud SQL](https://cloud.google.com/sql/docs)
