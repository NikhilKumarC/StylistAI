"""
LangGraph Agent for StylistAI
Autonomous agent that intelligently decides which tools to use for styling recommendations
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


# Define the agent state
class AgentState(TypedDict):
    """State object for the styling agent"""
    messages: Annotated[List[BaseMessage], add]
    user_id: str
    query: str
    weather_context: Optional[dict]


# Tools for the agent
@tool
def get_user_preferences(user_id: str) -> dict:
    """Fetch user's style preferences from the database"""
    try:
        from app.services.user_service import UserService

        # Get actual user preferences from database
        prefs = UserService.get_user_preferences(user_id)

        if prefs:
            return prefs
        else:
            # Return default preferences if user hasn't completed onboarding
            return {
                "occasions": ["casual", "business_casual"],
                "fit_preferences": "fitted",
                "budget": "mid-range",
                "style_aesthetics": ["minimalist", "modern"],
                "colors": ["navy", "grey", "white", "black"],
                "onboarding_completed": False
            }
    except Exception as e:
        print(f"Error fetching user preferences: {str(e)}")
        # Return defaults on error
        return {
            "occasions": ["casual"],
            "onboarding_completed": False
        }


@tool
async def search_outfit_history(user_id: str, query: str, limit: int = 5) -> List[dict]:
    """Search user's past outfits using vector similarity"""
    try:
        from app.services.image_service import ImageService

        # Use CLIP to search similar outfits
        results = await ImageService.search_similar_outfits(
            query=query,
            user_id=user_id,
            n_results=limit
        )

        # Format results for LLM consumption
        formatted_results = []
        for result in results:
            formatted_results.append({
                "image_id": result.get("image_id"),
                "filename": result.get("metadata", {}).get("filename", "Unknown"),
                "gcs_url": result.get("metadata", {}).get("gcs_url"),
                "similarity_score": result.get("similarity", 0),
                "metadata": result.get("metadata", {})
            })

        return formatted_results
    except Exception as e:
        print(f"Error searching outfits: {str(e)}")
        # Return empty list if search fails
        return []


@tool
def search_fashion_trends(query: str, limit: int = 3) -> List[dict]:
    """
    Search current fashion trends relevant to the query

    Note: This is OPTIONAL. GPT-4 already has extensive fashion knowledge.
    Only use web search if you need the very latest 2024/2025 trends.
    """
    try:
        # Option 1: Use web search for real-time trends (requires internet)
        # from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
        # search = DuckDuckGoSearchAPIWrapper()
        # results = search.results(f"{query} fashion trends 2024 2025", max_results=limit)

        # Option 2: For now, return GPT-4's built-in trend knowledge (sufficient for most cases)
        # GPT-4 already knows major trends through its training data
        return []  # Empty list means "use GPT-4's built-in knowledge"

    except Exception as e:
        print(f"Error searching trends: {e}")
        return []


# Create the LLM with tools bound
def create_llm_with_tools():
    """Create LLM with styling tools bound"""
    llm = ChatOpenAI(
        model=settings.OPENAI_LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7
    )

    # Bind tools to LLM
    tools = [get_user_preferences, search_outfit_history, search_fashion_trends]
    return llm.bind_tools(tools)


# Agent node - makes autonomous decisions about which tools to use
async def agent_node(state: AgentState) -> AgentState:
    """
    Autonomous agent that decides which tools to use based on the query
    """
    print(f"[Agent] Processing query: {state['query']}")

    # Get weather context if available
    weather_context = state.get('weather_context', None)

    # Build weather section for system prompt
    weather_section = ""
    if weather_context and not weather_context.get('error'):
        weather_section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌤️ WEATHER CONTEXT (CRITICAL - USE THIS!):

Location: {weather_context.get('location', 'Unknown')}
Date: {weather_context.get('date', 'Unknown')}
Temperature: {weather_context.get('temperature', 'Unknown')}
Conditions: {weather_context.get('conditions', 'Unknown')}
Feels Like: {weather_context.get('feels_like', 'N/A')}
Humidity: {weather_context.get('humidity', 'N/A')}

⚠️ MAKE CLIMATE-APPROPRIATE RECOMMENDATIONS!

**Temperature Guidelines:**

🥶 **COLD (Below 40°F/4°C):**
- Heavy winter coats, parkas, wool sweaters
- Thermal layers, long underwear
- Thick fabrics: wool, fleece, down
- Accessories: scarves, gloves, beanies
- Example: "Layer a wool sweater under a warm parka"

❄️ **COOL (40-55°F / 4-13°C):**
- Medium coats, jackets, hoodies
- Layering is key (can add/remove)
- Medium-weight fabrics: denim, cotton blends
- Light scarves optional
- Example: "A blazer with a light sweater underneath"

🌡️ **MODERATE (55-70°F / 13-21°C):**
- Light jackets, cardigans, long sleeves
- Can go with or without jacket
- Comfortable single-layer clothing
- Example: "A long-sleeve shirt with optional cardigan"

