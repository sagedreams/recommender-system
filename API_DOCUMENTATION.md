# Recommender System API Documentation

## Overview

The Recommender System API provides intelligent product recommendations using collaborative filtering techniques with Redis as a vector database. The system analyzes order-item relationships to suggest relevant products based on purchase patterns.

**Base URL**: `http://localhost:8000`  
**API Version**: `v1`  
**Content-Type**: `application/json`

## Authentication

Currently, the API does not require authentication. In production, consider implementing:
- API key authentication
- JWT tokens
- Rate limiting

## Rate Limiting

- **Default**: No rate limiting (development)
- **Production**: Recommended 100 requests/minute per IP
- **Headers**: Rate limit information will be included in response headers

## Data Model

### Recommendation Item
```json
{
  "item_name": "string",
  "similarity_score": 0.0-1.0,
  "reason": "string",
  "popularity_rank": integer | null
}
```

### Recommendation Response
```json
{
  "recommendations": [RecommendationItem],
  "metadata": {
    "limit": integer,
    "total_recommendations": integer,
    "additional_fields": "varies by endpoint"
  }
}
```

## Endpoints

### Health & Status

#### GET /health/
Check the health status of the service and Redis connection.

**Response:**
```json
{
  "status": "healthy|unhealthy",
  "redis_connected": boolean,
  "timestamp": "ISO 8601 timestamp"
}
```

**Example:**
```bash
curl "http://localhost:8000/health/"
```

#### GET /
Get basic API information.

