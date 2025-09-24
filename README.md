# Recommender System - Approach 1

A collaborative filtering recommender system built with FastAPI and Redis, designed to provide intelligent product recommendations based on order-item relationships.

## Project Structure

```
qnopy_poc/
├── api/                          # FastAPI application
│   └── app/
│       ├── main.py              # Main FastAPI app
│       ├── models/              # Pydantic models
│       ├── routers/             # API route handlers
│       ├── services/            # Business logic services
│       └── utils/               # Utility functions
├── processing/                   # Data processing pipeline
│   └── data_processor.py        # CSV data processing
├── data/                        # Data files
│   └── new_orders.csv          # Order-item data
├── config/                      # Configuration files
├── tests/                       # Test files
├── requirements.txt             # Python dependencies
├── run_api.py                   # API startup script
└── README.md                    # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- Redis server running on localhost:6379

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Redis server:**
   ```bash
   redis-server
   ```

3. **Run the API:**
   ```bash
   python run_api.py
   ```

4. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health/
   - Root: http://localhost:8000/

## API Endpoints

### Health Check
- `GET /health/` - Service health status

### Recommendations
- `GET /api/v1/recommendations/{order_id}` - Get recommendations for an order
- `GET /api/v1/similar-items/{item_name}` - Find similar items
- `POST /api/v1/basket-recommendations` - Get basket recommendations
- `GET /api/v1/popular-items` - Get popular items

## Current Status

This is a **minimal working version** with the following features:

✅ **Implemented:**
- Basic FastAPI service structure
- Redis service integration
- Health check endpoint
- Recommendation API endpoints (with mock data)
- Data processing pipeline
- Proper project structure

🚧 **Next Steps:**
- Connect data processing to Redis
- Implement actual collaborative filtering algorithms
- Add vector embeddings
- Docker containerization
- Performance optimization

## Development

### Running Tests
```bash
pytest tests/
```

### Data Processing
```bash
python processing/data_processor.py
```

### Code Formatting
```bash
black api/
flake8 api/
```

## Configuration

Copy `config.env.example` to `.env` and modify as needed:

```bash
cp config.env.example .env
```

## Architecture

The system uses a microservice architecture with:

- **FastAPI**: High-performance async web framework
- **Redis**: Vector database and caching layer
- **Pandas**: Data processing and analysis
- **scikit-learn**: Machine learning algorithms

## Future Enhancements

- Vector embeddings with RedisSearch
- Real-time recommendation updates
- A/B testing framework
- Advanced collaborative filtering algorithms
- Docker containerization
- Monitoring and logging
