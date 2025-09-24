"""
Recommendation service with HuggingFace embeddings
"""
import logging
import math
from typing import List, Dict, Any, Optional
from ..models.recommendation import RecommendationItem
from .redis_service import RedisService
from .huggingface_embedding_service import HuggingFaceEmbeddingService

logger = logging.getLogger(__name__)

class RecommendationService:
    """Service for generating recommendations using HuggingFace embeddings"""
    
    def __init__(self, redis_service: RedisService, huggingface_model: str = "all-minilm"):
        self.redis_service = redis_service
        self.huggingface_model = huggingface_model
        self.embedding_service: Optional[HuggingFaceEmbeddingService] = None
        self.item_embeddings: Dict[str, List[float]] = {}
        
    async def initialize_embeddings(self):
        """Initialize HuggingFace embeddings service"""
        try:
            logger.info(f"Initializing HuggingFace embeddings with model: {self.huggingface_model}")
            self.embedding_service = HuggingFaceEmbeddingService(self.huggingface_model)
            
            # Load embeddings from Redis if available
            all_embeddings = await self.redis_service.get_all_embeddings()
            if all_embeddings:
                logger.info(f"Loaded {len(all_embeddings)} embeddings from Redis")
                self.item_embeddings = {
                    item: data["embedding"] 
                    for item, data in all_embeddings.items()
                }
            else:
                logger.warning("No embeddings found in Redis. Embeddings need to be generated first.")
                
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace embeddings: {e}")
            raise
        
    async def initialize_data(self):
        """Initialize recommendation data from CSV"""
        # This will be implemented in the data processing pipeline
        pass
    
    async def get_order_recommendations(self, order_id: str, limit: int = 10) -> List[RecommendationItem]:
        """Get recommendations for a specific order"""
        try:
            # For now, return popular items as fallback
            # This will be enhanced with actual collaborative filtering
            return await self.get_popular_items(limit)
        except Exception as e:
            logger.error(f"Error getting order recommendations: {e}")
            return []
    
    async def get_similar_items(self, item_name: str, limit: int = 5) -> List[RecommendationItem]:
        """Find items similar to a given item using HuggingFace embeddings"""
        try:
            if not self.embedding_service:
                await self.initialize_embeddings()
            
            # Use HuggingFace embeddings for similarity
            similar_data = await self.redis_service.find_similar_items_by_embedding(item_name, limit)
            
            recommendations = []
            for item_data in similar_data:
                similar_item = item_data.get("item", "")
                similarity_score = item_data.get("similarity", 0.0)
                
                recommendations.append(RecommendationItem(
                    item_name=similar_item,
                    similarity_score=similarity_score,
                    reason=f"HuggingFace similarity: {similarity_score:.3f}",
                    popularity_rank=None
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting similar items with HuggingFace embeddings: {e}")
            return []
    
    async def get_basket_recommendations(self, items: List[str], limit: int = 10) -> List[RecommendationItem]:
        """Get recommendations for a basket of items using HuggingFace embeddings"""
        try:
            if not self.embedding_service:
                await self.initialize_embeddings()
            
            # Create a combined embedding for the basket
            basket_embedding = await self._create_basket_embedding(items)
            if not basket_embedding:
                # Fallback to popular items if basket embedding fails
                return await self.get_popular_items(limit)
            
            # Find items similar to the basket embedding
            similar_items = await self._find_items_similar_to_embedding(basket_embedding, limit + len(items))
            
            # Filter out items already in the basket
            basket_set = set(items)
            recommendations = [item for item in similar_items if item.item_name not in basket_set]
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting basket recommendations: {e}")
            return []
    
    async def get_popular_items(self, limit: int = 20) -> List[RecommendationItem]:
        """Get most frequently purchased items"""
        try:
            # Get popular items from Redis
            popular_data = await self.redis_service.get_popular_items(limit)
            
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
    
    async def _create_basket_embedding(self, items: List[str]) -> Optional[List[float]]:
        """Create a combined embedding for a basket of items"""
        try:
            if not items:
                return None
            
            # Get embeddings for all items in the basket
            item_embeddings = []
            for item in items:
                embedding_data = await self.redis_service.get_item_embedding(item)
                if embedding_data and embedding_data.get("embedding"):
                    item_embeddings.append(embedding_data["embedding"])
            
            if not item_embeddings:
                return None
            
            # Average the embeddings to create a basket embedding
            import numpy as np
            embeddings_array = np.array(item_embeddings)
            basket_embedding = np.mean(embeddings_array, axis=0)
            
            # Normalize the basket embedding
            basket_embedding = basket_embedding / np.linalg.norm(basket_embedding)
            
            return basket_embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error creating basket embedding: {e}")
            return None
    
    async def _find_items_similar_to_embedding(self, target_embedding: List[float], limit: int) -> List[RecommendationItem]:
        """Find items similar to a given embedding vector"""
        try:
            # Get all embeddings from Redis
            all_embeddings = await self.redis_service.get_all_embeddings()
            
            similarities = []
            for item_name, item_data in all_embeddings.items():
                item_embedding = item_data.get("embedding", [])
                if item_embedding:
                    similarity = self.calculate_cosine_similarity(target_embedding, item_embedding)
                    similarities.append((item_name, similarity))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            recommendations = []
            for item_name, similarity in similarities[:limit]:
                recommendations.append(RecommendationItem(
                    item_name=item_name,
                    similarity_score=similarity,
                    reason=f"Basket similarity: {similarity:.3f}",
                    popularity_rank=None
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error finding items similar to embedding: {e}")
            return []

    def calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            if len(vec1) != len(vec2):
                return 0.0
            
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(a * a for a in vec2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
