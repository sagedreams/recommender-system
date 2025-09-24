#!/usr/bin/env python3
"""
Script to load HuggingFace embeddings into Redis for all items
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

async def load_huggingface_embeddings_to_redis():
    """Load HuggingFace embeddings for all items into Redis"""
    try:
        logger.info("="*60)
        logger.info("LOADING HUGGINGFACE EMBEDDINGS TO REDIS")
        logger.info("="*60)
        
        # Initialize services
        redis_service = RedisService()
        await redis_service.initialize()
        
        # Process data and generate HuggingFace embeddings
        logger.info("Processing data and generating HuggingFace embeddings...")
        processor = DataProcessor(
            "new_orders.csv", 
            use_huggingface=True, 
            huggingface_model="all-minilm"
        )
        
        # Load and process data
        df = processor.load_data()
        processor.build_cooccurrence_matrix()
        processor.generate_embeddings()
        
        logger.info(f"Generated embeddings for {len(processor.item_embeddings)} items")
        
        # Store HuggingFace embeddings in Redis with separate keys
        logger.info("Storing HuggingFace embeddings in Redis...")
        hf_embeddings = {}
        hf_metadata = {}
        
        for item_name, embedding in processor.item_embeddings.items():
            # Use separate key pattern for HuggingFace embeddings
            hf_embeddings[f"hf:{item_name}"] = embedding
            hf_metadata[f"hf:{item_name}"] = {
                "frequency": processor.item_frequency.get(item_name, 0),
                "embedding_type": "huggingface",
                "model": "all-minilm",
                "dimension": len(embedding)
            }
        
        # Store embeddings using the existing bulk method but with new keys
        await redis_service.bulk_store_embeddings(hf_embeddings, hf_metadata)
        
        # Also store a summary of HuggingFace embeddings
        hf_summary = {
            "total_items": len(processor.item_embeddings),
            "model": "all-minilm",
            "embedding_dimension": len(list(processor.item_embeddings.values())[0]) if processor.item_embeddings else 0,
            "key_prefix": "hf:"
        }
        await redis_service.redis_client.set("hf:summary", str(hf_summary))
        
        logger.info(f"Successfully stored {len(processor.item_embeddings)} HuggingFace embeddings in Redis!")
        
        # Test the embeddings
        logger.info("Testing HuggingFace embeddings...")
        popular_items = processor.get_popular_items(5)
        if popular_items:
            test_item = popular_items[0][0]
            
            # Test individual embedding retrieval
            embedding_data = await redis_service.get_item_embedding(f"hf:{test_item}")
            if embedding_data:
                logger.info(f"Retrieved HuggingFace embedding for '{test_item}': {len(embedding_data['embedding'])} dimensions")
            
            # Test similarity search
            similar_items = await redis_service.find_similar_items_by_embedding(f"hf:{test_item}", 5)
            logger.info(f"Similar items to '{test_item}' (HuggingFace):")
            for item_data in similar_items:
                logger.info(f"  {item_data['item']}: {item_data['similarity']:.3f}")
        
        # Show summary
        logger.info("\n" + "="*60)
        logger.info("HUGGINGFACE EMBEDDINGS LOADED SUCCESSFULLY!")
        logger.info("="*60)
        logger.info(f"Total items processed: {len(processor.item_embeddings)}")
        logger.info(f"Embedding dimension: {len(list(processor.item_embeddings.values())[0]) if processor.item_embeddings else 0}")
        logger.info(f"Model used: all-minilm")
        logger.info(f"Redis key pattern: hf:item_name")
        logger.info("="*60)
        
        await redis_service.close()
        
    except Exception as e:
        logger.error(f"Error loading HuggingFace embeddings to Redis: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(load_huggingface_embeddings_to_redis())
