"""
Pydantic models for recommendation API
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class RecommendationItem(BaseModel):
    """Individual recommendation item"""
    item_name: str = Field(..., description="Name of the recommended item")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")
    reason: str = Field(..., description="Reason for recommendation")
    popularity_rank: Optional[int] = Field(None, description="Popularity rank of the item")

class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    recommendations: List[RecommendationItem] = Field(..., description="List of recommendations")
    metadata: dict = Field(..., description="Response metadata")

class RecommendationRequest(BaseModel):
    """Request model for basket recommendations"""
    items: List[str] = Field(..., min_items=1, description="List of items in the basket")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of recommendations")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    redis_connected: bool = Field(..., description="Redis connection status")
    timestamp: str = Field(..., description="Response timestamp")
