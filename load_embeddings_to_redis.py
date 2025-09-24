#!/usr/bin/env python3
"""
Script to load embeddings into Redis from processed data
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the api directory to the path
sys.path.append(str(Path(__file__).parent / "api"))

from api.app.services.redis_service import RedisService
from processing.data_processor import DataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def load_embeddings_to_redis():
    """Load embeddings and co-occurrence data into Redis"""
    try:
        # Initialize services
        redis_service = RedisService()
        await redis_service.initialize()
        
        # Process data and generate embeddings
        logger.info("Processing data and generating embeddings...")
        processor = DataProcessor("new_orders.csv", embedding_dimension=128)
        
        # Load and process data
        df = processor.load_data()
        processor.build_cooccurrence_matrix()
        processor.generate_embeddings()
        
        # Store embeddings in Redis
        logger.info("Storing embeddings in Redis...")
        await redis_service.bulk_store_embeddings(
            processor.item_embeddings,
            metadata={item: {"frequency": processor.item_frequency.get(item, 0)} 
                     for item in processor.item_embeddings.keys()}
        )
        
        # Store co-occurrence data for fallback
        logger.info("Storing co-occurrence data in Redis...")
        for item_name, cooccurrences in processor.item_cooccurrence.items():
            similar_items = processor.get_similar_items(item_name, 20)
            cooccurrence_data = {
                "similar_items": [{"item": item, "cooccurrence": count} 
                                for item, count in similar_items]
            }
            await redis_service.redis_client.set(
                f"cooccurrence:{item_name}", 
                str(cooccurrence_data)
            )
        
        # Store popular items
        popular_items = processor.get_popular_items(100)
        popular_data = {
            "items": [{"item": item, "frequency": freq} 
                     for item, freq in popular_items]
        }
        await redis_service.redis_client.set("popular_items", str(popular_data))
        
        # Store order items
        logger.info("Storing order data in Redis...")
        for order_id, items in processor.order_items.items():
            order_data = {"items": items}
            await redis_service.redis_client.set(f"order:{order_id}", str(order_data))
        
        logger.info("Successfully loaded all data into Redis!")
        
        # Test the embeddings
        logger.info("Testing embeddings...")
        test_item = popular_items[0][0] if popular_items else None
        if test_item:
            similar_items = await redis_service.find_similar_items_by_embedding(test_item, 5)
            logger.info(f"Similar items to '{test_item}':")
            for item_data in similar_items:
                logger.info(f"  {item_data['item']}: {item_data['similarity']:.3f}")
        
        await redis_service.close()
        
    except Exception as e:
        logger.error(f"Error loading embeddings to Redis: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(load_embeddings_to_redis())
