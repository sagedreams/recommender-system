# Recommender System - Approach 2: Matrix Factorization with Redis

## Executive Summary

This approach uses **Matrix Factorization** techniques to decompose the user-item interaction matrix into lower-dimensional representations. Unlike collaborative filtering, this method can handle sparse data more effectively and provides better scalability for large datasets. We'll use Redis to store the factorized matrices and FastAPI for the recommendation service.

## Why Matrix Factorization?

### Advantages over Collaborative Filtering
- **Sparse Data Handling**: Better performance with sparse user-item matrices
- **Scalability**: More efficient for large datasets (154K+ orders)
- **Latent Factors**: Discovers hidden patterns in user preferences
- **Cold Start**: Better handling of new items through latent features
- **Memory Efficiency**: Lower memory footprint than full similarity matrices

### Mathematical Foundation
```
R ≈ U × V^T
Where:
- R: User-Item interaction matrix (154,951 × 6,540)
- U: User latent factors matrix (154,951 × k)
- V: Item latent factors matrix (6,540 × k)
- k: Number of latent factors (typically 50-200)
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Redis         │    │   Training      │
│   Recommender   │◄──►│   Factor Store  │◄──►│   Pipeline      │
│   Service       │    │                 │    │   (Offline)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Technical Stack

- **API Layer**: FastAPI with async support
- **Storage**: Redis for factor matrices and metadata
- **Matrix Factorization**: scikit-learn, implicit, or custom implementation
- **Data Processing**: pandas, numpy, scipy
- **Training**: Offline batch processing
- **Deployment**: Docker containers

## Implementation Strategy

### Phase 1: Data Preparation

#### User-Item Matrix Construction
```python
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix

def build_interaction_matrix(orders_df):
    """
    Convert order-item data to user-item interaction matrix
    """
    # Create user-item matrix with implicit feedback
    user_item_matrix = orders_df.pivot_table(
        index='order_id', 
        columns='item_name', 
        values=1,  # Binary: item in order or not
        fill_value=0
    )
    
    # Convert to sparse matrix for memory efficiency
    sparse_matrix = csr_matrix(user_item_matrix.values)
    
    return sparse_matrix, user_item_matrix.index, user_item_matrix.columns
```

#### Matrix Characteristics
- **Dimensions**: 154,951 orders × 6,540 items
- **Sparsity**: ~99.7% (very sparse)
- **Data Type**: Binary (item in order = 1, not in order = 0)
- **Memory**: ~1.2GB for dense matrix, ~50MB for sparse

### Phase 2: Matrix Factorization Algorithms

#### Option A: Non-Negative Matrix Factorization (NMF)
```python
from sklearn.decomposition import NMF

def train_nmf_model(sparse_matrix, n_components=100):
    """
    Train NMF model for matrix factorization
    """
    model = NMF(
        n_components=n_components,
        init='random',
        random_state=42,
        max_iter=200
    )
    
    # Fit the model
    W = model.fit_transform(sparse_matrix)  # User factors
    H = model.components_                   # Item factors
    
    return model, W, H
```

#### Option B: Implicit Feedback Matrix Factorization
```python
import implicit

def train_implicit_model(sparse_matrix, factors=100):
    """
    Train implicit feedback model (better for binary data)
    """
    model = implicit.als.AlternatingLeastSquares(
        factors=factors,
        regularization=0.1,
        iterations=50
    )
    
    # Train the model
    model.fit(sparse_matrix.T)  # Transpose for user-item format
    
    return model
```

#### Option C: Singular Value Decomposition (SVD)
```python
from sklearn.decomposition import TruncatedSVD

def train_svd_model(sparse_matrix, n_components=100):
    """
    Train SVD model for matrix factorization
    """
    model = TruncatedSVD(
        n_components=n_components,
        random_state=42
    )
    
    # Fit the model
    user_factors = model.fit_transform(sparse_matrix)
    item_factors = model.components_
    
    return model, user_factors, item_factors
