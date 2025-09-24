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
    embedding_type: str = Query("cooccurrence", description="Embedding type: 'cooccurrence' or 'huggingface'"),
    recommendation_service: RecommendationService = Depends(get_recommendation_service)
):
    """Find items similar to a given item using different embedding approaches"""
    try:
        # Use the embedding_type parameter to determine which approach to use
        if embedding_type == "huggingface":
            # Use HuggingFace embeddings
            similar_data = await recommendation_service.redis_service.find_similar_items_by_embedding(
                item_name, limit, embedding_type="huggingface"
            )
            
            recommendations = []
            for item_data in similar_data:
                recommendations.append(RecommendationItem(
                    item_name=item_data["item"],
                    similarity_score=item_data["similarity"],
                    reason=f"HuggingFace similarity: {item_data['similarity']:.3f}",
                    popularity_rank=None
                ))
        else:
            # Use co-occurrence based similarity (default)
            similar_data = await recommendation_service.redis_service.get_similar_items(item_name, limit)
            
            recommendations = []
            for item_data in similar_data:
                similar_item = item_data.get("item", "")
                cooccurrence = item_data.get("cooccurrence", 0)
                
                # Calculate similarity score based on co-occurrence frequency
                max_cooccurrence = 17951  # From our data analysis
                similarity_score = min(cooccurrence / max_cooccurrence, 1.0)
                
                recommendations.append(RecommendationItem(
                    item_name=similar_item,
                    similarity_score=similarity_score,
                    reason=f"Co-occurrence similarity ({cooccurrence} times)",
                    popularity_rank=None
                ))
        
        return RecommendationResponse(
            recommendations=recommendations,
            metadata={
                "item_name": item_name,
                "limit": limit,
                "embedding_type": embedding_type,
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

@router.get("/embeddings/{item_name}")
async def get_item_embedding(
    item_name: str,
    embedding_type: str = Query("cooccurrence", description="Embedding type: 'cooccurrence' or 'huggingface'"),
    redis_service: RedisService = Depends(get_redis_service)
):
    """Get vector embedding for a specific item"""
    try:
        embedding_data = await redis_service.get_item_embedding(item_name, embedding_type)
        if not embedding_data:
            raise HTTPException(status_code=404, detail=f"{embedding_type} embedding not found for item: {item_name}")
        
        return {
            "item_name": item_name,
            "embedding": embedding_data["embedding"],
            "embedding_dimension": embedding_data.get("embedding_dimension", len(embedding_data["embedding"])),
            "embedding_type": embedding_data.get("embedding_type", embedding_type),
            "metadata": embedding_data.get("metadata", {}),
            "last_updated": embedding_data.get("last_updated", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get {embedding_type} embedding for {item_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get {embedding_type} item embedding")
