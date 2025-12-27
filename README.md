# StylistAI

> Trend-aware personal styling assistant with visual memory

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## What is StylistAI?

StylistAI is a **trend-aware, memory-driven** personal styling assistant that combines your unique fashion journey with global fashion intelligence. Upload outfit photos, get AI-powered styling advice that's both personalized to your history and aligned with current trends.

Unlike traditional styling apps that provide generic one-off advice, StylistAI maintains a persistent understanding of your style evolution while continuously adapting to contemporary fashion trends. The system uses vector embeddings and retrieval-augmented generation (RAG) to synthesize both personal historical context and up-to-date trend knowledge into actionable, modern recommendations.

## Key Features

- **Trend Intelligence** - Combines personal style memory with current fashion trends, silhouettes, and color palettes
- **Visual Memory** - Stores outfit photos as vector embeddings for intelligent similarity search
- **Dual-Context Recommendations** - Synthesizes both your historical preferences and contemporary fashion knowledge
- **Smart Retrieval** - Finds relevant past outfits to ensure consistent, context-aware suggestions
- **Adaptive Learning** - Captures and evolves your style profile while staying current with fashion trends
- **Secure Storage** - Cloud-based image storage with Google Cloud Storage

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/StylistAI.git
cd StylistAI
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your API keys and credentials

# Run
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## Tech Stack

**Backend & API**
- FastAPI - High-performance async API framework
- Python 3.9+ - Core language
- Pydantic - Data validation

**Storage & Database**
- Google Cloud Storage - Image storage
- ChromaDB - Vector similarity search
- PostgreSQL/SQLite - User data (optional)

**AI/ML**
- OpenAI/Anthropic - LLM for recommendations
- CLIP/multimodal embeddings - Image understanding
- RAG pipeline - Context retrieval

## Architecture

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
   ┌───▼────┐
   │FastAPI │
   └───┬────┘
       │
   ┌───▼────────────────────┐
   │  Upload Outfit Image   │
   └───┬────────────────┬───┘
       │                │
   ┌───▼───┐      ┌────▼─────┐
   │  GCS  │      │ Generate │
   │Storage│      │Embeddings│
   └───────┘      └────┬─────┘
                       │
                  ┌────▼─────┐
                  │ChromaDB  │
                  │(Vectors) │
                  └────┬─────┘
                       │
        ┌──────────────▼──────────────┐
        │     Parallel Retrieval      │
        ├──────────────┬──────────────┤
        │   Personal   │    Trend     │
        │   History    │  Knowledge   │
        │  (Similar    │  (Current    │
        │   Outfits)   │  Fashion)    │
        └──────┬───────┴──────┬───────┘
               │              │
               └──────┬───────┘
                      │
                 ┌────▼─────┐
                 │LLM + RAG │
                 │Synthesis │
                 └────┬─────┘
                      │
              ┌───────▼────────┐
              │   Personalized │
              │  + Trend-Aware │
              │     Advice     │
              └────────────────┘
```

## API Endpoints

### Authentication
```
POST   /auth/register      Register new user
POST   /auth/login         Login and get token
POST   /auth/refresh       Refresh access token
```

### Onboarding
```
POST   /onboarding/preferences    Set style preferences
GET    /onboarding/preferences    Get current preferences
PUT    /onboarding/preferences    Update preferences
```

### Outfits
```
POST   /outfits/upload       Upload outfit photo
GET    /outfits              List all outfits
GET    /outfits/{id}         Get specific outfit
DELETE /outfits/{id}         Delete outfit
```

### Styling
```
POST   /styling/analyze      Get advice for uploaded image
POST   /styling/query        Text-based styling query
POST   /styling/feedback     Submit feedback on advice
```

## Usage Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Register and login
auth = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "user@example.com",
    "password": "password123"
}).json()

headers = {"Authorization": f"Bearer {auth['access_token']}"}

# 2. Set preferences
requests.post(f"{BASE_URL}/onboarding/preferences",
    headers=headers,
    json={
        "occasions": ["casual", "business_casual"],
        "fit": "fitted",
        "budget": "mid-range",
        "styles": ["minimalist", "modern"]
    }
)

# 3. Upload outfit
with open("outfit.jpg", "rb") as f:
    requests.post(f"{BASE_URL}/outfits/upload",
        headers=headers,
        files={"file": f}
    )

# 4. Get styling advice
advice = requests.post(f"{BASE_URL}/styling/analyze",
    headers=headers,
    json={"query": "How can I improve this for a date night?"}
).json()

print(advice["recommendation"])
```

## Project Structure

```
StylistAI/
├── app/
│   ├── main.py              # App entry point
│   ├── config.py            # Configuration
│   ├── api/                 # Route handlers
│   │   ├── auth.py
│   │   ├── onboarding.py
│   │   ├── outfits.py
│   │   └── styling.py
│   ├── services/            # Business logic
│   │   ├── storage.py       # GCS integration
│   │   ├── embeddings.py    # Vector generation
│   │   ├── vectordb.py      # ChromaDB ops
│   │   └── llm.py           # LLM integration
│   ├── models/              # Data models
│   └── core/                # Security & deps
├── tests/                   # Test suite
├── requirements.txt
└── README.md
```

## Environment Variables

```bash
# Required
GCS_BUCKET_NAME=your-bucket-name
GCS_CREDENTIALS_PATH=/path/to/credentials.json
LLM_API_KEY=your-llm-api-key
EMBEDDING_API_KEY=your-embedding-api-key
JWT_SECRET_KEY=your-secret-key

# Optional
DATABASE_URL=sqlite:///./stylist.db
CHROMA_PERSIST_DIR=./chroma_db
LOG_LEVEL=INFO
```

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov

# Format code
black app/ && isort app/

# Type check
mypy app/

# Run linter
ruff check app/
```

## Roadmap

- [ ] Trend image retrieval (show examples of current trends)
- [ ] Seasonal trend reports and style guides
- [ ] Wardrobe management system
- [ ] Shopping integration with trend-aligned retailers
- [ ] Advanced vision analysis (color theory, fit assessment)
- [ ] Weather-based recommendations
- [ ] Social features and outfit sharing
- [ ] Mobile app (iOS/Android)
- [ ] Calendar integration for event-based styling

## Why StylistAI?

**Traditional styling apps have two problems:**
1. They **forget** - treating each interaction as isolated without learning from your history
2. They're **outdated** - providing generic advice that doesn't reflect current fashion trends

**StylistAI solves both:**

**Personal Memory**
- What worked for you in the past
- What didn't work and why
- Your evolving preferences over time
- Context from similar outfits and occasions

**Trend Intelligence**
- Current fashion trends and seasonal aesthetics
- Modern silhouettes and color palettes
- Contemporary styling techniques
- Up-to-date fashion knowledge

The system **synthesizes both contexts in parallel**, ensuring recommendations are both deeply personalized and refreshingly current. You get advice that's true to your style while keeping you fashion-forward.

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with modern AI/ML stack:
- FastAPI for high-performance APIs
- ChromaDB for vector similarity search
- Google Cloud for reliable infrastructure
- OpenAI/Anthropic for state-of-the-art LLMs

---

**Your style, remembered. Fashion trends, integrated.** • [Documentation](docs/) • [API Reference](http://localhost:8000/docs)
