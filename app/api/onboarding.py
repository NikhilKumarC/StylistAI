"""
Onboarding API endpoints
Handles the conversational onboarding flow for new users
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Optional, List
from pydantic import BaseModel
from app.models.user import UserResponse
from app.core.dependencies import get_current_user
from app.services.onboarding_agent_autonomous import run_autonomous_onboarding, save_autonomous_onboarding_data
from app.services.user_service import UserService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


class OnboardingMessage(BaseModel):
    """User's response during onboarding"""
    message: str


class OnboardingResponse(BaseModel):
    """Response from onboarding agent"""
    next_question: str
    current_step: str
    is_complete: bool
    collected_data: Optional[dict] = None
    photos_requested: Optional[bool] = False


# In-memory storage for onboarding states (replace with Redis/database in production)
_onboarding_states = {}


@router.post("/start", response_model=OnboardingResponse)
async def start_onboarding(
    current_user: dict = Depends(get_current_user)
):
    """
    🆕 Now uses AUTONOMOUS AGENT! (Updated)

    Start the onboarding process for a new user

    This initiates a conversational flow using the autonomous agent that:
    - Feels like chatting with a friendly stylist (NOT a form!)
    - Adapts questions based on your responses
    - Handles questions back from you
    - Accepts when you don't want to share something (stores NULL)
    - Knows when it has enough information
    """
    try:
        user_id = current_user["uid"]
        user_email = current_user.get("email")
        logger.info(f"[Autonomous] Starting onboarding for user: {user_id}")

        # Ensure user exists in database
        UserService.ensure_user_exists(user_id, user_email)

        # Check if user has already completed onboarding
        user_prefs = UserService.get_user_preferences(user_id)
        if user_prefs and user_prefs.get("onboarding_completed"):
            return OnboardingResponse(
                next_question="You've already completed onboarding! Ready to get styling advice?",
                current_step="complete",
                is_complete=True,
                collected_data=user_prefs
            )

        # Get conversation history
        if user_id not in _autonomous_conversations:
            _autonomous_conversations[user_id] = []

        # Use AUTONOMOUS AGENT
        result = await run_autonomous_onboarding(
            user_id=user_id,
            user_message=None,
            conversation_history=_autonomous_conversations[user_id]
        )

        ai_response = result["response"]
        is_complete = result.get("is_complete", False)

        # Save to conversation history
        _autonomous_conversations[user_id].append({"role": "assistant", "content": ai_response})

        # Store state for backward compatibility
        _onboarding_states[user_id] = {
            "next_question": ai_response,
            "current_step": "autonomous",
            "is_complete": is_complete,
            "collected_data": result.get("collected_data", {})
        }

        # Check if user wants to upload photos
        photos_requested = result.get("collected_data", {}).get("photos_requested", False) if is_complete else False

        return OnboardingResponse(
            next_question=ai_response,
            current_step="autonomous",
            is_complete=is_complete,
            collected_data=result.get("collected_data", {}) if is_complete else None,
            photos_requested=photos_requested
        )

    except Exception as e:
        logger.error(f"[Autonomous] Error starting onboarding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start onboarding: {str(e)}"
        )


