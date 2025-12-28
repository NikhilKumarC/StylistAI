# 🤖 Autonomous Agents Architecture - StylistAI

## Overview

We've implemented a **3-agent autonomous architecture** where each agent uses LLM-powered tool calling to make intelligent decisions.

---

## 🏗️ Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    NEW USER JOURNEY                           │
└──────────────────────────────────────────────────────────────┘

        USER SIGNS UP
             ↓
┌────────────────────────────────────────────────────────────┐
│  🎯 AGENT 1: Autonomous Onboarding                         │
│  File: onboarding_agent_autonomous.py                      │
│                                                             │
│  Purpose: Build user profile through natural conversation  │
│                                                             │
│  Tools:                                                     │
│    • update_user_profile_field(field, value, user_id)     │
│    • check_onboarding_completion(user_id)                  │
│                                                             │
│  Collects (with NULL support):                             │
│    - style_aesthetics (required)                           │
│    - colors (required)                                     │
│    - occasions (required)                                  │
│    - fit_preferences (required)                            │
│    - budget (required)                                     │
│    - body_type (required)                                  │
│    - default_location (required)                           │
│    - age_range (optional)                                  │
│    - lifestyle (optional)                                  │
│    - style_goals (optional)                                │
│                                                             │
│  Features:                                                  │
│    ✅ Natural conversation (not a form)                    │
│    ✅ Handles questions back                               │
│    ✅ Handles irrelevant answers                           │
│    ✅ Stores NULL for refused fields                       │
│    ✅ Extracts multiple fields at once                     │
│    ✅ Knows when complete                                  │
│                                                             │
│  Stores → User Profile Database                            │
└────────────────────────────────────────────────────────────┘
             ↓
    PROFILE SAVED (with NULLs where declined)
             ↓
┌────────────────────────────────────────────────────────────┐
│  💬 AGENT 2: Autonomous Conversational Stylist             │
│  File: conversational_stylist_autonomous.py                │
│                                                             │
│  Purpose: Chat naturally & gather event-specific context   │
│                                                             │
│  Tools:                                                     │
│    • get_weather_info(location, date)                      │
│    • search_user_wardrobe(query, user_id)                  │
│    • generate_outfit_recommendations(query, user_id, ...)  │
│                                                             │
│  Gathers per conversation:                                 │
│    - Occasion (date, meeting, wedding)                     │
│    - When (today, tomorrow, next week)                     │
│    - Where (location for weather)                          │
│    - Formality (casual, business casual, formal)           │
│    - Activity level (sitting, walking, dancing)            │
│    - Time of day (morning, evening)                        │
│    - Special requirements                                  │
│                                                             │
│  Loads: User profile from database                         │
│                                                             │
│  Intelligence:                                              │
│    ✅ Decides when to fetch weather                        │
│    ✅ Decides when to search wardrobe                      │
│    ✅ Decides when context is complete                     │
│    ✅ Calls recommendations tool when ready                │
│                                                             │
│  Calls Agent 3 when ready ↓                                │
└────────────────────────────────────────────────────────────┘
             ↓
    CONTEXT GATHERED + WEATHER FETCHED
             ↓
┌────────────────────────────────────────────────────────────┐
│  🎨 AGENT 3: Autonomous Styling Recommendations            │
│  File: langgraph_agent.py                                  │
│                                                             │
│  Purpose: Generate outfit recommendations                   │
│                                                             │
│  Tools (decides which to use):                             │
│    • get_user_preferences(user_id)                         │
│    • search_outfit_history(user_id, query)                 │
│    • search_fashion_trends(query)                          │
│                                                             │
│  Receives:                                                  │
│    - Event context (from Agent 2)                          │
│    - Weather data (from Agent 2)                           │
│    - User profile (fetches via tool)                       │
│                                                             │
│  Intelligence:                                              │
│    ✅ Decides if user preferences needed                   │
│    ✅ Decides if wardrobe search needed                    │
│    ✅ Decides if trend search needed                       │
│    ✅ Climate-aware recommendations                        │
│                                                             │
│  Output: Structured recommendations with reasoning         │
└────────────────────────────────────────────────────────────┘
```

---

## 📊 Agent Comparison: Old vs New

### Agent 1: Onboarding

| Feature | Old (Static) | New (Autonomous) |
|---------|-------------|------------------|
| Structure | Hardcoded steps 1→2→3... | Adaptive conversation |
| User refuses | Stores "I don't want to" | Stores NULL ✅ |
| User asks back | Stores question as data | Answers, continues ✅ |
| Irrelevant answer | Stores garbage | Redirects politely ✅ |
| Multi-field answer | Only first extracted | All extracted ✅ |
| Feel | Form/questionnaire | Natural chat ✅ |
| Turns | Always 11 questions | 5-7 conversational |
| Intelligence | None | LLM-powered ✅ |

### Agent 2: Conversational Stylist

| Feature | Old (Hardcoded) | New (Autonomous) |
|---------|----------------|------------------|
| Weather fetching | Regex + always tries | LLM decides when ✅ |
| Location extraction | Brittle regex | Natural language ✅ |
| Wardrobe search | Keyword matching | LLM decides when ✅ |
| Recommendations trigger | "recommend" keyword | Context completeness ✅ |
| Tool usage | No tools | 3 intelligent tools ✅ |
| Decisions | Regex/keywords | LLM reasoning ✅ |

### Agent 3: LangGraph Recommendations

| Feature | Old (Hardcoded) | New (Autonomous) |
|---------|----------------|------------------|
| Tool calling | ALL 3 tools ALWAYS | 0-3 as needed ✅ |
| Efficiency | High cost, slow | Optimized ✅ |
| Intelligence | Fixed state machine | Adaptive agent ✅ |
| Decisions | Hardcoded nodes | LLM reasoning ✅ |

---

## 🎯 Example: Complete User Journey

### Step 1: Onboarding (Agent 1)

```
Agent: "Hey! Welcome to StylistAI! 👋 I'm Alex, your personal AI stylist.
        Tell me about your fashion vibe!"

