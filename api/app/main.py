"""
FastAPI Recommender Service - Main Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import recommendations, health
from .services.redis_service import RedisService
from .utils.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting Recommender Service...")
    redis_service = RedisService()
    await redis_service.initialize()
    app.state.redis = redis_service
    logger.info("Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Recommender Service...")
    await redis_service.close()
    logger.info("Service shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Recommender Service",
    description="Collaborative filtering recommender system with Redis vector database",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Recommender Service API",
        "version": "1.0.0",
        "docs": "/docs"
    }
