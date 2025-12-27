"""
LangGraph Agent for StylistAI
Handles the multi-step styling recommendation workflow with state management
"""

from typing import TypedDict, List, Optional, Annotated
from operator import add
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from app.config import settings
import json


# Define the agent state
class AgentState(TypedDict):
    """State object for the styling agent"""
    messages: Annotated[List[BaseMessage], add]
    user_id: str
    user_preferences: Optional[dict]
    query: str
    outfit_context: Optional[List[dict]]
    trend_context: Optional[List[dict]]
    recommendations: Optional[List[dict]]
    next_action: Optional[str]


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


# Agent workflow nodes
def analyze_query(state: AgentState) -> AgentState:
    """Analyze the user's query and determine what information is needed"""
    print(f"[Agent] Analyzing query: {state['query']}")

    # Determine next action based on query type
    query_lower = state['query'].lower()

    if "outfit" in query_lower or "wear" in query_lower:
        state['next_action'] = "retrieve_context"
    elif "trend" in query_lower:
        state['next_action'] = "search_trends"
    else:
        state['next_action'] = "retrieve_context"

    state['messages'].append(
        AIMessage(content=f"Analyzing your request about: {state['query']}")
    )

    return state


async def retrieve_user_context(state: AgentState) -> AgentState:
    """Retrieve user preferences and past outfit history"""
    print(f"[Agent] Retrieving context for user: {state['user_id']}")

    # Get user preferences
    prefs = get_user_preferences.invoke({"user_id": state['user_id']})
    state['user_preferences'] = prefs

    # Search similar past outfits using CLIP
    past_outfits = await search_outfit_history.ainvoke({
        "user_id": state['user_id'],
        "query": state['query'],
        "limit": 5
    })
    state['outfit_context'] = past_outfits

    state['next_action'] = "search_trends"

    return state


def retrieve_trend_context(state: AgentState) -> AgentState:
    """Retrieve current fashion trends relevant to the query"""
    print(f"[Agent] Searching fashion trends")

    trends = search_fashion_trends.invoke({
        "query": state['query'],
        "limit": 3
    })
    state['trend_context'] = trends

    state['next_action'] = "generate_recommendations"

    return state


def generate_recommendations(state: AgentState) -> AgentState:
    """Generate personalized styling recommendations using OpenAI"""
    print(f"[Agent] Generating recommendations with OpenAI")

    # Initialize OpenAI LLM with JSON mode
    llm = ChatOpenAI(
        model=settings.OPENAI_LLM_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
        model_kwargs={"response_format": {"type": "json_object"}}
    )

    # Build enhanced context that leverages GPT-4's built-in fashion knowledge
    user_prefs = state.get('user_preferences', {})
    outfit_context = state.get('outfit_context', [])

    # Extract key user info
    favorite_colors = user_prefs.get('colors', [])
    style_aesthetics = user_prefs.get('style_aesthetics', [])
    occasions = user_prefs.get('occasions', [])
    budget = user_prefs.get('budget', 'mid-range')
    body_type = user_prefs.get('body_type', 'average')

    # Format wardrobe context
    wardrobe_items = []
    for outfit in outfit_context:
        wardrobe_items.append(f"- {outfit.get('filename', 'Unknown item')} (similarity: {outfit.get('similarity_score', 0):.2f})")
    wardrobe_str = "\n".join(wardrobe_items) if wardrobe_items else "No wardrobe items found yet"

    context = f"""
You are an expert personal stylist with deep knowledge of fashion, color theory, styling principles, and current trends.

USER'S STYLING REQUEST: {state['query']}

USER'S PROFILE:
- Favorite Colors: {', '.join(favorite_colors) if favorite_colors else 'Not specified'}
- Style Aesthetics: {', '.join(style_aesthetics) if style_aesthetics else 'Not specified'}
- Typical Occasions: {', '.join(occasions) if occasions else 'Not specified'}
- Budget Range: {budget}
- Body Type: {body_type}

USER'S WARDROBE (items they own):
{wardrobe_str}

YOUR TASK:
Using your expertise in fashion styling, color theory, and current trends, provide 3-5 personalized outfit recommendations that:

1. **Use their wardrobe**: Incorporate items they already own when relevant
2. **Match their style**: Align with their favorite colors and aesthetics
3. **Apply fashion principles**: Use your knowledge of color combinations, proportions, layering, and fit
4. **Consider current trends**: Reference 2024/2025 fashion trends where appropriate
5. **Respect their budget**: Suggest options within their budget range
6. **Fit their occasions**: Ensure recommendations work for their lifestyle

IMPORTANT: Mix their existing wardrobe items with styling suggestions. For example:
- "Pair your navy blazer with beige chinos (navy+beige is a classic sophisticated combination)"
- "Layer an oversized blazer over a fitted turtleneck (oversized tailoring is trending)"

Provide your response as a JSON object with this structure:
{{
  "recommendations": [
    {{
      "item": "Specific outfit or clothing suggestion",
      "reasoning": "Why this works for them (reference their preferences, colors, style)",
      "styling_tip": "Fashion principle or color theory behind this choice",
      "trend_note": "How this relates to current trends (if applicable)",
      "confidence": 0.0-1.0
    }}
  ]
}}
"""

    # Generate recommendations using GPT-4
    response = llm.invoke([HumanMessage(content=context)])

    # Parse the JSON response
    try:
        response_data = json.loads(response.content)
        state['recommendations'] = response_data.get('recommendations', [])
    except json.JSONDecodeError as e:
        print(f"Error parsing GPT-4 JSON response: {e}")
        # Fallback to empty recommendations
        state['recommendations'] = []
        # Store raw response for debugging
        state['messages'].append(
            AIMessage(content=f"[Debug] Raw response: {response.content}")
        )

    state['messages'].append(
        AIMessage(content=response.content)
    )

    state['next_action'] = "format_response"

    return state


