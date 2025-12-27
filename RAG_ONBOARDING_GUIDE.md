# RAG-Powered Onboarding System - StylistAI

This guide explains the new **Retrieval-Augmented Generation (RAG)** system with intelligent onboarding for StylistAI.

## Overview

Instead of immediately giving styling advice, the agent now:
1. **Asks questions** to understand your style preferences
2. **Collects photos** of your wardrobe
3. **Stores everything** in a vector database (ChromaDB)
4. **Uses RAG** to retrieve similar outfits when making recommendations
5. **Provides personalized** advice based on your actual wardrobe and preferences

---

## Architecture

```
┌─────────────────────────────────────────────┐
│            User Signs Up                     │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│     Onboarding Agent (LangGraph)            │
│  ├─ "What style aesthetics do you prefer?"  │
│  ├─ "What colors do you like?"             │
│  ├─ "What occasions do you dress for?"     │
│  ├─ "Upload wardrobe photos"                │
│  └─ Stores all responses                    │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│     Generate Embeddings (CLIP)              │
│  ├─ Text embeddings from preferences        │
│  └─ Image embeddings from photos            │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│    ChromaDB (Vector Database)               │
│  ├─ Store user preferences                  │
│  ├─ Store outfit image embeddings           │
│  └─ Enable similarity search                │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│      Styling Agent (LangGraph + RAG)        │
│  User asks: "What should I wear today?"     │
│  ├─ 1. Retrieve similar outfits (ChromaDB)  │
│  ├─ 2. Retrieve user preferences            │
│  ├─ 3. Search fashion trends                │
│  ├─ 4. Generate recommendations (OpenAI)    │
│  └─ 5. Return personalized advice           │
└─────────────────────────────────────────────┘
```

---

## Onboarding Flow

### Step-by-Step Conversation

The onboarding agent asks these questions in order:

1. **Greeting**: Welcome message
2. **Style Aesthetics**: "What style aesthetics do you prefer?"
   - Examples: minimalist, modern, classic, streetwear, bohemian
3. **Colors**: "What are your favorite colors to wear?"
   - Examples: navy, grey, white, black, beige
4. **Occasions**: "What occasions do you usually dress for?"
   - Examples: work, casual, formal, gym, dates
5. **Fit Preferences**: "What fit do you prefer?"
   - Examples: fitted, relaxed, oversized, slim
6. **Budget**: "What's your budget range?"
   - Examples: budget-friendly, mid-range, premium, luxury
7. **Body Type**: "What's your body type?"
   - Examples: athletic, slim, curvy, tall, petite
8. **Style Goals**: "What are your style goals?"
   - Examples: look professional, express creativity, stay comfortable
9. **Photos**: "Upload 3-5 photos of your wardrobe"
   - Upload actual outfit/clothing photos

### How It Works

#### Natural Language Processing

The agent uses **OpenAI GPT-4** to extract structured data from your natural language responses.

**Example:**

You say: "I love minimalist and modern styles, sometimes a bit of streetwear"

Agent extracts: `["minimalist", "modern", "streetwear"]`

#### Conversational State Management

The onboarding uses **LangGraph** to manage conversation state:
- Tracks which question you're on
- Stores your previous answers
- Moves to next question automatically
- Handles completion when done

---

## API Endpoints

### 1. Start Onboarding

**Endpoint:** `POST /onboarding/start`

**Headers:**
```
Authorization: Bearer <your_firebase_token>
```

**Response:**
```json
{
  "next_question": "👋 Welcome to StylistAI! I'm your personal AI stylist...",
  "current_step": "greeting",
  "is_complete": false
}
```

### 2. Respond to Question

**Endpoint:** `POST /onboarding/respond`

**Headers:**
```
Authorization: Bearer <your_firebase_token>
Content-Type: application/json
```

**Body:**
```json
{
  "message": "I prefer minimalist and modern styles"
}
```

**Response:**
```json
{
  "next_question": "What are your favorite colors to wear?",
  "current_step": "colors",
  "is_complete": false
}
```

### 3. Check Onboarding Status

**Endpoint:** `GET /onboarding/status`

**Response:**
```json
{
  "completed": false,
  "has_active_session": true,
  "current_step": "colors"
}
```

