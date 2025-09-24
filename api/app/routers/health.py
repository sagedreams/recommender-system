"""
Health check router
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from ..models.recommendation import HealthResponse
from ..services.redis_service import RedisService

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_redis_service() -> RedisService:
    """Dependency to get Redis service"""
    # This will be injected by the main app
    from ..main import app
    return app.state.redis

@router.get("/", response_model=HealthResponse)
async def health_check(redis_service: RedisService = Depends(get_redis_service)):
    """Health check endpoint"""
    try:
        redis_connected = await redis_service.health_check()
        status = "healthy" if redis_connected else "unhealthy"
        
        return HealthResponse(
            status=status,
            redis_connected=redis_connected,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            redis_connected=False,
            timestamp=datetime.utcnow().isoformat()
        )
