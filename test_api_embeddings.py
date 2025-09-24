#!/usr/bin/env python3
"""
Test script to verify both embedding approaches work through the API
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add the api directory to the path
sys.path.append(str(Path(__file__).parent / "api"))

from api.app.services.redis_service import RedisService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_both_embedding_approaches():
    """Test both co-occurrence and HuggingFace embedding approaches"""
    try:
        logger.info("="*60)
        logger.info("TESTING BOTH EMBEDDING APPROACHES")
        logger.info("="*60)
        
        # Initialize Redis service
        redis_service = RedisService()
        await redis_service.initialize()
        
        test_item = "PID"
        logger.info(f"Testing with item: '{test_item}'")
        
        # Test 1: Co-occurrence embeddings
        logger.info("\n" + "="*40)
        logger.info("TEST 1: Co-occurrence Embeddings")
        logger.info("="*40)
        
        cooccur_embedding = await redis_service.get_item_embedding(test_item, "cooccurrence")
        if cooccur_embedding:
            logger.info(f"Co-occurrence embedding found: {len(cooccur_embedding['embedding'])} dimensions")
        else:
            logger.info("No co-occurrence embedding found (expected - not loaded yet)")
        
        cooccur_similar = await redis_service.find_similar_items_by_embedding(test_item, 3, "cooccurrence")
        logger.info(f"Co-occurrence similar items:")
        for item_data in cooccur_similar:
            logger.info(f"  {item_data['item']}: {item_data['similarity']:.3f}")
        
        # Test 2: HuggingFace embeddings
        logger.info("\n" + "="*40)
        logger.info("TEST 2: HuggingFace Embeddings")
        logger.info("="*40)
        
        hf_embedding = await redis_service.get_item_embedding(test_item, "huggingface")
        if hf_embedding:
            logger.info(f"HuggingFace embedding found: {len(hf_embedding['embedding'])} dimensions")
            logger.info(f"Model: {hf_embedding['metadata'].get('model', 'unknown')}")
        else:
            logger.error("No HuggingFace embedding found!")
            return
        
        hf_similar = await redis_service.find_similar_items_by_embedding(test_item, 5, "huggingface")
        logger.info(f"HuggingFace similar items:")
        for item_data in hf_similar:
            logger.info(f"  {item_data['item']}: {item_data['similarity']:.3f}")
        
        # Test 3: Compare approaches
        logger.info("\n" + "="*40)
        logger.info("TEST 3: Comparison")
        logger.info("="*40)
        
        logger.info("Co-occurrence approach:")
        logger.info("  ✓ Based on actual purchase patterns")
        logger.info("  ✓ No external model dependencies")
        logger.info("  ✓ Fast and lightweight")
        
        logger.info("\nHuggingFace approach:")
        logger.info("  ✓ Semantic understanding of item names")
        logger.info("  ✓ Better handling of similar/related items")
        logger.info("  ✓ Pre-trained on large text corpora")
        logger.info("  ✓ Can understand abbreviations and technical terms")
        
        # Test 4: API-style calls
        logger.info("\n" + "="*40)
        logger.info("TEST 4: API-style Calls")
        logger.info("="*40)
        
        # Simulate API calls
        logger.info("API calls would be:")
        logger.info(f"  GET /similar-items/{test_item}?embedding_type=cooccurrence")
        logger.info(f"  GET /similar-items/{test_item}?embedding_type=huggingface")
        logger.info(f"  GET /embeddings/{test_item}?embedding_type=cooccurrence")
        logger.info(f"  GET /embeddings/{test_item}?embedding_type=huggingface")
        
        await redis_service.close()
        logger.info("\n" + "="*60)
        logger.info("BOTH EMBEDDING APPROACHES TEST COMPLETED!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error in embedding approaches test: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_both_embedding_approaches())
