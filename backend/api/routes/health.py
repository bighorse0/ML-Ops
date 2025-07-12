from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import time
import structlog

from ..database import get_db, check_db_health, get_db_stats
from ..models.base import APIResponse

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=APIResponse)
async def health_check():
    """Basic health check endpoint."""
    return APIResponse(
        success=True,
        message="Feature Store API is healthy",
        data={
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0"
        }
    )

@router.get("/detailed", response_model=APIResponse)
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with database connectivity."""
    try:
        # Check database health
        db_healthy = await check_db_health()
        
        # Get database stats
        db_stats = await get_db_stats()
        
        health_status = "healthy" if db_healthy else "unhealthy"
        
        return APIResponse(
            success=db_healthy,
            message=f"Feature Store API is {health_status}",
            data={
                "status": health_status,
                "timestamp": time.time(),
                "version": "1.0.0",
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "stats": db_stats
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return APIResponse(
            success=False,
            message="Feature Store API is unhealthy",
            data={
                "status": "unhealthy",
                "timestamp": time.time(),
                "version": "1.0.0",
                "error": str(e)
            }
        )

@router.get("/ready", response_model=APIResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check for Kubernetes."""
    try:
        db_healthy = await check_db_health()
        
        if not db_healthy:
            return APIResponse(
                success=False,
                message="Service not ready",
                data={"status": "not_ready"}
            )
        
        return APIResponse(
            success=True,
            message="Service is ready",
            data={"status": "ready"}
        )
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return APIResponse(
            success=False,
            message="Service not ready",
            data={"status": "not_ready", "error": str(e)}
        )

@router.get("/live", response_model=APIResponse)
async def liveness_check():
    """Liveness check for Kubernetes."""
    return APIResponse(
        success=True,
        message="Service is alive",
        data={"status": "alive"}
    ) 