"""
Embedding service for generating item vectors from co-occurrence data
"""
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
import pickle

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and managing item embeddings"""
    
    def __init__(self, embedding_dimension: int = 128):
        self.embedding_dimension = embedding_dimension
        self.item_embeddings: Dict[str, np.ndarray] = {}
        self.item_index: Dict[str, int] = {}
        self.index_item: Dict[int, str] = {}
        self.svd_model: Optional[TruncatedSVD] = None
        
    def build_cooccurrence_matrix(self, item_cooccurrence: Dict[str, Dict[str, int]]) -> np.ndarray:
        """Build normalized co-occurrence matrix from item relationships"""
        try:
            logger.info("Building co-occurrence matrix for embeddings...")
            
            # Create item index mapping
            items = sorted(item_cooccurrence.keys())
            self.item_index = {item: idx for idx, item in enumerate(items)}
            self.index_item = {idx: item for idx, item in enumerate(items)}
            
            n_items = len(items)
            cooccurrence_matrix = np.zeros((n_items, n_items))
            
            # Fill the matrix
            for item1, cooccurrences in item_cooccurrence.items():
                if item1 in self.item_index:
                    idx1 = self.item_index[item1]
                    for item2, count in cooccurrences.items():
                        if item2 in self.item_index:
                            idx2 = self.item_index[item2]
                            cooccurrence_matrix[idx1, idx2] = count
            
            # Normalize the matrix (optional: apply log scaling)
            cooccurrence_matrix = np.log1p(cooccurrence_matrix)  # log(1 + x) to handle zeros
            
            logger.info(f"Built co-occurrence matrix: {cooccurrence_matrix.shape}")
            return cooccurrence_matrix
            
        except Exception as e:
            logger.error(f"Error building co-occurrence matrix: {e}")
            raise
    
    def generate_embeddings(self, cooccurrence_matrix: np.ndarray) -> Dict[str, List[float]]:
        """Generate item embeddings using SVD"""
        try:
            logger.info(f"Generating embeddings with dimension {self.embedding_dimension}...")
            
            # Use Truncated SVD for dimensionality reduction
            self.svd_model = TruncatedSVD(
                n_components=self.embedding_dimension,
                random_state=42
            )
            
            # Fit SVD on the co-occurrence matrix
            embeddings_matrix = self.svd_model.fit_transform(cooccurrence_matrix)
            
            # Normalize embeddings for consistent similarity calculations
            embeddings_matrix = normalize(embeddings_matrix, norm='l2', axis=1)
            
            # Convert to dictionary format
            item_embeddings = {}
            for idx, item in self.index_item.items():
                embedding = embeddings_matrix[idx].tolist()
                item_embeddings[item] = embedding
                self.item_embeddings[item] = embeddings_matrix[idx]
            
            logger.info(f"Generated embeddings for {len(item_embeddings)} items")
            return item_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def calculate_similarity(self, item1: str, item2: str) -> float:
        """Calculate cosine similarity between two items"""
        try:
            if item1 not in self.item_embeddings or item2 not in self.item_embeddings:
                return 0.0
            
            vec1 = self.item_embeddings[item1]
            vec2 = self.item_embeddings[item2]
            
            # Cosine similarity
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
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
    
    def get_item_embedding(self, item_name: str) -> Optional[List[float]]:
        """Get embedding vector for a specific item"""
        try:
            if item_name in self.item_embeddings:
                return self.item_embeddings[item_name].tolist()
            return None
        except Exception as e:
            logger.error(f"Error getting embedding for {item_name}: {e}")
            return None
    
    def save_embeddings(self, filepath: str):
        """Save embeddings to file"""
        try:
            embeddings_data = {
                'item_embeddings': {k: v.tolist() for k, v in self.item_embeddings.items()},
                'item_index': self.item_index,
                'index_item': self.index_item,
                'embedding_dimension': self.embedding_dimension
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
            with open(filepath, 'rb') as f:
                embeddings_data = pickle.load(f)
            
            self.item_embeddings = {
                k: np.array(v) for k, v in embeddings_data['item_embeddings'].items()
            }
            self.item_index = embeddings_data['item_index']
            self.index_item = embeddings_data['index_item']
            self.embedding_dimension = embeddings_data['embedding_dimension']
            
            logger.info(f"Loaded embeddings from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            raise
