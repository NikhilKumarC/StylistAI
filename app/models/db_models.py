"""
SQLAlchemy Database Models
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class User(Base):
    """User table - stores Firebase UID and basic info"""
    __tablename__ = "users"

    uid = Column(String(128), primary_key=True, index=True)  # Firebase UID
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Onboarding status
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    onboarding_completed_at = Column(DateTime, nullable=True)

    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    outfits = relationship("Outfit", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class UserPreferences(Base):
    """User preferences table - stores style preferences from onboarding"""
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True)  # UUID
    user_uid = Column(String(128), ForeignKey("users.uid"), nullable=False, unique=True, index=True)

    # Style preferences (stored as JSON for flexibility)
    style_aesthetics = Column(JSON, nullable=True)  # ["minimalist", "modern"]
    colors = Column(JSON, nullable=True)  # ["navy", "grey", "white"]
    occasions = Column(JSON, nullable=True)  # ["casual", "work", "formal"]
    style_goals = Column(JSON, nullable=True)  # ["look professional"]

    # Single values
    fit_preferences = Column(String(50), nullable=True)  # "fitted"
    budget = Column(String(50), nullable=True)  # "mid-range"
    body_type = Column(String(50), nullable=True)  # "athletic"

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="preferences")

    def __repr__(self):
        return f"<UserPreferences for {self.user_uid}>"


class Outfit(Base):
    """Outfit images table - stores uploaded wardrobe images with URLs and metadata"""
    __tablename__ = "outfits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_uid = Column(String(128), ForeignKey("users.uid"), nullable=False, index=True)

    # Image identification
    image_id = Column(String(255), unique=True, nullable=False, index=True)  # ChromaDB ID
    filename = Column(String(500), nullable=False)  # Original filename

    # Storage locations
    gcs_url = Column(Text, nullable=True)  # Google Cloud Storage URL
    local_path = Column(Text, nullable=True)  # Local file path (fallback)

    # Image metadata
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)  # image/jpeg, image/png, etc.
    width = Column(Integer, nullable=True)  # Image width in pixels
    height = Column(Integer, nullable=True)  # Image height in pixels

    # Categorization
    tags = Column(JSON, nullable=True)  # ["casual", "work", "summer"]
    description = Column(Text, nullable=True)  # User-provided description
    occasion = Column(String(100), nullable=True)  # "work", "casual", "formal"
    season = Column(String(50), nullable=True)  # "spring", "summer", "fall", "winter"

    # AI-generated metadata (from CLIP/GPT-4)
    ai_description = Column(Text, nullable=True)  # AI-generated description
    ai_tags = Column(JSON, nullable=True)  # AI-detected tags
    dominant_colors = Column(JSON, nullable=True)  # ["navy", "white"]

    # Embedding reference (actual vector stored in ChromaDB)
    embedding_stored = Column(Boolean, default=False)  # Whether CLIP embedding exists
    embedding_dimensions = Column(Integer, nullable=True)  # Usually 512 for CLIP

    # Source tracking
    source = Column(String(50), nullable=True)  # "onboarding", "upload", "camera"

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationship
    user = relationship("User", back_populates="outfits")

    def __repr__(self):
        return f"<Outfit {self.filename} for {self.user_uid}>"

    @property
    def image_url(self):
        """Get the primary image URL (prefer GCS, fallback to local)"""
        return self.gcs_url or self.local_path

    @property
    def all_tags(self):
        """Get combined user and AI tags"""
        user_tags = self.tags or []
        ai_tags = self.ai_tags or []
        return list(set(user_tags + ai_tags))
