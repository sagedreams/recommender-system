"""
HuggingFace-based embedding service for generating item vectors from text
"""
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from sentence_transformers import SentenceTransformer
import torch
import re

logger = logging.getLogger(__name__)

class HuggingFaceEmbeddingService:
    """Service for generating item embeddings using HuggingFace models"""
    
    # Available models with their characteristics
    AVAILABLE_MODELS = {
        "msmarco": {
            "model_name": "sentence-transformers/msmarco-distilbert-base-v4",
            "description": "MS MARCO trained model, good for search and retrieval",
            "dimension": 768,
            "max_length": 512
        },
        "all-minilm": {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "description": "General purpose model, fast and efficient",
            "dimension": 384,
            "max_length": 256
        },
        "all-mpnet": {
            "model_name": "sentence-transformers/all-mpnet-base-v2",
            "description": "High quality general purpose model",
            "dimension": 768,
            "max_length": 384
        },
        "paraphrase": {
            "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "description": "Multilingual model for diverse text",
            "dimension": 384,
            "max_length": 128
        }
    }
    
    def __init__(self, model_name: str = "all-minilm", device: str = "auto"):
        """
        Initialize the embedding service
        
        Args:
            model_name: Name of the model to use (key from AVAILABLE_MODELS)
            device: Device to run on ("auto", "cpu", "cuda", "mps")
        """
        self.model_name = model_name
        self.device = self._get_device(device)
        self.model = None
        self.model_info = self.AVAILABLE_MODELS.get(model_name, self.AVAILABLE_MODELS["all-minilm"])
        self.item_embeddings: Dict[str, np.ndarray] = {}
        
    def _get_device(self, device: str) -> str:
        """Determine the best device to use"""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"  # Apple Silicon
            else:
                return "cpu"
        return device
    
    def load_model(self):
        """Load the sentence transformer model"""
        try:
            logger.info(f"Loading HuggingFace model: {self.model_info['model_name']}")
            self.model = SentenceTransformer(
                self.model_info['model_name'],
                device=self.device
            )
            logger.info(f"Model loaded successfully on device: {self.device}")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_info['model_name']}: {e}")
            raise
    
    def preprocess_item_name(self, item_name: str) -> str:
        """
        Preprocess item names to make them more suitable for text embedding
        
        Args:
            item_name: Raw item name from the dataset
            
        Returns:
            Preprocessed item name
        """
        # Clean and normalize the item name
        processed = item_name.strip()
        
        # Replace common separators with spaces
        processed = re.sub(r'[-_/\\]', ' ', processed)
        
        # Remove extra whitespace
        processed = re.sub(r'\s+', ' ', processed)
        
        # Add context if the item name is very short or technical
        if len(processed.split()) <= 2:
            # For short technical names, add some context
            processed = f"product {processed}"
        
        return processed.strip()
    
    def generate_item_embeddings(self, items: List[str], batch_size: int = 32) -> Dict[str, List[float]]:
        """
        Generate embeddings for a list of items
        
        Args:
            items: List of item names
            batch_size: Batch size for processing
            
        Returns:
            Dictionary mapping item names to their embeddings
        """
        if not self.model:
            self.load_model()
        
        try:
            logger.info(f"Generating embeddings for {len(items)} items...")
            
            # Preprocess item names
            processed_items = [self.preprocess_item_name(item) for item in items]
            
            # Generate embeddings in batches
            embeddings = self.model.encode(
                processed_items,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalize for cosine similarity
            )
            
            # Create mapping
            item_embeddings = {}
            for i, item in enumerate(items):
                embedding = embeddings[i].tolist()
                item_embeddings[item] = embedding
                self.item_embeddings[item] = embeddings[i]
            
            logger.info(f"Generated embeddings for {len(item_embeddings)} items")
            return item_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def get_item_embedding(self, item_name: str) -> Optional[List[float]]:
        """Get embedding for a specific item"""
        if item_name in self.item_embeddings:
            return self.item_embeddings[item_name].tolist()
        return None
    
    def calculate_similarity(self, item1: str, item2: str) -> float:
        """Calculate cosine similarity between two items"""
        try:
            if item1 not in self.item_embeddings or item2 not in self.item_embeddings:
                return 0.0
            
            vec1 = self.item_embeddings[item1]
            vec2 = self.item_embeddings[item2]
            
            # Since embeddings are normalized, cosine similarity is just dot product
            similarity = np.dot(vec1, vec2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity between {item1} and {item2}: {e}")
            return 0.0
    
    def find_similar_items(self, item_name: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Find most similar items to a given item"""
        try:
            if item_name not in self.item_embeddings:
                return []
            
            similarities = []
            target_vector = self.item_embeddings[item_name]
            
            for other_item, other_vector in self.item_embeddings.items():
                if other_item != item_name:
                    similarity = np.dot(target_vector, other_vector)
                    similarities.append((other_item, float(similarity)))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar items for {item_name}: {e}")
            return []
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        return self.model_info['dimension']
    
    def get_model_info(self) -> Dict[str, any]:
        """Get information about the current model"""
        return {
            "model_name": self.model_name,
            "model_path": self.model_info['model_name'],
            "description": self.model_info['description'],
            "dimension": self.model_info['dimension'],
            "max_length": self.model_info['max_length'],
            "device": self.device,
            "loaded": self.model is not None
        }
    
    def save_embeddings(self, filepath: str):
        """Save embeddings to file"""
        try:
            import pickle
            embeddings_data = {
                'item_embeddings': {k: v.tolist() for k, v in self.item_embeddings.items()},
                'model_info': self.get_model_info(),
                'embedding_dimension': self.get_embedding_dimension()
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(embeddings_data, f)
            
            logger.info(f"Saved embeddings to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving embeddings: {e}")
            raise
    
    def load_embeddings(self, filepath: str):
        """Load embeddings from file"""
        try:
            import pickle
            with open(filepath, 'rb') as f:
                embeddings_data = pickle.load(f)
            
            self.item_embeddings = {
                k: np.array(v) for k, v in embeddings_data['item_embeddings'].items()
            }
            
            logger.info(f"Loaded embeddings from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            raise
