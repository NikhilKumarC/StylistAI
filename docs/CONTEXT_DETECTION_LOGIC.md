# 🎯 Multi-Signal Context Detection

## Problem with Single-Signal Detection

**Original (Naive) Approach:**
```python
needs_more_context = weather_info is None  # ❌ TOO SIMPLE!
```

**Issues:**
- ❌ User asks "what's the weather in NYC?" → Weather fetched, triggers recommendations
- ❌ Agent fetches weather too early (before occasion/formality)
- ❌ No validation that styling context was actually gathered

---

## ✅ New Multi-Signal Detection

**File:** `app/services/conversational_stylist_autonomous.py:466-519`

### Three Required Signals

```python
# Signal 1: Weather Data Present
has_weather = weather_info is not None

# Signal 2: Agent Uses Readiness Phrase
readiness_phrases = [
    "let me find",
    "i'll find",
    "let me get",
    "i've got all",
    "i have all",
    "perfect! let me",
    "great! let me",
    ...
]
agent_signals_ready = any(phrase in ai_response.lower() for phrase in readiness_phrases)

# Signal 3: Minimum Conversation Depth
min_conversation_depth = len(conversation_history) >= 2

# ALL THREE must be true
needs_more_context = not (has_weather and agent_signals_ready and min_conversation_depth)
```

---

## How It Works

### Signal 1: Weather Data (Proxy for Location + When)

**Why:** Weather is only fetched when agent has:
- Location (where the event is)
- When (today, tomorrow, specific date)

**Limitations alone:** Could be weather-only query

---

### Signal 2: Readiness Phrases (Agent Intent)

**Why:** Agent explicitly signals it's ready by using specific language

**Detected phrases:**
- "Let me find..."
- "I'll find..."
- "Let me get..."
- "I've got all..."
- "Perfect! Let me..."
- "Great! Let me..."
- "Let me put together..."

**Example:**
```
✅ "Perfect! Let me find you the ideal outfit!" → Triggers
❌ "The weather looks great!" → Doesn't trigger
```

---

### Signal 3: Conversation Depth (Prevents Premature Triggers)

**Why:** Ensures meaningful conversation happened

**Logic:** `len(conversation_history) >= 2`
- At least 1 user message + 1 assistant message before current turn

**Prevents:**
```
User: "What should I wear for a date in NYC tomorrow?"
[Agent immediately fetches weather on Turn 1]
→ Signal 3 fails (depth = 0)
→ Doesn't trigger recommendations (agent needs to ask about formality, vibe, etc.)
```

---

## Example Scenarios

### ✅ Scenario 1: Normal Flow (All Signals Met)

```
Turn 1:
User: "I need outfit help"
Agent: "What's the occasion?"
→ has_weather=False, agent_ready=False, depth=2
→ needs_more_context=True (keep gathering)

Turn 2:
User: "A date tomorrow evening"
Agent: "Where will you be?"
→ has_weather=False, agent_ready=False, depth=4
→ needs_more_context=True (keep gathering)

Turn 3:
User: "In Seattle"
Agent: [Fetches weather] "Perfect! Let me find you some great date outfits!"
→ has_weather=True ✅
→ agent_ready=True ✅ ("let me find" detected)
→ depth=6 ✅
→ needs_more_context=False → GENERATE RECOMMENDATIONS!
```

---

### ✅ Scenario 2: Quick Request (All Signals Met)

```
Turn 1:
User: "What should I wear for a business meeting tomorrow in NYC?"
Agent: "How formal - business casual or business formal?"
→ has_weather=False, agent_ready=False, depth=2
→ needs_more_context=True

Turn 2:
User: "Business casual"
Agent: [Fetches weather] "Great! Let me find you the perfect business casual outfit!"
→ has_weather=True ✅
→ agent_ready=True ✅ ("let me find" detected)
→ depth=4 ✅
→ needs_more_context=False → GENERATE RECOMMENDATIONS!
```

---

### ❌ Scenario 3: Weather-Only Query (Signals NOT Met)

