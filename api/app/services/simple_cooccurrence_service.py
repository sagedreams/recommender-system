"""
Simple co-occurrence service for basic collaborative filtering
"""
import logging
import math
from typing import List, Dict, Any, Optional
from ..models.recommendation import RecommendationItem
from .redis_service import RedisService

logger = logging.getLogger(__name__)

class SimpleCooccurrenceService:
    """Service for generating recommendations using simple co-occurrence counting"""
    
    def __init__(self, redis_service: RedisService):
        self.redis_service = redis_service
        
    async def get_similar_items(self, item_name: str, limit: int = 5) -> List[RecommendationItem]:
        """Find items similar to a given item based on co-purchase patterns"""
        try:
            # Get similar items from Redis co-occurrence data
            similar_data = await self.redis_service.get_similar_items_simple(item_name, limit)
            
            recommendations = []
            for i, item_data in enumerate(similar_data):
                similar_item = item_data.get("item", "")
                cooccurrence = item_data.get("cooccurrence", 0)
                
                # Calculate similarity score based on co-occurrence frequency
                # Normalize based on typical co-occurrence values
                max_cooccurrence = 17951  # From our data analysis (PID + Cal Kit)
                similarity_score = min(cooccurrence / max_cooccurrence, 1.0)
                
                recommendations.append(RecommendationItem(
                    item_name=similar_item,
                    similarity_score=similarity_score,
                    reason=f"Co-occurrence similarity ({cooccurrence} times)",
                    popularity_rank=None
                ))
            
            return recommendations
        except Exception as e:
            logger.error(f"Error getting similar items: {e}")
            return []
    
    async def get_popular_items(self, limit: int = 20) -> List[RecommendationItem]:
        """Get most frequently purchased items"""
        try:
            # Get popular items from Redis
            popular_data = await self.redis_service.get_popular_items_simple(limit)
            
            recommendations = []
            for i, item_data in enumerate(popular_data):
                item_name = item_data.get("item", "")
                frequency = item_data.get("frequency", 0)
                
                # Calculate similarity score based on frequency (normalized)
                max_frequency = 30245  # From our data analysis
                similarity_score = min(frequency / max_frequency, 1.0)
                
                recommendations.append(RecommendationItem(
                    item_name=item_name,
                    similarity_score=similarity_score,
                    reason=f"Popular item (purchased {frequency} times)",
                    popularity_rank=i + 1
                ))
            
            return recommendations
        except Exception as e:
            logger.error(f"Error getting popular items: {e}")
            return []
    
    async def get_basket_recommendations(self, items: List[str], limit: int = 10) -> List[RecommendationItem]:
        """Get recommendations for a basket of items using simple co-occurrence"""
        try:
            # For now, return popular items as fallback
            # This could be enhanced with basket-based co-occurrence analysis
            popular_items = await self.get_popular_items(limit + len(items))
            # Filter out items already in the basket
            basket_set = set(items)
            recommendations = [item for item in popular_items if item.item_name not in basket_set]
            return recommendations[:limit]
        except Exception as e:
            logger.error(f"Error getting basket recommendations: {e}")
            return []
