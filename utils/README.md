# StylistAI Utility Scripts

This directory contains utility scripts for managing and monitoring the StylistAI application.

## Available Scripts

### 📊 check_database.py

**Purpose:** Check the status of PostgreSQL and ChromaDB databases, showing counts, sample data, and system health.

**Usage:**
```bash
# From project root
python utils/check_database.py

# Or using module syntax
python -m utils.check_database

# With virtual environment
source venv/bin/activate
python utils/check_database.py
```

**What it shows:**
- PostgreSQL table counts and structure
- User preferences and their completion status
- Outfit images and metadata
- Photos by user
- Embedding generation statistics
- ChromaDB vector embeddings count
- Sample data from both databases
- System health check

**Example Output:**
```
🔍 STYLISTAI DATABASE STATUS CHECKER 🔍

================================================================================
                           SYSTEM HEALTH CHECK
================================================================================

   ✅ PostgreSQL: Connected
   ✅ ChromaDB: Connected

   🎉 All systems operational!

================================================================================
                         POSTGRESQL DATABASE
================================================================================

📊 Found 3 tables:

   ✓ outfits: 19 rows
   ✓ user_preferences: 7 rows
   ✓ users: 7 rows
```

---

## Future Utility Scripts

### Planned additions:

- **clear_test_data.py** - Remove test users and their data
- **backup_database.py** - Backup PostgreSQL and ChromaDB data
- **migrate_embeddings.py** - Migrate embeddings between vector databases
- **test_vector_search.py** - Test vector similarity search functionality
- **generate_sample_data.py** - Generate sample users and wardrobe data for testing

---

## Adding New Utility Scripts

When creating new utility scripts:

1. Add the script to the `utils/` directory
2. Include a docstring at the top explaining what it does
3. Add usage instructions
4. Update this README
5. Make the script executable: `chmod +x utils/your_script.py`

**Template:**
```python
#!/usr/bin/env python3
"""
Your Script Name

Description of what this script does.

Usage:
    python utils/your_script.py [arguments]
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

def main():
    """Main function"""
    pass

if __name__ == "__main__":
    main()
```

---

## Notes

- All scripts assume they're being run from the project root directory
- Virtual environment should be activated before running scripts
- Scripts will automatically import app modules using the path hack at the top
- Database connection settings are pulled from `app.config.settings`