☀️ **WARM (70-85°F / 21-29°C):**
- Light shirts, breathable fabrics
- Short sleeves, light materials
- Cotton, linen, breathable blends
- Avoid heavy layers
- Example: "A cotton button-down shirt"

🔥 **HOT (Above 85°F/29°C):**
- Ultra-lightweight, loose-fitting
- Moisture-wicking, breathable fabrics
- Linen, light cotton, performance fabrics
- Light colors (reflect heat)
- Minimal layers
- Example: "A linen shirt - breathes in the heat"

**Additional Weather Factors:**

🌧️ **Rain/Wet:**
- Water-resistant outer layers
- Avoid suede, delicate fabrics
- Waterproof footwear
- Example: "Add a water-resistant trench coat"

💨 **Windy:**
- Windbreaker or closed jackets
- Avoid loose, flowing items
- Secure layering
- Example: "A windbreaker over your outfit"

☀️ **Sunny/High UV:**
- Sun protection considerations
- Hats, sunglasses for outdoor events
- Light colors to reflect sun

💧 **High Humidity:**
- Extra breathable fabrics
- Moisture-wicking materials
- Looser fits (less clingy when sweaty)
- Avoid: heavy fabrics, tight clothing

IMPORTANT:
- Temperature is {weather_context.get('temperature', 'Unknown')}
- ALWAYS factor this into your recommendations!
- Mention weather in your reasoning
- Add a "climate_note" to each recommendation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    else:
        weather_section = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ NO WEATHER DATA AVAILABLE

Provide VERSATILE recommendations with layering options:
- Suggest pieces that work in multiple temperatures
- Recommend layers (user can add/remove as needed)
- Mention: "Adjust layers based on your local weather"
- Provide options: "If it's cold, add X. If warm, skip Y"

Example response:
"I recommend a layered approach since I don't have weather data:
 - Base: Cotton button-down shirt
 - Mid-layer: Lightweight cardigan (remove if warm)
 - Outer: Blazer (optional depending on temperature)

💡 Tip: Check your local weather and adjust layers accordingly!"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # Create system message with instructions
    system_message = SystemMessage(content=f"""You are an expert personal stylist AI with access to tools.

Your goal: Provide personalized outfit recommendations based on the user's request.

{weather_section}

AVAILABLE TOOLS:
1. get_user_preferences - Fetch user's style preferences (colors, aesthetics, occasions, budget, body type)
2. search_outfit_history - Search user's wardrobe using vector similarity (finds relevant items they own)
3. search_fashion_trends - Search current fashion trends (OPTIONAL - GPT-4 already knows trends)

DECISION LOGIC - ALWAYS CHECK WARDROBE FOR OUTFIT RECOMMENDATIONS:

**When to use get_user_preferences:**
- For ANY outfit recommendation request
- You need to know their style, colors, or preferences
- SKIP ONLY if: Query is purely about trends, not outfits

**When to use search_outfit_history:**
- ⚠️ CRITICAL: Use this for ALMOST ALL outfit recommendations!
- User asks "what should I wear", "outfit ideas", "help me style", etc.
- Even if they don't explicitly mention "my wardrobe", CHECK IT ANYWAY
- This helps you give personalized advice using items they actually own
- SKIP ONLY if: User explicitly asks about trends only, or shopping recommendations only

**When to use search_fashion_trends:**
- User explicitly asks about trends ("what's trending?", "latest fashion")
- SKIP MOST OF THE TIME - GPT-4 already has excellent fashion knowledge

EXAMPLES:

Query: "What should I wear for a business meeting?"
→ ✅ Use: get_user_preferences (for their style)
→ ✅ Use: search_outfit_history (to find items they own)
→ ❌ Skip: search_fashion_trends (not needed)

Query: "I need outfit ideas for a date"
→ ✅ Use: get_user_preferences (personalization)
→ ✅ Use: search_outfit_history (check their wardrobe first!)
→ ❌ Skip: search_fashion_trends (you know date fashion)

Query: "What's trending in streetwear 2025?"
→ ❌ Skip: get_user_preferences (not personalized request)
→ ❌ Skip: search_outfit_history (not about outfits)
→ ✅ Use: search_fashion_trends (explicitly about trends)

Query: "Help me look good for tomorrow"
→ ✅ Use: get_user_preferences (personalization)
→ ✅ Use: search_outfit_history (check what they have!)
→ ❌ Skip: search_fashion_trends (not needed)

RESPONSE STRUCTURE - Combine Wardrobe + Generic Suggestions:

After using tools, provide recommendations in TWO SECTIONS:

**Section 1: From Your Wardrobe** (if search_outfit_history returned items)
- Reference specific items they own
- Use similarity scores to judge quality
- If similarity > 0.7: "Perfect match!"
- If similarity 0.4-0.7: "These could work..."
- If similarity < 0.4: "I couldn't find exactly that, but here are alternatives..."

**Section 2: Additional Suggestions** (always include this)
- General fashion advice
- Items to consider adding to wardrobe
- Styling principles and tips

FINAL OUTPUT FORMAT:
{{
  "recommendations": [
    {{
      "item": "Specific outfit (from wardrobe OR generic suggestion)",
      "reasoning": "Why this works (mention wardrobe items by filename if available)",
      "styling_tip": "Fashion principle or color theory",
      "trend_note": "Current trend relevance (if applicable)",
      "climate_note": "How this outfit works for the weather (REQUIRED if weather data available)",
      "confidence": 0.85,
      "wardrobe_based": true  // true if using user's actual items, false if generic
    }}
  ]
}}

IMPORTANT: Be PROACTIVE about checking the wardrobe! Users want personalized advice based on what they own!
""")

    # Build messages list
    messages = [system_message]
    messages.extend(state['messages'])

    # Add user query if not already in messages
    if not state['messages'] or not isinstance(state['messages'][-1], HumanMessage):
        messages.append(HumanMessage(content=state['query']))

    # Get LLM with tools
    llm_with_tools = create_llm_with_tools()

    # Invoke LLM - it will decide whether to use tools
    response = await llm_with_tools.ainvoke(messages)

    print(f"[Agent] LLM response type: {type(response)}")
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"[Agent] LLM wants to use {len(response.tool_calls)} tools")
    else:
        print(f"[Agent] LLM gave final answer without tools")

    return {"messages": [response]}


