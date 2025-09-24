#!/usr/bin/env python3
"""
Test script for vector embeddings functionality
"""
import asyncio
import logging
import sys
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

async def test_embeddings():
    """Test the embedding functionality"""
    try:
        # Test data processing and embedding generation
        logger.info("Testing embedding generation...")
        processor = DataProcessor("new_orders.csv", embedding_dimension=64)  # Smaller dimension for testing
        
        # Load and process data
        df = processor.load_data()
        processor.build_cooccurrence_matrix()
        processor.generate_embeddings()
        
        logger.info(f"Generated embeddings for {len(processor.item_embeddings)} items")
        
        # Test embedding retrieval
        popular_items = processor.get_popular_items(5)
        if popular_items:
            test_item = popular_items[0][0]
            embedding = processor.get_item_embedding(test_item)
            logger.info(f"Embedding for '{test_item}': {len(embedding)} dimensions")
            
            # Test similarity
            similar_items = processor.find_similar_items_vector(test_item, 3)
            logger.info(f"Similar items to '{test_item}':")
            for item, similarity in similar_items:
                logger.info(f"  {item}: {similarity:.3f}")
        
        # Test Redis operations (if Redis is available)
        try:
            redis_service = RedisService()
            await redis_service.initialize()
            
            # Store a test embedding
            if popular_items:
                test_item = popular_items[0][0]
                test_embedding = processor.get_item_embedding(test_item)
                await redis_service.set_item_embedding(
                    test_item, 
                    test_embedding, 
                    {"frequency": popular_items[0][1]}
                )
                
                # Retrieve it back
                retrieved = await redis_service.get_item_embedding(test_item)
                logger.info(f"Retrieved embedding from Redis: {len(retrieved['embedding'])} dimensions")
            
            await redis_service.close()
            logger.info("Redis operations completed successfully")
            
        except Exception as e:
            logger.warning(f"Redis operations failed (Redis may not be running): {e}")
        
        logger.info("Embedding tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in embedding tests: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_embeddings())