```
Turn 1:
User: "What's the weather like in NYC tomorrow?"
Agent: [Fetches weather] "Tomorrow in NYC will be 65°F and sunny!"
→ has_weather=True ✅
→ agent_ready=False ❌ (no readiness phrase)
→ depth=2 ✅
→ needs_more_context=True → NO RECOMMENDATIONS (correct!)
```

**Result:** Agent answers weather question without triggering recommendations. Perfect!

---

### ❌ Scenario 4: Weather Fetched Too Early (Signals NOT Met)

```
Turn 1:
User: "I have an event tomorrow in LA"
Agent: [Fetches weather] "LA will be 78°F tomorrow! What kind of event?"
→ has_weather=True ✅
→ agent_ready=False ❌ (asking question, not ready phrase)
→ depth=2 ✅
→ needs_more_context=True → NO RECOMMENDATIONS (correct!)

Turn 2:
User: "A wedding"
Agent: "Formal or semi-formal?"
→ Still gathering context...

Turn 3:
User: "Semi-formal"
Agent: "Perfect! Let me find you some stunning semi-formal outfits!"
→ has_weather=True ✅
→ agent_ready=True ✅ ("let me find" detected)
→ depth=6 ✅
→ needs_more_context=False → NOW generate recommendations!
```

**Result:** Weather fetched early doesn't trigger prematurely. Waits for agent's readiness signal.

---

## API Detection Logic

**File:** `app/api/styling.py:209`

```python
if not needs_more_context and weather_info:
    # Context is complete! Call LangGraph Agent
    agent_result = await run_styling_agent(...)
```

**Note:** API still checks `weather_info` for safety (belt-and-suspenders approach)

---

## Logging & Debugging

The function returns `context_signals` for debugging:

```python
{
  "response": "Perfect! Let me find...",
  "needs_more_context": False,
  "context_signals": {
    "has_weather": True,
    "agent_signals_ready": True,
    "min_conversation_depth": True
  }
}
```

**Logs:**
```
[Context Detection] has_weather=True, agent_ready=True, min_depth=True
[Context Detection] needs_more_context=False
```

---

## Why This Approach Works

### 1. **Robust Against Edge Cases**
- Weather-only queries don't trigger
- Premature weather fetching doesn't trigger
- Requires agent's explicit readiness

### 2. **Natural Language Based**
- Agent uses natural phrases users expect
- Not rigid keyword matching
- Flexible phrase detection

### 3. **Conversation Quality Gate**
- Ensures minimal interaction depth
- Prevents one-shot triggers on complex queries

### 4. **Easy to Debug**
- Clear signals logged
- Can see which signal failed
- `context_signals` object for inspection

### 5. **Easy to Extend**
- Add more readiness phrases
- Adjust conversation depth threshold
- Add Signal 4 if needed (e.g., keyword detection)

---

## Tuning Parameters

### Readiness Phrases (Signal 2)
```python
# Add more phrases if agent uses different language
readiness_phrases = [
    "let me find",
    # Add: "i'll get you", "here are some", etc.
]
```

### Conversation Depth (Signal 3)
```python
# Currently: >= 2 (at least 1 exchange before current)
# Can adjust: >= 4 for more depth, >= 1 for less
min_conversation_depth = len(conversation_history) >= 2
```

---

## Testing Checklist

- [ ] Normal flow with 3+ turns
- [ ] Quick request with full context in 1 message
- [ ] Weather-only query (shouldn't trigger)
- [ ] Agent fetches weather early (shouldn't trigger until ready)
- [ ] User asks "what's trending?" (shouldn't trigger)
- [ ] Agent says "sounds good" without readiness phrase (shouldn't trigger)
- [ ] Log inspection shows correct signal states

---

## Summary

**Old Logic:**
```python
needs_more_context = weather_info is None  # Single signal ❌
```

**New Logic:**
```python
needs_more_context = not (
    has_weather and              # Signal 1 ✅
    agent_signals_ready and      # Signal 2 ✅
    min_conversation_depth       # Signal 3 ✅
)
```

**Result:** Robust, reliable context detection that prevents false triggers while enabling smooth recommendations when truly ready! 🎯
