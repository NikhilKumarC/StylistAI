"""
Styling API endpoints using conversational agent
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from app.models.user import UserResponse
from app.models.styling import (
    StylingQueryRequest,
    StylingResponse,
    StylingRecommendation,
    TrendInsight
)
from app.core.dependencies import get_current_user
from app.services.conversational_stylist_autonomous import chat_with_stylist
from app.services.langgraph_agent import run_styling_agent
from app.services.user_service import UserService
from app.services.image_service import ImageService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/styling", tags=["Styling"])

# In-memory conversation storage (for POC - use Redis in production)
_conversation_histories = {}


@router.post("/query")
async def get_styling_advice(
    request: StylingQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    🆕 Now uses AUTONOMOUS AGENT with Pure Sequential Pattern! (Updated)

    Have a natural conversation with your AI stylist

    This endpoint uses the autonomous multi-agent architecture where:
    1. Agent 2 (Conversational) gathers context through natural dialogue
    2. API detects when context is complete (weather + readiness + depth)
    3. Agent 3 (LangGraph) generates recommendations with intelligent tool selection

    Benefits of the autonomous system:
    - Truly autonomous tool selection (0-3 tools as needed)
    - Climate-aware recommendations
    - More efficient (only calls needed tools)
    - Better conversation flow
    - Proper multi-agent orchestration

    Args:
        request: Your message to the stylist
        current_user: Authenticated user

    Returns:
        Conversational response with recommendations when context is complete
    """
    try:
        user_id = current_user["uid"]
        logger.info(f"[Autonomous] Styling query from user {user_id}: {request.query}")

        # Get conversation history for this user
        if user_id not in _conversation_histories:
            _conversation_histories[user_id] = []

        conversation_history = _conversation_histories[user_id]

        # Get user preferences
        user_prefs = UserService.get_user_preferences(user_id)

        # STEP 1: Call Conversational Agent (Agent 2) - Pure Sequential Pattern
        logger.info(f"[Autonomous] Step 1: Calling conversational agent...")
        chat_result = await chat_with_stylist(
            user_id=user_id,
            user_message=request.query,
            conversation_history=conversation_history,
            user_preferences=user_prefs
        )

        ai_response = chat_result["response"]
        tools_used = chat_result.get("tools_used", [])
        weather_info = chat_result.get("weather_info")
        needs_more_context = chat_result.get("needs_more_context", True)

        logger.info(f"[Autonomous] Conversational agent used tools: {tools_used}")
        logger.info(f"[Autonomous] Needs more context: {needs_more_context}")

        # Save to conversation history
        conversation_history.append({"role": "user", "content": request.query})
        conversation_history.append({"role": "assistant", "content": ai_response})

        recommendations = []

        # STEP 2: PURE SEQUENTIAL PATTERN - Explicit Orchestration
        # Check if conversational agent gathered complete context
        if not needs_more_context and weather_info:
            logger.info(f"[Autonomous] Step 2: Context complete, orchestrating LangGraph agent...")

            # Build enriched query with all gathered context
            enriched_query = request.query
            if weather_info:
                enriched_query += f"\n\nWeather context: {weather_info.get('location')} on {weather_info.get('date')} - {weather_info.get('temperature')}, {weather_info.get('conditions')}"

            # Call LangGraph Agent (Agent 3) directly
            agent_result = await run_styling_agent(
                user_id=user_id,
                query=enriched_query,
                user_preferences=user_prefs,
                weather_context=weather_info
            )

            # Format recommendations
            for rec in agent_result.get('recommendations', []):
                recommendations.append({
                    "title": rec.get('item', 'Outfit Recommendation'),
                    "description": rec.get('reasoning', ''),
                    "styling_tip": rec.get('styling_tip', ''),
                    "trend_note": rec.get('trend_note', ''),
                    "climate_note": rec.get('climate_note', ''),
                    "confidence_score": rec.get('confidence', 0.85)
                })

            logger.info(f"[Autonomous] Generated {len(recommendations)} recommendations via sequential orchestration")

        # Return response
        return {
            "response": ai_response,
            "recommendations": recommendations,
            "is_conversational": needs_more_context,
            "context_complete": not needs_more_context,
            "weather_info": weather_info,
            "tools_used": tools_used,
            "agent_architecture": "pure_sequential",
            "orchestration_method": "explicit_api_orchestration"
        }

    except Exception as e:
        logger.error(f"[Autonomous] Error in styling conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process conversation: {str(e)}"
        )


