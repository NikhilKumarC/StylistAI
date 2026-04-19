# StylistAI - Architecture Diagrams (Mermaid)

## 📊 Use These Diagrams in Your Presentation

Copy and paste these Mermaid diagrams into your presentation tool, Mermaid Live Editor, or Markdown viewer.

---

## 1️⃣ Overall System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[React/HTML5 Frontend<br/>📱 Responsive UI]
        Chat[Chat Interface<br/>💬 Conversational UX]
    end

    subgraph "API Gateway"
        FastAPI[FastAPI Server<br/>⚡ Async/Await]
        Auth[Firebase Auth<br/>🔐 JWT Tokens]
    end

    subgraph "Multi-Agent System"
        Orchestrator[API Orchestrator<br/>🎯 Pure Sequential Pattern]

        subgraph "Agent 0: Onboarding Agent"
            OnboardAgent[LangGraph Agent<br/>👋 First-Time Setup]
            PhotoUpload[Photo Upload<br/>📸 Wardrobe Processing]
        end

        subgraph "Agent 1: Conversational Stylist"
            ConvAgent[LangGraph Agent<br/>💬 Context Gathering]
            WeatherTool[Weather Tool<br/>🌤️ Autonomous Calling]
        end

        subgraph "Agent 2: Recommendation Engine"
            RecAgent[LangGraph Agent<br/>🎨 Outfit Generation]
            PrefTool[User Preferences<br/>👤 PostgreSQL]
            WardrobeTool[Wardrobe Search<br/>👔 Vector Similarity]
            TrendTool[Trend Search<br/>📈 Optional]
        end
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL<br/>👥 User Data)]
        ChromaDB[(ChromaDB<br/>🎨 Vector Embeddings)]
        Storage[File Storage<br/>📁 Images]
    end

    subgraph "AI Models"
        GPT4[GPT-4 Turbo<br/>🧠 LLM Reasoning]
        CLIP[CLIP ViT-B/32<br/>👁️ Vision Embeddings]
    end

    subgraph "Observability"
        Datadog[Datadog LLM Obs<br/>📊 Token Tracking]
    end

    UI --> FastAPI
    Chat --> FastAPI
    FastAPI --> Auth
    Auth --> Orchestrator

    %% Onboarding Flow
    Orchestrator -->|New User| OnboardAgent
    OnboardAgent --> GPT4
    OnboardAgent -->|Save Preferences| PostgreSQL
    OnboardAgent --> PhotoUpload
    PhotoUpload -->|Process Images| CLIP
    CLIP -->|Store Embeddings| ChromaDB
    PhotoUpload -->|Save Metadata| PostgreSQL
    PhotoUpload -->|Store Files| Storage

    %% Conversational Agent Flow
    Orchestrator -->|Step 1| ConvAgent
    ConvAgent --> GPT4
    ConvAgent --> WeatherTool

    %% Recommendation Agent Flow
    Orchestrator -->|Step 2<br/>When Ready| RecAgent
    RecAgent --> GPT4
    RecAgent --> PrefTool
    RecAgent --> WardrobeTool
    RecAgent --> TrendTool

    %% Tool to Data Layer Connections
    PrefTool -->|Read| PostgreSQL
    WardrobeTool -->|Query| ChromaDB
    WardrobeTool -->|Encode Query| CLIP
    Storage -.->|Load Images| WardrobeTool

    %% Observability
    GPT4 -.->|Traces| Datadog
    FastAPI -.->|Metrics| Datadog

    style UI fill:#e1f5ff
    style FastAPI fill:#fff3e0
    style OnboardAgent fill:#ffe0b2
    style ConvAgent fill:#f3e5f5
    style RecAgent fill:#e8f5e9
    style ChromaDB fill:#fce4ec
    style Datadog fill:#fff9c4