**Response:**
```json
{
  "message": "Recommender Service API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### Recommendations

#### GET /api/v1/popular-items
Get the most frequently purchased items.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of items to return (1-100, default: 10)

**Response:**
```json
{
  "recommendations": [
    {
      "item_name": "PID",
      "similarity_score": 1.0,
      "reason": "Popular item (purchased 30245 times)",
      "popularity_rank": 1
    }
  ],
  "metadata": {
    "limit": 10,
    "total_recommendations": 10
  }
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/popular-items?limit=5"
```

#### GET /api/v1/similar-items/{item_name}
Find items frequently co-purchased with the specified item.

**Path Parameters:**
- `item_name` (string): Name of the item to find similar items for

**Query Parameters:**
- `limit` (integer, optional): Maximum number of similar items (1-20, default: 5)

**Response:**
```json
{
  "recommendations": [
    {
      "item_name": "Cal Kit - Std - 34L Regulator 100PPM/Tedlar Bag",
      "similarity_score": 1.0,
      "reason": "Frequently purchased together (17951 times)",
      "popularity_rank": null
    }
  ],
  "metadata": {
    "item_name": "PID",
    "limit": 5,
    "total_recommendations": 5
  }
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/similar-items/PID?limit=3"
```

#### POST /api/v1/basket-recommendations
Get real-time recommendations for a basket of items.

**Request Body:**
```json
{
  "items": ["string"],
  "limit": integer
}
```

**Request Parameters:**
- `items` (array): List of item names in the basket (min: 1)
- `limit` (integer): Maximum number of recommendations (1-50, default: 10)

**Response:**
```json
{
  "recommendations": [
    {
      "item_name": "Cal Kit - Std - 34L Regulator 100PPM/Tedlar Bag",
      "similarity_score": 0.759629690857993,
      "reason": "Popular item (purchased 22975 times)",
      "popularity_rank": 3
    }
  ],
  "metadata": {
    "basket_items": ["PID", "Water Level Meter"],
    "limit": 10,
    "total_recommendations": 10
  }
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/basket-recommendations" \
  -H "Content-Type: application/json" \
  -d '{"items": ["PID", "Water Level Meter"], "limit": 5}'
```

#### GET /api/v1/recommendations/{order_id}
Get recommendations for a specific order.

**Path Parameters:**
- `order_id` (string): ID of the order to get recommendations for

**Query Parameters:**
- `limit` (integer, optional): Maximum number of recommendations (1-50, default: 10)

**Response:**
```json
{
  "recommendations": [
    {
      "item_name": "PID",
      "similarity_score": 1.0,
      "reason": "Popular item (purchased 30245 times)",
      "popularity_rank": 1
    }
  ],
  "metadata": {
    "order_id": "12345",
    "limit": 10,
    "total_recommendations": 10
  }
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/recommendations/12345?limit=5"
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error message",
      "type": "error_type"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Response Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error - Server error |

## Data Insights

### Top Items (Based on Real Data)
1. **PID** - 30,245 purchases
2. **Water Level Meter** - 29,558 purchases
3. **Cal Kit - Std - 34L Regulator 100PPM/Tedlar Bag** - 22,975 purchases
4. **YSI** - 18,676 purchases
5. **Horiba** - 15,305 purchases

### Strong Co-occurrence Patterns
- **PID + Cal Kit**: 17,951 co-purchases
- **PID + Water Level Meter**: 8,124 co-purchases
- **PID + Gloves**: 3,609 co-purchases

### Dataset Statistics
- **Total Records**: 486,620 order-item pairs
- **Unique Orders**: 154,167
- **Unique Items**: 15,105
- **Average Order Size**: 3.16 items
- **Max Order Size**: 35 items

## Testing

### Postman Collection
Import the provided Postman collection for comprehensive API testing:
- `postman_collection.json` - Complete API test suite
- `postman_environment.json` - Environment variables

### Test Scenarios
1. **Basic Functionality**
   - Health check
   - Popular items retrieval
   - Similar items lookup
   - Basket recommendations

2. **Edge Cases**
   - Invalid item names
   - Empty baskets
   - Limit validation
   - Malformed JSON

3. **Performance**
   - Response time < 100ms
   - Concurrent requests
   - Large result sets

### Example Test Commands

```bash
# Health check
curl "http://localhost:8000/health/"

# Get top 5 popular items
curl "http://localhost:8000/api/v1/popular-items?limit=5"

# Find items similar to PID
curl "http://localhost:8000/api/v1/similar-items/PID?limit=3"

# Get basket recommendations
curl -X POST "http://localhost:8000/api/v1/basket-recommendations" \
  -H "Content-Type: application/json" \
  -d '{"items": ["PID", "Water Level Meter"], "limit": 3}'

# Test error handling
curl "http://localhost:8000/api/v1/similar-items/NonExistentItem?limit=5"
```

## Performance

### Benchmarks
- **API Response Time**: < 100ms (95th percentile)
- **Redis Query Time**: < 10ms
- **Memory Usage**: ~16MB for 29K+ keys
- **Throughput**: 100+ requests/second

### Optimization
- Redis caching for frequent queries
- Pre-computed popular items
- Efficient co-occurrence matrix storage
- Async request handling

## Monitoring

### Health Checks
- Service health: `/health/`
- Redis connectivity
- Response time monitoring
- Error rate tracking

### Metrics
- Request count per endpoint
- Response time distribution
- Error rates by type
- Cache hit rates

## Deployment

### Development
```bash
# Start Redis
redis-server

# Start API
python run_api.py
```

### Production
```bash
# Using Docker Compose
docker-compose up -d

# Or using Docker
docker build -t recommender-api .
docker run -p 8000:8000 recommender-api
```

### Environment Variables
- `REDIS_URL`: Redis connection string
- `API_HOST`: API host (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)

## Changelog

### v1.0.0 (2025-09-24)
- Initial release
- Basic recommendation endpoints
- Redis integration
- Audit logging
- Comprehensive testing suite

## Support

For issues and questions:
1. Check the health endpoint: `/health/`
2. Review error responses
3. Check Redis connectivity
4. Verify data processing logs

## Future Enhancements

- User-based recommendations
- Real-time learning
- A/B testing framework
- Advanced filtering options
- Recommendation explanations
- Performance analytics
