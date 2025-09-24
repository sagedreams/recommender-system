"""
Redis service for vector operations and caching
"""
import json
import logging
from typing import List, Dict, Optional, Any
import redis.asyncio as redis
from ..utils.config import get_settings

logger = logging.getLogger(__name__)

class RedisService:
    """Redis service for vector database operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                password=self.settings.redis_password,
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def set_item_embedding(self, item_name: str, embedding: List[float], metadata: Dict[str, Any] = None):
        """Store item embedding in Redis"""
        try:
            key = f"item:{item_name}"
            data = {
                "embedding": json.dumps(embedding),
                "metadata": json.dumps(metadata or {})
            }
            await self.redis_client.hset(key, mapping=data)
            logger.debug(f"Stored embedding for item: {item_name}")
        except Exception as e:
            logger.error(f"Failed to store embedding for {item_name}: {e}")
            raise
    
    async def get_item_embedding(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve item embedding from Redis"""
        try:
            key = f"item:{item_name}"
            data = await self.redis_client.hgetall(key)
            if data:
                return {
                    "embedding": json.loads(data.get("embedding", "[]")),
                    "metadata": json.loads(data.get("metadata", "{}"))
                }
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve embedding for {item_name}: {e}")
            return None
    
    async def set_recommendation_cache(self, cache_key: str, recommendations: List[Dict[str, Any]]):
        """Cache recommendations"""
        try:
            key = f"cache:recommendations:{cache_key}"
            data = json.dumps(recommendations)
            await self.redis_client.setex(
                key, 
                self.settings.cache_ttl_seconds, 
                data
            )
            logger.debug(f"Cached recommendations for key: {cache_key}")
        except Exception as e:
            logger.error(f"Failed to cache recommendations: {e}")
    
    async def get_recommendation_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached recommendations"""
        try:
            key = f"cache:recommendations:{cache_key}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve cached recommendations: {e}")
            return None
    
    async def set_item_stats(self, item_name: str, stats: Dict[str, Any]):
        """Store item statistics"""
        try:
            key = f"stats:item:{item_name}"
            data = json.dumps(stats)
            await self.redis_client.set(key, data)
            logger.debug(f"Stored stats for item: {item_name}")
        except Exception as e:
            logger.error(f"Failed to store stats for {item_name}: {e}")
    
    async def get_item_stats(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve item statistics"""
        try:
            key = f"stats:item:{item_name}"
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve stats for {item_name}: {e}")
            return None
    
    async def get_popular_items(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve popular items from Redis"""
        try:
            data = await self.redis_client.get("popular_items")
            if data:
                popular_data = eval(data)  # Simple eval for stored dict
                items = popular_data.get("items", [])
                return items[:limit]
            return []
        except Exception as e:
            logger.error(f"Failed to retrieve popular items: {e}")
            return []
    
    async def get_similar_items(self, item_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve similar items from co-occurrence data"""
        try:
            key = f"cooccurrence:{item_name}"
            data = await self.redis_client.get(key)
            if data:
                cooccurrence_data = eval(data)  # Simple eval for stored dict
                similar_items = cooccurrence_data.get("similar_items", [])
                return similar_items[:limit]
            return []
        except Exception as e:
            logger.error(f"Failed to retrieve similar items for {item_name}: {e}")
            return []
    
    async def get_order_items(self, order_id: str) -> List[str]:
        """Retrieve items for a specific order"""
        try:
            key = f"order:{order_id}"
            data = await self.redis_client.get(key)
            if data:
                order_data = eval(data)  # Simple eval for stored dict
                return order_data.get("items", [])
            return []
        except Exception as e:
            logger.error(f"Failed to retrieve order items for {order_id}: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check Redis connection health"""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            return False
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
