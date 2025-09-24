#!/usr/bin/env python3
"""
Script to load SVD-based embeddings into Redis
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from processing.data_processor import DataProcessor
from api.app.services.redis_service import RedisService

async def load_svd_embeddings_to_redis():
    """Load SVD embeddings into Redis"""
    try:
        print("Processing data and generating SVD embeddings...")
        
        # Initialize data processor with SVD approach
        processor = DataProcessor(
            csv_file_path="new_orders.csv",
            embedding_dimension=128,
            use_huggingface=False  # Use SVD instead
        )
        
        # Load and process data
        processor.load_data()
        processor.build_cooccurrence_matrix()
        
        # Generate SVD embeddings
        processor.generate_embeddings()
        embeddings = processor.item_embeddings
        
        print(f"Generated {len(embeddings)} SVD embeddings")
        
        # Initialize Redis service
        redis_service = RedisService()
        await redis_service.initialize()
        
        print("Storing SVD embeddings in Redis...")
        
        # Store embeddings with correct key pattern (item:*)
        for item_name, embedding in embeddings.items():
            await redis_service.set_item_embedding(
                item_name=item_name,
                embedding=embedding,
                metadata={
                    "approach": "svd",
                    "dimension": len(embedding),
                    "model": "TruncatedSVD"
                }
            )
        
        print(f"Stored {len(embeddings)} SVD embeddings in Redis")
        
        # Test the embeddings
        print("Testing SVD embeddings...")
        test_item = "PID"
        similar_items = await redis_service.find_similar_items_by_embedding(
            test_item, limit=5, embedding_type="cooccurrence"
        )
        
        print(f"Similar items to '{test_item}':")
        for item in similar_items:
            print(f"  - {item.get('item_name', 'Unknown')}: {item.get('similarity_score', 0):.3f}")
        
        await redis_service.close()
        print("Successfully loaded SVD embeddings into Redis!")
        
    except Exception as e:
        print(f"Error loading SVD embeddings: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(load_svd_embeddings_to_redis())
