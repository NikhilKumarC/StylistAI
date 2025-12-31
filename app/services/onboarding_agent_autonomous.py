"""
Autonomous Onboarding Agent for StylistAI
Natural conversational onboarding that adapts to user responses
"""

from typing import TypedDict, List, Optional, Annotated
from operator import add
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)

# Import Datadog LLM Observability decorators
try:
    from ddtrace.llmobs.decorators import agent as llm_agent
    DATADOG_AVAILABLE = True
except ImportError:
    DATADOG_AVAILABLE = False
    # Create no-op decorator if ddtrace not available
    def llm_agent(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


# Define the onboarding state
class OnboardingState(TypedDict):
    """State for autonomous onboarding conversation"""
    messages: Annotated[List[BaseMessage], add]
    user_id: str
    collected_data: dict


# Define tool for updating user profile
@tool
def update_user_profile_field(field_name: str, value: any, user_id: str) -> dict:
    """
    Update a specific field in the user's profile during onboarding.

    Call this tool when you've successfully extracted valid information from the user.

    REQUIRED FIELDS (must collect these):
    - style_aesthetics: List of style preferences (e.g., ["minimalist", "modern"])
    - colors: List of favorite colors (e.g., ["navy", "grey", "black"])
    - occasions: List of occasions they dress for (e.g., ["work", "casual", "dates"])
    - fit_preferences: Preferred fit (e.g., "fitted", "relaxed", "oversized")
    - budget: Budget range (e.g., "budget-friendly", "mid-range", "premium")
    - body_type: Body type (e.g., "athletic", "slim", "tall", "petite")
    - default_location: City or region (e.g., "Seattle", "New York")

    OPTIONAL FIELDS (nice to have):
    - age_range: Age bracket (e.g., "25-34", "35-44")
    - lifestyle: Lifestyle descriptors (e.g., ["professional", "active"])
    - style_goals: Style goals (e.g., ["look professional", "stay comfortable"])

    VALIDATION:
    - Only call this with VALID data (not "idk", "nothing", "skip", etc.)
    - If user refuses to answer, DON'T call this tool (we'll store None)
    - If answer is irrelevant or unclear, DON'T call this tool

    Args:
        field_name: Name of the profile field
        value: The extracted value (string or list)
        user_id: User's ID

    Returns:
        Updated profile status showing what's been collected and what's still needed
    """
    # In-memory storage during onboarding session
    # In real implementation, this would update a session state
    logger.info(f"[Onboarding Tool] Updating {field_name} = {value} for user {user_id}")

    return {
        "status": "updated",
        "field": field_name,
        "value": value,
        "message": f"Saved {field_name}!"
    }


@tool
def check_onboarding_completion(user_id: str) -> dict:
    """
    Check if onboarding has collected all required information.

    Call this when you think you've gathered enough information to complete onboarding.

    Returns:
        Status of onboarding completion and what fields are still missing
    """
    # This would check actual collected data in real implementation
    logger.info(f"[Onboarding Tool] Checking completion status for user {user_id}")

    return {
        "is_complete": True,  # Placeholder - would check actual collected fields
        "missing_required": [],
        "missing_optional": ["age_range", "lifestyle"],
        "message": "All required fields collected! Ready to complete onboarding."
    }


# Create LLM with tools bound
def create_onboarding_llm():
    """Create LLM with onboarding tools bound"""
    llm = ChatOpenAI(
        model=settings.OPENAI_LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.8  # Higher temperature for natural, warm conversation
    )

    tools = [update_user_profile_field, check_onboarding_completion]
    return llm.bind_tools(tools)


# Agent node - autonomous conversation
async def onboarding_agent_node(state: OnboardingState) -> OnboardingState:
    """
    Autonomous onboarding agent that naturally collects user profile data
    """
    logger.info(f"[Onboarding Agent] Processing for user: {state['user_id']}")

    # Build system message with comprehensive instructions
    system_message = SystemMessage(content="""You are Alex, a friendly and enthusiastic personal stylist helping a new user set up their profile on StylistAI.

YOUR GOAL: Collect user profile information through natural, warm conversation (NOT a rigid questionnaire!)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 REQUIRED INFORMATION TO COLLECT:

1. **style_aesthetics** - Their style vibe (minimalist, bohemian, streetwear, classic, modern, etc.)
2. **colors** - Favorite colors to wear (3-5 colors)
3. **occasions** - What they typically dress for (work, casual, dates, gym, formal events, etc.)
4. **fit_preferences** - Preferred fit (fitted, relaxed, oversized, slim, tailored)
5. **budget** - Budget range (budget-friendly, mid-range, premium, luxury)
6. **body_type** - Body type (athletic, slim, curvy, tall, petite, average, etc.)
7. **default_location** - Where they're based (city or region for weather recommendations)

📋 OPTIONAL INFORMATION (nice to have):

8. **age_range** - Age bracket (18-24, 25-34, 35-44, 45-54, 55+)
9. **lifestyle** - Lifestyle descriptors (professional, student, parent, entrepreneur, creative, active)
10. **style_goals** - What they want to achieve (look professional, express creativity, stay comfortable, follow trends)

📸 WARDROBE PHOTOS (REQUIRED - MUST ASK BEFORE COMPLETION):

11. **photos_requested** - MANDATORY: You MUST ask about photos before calling check_onboarding_completion!
    - Ask this AFTER collecting the 7 required fields above
    - Explain benefits: "One last thing! Want to upload some photos of your current wardrobe? This helps me understand what you already own and suggest better outfit combinations! 📸"
    - If YES:
      * Call update_user_profile_field("photos_requested", True, user_id)
      * Tell them: "Perfect! After we finish here, you'll see an upload button where you can add 3-5 photos of your favorite outfits or wardrobe items."
    - If NO:
      * Call update_user_profile_field("photos_requested", False, user_id)
      * Tell them: "No problem! You can always add photos later from your profile."
    - ⚠️ CRITICAL: Always call the tool to store the user's photo preference (true or false)
    - ⚠️ DO NOT call check_onboarding_completion until you've asked about photos!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 YOUR APPROACH (VERY IMPORTANT):

✅ **BE CONVERSATIONAL:**
- Have a natural dialogue, NOT an interrogation
- Ask 1-2 related questions at a time
- Follow up on interesting answers
- Show enthusiasm and personality
- Use emojis occasionally (not excessively)

✅ **BE EFFICIENT:**
- Extract multiple pieces of info from one answer when possible
- If they volunteer extra info, use it!
- Group related questions naturally

✅ **BE FLEXIBLE:**
- Adapt question order based on their responses
- Skip optional fields if conversation flows without them
- Don't force questions if they're naturally covered

✅ **BE RESPECTFUL:**
- If they refuse to answer, accept it gracefully
- Store None/null for refused fields (don't push)
- If they ask why, explain transparently

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛠️ USING TOOLS:

**update_user_profile_field(field_name, value, user_id)**
- Call this when you've extracted VALID information
- Only call with actual data (not "idk", "nothing", "skip", "I don't know")
- If user refuses or gives irrelevant answer, DON'T call tool
- Can call multiple times in one turn if user gave multiple pieces of info

**check_onboarding_completion(user_id)**
- ⚠️ ONLY call this AFTER you've asked about photos and stored photos_requested
- Call this when you've collected all 7 REQUIRED fields AND asked about photos
- This checks if we're done
- If complete, wrap up warmly and welcome them to the platform

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎭 HANDLING DIFFERENT USER BEHAVIORS:

**1. User Asks Questions Back:**
Example: "Why do you need my location?"
→ Answer their question first, then gently redirect
→ "Great question! I ask for your city so I can give weather-appropriate recommendations. Like, I won't suggest heavy coats in Miami summer! Your location stays private. So, what city are you in?"

**2. Irrelevant/Off-Topic Answers:**
Example: "I love pizza" (when asked about budget)
→ Acknowledge with humor, redirect kindly
→ "Haha, pizza is great! 🍕 But let me ask about fashion - when shopping for clothes, do you usually look for deals, go mid-range, or splurge?"

**3. Vague Answers:**
Example: "idk", "normal", "whatever"
→ Provide specific options/examples
→ "No worries! Let me give you some options: Are you more A) Clean & simple, B) Edgy & trendy, C) Classic & polished, or D) Casual & relaxed?"

**4. User Refuses to Answer:**
Example: "I'd rather not say"
→ Accept gracefully, DON'T call update_user_profile_field
→ "No problem at all! That one's optional anyway. Let me ask about..."

**5. Privacy Concerns:**
Example: "Are you tracking me?"
→ Address concerns honestly and warmly
→ "I totally understand the concern! I only ask for your city/region (like 'Seattle') for weather recommendations, nothing more specific. It stays private. You can skip if you'd like!"

**6. Answers Multiple Things at Once:**
Example: "I like minimalist style, mostly wear black and grey, based in NYC"
→ Extract all pieces! Call update_user_profile_field multiple times
→ "Awesome! You just gave me a ton of great info - minimalist in NYC with black & grey. Love it! 🖤"

**7. Completely Ignores Question:**
→ Try once more with different phrasing
→ If still ignored, move on (store None for that field)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 CONVERSATION EXAMPLES:

❌ **BAD (Rigid Questionnaire):**
You: "What style aesthetics do you prefer?"
User: "Minimalist"
You: "What are your favorite colors?"

✅ **GOOD (Natural Conversation):**
You: "What's your vibe when it comes to fashion? 😊"
User: "I like clean, simple looks"
You: [Calls update_user_profile_field("style_aesthetics", ["minimalist", "clean"])]
You: "Ah, minimalist! Love it. Do you stick to neutrals or mix in some color?"
[Gets both style AND color info naturally]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎬 OPENING MESSAGE (Use this style):

"Hey! Welcome to StylistAI! 👋 I'm Nikhil, your personal AI stylist.

I'm excited to get to know your style! This should only take a few minutes. Let's start with the fun part - tell me about your fashion vibe! Are you more classic, edgy, minimalist, bohemian, or something totally unique?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏁 FLOW SEQUENCE (FOLLOW THIS ORDER):

1. Collect the 7 required fields through natural conversation
2. ⚠️ THEN ask about wardrobe photos (photos_requested)
3. ⚠️ THEN call check_onboarding_completion
4. THEN give closing message

🏁 CLOSING MESSAGE (After check_onboarding_completion returns success):

"Perfect! I've got everything I need! 🎉

Here's your style profile:
- Style: [their style]
- Colors: [their colors]
- Occasions: [their occasions]
- Fit: [their fit]
- Budget: [their budget]
- Based in: [their location]

You're all set! Let's start finding amazing outfits for you!"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REMEMBER:
- Be warm and enthusiastic!
- Make it feel like chatting with a friendly stylist, NOT filling out a form
- Extract information efficiently but naturally
- Accept when users don't want to share something
- Call update_user_profile_field only with VALID data
- ⚠️ ALWAYS ask about photos BEFORE calling check_onboarding_completion
- Follow the flow sequence: required fields → photos question → completion check → closing
""")

    # Build messages
    messages = [system_message]
    messages.extend(state['messages'])

    # Get LLM with tools
    llm_with_tools = create_onboarding_llm()

    # Invoke LLM
    response = await llm_with_tools.ainvoke(messages)

    logger.info(f"[Onboarding Agent] LLM response type: {type(response)}")
    if hasattr(response, 'tool_calls') and response.tool_calls:
        logger.info(f"[Onboarding Agent] LLM called {len(response.tool_calls)} tools")

    return {"messages": [response]}


# Tool execution node
tools_list = [update_user_profile_field, check_onboarding_completion]
tool_node = ToolNode(tools_list)


# Router: decide if we should continue to tools or end
def should_continue(state: OnboardingState) -> str:
    """Determine if we should call tools or continue conversation"""
    messages = state['messages']
    last_message = messages[-1]

    # If LLM makes tool calls, route to tools node
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        logger.info(f"[Onboarding Router] Routing to tools")
        return "tools"

    # Otherwise, wait for user response
    logger.info(f"[Onboarding Router] Waiting for user response")
    return "end"


# Build the LangGraph workflow
def create_autonomous_onboarding_agent() -> StateGraph:
    """Create and compile the autonomous onboarding agent"""

    workflow = StateGraph(OnboardingState)

    # Add nodes
    workflow.add_node("agent", onboarding_agent_node)
    workflow.add_node("tools", tool_node)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )

    # After tools, go back to agent
    workflow.add_edge("tools", "agent")

    return workflow.compile()


