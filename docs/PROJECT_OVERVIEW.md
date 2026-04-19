# StylistAI - Project Overview

## Inspiration

Fashion is personal, yet most of us struggle with daily styling decisions. We have closets full of clothes but still feel we have "nothing to wear." We see trending styles on social media but don't know how to recreate them with what we own. And when we do need to buy something new, we're overwhelmed by endless options with no guidance on what actually complements our existing wardrobe.

The problem? **Existing fashion solutions are incomplete.** Trend websites show what's popular but ignore your actual wardrobe. Wardrobe apps catalog your clothes but offer no styling direction. Shopping sites recommend products without knowing your style or what you already own. Personal stylists are expensive and inaccessible. What we really need is a **fashion advisor** that understands three things - your closet, the runway, AND smart shopping recommendations when needed.

That's why we built StylistAI: an AI-powered fashion advisor that combines **personalized wardrobe intelligence** with **real-time trend awareness**, and as our next major step, **smart vendor recommendations** for when you do need to shop. Using breakthrough AI technologies - **GPT-4 for conversation**, **CLIP for visual understanding**, and **intelligent trend analysis** - StylistAI acts as your personal stylist who knows every piece you own, stays current with what's trending, and will guide you to buy pieces that match your personal style preferences and current fashion trends.

Imagine asking: *"What's a trendy outfit for a weekend brunch?"* and getting recommendations using clothes from YOUR closet, styled in ways that are actually in fashion right now. And if you're missing a key piece, StylistAI will suggest exactly where to buy it. That's StylistAI - your complete fashion advisor that bridges your wardrobe, the runway, and smart shopping.

---

## What it does

**StylistAI is your AI personal stylist that knows your wardrobe AND what's trending.** It combines conversational AI, computer vision, and real-time fashion intelligence to provide personalized recommendations that blend clothes you already own with current style trends.

> **Note:** Currently, StylistAI focuses on **wardrobe search** and **style recommendations based on trends**. Smart shopping recommendations from vendors will be added as the next major feature enhancement.

### Core Features

