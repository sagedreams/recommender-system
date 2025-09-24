"""
Redis service for vector operations and caching
"""
import json
import logging
from typing import List, Dict, Optional, Any
import redis.asyncio as redis
import pandas as pd
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
                "metadata": json.dumps(metadata or {}),
                "embedding_dimension": len(embedding),
                "last_updated": str(pd.Timestamp.now())
            }
            await self.redis_client.hset(key, mapping=data)
            logger.debug(f"Stored embedding for item: {item_name} (dim: {len(embedding)})")
        except Exception as e:
            logger.error(f"Failed to store embedding for {item_name}: {e}")
            raise
    
    async def get_item_embedding(self, item_name: str, embedding_type: str = "cooccurrence") -> Optional[Dict[str, Any]]:
        """Retrieve item embedding from Redis"""
        try:
            # Choose key pattern based on embedding type
            if embedding_type == "huggingface":
                key = f"hf:{item_name}"
            else:
                key = f"item:{item_name}"
            
            data = await self.redis_client.hgetall(key)
            if data:
                return {
                    "embedding": json.loads(data.get("embedding", "[]")),
                    "metadata": json.loads(data.get("metadata", "{}")),
                    "embedding_dimension": int(data.get("embedding_dimension", 0)),
                    "last_updated": data.get("last_updated", ""),
                    "embedding_type": embedding_type
                }
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve {embedding_type} embedding for {item_name}: {e}")
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
    
    async def bulk_store_embeddings(self, embeddings: Dict[str, List[float]], metadata: Dict[str, Dict[str, Any]] = None):
        """Store multiple item embeddings in Redis"""
        try:
            pipeline = self.redis_client.pipeline()
            
            for item_name, embedding in embeddings.items():
                # Use the key as provided (already includes prefix like hf:)
                key = item_name
                item_metadata = metadata.get(item_name, {}) if metadata else {}
                data = {
                    "embedding": json.dumps(embedding),
                    "metadata": json.dumps(item_metadata),
                    "embedding_dimension": len(embedding),
                    "last_updated": str(pd.Timestamp.now())
                }
                pipeline.hset(key, mapping=data)
            
            await pipeline.execute()
            logger.info(f"Stored embeddings for {len(embeddings)} items")
            
        except Exception as e:
            logger.error(f"Failed to bulk store embeddings: {e}")
            raise
    
    async def get_all_embeddings(self, embedding_type: str = "cooccurrence") -> Dict[str, Dict[str, Any]]:
        """Retrieve all item embeddings from Redis"""
        try:
            # Choose key pattern based on embedding type
            if embedding_type == "huggingface":
                key_pattern = "hf:*"
                key_prefix = "hf:"
            else:
                key_pattern = "item:*"
                key_prefix = "item:"
            
            # Get all keys matching the pattern
            keys = await self.redis_client.keys(key_pattern)
            embeddings = {}
            
            for key in keys:
                try:
                    item_name = key.replace(key_prefix, "")
                    # Check if key is a hash type
                    key_type = await self.redis_client.type(key)
                    if key_type != "hash":
                        logger.warning(f"Skipping key {key} - not a hash type: {key_type}")
                        continue
                    
                    data = await self.redis_client.hgetall(key)
                    if data and "embedding" in data:
                        embeddings[item_name] = {
                            "embedding": json.loads(data.get("embedding", "[]")),
                            "metadata": json.loads(data.get("metadata", "{}")),
                            "embedding_dimension": int(data.get("embedding_dimension", 0)),
                            "last_updated": data.get("last_updated", ""),
                            "embedding_type": embedding_type
                        }
                except Exception as key_error:
                    logger.warning(f"Error processing key {key}: {key_error}")
                    continue
            
            logger.info(f"Retrieved {len(embeddings)} {embedding_type} embeddings from Redis")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to retrieve all {embedding_type} embeddings: {e}")
            return {}
    
    async def find_similar_items_by_embedding(self, target_item: str, limit: int = 10, embedding_type: str = "cooccurrence") -> List[Dict[str, Any]]:
        """Find similar items using vector similarity"""
        try:
            # Get target item embedding
            target_data = await self.get_item_embedding(target_item, embedding_type)
            if not target_data:
                return []
            
            target_embedding = target_data["embedding"]
            
            # Get all embeddings of the same type
            all_embeddings = await self.get_all_embeddings(embedding_type)
            
            # Calculate similarities
            similarities = []
            for item_name, item_data in all_embeddings.items():
                if item_name != target_item:
                    similarity = self._calculate_cosine_similarity(target_embedding, item_data["embedding"])
                    similarities.append({
                        "item": item_name,
                        "similarity": similarity,
                        "metadata": item_data["metadata"],
                        "embedding_type": embedding_type
                    })
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar items for {target_item} using {embedding_type}: {e}")
            return []
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            if len(vec1) != len(vec2):
                return 0.0
            
            import numpy as np
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

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
