"""
Firebase Authentication utilities
Handles Firebase Admin SDK initialization and token verification
"""

import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional, Dict
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Global Firebase app instance
_firebase_app: Optional[firebase_admin.App] = None


def initialize_firebase() -> None:
    """
    Initialize Firebase Admin SDK with service account credentials
    This should be called once during application startup
    """
    global _firebase_app

    if _firebase_app is not None:
        logger.info("Firebase already initialized")
        return

    try:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        _firebase_app = firebase_admin.initialize_app(cred, {
            'projectId': settings.FIREBASE_PROJECT_ID,
        })
        logger.info(f"Firebase initialized successfully for project: {settings.FIREBASE_PROJECT_ID}")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        raise


def verify_firebase_token(id_token: str) -> Optional[Dict]:
    """
    Verify a Firebase ID token and return decoded claims

    Args:
        id_token: Firebase ID token from client

    Returns:
        Decoded token containing user information if valid, None otherwise

    Token contains:
        - uid: User's Firebase UID
        - email: User's email address
        - name: User's display name (if set)
        - picture: User's profile picture URL (if set)
        - email_verified: Whether email is verified
        - auth_time: Time of authentication
        - exp: Token expiration time
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except firebase_admin.auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase ID token")
        return None
    except firebase_admin.auth.ExpiredIdTokenError:
        logger.warning("Expired Firebase ID token")
        return None
    except firebase_admin.auth.RevokedIdTokenError:
        logger.warning("Revoked Firebase ID token")
        return None
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {str(e)}")
        return None


def get_user_by_uid(uid: str) -> Optional[auth.UserRecord]:
    """
    Get Firebase user record by UID

    Args:
        uid: Firebase user UID

    Returns:
        UserRecord if user exists, None otherwise
    """
    try:
        user = auth.get_user(uid)
        return user
    except firebase_admin.auth.UserNotFoundError:
        logger.warning(f"User not found: {uid}")
        return None
    except Exception as e:
        logger.error(f"Error fetching user: {str(e)}")
        return None


def get_user_by_email(email: str) -> Optional[auth.UserRecord]:
    """
    Get Firebase user record by email

    Args:
        email: User's email address

    Returns:
        UserRecord if user exists, None otherwise
    """
    try:
        user = auth.get_user_by_email(email)
        return user
    except firebase_admin.auth.UserNotFoundError:
        logger.warning(f"User not found with email: {email}")
        return None
    except Exception as e:
        logger.error(f"Error fetching user by email: {str(e)}")
        return None


def verify_token_and_get_user(id_token: str) -> Optional[Dict]:
    """
    Verify token and return user information in a standardized format

    Args:
        id_token: Firebase ID token

    Returns:
        Dictionary with user information if valid, None otherwise
    """
    decoded_token = verify_firebase_token(id_token)

    if not decoded_token:
        return None

    return {
        "uid": decoded_token.get("uid"),
        "email": decoded_token.get("email"),
        "name": decoded_token.get("name"),
        "email_verified": decoded_token.get("email_verified", False),
        "picture": decoded_token.get("picture"),
    }
