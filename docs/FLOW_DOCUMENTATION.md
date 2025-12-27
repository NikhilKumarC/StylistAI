# StylistAI - Complete Flow Documentation

This document explains the step-by-step execution flow of StylistAI, covering how the AI asks questions, stores responses, and feeds data to the vector database.

---

## Table of Contents

1. [Part 1: Onboarding Flow (Collecting User Data)](#part-1-onboarding-flow)
2. [Part 2: Photo Upload Flow (To Vector DB)](#part-2-photo-upload-flow)
3. [Part 3: Main Chat Flow (Using Vector DB)](#part-3-main-chat-flow)
4. [Part 4: Turn-Based State Machine Explained](#part-4-turn-based-state-machine)
5. [Visual Flow Diagram](#visual-flow-diagram)

---

## Part 1: Onboarding Flow (Collecting User Data)

### Step 1: User Clicks "Let's Get Started"

**Frontend (index.html:891)**
```javascript
async function startOnboarding() {
    const response = await fetch('http://localhost:8000/onboarding/start', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${authToken}` }
    });
}
```

### Step 2: Backend Processes Start Request

**app/api/onboarding.py:37-90** (`start_onboarding()`)
```python
@router.post("/start")
async def start_onboarding(current_user: dict):
    user_id = current_user["uid"]  # Get Firebase UID

    # Call the onboarding agent
    result = await run_onboarding_agent(
        user_id=user_id,
        user_message=None,  # No message for first call
        current_state=None   # No existing state
    )

    # Store state in memory
    _onboarding_states[user_id] = result

    return OnboardingResponse(
        next_question=result["next_question"],  # "Welcome to StylistAI! ..."
        current_step="greeting",
        is_complete=False
    )
```

### Step 3: Onboarding Agent Initializes

**app/services/onboarding_agent.py:241-306** (`run_onboarding_agent()`)
```python
async def run_onboarding_agent(user_id, user_message=None, current_state=None):
    agent = create_onboarding_agent()  # Create LangGraph workflow

    if current_state is None:  # First interaction
        initial_state = {
            "messages": [],
            "user_id": user_id,
            "current_step": "greeting",
            "collected_data": {},
            "is_complete": False
        }

        result = agent.invoke(initial_state)  # Run the graph
```

### Step 4: LangGraph Workflow Executes

**app/services/onboarding_agent.py:210-237** (`create_onboarding_agent()`)

The workflow graph:
```
START → start_onboarding() → ask_next_question() → END
```

**app/services/onboarding_agent.py:81-92** (`start_onboarding()`)
```python
def start_onboarding(state: OnboardingState):
    state['current_step'] = 'greeting'
    state['collected_data'] = {}

    # Get greeting from predefined steps
    greeting = ONBOARDING_STEPS['greeting']['question']
    # "👋 Welcome to StylistAI! I'm your personal AI stylist..."

    state['messages'].append(AIMessage(content=greeting))
    return state
```

**app/services/onboarding_agent.py:171-199** (`ask_next_question()`)
```python
def ask_next_question(state: OnboardingState):
    current_step_info = ONBOARDING_STEPS.get(state['current_step'])
    next_step = current_step_info['next']  # 'style_aesthetics'

    state['current_step'] = next_step
    next_question = ONBOARDING_STEPS[next_step]['question']
    # "What style aesthetics do you prefer?"

    state['messages'].append(AIMessage(content=next_question))
    return state
```

### Step 5: User Answers Question

**Frontend (index.html:954-978)** - User types answer
```javascript
async function sendOnboardingMessage() {
    const message = userInput.value;  // "I like minimalist and modern"

    const response = await fetch('http://localhost:8000/onboarding/respond', {
        method: 'POST',
        body: JSON.stringify({ message: message })
    });
}
```

### Step 6: Backend Processes Answer

**app/api/onboarding.py:93-154** (`respond_to_onboarding()`)
```python
@router.post("/respond")
async def respond_to_onboarding(message: OnboardingMessage, current_user: dict):
    user_id = current_user["uid"]

    # Get saved state from memory
    current_state = _onboarding_states.get(user_id)

    # Run agent with user's response
    result = await run_onboarding_agent(
        user_id=user_id,
        user_message=message.message,  # "I like minimalist and modern"
        current_state=current_state     # Previous state
    )

    # Update stored state
    _onboarding_states[user_id] = result
```

### Step 7: Agent Processes Response with LLM

**app/services/onboarding_agent.py:273-290** (continuing in agent)
```python
else:  # Continue onboarding
    state = current_state
    state["messages"].append(HumanMessage(content=user_message))

    # Extract data from user's answer using LLM
    state = process_user_response(state)

    # Ask next question
    state = ask_next_question(state)
```

**app/services/onboarding_agent.py:95-121** (`process_user_response()`)
```python
def process_user_response(state):
    last_user_message = "I like minimalist and modern"
    step_info = ONBOARDING_STEPS[state['current_step']]  # 'style_aesthetics'

    # Call LLM to extract structured data
    extracted_data = extract_preference_with_llm(
        user_response=last_user_message,
        field_name='style_aesthetics'
    )

    # Store in collected_data
    state['collected_data']['style_aesthetics'] = extracted_data
    # Result: ["minimalist", "modern"]
```

**app/services/onboarding_agent.py:124-168** (`extract_preference_with_llm()`)
```python
def extract_preference_with_llm(user_response, field_name):
    llm = ChatOpenAI(model="gpt-4-turbo-preview")

    prompt = f"""
    Extract {field_name} from: "{user_response}"
    Return JSON: {{"{field_name}": ["value1", "value2"]}}
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    # GPT-4 returns: {"style_aesthetics": ["minimalist", "modern"]}

    data = json.loads(response.content)
    return data.get(field_name)  # ["minimalist", "modern"]
```

### Step 8: Repeat for All Questions

The flow repeats steps 5-7 for each question:
- `style_aesthetics` → `colors` → `occasions` → `fit_preferences` → `budget` → `body_type` → `style_goals` → `photos`

### Step 9: Save Preferences to Database

**app/services/onboarding_agent.py:310-328** (`save_onboarding_data()`)
```python
def save_onboarding_data(user_id, data):
    preferences = {
        "style_aesthetics": data.get("style_aesthetics", []),
        "colors": data.get("colors", []),
        "occasions": data.get("occasions", []),
        "fit_preferences": data.get("fit_preferences", ""),
        "budget": data.get("budget", ""),
        "body_type": data.get("body_type", ""),
        "style_goals": data.get("style_goals", []),
        "onboarding_completed": True
    }

    UserService.save_user_preferences(user_id, preferences)
    # Saves to: user_preferences/{user_id}.json
```

---

## Part 2: Photo Upload Flow (To Vector DB)

### Step 1: User Uploads Photos

**Frontend (index.html:1009-1047)**
```javascript
async function uploadOnboardingPhotos() {
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    const response = await fetch('http://localhost:8000/onboarding/upload-photos', {
        method: 'POST',
        body: formData
    });
}
```

### Step 2: Backend Receives Photos

**app/api/onboarding.py:247-344** (`upload_wardrobe_photos()`)
```python
@router.post("/upload-photos")
async def upload_wardrobe_photos(files: List[UploadFile], current_user: dict):
    user_id = current_user["uid"]

    image_data = []
    for file in files:
        # Validate image
        content = await file.read()
        is_valid, error = ImageService.validate_image(content)

        image_data.append((content, file.filename))

    # Process all images
    results = await ImageService.process_multiple_images(
        images=image_data,
        user_id=user_id,
        metadata={"source": "onboarding"}
    )
```

### Step 3: Generate CLIP Embeddings

**app/services/image_service.py** (`process_multiple_images()`)
```python
async def process_multiple_images(images, user_id, metadata):
    results = []
    for content, filename in images:
        # Generate CLIP embedding
        embedding = await generate_clip_embedding(content)
        # Returns: 512-dimensional vector [0.123, -0.456, ...]

        # Upload to Google Cloud Storage (if configured)
        gcs_url = await upload_to_gcs(content, user_id, filename)

        # Store in ChromaDB
        await store_in_chromadb(
            embedding=embedding,
            user_id=user_id,
            filename=filename,
            gcs_url=gcs_url,
            metadata=metadata
        )
```

### Step 4: Store in ChromaDB

**app/services/vector_store.py** (conceptual)
```python
async def store_in_chromadb(embedding, user_id, filename, gcs_url, metadata):
    collection = chroma_client.get_collection("outfits")

    collection.add(
        embeddings=[embedding],  # 512-dim CLIP vector
        ids=[f"{user_id}_{filename}_{timestamp}"],
        metadatas=[{
            "user_id": user_id,
            "filename": filename,
            "gcs_url": gcs_url,
            "source": "onboarding",
            "uploaded_at": datetime.now()
        }]
    )
    # Now stored in ChromaDB for similarity search!
```

---

## Part 3: Main Chat Flow (Using Vector DB)

### Step 1: User Asks Question

**Frontend (index.html:1074-1134)**
```javascript
async function sendMainChatMessage() {
    const query = "What should I wear for a business meeting?";

    const response = await fetch('http://localhost:8000/styling/query', {
        method: 'POST',
        body: JSON.stringify({ query: query })
    });
}
```

### Step 2: Styling Endpoint Called

**app/api/styling.py:24-98** (`get_styling_advice()`)
```python
@router.post("/query")
async def get_styling_advice(request: StylingQueryRequest, current_user: dict):
    user_id = current_user["uid"]

    # Get user preferences from JSON file
    user_prefs = UserService.get_user_preferences(user_id)
    # Returns: {"style_aesthetics": ["minimalist", "modern"], ...}

    # Run LangGraph agent
    agent_result = await run_styling_agent(
        user_id=user_id,
        query=request.query,
        user_preferences=user_prefs
    )
```

### Step 3: LangGraph Agent Workflow

**app/services/langgraph_agent.py** (simplified flow)

```
START
  ↓
analyze_query → retrieve_user_context → retrieve_trend_context → generate_recommendations → END
```

**Node 1: Retrieve User Context**
```python
@tool
async def search_outfit_history(user_id: str, query: str):
    # Generate CLIP embedding for query
    query_embedding = await generate_clip_embedding(query)
    # "business meeting" → [0.234, -0.567, ...]

    # Search ChromaDB for similar outfits
    collection = chroma_client.get_collection("outfits")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where={"user_id": user_id}  # Filter by user
    )

    # Returns: Top 5 similar outfits from user's wardrobe
    # Based on cosine similarity of CLIP embeddings
```

**Node 2: Generate Recommendations**
```python
def generate_recommendations(state: AgentState):
    llm = ChatOpenAI(model="gpt-4-turbo")

    prompt = f"""
    User Query: {state['query']}
    User Preferences: {state['user_preferences']}
    Similar Outfits from Wardrobe: {state['outfit_context']}
    Fashion Trends: {state['trend_context']}

    Generate personalized styling recommendations.
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    # GPT-4 generates recommendations using RAG context

    state['recommendations'] = parse_recommendations(response)
```

### Step 4: Return to Frontend

**Frontend displays formatted response with bold text and line breaks**

---

## Part 4: Turn-Based State Machine Explained

### Why No Loop in ask_next_question()?

**IMPORTANT:** The onboarding flow is NOT a traditional loop. It's a **turn-based state machine** that operates across multiple HTTP requests.

### The ONBOARDING_STEPS Structure

```python
ONBOARDING_STEPS = {
    "greeting": {
        "question": "Welcome! ...",
        "next": "style_aesthetics"  # ← Pointer to next step
    },
    "style_aesthetics": {
        "question": "What style aesthetics...",
        "field": "style_aesthetics",
        "next": "colors"  # ← Pointer to next step
    },
    "colors": {
        "question": "What colors...",
        "field": "colors",
        "next": "occasions"  # ← Pointer to next step
    },
    "occasions": {
        "question": "What occasions...",
        "field": "occasions",
        "next": "fit_preferences"
    },
    "fit_preferences": {
        "question": "What fit...",
        "field": "fit_preferences",
        "next": "budget"
    },
    "budget": {
        "question": "What's your budget...",
        "field": "budget",
        "next": "body_type"
    },
    "body_type": {
        "question": "What's your body type...",
        "field": "body_type",
        "next": "style_goals"
    },
    "style_goals": {
        "question": "What are your style goals...",
        "field": "style_goals",
        "next": "photos"
    },
    "photos": {
        "question": "Great! Now upload photos...",
        "field": "photo_upload_requested",
        "next": "complete"
    },
    "complete": {
        "question": "Perfect! Let's start creating amazing outfits! 🎉",
        "next": None  # ← End of chain
    }
}
```

This is like a **linked list** - each step points to the next using the "next" field.

### How ask_next_question() Works

**app/services/onboarding_agent.py:171-199**

```python
def ask_next_question(state: OnboardingState):
    # Get current step info
    current_step_info = ONBOARDING_STEPS.get(state['current_step'])
    # Example: state['current_step'] = "greeting"
    # Returns: {"question": "Welcome...", "next": "style_aesthetics"}

    next_step = current_step_info['next']  # "style_aesthetics"

    if next_step is None or next_step == 'complete':
        # End of onboarding
        state['is_complete'] = True
        return state

    # Move to next step (UPDATE STATE)
    state['current_step'] = next_step  # Now "style_aesthetics"

    # Get the next question
    next_question = ONBOARDING_STEPS[next_step]['question']
    # "What style aesthetics do you prefer?"

    # Add to messages
    state['messages'].append(AIMessage(content=next_question))

    return state  # ← Returns and STOPS here
```

**Key Point:** The function **doesn't loop** - it:
1. Looks at `state['current_step']` (current position in the chain)
2. Gets the `next` pointer from ONBOARDING_STEPS
3. Updates `state['current_step']` to the next step
4. Returns ONE question
5. **STOPS and waits for the next HTTP request**

### The Turn-Taking Flow

Here's the actual execution sequence across multiple HTTP requests:

#### Turn 1: Initial Request

```
User clicks "Let's Get Started"
  ↓
POST /onboarding/start
  ↓
run_onboarding_agent(user_message=None, current_state=None)
  ↓
LangGraph: start_onboarding() → ask_next_question()
  ↓
ask_next_question():
  - current_step = "greeting"
  - next_step = ONBOARDING_STEPS["greeting"]["next"] = "style_aesthetics"
  - state['current_step'] = "style_aesthetics"
  - Return question: "What style aesthetics do you prefer?"
  ↓
Store state in _onboarding_states[user_id]
  ↓
Return to frontend with question
**STOPS HERE - WAITING FOR USER**
```

#### Turn 2: User Answers

```
User types: "I like minimalist and modern"
  ↓
POST /onboarding/respond
  ↓
Load state from _onboarding_states[user_id]
  - state['current_step'] = "style_aesthetics"
  ↓
run_onboarding_agent(
    user_message="I like minimalist and modern",
    current_state=<previous state>
)
  ↓
process_user_response():
  - Extract: ["minimalist", "modern"] using GPT-4
  - Store: collected_data["style_aesthetics"] = ["minimalist", "modern"]
  ↓
ask_next_question():
  - current_step = "style_aesthetics"
  - next_step = ONBOARDING_STEPS["style_aesthetics"]["next"] = "colors"
  - state['current_step'] = "colors"
  - Return question: "What are your favorite colors?"
  ↓
Update state in _onboarding_states[user_id]
  ↓
Return to frontend with question
**STOPS HERE - WAITING FOR USER**
```

#### Turn 3: User Answers Again

```
User types: "Navy, grey, white"
  ↓
POST /onboarding/respond
  ↓
Load state from _onboarding_states[user_id]
  - state['current_step'] = "colors"
  - state['collected_data'] = {"style_aesthetics": ["minimalist", "modern"]}
  ↓
run_onboarding_agent(
    user_message="Navy, grey, white",
    current_state=<state with current_step="colors">
)
  ↓
process_user_response():
  - Extract: ["navy", "grey", "white"] using GPT-4
  - Store: collected_data["colors"] = ["navy", "grey", "white"]
  ↓
ask_next_question():
  - current_step = "colors"
  - next_step = ONBOARDING_STEPS["colors"]["next"] = "occasions"
  - state['current_step'] = "occasions"
  - Return question: "What occasions do you dress for?"
  ↓
Update state in _onboarding_states[user_id]
  ↓
Return to frontend with question
**STOPS HERE - WAITING FOR USER**
```

#### This continues until completion...

### Why No Loop?

Because it's a **conversational API** - each HTTP request:
1. Receives user's answer
2. Processes it with GPT-4
3. Asks the **NEXT** question (following the "next" pointer)
4. Returns that ONE question
5. Waits for the next HTTP request

**The "loop" happens at the HTTP request level, not in the code:**

```
HTTP Request 1 (start)
  → Question 1
  → Return
  → Wait for user
       ↓
HTTP Request 2 (respond)
  → Process Answer 1
  → Question 2
  → Return
  → Wait for user
       ↓
HTTP Request 3 (respond)
  → Process Answer 2
  → Question 3
  → Return
  → Wait for user
       ↓
... continues until all questions answered
       ↓
HTTP Request N (respond)
  → Process Answer N-1
  → Mark is_complete = True
  → Save to database
  → Return completion message
```

### State Tracking Between Requests

The state is preserved in memory between HTTP requests:

**After Request 1 (START):**
```python
_onboarding_states[user_id] = {
    "current_step": "style_aesthetics",
    "collected_data": {},
    "is_complete": False,
    "messages": [...]
}
```

**After Request 2 (User answered "style_aesthetics"):**
```python
_onboarding_states[user_id] = {
    "current_step": "colors",  # ← Moved to next
    "collected_data": {
        "style_aesthetics": ["minimalist", "modern"]  # ← Stored answer
    },
    "is_complete": False,
    "messages": [...]
}
```

**After Request 3 (User answered "colors"):**
```python
_onboarding_states[user_id] = {
    "current_step": "occasions",  # ← Moved to next
    "collected_data": {
        "style_aesthetics": ["minimalist", "modern"],
        "colors": ["navy", "grey", "white"]  # ← Added new answer
    },
    "is_complete": False,
    "messages": [...]
}
```

**After Final Request (All questions answered):**
```python
_onboarding_states[user_id] = {
    "current_step": "complete",  # ← Reached end
    "collected_data": {
        "style_aesthetics": ["minimalist", "modern"],
        "colors": ["navy", "grey", "white"],
        "occasions": ["work", "casual"],
        "fit_preferences": "fitted",
        "budget": "mid-range",
        "body_type": "athletic",
        "style_goals": ["look professional", "stay comfortable"]
    },
    "is_complete": True,  # ← Onboarding complete
    "messages": [...]
}

# Then saved to: user_preferences/{user_id}.json
```

### Advantages of This Approach

1. **Natural Conversation Flow**: One question at a time, just like talking to a real stylist
2. **User Can Leave and Return**: State is preserved between sessions
3. **No Blocking**: Server doesn't wait - responds immediately and continues on next request
4. **Multi-User Support**: Each user has their own isolated state in the dictionary
5. **Easy to Debug**: Each step is a clear HTTP request/response you can inspect

### Summary: No Loop, Just Pointers!

- ❌ **NOT a for/while loop** iterating through questions
- ✅ **IS a linked list traversal** using "next" pointers
- ✅ **One question per HTTP request/response**
- ✅ **State preserved between requests** in `_onboarding_states`
- ✅ **Advances one step at a time** by following the "next" chain

The brilliance is that it *feels* like a conversation while being completely stateless per request!

---

## Visual Flow Diagram

```
USER INTERACTION
       ↓
┌──────────────────────────────────────────────────────────────┐
│  ONBOARDING FLOW (Turn-Based State Machine)                  │
├──────────────────────────────────────────────────────────────┤
│ Turn 1:                                                       │
│   1. Click "Start" (Frontend)                                │
│   2. POST /onboarding/start                                  │
│   3. run_onboarding_agent(user_message=None)                 │
│   4. LangGraph: start → ask_question                         │
│   5. ask_next_question():                                    │
│      - current_step="greeting" → next="style_aesthetics"     │
│      - Update: current_step="style_aesthetics"               │
│   6. Return: "What style aesthetics do you prefer?"          │
│   7. Store state in _onboarding_states[user_id]              │
│   **WAIT FOR USER**                                          │
│                                                              │
│ Turn 2:                                                       │
│   1. User types answer (Frontend)                            │
│   2. POST /onboarding/respond                                │
│   3. Load state from _onboarding_states[user_id]             │
│   4. run_onboarding_agent(user_message="...")                │
│   5. process_user_response():                                │
│      - GPT-4 extracts: ["minimalist", "modern"]              │
│      - Store in collected_data                               │
│   6. ask_next_question():                                    │
│      - current_step="style_aesthetics" → next="colors"       │
│      - Update: current_step="colors"                         │
│   7. Return: "What are your favorite colors?"                │
│   8. Update state in _onboarding_states[user_id]             │
│   **WAIT FOR USER**                                          │
│                                                              │
│ Turn 3-8: Repeat for remaining questions...                  │
│                                                              │
│ Final Turn:                                                   │
│   1. Process last answer                                     │
│   2. ask_next_question() detects next=None                   │
│   3. Set is_complete=True                                    │
│   4. save_onboarding_data()                                  │
│      → Save to user_preferences/{user_id}.json               │
│   5. Clear from _onboarding_states[user_id]                  │
└──────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────┐
│  PHOTO UPLOAD FLOW                                           │
├──────────────────────────────────────────────────────────────┤
│ 1. User selects photos (Frontend)                            │
│ 2. POST /onboarding/upload-photos                            │
│ 3. ImageService.validate_image()                             │
│ 4. generate_clip_embedding()                                 │
│    → CLIP model creates 512-D vector for each image          │
│ 5. upload_to_gcs() (optional, if GCS configured)             │
│ 6. store_in_chromadb()                                       │
│    → collection.add(embeddings, ids, metadatas)              │
│    → Indexed by user_id for isolation                        │
│    → Stored in ChromaDB for semantic search                  │
└──────────────────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────────────────┐
│  STYLING QUERY FLOW (RAG with Vector Search)                 │
├──────────────────────────────────────────────────────────────┤
│ 1. User asks question (Frontend)                             │
│    "What should I wear for a business meeting?"              │
│ 2. POST /styling/query                                       │
│ 3. run_styling_agent()                                       │
│ 4. LangGraph Workflow:                                       │
│    a. get_user_preferences()                                 │
│       → Read from user_preferences/{user_id}.json            │
│       → Returns: style, colors, budget, etc.                 │
│                                                              │
│    b. search_outfit_history()                                │
│       → Generate CLIP embedding for query                    │
│       → "business meeting" → 512-D vector                    │
│       → ChromaDB.query(embedding, where={user_id})           │
│       → Returns top 5 similar outfits                        │
│       → Based on cosine similarity                           │
│                                                              │
│    c. search_fashion_trends()                                │
│       → Get current trends (mock data for POC)               │
│                                                              │
│    d. generate_recommendations()                             │
│       → Compile all context:                                 │
│         * User query                                         │
│         * User preferences                                   │
│         * Similar outfits from wardrobe (RAG)                │
│         * Fashion trends                                     │
│       → Feed to GPT-4                                        │
│       → GPT-4 generates personalized recommendations         │
│                                                              │
│ 5. Format and return response                                │
│    → Frontend displays with formatting                       │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Architectural Points

### 1. Onboarding Uses GPT-4 for NLP
- User answers in natural language
- GPT-4 parses and extracts structured data
- No need for rigid forms or dropdowns

### 2. Photos → CLIP Embeddings → ChromaDB
- CLIP converts images to 512-dimensional vectors
- Semantic similarity: "formal outfit" finds blazers, not just keyword matches
- Each user's photos are isolated by user_id

### 3. Styling Queries Use RAG (Retrieval Augmented Generation)
- Query → CLIP embedding → ChromaDB search
- Retrieve similar outfits from user's wardrobe
- Feed context to GPT-4 for personalized recommendations

### 4. Multi-User Isolation
- Firebase UID used throughout
- State stored per user_id
- ChromaDB filters by user_id
- No data leakage between users

### 5. Stateless Conversations (POC)
- Each styling query is independent
- No conversation history preserved
- Simple and sufficient for demo
- Can be upgraded to stateful for production

---

## Data Flow Summary

```
User Input (Natural Language)
    ↓
GPT-4 Extraction → Structured Data
    ↓
Saved to JSON → user_preferences/{user_id}.json
    ↓
User Photos
    ↓
CLIP Model → 512-D Embeddings
    ↓
ChromaDB → Vector Storage (searchable)
    ↓
User Query
    ↓
CLIP Embedding → ChromaDB Search → Retrieved Context
    ↓
Context + Preferences + Query → GPT-4
    ↓
Personalized Recommendations → User
```

---

## Files Reference

### Core Files
- **app/api/onboarding.py** - Onboarding HTTP endpoints
- **app/api/styling.py** - Styling query HTTP endpoints
- **app/services/onboarding_agent.py** - LangGraph onboarding workflow
- **app/services/langgraph_agent.py** - LangGraph styling workflow
- **app/services/image_service.py** - CLIP embeddings and image processing
- **app/services/user_service.py** - User preference storage
- **frontend/index.html** - Complete frontend UI

### Configuration
- **.env** - Environment variables (API keys, Firebase config)
- **app/config.py** - Application configuration
- **app/core/security.py** - Firebase authentication

---

## Conclusion

The StylistAI flow demonstrates a modern AI application architecture:

1. **Conversational UI** with turn-based state machine
2. **LLM-powered data extraction** for natural language input
3. **Vector embeddings** for semantic similarity search
4. **RAG (Retrieval Augmented Generation)** for personalized recommendations
5. **Multi-user support** with proper isolation
6. **Simple but effective** POC architecture

The beauty is that it combines multiple AI technologies (GPT-4, CLIP, ChromaDB) into a cohesive user experience that feels natural and intelligent!
