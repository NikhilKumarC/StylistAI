"""
Styling recommendation data models and schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class StylingQueryRequest(BaseModel):
    """Request schema for styling advice query"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User's styling question or request",
        examples=["How can I improve this outfit for a date night?"],
    )
    outfit_id: Optional[str] = Field(
        None, description="Optional outfit ID to analyze"
    )
    occasion: Optional[str] = Field(
        None, description="Occasion context", examples=["date", "work", "party"]
    )
    consider_trends: bool = Field(
        True, description="Whether to include current fashion trends"
    )


class StylingAnalysisRequest(BaseModel):
    """Request schema for analyzing uploaded image"""

    query: Optional[str] = Field(
        None, description="Optional specific question about the outfit"
    )
    occasion: Optional[str] = Field(None, description="Occasion for the outfit")
    consider_trends: bool = Field(
        True, description="Whether to include trend analysis"
    )


class TrendInsight(BaseModel):
    """Fashion trend insight"""

    trend_name: str = Field(..., description="Name of the trend")
    description: str = Field(..., description="Description of the trend")
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="How relevant to user (0-1)"
    )
    application: str = Field(
        ..., description="How to apply this trend to the outfit"
    )


class OutfitAnalysis(BaseModel):
    """Detailed outfit analysis"""

    overall_rating: float = Field(..., ge=0.0, le=10.0, description="Rating out of 10")
    strengths: List[str] = Field(
        ..., description="What works well in the outfit"
    )
    areas_for_improvement: List[str] = Field(
        ..., description="What could be improved"
    )
    color_analysis: str = Field(..., description="Analysis of color choices")
    fit_analysis: str = Field(..., description="Analysis of fit and silhouette")
    occasion_appropriateness: str = Field(
        ..., description="How appropriate for the occasion"
    )


class StylingRecommendation(BaseModel):
    """Individual styling recommendation"""

    category: str = Field(
        ...,
        description="Category of recommendation",
        examples=["accessory", "layer", "swap", "color"],
    )
    suggestion: str = Field(..., description="The specific suggestion")
    reasoning: str = Field(..., description="Why this recommendation makes sense")
    priority: str = Field(
        ..., description="Priority level", examples=["high", "medium", "low"]
    )


class StylingResponse(BaseModel):
    """Complete styling advice response"""

    query: str
    outfit_id: Optional[str] = None
    analysis: OutfitAnalysis
    recommendations: List[StylingRecommendation]
    trend_insights: List[TrendInsight] = Field(
        default_factory=list, description="Current trend insights"
    )
    similar_past_outfits: List[str] = Field(
        default_factory=list,
        description="IDs of similar outfits from user's history",
    )
    personalization_note: str = Field(
        ..., description="Note about how this advice is personalized"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class StylingFeedback(BaseModel):
    """Feedback on styling advice"""

    styling_session_id: str
    helpful: bool = Field(..., description="Was the advice helpful?")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = Field(None, max_length=1000)
    implemented_suggestions: Optional[List[str]] = Field(
        default_factory=list, description="Which suggestions were implemented"
    )


class TrendQuery(BaseModel):
    """Query for current fashion trends"""

    category: Optional[str] = Field(
        None, description="Category to focus on", examples=["tops", "bottoms", "shoes"]
    )
    season: Optional[str] = Field(
        None,
        description="Season to consider",
        examples=["spring", "summer", "fall", "winter"],
    )
    style: Optional[str] = Field(
        None, description="Style aesthetic", examples=["minimalist", "streetwear"]
    )


class TrendResponse(BaseModel):
    """Response with current fashion trends"""

    trends: List[TrendInsight]
    season: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    sources: List[str] = Field(
        default_factory=list, description="Sources of trend information"
    )