def format_response(state: AgentState) -> AgentState:
    """Format the final response for the user"""
    print(f"[Agent] Formatting final response")

    response = {
        "query": state['query'],
        "recommendations": state['recommendations'],
        "personalization_factors": {
            "used_preferences": bool(state.get('user_preferences')),
            "used_history": bool(state.get('outfit_context')),
            "used_trends": bool(state.get('trend_context'))
        }
    }

    state['messages'].append(
        AIMessage(content=json.dumps(response, indent=2))
    )

    state['next_action'] = "end"

    return state


# Router function to determine next node
def route_next_action(state: AgentState) -> str:
    """Route to the next node based on the agent's decision"""
    next_action = state.get('next_action', 'end')

    routing = {
        "retrieve_context": "retrieve_user_context",
        "search_trends": "retrieve_trend_context",
        "generate_recommendations": "generate_recommendations",
        "format_response": "format_response",
        "end": END
    }

    return routing.get(next_action, END)


# Build the LangGraph workflow
def create_styling_agent() -> StateGraph:
    """Create and compile the styling agent workflow"""

    # Initialize the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("analyze_query", analyze_query)
    workflow.add_node("retrieve_user_context", retrieve_user_context)
    workflow.add_node("retrieve_trend_context", retrieve_trend_context)
    workflow.add_node("generate_recommendations", generate_recommendations)
    workflow.add_node("format_response", format_response)

    # Set entry point
    workflow.set_entry_point("analyze_query")

    # Add conditional edges
    workflow.add_conditional_edges(
        "analyze_query",
        route_next_action
    )

    workflow.add_conditional_edges(
        "retrieve_user_context",
        route_next_action
    )

    workflow.add_conditional_edges(
        "retrieve_trend_context",
        route_next_action
    )

    workflow.add_conditional_edges(
        "generate_recommendations",
        route_next_action
    )

    workflow.add_conditional_edges(
        "format_response",
        route_next_action
    )

    # Compile the graph
    app = workflow.compile()

    return app


# Agent execution function
async def run_styling_agent(
    user_id: str,
    query: str,
    user_preferences: Optional[dict] = None
) -> dict:
    """
    Run the styling agent workflow

    Args:
        user_id: The user's ID
        query: The styling query from the user
        user_preferences: Optional pre-loaded user preferences

    Returns:
        dict: The agent's recommendations and response
    """

    # Create the agent
    agent = create_styling_agent()

    # Initialize state
    initial_state: AgentState = {
        "messages": [HumanMessage(content=query)],
        "user_id": user_id,
        "user_preferences": user_preferences,
        "query": query,
        "outfit_context": None,
        "trend_context": None,
        "recommendations": None,
        "next_action": None
    }

    # Run the agent
    print(f"\n{'='*50}")
    print(f"Starting Styling Agent for user: {user_id}")
    print(f"Query: {query}")
    print(f"{'='*50}\n")

    final_state = await agent.ainvoke(initial_state)

    print(f"\n{'='*50}")
    print(f"Agent completed successfully")
    print(f"{'='*50}\n")

    # Extract and return results
    return {
        "user_id": final_state['user_id'],
        "query": final_state['query'],
        "recommendations": final_state.get('recommendations', []),
        "messages": [msg.content for msg in final_state['messages']],
        "context_used": {
            "preferences": final_state.get('user_preferences') is not None,
            "outfit_history": final_state.get('outfit_context') is not None,
            "trends": final_state.get('trend_context') is not None
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