```

---

## 2️⃣ Multi-Agent Conversation Flow (Pure Sequential Pattern)

```mermaid
sequenceDiagram
    participant User
    participant API as API Orchestrator
    participant Agent1 as Agent 1<br/>Conversational
    participant Weather as Weather Tool
    participant Agent2 as Agent 2<br/>Recommendation
    participant Wardrobe as Vector Search
    participant DB as ChromaDB

    User->>API: "I need an outfit for<br/>interview in Madison Monday"

    Note over API: Step 1: Gather Context
    API->>Agent1: Process message + history

    Agent1->>Agent1: Analyze query<br/>(autonomous decision)
    Agent1->>Weather: get_weather_info("Madison", "Monday")
    Weather-->>Agent1: 35-55°F, winter, cool

    Agent1-->>API: Response + weather_info<br/>needs_more_context=False

    Note over API: Check Readiness Signals:<br/>✅ has_weather=True<br/>✅ min_conversation_depth=True<br/>→ Context Complete!

    Note over API: Step 2: Generate Recommendations
    API->>Agent2: Enriched query + weather context

    Agent2->>Agent2: Analyze query<br/>(autonomous decision)
    Agent2->>Wardrobe: search_outfit_history(<br/>"business casual winter")
    Wardrobe->>DB: Vector similarity search
    DB-->>Wardrobe: Top 3 matches<br/>(20%, 19%, 18% similarity)
    Wardrobe-->>Agent2: Wardrobe images + metadata

    Agent2->>Agent2: Generate recommendations<br/>combining wardrobe + generic
    Agent2-->>API: Recommendations + images

    API-->>User: "Here are options from YOUR wardrobe"<br/>🖼️ [Image 1] [Image 2] [Image 3]

    Note over User,API: Follow-up: "Show me more options"
    User->>API: "Show me more blazer options"

    Note over API: Reuse cached weather!<br/>No need to fetch again
    API->>Agent1: Process message + cached weather
    Agent1-->>API: needs_more_context=False<br/>(weather cached)
    API->>Agent2: Direct to recommendations
    Agent2->>Wardrobe: search_outfit_history("blazer")
    Wardrobe-->>Agent2: Different matches
    Agent2-->>API: New recommendations
    API-->>User: Updated wardrobe suggestions
```

---

## 3️⃣ Wardrobe Image Processing Pipeline

```mermaid
graph LR
    subgraph "User Upload"
        Upload[Upload Photos<br/>📸 3-5 Images]
        Validate[Validation<br/>✓ Format, Size]
    end

    subgraph "Image Processing"
        Load[Load Image<br/>PIL/Pillow]
        Preprocess[Preprocessing<br/>Resize, Normalize]
        CLIP[CLIP Model<br/>ViT-B/32]
        Embed[Generate Embedding<br/>512-dim vector]
    end

    subgraph "Storage"
        Local[Local Storage<br/>📁 /uploads/outfits/]
        GCS[Google Cloud Storage<br/>☁️ Optional]
    end

    subgraph "Vector Database"
        Chroma[ChromaDB<br/>Collection: 'outfits']
        Index[HNSW Index<br/>Fast Similarity Search]
    end

    subgraph "Metadata"
        Postgres[(PostgreSQL<br/>user_id, filename,<br/>upload_date)]
    end

    Upload --> Validate
    Validate -->|Valid| Load
    Load --> Preprocess
    Preprocess --> CLIP
    CLIP --> Embed

    Embed --> Local
    Embed --> GCS
    Embed --> Chroma
    Embed --> Postgres

    Chroma --> Index

    Local -.->|Serve| URL[Image URLs<br/>/uploads/...]

    style Upload fill:#e1f5ff
    style CLIP fill:#f3e5f5
    style Chroma fill:#fce4ec
    style Index fill:#fff9c4
