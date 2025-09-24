# Recommender System - Approach 1: Collaborative Filtering with Redis Vector Database

## Executive Summary

This document outlines the first approach for building a recommender system using collaborative filtering techniques with Redis as a vector database and FastAPI as the microservice framework. The system will analyze order-item relationships to provide intelligent product recommendations.

## Data Analysis Summary

Based on analysis of the `new_orders.csv` dataset:

- **Total records**: 497,585 order-item pairs
- **Unique orders**: 154,951 orders  
- **Unique items**: 6,540 different products
- **Data structure**: Simple CSV with `order_id` and `item_name` columns
- **Order size distribution**: Orders range from 1 item to 37 items (max observed)
- **Item popularity**: Some items appear very frequently (31,165 times for the most popular item)

## Architecture Overview

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Redis         │    │   Data          │
│   Recommender   │◄──►│   Vector DB     │◄──►│   Processing    │
│   Service       │    │                 │    │   Pipeline      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technical Stack

- **API Layer**: FastAPI (async, high-performance)
- **Vector Database**: Redis with RedisSearch module
- **Embedding Generation**: scikit-learn or sentence-transformers
- **Data Processing**: pandas, numpy
- **Containerization**: Docker & Docker Compose
- **Monitoring**: Built-in FastAPI metrics + Redis monitoring

## Approach: Collaborative Filtering with Vector Embeddings

### Why This Approach?

1. **Proven Effectiveness**: Collaborative filtering works well with purchase history data
2. **Scalability**: Redis vector search handles large datasets efficiently
3. **Real-time Performance**: Fast similarity search with Redis
4. **Flexibility**: Easy to extend with additional features

### Vector Generation Strategy

#### Option 1: Item-Based Embeddings
- Create vectors for each item based on co-purchase patterns
- Use TF-IDF or Word2Vec on item co-occurrence matrix
- Store item embeddings in Redis with metadata

#### Option 2: Order-Based Embeddings  
- Create vectors for each order (basket) by averaging item vectors
- Find similar historical baskets
- Recommend items from similar baskets

#### Option 3: Hybrid Approach (Recommended)
- Combine both item-based and order-based embeddings
- Weight recommendations based on multiple similarity signals
- Better coverage and accuracy

## Implementation Plan

### Phase 1: Data Preprocessing

```python
# Data cleaning pipeline
1. Standardize item names (remove special characters, normalize case)
2. Handle missing or invalid data
3. Create item-item co-occurrence matrix
4. Generate item frequency statistics
5. Create order-item mapping
```

### Phase 2: Embedding Generation

```python
# Vector creation process
1. Build item co-occurrence matrix from order data
2. Apply TF-IDF or Word2Vec to create item embeddings
3. Generate order embeddings by averaging constituent item vectors
4. Normalize vectors for consistent similarity calculations
5. Store embeddings with metadata in Redis
```

### Phase 3: Redis Vector Database Setup

```redis
# Redis configuration
FT.CREATE item_index ON HASH PREFIX 1 item: SCHEMA 
    id TEXT SORTABLE 
    name TEXT 
    embedding VECTOR HNSW 6 TYPE FLOAT32 DIM 128 DISTANCE_METRIC COSINE

FT.CREATE order_index ON HASH PREFIX 1 order: SCHEMA 
    id TEXT SORTABLE 
    embedding VECTOR HNSW 6 TYPE FLOAT32 DIM 128 DISTANCE_METRIC COSINE
```

### Phase 4: FastAPI Microservice Development

#### Core API Endpoints

```python
# Recommendation endpoints
GET /recommendations/{order_id}?limit=10
    - Get recommendations for a specific order
    - Returns similar items based on order history

GET /similar-items/{item_name}?limit=5
    - Find items similar to a given item
    - Based on co-purchase patterns

GET /basket-recommendations?items=item1,item2,item3&limit=10
    - Real-time recommendations for a basket
    - Combines multiple items for suggestions

# Analytics endpoints
GET /item-stats/{item_name}
    - Item popularity and co-purchase statistics

GET /order-stats/{order_id}
    - Order composition and similarity metrics

GET /popular-items?limit=20
    - Most frequently purchased items
```

#### API Response Format

```json
{
  "recommendations": [
    {
      "item_name": "MultiRae PID LEL",
      "similarity_score": 0.85,
      "reason": "Frequently purchased together",
      "popularity_rank": 3
    }
  ],
  "metadata": {
    "total_items": 6540,
    "processing_time_ms": 45,
    "algorithm_version": "v1.0"
  }
}
```

### Phase 5: Recommendation Algorithms

#### Primary Algorithm: Item-Based Collaborative Filtering

```python
def get_item_recommendations(item_name, limit=10):
    """
    1. Find items frequently co-purchased with target item
    2. Calculate vector similarity scores
    3. Apply popularity weighting
    4. Return top recommendations
    """
    pass

def get_basket_recommendations(items, limit=10):
    """
    1. Create basket embedding from item vectors
    2. Find similar historical baskets
    3. Extract items from similar baskets
    4. Rank by frequency and similarity
    """
    pass
```

