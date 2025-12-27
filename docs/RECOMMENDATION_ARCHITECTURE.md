# StylistAI Recommendation Architecture

## Overview

The recommendation system combines **user-specific data** with **GPT-4's built-in fashion knowledge** to provide personalized styling advice.

## Key Insight: GPT-4 Already Knows Fashion

GPT-4 was trained on extensive fashion data and already knows:
- ✅ Color theory (complementary colors, monochromatic styling, etc.)
- ✅ Styling principles (proportions, layering, fit guidelines)
- ✅ Outfit formulas for different occasions
- ✅ Body type guidance
- ✅ Major fashion trends (up to its knowledge cutoff)
- ✅ Designer brands, materials, and quality markers

**We don't need to teach GPT-4 fashion - we just need to give it your specific context.**

## What Makes Recommendations Personal

The system provides **3 types of context** to GPT-4:

### 1. User's Preferences (from PostgreSQL)
```
Favorite Colors: ["navy", "grey", "white"]
Style Aesthetics: ["minimalist", "modern"]
Occasions: ["business", "casual"]
Budget: "mid-range"
Body Type: "athletic"
```

### 2. User's Wardrobe (from ChromaDB + PostgreSQL)
```
Items Found via Semantic Search:
- Navy blazer (similarity: 0.92)
- White button-down shirt (similarity: 0.87)
- Grey dress pants (similarity: 0.85)
```

### 3. GPT-4's Fashion Knowledge (built-in)
```
The model automatically applies:
- Color combinations: "Navy + beige is sophisticated"
- Styling rules: "Oversized top with tapered bottom"
- Current trends: "Wide-leg pants are trending in 2024"
- Fit principles: "Shoulders should fit perfectly"
```

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    USER ASKS QUESTION                       │
│         "What should I wear to a business meeting?"         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              STEP 1: Get User Preferences                   │
│         SELECT * FROM user_preferences WHERE uid=...        │
│                                                             │
│         Returns: favorite colors, style, budget, body type  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              STEP 2: Search User's Wardrobe                 │
│         - Generate query embedding with CLIP                │
│         - Search ChromaDB for similar outfit images         │
│         - Get outfit metadata from PostgreSQL               │
│                                                             │
│         Returns: Images matching "business meeting"         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              STEP 3: Build Context for GPT-4                │
│                                                             │
│    "You are an expert stylist. The user:                   │
│     - Loves navy, grey, minimalist style                   │
│     - Owns: navy blazer, white shirt, grey pants           │
│     - Asking: 'What should I wear to business meeting?'    │
│                                                             │
│     Use your fashion expertise (color theory, styling      │
│     principles, trends) to give personalized advice."      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              STEP 4: GPT-4 Generates Response               │
│                                                             │
│    GPT-4 combines:                                         │
│    ✓ User's preferences (navy, minimalist)                 │
│    ✓ User's wardrobe (navy blazer, white shirt)            │
│    ✓ Its fashion knowledge (navy+beige combo, fit rules)   │
│    ✓ Current trends (oversized blazers trending)           │
│                                                             │
│    Returns structured JSON recommendations                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 FINAL RECOMMENDATION                        │
│                                                             │
│  "Pair your navy blazer with beige chinos and white shirt. │
│   Navy + beige is a sophisticated combination that aligns  │
│   with your minimalist aesthetic. The fitted blazer works  │
│   well for your athletic build. This is a timeless look    │
│   that's trending with the 'quiet luxury' movement."       │
└─────────────────────────────────────────────────────────────┘
```

## Storage Architecture

### PostgreSQL (Structured Data)
- **users**: User info, onboarding status
- **user_preferences**: Colors, style, budget, body type, occasions
- **outfits**: Image URLs, tags, descriptions, AI metadata

**Why**: Fast queries, filtering, pagination for frontend

### ChromaDB (Vector Embeddings)
- **Embeddings**: 512-D CLIP vectors for semantic search
- **Metadata**: image_id, user_id (minimal)

**Why**: Semantic similarity search (find similar outfits by visual/text meaning)

### Google Cloud Storage (Image Files)
- **Actual image files** (JPG, PNG)
- **URLs stored in PostgreSQL** for retrieval

**Why**: Scalable blob storage

## Recommendation Flow Code

### File: `app/services/langgraph_agent.py`

**Key Functions**:

1. **`get_user_preferences(user_id)`** (line 31-57)
   - Fetches user's colors, style, budget from PostgreSQL

2. **`search_outfit_history(user_id, query)`** (line 61-88)
   - Uses CLIP to search similar outfits in ChromaDB
   - Returns matching wardrobe items

3. **`search_fashion_trends(query)`** (line 92-111)
   - OPTIONAL: Can add web search for latest trends
   - Currently returns empty (uses GPT-4's built-in knowledge)

4. **`generate_recommendations(state)`** (line 163-257)
   - **Main function** that combines all context
   - Sends enhanced prompt to GPT-4
   - Parses JSON response
   - Returns personalized recommendations

## Example Prompt to GPT-4

```
You are an expert personal stylist with deep knowledge of fashion,
color theory, styling principles, and current trends.

USER'S STYLING REQUEST: What should I wear to a business meeting?

USER'S PROFILE:
- Favorite Colors: navy, grey, white
- Style Aesthetics: minimalist, modern
- Typical Occasions: business, casual
- Budget Range: mid-range
- Body Type: athletic

USER'S WARDROBE (items they own):
- navy_blazer.jpg (similarity: 0.92)
- white_shirt.jpg (similarity: 0.87)
- grey_pants.jpg (similarity: 0.85)

YOUR TASK:
Using your expertise in fashion styling, color theory, and current trends,
provide 3-5 personalized outfit recommendations that:

1. Use their wardrobe: Incorporate items they already own
2. Match their style: Align with their favorite colors and aesthetics
3. Apply fashion principles: Use your knowledge of color combinations,
   proportions, layering, and fit
4. Consider current trends: Reference 2024/2025 fashion trends
5. Respect their budget: Suggest options within their budget range
6. Fit their occasions: Ensure recommendations work for their lifestyle

IMPORTANT: Mix their existing wardrobe items with styling suggestions.

Provide response as JSON:
{
  "recommendations": [
    {
      "item": "Navy blazer + white shirt + beige chinos",
      "reasoning": "Uses your blazer and shirt. Navy+beige is sophisticated",
      "styling_tip": "Navy and beige is a classic color combination",
      "trend_note": "Quiet luxury aesthetic is trending",
      "confidence": 0.95
    }
  ]
}
```

## GPT-4 Response Example

```json
{
  "recommendations": [
    {
      "item": "Navy blazer + white dress shirt + beige chinos + brown leather loafers",
      "reasoning": "This uses your navy blazer and white shirt while adding beige for warmth. Navy and beige create a sophisticated color palette perfect for business settings. Matches your minimalist aesthetic.",
      "styling_tip": "Navy + beige is a timeless sophisticated combination. The neutral palette creates visual harmony while remaining professional.",
      "trend_note": "This aligns with the 'quiet luxury' trend - quality pieces in neutral colors without logos. Relaxed tailoring is also trending for 2024.",
      "confidence": 0.95
    },
    {
      "item": "Grey dress pants + white shirt + navy cardigan",
      "reasoning": "Softer alternative using your existing grey pants and white shirt. The cardigan adds approachability while maintaining professionalism for business casual meetings.",
      "styling_tip": "Monochromatic grey with navy creates depth. Cardigan instead of blazer follows the 'elevated loungewear' trend while staying polished.",
      "trend_note": "Knitwear in business settings is increasingly acceptable and trending as comfort becomes priority.",
      "confidence": 0.88
    },
    {
      "item": "Your navy blazer + light blue button-down + dark denim (if you have) + white sneakers",
      "reasoning": "For a more casual business meeting or creative environment. Uses your blazer but with a relaxed bottom and modern footwear.",
      "styling_tip": "Mixing formal (blazer) with casual (denim, sneakers) creates balance. Light blue adds color while staying in your preferred palette.",
      "trend_note": "Smart casual with clean sneakers is widely accepted in modern business. Athletic body types look great in this balanced fit.",
      "confidence": 0.82
    }
  ]
}
```

## Why This Approach Works

### 1. Personalized
- Uses YOUR wardrobe items
- Matches YOUR color preferences
- Respects YOUR budget and occasions
- Considers YOUR body type

### 2. Knowledgeable
- GPT-4 applies color theory (navy+beige sophistication)
- GPT-4 applies styling rules (proportions, layering)
- GPT-4 references trends (quiet luxury, elevated loungewear)
- GPT-4 explains WHY (reasoning + styling tips)

### 3. Actionable
- Specific items to wear
- Combinations from existing wardrobe
- Confidence scores
- Styling tips for execution

### 4. Scalable
- No manual knowledge base to maintain
- GPT-4's fashion knowledge updates with model versions
- Can add web search for latest trends if needed
- Works for any user, any style, any occasion

## Optional Enhancements

### Web Search for Latest Trends
```python
# In search_fashion_trends()
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

search = DuckDuckGoSearchAPIWrapper()
results = search.results(f"{query} fashion trends 2025", max_results=3)
```

Only needed if you want **real-time trend data** beyond GPT-4's knowledge cutoff.

### Conversational Refinement
Add follow-up questions:
```
User: "What should I wear?"
Agent: "What's the occasion - business meeting, casual outing, or date night?"
User: "Business meeting"
Agent: [Provides tailored recommendations]
```

### Image Generation
Generate outfit visualization using DALL-E or Stable Diffusion based on recommendations.

## Testing the System

### Test Endpoint
```bash
POST /api/recommendations
{
  "user_id": "user_123",
  "query": "What should I wear to a business meeting?"
}
```

### Expected Response
```json
{
  "recommendations": [
    {
      "item": "Navy blazer + beige chinos + white shirt",
      "reasoning": "Uses your wardrobe, matches minimalist style",
      "styling_tip": "Navy + beige is sophisticated",
      "trend_note": "Quiet luxury trending",
      "confidence": 0.95
    }
  ],
  "context_used": {
    "preferences": true,
    "wardrobe": true,
    "gpt4_knowledge": true
  }
}
```

## Summary

**Simple Architecture**:
1. Get user preferences from database
2. Search user's wardrobe with CLIP
3. Give GPT-4 the context
4. GPT-4 applies its fashion knowledge automatically
5. Return personalized recommendations

**No need for**:
- ❌ Static fashion knowledge base
- ❌ Manual trend curation
- ❌ Color theory database

**GPT-4 already knows fashion - we just give it YOUR context.**
