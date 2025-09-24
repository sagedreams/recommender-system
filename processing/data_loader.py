"""
Data loader to process CSV data and store in Redis
"""
import asyncio
import logging
import sys
import os
from typing import Dict, List, Tuple

# Add the api directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from data_processor import DataProcessor
from app.services.redis_service import RedisService
from app.utils.config import get_settings

logger = logging.getLogger(__name__)

class DataLoader:
    """Load processed data into Redis"""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.data_processor = DataProcessor(csv_file_path)
        self.redis_service = RedisService()
        self.settings = get_settings()
        
    async def initialize(self):
        """Initialize Redis connection"""
        await self.redis_service.initialize()
        logger.info("Redis connection established")
    
    async def load_all_data(self):
        """Load all processed data into Redis"""
        try:
            logger.info("Starting data loading process...")
            
            # Process the CSV data
            logger.info("Processing CSV data...")
            self.data_processor.load_data()
            self.data_processor.build_cooccurrence_matrix()
            
            # Store item statistics
            await self._store_item_statistics()
            
            # Store popular items
            await self._store_popular_items()
            
            # Store co-occurrence data
            await self._store_cooccurrence_data()
            
            # Store order data
            await self._store_order_data()
            
            logger.info("Data loading completed successfully!")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
        finally:
            await self.redis_service.close()
    
    async def _store_item_statistics(self):
        """Store item statistics in Redis"""
        logger.info("Storing item statistics...")
        
        # Get all unique items
        items = list(self.data_processor.item_frequency.keys())
        
        for item in items:
            stats = self.data_processor.get_item_stats(item)
            await self.redis_service.set_item_stats(item, stats)
        
        logger.info(f"Stored statistics for {len(items)} items")
    
    async def _store_popular_items(self):
        """Store popular items list in Redis"""
        logger.info("Storing popular items...")
        
        popular_items = self.data_processor.get_popular_items(100)  # Top 100
        
        # Store as a simple list in Redis
        popular_data = {
            "items": [{"item": item, "frequency": freq} for item, freq in popular_items],
            "total_items": len(popular_items)
        }
        
        await self.redis_service.redis_client.set(
            "popular_items", 
            str(popular_data)
        )
        
        logger.info(f"Stored {len(popular_items)} popular items")
    
    async def _store_cooccurrence_data(self):
        """Store co-occurrence data in Redis"""
        logger.info("Storing co-occurrence data...")
        
        # Store top co-occurring items for each item
        items = list(self.data_processor.item_cooccurrence.keys())
        
        for item in items:
            similar_items = self.data_processor.get_similar_items(item, 20)  # Top 20 similar
            
            cooccurrence_data = {
                "similar_items": [{"item": sim_item, "cooccurrence": count} for sim_item, count in similar_items],
                "total_similar": len(similar_items)
            }
            
            await self.redis_service.redis_client.set(
                f"cooccurrence:{item}", 
                str(cooccurrence_data)
            )
        
        logger.info(f"Stored co-occurrence data for {len(items)} items")
    
    async def _store_order_data(self):
        """Store order composition data in Redis"""
        logger.info("Storing order data...")
        
        # Store a sample of orders for testing
        sample_orders = dict(list(self.data_processor.order_items.items())[:1000])  # First 1000 orders
        
        for order_id, items in sample_orders.items():
            order_data = {
                "items": items,
                "item_count": len(items)
            }
            
            await self.redis_service.redis_client.set(
                f"order:{order_id}", 
                str(order_data)
            )
        
        logger.info(f"Stored data for {len(sample_orders)} sample orders")
    
    async def close(self):
        """Close Redis connection"""
        await self.redis_service.close()

async def main():
    """Main function to run data loading"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize data loader
    loader = DataLoader("new_orders.csv")
    
    try:
        await loader.initialize()
        await loader.load_all_data()
        
        # Print summary
        print("\n" + "="*50)
        print("DATA LOADING SUMMARY")
        print("="*50)
        
        # Get some stats from Redis
        redis = loader.redis_service.redis_client
        
        # Count stored items
        item_keys = await redis.keys("stats:item:*")
        print(f"Items with statistics stored: {len(item_keys)}")
        
        # Count co-occurrence data
        cooccurrence_keys = await redis.keys("cooccurrence:*")
        print(f"Items with co-occurrence data: {len(cooccurrence_keys)}")
        
        # Count sample orders
        order_keys = await redis.keys("order:*")
        print(f"Sample orders stored: {len(order_keys)}")
        
        # Test retrieval
        popular_data = await redis.get("popular_items")
        if popular_data:
            print("✅ Popular items data stored successfully")
        
        print("="*50)
        
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        return 1
    
    finally:
        await loader.close()
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
