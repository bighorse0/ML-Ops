from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import (
    Column, String, Text, JSON, Float, Integer, DateTime, 
    ForeignKey, Index, Boolean, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

from .base import Base, BaseModelMixin, PydanticBaseModel, Field

class JobStatus(str, Enum):
    """Computation job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class JobType(str, Enum):
    """Types of computation jobs."""
    BATCH = "batch"
    STREAMING = "streaming"
    BACKFILL = "backfill"
    VALIDATION = "validation"

class ComputeEngine(str, Enum):
    """Supported compute engines."""
    SPARK = "spark"
    FLINK = "flink"
    PYTHON = "python"
    SQL = "sql"

class FeatureComputation(Base, BaseModelMixin):
    """Feature computation configuration model."""
    __tablename__ = "feature_computations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id"), nullable=False)
    version_id = Column(UUID(as_uuid=True), ForeignKey("feature_versions.id"), nullable=False)
    
    # Computation configuration
    job_type = Column(SQLEnum(JobType), nullable=False)
    compute_engine = Column(SQLEnum(ComputeEngine), nullable=False)
    schedule = Column(String(100), nullable=True)  # Cron expression for scheduling
    
    # Resource requirements
    cpu_cores = Column(Integer, default=1)
    memory_gb = Column(Integer, default=2)
    timeout_minutes = Column(Integer, default=60)
    
    # Configuration
    config = Column(JSON, nullable=True)  # Engine-specific configuration
    dependencies = Column(JSON, nullable=True)  # Feature dependencies
    output_schema = Column(JSON, nullable=True)  # Expected output schema
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    
    # Relationships
    feature = relationship("Feature")
    version = relationship("FeatureVersion")
    jobs = relationship("ComputationJob", back_populates="computation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_computation_feature', 'feature_id'),
        Index('idx_computation_type', 'job_type'),
        Index('idx_computation_engine', 'compute_engine'),
        Index('idx_computation_active', 'is_active'),
        Index('idx_computation_schedule', 'next_run_at'),
    )

class ComputationJob(Base, BaseModelMixin):
    """Individual computation job execution model."""
    __tablename__ = "computation_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    computation_id = Column(UUID(as_uuid=True), ForeignKey("feature_computations.id"), nullable=False)
    
    # Job identification
    job_id = Column(String(255), nullable=False, unique=True)  # External job ID
    job_name = Column(String(255), nullable=False)
    
    # Execution details
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Resource usage
    cpu_usage = Column(Float, nullable=True)
    memory_usage_gb = Column(Float, nullable=True)
    
    # Results
    records_processed = Column(Integer, nullable=True)
    records_output = Column(Integer, nullable=True)
    error_count = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Input/output
    input_data = Column(JSON, nullable=True)  # Input parameters
    output_data = Column(JSON, nullable=True)  # Output summary
    artifacts = Column(JSON, nullable=True)    # Generated artifacts
    
    # Monitoring
    progress_percentage = Column(Float, default=0.0)
    checkpoint_data = Column(JSON, nullable=True)
    
    # Relationships
    computation = relationship("FeatureComputation", back_populates="jobs")
    
    # Indexes
    __table_args__ = (
        Index('idx_job_computation', 'computation_id'),
        Index('idx_job_status', 'status'),
        Index('idx_job_started', 'started_at'),
        Index('idx_job_external', 'job_id'),
    )

class DataSource(Base, BaseModelMixin):
    """Data source configuration model."""
    __tablename__ = "data_sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source identification
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    source_type = Column(String(100), nullable=False)  # "database", "file", "api", "stream"
    
    # Connection details
    connection_config = Column(JSON, nullable=False)
    schema = Column(JSON, nullable=True)
    
    # Access control
    credentials = Column(JSON, nullable=True)  # Encrypted credentials
    is_encrypted = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Relationships
    lineage_sources = relationship("FeatureLineage", back_populates="source")
    
    # Indexes
    __table_args__ = (
        Index('idx_source_type', 'source_type'),
        Index('idx_source_active', 'is_active'),
    )

# Pydantic models for API
class FeatureComputationCreate(PydanticBaseModel):
    """Model for creating feature computations."""
    feature_id: str = Field(..., description="Feature ID")
    version_id: str = Field(..., description="Feature version ID")
    job_type: JobType = Field(..., description="Job type")
    compute_engine: ComputeEngine = Field(..., description="Compute engine")
    schedule: Optional[str] = Field(None, description="Cron schedule expression")
    cpu_cores: Optional[int] = Field(1, ge=1, description="CPU cores required")
    memory_gb: Optional[int] = Field(2, ge=1, description="Memory in GB")
    timeout_minutes: Optional[int] = Field(60, ge=1, description="Timeout in minutes")
    config: Optional[Dict[str, Any]] = Field(None, description="Engine-specific config")
    dependencies: Optional[Dict[str, Any]] = Field(None, description="Feature dependencies")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output schema")

class FeatureComputationUpdate(PydanticBaseModel):
    """Model for updating feature computations."""
    schedule: Optional[str] = None
    cpu_cores: Optional[int] = Field(None, ge=1)
    memory_gb: Optional[int] = Field(None, ge=1)
    timeout_minutes: Optional[int] = Field(None, ge=1)
    config: Optional[Dict[str, Any]] = None
    dependencies: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class FeatureComputationResponse(PydanticBaseModel):
    """Model for feature computation API responses."""
    id: str
    feature_id: str
    version_id: str
    job_type: JobType
    compute_engine: ComputeEngine
    schedule: Optional[str]
    cpu_cores: int
    memory_gb: int
    timeout_minutes: int
    config: Optional[Dict[str, Any]]
    dependencies: Optional[Dict[str, Any]]
    output_schema: Optional[Dict[str, Any]]
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class ComputationJobCreate(PydanticBaseModel):
    """Model for creating computation jobs."""
    computation_id: str = Field(..., description="Computation ID")
    job_name: str = Field(..., description="Job name")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input parameters")
    max_retries: Optional[int] = Field(3, ge=0, description="Maximum retry attempts")

class ComputationJobResponse(PydanticBaseModel):
    """Model for computation job API responses."""
    id: str
    computation_id: str
    job_id: str
    job_name: str
    status: JobStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    cpu_usage: Optional[float]
    memory_usage_gb: Optional[float]
    records_processed: Optional[int]
    records_output: Optional[int]
    error_count: int
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    retry_count: int
    max_retries: int
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    artifacts: Optional[Dict[str, Any]]
    progress_percentage: float
    checkpoint_data: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class DataSourceCreate(PydanticBaseModel):
    """Model for creating data sources."""
    name: str = Field(..., min_length=1, max_length=255, description="Data source name")
    description: Optional[str] = Field(None, description="Data source description")
    source_type: str = Field(..., description="Source type")
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration")
    schema: Optional[Dict[str, Any]] = Field(None, description="Data schema")
    credentials: Optional[Dict[str, Any]] = Field(None, description="Access credentials")

class DataSourceUpdate(PydanticBaseModel):
    """Model for updating data sources."""
    description: Optional[str] = None
    connection_config: Optional[Dict[str, Any]] = None
    schema: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class DataSourceResponse(PydanticBaseModel):
    """Model for data source API responses."""
    id: str
    name: str
    description: Optional[str]
    source_type: str
    connection_config: Dict[str, Any]
    schema: Optional[Dict[str, Any]]
    is_encrypted: bool
    is_active: bool
    last_accessed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime 