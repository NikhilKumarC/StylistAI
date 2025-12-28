# 🎨 UI Integration Guide - Pure Sequential Pattern

## Overview

The autonomous agents now use a **Pure Sequential Pattern** where:
1. **Agent 2 (Conversational)** gathers context through natural dialogue
2. **API** detects when context is complete
3. **Agent 3 (LangGraph)** generates recommendations

This makes UI integration **clean, predictable, and simple**!

---

## API Endpoints

### 1. Autonomous Onboarding
```
POST /api/onboarding/autonomous
```

### 2. Autonomous Styling Conversation
```
POST /api/styling/query-autonomous
```

---

## Complete UI Flow

### Step 1: User Onboarding (First-Time Users)

**Component: OnboardingChat.tsx**

```typescript
import React, { useState } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function OnboardingChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const [loading, setLoading] = useState(false);

  // Start onboarding on mount
  useEffect(() => {
    startOnboarding();
  }, []);

  const startOnboarding = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/onboarding/autonomous', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({}) // Empty body to start
      });

      const data = await response.json();

      // Add agent's greeting
      setMessages([
        { role: 'assistant', content: data.response }
      ]);

      setIsComplete(data.is_complete);
    } catch (error) {
      console.error('Failed to start onboarding:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');

    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await fetch('/api/onboarding/autonomous', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({ message: userMessage })
      });

      const data = await response.json();

      // Add agent response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response
      }]);

      // Check if onboarding is complete
      if (data.is_complete) {
        setIsComplete(true);
        // Redirect to styling chat after 2 seconds
        setTimeout(() => {
          router.push('/styling');
        }, 2000);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="onboarding-chat">
      <div className="messages">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        {loading && <LoadingIndicator />}
      </div>

      {!isComplete && (
        <div className="input-area">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyPress={e => e.key === 'Enter' && sendMessage()}
            placeholder="Type your answer..."
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading}>
            Send
          </button>
        </div>
      )}

      {isComplete && (
        <div className="completion-banner">
          ✅ Onboarding complete! Redirecting to styling chat...
        </div>
      )}
    </div>
  );
}
```

---

### Step 2: Styling Conversation (Main Experience)

**Component: StylingChat.tsx**

```typescript
import React, { useState } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Recommendation {
  title: string;
  description: string;
  styling_tip: string;
  climate_note?: string;
  confidence_score: number;
}

interface WeatherInfo {
  location: string;
  temperature: string;
  conditions: string;
  date: string;
}

export function StylingChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Recommendation state
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [weatherInfo, setWeatherInfo] = useState<WeatherInfo | null>(null);
  const [contextComplete, setContextComplete] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');

    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      // PURE SEQUENTIAL PATTERN - Single endpoint
      const response = await fetch('/api/styling/query-autonomous', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({ query: userMessage })
      });

      const data = await response.json();

      // Add agent response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response
      }]);

      // Update state based on response
      setContextComplete(data.context_complete);

      // Show weather info if available
      if (data.weather_info) {
        setWeatherInfo(data.weather_info);
      }

      // PREDICTABLE: Recommendations are only present when context is complete
      if (data.recommendations && data.recommendations.length > 0) {
        setRecommendations(data.recommendations);
        // Scroll to recommendations
        setTimeout(() => {
          document.getElementById('recommendations')?.scrollIntoView({
            behavior: 'smooth'
          });
        }, 100);
      }

      // Log orchestration info (for debugging)
      console.log('Agent Architecture:', data.agent_architecture); // "pure_sequential"
      console.log('Orchestration Method:', data.orchestration_method); // "explicit_api_orchestration"
      console.log('Tools Used:', data.tools_used); // e.g., ["get_weather_info"]

    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, something went wrong. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="styling-chat">
      {/* Header with weather indicator */}
      {weatherInfo && (
        <div className="weather-banner">
          🌤️ {weatherInfo.location} - {weatherInfo.temperature}, {weatherInfo.conditions}
        </div>
      )}

      {/* Chat messages */}
      <div className="messages">
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        {loading && <LoadingIndicator />}
      </div>

      {/* Recommendations section (appears when context is complete) */}
      {recommendations.length > 0 && (
        <div id="recommendations" className="recommendations-section">
          <h2>✨ Your Perfect Outfits</h2>
          <div className="recommendations-grid">
            {recommendations.map((rec, idx) => (
              <RecommendationCard key={idx} recommendation={rec} />
            ))}
          </div>

          {/* Show "Ask for more" button */}
          <button
            onClick={() => {
              setInput("Can you suggest more options?");
              sendMessage();
            }}
            className="more-recommendations-btn"
          >
            Show More Options
          </button>
        </div>
      )}

      {/* Input area */}
      <div className="input-area">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && sendMessage()}
          placeholder={
            contextComplete
              ? "Want more suggestions?"
              : "What's the occasion?"
          }
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
```

