#!/usr/bin/env python3
"""
Test script for HuggingFace embeddings functionality
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add the api directory to the path
sys.path.append(str(Path(__file__).parent / "api"))

from api.app.services.huggingface_embedding_service import HuggingFaceEmbeddingService
from processing.data_processor import DataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_huggingface_embeddings():
    """Test the HuggingFace embedding functionality"""
    try:
        # Test different models
        models_to_test = ["all-minilm", "msmarco", "all-mpnet"]
        
        for model_name in models_to_test:
            logger.info(f"\n{'='*50}")
            logger.info(f"Testing model: {model_name}")
            logger.info(f"{'='*50}")
            
            # Initialize the embedding service
            embedding_service = HuggingFaceEmbeddingService(model_name)
            
            # Get model info
            model_info = embedding_service.get_model_info()
            logger.info(f"Model info: {model_info}")
            
            # Test with sample item names
            sample_items = [
                "PID Controller",
                "Temperature Sensor",
                "Pressure Gauge",
                "Flow Meter",
                "Calibration Kit",
                "Data Logger",
                "Control Valve",
                "Process Monitor"
            ]
            
            logger.info(f"Generating embeddings for {len(sample_items)} sample items...")
            embeddings = embedding_service.generate_item_embeddings(sample_items)
            
            logger.info(f"Generated embeddings with dimension: {embedding_service.get_embedding_dimension()}")
            
            # Test similarity calculations
            if len(sample_items) >= 2:
                test_item = sample_items[0]
                similar_items = embedding_service.find_similar_items(test_item, 3)
                
                logger.info(f"Items similar to '{test_item}':")
                for item, similarity in similar_items:
                    logger.info(f"  {item}: {similarity:.3f}")
            
            # Test individual embedding retrieval
            test_embedding = embedding_service.get_item_embedding(sample_items[0])
            if test_embedding:
                logger.info(f"Retrieved embedding for '{sample_items[0]}': {len(test_embedding)} dimensions")
            
            logger.info(f"Model {model_name} test completed successfully!")

    except Exception as e:
        logger.error(f"Error in HuggingFace embedding tests: {e}")
        raise

def test_data_processor_with_huggingface():
    """Test data processor with HuggingFace embeddings"""
    try:
        logger.info(f"\n{'='*50}")
        logger.info("Testing DataProcessor with HuggingFace embeddings")
        logger.info(f"{'='*50}")
        
        # Test with a small subset first
        processor = DataProcessor(
            "new_orders.csv", 
            use_huggingface=True, 
            huggingface_model="all-minilm"
        )
        
        # Load and process data
        logger.info("Loading data...")
        df = processor.load_data()
        
        # Take only first 1000 rows for testing
        processor.df = processor.df.head(1000)
        logger.info(f"Using subset of {len(processor.df)} records for testing")
        
        # Build co-occurrence matrix
        logger.info("Building co-occurrence matrix...")
        processor.build_cooccurrence_matrix()
        
        # Generate embeddings
        logger.info("Generating HuggingFace embeddings...")
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
        
        logger.info("DataProcessor with HuggingFace test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in DataProcessor HuggingFace test: {e}")
        raise

if __name__ == "__main__":
    # Test HuggingFace embedding service directly
    test_huggingface_embeddings()
    
    # Test with data processor
    test_data_processor_with_huggingface()
