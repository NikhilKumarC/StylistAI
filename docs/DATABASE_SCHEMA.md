# StylistAI Database Schema

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                          USERS                              │
├─────────────────────────────────────────────────────────────┤
│ PK  uid (VARCHAR 128)                 [Firebase UID]        │
│     email (VARCHAR 255)               [UNIQUE, NOT NULL]    │
│     name (VARCHAR 100)                                      │
│     created_at (TIMESTAMP)            [NOT NULL]            │
│     updated_at (TIMESTAMP)                                  │
│     onboarding_completed (BOOLEAN)    [NOT NULL, DEFAULT F] │
│     onboarding_completed_at (TIMESTAMP)                     │
└─────────────────────────────────────────────────────────────┘
                    │                          │
                    │ 1:1                      │ 1:*
                    │                          │
                    ▼                          ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│      USER_PREFERENCES        │  │          OUTFITS             │
├──────────────────────────────┤  ├──────────────────────────────┤
│ PK  id (VARCHAR 36)          │  │ PK  id (VARCHAR 36)          │
│ FK  user_uid → users.uid     │  │ FK  user_uid → users.uid     │
│                              │  │                              │
│     style_aesthetics (JSON)  │  │     image_id (VARCHAR 255)   │
│     colors (JSON)            │  │     filename (VARCHAR 500)   │
│     occasions (JSON)         │  │     gcs_url (TEXT)           │
│     style_goals (JSON)       │  │     local_path (TEXT)        │
│     fit_preferences (VARCHAR)│  │     file_size (INT)          │
│     budget (VARCHAR)         │  │     mime_type (VARCHAR)      │
│     body_type (VARCHAR)      │  │     width, height (INT)      │
│     created_at, updated_at   │  │     tags (JSON)              │
└──────────────────────────────┘  │     description (TEXT)       │
                                  │     occasion (VARCHAR)       │
                                  │     season (VARCHAR)         │
                                  │     ai_description (TEXT)    │
                                  │     ai_tags (JSON)           │
                                  │     dominant_colors (JSON)   │
                                  │     embedding_stored (BOOL)  │
                                  │     source (VARCHAR)         │
                                  │     uploaded_at (TIMESTAMP)  │
                                  │     is_deleted (BOOL)        │
                                  └──────────────────────────────┘
```

## Relationships

### Users → User Preferences (One-to-One)
- **Type**: One-to-One (required)
- **Foreign Key**: `user_preferences.user_uid` → `users.uid`
- **Constraint**: UNIQUE constraint on `user_uid` ensures one preference per user
- **Cascade**: When user is deleted, preferences should be deleted (CASCADE)

---

## Table Details

### 1. **users** Table

**Purpose**: Stores user authentication and profile information

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `uid` | VARCHAR(128) | PRIMARY KEY, NOT NULL | Firebase User ID (unique identifier) |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | User's email address |
| `name` | VARCHAR(100) | NULL | User's display name |
| `created_at` | TIMESTAMP | NOT NULL | Account creation timestamp |
| `updated_at` | TIMESTAMP | NULL | Last profile update timestamp |
| `onboarding_completed` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether user completed onboarding |
| `onboarding_completed_at` | TIMESTAMP | NULL | When onboarding was completed |

**Indexes**:
- Primary Key: `uid`
- Unique Index: `email` (for fast lookups and uniqueness)
- Index: `uid` (for FK relationships)

**Sample Data**:
```sql
uid                              | email                | name       | onboarding_completed
-------------------------------- | -------------------- | ---------- | --------------------
yCVT46fVV7RWJ0IynQ1UHffYRMl1     | user@example.com     | John Doe   | true
```

---

### 2. **user_preferences** Table

**Purpose**: Stores user style preferences collected during onboarding

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(36) | PRIMARY KEY, NOT NULL | UUID for the preference record |
| `user_uid` | VARCHAR(128) | FOREIGN KEY, UNIQUE, NOT NULL | References `users.uid` |
| `style_aesthetics` | JSON | NULL | Array of style preferences |
| `colors` | JSON | NULL | Array of favorite colors |
| `occasions` | JSON | NULL | Array of occasions they dress for |
| `style_goals` | JSON | NULL | Array of styling goals |
| `fit_preferences` | VARCHAR(50) | NULL | Single fit preference |
| `budget` | VARCHAR(50) | NULL | Budget range |
| `body_type` | VARCHAR(50) | NULL | Body type |
| `created_at` | TIMESTAMP | NOT NULL | When preferences were created |
| `updated_at` | TIMESTAMP | NULL | Last preference update |

**Indexes**:
- Primary Key: `id`
- Unique Index: `user_uid` (one preference per user)
- Foreign Key: `user_uid` → `users.uid`

**Sample Data**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_uid": "yCVT46fVV7RWJ0IynQ1UHffYRMl1",
  "style_aesthetics": ["minimalist", "modern"],
  "colors": ["navy", "grey", "white"],
  "occasions": ["work", "casual"],
  "style_goals": ["look professional", "stay comfortable"],
  "fit_preferences": "fitted",
  "budget": "mid-range",
  "body_type": "athletic"
}
```

