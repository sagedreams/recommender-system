"""
Recommendation router with basic endpoints
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from ..models.recommendation import (
    RecommendationResponse, 
    RecommendationRequest, 
    RecommendationItem
)
from ..services.redis_service import RedisService
from ..services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_redis_service() -> RedisService:
    """Dependency to get Redis service"""
    from ..main import app
    return app.state.redis

async def get_recommendation_service(redis_service: RedisService = Depends(get_redis_service)) -> RecommendationService:
    """Dependency to get recommendation service"""
    return RecommendationService(redis_service)

@router.get("/recommendations/{order_id}", response_model=RecommendationResponse)
async def get_order_recommendations(
    order_id: str,
    limit: int = Query(10, ge=1, le=50),
    recommendation_service: RecommendationService = Depends(get_recommendation_service)
):
    """Get recommendations for a specific order"""
    try:
        recommendations = await recommendation_service.get_order_recommendations(order_id, limit)
        return RecommendationResponse(
            recommendations=recommendations,
            metadata={
                "order_id": order_id,
                "limit": limit,
                "total_recommendations": len(recommendations)
            }
        )
    except Exception as e:
        logger.error(f"Failed to get recommendations for order {order_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@router.get("/similar-items/{item_name}", response_model=RecommendationResponse)
async def get_similar_items(
    item_name: str,
    limit: int = Query(5, ge=1, le=20),
    recommendation_service: RecommendationService = Depends(get_recommendation_service)
):
    """Find items similar to a given item"""
    try:
        recommendations = await recommendation_service.get_similar_items(item_name, limit)
        return RecommendationResponse(
            recommendations=recommendations,
            metadata={
                "item_name": item_name,
                "limit": limit,
                "total_recommendations": len(recommendations)
            }
        )
    except Exception as e:
        logger.error(f"Failed to get similar items for {item_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get similar items")

@router.post("/basket-recommendations", response_model=RecommendationResponse)
async def get_basket_recommendations(
    request: RecommendationRequest,
    recommendation_service: RecommendationService = Depends(get_recommendation_service)
):
    """Get real-time recommendations for a basket of items"""
    try:
        recommendations = await recommendation_service.get_basket_recommendations(
            request.items, 
            request.limit
        )
        return RecommendationResponse(
            recommendations=recommendations,
            metadata={
                "basket_items": request.items,
                "limit": request.limit,
                "total_recommendations": len(recommendations)
            }
        )
    except Exception as e:
        logger.error(f"Failed to get basket recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get basket recommendations")

@router.get("/popular-items", response_model=RecommendationResponse)
async def get_popular_items(
    limit: int = Query(20, ge=1, le=100),
    recommendation_service: RecommendationService = Depends(get_recommendation_service)
):
    """Get most frequently purchased items"""
    try:
        recommendations = await recommendation_service.get_popular_items(limit)
        return RecommendationResponse(
            recommendations=recommendations,
            metadata={
                "limit": limit,
                "total_recommendations": len(recommendations)
            }
        )
    except Exception as e:
        logger.error(f"Failed to get popular items: {e}")
        raise HTTPException(status_code=500, detail="Failed to get popular items")
