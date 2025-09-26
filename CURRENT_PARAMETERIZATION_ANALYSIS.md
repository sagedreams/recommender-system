# Current Parameterization Analysis

## ✅ Already Implemented Parameters

### API Parameters
- **`limit`**: Number of recommendations returned (1-20 for similar-items, 1-50 for orders, 1-100 for popular)
- **`embedding_type`**: Choose approach (simple, cooccurrence, huggingface, unified)

### Current API Usage
```bash
# Already working - limit parameter
curl "http://localhost:8000/api/v1/similar-items/PID?limit=10&embedding_type=unified"

# Already working - embedding type selection
curl "http://localhost:8000/api/v1/similar-items/PID?embedding_type=simple"
curl "http://localhost:8000/api/v1/similar-items/PID?embedding_type=cooccurrence"
curl "http://localhost:8000/api/v1/similar-items/PID?embedding_type=huggingface"
curl "http://localhost:8000/api/v1/similar-items/PID?embedding_type=unified"
```

## 🔧 Currently Hardcoded (Can Be Parameterized)

### 1. Unified Approach Weights
**Location**: `api/app/services/recommendation_service.py:248-252`
```python
weights = {
    'simple': 0.3,    # Simple co-occurrence
    'svd': 0.4,       # SVD embeddings (co-occurrence based)
    'huggingface': 0.3  # HuggingFace semantic embeddings
}
```

### 2. Consensus Boost Factor
**Location**: `api/app/services/recommendation_service.py:307`
```python
consensus_boost = 1.0 + (approach_count - 1) * 0.1
```

### 3. Similarity Calculation Method
**Location**: `api/app/services/redis_service.py:280-290`
```python
def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
    # Currently only cosine similarity
```

### 4. Embedding Dimensions
**Location**: `api/app/services/embedding_service.py:17`
```python
def __init__(self, embedding_dimension: int = 128):
```

### 5. HuggingFace Model Selection
**Location**: `api/app/services/huggingface_embedding_service.py:44`
```python
def __init__(self, model_name: str = "all-minilm", device: str = "auto"):
```

## 📊 Current Monitoring Capabilities

### What We Can Monitor Now
1. **Redis Memory Usage**: `redis-cli info memory`
2. **API Response Times**: FastAPI built-in metrics
3. **Request Counts**: FastAPI built-in metrics
4. **Error Rates**: FastAPI built-in metrics

### What We Need to Add
1. **Per-approach Memory Usage**: Track memory per embedding type
2. **Per-approach Response Times**: Time each approach separately
3. **Similarity Score Distributions**: Analyze recommendation quality
4. **Cache Hit Rates**: Track Redis cache performance
5. **Embedding Generation Metrics**: Track model loading and inference times

## 🚀 Quick Wins (Can Implement Immediately)

### 1. Add Weight Parameters to API
```python
# Add to get_similar_items endpoint
simple_weight: float = Query(0.3, ge=0.0, le=1.0)
svd_weight: float = Query(0.4, ge=0.0, le=1.0)
hf_weight: float = Query(0.3, ge=0.0, le=1.0)
consensus_boost: float = Query(1.1, ge=1.0, le=2.0)
```

### 2. Add Basic Performance Monitoring
```python
# Add timing decorator
@timing
async def get_similar_items_unified(self, item_name: str, limit: int = 5):
    start_time = time.time()
    # ... existing code ...
    end_time = time.time()
    logger.info(f"Unified recommendations took {end_time - start_time:.3f}s")
```

### 3. Add Memory Usage Endpoint
```python
@router.get("/monitoring/memory")
async def get_memory_usage():
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        "rss_mb": memory_info.rss / 1024 / 1024,
        "vms_mb": memory_info.vms / 1024 / 1024,
        "percent": process.memory_percent()
    }
```

### 4. Add Redis Metrics Endpoint
```python
@router.get("/monitoring/redis")
async def get_redis_metrics(redis_service: RedisService = Depends(get_redis_service)):
    info = await redis_service.redis_client.info()
    return {
        "memory_used_mb": info.get("used_memory", 0) / 1024 / 1024,
        "connected_clients": info.get("connected_clients", 0),
        "total_commands_processed": info.get("total_commands_processed", 0),
        "keyspace": info.get("db0", {})
    }
```

## 🎯 Immediate Implementation Priority

### High Priority (Week 1)
1. **Weight Parameters**: Make unified approach weights configurable via API
2. **Basic Monitoring**: Add memory and response time endpoints
3. **Performance Logging**: Add timing to all recommendation methods

### Medium Priority (Week 2)
1. **Similarity Thresholds**: Add minimum similarity score filtering
2. **Diversity Controls**: Add penalty for similar items in results
3. **Cache Metrics**: Track Redis performance

### Low Priority (Week 3+)
1. **A/B Testing**: Framework for testing different configurations
2. **Real-time Streaming**: WebSocket for live metrics
3. **Advanced Analytics**: Recommendation quality metrics

## 📈 Expected Impact

### Parameterization Benefits
- **Flexibility**: Easy to tune system for different use cases
- **Experimentation**: A/B test different approaches
- **Optimization**: Find optimal weights for specific scenarios
- **User Control**: Allow users to customize recommendations

### Monitoring Benefits
- **Performance**: Identify bottlenecks and optimize
- **Quality**: Track recommendation effectiveness
- **Reliability**: Monitor system health and errors
- **Scaling**: Understand resource usage for capacity planning

This analysis shows we have a solid foundation and can quickly add significant parameterization and monitoring capabilities with minimal changes to the existing system.