---

## Extended Schema (Future Tables)

### 3. **outfits** (Not Yet Implemented)

```
┌─────────────────────────────────────────────────────────────┐
│                         OUTFITS                             │
├─────────────────────────────────────────────────────────────┤
│ PK  id (UUID)                                               │
│ FK  user_uid (VARCHAR 128)            → users.uid           │
│     image_url (TEXT)                  [GCS URL]             │
│     image_id (VARCHAR 255)            [ChromaDB ID]         │
│     embedding (VECTOR)                [Stored in ChromaDB]  │
│     description (TEXT)                                      │
│     tags (JSON)                       ["casual", "work"]    │
│     uploaded_at (TIMESTAMP)                                 │
└─────────────────────────────────────────────────────────────┘
```

### 4. **chat_history** (Not Yet Implemented)

```
┌─────────────────────────────────────────────────────────────┐
│                      CHAT_HISTORY                           │
├─────────────────────────────────────────────────────────────┤
│ PK  id (BIGSERIAL)                                          │
│ FK  user_uid (VARCHAR 128)            → users.uid           │
│     role (VARCHAR 20)                 ["user", "assistant"] │
│     content (TEXT)                                          │
│     created_at (TIMESTAMP)            [NOT NULL]            │
└─────────────────────────────────────────────────────────────┘
```

### 5. **recommendations** (Not Yet Implemented)

```
┌─────────────────────────────────────────────────────────────┐
│                    RECOMMENDATIONS                          │
├─────────────────────────────────────────────────────────────┤
│ PK  id (UUID)                                               │
│ FK  user_uid (VARCHAR 128)            → users.uid           │
│     query (TEXT)                      [User's question]     │
│     recommendations (JSON)            [AI response]         │
│     confidence_score (FLOAT)                                │
│     created_at (TIMESTAMP)                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Complete Future ER Diagram

```
                    ┌──────────────┐
                    │    USERS     │
                    │──────────────│
                    │ PK uid       │
                    │    email     │
                    │    name      │
                    └──────────────┘
                           │
                           │ 1
              ┌────────────┼────────────┬────────────┐
              │            │            │            │
              │ 1          │ 1          │ 1          │ *
              ▼            ▼            ▼            ▼
    ┌─────────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐
    │USER_PREFS   │  │ OUTFITS │  │  CHAT   │  │  RECS    │
    │─────────────│  │─────────│  │─────────│  │──────────│
    │ PK id       │  │ PK id   │  │ PK id   │  │ PK id    │
    │ FK user_uid │  │ FK uid  │  │ FK uid  │  │ FK uid   │
    │    styles   │  │    url  │  │    role │  │    query │
    │    colors   │  │    tags │  │ content │  │    recs  │
    └─────────────┘  └─────────┘  └─────────┘  └──────────┘
```

---

## Data Flow

### Onboarding Flow
```
1. User Signs Up (Firebase)
   ↓