# Main execution function
@llm_agent(name="onboarding_agent")
async def run_autonomous_onboarding(
    user_id: str,
    user_message: Optional[str] = None,
    conversation_history: Optional[List[dict]] = None
) -> dict:
    """
    Run the autonomous onboarding agent

    Automatically tracked by Datadog LLM Observability:
    - Token usage (prompt + completion)
    - Cost estimation
    - Agent decision flow
    - Tool calls

    Args:
        user_id: User's ID
        user_message: User's latest message (None for first interaction)
        conversation_history: Previous messages (None for first interaction)

    Returns:
        Agent's response and current status
    """

    agent = create_autonomous_onboarding_agent()

    # Build messages from history
    messages = []
    if conversation_history:
        for msg in conversation_history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg["content"]))

    # Add current user message
    if user_message:
        messages.append(HumanMessage(content=user_message))

    # Initial state
    initial_state: OnboardingState = {
        "messages": messages,
        "user_id": user_id,
        "collected_data": {}
    }

    logger.info(f"\n{'='*50}")
    logger.info(f"Autonomous Onboarding Agent - User: {user_id}")
    logger.info(f"{'='*50}\n")

    # Run agent (automatically tracked by @llm_agent decorator)
    final_state = await agent.ainvoke(initial_state)

    # Extract response
    final_messages = final_state['messages']

    # Get last AI message (skip tool messages and system messages)
    ai_response = None
    for msg in reversed(final_messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'content') and msg.content:
            # Make sure it's not a tool call message
            if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                ai_response = msg.content
                break

    # Build collected_data from tool messages
    collected_data = {}
    for msg in final_messages:
        if isinstance(msg, ToolMessage):
            try:
                result = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                # Extract field updates from update_user_profile_field tool
                if result.get('field') and result.get('value'):
                    collected_data[result['field']] = result['value']
                    logger.info(f"[Onboarding] Extracted {result['field']} = {result['value']}")
            except Exception as e:
                logger.warning(f"[Onboarding] Failed to parse tool message: {e}")
                pass

    # Check if onboarding is complete
    # Look for check_onboarding_completion tool results
    is_complete = False
    for msg in final_messages:
        if isinstance(msg, ToolMessage):
            try:
                result = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                if result.get('is_complete'):
                    is_complete = True
                    break
            except:
                pass

    logger.info(f"[Onboarding] Final collected_data: {collected_data}")

    return {
        "response": ai_response or "I'm here to help you set up your profile!",
        "is_complete": is_complete,
        "user_id": user_id,
        "collected_data": collected_data
    }


# Helper function to save onboarding data
def save_autonomous_onboarding_data(user_id: str, collected_data: dict):
    """Save collected onboarding data to user preferences"""
    from app.services.user_service import UserService

    # Build preferences dict with None for missing fields
    preferences = {
        "style_aesthetics": collected_data.get("style_aesthetics", None),
        "colors": collected_data.get("colors", None),
        "occasions": collected_data.get("occasions", None),
        "fit_preferences": collected_data.get("fit_preferences", None),
        "budget": collected_data.get("budget", None),
        "body_type": collected_data.get("body_type", None),
        "default_location": collected_data.get("default_location", None),
        "age_range": collected_data.get("age_range", None),
        "lifestyle": collected_data.get("lifestyle", None),
        "style_goals": collected_data.get("style_goals", None),
        "onboarding_completed": True
    }

    UserService.save_user_preferences(user_id, preferences)
    logger.info(f"[Autonomous Onboarding] Saved preferences for user: {user_id}")
    logger.info(f"[Autonomous Onboarding] Stored values: {preferences}")

    return preferences
