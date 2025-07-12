from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import time
import structlog
from contextlib import asynccontextmanager

from .config import settings
from .database import engine, Base
from .middleware import RequestLoggingMiddleware, RateLimitMiddleware
from .auth import get_current_user
from .routes import (
    features,
    feature_values,
    users,
    organizations,
    monitoring,
    computation,
    lineage,
    health
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Feature Store API")
    
    # Create database tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Feature Store API")

# Create FastAPI application
app = FastAPI(
    title="Feature Store as a Service",
    description="A comprehensive Feature Store platform for ML teams",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Custom exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else None
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )

# Custom OpenAPI schema
def custom_openapi():
    """Custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Feature Store as a Service",
        version="1.0.0",
        description="""
        ## Overview
        
        A comprehensive Feature Store as a Service platform that enables ML teams to store, manage, serve, and monitor machine learning features at scale.
        
        ## Key Features
        
        * **Feature Registry**: Metadata management, feature definitions, lineage tracking
        * **Multi-Modal Serving**: Online (<1ms p99), batch, and streaming feature serving
        * **Data Quality & Monitoring**: Schema validation, drift detection, anomaly detection
        * **Multi-Tenancy**: Namespace isolation, RBAC, API rate limiting
        * **Enterprise Security**: SOC2, GDPR, HIPAA ready with audit trails
        
        ## Authentication
        
        This API uses JWT tokens for authentication. Include the token in the Authorization header:
        
        ```
        Authorization: Bearer <your-jwt-token>
        ```
        
        ## Rate Limiting
        
        API requests are rate limited per organization. Limits are:
        - 1000 requests per minute for free tier
        - 10000 requests per minute for pro tier
        - 100000 requests per minute for enterprise tier
        
        ## Performance
        
        - Online serving: <1ms p99 latency, >10k RPS
        - Batch processing: Handle 1M+ feature computations/hour
        - Memory usage: <2GB per service instance
        - Database query performance: <10ms average
        """,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Include API routes
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(features.router, prefix="/api/v1/features", tags=["Features"])
app.include_router(feature_values.router, prefix="/api/v1/feature-values", tags=["Feature Values"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])
app.include_router(computation.router, prefix="/api/v1/computation", tags=["Computation"])
app.include_router(lineage.router, prefix="/api/v1/lineage", tags=["Lineage"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "success": True,
        "message": "Feature Store as a Service API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "features": {
            "description": "Comprehensive Feature Store platform for ML teams",
            "capabilities": [
                "Feature Registry & Metadata Management",
                "Multi-Modal Feature Serving (Online/Batch/Streaming)",
                "Data Quality & Drift Monitoring",
                "Multi-Tenant RBAC Security",
                "Feature Lineage & Governance",
                "Enterprise Compliance (SOC2, GDPR, HIPAA)"
            ],
            "performance": {
                "online_serving_latency": "<1ms p99",
                "throughput": ">10k RPS",
                "batch_processing": "1M+ features/hour",
                "memory_usage": "<2GB per instance"
            }
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 