```

---

## 4️⃣ Semantic Wardrobe Search Flow

```mermaid
graph TB
    Query[User Query:<br/>"show me business casual"]

    subgraph "Query Processing"
        Text[Text Query]
        CLIPText[CLIP Text Encoder]
        QueryEmbed[Query Embedding<br/>512-dim vector]
    end

    subgraph "Vector Search"
        ChromaDB[(ChromaDB<br/>User's Wardrobe)]
        Similarity[Cosine/L2 Distance<br/>Similarity Calculation]
        Rank[Rank by Similarity<br/>Top K Results]
    end

    subgraph "Post-Processing"
        Convert[Distance → Similarity %<br/>exp(-distance/100)]
        Filter[Filter & Format<br/>Extract metadata]
        URLs[Generate Image URLs<br/>/uploads/...]
    end

    subgraph "Response"
        Results[Wardrobe Matches<br/>With Similarity Scores]
        Display[Display in UI<br/>📊 20%, 19%, 18%]
    end

    Query --> Text
    Text --> CLIPText
    CLIPText --> QueryEmbed

    QueryEmbed --> ChromaDB
    ChromaDB --> Similarity
    Similarity --> Rank

    Rank --> Convert
    Convert --> Filter
    Filter --> URLs

    URLs --> Results
    Results --> Display

    style Query fill:#e1f5ff
    style CLIPText fill:#f3e5f5
    style ChromaDB fill:#fce4ec
    style Display fill:#e8f5e9
```

---

## 5️⃣ User Journey Flow

```mermaid
flowchart TD
    Start([New User Visits Site]) --> Login{Has Account?}

    Login -->|No| Signup[Sign Up<br/>Firebase Auth]
    Login -->|Yes| SignIn[Sign In<br/>Firebase Auth]

    Signup --> OnboardStart[Start Onboarding]
    SignIn --> CheckOnboard{Onboarding<br/>Complete?}

    CheckOnboard -->|No| OnboardStart
    CheckOnboard -->|Yes| MainChat[Main Chat Interface]

    OnboardStart --> OnboardAgent[Conversational Agent<br/>Gathers Preferences]
    OnboardAgent --> StyleQs[Style Questions<br/>Occasions, Colors, etc.]
    StyleQs --> PhotoUpload{Upload<br/>Wardrobe?}

    PhotoUpload -->|Yes| UploadPhotos[Upload 3-5 Photos]
    PhotoUpload -->|No| Skip[Skip Photos]

    UploadPhotos --> ProcessImages[Process Images<br/>CLIP Embeddings]
    ProcessImages --> StoreVectors[Store in ChromaDB]

    StoreVectors --> MainChat
    Skip --> MainChat

    MainChat --> UserQuery[User Types Query]
    UserQuery --> ConvAgent[Agent 1:<br/>Gather Context]

    ConvAgent --> CheckWeather{Need<br/>Weather?}
    CheckWeather -->|Yes| FetchWeather[Fetch Weather<br/>Autonomous]
    CheckWeather -->|No| CheckReady
    FetchWeather --> CheckReady

    CheckReady{Context<br/>Complete?} -->|No| AskMore[Ask More Questions]
    AskMore --> UserQuery

    CheckReady -->|Yes| RecAgent[Agent 2:<br/>Generate Recommendations]
    RecAgent --> SearchWardrobe[Search Wardrobe<br/>Vector Similarity]

    SearchWardrobe --> ShowResults[Display Results<br/>Images + Text]
    ShowResults --> FollowUp{Follow-up<br/>Question?}

    FollowUp -->|Yes| UserQuery
    FollowUp -->|No| End([Session End])

    style Start fill:#4caf50,color:#fff
    style MainChat fill:#2196f3,color:#fff
    style SearchWardrobe fill:#ff9800,color:#fff
    style ShowResults fill:#9c27b0,color:#fff
    style End fill:#f44336,color:#fff
```

---

## 6️⃣ Agent Decision Making (Autonomous Tool Calling)

```mermaid
graph TD
    subgraph "LLM Decision Process"
        Query[User Query]
        LLM[GPT-4 Turbo<br/>🧠 Reasoning Engine]
        Analyze[Analyze Intent<br/>What tools needed?]
    end

    subgraph "Tool Selection Logic"
        Decision{Query Type?}

        Decision -->|"outfit for interview"| UseAll[Use Multiple Tools:<br/>✅ get_user_preferences<br/>✅ search_outfit_history<br/>❌ search_fashion_trends]

        Decision -->|"what's trending"| UseTrends[Use Trend Tool:<br/>❌ get_user_preferences<br/>❌ search_outfit_history<br/>✅ search_fashion_trends]

        Decision -->|"show my wardrobe"| UseWardrobe[Use Wardrobe Only:<br/>❌ get_user_preferences<br/>✅ search_outfit_history<br/>❌ search_fashion_trends]

        Decision -->|"general advice"| UseNone[Use No Tools:<br/>GPT-4 knowledge only]
    end

    subgraph "Tool Execution"
        UseAll --> Execute[Execute Selected Tools]
        UseTrends --> Execute
        UseWardrobe --> Execute
        UseNone --> Generate

        Execute --> Results[Gather Tool Results]
        Results --> Generate[Generate Response<br/>Based on Tool Data]
    end

    Query --> LLM
    LLM --> Analyze
    Analyze --> Decision
    Generate --> Output[Final Response<br/>with Recommendations]

    style LLM fill:#9c27b0,color:#fff
    style Decision fill:#ff9800,color:#fff
    style Execute fill:#4caf50,color:#fff
    style Output fill:#2196f3,color:#fff
```

---

## 7️⃣ Data Architecture & Storage

```mermaid
erDiagram
    USERS ||--o{ USER_PREFERENCES : has
    USERS ||--o{ OUTFIT_IMAGES : uploads
    USERS ||--o{ ONBOARDING_STATE : completes
    OUTFIT_IMAGES ||--o{ IMAGE_EMBEDDINGS : generates

    USERS {
        string user_id PK "Firebase UID"
        string email
        datetime created_at
        datetime last_login
    }

    USER_PREFERENCES {
        string user_id PK,FK
        json occasions "['professional', 'casual']"
        json style_aesthetics "['minimalist', 'classic']"
        json colors "['navy', 'white', 'black']"
        string fit_preferences
        string budget
        string body_type
        string default_location
    }

    OUTFIT_IMAGES {
        string image_id PK
        string user_id FK
        string filename
        string local_path
        string gcs_url "Optional cloud storage"
        int file_size
        datetime uploaded_at
        string source "onboarding | manual_upload"
    }

    IMAGE_EMBEDDINGS {
        string image_id PK,FK
        string user_id FK
        vector embedding "512-dim CLIP vector"
        string collection_name
        datetime created_at
    }

    ONBOARDING_STATE {
        string user_id PK,FK
        boolean completed
        int current_step
        json collected_data
        datetime completed_at
    }
```

---

## 8️⃣ Technology Stack Overview

```mermaid
mindmap
  root((StylistAI<br/>Tech Stack))
    Frontend
      HTML5/JavaScript
      Firebase Auth SDK
      Responsive Design
    Backend
      FastAPI
        Async/Await
        Pydantic Models
        Dependency Injection
      LangChain
        LangGraph Agents
        Tool Calling
        State Management
    AI/ML
      OpenAI GPT-4 Turbo
      CLIP ViT-B/32
      Vector Embeddings
      Semantic Search
    Data
      PostgreSQL
        User Data
        Preferences
        Metadata
      ChromaDB
        Vector Storage
        HNSW Index
        Similarity Search
      File Storage
        Local Uploads
        GCS Ready
    Observability
      Datadog LLM Obs
        Token Tracking
        Cost Monitoring
        Trace Analysis
      Logging
        Python logging
        Structured logs
    Infrastructure
      Docker Ready
      uvicorn Server
      Environment Config
```

---

## 9️⃣ Deployment Architecture (Future Production)

```mermaid
graph TB
    subgraph "Client Layer"
        Web[Web App<br/>React/Next.js]
        Mobile[Mobile App<br/>React Native]
    end

    subgraph "CDN & Load Balancer"
        CDN[CloudFlare CDN<br/>Static Assets]
        LB[Load Balancer<br/>Nginx/AWS ALB]
    end

    subgraph "Application Layer"
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
        API3[FastAPI Instance 3]
    end

    subgraph "Service Layer"
        Agent[Agent Service<br/>LangGraph Workers]
        CLIP[CLIP Service<br/>GPU Inference]
        Weather[Weather Service<br/>External API]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Primary)]
        PGR[(PostgreSQL<br/>Read Replica)]
        Redis[Redis<br/>Session Cache]
        Chroma[(ChromaDB<br/>Vector Store)]
    end

    subgraph "Storage"
        GCS[Google Cloud Storage<br/>Image Hosting]
    end

    subgraph "Monitoring"
        DD[Datadog<br/>Metrics & Traces]
        Sentry[Sentry<br/>Error Tracking]
    end

    Web --> CDN
    Mobile --> LB
    CDN --> LB

    LB --> API1
    LB --> API2
    LB --> API3

    API1 --> Agent
    API2 --> Agent
    API3 --> Agent

    Agent --> CLIP
    Agent --> Weather

    API1 --> PG
    API2 --> PGR
    API1 --> Redis
    API1 --> Chroma

    CLIP --> Chroma
    API1 --> GCS

    API1 -.-> DD
    API2 -.-> DD
    API3 -.-> DD
    Agent -.-> DD

    API1 -.-> Sentry

    style Web fill:#e1f5ff
    style LB fill:#fff3e0
    style Agent fill:#f3e5f5
    style Chroma fill:#fce4ec
    style DD fill:#fff9c4
```

---

## 🎯 How to Use These Diagrams

### **For Presentation Slides:**

1. **Copy Mermaid code** from above
2. **Paste into Mermaid Live Editor**: https://mermaid.live/
3. **Export as PNG/SVG** for slides
4. **Or use Mermaid plugins** for PowerPoint/Google Slides

### **Recommended Diagram Flow for Presentation:**

1. **Slide 3**: Overall System Architecture (#1)
2. **Slide 5** (after demo): Multi-Agent Conversation Flow (#2)
3. **Slide 6**: Semantic Wardrobe Search Flow (#4)
4. **Slide 7**: Technology Stack Overview (#8)
5. **Backup Slides**: Others for technical deep-dive questions

### **Print/Poster:**
- Use diagrams #1, #2, #4 in high resolution
- Mermaid Live Editor supports export up to 4K resolution

### **Documentation:**
- All diagrams render automatically in GitHub/GitLab
- Use in README.md or technical documentation

---

## 📝 Diagram Customization Tips

Want to modify the diagrams? Here are the Mermaid color codes used:

- Blue (`#e1f5ff`) = User-facing components
- Orange (`#fff3e0`) = API/Gateway layer
- Light Orange (`#ffe0b2`) = Onboarding/Setup components
- Purple (`#f3e5f5`) = Conversational Agent components
- Green (`#e8f5e9`) = Recommendation Agent components
- Pink (`#fce4ec`) = Vector/ML components
- Yellow (`#fff9c4`) = Observability/Monitoring

Change colors by editing the `style` lines at the bottom of each diagram.

---

**Good luck with your presentation! These diagrams will help judges understand your technical sophistication.** 🎨📊
