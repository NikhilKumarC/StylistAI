"""
Outfit data models and schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class OutfitBase(BaseModel):
    """Base outfit schema"""

    description: Optional[str] = Field(
        None, max_length=500, description="Optional description of the outfit"
    )
    occasion: Optional[str] = Field(
        None, description="Occasion for the outfit", examples=["casual", "business"]
    )
    tags: Optional[List[str]] = Field(
        default_factory=list, description="Tags for categorizing the outfit"
    )


class OutfitCreate(OutfitBase):
    """Schema for creating a new outfit"""

    pass


class OutfitUploadResponse(BaseModel):
    """Response after uploading an outfit"""

    outfit_id: str
    message: str
    image_url: str
    uploaded_at: datetime


class OutfitResponse(OutfitBase):
    """Schema for outfit response"""

    id: str
    user_id: str
    image_url: str
    gcs_path: str
    embedding_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OutfitListResponse(BaseModel):
    """Schema for listing multiple outfits"""

    outfits: List[OutfitResponse]
    total: int
    page: int = 1
    page_size: int = 20


class OutfitUpdate(BaseModel):
    """Schema for updating outfit details"""

    description: Optional[str] = None
    occasion: Optional[str] = None
    tags: Optional[List[str]] = None


class OutfitFeedback(BaseModel):
    """Schema for outfit feedback"""

    outfit_id: str
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = Field(
        None, max_length=1000, description="Detailed feedback"
    )
    what_worked: Optional[List[str]] = Field(
        default_factory=list, description="Aspects that worked well"
    )
    what_didnt_work: Optional[List[str]] = Field(
        default_factory=list, description="Aspects that didn't work"
    )
