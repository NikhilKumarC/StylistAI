"""
Authentication API endpoints
Works with Firebase Authentication on the frontend
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from app.core.dependencies import get_current_user, get_current_active_user
from app.services.user_service import user_service
from app.models.user import UserResponse, StylePreferences, UserPreferencesResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user),
):
    """
    Get current authenticated user's information

    This endpoint is called after Firebase authentication to sync user data
    with the backend and create a user profile if it doesn't exist.

    Headers:
        Authorization: Bearer <firebase_id_token>

    Returns:
        User information including uid, email, name
    """
    uid = current_user["uid"]
    email = current_user["email"]
    name = current_user.get("name")

    # Create or update user profile
    user_profile = user_service.create_or_update_user_profile(
        uid=uid, email=email, name=name
    )

    return {
        "id": uid,
        "email": email,
        "name": name or "",
        "created_at": user_profile.get("created_at"),
        "is_active": True,
    }


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: Dict = Depends(get_current_active_user),
):
    """
    Get user's style preferences

    Headers:
        Authorization: Bearer <firebase_id_token>

    Returns:
        User's saved style preferences or 404 if not set
    """
    uid = current_user["uid"]
    preferences = user_service.get_user_preferences(uid)

    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User preferences not found. Please complete onboarding.",
        )

    return {
        "user_id": uid,
        "preferences": preferences,
        "updated_at": user_service.get_user_profile(uid).get(
            "preferences_updated_at"
        ),
    }


@router.post("/preferences", response_model=UserPreferencesResponse)
async def save_user_preferences(
    preferences: StylePreferences,
    current_user: Dict = Depends(get_current_active_user),
):
    """
    Save or update user's style preferences (onboarding)

    Headers:
        Authorization: Bearer <firebase_id_token>

    Body:
        Style preferences including occasions, fit, budget, aesthetics, colors, etc.

    Returns:
        Saved preferences with timestamp
    """
    uid = current_user["uid"]

    # Convert Pydantic model to dict
    preferences_dict = preferences.model_dump()

    # Save preferences
    user_profile = user_service.save_user_preferences(uid, preferences_dict)

    return {
        "user_id": uid,
        "preferences": preferences_dict,
        "updated_at": user_profile.get("preferences_updated_at"),
    }


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences: StylePreferences,
    current_user: Dict = Depends(get_current_active_user),
):
    """
    Update user's style preferences

    Same as POST /preferences but semantically indicates an update.

    Headers:
        Authorization: Bearer <firebase_id_token>

    Body:
        Updated style preferences

    Returns:
        Updated preferences with timestamp
    """
    # Reuse the save logic (upsert behavior)
    return await save_user_preferences(preferences, current_user)


@router.get("/profile")
async def get_user_profile(
    current_user: Dict = Depends(get_current_active_user),
):
    """
    Get complete user profile including preferences

    Headers:
        Authorization: Bearer <firebase_id_token>

    Returns:
        Complete user profile with preferences and metadata
    """
    uid = current_user["uid"]
    profile = user_service.get_user_profile(uid)

    if not profile:
        # Create profile if it doesn't exist
        profile = user_service.create_or_update_user_profile(
            uid=uid,
            email=current_user["email"],
            name=current_user.get("name"),
        )

    return {
        "uid": uid,
        "email": current_user["email"],
        "name": current_user.get("name"),
        "email_verified": current_user.get("email_verified", False),
        "picture": current_user.get("picture"),
        "preferences": profile.get("preferences"),
        "created_at": profile.get("created_at"),
        "preferences_updated_at": profile.get("preferences_updated_at"),
    }