#### Secondary Algorithm: Popularity-Based Fallback

```python
def get_popular_items(limit=10):
    """
    Fallback for cold start scenarios
    Returns most frequently purchased items
    """
    pass
```

## Performance Optimizations

### Caching Strategy
- **Redis Caching**: Cache frequent recommendations
- **TTL Management**: Different TTLs for different recommendation types
- **Cache Warming**: Pre-compute popular recommendations

### Database Optimizations
- **Vector Indexing**: Use HNSW algorithm for fast similarity search
- **Batch Processing**: Process embeddings in batches
- **Connection Pooling**: Optimize Redis connections

### API Optimizations
- **Async Processing**: Use FastAPI async for concurrent requests
- **Response Compression**: Compress large responses
- **Rate Limiting**: Implement request rate limiting

## Deployment Architecture

### Docker Compose Configuration

```yaml
version: '3.8'
services:
  recommender-api:
    build: ./api
    ports: ["8000:8000"]
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on: [redis]
    volumes:
      - ./data:/app/data
  
  redis:
    image: redis/redis-stack:latest
    ports: ["6379:6379"]
    volumes: 
      - ./redis-data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
  
  nginx:
    image: nginx:alpine
    ports: ["80:80"]
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on: [recommender-api]
```

### Environment Configuration

```bash
# .env file
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_password
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
EMBEDDING_DIMENSION=128
MAX_RECOMMENDATIONS=50
```

## Monitoring & Analytics

### Key Metrics
- **Response Time**: API endpoint performance
- **Hit Rate**: Cache effectiveness
- **Recommendation Quality**: User engagement metrics
- **System Health**: Redis connectivity, memory usage

### Logging Strategy
```python
# Structured logging with FastAPI
import structlog

logger = structlog.get_logger()

@logger.bind(endpoint="recommendations")
async def get_recommendations(order_id: str):
    # Log request details, processing time, results
    pass
```

### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "redis_connected": await check_redis_connection(),
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Data Quality & Edge Cases

### Cold Start Problem
- **New Items**: Use popularity-based recommendations
- **New Orders**: Recommend popular items or similar user baskets
- **Sparse Data**: Implement fallback strategies

### Data Validation
- **Input Sanitization**: Validate item names and order IDs
- **Error Handling**: Graceful handling of missing data
- **Data Consistency**: Regular data quality checks

### Bias Mitigation
- **Popularity Bias**: Balance popular vs. niche items
- **Temporal Bias**: Consider recency if timestamps available
- **Category Diversity**: Ensure diverse recommendations

## Scalability Considerations

### Horizontal Scaling
- **Load Balancing**: Multiple FastAPI instances behind nginx
- **Redis Clustering**: For larger datasets
- **Stateless Design**: No session state in API layer

### Performance Tuning
- **Vector Dimensions**: Optimize embedding dimensions (128-256)
- **Index Parameters**: Tune HNSW parameters for speed vs. accuracy
- **Memory Management**: Monitor Redis memory usage

## Testing Strategy

### Unit Tests
- Embedding generation accuracy
- Recommendation algorithm correctness
- API endpoint functionality

### Integration Tests
- Redis connectivity and operations
- End-to-end recommendation flow
- Performance benchmarks

### A/B Testing Framework
- Compare different algorithms
- Measure recommendation effectiveness
- User engagement metrics

## Future Enhancements

### Phase 2 Features
- **User Profiles**: Incorporate user behavior patterns
- **Temporal Patterns**: Seasonal and trend analysis
- **Content-Based Filtering**: Item description analysis
- **Real-time Learning**: Update models with new data

### Advanced Features
- **Multi-Armed Bandit**: Dynamic recommendation optimization
- **Deep Learning**: Neural collaborative filtering
- **Explainable AI**: Recommendation reasoning
- **Personalization**: User-specific preferences

## Risk Assessment

### Technical Risks
- **Redis Memory Usage**: Monitor and optimize
- **Vector Quality**: Validate embedding effectiveness
- **API Performance**: Load testing and optimization

### Business Risks
- **Recommendation Quality**: A/B testing and user feedback
- **Data Privacy**: Ensure compliance with regulations
- **System Reliability**: Implement proper monitoring

## Success Metrics

### Technical KPIs
- **Response Time**: < 100ms for recommendations
- **Availability**: 99.9% uptime
- **Cache Hit Rate**: > 80%

### Business KPIs
- **Recommendation Accuracy**: Measured through user engagement
- **Conversion Rate**: Items recommended vs. purchased
- **User Satisfaction**: Feedback and rating systems

## Conclusion

This collaborative filtering approach with Redis vector database provides a solid foundation for building an effective recommender system. The architecture is scalable, performant, and can be extended with additional features as requirements evolve.

The key advantages of this approach:
- **Fast Similarity Search**: Redis vector operations are highly optimized
- **Real-time Recommendations**: Low latency API responses
- **Scalable Architecture**: Can handle growing datasets
- **Flexible Design**: Easy to extend and modify

Next steps involve implementing the data preprocessing pipeline and setting up the Redis vector database infrastructure.
