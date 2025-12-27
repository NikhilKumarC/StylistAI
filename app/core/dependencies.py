"""
FastAPI dependencies for authentication and authorization
Used to protect API endpoints and inject authenticated user context
"""

from typing import Optional, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_token_and_get_user

# Security scheme for extracting Bearer token from Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """
    Dependency to get current authenticated user from Firebase token

    Extracts the Bearer token from Authorization header,
    verifies it with Firebase, and returns user information.

    Usage in endpoints:
        @app.get("/protected")
        async def protected_route(user: Dict = Depends(get_current_user)):
            user_id = user["uid"]
            email = user["email"]
            ...

    Args:
        credentials: HTTP Bearer credentials from Authorization header

    Returns:
        Dictionary with user information (uid, email, name, etc.)

    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = verify_token_and_get_user(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    """
    Dependency to get current user and verify they are active

    Adds an additional check to ensure the user account is active.
    Can be extended to check email verification, banned status, etc.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Dictionary with user information if user is active

    Raises:
        HTTPException: 403 if user is not active
    """
    # Check if email is verified (optional - uncomment if you want to enforce)
    # if not current_user.get("email_verified"):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Email not verified. Please verify your email."
    #     )

    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[Dict]:
    """
    Dependency to optionally get authenticated user

    Returns user information if valid token is provided,
    otherwise returns None. Does not raise exceptions.

    Useful for endpoints that can work with or without authentication.

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        User dictionary if authenticated, None otherwise
    """
    if not credentials:
        return None

    token = credentials.credentials
    if not token:
        return None

    return verify_token_and_get_user(token)