```

### Phase 3: Redis Storage Strategy

#### Factor Matrix Storage
```redis
# User factors storage
HSET user:factors:{order_id} factor_0 0.123 factor_1 0.456 ... factor_99 0.789

# Item factors storage  
HSET item:factors:{item_name} factor_0 0.234 factor_1 0.567 ... factor_99 0.890

# Metadata storage
HSET item:meta:{item_name} popularity 1234 category "sensors" last_updated "2024-01-01"
HSET user:meta:{order_id} order_size 5 total_items 12 last_updated "2024-01-01"
```

#### Redis Index Structure
```redis
# Create indexes for fast retrieval
FT.CREATE user_factors_idx ON HASH PREFIX 1 user:factors: SCHEMA 
    order_id TEXT SORTABLE
    factors VECTOR HNSW 6 TYPE FLOAT32 DIM 100 DISTANCE_METRIC COSINE

FT.CREATE item_factors_idx ON HASH PREFIX 1 item:factors: SCHEMA 
    item_name TEXT SORTABLE
    factors VECTOR HNSW 6 TYPE FLOAT32 DIM 100 DISTANCE_METRIC COSINE
```

### Phase 4: FastAPI Implementation

#### Core Recommendation Endpoints

```python
from fastapi import FastAPI, HTTPException
import redis
import numpy as np

app = FastAPI(title="Matrix Factorization Recommender")