---

### Step 3: Recommendation Card Component

**Component: RecommendationCard.tsx**

```typescript
interface RecommendationCardProps {
  recommendation: {
    title: string;
    description: string;
    styling_tip: string;
    climate_note?: string;
    trend_note?: string;
    confidence_score: number;
  };
}

export function RecommendationCard({ recommendation }: RecommendationCardProps) {
  return (
    <div className="recommendation-card">
      <div className="card-header">
        <h3>{recommendation.title}</h3>
        <div className="confidence-badge">
          {Math.round(recommendation.confidence_score * 100)}% Match
        </div>
      </div>

      <div className="card-body">
        <p className="description">{recommendation.description}</p>

        {recommendation.styling_tip && (
          <div className="tip-section">
            <span className="icon">💡</span>
            <span>{recommendation.styling_tip}</span>
          </div>
        )}

        {recommendation.climate_note && (
          <div className="climate-section">
            <span className="icon">🌤️</span>
            <span>{recommendation.climate_note}</span>
          </div>
        )}

        {recommendation.trend_note && (
          <div className="trend-section">
            <span className="icon">✨</span>
            <span>{recommendation.trend_note}</span>
          </div>
        )}
      </div>

      <div className="card-actions">
        <button className="save-btn">💾 Save Outfit</button>
        <button className="share-btn">🔗 Share</button>
      </div>
    </div>
  );
}
```

---

## API Response Schemas

### Onboarding Response

```typescript
interface OnboardingResponse {
  response: string;                 // Agent's message
  is_complete: boolean;             // Onboarding finished?
  onboarding_completed: boolean;    // Same as is_complete
  preferences?: UserPreferences;    // Final preferences (when complete)
  collected_so_far?: Partial<UserPreferences>; // Progress (while gathering)
}

interface UserPreferences {
  style_aesthetics: string[];
  colors: string[];
  occasions: string[];
  fit_preferences: string;
  budget: string;
  body_type: string;
  default_location: string;
  age_range?: string | null;       // Can be null if user declined
  lifestyle?: string[] | null;      // Can be null if user declined
  style_goals?: string[] | null;    // Can be null if user declined
}
```

### Styling Response

```typescript
interface StylingResponse {
  response: string;                      // Agent's conversational message
  recommendations: Recommendation[];     // Empty until context complete
  is_conversational: boolean;            // true = still gathering context
  context_complete: boolean;             // true = ready for/has recommendations
  weather_info: WeatherInfo | null;      // Weather data (if fetched)
  tools_used: string[];                  // ["get_weather_info"] etc.
  agent_architecture: "pure_sequential"; // Always this value
  orchestration_method: "explicit_api_orchestration"; // Always this
  pattern: string;                       // Describes the flow
}

interface Recommendation {
  title: string;
  description: string;
  styling_tip: string;
  trend_note?: string;
  climate_note?: string;              // NEW: Weather-specific guidance
  confidence_score: number;           // 0.0 - 1.0
}

interface WeatherInfo {
  location: string;
  date: string;
  temperature: string;                // e.g., "65°F"
  conditions: string;                 // e.g., "partly cloudy"
  feels_like?: string;
  humidity?: string;
}
```

---

## Conversation Flow Examples

### Example 1: Quick Request with Full Context

```
User: "What should I wear for a business meeting tomorrow in Seattle?"

API Response 1:
{
  "response": "Got it! Let me check the weather for Seattle tomorrow...",
  "recommendations": [],
  "is_conversational": true,
  "context_complete": false,
  "weather_info": null,
  "tools_used": []
}

[Agent calls get_weather_info tool internally]

User: (no additional input needed, same turn continues)

API Response 2:
{
  "response": "Perfect! Tomorrow in Seattle will be 65°F and partly cloudy. Let me find you the ideal business casual outfit!",
  "recommendations": [
    {
      "title": "Navy blazer with chinos",
      "description": "Professional yet comfortable for Seattle's mild weather...",
      "styling_tip": "Layer with a light sweater you can remove indoors",
      "climate_note": "65°F is perfect for a blazer - comfortable without overheating",
      "confidence_score": 0.93
    },
    // ... more recommendations
  ],
  "is_conversational": false,
  "context_complete": true,
  "weather_info": {
    "location": "Seattle",
    "date": "tomorrow",
    "temperature": "65°F",
    "conditions": "partly cloudy"
  },
  "tools_used": ["get_weather_info"],
  "agent_architecture": "pure_sequential",
  "orchestration_method": "explicit_api_orchestration"
}
```

