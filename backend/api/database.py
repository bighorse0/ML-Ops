from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio
from typing import AsyncGenerator
import structlog

from .config import settings
from models import Base

logger = structlog.get_logger()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create sync session factory for migrations
SessionLocal = sessionmaker(
    bind=engine.sync_engine,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def close_db():
    """Close database connections."""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

# Database health check
async def check_db_health() -> bool:
    """Check database health."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

# Database utilities
async def execute_raw_sql(sql: str, params: dict = None):
    """Execute raw SQL query."""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(sql, params or {})
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            logger.error(f"Raw SQL execution failed: {e}")
            raise

async def get_db_stats():
    """Get database statistics."""
    try:
        async with AsyncSessionLocal() as session:
            # Get table counts
            tables = [
                "features", "feature_versions", "feature_values",
                "users", "organizations", "roles", "permissions",
                "feature_drift", "data_quality", "monitoring_alerts",
                "feature_computations", "computation_jobs", "data_sources",
                "feature_lineage", "data_lineage", "model_lineage"
            ]
            
            stats = {}
            for table in tables:
                result = await session.execute(f"SELECT COUNT(*) FROM {table}")
                count = result.scalar()
                stats[table] = count
            
            return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}

# Migration utilities
def run_migrations():
    """Run database migrations."""
    try:
        import alembic.config
        import alembic.command
        
        alembic_cfg = alembic.config.Config("alembic.ini")
        alembic.command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        raise

def create_migration(message: str):
    """Create a new migration."""
    try:
        import alembic.config
        import alembic.command
        
        alembic_cfg = alembic.config.Config("alembic.ini")
        alembic.command.revision(alembic_cfg, message=message, autogenerate=True)
        logger.info(f"Migration created: {message}")
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise 