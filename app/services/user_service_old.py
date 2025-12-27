"""
User service for managing user preferences and profile data
Authentication is handled by Firebase, this service manages additional user data
"""

from typing import Optional, Dict
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

# In-memory storage for now (replace with database later)
# Key: Firebase UID, Value: User preferences dict
_user_preferences: Dict[str, Dict] = {}


class UserService:
    """Service for managing user preferences and profile data"""

    @staticmethod
    def create_or_update_user_profile(uid: str, email: str, name: Optional[str] = None) -> Dict:
        """
        Create or update user profile when they first authenticate

        Args:
            uid: Firebase user UID
            email: User's email
            name: Optional display name

        Returns:
            User profile dictionary
        """
        if uid not in _user_preferences:
            _user_preferences[uid] = {
                "uid": uid,
                "email": email,
                "name": name,
                "created_at": datetime.utcnow().isoformat(),
                "preferences": None,
            }
            logger.info(f"Created new user profile for: {email}")
        else:
            _user_preferences[uid]["email"] = email
            _user_preferences[uid]["name"] = name
            logger.info(f"Updated user profile for: {email}")

        return _user_preferences[uid]

    @staticmethod
    def get_user_preferences(uid: str) -> Optional[Dict]:
        """
        Get user's style preferences

        Args:
            uid: Firebase user UID

        Returns:
            User preferences dictionary if exists, None otherwise
        """
        user_data = _user_preferences.get(uid)
        if not user_data:
            return None

        return user_data.get("preferences")

    @staticmethod
    def save_user_preferences(uid: str, preferences: Dict) -> Dict:
        """
        Save or update user's style preferences

        Args:
            uid: Firebase user UID
            preferences: Style preferences dictionary

        Returns:
            Updated user preferences
        """
        if uid not in _user_preferences:
            _user_preferences[uid] = {
                "uid": uid,
                "created_at": datetime.utcnow().isoformat(),
            }

        _user_preferences[uid]["preferences"] = preferences
        _user_preferences[uid]["preferences_updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"Saved preferences for user: {uid}")
        return _user_preferences[uid]

    @staticmethod
    def get_user_profile(uid: str) -> Optional[Dict]:
        """
        Get complete user profile including preferences

        Args:
            uid: Firebase user UID

        Returns:
            Complete user profile dictionary if exists, None otherwise
        """
        return _user_preferences.get(uid)

    @staticmethod
    def user_exists(uid: str) -> bool:
        """
        Check if user profile exists

        Args:
            uid: Firebase user UID

        Returns:
            True if user exists, False otherwise
        """
        return uid in _user_preferences


# Singleton instance
user_service = UserService()
