"""
User service with PostgreSQL database backend
"""

from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import logging

from app.models.db_models import User, UserPreferences
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user preferences and profile data using PostgreSQL"""

    @staticmethod
    def ensure_user_exists(uid: str, email: Optional[str] = None) -> bool:
        """
        Ensure user record exists in PostgreSQL
        Creates user if doesn't exist (useful for image uploads during onboarding)

        Args:
            uid: Firebase user UID
            email: User email (optional)

        Returns:
            True if user exists or was created
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.uid == uid).first()
            if not user:
                user = User(
                    uid=uid,
                    email=email or f"{uid}@temp.com",
                    onboarding_completed=False
                )
                db.add(user)
                db.commit()
                logger.info(f"Created user record for {uid}")
            return True
        except Exception as e:
            logger.error(f"Error ensuring user exists for {uid}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    @staticmethod
    def get_user_preferences(uid: str) -> Optional[Dict]:
        """
        Get user's style preferences

        Args:
            uid: Firebase user UID

        Returns:
            User preferences dictionary if exists, None otherwise
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.uid == uid).first()
            if not user or not user.preferences:
                return None

            prefs = user.preferences
            return {
                "style_aesthetics": prefs.style_aesthetics,
                "colors": prefs.colors,
                "occasions": prefs.occasions,
                "style_goals": prefs.style_goals,
                "fit_preferences": prefs.fit_preferences,
                "budget": prefs.budget,
                "body_type": prefs.body_type,
                "onboarding_completed": user.onboarding_completed
            }
        except Exception as e:
            logger.error(f"Error getting preferences for {uid}: {e}")
            return None
        finally:
            db.close()

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
        db = SessionLocal()
        try:
            # Get or create user
            user = db.query(User).filter(User.uid == uid).first()
            if not user:
                # Create user if doesn't exist
                user = User(
                    uid=uid,
                    email=preferences.get("email", f"{uid}@temp.com"),
                    onboarding_completed=preferences.get("onboarding_completed", True),
                    onboarding_completed_at=datetime.utcnow() if preferences.get("onboarding_completed") else None
                )
                db.add(user)
            else:
                # Update onboarding status
                if preferences.get("onboarding_completed"):
                    user.onboarding_completed = True
                    if not user.onboarding_completed_at:
                        user.onboarding_completed_at = datetime.utcnow()

            # Get or create preferences
            user_prefs = db.query(UserPreferences).filter(UserPreferences.user_uid == uid).first()
            if not user_prefs:
                user_prefs = UserPreferences(
                    id=str(uuid.uuid4()),
                    user_uid=uid,
                    style_aesthetics=preferences.get("style_aesthetics"),
                    colors=preferences.get("colors"),
                    occasions=preferences.get("occasions"),
                    style_goals=preferences.get("style_goals"),
                    fit_preferences=preferences.get("fit_preferences"),
                    budget=preferences.get("budget"),
                    body_type=preferences.get("body_type")
                )
                db.add(user_prefs)
            else:
                # Update existing preferences
                user_prefs.style_aesthetics = preferences.get("style_aesthetics", user_prefs.style_aesthetics)
                user_prefs.colors = preferences.get("colors", user_prefs.colors)
                user_prefs.occasions = preferences.get("occasions", user_prefs.occasions)
                user_prefs.style_goals = preferences.get("style_goals", user_prefs.style_goals)
                user_prefs.fit_preferences = preferences.get("fit_preferences", user_prefs.fit_preferences)
                user_prefs.budget = preferences.get("budget", user_prefs.budget)
                user_prefs.body_type = preferences.get("body_type", user_prefs.body_type)
                user_prefs.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(user)
            logger.info(f"Saved preferences for user: {uid}")

            return {
                "uid": uid,
                "style_aesthetics": user_prefs.style_aesthetics,
                "colors": user_prefs.colors,
                "occasions": user_prefs.occasions,
                "style_goals": user_prefs.style_goals,
                "fit_preferences": user_prefs.fit_preferences,
                "budget": user_prefs.budget,
                "body_type": user_prefs.body_type,
                "onboarding_completed": user.onboarding_completed
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving preferences for {uid}: {e}")
            raise
        finally:
            db.close()

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
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.uid == uid).first()
            if not user:
                user = User(uid=uid, email=email, name=name)
                db.add(user)
                logger.info(f"Created new user: {email}")
            else:
                user.email = email
                user.name = name
                user.updated_at = datetime.utcnow()
                logger.info(f"Updated user: {email}")

            db.commit()
            db.refresh(user)

            return {
                "uid": user.uid,
                "email": user.email,
                "name": user.name,
                "onboarding_completed": user.onboarding_completed,
                "created_at": user.created_at.isoformat()
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating/updating user {email}: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def get_user_profile(uid: str) -> Optional[Dict]:
        """
        Get complete user profile including preferences

        Args:
            uid: Firebase user UID

        Returns:
            Complete user profile dictionary if exists, None otherwise
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.uid == uid).first()
            if not user:
                return None

            profile = {
                "uid": user.uid,
                "email": user.email,
                "name": user.name,
                "onboarding_completed": user.onboarding_completed,
                "created_at": user.created_at.isoformat(),
                "preferences": None
            }

            if user.preferences:
                prefs = user.preferences
                profile["preferences"] = {
                    "style_aesthetics": prefs.style_aesthetics,
                    "colors": prefs.colors,
                    "occasions": prefs.occasions,
                    "style_goals": prefs.style_goals,
                    "fit_preferences": prefs.fit_preferences,
                    "budget": prefs.budget,
                    "body_type": prefs.body_type
                }

            return profile
        except Exception as e:
            logger.error(f"Error getting profile for {uid}: {e}")
            return None
        finally:
            db.close()

    @staticmethod
    def user_exists(uid: str) -> bool:
        """
        Check if user profile exists

        Args:
            uid: Firebase user UID

        Returns:
            True if user exists, False otherwise
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.uid == uid).first()
            return user is not None
        except Exception as e:
            logger.error(f"Error checking user existence {uid}: {e}")
            return False
        finally:
            db.close()


# Singleton instance
user_service = UserService()