@router.post("/respond", response_model=OnboardingResponse)
async def respond_to_onboarding(
    message: OnboardingMessage,
    current_user: dict = Depends(get_current_user)
):
    """
    🆕 Now uses AUTONOMOUS AGENT! (Updated)

    Respond to onboarding question

    The autonomous agent will:
    - Answer questions you ask back
    - Handle vague or irrelevant answers
    - Extract multiple pieces of info from one answer
    - Know when onboarding is complete
    """
    try:
        user_id = current_user["uid"]
        logger.info(f"[Autonomous] Processing response from user: {user_id}")

        # Get conversation history
        if user_id not in _autonomous_conversations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active onboarding session. Please start onboarding first."
            )

        conversation_history = _autonomous_conversations[user_id]

        # Check if already complete
        current_state = _onboarding_states.get(user_id, {})
        if current_state.get("is_complete"):
            return OnboardingResponse(
                next_question="Onboarding is already complete! You can start chatting.",
                current_step="complete",
                is_complete=True,
                collected_data=current_state["collected_data"]
            )

        # Use AUTONOMOUS AGENT
        result = await run_autonomous_onboarding(
            user_id=user_id,
            user_message=message.message,
            conversation_history=conversation_history
        )

        ai_response = result["response"]
        is_complete = result.get("is_complete", False)
        collected_data = result.get("collected_data", {})

        # Save to conversation history
        conversation_history.append({"role": "user", "content": message.message})
        conversation_history.append({"role": "assistant", "content": ai_response})

        # Update state
        _onboarding_states[user_id] = {
            "next_question": ai_response,
            "current_step": "autonomous",
            "is_complete": is_complete,
            "collected_data": collected_data
        }

        # If onboarding is complete, save preferences
        if is_complete:
            preferences = save_autonomous_onboarding_data(user_id, collected_data)
            logger.info(f"[Autonomous] Onboarding completed for user: {user_id}")

            # Check if user wants to upload photos
            photos_requested = collected_data.get("photos_requested", False)
            logger.info(f"[Autonomous] Photos requested: {photos_requested}")

            # Clear conversation history
            del _autonomous_conversations[user_id]
            if user_id in _onboarding_states:
                del _onboarding_states[user_id]

            return OnboardingResponse(
                next_question=ai_response,
                current_step="complete",
                is_complete=True,
                collected_data=preferences,
                photos_requested=photos_requested
            )

        return OnboardingResponse(
            next_question=ai_response,
            current_step="autonomous",
            is_complete=False,
            collected_data=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Autonomous] Error processing response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process response: {str(e)}"
        )


@router.get("/status")
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Check if user has completed onboarding

    Returns:
    - completed: Boolean indicating if onboarding is done
    - preferences: User's collected preferences (if completed)
    """
    try:
        user_id = current_user["uid"]
        user_prefs = UserService.get_user_preferences(user_id)

        if user_prefs and user_prefs.get("onboarding_completed"):
            return {
                "completed": True,
                "preferences": user_prefs
            }

        # Check if there's an active onboarding session
        active_session = _onboarding_states.get(user_id)

        return {
            "completed": False,
            "has_active_session": active_session is not None,
            "current_step": active_session.get("current_step") if active_session else None
        }

    except Exception as e:
        logger.error(f"Error checking onboarding status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check status: {str(e)}"
        )


@router.post("/skip")
async def skip_onboarding(
    current_user: dict = Depends(get_current_user)
):
    """
    Skip onboarding (for testing purposes)

    This sets default preferences so the user can start chatting immediately.
    """
    try:
        user_id = current_user["uid"]
        logger.info(f"Skipping onboarding for user: {user_id}")

        # Set default preferences
        default_preferences = {
            "style_aesthetics": ["modern", "casual"],
            "colors": ["navy", "grey", "white"],
            "occasions": ["casual", "work"],
            "fit_preferences": "fitted",
            "budget": "mid-range",
            "body_type": "average",
            "style_goals": ["look professional", "stay comfortable"],
            "onboarding_completed": True,
            "onboarding_skipped": True
        }

        UserService.save_user_preferences(user_id, default_preferences)

        # Clear any active session
        if user_id in _onboarding_states:
            del _onboarding_states[user_id]

        return {
            "message": "Onboarding skipped. Default preferences set.",
            "preferences": default_preferences
        }

    except Exception as e:
        logger.error(f"Error skipping onboarding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to skip onboarding: {str(e)}"
        )


# In-memory storage for autonomous onboarding conversations
_autonomous_conversations = {}


@router.post("/autonomous")
async def autonomous_onboarding_chat(
    message: Optional[OnboardingMessage] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    🆕 AUTONOMOUS ONBOARDING (Natural Conversational Flow)

    This endpoint uses the new autonomous onboarding agent that:
    - Feels like chatting with a friendly stylist (NOT a form!)
    - Adapts questions based on your responses
    - Handles questions back from you
    - Accepts when you don't want to share something (stores NULL)
    - Extracts multiple pieces of info from one answer
    - Knows when it has enough information

    Benefits over /start + /respond:
    - Single endpoint for entire conversation
    - More natural, less rigid
    - Handles edge cases gracefully
    - Better user experience

    Usage:
    1. First call with message=None to start
    2. Subsequent calls with your responses
    3. Agent will tell you when onboarding is complete

    Args:
        message: Your message (None for first call)
        current_user: Authenticated user

    Returns:
        Agent's response and completion status
    """
    try:
        user_id = current_user["uid"]
        user_email = current_user.get("email")

        # Ensure user exists in database
        UserService.ensure_user_exists(user_id, user_email)

        # Check if user has already completed onboarding
        user_prefs = UserService.get_user_preferences(user_id)
        if user_prefs and user_prefs.get("onboarding_completed"):
            return {
                "response": "You've already completed onboarding! Ready to get styling recommendations? Head over to the styling chat!",
                "is_complete": True,
                "onboarding_completed": True,
                "preferences": user_prefs
            }

        # Get conversation history
        if user_id not in _autonomous_conversations:
            _autonomous_conversations[user_id] = []

        conversation_history = _autonomous_conversations[user_id]

        # Run autonomous onboarding agent
        logger.info(f"[Autonomous Onboarding] User {user_id}: {message.message if message else 'Starting...'}")

        result = await run_autonomous_onboarding(
            user_id=user_id,
            user_message=message.message if message else None,
            conversation_history=conversation_history
        )

        ai_response = result["response"]
        is_complete = result.get("is_complete", False)
        collected_data = result.get("collected_data", {})

        # Save to conversation history
        if message and message.message:
            conversation_history.append({"role": "user", "content": message.message})
        conversation_history.append({"role": "assistant", "content": ai_response})

        # If onboarding is complete, save preferences
        if is_complete:
            logger.info(f"[Autonomous Onboarding] Complete for user {user_id}")
            preferences = save_autonomous_onboarding_data(user_id, collected_data)

            # Check if user wants to upload photos
            photos_requested = collected_data.get("photos_requested", False)
            logger.info(f"[Autonomous Onboarding] Photos requested: {photos_requested}")

            # Clear conversation history
            del _autonomous_conversations[user_id]

            return {
                "response": ai_response,
                "is_complete": True,
                "onboarding_completed": True,
                "preferences": preferences,
                "photos_requested": photos_requested,
                "message": "Onboarding complete! You're all set to get personalized styling advice!"
            }

        # Still gathering information
        return {
            "response": ai_response,
            "is_complete": False,
            "onboarding_completed": False,
            "collected_so_far": collected_data
        }

    except Exception as e:
        logger.error(f"[Autonomous Onboarding] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process onboarding: {str(e)}"
        )