**UI Behavior:**
1. Show agent's initial response
2. Show loading indicator (agent fetching weather)
3. Show agent's final response + recommendations
4. Scroll to recommendations section
5. Display weather banner

---

### Example 2: Gradual Context Gathering

```
Turn 1:
User: "I need outfit help"
Response: {
  "response": "I'd love to help! What's the occasion?",
  "recommendations": [],
  "is_conversational": true,
  "context_complete": false,
  ...
}

Turn 2:
User: "A date"
Response: {
  "response": "Exciting! When is your date and where will you be?",
  "recommendations": [],
  "is_conversational": true,
  "context_complete": false,
  ...
}

Turn 3:
User: "Tomorrow evening in LA"
Response: {
  "response": "Perfect! Let me check LA's weather and find you some great options!",
  "recommendations": [/* 3-5 recommendations */],
  "is_conversational": false,
  "context_complete": true,
  "weather_info": {
    "location": "Los Angeles",
    "temperature": "78°F",
    "conditions": "sunny"
  },
  ...
}
```

**UI Behavior:**
1. Turn 1-2: Just show chat messages (gathering context)
2. Turn 3: Show final message + recommendations section appears
3. Weather banner appears in header

---

## UI State Management (React)

```typescript
interface ChatState {
  // Messages
  messages: Message[];

  // Context gathering
  isGatheringContext: boolean;     // !context_complete
  weatherInfo: WeatherInfo | null;

  // Recommendations
  recommendations: Recommendation[];
  hasRecommendations: boolean;

  // Loading
  loading: boolean;
}

// Derived state
const showRecommendations = recommendations.length > 0;
const showWeatherBanner = weatherInfo !== null;
const promptText = isGatheringContext
  ? "What's the occasion?"
  : "Want more suggestions?";
```

---

## Error Handling

```typescript
try {
  const response = await fetch('/api/styling/query-autonomous', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${userToken}`
    },
    body: JSON.stringify({ query: userMessage })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  const data = await response.json();

  // Handle response...

} catch (error) {
  console.error('Failed to get styling advice:', error);

  // Show user-friendly error
  setMessages(prev => [...prev, {
    role: 'assistant',
    content: "Sorry, I'm having trouble right now. Please try again in a moment!"
  }]);
}
```

---

## Key UI Benefits of Pure Sequential Pattern

### ✅ Predictable Flow
- Context gathering → Weather appears → Recommendations appear
- Always in that order, never out of sequence
- No surprises for UI logic

### ✅ Single Endpoint
- No need to call multiple endpoints
- One POST request per user message
- Simpler state management

### ✅ Clear State Indicators
- `is_conversational`: Show chat interface
- `context_complete`: Show "finding outfits" loader
- `recommendations.length > 0`: Show recommendation cards

### ✅ Weather Integration
- Weather banner appears when weather is fetched
- Automatically included in recommendations
- No separate weather API call needed

### ✅ Progressive Enhancement
- Chat works without recommendations (gathering context)
- Recommendations appear naturally when ready
- Smooth transition between states

---

## Testing Checklist

### Onboarding
- [ ] Start onboarding shows greeting
- [ ] User can answer questions naturally
- [ ] User can ask questions back
- [ ] User can refuse to answer (stores NULL)
- [ ] Completion redirects to styling chat
- [ ] Error handling works

### Styling Chat
- [ ] Initial message shows gathering context
- [ ] Weather banner appears after weather fetch
- [ ] Recommendations appear when context complete
- [ ] Can ask for more recommendations
- [ ] Can start new conversation
- [ ] Handles vague requests (asks follow-ups)
- [ ] Handles complete requests (immediate recommendations)
- [ ] Error handling works

### Responsive Design
- [ ] Works on mobile
- [ ] Recommendations grid adapts
- [ ] Input area stays visible
- [ ] Scroll behavior correct

---

## Performance Tips

1. **Lazy load recommendation images** (if added later)
2. **Debounce input** if implementing typing indicators
3. **Cache weather info** client-side for same location/date
4. **Virtualize message list** for long conversations
5. **Optimistic UI updates** - add user message immediately

---

## Summary

The Pure Sequential Pattern makes UI integration **simple and predictable**:

1. ✅ **Single endpoint** per user message
2. ✅ **Clear state flow** - context → weather → recommendations
3. ✅ **Predictable responses** - always same structure
4. ✅ **No race conditions** - API orchestrates everything
5. ✅ **Clean separation** - UI just displays what API returns

**You don't need to:**
- ❌ Detect when to call recommendations yourself
- ❌ Manage complex multi-agent logic
- ❌ Call multiple endpoints in sequence
- ❌ Handle tool orchestration

**API handles everything automatically!** 🎉
