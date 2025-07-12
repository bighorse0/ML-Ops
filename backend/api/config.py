from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "Feature Store as a Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Security
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["*"],
        env="ALLOWED_HOSTS"
    )
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    REDIS_POOL_SIZE: int = Field(default=10, env="REDIS_POOL_SIZE")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        env="KAFKA_BOOTSTRAP_SERVERS"
    )
    KAFKA_TOPIC_PREFIX: str = Field(default="feature-store", env="KAFKA_TOPIC_PREFIX")
    
    # Storage
    S3_ENDPOINT_URL: Optional[str] = Field(default=None, env="S3_ENDPOINT_URL")
    S3_ACCESS_KEY_ID: Optional[str] = Field(default=None, env="S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, env="S3_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME: str = Field(default="feature-store", env="S3_BUCKET_NAME")
    S3_REGION: str = Field(default="us-east-1", env="S3_REGION")
    
    # MinIO (for local development)
    MINIO_ENDPOINT: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    MINIO_BUCKET: str = Field(default="feature-store", env="MINIO_BUCKET")
    MINIO_SECURE: bool = Field(default=False, env="MINIO_SECURE")
    
    # ClickHouse
    CLICKHOUSE_HOST: str = Field(default="localhost", env="CLICKHOUSE_HOST")
    CLICKHOUSE_PORT: int = Field(default=8123, env="CLICKHOUSE_PORT")
    CLICKHOUSE_DATABASE: str = Field(default="feature_store_analytics", env="CLICKHOUSE_DATABASE")
    CLICKHOUSE_USER: str = Field(default="default", env="CLICKHOUSE_USER")
    CLICKHOUSE_PASSWORD: str = Field(default="", env="CLICKHOUSE_PASSWORD")
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_DEFAULT: int = Field(default=1000, env="RATE_LIMIT_DEFAULT")  # requests per minute
    RATE_LIMIT_FREE_TIER: int = Field(default=1000, env="RATE_LIMIT_FREE_TIER")
    RATE_LIMIT_PRO_TIER: int = Field(default=10000, env="RATE_LIMIT_PRO_TIER")
    RATE_LIMIT_ENTERPRISE_TIER: int = Field(default=100000, env="RATE_LIMIT_ENTERPRISE_TIER")
    
    # Feature Store Specific
    FEATURE_CACHE_TTL: int = Field(default=3600, env="FEATURE_CACHE_TTL")  # seconds
    FEATURE_BATCH_SIZE: int = Field(default=1000, env="FEATURE_BATCH_SIZE")
    FEATURE_MAX_RETRIES: int = Field(default=3, env="FEATURE_MAX_RETRIES")
    
    # Computation
    SPARK_MASTER_URL: str = Field(default="local[*]", env="SPARK_MASTER_URL")
    FLINK_JOBMANAGER_URL: str = Field(default="localhost:8081", env="FLINK_JOBMANAGER_URL")
    
    # Email (for notifications)
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_USE_TLS: bool = Field(default=True, env="SMTP_USE_TLS")
    
    # Slack (for notifications)
    SLACK_WEBHOOK_URL: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    # Testing
    TESTING: bool = Field(default=False, env="TESTING")
    TEST_DATABASE_URL: Optional[str] = Field(default=None, env="TEST_DATABASE_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate required settings
def validate_settings():
    """Validate required settings."""
    required_settings = [
        "SECRET_KEY",
        "DATABASE_URL"
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not getattr(settings, setting, None):
            missing_settings.append(setting)
    
    if missing_settings:
        raise ValueError(f"Missing required settings: {', '.join(missing_settings)}")

# Validate settings on import
if not settings.TESTING:
    validate_settings() 