1. **Visual Wardrobe Memory**
   - Upload 3-5 photos of your clothes during onboarding
   - AI creates semantic embeddings using CLIP (OpenAI's vision-language model)
   - Search your wardrobe in plain English: "show me business casual" or "blue dresses"
   - Returns actual items from your closet with similarity scores (e.g., 20%, 19%, 18%)

2. **Natural Conversation**
   - Chat like you're texting a friend: *"I have an interview in Madison on Monday"*
   - No boring forms or dropdowns - just natural dialogue
   - AI autonomously gathers context through conversation

3. **Climate-Aware Recommendations**
   - AI automatically fetches weather data when it detects location + date mentions
   - Recommendations adjust for temperature, precipitation, and season
   - Weather context persists across conversation for natural follow-ups

4. **Personalized Styling with Trend Intelligence**
   - Learns your style preferences, color preferences, and fit preferences during onboarding
   - Every recommendation considers your unique taste
   - Combines your wardrobe items with current fashion trends and seasonal insights
   - Suggests how to style existing pieces in trending ways

### Example Conversation

**You**: *"I need an outfit for an interview Monday in Chicago"*
**StylistAI**: *Autonomously fetches Chicago weather for Monday*
**StylistAI**: *"It'll be 45°F and cloudy. I found your navy blazer (similarity: 22%), white button-down (19%), and grey slacks (18%). Here's why this works..."*
**You**: *"Show me more blazer options"*
**StylistAI**: *Searches wardrobe again, reusing weather context*

---

## How we built it

### Architecture: Multi-Agent Orchestration

We built a **sophisticated 3-agent system** using **LangGraph** and **GPT-4 Turbo**, orchestrated by the API in a pure sequential pattern:

**Agent 0: Onboarding Agent**
- Conversationally gathers style preferences (no boring forms)
- Processes wardrobe photo uploads
- Generates CLIP embeddings and stores in ChromaDB vector database
- Saves preferences to PostgreSQL

**Agent 1: Conversational Stylist**
- Gathers context through natural dialogue
- **Autonomously decides** when to fetch weather data using GPT-4 function calling
- Detects readiness signals: weather context + conversation depth + explicit wardrobe requests
- Returns structured context to API orchestrator

**Agent 2: Recommendation Engine**
- Receives enriched query with weather context from API
- **Autonomously selects** which tools to use (0-3 tools):
  - `get_user_preferences` - Fetch style preferences
  - `search_outfit_history` - Vector search wardrobe using CLIP embeddings
  - `search_fashion_trends` - Optional trend data
- Combines wardrobe items with fashion advice
- Returns recommendations + wardrobe images + reasoning

### Technology Stack

**Backend**
- **FastAPI** (Python 3.11+) with async/await for high performance
- **Firebase Authentication** for secure user management (JWT tokens)
- **PostgreSQL** for user data, preferences, and metadata
- Pydantic models for type safety and validation

**AI/ML Layer**
- **LLM**: OpenAI GPT-4 Turbo for reasoning and conversation
- **Vision**: CLIP ViT-B/32 for image-text embeddings (512-dimensional vectors)
- **Framework**: LangChain + LangGraph for agent orchestration
- **Vector Database**: ChromaDB with HNSW indexing for sub-second similarity search

**Observability**
- **Datadog LLM Observability** for comprehensive monitoring:
  - Token usage tracking across all GPT-4 calls
  - Cost monitoring (discovered 3x higher token usage than expected)
  - Request latency analysis and bottleneck identification
  - Trace analysis for multi-agent workflows
- Structured Python logging for debugging
- Performance monitoring for search latency and API response times

**Frontend**
- HTML5/JavaScript with responsive design
- Firebase Auth SDK for authentication
- Real-time chat interface with typing indicators
- Image display with similarity scores

### Key Technical Innovations

1. **Semantic Image Search**
   - CLIP creates embeddings in a shared space for images and text
   - Your query "business casual" and your blazer photo live in the same 512-dimensional vector space
   - ChromaDB performs cosine similarity search to find matches
   - Result: Search your wardrobe like Google - in plain English

2. **Autonomous Tool Calling**
   - Agents use GPT-4's function calling to decide which tools to use
   - No hardcoded "if weather then fetch" rules
   - LLM-driven decision making: Agent 1 makes 0-1 weather calls, Agent 2 makes 0-3 tool calls
   - Reduces unnecessary API calls and latency

3. **Context Caching**
   - Weather data persists across conversation turns
   - User: *"I need outfit for Monday in Madison"* → weather fetched
   - User: *"Show me more blazer options"* → weather reused
   - Natural conversation flow without repeated API calls

4. **Exponential Decay Similarity Scoring**
   - Challenge: ChromaDB L2 distances in 512-dim space are 150-200+ (curse of dimensionality)
   - Solution: `exp(-distance/100)` to convert to meaningful 15-25% similarity scores
   - Users see intuitive percentages instead of raw distances

---

## Challenges we ran into

### 1. High-Dimensional Vector Search Scoring
**Problem**: ChromaDB returns L2 distances that are 150-200+ in 512-dimensional space. Linear scaling produced negative percentages or meaningless scores.

**Solution**: We implemented exponential decay with scale factor tuning: `similarity = exp(-distance/100)`. This accounts for the curse of dimensionality and produces intuitive 15-25% similarity scores that users can understand.

### 2. Multi-Agent Orchestration Complexity
**Problem**: Coordinating 3 specialized agents without creating spaghetti code or complex state machines. Initial attempts used "agent-as-tool" patterns that led to circular dependencies.

**Solution**: We adopted a **pure sequential pattern** where the API explicitly orchestrates agent flow:
1. API invokes Agent 1 (context gathering)
2. API receives structured output
3. API invokes Agent 2 (recommendations) with enriched context

This pattern provides clear separation of concerns, better debugging, and easier observability.

### 3. Autonomous Tool Selection (Avoiding Wasted API Calls)
**Problem**: How do we avoid unnecessary weather API calls or wardrobe searches? Hardcoding rules like "if query contains location, fetch weather" is brittle and doesn't scale.

**Solution**: We leverage **GPT-4's native function calling** to let the LLM autonomously decide:
- Agent 1: "Does this query need weather data?" (0 or 1 call)
- Agent 2: "Which tools do I need?" (0-3 calls: preferences, wardrobe, trends)

This reduces costs, latency, and makes the system more intelligent over time.

### 4. Async User Context Propagation
**Problem**: LangGraph tools need `user_id` to query databases, but function signatures can't include it (LangChain expects specific parameters).

**Solution**: We used Python's **ContextVar** for thread-safe async context propagation. User context is set at the API layer and automatically available to all tools without explicit parameters.

### 5. Conversation Continuity
**Problem**: Multi-turn conversations lose context. User says "I have an interview Monday" (turn 1), then "show me more options" (turn 2) - how does Agent 2 remember the weather?

**Solution**: We implemented **conversation history** + **weather caching**:
- Agent 1 stores weather data in conversation state
- Agent 2 receives full conversation history including cached weather
- Readiness detection: Agent 1 signals when it has enough context to invoke Agent 2

### 6. CLIP Model Loading Performance
**Problem**: Loading CLIP ViT-B/32 model takes 3-5 seconds on every request, causing timeout issues.

**Solution**: We implemented **lazy loading with module-level caching**. The CLIP model loads once when the module is imported and persists across requests, reducing inference time to 50ms per image.

---

## Accomplishments that we're proud of

### Technical Achievements

1. **Production-Ready Multi-Agent System**
   - Built a sophisticated 3-agent architecture with autonomous tool calling
   - Achieved true LLM-driven orchestration (not hardcoded rules)
   - Implemented in 6 weeks from scratch

2. **Sub-Second Vector Search at Scale**
   - ChromaDB + HNSW indexing enables <500ms search latency
   - Scales to 10,000+ wardrobe items per user
   - 85%+ semantic search relevance based on testing

3. **End-to-End AI Pipeline with Production Observability**
   - Integrated 4 major technologies: GPT-4, CLIP, ChromaDB, Firebase
   - **Datadog LLM Observability** revealed critical insights: caught 3x token usage inefficiency, identified latency bottlenecks in agent orchestration
   - Cost-efficient: ~$0.01 per query (2,500 tokens) after optimization

4. **Seamless User Experience**
   - Natural conversation that feels like texting a friend
   - Image search works in plain English (no tagging required)
   - Weather integration is completely automatic
   - Real-time responses with typing indicators

### Innovation Highlights

- **First fashion AI** that combines conversational agents, computer vision, real-time context, and trend intelligence
- **Autonomous decision-making**: Agents intelligently choose which tools to use
- **Semantic search**: Search wardrobe by concept ("business casual") not tags
- **Trend-aware recommendations**: Bridges your closet and the runway
- **Sustainability focus**: Help users wear 80% of wardrobe instead of 20%

### Results

- Processed 100+ real wardrobe photos
- Tested with multiple user scenarios (interviews, dates, travel)
- Achieved 2-4 second end-to-end response times
- Successfully deployed locally with Firebase Auth + PostgreSQL + ChromaDB

---

## What we learned

### Technical Learnings

1. **LangGraph is powerful but complex**
   - Great for agent orchestration with built-in state management
   - Learning curve: Understanding when to use StateGraph vs explicit orchestration
   - Pure sequential patterns are simpler and more maintainable than agent-as-tool patterns

2. **Vector embeddings are magical but tricky**
   - CLIP creates a shared semantic space for images and text (mind-blowing!)
   - High-dimensional vectors behave counterintuitively (curse of dimensionality)
   - Similarity scoring requires careful tuning (exponential decay > linear scaling)

3. **LLM function calling is underrated**
   - GPT-4 autonomously deciding which tools to use is incredibly powerful
   - Reduces hardcoded logic and makes systems more adaptive
   - Proper tool descriptions are critical for reliable behavior

4. **Context management is crucial**
   - ContextVar in Python is perfect for async user_id propagation
   - Weather caching dramatically improves conversation flow
   - Conversation history must be carefully managed to avoid token bloat

5. **Observability is essential**
   - Datadog LLM Observability revealed we were using 3x more tokens than expected
   - Structured logging saved hours of debugging agent decision-making
   - Cost tracking is critical when using GPT-4 ($0.01 per query adds up!)

### Product Learnings

1. **Users hate forms**
   - Conversational onboarding is 10x better than traditional forms
   - People naturally describe their style in conversation
   - Wardrobe photo upload needs clear instructions (3-5 items per photo works best)

2. **Context is everything in fashion**
   - Weather, occasion, personal style all matter equally
   - Generic fashion advice is worse than no advice
   - Seeing actual wardrobe items builds trust instantly

3. **Similarity scores matter**
   - Users want to know why the AI chose each item
   - 20% similarity feels low but is actually good for high-dimensional space
   - Visual display + percentage + reasoning = confidence

4. **Sustainability resonates**
   - "Use what you own" is a powerful message
   - People are frustrated by underutilized wardrobes
   - Rediscovering forgotten items creates delight

### Personal Growth

- Built first production multi-agent system (previously only single-agent chatbots)
- Learned computer vision concepts (embeddings, similarity search, CLIP architecture)
- Gained experience with vector databases (ChromaDB, HNSW indexing)
- Improved prompt engineering for autonomous tool calling
- Learned to balance innovation with practical constraints (cost, latency, complexity)

---

## What's next for StylistAI

Our roadmap focuses on four key areas:

**1. Enhanced Intelligence**
- **GPT-4 Vision integration** for real-time outfit feedback ("Does this match?")
- **Automatic clothing categorization** (fabric types, occasions, styles)
- **Fashion trend prediction** using runway data and seasonal analysis

**2. Social & Gamification**
- **Community features**: Share outfits, get feedback, style challenges
- **Influencer partnerships**: Apply celebrity styling to your own wardrobe
- **Achievement system**: Badges for minimalist, trendsetter, sustainable styling

**3. Shopping Integration (Next Major Step)**
- **Smart vendor recommendations**: When you don't have a trendy piece, AI suggests where to buy it from trusted fashion retailers
- **Wardrobe gap analysis**: AI identifies missing items to complete outfits and recommends specific products
- **Multi-retailer price comparison**: Compare prices across 50+ fashion sites to find the best deals
- **Personalized shopping feed**: Get product recommendations that match your style and existing wardrobe
- **Virtual try-on** using generative AI (Stable Diffusion)
- **Affiliate revenue model**: Partner with retailers for 10% commission on sales

**4. Hybrid AI + Human Model**
- **Professional stylist consultations**: AI preps human stylists with your wardrobe analysis
- **Seasonal wardrobe audits**: What to keep/donate/buy recommendations
- **Special occasion planning**: Weddings, interviews, date nights

**Technical Evolution**
- **Advanced observability with Datadog**: Currently using Datadog LLM Observability for token tracking and cost monitoring. Future: Real-time latency detection with automatic fallback to faster models (GPT-4 Turbo → GPT-3.5 Turbo) when response times exceed thresholds, ensuring users stay engaged with sub-2-second responses
- **Intelligent model routing**: Dynamic model selection based on query complexity and latency requirements
- Mobile app (iOS/Android) with native camera integration
- White-label API marketplace for e-commerce platforms ($10K-100K/month)
- Fine-tuned fashion-specific CLIP model (95%+ accuracy)
- Real-time personalization with collaborative filtering

**Business Growth**
- Freemium model with Pro ($9.99/month) and Premium ($19.99/month) tiers
- B2B partnerships with fashion retailers to reduce returns
- Geographic expansion to UK, Canada, Australia

**Vision**: We're building the operating system for your wardrobe - the AI layer between you and your clothes that helps you look amazing every day while promoting sustainability.

---

**We're not just building a fashion app - we're building the operating system for your wardrobe. The AI layer between you, your closet, and the runway.**

**StylistAI: Wear what you own. Stay current with what's trending. Look amazing every day.**