User: "I like streetwear but also business casual for work"

Agent: [LLM extracts: style_aesthetics = ["streetwear", "business casual"]]
       [Calls: update_user_profile_field("style_aesthetics", [...], user_id)]

       "Love that mix! Versatile. Where are you based? Helps me factor in weather."

User: "LA"

Agent: [Calls: update_user_profile_field("default_location", "Los Angeles", user_id)]

       "LA - perfect weather for both styles! What colors are you drawn to?"

User: "Mostly black, grey, olive green"

Agent: [Calls: update_user_profile_field("colors", ["black", "grey", "olive"], user_id)]

       "Classic streetwear palette! What's your budget usually like?"

User: "Mid-range mostly"

Agent: [Calls: update_user_profile_field("budget", "mid-range", user_id)]

       "Smart choice! What fit do you prefer - oversized, fitted, or in between?"

User: "Oversized for streetwear, fitted for work"

Agent: [Calls: update_user_profile_field("fit_preferences", "oversized/fitted", user_id)]

       "Perfect! And what's your build like?"

User: "Tall and slim"

Agent: [Calls: update_user_profile_field("body_type", "tall, slim", user_id)]

       "Oversized looks great on tall builds! Last thing: what do you usually dress for?"

User: "Work and casual hangouts"

Agent: [Calls: update_user_profile_field("occasions", ["work", "casual"], user_id)]
       [Calls: check_onboarding_completion(user_id)]

       "Perfect! You're all set! 🎉

        Your profile:
        - Style: Streetwear + Business Casual
        - Colors: Black, grey, olive
        - Based in: Los Angeles
        - Budget: Mid-range
        - Fit: Oversized/Fitted
        - Build: Tall, slim

        Ready to find some fire outfits?"

SAVED TO DATABASE ✅
```

### Step 2: Styling Session (Agent 2 → Agent 3)

**Week Later...**

```
User: "What should I wear tomorrow?"

Agent 2: [Loads user profile from database]

         "Hey! What's the occasion tomorrow? 😊"

User: "Business meeting downtown"

Agent 2: "Got it - business meeting! How formal?"

User: "Business casual"

Agent 2: [Has: occasion=meeting, formality=business casual]
         [Needs: weather]
         [Calls: get_weather_info("Los Angeles", "tomorrow")]

         [Weather result: 78°F, sunny]

         "Perfect! LA will be 78°F and sunny tomorrow - nice weather for business casual!
          Let me find you some great outfits..."

         [Has complete context now]
         [Calls: generate_outfit_recommendations(
             query="Business casual outfit for business meeting tomorrow in Los Angeles, 78°F sunny",
             user_id=user_id,
             weather_context={temp: 78, conditions: "sunny"}
         )]

         ↓ CALLS AGENT 3 ↓

Agent 3: [Receives enriched query]
         [LLM decides: "I need user preferences and wardrobe"]
         [Calls: get_user_preferences(user_id)]
         → Returns: {style: ["streetwear", "business casual"], colors: ["black", "grey", "olive"], ...}

         [Calls: search_outfit_history(user_id, "business casual meeting")]
         → Returns: [{item: "grey blazer"}, {item: "black pants"}, ...]

         [SKIPS: search_fashion_trends - not needed for business casual]

         [Generates recommendations with climate awareness]
         → 78°F = warm but not hot = light blazer, breathable fabrics

         Returns: {
            recommendations: [
              {
                item: "Grey blazer with black chinos",
                reasoning: "Professional yet comfortable for 78°F LA weather.
                           Matches your business casual + minimalist style.",
                styling_tip: "Breathable cotton blend works in warm weather",
                climate_note: "78°F is perfect blazer weather - not too hot",
                confidence: 0.93
              }
            ]
         }