# Tool execution node
tools_list = [get_user_preferences, search_outfit_history, search_fashion_trends]
tool_node = ToolNode(tools_list)


# Router: decide if we should continue to tools or end
def should_continue(state: AgentState) -> str:
    """Determine if we should call tools or end"""
    messages = state['messages']
    last_message = messages[-1]

    # If the LLM makes tool calls, route to tools node
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print(f"[Router] Routing to tools")
        return "tools"

    # Otherwise, we're done
    print(f"[Router] Routing to end")
    return "end"


# Build the LangGraph workflow
def create_styling_agent() -> StateGraph:
    """Create and compile the autonomous styling agent workflow"""

    # Initialize the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)  # Main agent that decides tool usage
    workflow.add_node("tools", tool_node)   # Tool execution node

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",  # If LLM wants to use tools
            "end": END         # If LLM has final answer
        }
    )

    # After tools execute, go back to agent for final response
    workflow.add_edge("tools", "agent")

    # Compile the graph
    app = workflow.compile()

    return app


# Agent execution function
async def run_styling_agent(
    user_id: str,
    query: str,
    user_preferences: Optional[dict] = None,
    weather_context: Optional[dict] = None
) -> dict:
    """
    Run the autonomous styling agent workflow

    Args:
        user_id: The user's ID
        query: The styling query from the user
        user_preferences: Optional pre-loaded user preferences (unused in new version)
        weather_context: Optional weather data (temperature, conditions, location, etc.)

    Returns:
        dict: The agent's recommendations and response
    """

    # Create the agent
    agent = create_styling_agent()

    # Initialize state - now with weather context!
    initial_state: AgentState = {
        "messages": [],
        "user_id": user_id,
        "query": query,
        "weather_context": weather_context
    }

    # Run the agent
    print(f"\n{'='*50}")
    print(f"Starting Autonomous Styling Agent for user: {user_id}")
    print(f"Query: {query}")
    print(f"{'='*50}\n")

    final_state = await agent.ainvoke(initial_state)

    print(f"\n{'='*50}")
    print(f"Agent completed successfully")
    print(f"{'='*50}\n")

    # Extract final message content
    messages = final_state['messages']
    final_message = messages[-1] if messages else None

    # Parse recommendations from final message
    recommendations = []
    tools_used = []

    # Check which tools were used by looking at ToolMessages
    for msg in messages:
        if isinstance(msg, ToolMessage):
            tools_used.append(msg.name if hasattr(msg, 'name') else 'unknown')

    # Try to parse JSON from final AI message
    if final_message and hasattr(final_message, 'content'):
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{[\s\S]*"recommendations"[\s\S]*\}', final_message.content)
            if json_match:
                data = json.loads(json_match.group())
                recommendations = data.get('recommendations', [])
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Could not parse recommendations from response: {e}")
            # Return raw response if JSON parsing fails
            recommendations = [{
                "item": "See full response below",
                "reasoning": final_message.content if hasattr(final_message, 'content') else str(final_message),
                "styling_tip": "",
                "trend_note": "",
                "confidence": 0.8
            }]

    # Extract and return results
    return {
        "user_id": final_state['user_id'],
        "query": final_state['query'],
        "recommendations": recommendations,
        "messages": [
            msg.content if hasattr(msg, 'content') else str(msg)
            for msg in messages
            if not isinstance(msg, SystemMessage)  # Exclude system messages
        ],
        "tools_used": list(set(tools_used)),  # Unique tools used
        "context_used": {
            "preferences": "get_user_preferences" in tools_used,
            "outfit_history": "search_outfit_history" in tools_used,
            "trends": "search_fashion_trends" in tools_used
        }
    }


# Example usage
if __name__ == "__main__":
    import asyncio

    async def test():
        result = await run_styling_agent(
            user_id="user_123",
            query="What should I wear for a business casual meeting?"
        )
        print("\nFinal Result:")
        print(json.dumps(result, indent=2))

    asyncio.run(test())
