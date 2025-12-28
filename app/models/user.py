"""
User data models and schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration"""

    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response (without password)"""

    id: str
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""

    user_id: Optional[str] = None
    email: Optional[str] = None


class StylePreferences(BaseModel):
    """User style preferences for onboarding"""

    occasions: List[str] = Field(
        ...,
        description="Occasions user dresses for (e.g., casual, business, formal)",
        examples=[["casual", "business_casual", "formal"]],
    )
    fit_preferences: str = Field(
        ...,
        description="Preferred fit style",
        examples=["fitted", "relaxed", "oversized"],
    )
    budget: str = Field(
        ..., description="Budget range", examples=["budget", "mid-range", "luxury"]
    )
    style_aesthetics: List[str] = Field(
        ...,
        description="Style aesthetics",
        examples=[["minimalist", "modern", "classic", "streetwear"]],
    )
    colors: List[str] = Field(
        ...,
        description="Preferred colors",
        examples=[["navy", "grey", "white", "black"]],
    )
    body_type: Optional[str] = Field(
        None, description="Body type (optional)", examples=["athletic", "slim", "curvy"]
    )
    style_goals: Optional[str] = Field(
        None,
        description="What user wants to achieve",
        examples=["build confidence", "dress professionally"],
    )


class UserPreferencesResponse(BaseModel):
    """Response schema for user preferences"""

    user_id: str
    preferences: StylePreferences
    updated_at: datetime

    class Config:
        from_attributes = True