@app.get("/recommendations/{order_id}")
async def get_recommendations(order_id: str, limit: int = 10):
    """
    Get recommendations for a specific order using matrix factorization
    """
    try:
        # Get user factors from Redis
        user_factors = await get_user_factors(order_id)
        
        # Get all item factors
        item_factors = await get_all_item_factors()
        
        # Calculate scores
        scores = np.dot(user_factors, item_factors.T)
        
        # Get top recommendations
        top_items = np.argsort(scores)[::-1][:limit]
        
        return {
            "order_id": order_id,
            "recommendations": [
                {
                    "item_name": item_names[i],
                    "score": float(scores[i]),
                    "rank": idx + 1
                }
                for idx, i in enumerate(top_items)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/similar-items/{item_name}")
async def get_similar_items(item_name: str, limit: int = 5):
    """
    Find items similar to a given item using factor similarity
    """
    try:
        # Get item factors
        item_factors = await get_item_factors(item_name)
        
        # Find similar items using vector similarity
        similar_items = await find_similar_items_by_factors(
            item_factors, limit
        )
        
        return {
            "item_name": item_name,
            "similar_items": similar_items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-recommendations")
async def get_batch_recommendations(
    order_ids: List[str], 
    limit: int = 10
):
    """
    Get recommendations for multiple orders in batch
    """
    results = {}
    for order_id in order_ids:
        recommendations = await get_recommendations(order_id, limit)
        results[order_id] = recommendations
    
    return {"batch_results": results}
```

### Phase 5: Recommendation Algorithms

#### User-Based Recommendations
```python
async def get_user_recommendations(order_id: str, limit: int = 10):
    """
    Generate recommendations using user latent factors
    """
    # Get user factors
    user_factors = await redis_client.hgetall(f"user:factors:{order_id}")
    user_vector = np.array([float(v) for v in user_factors.values()])
    
    # Get all item factors
    item_factors = await get_all_item_factors()
    
    # Calculate preference scores
    scores = np.dot(user_vector, item_factors.T)
    
    # Get items not already in order
    order_items = await get_order_items(order_id)
    available_items = set(item_factors.keys()) - set(order_items)
    
    # Filter and rank
    filtered_scores = {
        item: scores[i] for i, item in enumerate(item_factors.keys())
        if item in available_items
    }
    
    # Return top recommendations
    top_items = sorted(filtered_scores.items(), 
                      key=lambda x: x[1], reverse=True)[:limit]
    
    return top_items
```

#### Item-Based Recommendations
```python
async def get_item_recommendations(item_name: str, limit: int = 10):
    """
    Generate recommendations using item latent factors
    """
    # Get item factors
    item_factors = await redis_client.hgetall(f"item:factors:{item_name}")
    item_vector = np.array([float(v) for v in item_factors.values()])
    
    # Find similar items using cosine similarity
    similar_items = await find_similar_items_by_factors(
        item_vector, limit + 1  # +1 to exclude the item itself
    )
    
    # Remove the item itself from results
    similar_items = [item for item in similar_items 
                    if item['item_name'] != item_name][:limit]
    
    return similar_items
```

#### Hybrid Recommendations
```python
async def get_hybrid_recommendations(order_id: str, limit: int = 10):
    """
    Combine user-based and item-based recommendations
    """
    # Get user-based recommendations
    user_recs = await get_user_recommendations(order_id, limit * 2)
    
    # Get order items for item-based recommendations
    order_items = await get_order_items(order_id)
    
    # Get item-based recommendations for each order item
    item_recs = []
    for item in order_items[:3]:  # Limit to top 3 items in order
        similar = await get_item_recommendations(item, limit // 2)
        item_recs.extend(similar)
    
    # Combine and deduplicate
    all_recs = user_recs + item_recs
    unique_recs = {}
    
    for item, score in all_recs:
        if item not in unique_recs:
            unique_recs[item] = score
        else:
            unique_recs[item] = max(unique_recs[item], score)
    
    # Return top recommendations
    top_recs = sorted(unique_recs.items(), 
                     key=lambda x: x[1], reverse=True)[:limit]
    
    return top_recs
```

## Performance Optimizations

### Memory Management
```python
# Batch processing for large matrices
def process_factors_in_batches(factors, batch_size=1000):
    """
    Process factor matrices in batches to manage memory
    """
    for i in range(0, len(factors), batch_size):
        batch = factors[i:i + batch_size]
        yield batch

# Sparse matrix operations
from scipy.sparse import csr_matrix

def optimize_matrix_operations(matrix):
    """
    Optimize matrix operations for sparse data
    """
    # Convert to CSR format for efficient row operations
    if not isinstance(matrix, csr_matrix):
        matrix = csr_matrix(matrix)
    
    return matrix
```

### Caching Strategy
```python
# Redis caching for frequent computations
@lru_cache(maxsize=1000)
async def get_cached_recommendations(order_id: str, limit: int):
    """
    Cache recommendations for frequently requested orders
    """
    return await get_user_recommendations(order_id, limit)

# Pre-compute popular recommendations
async def precompute_popular_recommendations():
    """
    Pre-compute recommendations for popular orders
    """
    popular_orders = await get_popular_orders(limit=1000)
    
    for order_id in popular_orders:
        recommendations = await get_user_recommendations(order_id, 10)
        await redis_client.setex(
            f"precomputed:recs:{order_id}",
            3600,  # 1 hour TTL
            json.dumps(recommendations)
        )
```

## Training Pipeline

### Offline Training Process
```python
import schedule
import time

def train_model_pipeline():
    """
    Scheduled model training pipeline
    """
    # 1. Load latest data
    orders_df = load_latest_orders()
    
    # 2. Build interaction matrix
    matrix, user_ids, item_ids = build_interaction_matrix(orders_df)
    
    # 3. Train model
    model, user_factors, item_factors = train_nmf_model(matrix)
    
    # 4. Store factors in Redis
    store_factors_in_redis(user_factors, item_factors, user_ids, item_ids)
    
    # 5. Update model metadata
    update_model_metadata(model)

# Schedule training (e.g., daily at 2 AM)
schedule.every().day.at("02:00").do(train_model_pipeline)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(60)
```

### Model Evaluation
```python
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

def evaluate_model(model, test_matrix):
    """
    Evaluate model performance using holdout data
    """
    # Split data
    train_matrix, test_matrix = train_test_split(
        test_matrix, test_size=0.2, random_state=42
    )
    
    # Train on training set
    model.fit(train_matrix)
    
    # Predict on test set
    predictions = model.transform(test_matrix)
    
    # Calculate metrics
    mse = mean_squared_error(test_matrix, predictions)
    rmse = np.sqrt(mse)
    
    return {"mse": mse, "rmse": rmse}
```

## Deployment Architecture

### Docker Configuration
```dockerfile
# Dockerfile for training service
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY training/ ./training/
COPY data/ ./data/

CMD ["python", "training/train_model.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  recommender-api:
    build: ./api
    ports: ["8000:8000"]
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on: [redis]
  
  training-service:
    build: ./training
    volumes:
      - ./data:/app/data
    depends_on: [redis]
    command: python training/scheduler.py
  
  redis:
    image: redis/redis-stack:latest
    ports: ["6379:6379"]
    volumes:
      - ./redis-data:/data
```

## Monitoring & Analytics

### Model Performance Metrics
```python
# Track model performance
@app.get("/model/metrics")
async def get_model_metrics():
    """
    Get current model performance metrics
    """
    return {
        "model_version": await get_model_version(),
        "training_date": await get_training_date(),
        "rmse": await get_model_rmse(),
        "factors_count": await get_factors_count(),
        "coverage": await get_recommendation_coverage()
    }
```

### Recommendation Quality Metrics
```python
# Track recommendation effectiveness
async def track_recommendation_metrics(order_id: str, recommendations: list):
    """
    Track recommendation quality metrics
    """
    metrics = {
        "order_id": order_id,
        "recommendation_count": len(recommendations),
        "avg_score": np.mean([r["score"] for r in recommendations]),
        "score_std": np.std([r["score"] for r in recommendations]),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await redis_client.lpush("metrics:recommendations", json.dumps(metrics))
```

## Advantages of Matrix Factorization

### Technical Benefits
- **Scalability**: Handles large sparse matrices efficiently
- **Memory Efficiency**: Lower memory footprint than similarity matrices
- **Cold Start**: Better handling of new items through latent factors
- **Interpretability**: Latent factors can reveal item categories/features

### Business Benefits
- **Accuracy**: Often outperforms collaborative filtering
- **Diversity**: Can recommend diverse items through latent factors
- **Personalization**: Captures individual user preferences
- **Efficiency**: Fast inference once model is trained

## Limitations & Considerations

### Challenges
- **Training Time**: Requires offline training (not real-time)
- **Cold Start**: Still challenging for completely new users
- **Interpretability**: Latent factors are not easily interpretable
- **Data Requirements**: Needs sufficient interaction data

### Mitigation Strategies
- **Incremental Learning**: Update model with new data
- **Hybrid Approaches**: Combine with content-based filtering
- **Fallback Mechanisms**: Use popularity-based recommendations
- **Regular Retraining**: Schedule frequent model updates

## Comparison with Approach 1

| Aspect | Collaborative Filtering | Matrix Factorization |
|--------|------------------------|---------------------|
| **Scalability** | Good | Excellent |
| **Sparse Data** | Challenging | Excellent |
| **Training** | Real-time | Offline |
| **Memory Usage** | High | Moderate |
| **Cold Start** | Poor | Better |
| **Interpretability** | High | Low |
| **Accuracy** | Good | Excellent |

## Success Metrics

### Technical KPIs
- **Model RMSE**: < 0.1 for good performance
- **Training Time**: < 2 hours for full dataset
- **Inference Time**: < 50ms per recommendation
- **Memory Usage**: < 2GB for factor storage

### Business KPIs
- **Recommendation Diversity**: Measure item category spread
- **User Engagement**: Click-through rates on recommendations
- **Conversion Rate**: Items recommended vs. purchased
- **Coverage**: Percentage of items that can be recommended

## Conclusion

Matrix Factorization provides a robust and scalable approach for recommendation systems, particularly well-suited for sparse interaction data like your order-item dataset. The offline training requirement is offset by superior accuracy and scalability benefits.

**Key Advantages:**
- Excellent handling of sparse data
- Superior scalability for large datasets
- Better cold start performance
- Lower memory requirements

**Best Use Cases:**
- Large-scale recommendation systems
- Sparse interaction data
- When accuracy is more important than real-time training
- Systems with sufficient computational resources for offline training

This approach complements Approach 1 and could be used in a hybrid system where matrix factorization provides the primary recommendations with collaborative filtering as a fallback mechanism.
