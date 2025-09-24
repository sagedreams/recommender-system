#!/usr/bin/env python3
"""
Test script for HuggingFace-only recommendation service
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add the api directory to the path
sys.path.append(str(Path(__file__).parent / "api"))

from api.app.services.redis_service import RedisService
from api.app.services.recommendation_service import RecommendationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_huggingface_recommendation_service():
    """Test the HuggingFace-only recommendation service"""
    try:
        logger.info("="*60)
        logger.info("TESTING HUGGINGFACE-ONLY RECOMMENDATION SERVICE")
        logger.info("="*60)
        
        # Initialize Redis service
        redis_service = RedisService()
        await redis_service.initialize()
        
        # Initialize recommendation service with HuggingFace embeddings
        recommendation_service = RecommendationService(
            redis_service=redis_service,
            huggingface_model="all-minilm"
        )
        
        # Initialize embeddings
        logger.info("Initializing HuggingFace embeddings...")
        await recommendation_service.initialize_embeddings()
        
        # Test 1: Get similar items
        logger.info("\n" + "="*40)
        logger.info("TEST 1: Similar Items")
        logger.info("="*40)
        
        test_items = ["PID", "Temperature Sensor", "Pressure Gauge"]
        for test_item in test_items:
            logger.info(f"\nFinding items similar to '{test_item}':")
            similar_items = await recommendation_service.get_similar_items(test_item, limit=3)
            
            if similar_items:
                for item in similar_items:
                    logger.info(f"  {item.item_name}: {item.similarity_score:.3f} - {item.reason}")
            else:
                logger.warning(f"  No similar items found for '{test_item}'")
        
        # Test 2: Basket recommendations
        logger.info("\n" + "="*40)
        logger.info("TEST 2: Basket Recommendations")
        logger.info("="*40)
        
        test_baskets = [
            ["PID", "Temperature Sensor"],
            ["Pressure Gauge", "Flow Meter"],
            ["Calibration Kit", "Data Logger"]
        ]
        
        for basket in test_baskets:
            logger.info(f"\nBasket: {basket}")
            recommendations = await recommendation_service.get_basket_recommendations(basket, limit=3)
            
            if recommendations:
                for rec in recommendations:
                    logger.info(f"  {rec.item_name}: {rec.similarity_score:.3f} - {rec.reason}")
            else:
                logger.warning(f"  No recommendations found for basket: {basket}")
        
        # Test 3: Popular items
        logger.info("\n" + "="*40)
        logger.info("TEST 3: Popular Items")
        logger.info("="*40)
        
        popular_items = await recommendation_service.get_popular_items(limit=5)
        if popular_items:
            logger.info("Top 5 popular items:")
            for item in popular_items:
                logger.info(f"  {item.item_name}: {item.similarity_score:.3f} - {item.reason}")
        else:
            logger.warning("No popular items found")
        
        # Test 4: Order recommendations
        logger.info("\n" + "="*40)
        logger.info("TEST 4: Order Recommendations")
        logger.info("="*40)
        
        test_orders = ["order_123", "order_456", "order_789"]
        for order_id in test_orders:
            logger.info(f"\nRecommendations for order '{order_id}':")
            order_recommendations = await recommendation_service.get_order_recommendations(order_id, limit=3)
            
            if order_recommendations:
                for rec in order_recommendations:
                    logger.info(f"  {rec.item_name}: {rec.similarity_score:.3f} - {rec.reason}")
            else:
                logger.warning(f"  No recommendations found for order: {order_id}")
        
        await redis_service.close()
        logger.info("\n" + "="*60)
        logger.info("HUGGINGFACE RECOMMENDATION SERVICE TEST COMPLETED!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error in HuggingFace recommendation service test: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_huggingface_recommendation_service())