Agent 2: [Receives recommendations from Agent 3]

         "Here's a perfect outfit for your meeting tomorrow! 💼

          🎯 Grey blazer with black chinos

          Why: Professional business casual that matches your style perfectly.
          The grey and black combo is classic and works great in 78°F weather!

          💡 Tip: Go with a breathable cotton blend since it'll be warm.

          ☀️ Weather note: 78°F is ideal blazer weather - you'll be comfortable
          without a coat!"

User: "Perfect, thanks!"
```

---

## 🔧 Technical Implementation

### File Structure

```
app/services/
├── onboarding_agent_autonomous.py      # Agent 1
├── conversational_stylist_autonomous.py # Agent 2
├── langgraph_agent.py                   # Agent 3 (refactored)
├── onboarding_agent.py                  # OLD - keep for reference
└── conversational_stylist.py            # OLD - keep for reference
```

### Database Schema (Supports NULL)

```python
user_profile = {
    "user_id": "user_123",
    "onboarding_completed": True,

    # Required (collected by Agent 1)
    "style_aesthetics": ["streetwear", "business casual"],  # ✅
    "colors": ["black", "grey", "olive"],                    # ✅
    "occasions": ["work", "casual"],                         # ✅
    "fit_preferences": "oversized/fitted",                   # ✅
    "budget": "mid-range",                                   # ✅
    "body_type": "tall, slim",                               # ✅
    "default_location": "Los Angeles",                       # ✅

    # Optional (may be NULL)
    "age_range": None,              # ❌ User declined
    "lifestyle": ["professional"],  # ✅ Provided
    "style_goals": None             # ❌ Skipped
}
```

---

## 🎯 Key Benefits

### 1. **Intelligent Tool Usage**
- Agents decide WHEN to use tools (not hardcoded)
- Only fetch data when needed
- Lower costs, faster responses

### 2. **Natural Conversations**
- Feels like chatting with a friend
- Not rigid forms or questionnaires
- Adaptive to user's style of communication

### 3. **Robust Edge Case Handling**
- User refuses to answer → Stores NULL
- User asks questions back → Answers them
- Irrelevant answers → Redirects politely
- Multi-field answers → Extracts all

### 4. **Climate-Aware Recommendations**
- Agent 2 fetches weather autonomously
- Agent 3 receives weather context
- Recommendations adapted to temperature

### 5. **Efficient & Cost-Effective**
- Only calls tools when needed
- No wasted API calls
- Optimized token usage

---

## 🚀 API Endpoints

### Autonomous Onboarding
```
POST /api/onboarding/autonomous
```
- Single endpoint for entire onboarding conversation
- Natural conversational flow (not form-based)
- Handles edge cases (questions back, refusals, vague answers)
- Stores NULL for declined fields
- Returns completion status and preferences

**Usage:**
```json
// First call (start onboarding)
POST /api/onboarding/autonomous
Body: null or {"message": null}

// Subsequent calls
POST /api/onboarding/autonomous
Body: {"message": "I like minimalist style"}

// Response
{
  "response": "Love that clean aesthetic! What colors do you gravitate toward?",
  "is_complete": false,
  "collected_so_far": {...}
}
```

### Autonomous Styling Conversation
```
POST /api/styling/query-autonomous
```
- Sequential multi-agent architecture
- Agent 2 (Conversational) gathers context
- Agent 3 (LangGraph) generates recommendations
- API orchestrates agents explicitly
- Climate-aware recommendations

**Usage:**
```json
POST /api/styling/query-autonomous
Body: {"query": "What should I wear for a date tomorrow?"}

// Response
{
  "response": "Exciting! When is it and where?",
  "recommendations": [],
  "is_conversational": true,
  "context_complete": false,
  "weather_info": null,
  "tools_used": [],
  "agent_architecture": "autonomous_sequential"
}

// After gathering context
{
  "response": "Here are perfect outfits for your date!",
  "recommendations": [
    {
      "title": "Navy blazer with chinos",
      "description": "Professional yet relaxed...",
      "styling_tip": "...",
      "climate_note": "78°F is perfect blazer weather",
      "confidence_score": 0.93
    }
  ],
  "is_conversational": false,
  "context_complete": true,
  "weather_info": {...},
  "tools_used": ["get_weather_info", "generate_outfit_recommendations"],
  "orchestration_method": "explicit_sequential"
}
```

---

## 🚀 Next Steps

1. ✅ Update API endpoints to use new autonomous agents
2. Test complete flow end-to-end
3. Monitor tool usage and costs
4. Gather user feedback
5. Fine-tune system prompts based on real conversations

---

## 📝 Notes

- Old agents kept in codebase for reference
- Gradual migration: Can run both old/new in parallel
- All new agents support async/await for better performance
- Comprehensive logging for debugging and monitoring

---

**Architecture Status:** ✅ Complete
**Implementation:** ✅ Done
**API Endpoints:** ✅ Done
**Sequential Pattern:** ✅ Implemented
**Testing:** ⏳ Pending
**Deployment:** ⏳ Pending