2. Create User Record in PostgreSQL
   INSERT INTO users (uid, email)
   ↓
3. User Completes Onboarding
   ↓
4. Save Preferences
   INSERT INTO user_preferences
   UPDATE users SET onboarding_completed = TRUE
```

### Styling Query Flow
```
1. User Asks Question
   ↓
2. Retrieve User Preferences
   SELECT * FROM user_preferences WHERE user_uid = ?
   ↓
3. Search ChromaDB (Vectors)
   [Not stored in PostgreSQL]
   ↓
4. Generate Recommendations with GPT-4
   ↓
5. Return Response
   (Optional: Store in recommendations table)
```

---

## Storage Strategy

| Data Type | Storage Location | Why |
|-----------|------------------|-----|
| User profiles | **PostgreSQL** | Structured, needs queries, ACID |
| User preferences | **PostgreSQL** | Structured, needs queries, transactions |
| Onboarding state | **In-Memory Dict** | Temporary, no persistence needed |
| Image embeddings (512-D) | **ChromaDB** | Vector search, similarity |
| Image files | **GCS/Local** | Blob storage |
| Chat history | **PostgreSQL** (future) | Queryable, persistent |

---

## Indexes & Performance

### Current Indexes
```sql
-- users table
CREATE INDEX ix_users_uid ON users(uid);
CREATE UNIQUE INDEX ix_users_email ON users(email);

-- user_preferences table
CREATE UNIQUE INDEX ix_user_preferences_user_uid ON user_preferences(user_uid);
```

### Future Indexes (when tables are added)
```sql
-- outfits table
CREATE INDEX ix_outfits_user_uid ON outfits(user_uid);
CREATE INDEX ix_outfits_uploaded_at ON outfits(uploaded_at DESC);

-- chat_history table
CREATE INDEX ix_chat_user_uid_created ON chat_history(user_uid, created_at DESC);

-- recommendations table
CREATE INDEX ix_recs_user_uid_created ON recommendations(user_uid, created_at DESC);
```

---

## Sample Queries

### Get User with Preferences
```sql
SELECT
    u.uid,
    u.email,
    u.name,
    u.onboarding_completed,
    p.style_aesthetics,
    p.colors,
    p.budget
FROM users u
LEFT JOIN user_preferences p ON u.uid = p.user_uid
WHERE u.uid = 'yCVT46fVV7RWJ0IynQ1UHffYRMl1';
```

### Find Users by Style
```sql
SELECT
    u.email,
    u.name,
    p.style_aesthetics
FROM users u
JOIN user_preferences p ON u.uid = p.user_uid
WHERE p.style_aesthetics @> '["minimalist"]'::jsonb;
```

### Count Users by Onboarding Status
```sql
SELECT
    onboarding_completed,
    COUNT(*) as user_count
FROM users
GROUP BY onboarding_completed;
```

---

## Database Migrations

### Initial Schema
```sql
-- Already created via SQLAlchemy
-- See: app/models/db_models.py
```

### Future Migrations (Alembic)
```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add outfits table"

# Apply migration
alembic upgrade head
```

---

## Backup Strategy

### PostgreSQL Backup
```bash
# Dump database
docker exec airflow_e2f51f-postgres-1 pg_dump -U stylistai_user stylistai > backup.sql

# Restore database
docker exec -i airflow_e2f51f-postgres-1 psql -U stylistai_user stylistai < backup.sql
```

### Full Backup (Database + Vectors + Images)
```
1. PostgreSQL: pg_dump
2. ChromaDB: Export collections
3. Images: Sync GCS bucket
```

---

## Connection String

```python
# Local Development
DATABASE_URL = "postgresql://stylistai_user:stylistai_password@localhost:5432/stylistai"

# Docker Compose (app in container)
DATABASE_URL = "postgresql://stylistai_user:stylistai_password@postgres:5432/stylistai"

# Production (Cloud SQL / RDS)
DATABASE_URL = "postgresql://user:pass@cloud-db-host:5432/stylistai"
```
