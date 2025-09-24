#!/usr/bin/env python3
"""
Comprehensive comparison between HuggingFace embeddings and SVD approach
"""
import asyncio
import logging
import sys
import time
from pathlib import Path

# Add the api directory to the path
sys.path.append(str(Path(__file__).parent / "api"))

from processing.data_processor import DataProcessor
from api.app.services.redis_service import RedisService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compare_embedding_approaches():
    """Compare HuggingFace vs SVD embedding approaches"""
    try:
        logger.info("="*80)
        logger.info("COMPREHENSIVE EMBEDDING APPROACH COMPARISON")
        logger.info("="*80)
        
        # Test with a reasonable subset for comparison
        test_size = 5000  # 5000 records for meaningful comparison
        
        # 1. Test HuggingFace Embeddings
        logger.info("\n" + "="*50)
        logger.info("TESTING HUGGINGFACE EMBEDDINGS")
        logger.info("="*50)
        
        start_time = time.time()
        hf_processor = DataProcessor(
            "new_orders.csv", 
            use_huggingface=True, 
            huggingface_model="all-minilm"
        )
        
        # Load and process data
        df = hf_processor.load_data()
        hf_processor.df = hf_processor.df.head(test_size)
        logger.info(f"Using {len(hf_processor.df)} records for HuggingFace test")
        
        hf_processor.build_cooccurrence_matrix()
        hf_processor.generate_embeddings()
        
        hf_time = time.time() - start_time
        logger.info(f"HuggingFace processing time: {hf_time:.2f} seconds")
        logger.info(f"HuggingFace embeddings: {len(hf_processor.item_embeddings)} items")
        
        # 2. Test SVD Embeddings
        logger.info("\n" + "="*50)
        logger.info("TESTING SVD EMBEDDINGS")
        logger.info("="*50)
        
        start_time = time.time()
        svd_processor = DataProcessor(
            "new_orders.csv", 
            use_huggingface=False, 
            embedding_dimension=128
        )
        
        # Load and process data
        df = svd_processor.load_data()
        svd_processor.df = svd_processor.df.head(test_size)
        logger.info(f"Using {len(svd_processor.df)} records for SVD test")
        
        svd_processor.build_cooccurrence_matrix()
        svd_processor.generate_embeddings()
        
        svd_time = time.time() - start_time
        logger.info(f"SVD processing time: {svd_time:.2f} seconds")
        logger.info(f"SVD embeddings: {len(svd_processor.item_embeddings)} items")
        
        # 3. Compare Results
        logger.info("\n" + "="*50)
        logger.info("COMPARISON RESULTS")
        logger.info("="*50)
        
        # Get popular items for comparison
        popular_items = hf_processor.get_popular_items(10)
        if popular_items:
            test_item = popular_items[0][0]
            logger.info(f"Comparing similarities for item: '{test_item}'")
            
            # HuggingFace similarities
            hf_similar = hf_processor.find_similar_items_vector(test_item, 5)
            logger.info(f"\nHuggingFace similarities:")
            for item, similarity in hf_similar:
                logger.info(f"  {item}: {similarity:.3f}")
            
            # SVD similarities
            svd_similar = svd_processor.find_similar_items_vector(test_item, 5)
            logger.info(f"\nSVD similarities:")
            for item, similarity in svd_similar:
                logger.info(f"  {item}: {similarity:.3f}")
            
            # Traditional co-occurrence similarities
            cooccur_similar = hf_processor.get_similar_items(test_item, 5)
            logger.info(f"\nCo-occurrence similarities:")
            for item, count in cooccur_similar:
                logger.info(f"  {item}: {count} co-occurrences")
        
        # 4. Performance Summary
        logger.info("\n" + "="*50)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("="*50)
        logger.info(f"HuggingFace approach:")
        logger.info(f"  - Processing time: {hf_time:.2f} seconds")
        logger.info(f"  - Embedding dimension: 384")
        logger.info(f"  - Items processed: {len(hf_processor.item_embeddings)}")
        logger.info(f"  - Speed: {len(hf_processor.item_embeddings)/hf_time:.1f} items/second")
        
        logger.info(f"\nSVD approach:")
        logger.info(f"  - Processing time: {svd_time:.2f} seconds")
        logger.info(f"  - Embedding dimension: 128")
        logger.info(f"  - Items processed: {len(svd_processor.item_embeddings)}")
        logger.info(f"  - Speed: {len(svd_processor.item_embeddings)/svd_time:.1f} items/second")
        
        # 5. Quality Assessment
        logger.info("\n" + "="*50)
        logger.info("QUALITY ASSESSMENT")
        logger.info("="*50)
        
        logger.info("HuggingFace advantages:")
        logger.info("  ✓ Semantic understanding of item names")
        logger.info("  ✓ Better handling of similar/related items")
        logger.info("  ✓ Pre-trained on large text corpora")
        logger.info("  ✓ Can understand abbreviations and technical terms")
        
        logger.info("\nSVD advantages:")
        logger.info("  ✓ Based on actual purchase patterns")
        logger.info("  ✓ Smaller embedding size (128 vs 384)")
        logger.info("  ✓ Faster processing for large datasets")
        logger.info("  ✓ No external model dependencies")
        
        logger.info("\n" + "="*80)
        logger.info("COMPARISON COMPLETED SUCCESSFULLY!")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"Error in embedding comparison: {e}")
        raise

async def test_redis_integration():
    """Test Redis integration with HuggingFace embeddings"""
    try:
        logger.info("\n" + "="*50)
        logger.info("TESTING REDIS INTEGRATION")
        logger.info("="*50)
        
        # Initialize Redis service
        redis_service = RedisService()
        await redis_service.initialize()
        
        # Generate some test embeddings
        processor = DataProcessor(
            "new_orders.csv", 
            use_huggingface=True, 
            huggingface_model="all-minilm"
        )
        
        # Use small subset for Redis test
        df = processor.load_data()
        processor.df = processor.df.head(1000)
        processor.build_cooccurrence_matrix()
        processor.generate_embeddings()
        
        # Store embeddings in Redis
        logger.info("Storing embeddings in Redis...")
        await redis_service.bulk_store_embeddings(
            processor.item_embeddings,
            metadata={item: {"frequency": processor.item_frequency.get(item, 0)} 
                     for item in processor.item_embeddings.keys()}
        )
        
        # Test retrieval
        popular_items = processor.get_popular_items(3)
        if popular_items:
            test_item = popular_items[0][0]
            
            # Test individual embedding retrieval
            embedding_data = await redis_service.get_item_embedding(test_item)
            if embedding_data:
                logger.info(f"Retrieved embedding for '{test_item}': {len(embedding_data['embedding'])} dimensions")
            
            # Test similarity search
            similar_items = await redis_service.find_similar_items_by_embedding(test_item, 3)
            logger.info(f"Redis similarity search for '{test_item}':")
            for item_data in similar_items:
                logger.info(f"  {item_data['item']}: {item_data['similarity']:.3f}")
        
        await redis_service.close()
        logger.info("Redis integration test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in Redis integration test: {e}")
        # Don't raise - Redis might not be running

if __name__ == "__main__":
    # Run comparison
    compare_embedding_approaches()
    
    # Test Redis integration
    asyncio.run(test_redis_integration())
