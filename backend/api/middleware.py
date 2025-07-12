from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
import time
import structlog
from typing import Dict, Any
import asyncio
from collections import defaultdict
import aioredis
from prometheus_client import Counter, Histogram, Gauge

from .config import settings

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'organization_id']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'organization_id']
)

ACTIVE_REQUESTS = Gauge(
    'http_active_requests',
    'Number of active HTTP requests',
    ['organization_id']
)

RATE_LIMIT_EXCEEDED = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit exceeded requests',
    ['organization_id', 'endpoint']
)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # Extract request information
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Get organization ID from headers or context
        organization_id = request.headers.get("X-Organization-ID", "unknown")
        
        # Log request start
        logger.info(
            "Request started",
            method=method,
            url=url,
            client_ip=client_ip,
            user_agent=user_agent,
            organization_id=organization_id
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log request completion
            logger.info(
                "Request completed",
                method=method,
                url=url,
                status_code=response.status_code,
                duration=duration,
                organization_id=organization_id
            )
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=request.url.path,
                status_code=response.status_code,
                organization_id=organization_id
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=request.url.path,
                organization_id=organization_id
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log request error
            logger.error(
                "Request failed",
                method=method,
                url=url,
                error=str(e),
                duration=duration,
                organization_id=organization_id,
                exc_info=True
            )
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=request.url.path,
                status_code=500,
                organization_id=organization_id
            ).inc()
            
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting based on organization."""
    
    def __init__(self, app):
        super().__init__(app)
        self.redis = None
        self.rate_limit_cache = defaultdict(lambda: {"count": 0, "reset_time": 0})
    
    async def get_redis(self):
        """Get Redis connection."""
        if self.redis is None:
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis
    
    async def check_rate_limit(self, organization_id: str, endpoint: str) -> bool:
        """Check if request is within rate limit."""
        try:
            redis = await self.get_redis()
            
            # Create rate limit key
            key = f"rate_limit:{organization_id}:{endpoint}"
            current_time = int(time.time())
            
            # Get current count
            count = await redis.get(key)
            count = int(count) if count else 0
            
            # Get rate limit for organization (simplified - in real app, get from DB)
            rate_limit = settings.RATE_LIMIT_DEFAULT
            
            if count >= rate_limit:
                RATE_LIMIT_EXCEEDED.labels(
                    organization_id=organization_id,
                    endpoint=endpoint
                ).inc()
                return False
            
            # Increment counter
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, 60)  # Reset every minute
            await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Allow request if rate limiting fails
            return True
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get organization ID
        organization_id = request.headers.get("X-Organization-ID", "default")
        endpoint = request.url.path
        
        # Check rate limit
        allowed = await self.check_rate_limit(organization_id, endpoint)
        
        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                organization_id=organization_id,
                endpoint=endpoint,
                client_ip=request.client.host if request.client else "unknown"
            )
            
            return Response(
                content='{"success": false, "message": "Rate limit exceeded", "error_code": "RATE_LIMIT_EXCEEDED"}',
                status_code=429,
                media_type="application/json"
            )
        
        # Increment active requests
        ACTIVE_REQUESTS.labels(organization_id=organization_id).inc()
        
        try:
            response = await call_next(request)
            return response
        finally:
            # Decrement active requests
            ACTIVE_REQUESTS.labels(organization_id=organization_id).dec()

class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for application monitoring."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        # Extract monitoring information
        organization_id = request.headers.get("X-Organization-ID", "unknown")
        endpoint = request.url.path
        method = request.method
        
        # Track request start
        logger.debug(
            "Request monitoring start",
            organization_id=organization_id,
            endpoint=endpoint,
            method=method
        )
        
        try:
            response = await call_next(request)
            
            # Calculate metrics
            duration = time.time() - start_time
            
            # Log performance metrics
            if duration > 1.0:  # Log slow requests
                logger.warning(
                    "Slow request detected",
                    organization_id=organization_id,
                    endpoint=endpoint,
                    method=method,
                    duration=duration,
                    status_code=response.status_code
                )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error metrics
            logger.error(
                "Request error",
                organization_id=organization_id,
                endpoint=endpoint,
                method=method,
                duration=duration,
                error=str(e),
                exc_info=True
            )
            
            raise

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers and validation."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Remove sensitive headers
        response.headers.pop("Server", None)
        
        return response

class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware for request correlation and tracing."""
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            import uuid
            correlation_id = str(uuid.uuid4())
        
        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        
        # Add correlation ID to response headers
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response

# Middleware factory
def create_middleware_stack(app):
    """Create and configure middleware stack."""
    app.add_middleware(CorrelationMiddleware)
    app.add_middleware(SecurityMiddleware)
    app.add_middleware(MonitoringMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    return app 