**Or if completed:**
```json
{
  "completed": true,
  "preferences": {
    "style_aesthetics": ["minimalist", "modern"],
    "colors": ["navy", "grey", "white"],
    "occasions": ["work", "casual"],
    "onboarding_completed": true
  }
}
```

### 4. Upload Photos

**Endpoint:** `POST /onboarding/upload-photos`

**Headers:**
```
Authorization: Bearer <your_firebase_token>
Content-Type: multipart/form-data
```

**Body:**
```
files: [image1.jpg, image2.jpg, image3.jpg]
```

**Response:**
```json
{
  "message": "Successfully uploaded 3 photos",
  "files": [
    {
      "filename": "outfit1.jpg",
      "content_type": "image/jpeg",
      "size": 245678
    }
  ]
}
```

### 5. Skip Onboarding (Testing Only)

**Endpoint:** `POST /onboarding/skip`

Sets default preferences so you can test the chat immediately without completing onboarding.

---

## Using the Onboarding API

### Example Flow with cURL

```bash
# 1. Get your Firebase token (from localStorage after login)
export TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI..."

# 2. Start onboarding
curl -X POST http://localhost:8000/onboarding/start \
  -H "Authorization: Bearer $TOKEN"

# Response: "What style aesthetics do you prefer?"

# 3. Answer first question
curl -X POST http://localhost:8000/onboarding/respond \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "I like minimalist and modern styles"}'

# Response: "What are your favorite colors to wear?"

# 4. Answer second question
curl -X POST http://localhost:8000/onboarding/respond \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "navy, grey, white, and black"}'

# ... continue until photo upload step

# 5. Upload photos
curl -X POST http://localhost:8000/onboarding/upload-photos \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@outfit1.jpg" \
  -F "files=@outfit2.jpg" \
  -F "files=@outfit3.jpg"

# 6. Complete onboarding with final response
curl -X POST http://localhost:8000/onboarding/respond \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Done uploading photos!"}'

# Response: "Perfect! I've learned a lot about your style. Let's start creating amazing outfits together! 🎉"
# "is_complete": true
```

---

## RAG Implementation (Coming Next)

### Phase 1: Image Embeddings with CLIP

**CLIP (Contrastive Language-Image Pre-training)** will generate embeddings from outfit photos.

```python
# Pseudo-code
from transformers import CLIPProcessor, CLIPModel

# Load CLIP model
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Generate embedding from image
image = Image.open("outfit.jpg")
inputs = processor(images=image, return_tensors="pt")
embedding = model.get_image_features(**inputs)

# Store in ChromaDB
chromadb_collection.add(
    embeddings=[embedding.tolist()],
    metadatas=[{"user_id": "user123", "occasion": "casual"}],
    ids=["outfit_001"]
)
```

### Phase 2: ChromaDB Integration

Store and retrieve similar outfits:

```python
# Query for similar outfits
results = chromadb_collection.query(
    query_embeddings=[user_query_embedding],
    n_results=5
)

# Returns 5 most similar outfits from user's wardrobe
```

### Phase 3: RAG Pipeline

Combine retrieval + generation:

```python
# 1. User asks: "What should I wear for a business meeting?"

# 2. Retrieve similar outfits from ChromaDB
similar_outfits = retrieve_similar_outfits(query="business meeting", user_id="user123")

# 3. Retrieve user preferences
user_prefs = get_user_preferences("user123")

# 4. Generate recommendations with context
context = f"""
User preferences: {user_prefs}
Similar outfits from wardrobe: {similar_outfits}
Current trends: {fashion_trends}
"""

response = openai.chat.completions.create(
    model="gpt-4-turbo",
    messages=[
        {"role": "system", "content": "You are a personal stylist..."},
        {"role": "user", "content": context + "\n\nWhat should I wear?"}
    ]
)

# 5. Return personalized recommendations based on actual wardrobe
```

---

## Frontend Integration

### Updating the Chat Interface

The frontend will need to:

1. **Check onboarding status** on login
2. **Show onboarding UI** if not completed
3. **Show chat UI** if completed

### Example Frontend Flow