@router.post("/query-autonomous")
async def get_styling_advice_autonomous(
    request: StylingQueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    🆕 AUTONOMOUS MULTI-AGENT STYLING CONVERSATION (Sequential Pattern)

    This endpoint uses the new autonomous agent architecture where:
    1. Agent 2 (Conversational Stylist) gathers context through natural conversation
    2. When context is complete, Agent 3 (LangGraph) generates recommendations
    3. API orchestrates agents explicitly (Sequential Pattern, not tool-wrapper)

    The autonomous agents use LLM tool calling to decide:
    - When to fetch weather (Agent 2)
    - When to search wardrobe (Agent 3)
    - When to search trends (Agent 3)
    - Which tools are actually needed (0-3 tools, not always all)

    Benefits over /query:
    - Truly autonomous tool selection
    - Climate-aware recommendations
    - More efficient (only calls needed tools)
    - Better conversation flow
    - Proper multi-agent orchestration

    Args:
        request: Your message to the stylist
        current_user: Authenticated user

    Returns:
        Conversational response with recommendations when ready
    """
    try:
        user_id = current_user["uid"]
        logger.info(f"[Autonomous] Styling query from user {user_id}: {request.query}")

        # Get conversation history for this user
        if user_id not in _conversation_histories:
            _conversation_histories[user_id] = []

        conversation_history = _conversation_histories[user_id]

        # Get user preferences
        user_prefs = UserService.get_user_preferences(user_id)

        # STEP 1: Call Conversational Agent (Agent 2) to gather context
        logger.info(f"[Autonomous] Step 1: Calling conversational agent...")
        chat_result = await chat_with_stylist(
            user_id=user_id,
            user_message=request.query,
            conversation_history=conversation_history,
            user_preferences=user_prefs
        )

        ai_response = chat_result["response"]
        tools_used = chat_result.get("tools_used", [])
        weather_info = chat_result.get("weather_info")
        has_recommendations = chat_result.get("has_recommendations", False)
        needs_more_context = chat_result.get("needs_more_context", True)

        logger.info(f"[Autonomous] Conversational agent used tools: {tools_used}")
        logger.info(f"[Autonomous] Has recommendations: {has_recommendations}")
        logger.info(f"[Autonomous] Needs more context: {needs_more_context}")

        # Save to conversation history
        conversation_history.append({"role": "user", "content": request.query})
        conversation_history.append({"role": "assistant", "content": ai_response})

        recommendations = []

        # STEP 2: PURE SEQUENTIAL PATTERN - Explicit Orchestration
        # Check if conversational agent gathered complete context (weather + readiness)
        # If so, API explicitly calls LangGraph Agent (Agent 3)
        if not needs_more_context and weather_info:
            logger.info(f"[Autonomous] Step 2: Context complete, orchestrating LangGraph agent...")

            # Build enriched query with all gathered context
            enriched_query = request.query
            if weather_info:
                enriched_query += f"\n\nWeather context: {weather_info.get('location')} on {weather_info.get('date')} - {weather_info.get('temperature')}, {weather_info.get('conditions')}"

            # Call LangGraph Agent (Agent 3) directly - TRUE SEQUENTIAL PATTERN
            agent_result = await run_styling_agent(
                user_id=user_id,
                query=enriched_query,
                user_preferences=user_prefs,
                weather_context=weather_info
            )

            # Format recommendations
            for rec in agent_result.get('recommendations', []):
                recommendations.append({
                    "title": rec.get('item', 'Outfit Recommendation'),
                    "description": rec.get('reasoning', ''),
                    "styling_tip": rec.get('styling_tip', ''),
                    "trend_note": rec.get('trend_note', ''),
                    "climate_note": rec.get('climate_note', ''),
                    "confidence_score": rec.get('confidence', 0.85)
                })

            logger.info(f"[Autonomous] Generated {len(recommendations)} recommendations via explicit sequential orchestration")

        # Format response
        return {
            "response": ai_response,
            "recommendations": recommendations,
            "is_conversational": needs_more_context,
            "context_complete": not needs_more_context,
            "weather_info": weather_info,
            "tools_used": tools_used,
            "agent_architecture": "pure_sequential",
            "orchestration_method": "explicit_api_orchestration",
            "pattern": "Agent 2 (Conversational) → API checks readiness → Agent 3 (LangGraph)"
        }

    except Exception as e:
        logger.error(f"[Autonomous] Error in styling conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process conversation: {str(e)}"
        )


@router.post("/analyze-outfit")
async def analyze_outfit_image(
    # TODO: Add image upload and analysis
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze an outfit image and provide styling feedback

    This endpoint will:
    1. Upload image to Google Cloud Storage
    2. Extract outfit components using vision AI
    3. Run LangGraph agent to analyze the outfit
    4. Provide improvement suggestions

    Status: Coming Soon
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Outfit image analysis coming soon. Currently implementing ChromaDB and image processing."
    )


@router.get("/agent-status")
async def get_agent_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the status of the LangGraph agent workflow

    Useful for debugging and understanding the agent's capabilities
    """
    return {
        "status": "operational",
        "agent_type": "langgraph",
        "workflow_steps": [
            "analyze_query",
            "retrieve_user_context",
            "retrieve_trend_context",
            "generate_recommendations",
            "format_response"
        ],
        "features": {
            "user_preferences": True,
            "outfit_history": True,
            "trend_search": True,
            "personalization": True,
            "stateful": True
        },
        "models": {
            "llm": "openai",
            "model_name": "gpt-4-turbo",
            "embeddings": "openai-text-embedding-3-large",
            "vector_db": "chromadb"
        }
    }


@router.get("/debug/workflow")
async def debug_workflow():
    """
    Debug endpoint to visualize the LangGraph workflow

    Returns the workflow structure for debugging and visualization
    """
    return {
        "workflow": {
            "entry_point": "analyze_query",
            "nodes": {
                "analyze_query": {
                    "description": "Analyzes user query and determines next action",
                    "next": "conditional (retrieve_context or search_trends)"
                },
                "retrieve_user_context": {
                    "description": "Fetches user preferences and past outfit history",
                    "tools": ["get_user_preferences", "search_outfit_history"],
                    "next": "retrieve_trend_context"
                },
                "retrieve_trend_context": {
                    "description": "Searches current fashion trends",
                    "tools": ["search_fashion_trends"],
                    "next": "generate_recommendations"
                },
                "generate_recommendations": {
                    "description": "Uses LLM to generate personalized recommendations",
                    "model": "GPT-4 or Claude",
                    "next": "format_response"
                },
                "format_response": {
                    "description": "Formats final response for user",
                    "next": "END"
                }
            }
        }
    }