@router.post("/upload-photos")
async def upload_wardrobe_photos(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload wardrobe/outfit photos during onboarding

    These photos will be:
    1. Validated (size, format)
    2. Generated CLIP embeddings
    3. Stored in Google Cloud Storage
    4. Embeddings stored in ChromaDB for similarity search
    5. Used to understand user's existing style

    Maximum 5 photos, each up to 10MB.
    Supported formats: JPG, JPEG, PNG, WEBP
    """
    try:
        user_id = current_user["uid"]
        user_email = current_user.get("email")
        logger.info(f"Receiving {len(files)} photos from user: {user_id}")

        # Ensure user exists in PostgreSQL before saving outfit images
        UserService.ensure_user_exists(user_id, user_email)

        if len(files) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 photos allowed"
            )

        from app.services.image_service import ImageService

        uploaded_files = []
        image_data = []

        for file in files:
            # Validate file type
            if not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} is not an image"
                )

            # Read file content
            content = await file.read()

            # Validate image
            is_valid, error = ImageService.validate_image(content)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid image {file.filename}: {error}"
                )

            # Store for processing
            image_data.append((content, file.filename))

            logger.info(f"Received valid image: {file.filename} ({len(content)/1024:.1f}KB)")

        # Process all images (generate embeddings, upload to GCS, store in ChromaDB)
        logger.info(f"Processing {len(image_data)} images for user: {user_id}")

        results = await ImageService.process_multiple_images(
            images=image_data,
            user_id=user_id,
            metadata={"source": "onboarding"}
        )

        # Count successful uploads
        successful = sum(1 for r in results if "error" not in r)
        failed = len(results) - successful

        # Mark photo upload as complete in onboarding
        current_state = _onboarding_states.get(user_id)
        if current_state:
            current_state["collected_data"]["photos_uploaded"] = True
            current_state["collected_data"]["photo_count"] = successful
            current_state["collected_data"]["photo_details"] = results

        response = {
            "message": f"Successfully processed {successful} out of {len(files)} photos",
            "successful": successful,
            "failed": failed,
            "details": results
        }

        if failed > 0:
            response["warning"] = f"{failed} images failed to process"

        logger.info(f"Image processing complete: {successful} successful, {failed} failed")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading photos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload photos: {str(e)}"
        )