```javascript
// After user logs in
async function checkOnboarding() {
    const token = localStorage.getItem('authToken');

    const response = await fetch('http://localhost:8000/onboarding/status', {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    const data = await response.json();

    if (!data.completed) {
        // Show onboarding interface
        showOnboardingUI();
    } else {
        // Show chat interface
        showChatUI();
    }
}

// Onboarding conversation
async function sendOnboardingResponse(message) {
    const token = localStorage.getItem('authToken');

    const response = await fetch('http://localhost:8000/onboarding/respond', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    });

    const data = await response.json();

    // Show next question
    displayMessage('agent', data.next_question);

    if (data.is_complete) {
        // Onboarding done! Switch to chat
        showChatUI();
    }
}

// Photo upload
async function uploadPhotos(files) {
    const token = localStorage.getItem('authToken');
    const formData = new FormData();

    files.forEach(file => {
        formData.append('files', file);
    });

    const response = await fetch('http://localhost:8000/onboarding/upload-photos', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
    });

    const data = await response.json();
    console.log(`Uploaded ${data.files.length} photos`);
}
```

---

## Benefits of This Approach

### 1. Personalized Recommendations
- Agent knows your actual wardrobe
- Suggestions based on colors you already own
- Fits your budget and occasions

### 2. Visual Understanding
- Sees what you actually wear
- Understands your style from photos
- Can suggest combinations from existing pieces

### 3. Continuous Learning
- As you upload more photos, agent gets smarter
- Feedback on recommendations improves future advice
- Your style profile evolves over time

### 4. Context-Aware
- Knows if you're dressing for work vs. weekend
- Understands your body type for better fits
- Considers your budget constraints

---

## Next Steps to Complete RAG

### Phase 1: Storage & Embeddings (Priority)

1. **Start ChromaDB:**
   ```bash
   docker-compose up -d chromadb
   ```

2. **Install CLIP:**
   ```bash
   pip install transformers pillow torch
   ```

3. **Implement image processing service:**
   - `app/services/image_service.py`
   - Upload to cloud storage
   - Generate CLIP embeddings
   - Store in ChromaDB

### Phase 2: Retrieval

1. **Implement similarity search:**
   - Query ChromaDB with text/image
   - Return top-k similar outfits
   - Filter by occasion, color, etc.

2. **Update styling agent:**
   - Retrieve user's outfits before generating advice
   - Include in context for OpenAI
   - Reference specific items from wardrobe

### Phase 3: Advanced Features

1. **Outfit combinations:**
   - Suggest mixing pieces from wardrobe
   - "Wear your navy blazer with grey chinos"

2. **Shopping recommendations:**
   - Identify gaps in wardrobe
   - Suggest new pieces that complement existing style

3. **Trend integration:**
   - Compare wardrobe to current trends
   - Suggest modern ways to wear existing pieces

---

## Testing the Onboarding

### Manual Test (CLI)

```bash
# 1. Login to get token
# 2. Start onboarding
curl -X POST http://localhost:8000/onboarding/start \
  -H "Authorization: Bearer $TOKEN"

# 3. Follow the conversation
# 4. Check API docs
open http://localhost:8000/docs
```

### Skip for Quick Testing

```bash
# Skip onboarding and set defaults
curl -X POST http://localhost:8000/onboarding/skip \
  -H "Authorization: Bearer $TOKEN"
```

---

## Current Implementation Status

### ✅ Completed

- [x] Onboarding agent with LangGraph
- [x] Conversational flow (9 questions)
- [x] Natural language extraction with LLM
- [x] API endpoints for onboarding
- [x] State management for conversations
- [x] Preference storage
- [x] Skip functionality for testing

### 🔄 In Progress

- [ ] Frontend onboarding UI
- [ ] Image upload implementation
- [ ] ChromaDB integration
- [ ] CLIP embeddings
- [ ] RAG pipeline

### 📅 Coming Next

- [ ] Similarity search
- [ ] Outfit retrieval in styling agent
- [ ] Image storage (GCS)
- [ ] Advanced RAG features

---

## API Documentation

Full interactive API documentation available at:
**http://localhost:8000/docs**

Try the onboarding endpoints there!

---

**Your intelligent onboarding system is ready! Next step: Add the frontend UI and complete the RAG pipeline.** 🚀
