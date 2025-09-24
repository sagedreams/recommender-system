#!/usr/bin/env python3
"""
Debug script to test embedding retrieval
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.app.services.redis_service import RedisService

async def debug_embeddings():
    """Debug embedding retrieval"""
    try:
        redis_service = RedisService()
        await redis_service.initialize()
        
        test_item = "PID"
        
        print("=== Testing SVD Embeddings ===")
        svd_embedding = await redis_service.get_item_embedding(test_item, "cooccurrence")
        print(f"SVD embedding for {test_item}: {svd_embedding is not None}")
        if svd_embedding:
            print(f"  Dimension: {len(svd_embedding.get('embedding', []))}")
        
        print("\n=== Testing HuggingFace Embeddings ===")
        hf_embedding = await redis_service.get_item_embedding(test_item, "huggingface")
        print(f"HF embedding for {test_item}: {hf_embedding is not None}")
        if hf_embedding:
            print(f"  Dimension: {len(hf_embedding.get('embedding', []))}")
        
        print("\n=== Testing Similar Items SVD ===")
        svd_similar = await redis_service.find_similar_items_by_embedding(test_item, 3, "cooccurrence")
        print(f"SVD similar items: {len(svd_similar)}")
        for item in svd_similar[:3]:
            print(f"  - {item.get('item_name', 'Unknown')}: {item.get('similarity_score', 0):.3f}")
        
        print("\n=== Testing Similar Items HuggingFace ===")
        hf_similar = await redis_service.find_similar_items_by_embedding(test_item, 3, "huggingface")
        print(f"HF similar items: {len(hf_similar)}")
        for item in hf_similar[:3]:
            print(f"  - {item.get('item_name', 'Unknown')}: {item.get('similarity_score', 0):.3f}")
        
        await redis_service.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_embeddings())
