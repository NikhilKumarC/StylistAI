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
from app.services.conversational_stylist import get_conversational_stylist
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
    Have a natural conversation with your AI stylist

    This endpoint creates a friendly, conversational experience where the AI:
    1. Chats naturally like a real stylist
    2. Asks follow-up questions to understand your needs
    3. Builds context organically through conversation
    4. Gives recommendations when ready (not immediately)

    The AI will make you feel comfortable and understood before suggesting outfits!

    Args:
        request: Your message to the stylist
        current_user: Authenticated user

    Returns:
        Conversational response from your AI stylist
    """
    try:
        user_id = current_user["uid"]
        logger.info(f"Conversational styling query from user {user_id}: {request.query}")

        # Get conversation history for this user
        if user_id not in _conversation_histories:
            _conversation_histories[user_id] = []

        conversation_history = _conversation_histories[user_id]

        # Get user preferences
        user_prefs = UserService.get_user_preferences(user_id)

        # Get conversational stylist
        stylist = get_conversational_stylist()

        # Have conversation
        chat_result = await stylist.chat(
            user_message=request.query,
            user_id=user_id,
            conversation_history=conversation_history,
            user_preferences=user_prefs
        )

        ai_response = chat_result["response"]

        # Save to conversation history
        conversation_history.append({"role": "user", "content": request.query})
        conversation_history.append({"role": "assistant", "content": ai_response})

        # If AI is ready to give recommendations, search wardrobe
        recommendations = []
        if chat_result.get("should_search_wardrobe"):
            try:
                # Search user's wardrobe for relevant items
                similar_outfits = await ImageService.search_similar_outfits(
                    query=request.query,
                    user_id=user_id,
                    n_results=5
                )

                # If we found items, enhance the response
                if similar_outfits:
                    logger.info(f"Found {len(similar_outfits)} wardrobe items to reference")

                    # Run full styling agent for detailed recommendations
                    agent_result = await run_styling_agent(
                        user_id=user_id,
                        query=request.query,
                        user_preferences=user_prefs
                    )

                    # Format recommendations
                    for rec in agent_result.get('recommendations', []):
                        recommendations.append({
                            "title": rec.get('item', 'Outfit Recommendation'),
                            "description": rec.get('reasoning', ''),
                            "styling_tip": rec.get('styling_tip', ''),
                            "trend_note": rec.get('trend_note', ''),
                            "confidence_score": rec.get('confidence', 0.85)
                        })

            except Exception as e:
                logger.warning(f"Error searching wardrobe: {e}")
                # Continue with conversational response only

        # Return conversational response
        return {
            "response": ai_response,
            "recommendations": recommendations,
            "is_conversational": chat_result.get("needs_more_context", True),
            "context_complete": not chat_result.get("needs_more_context", True)
        }

    except Exception as e:
        logger.error(f"Error in conversational styling: {str(e)}")
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
