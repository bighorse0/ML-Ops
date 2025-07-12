from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import (
    Column, String, Text, JSON, DateTime, ForeignKey, 
    Index, Boolean, Enum as SQLEnum, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

from .base import Base, BaseModelMixin, PydanticBaseModel, Field

class LineageType(str, Enum):
    """Types of lineage relationships."""
    DEPENDS_ON = "depends_on"
    DERIVED_FROM = "derived_from"
    CONSUMED_BY = "consumed_by"
    GENERATES = "generates"

class LineageStatus(str, Enum):
    """Lineage status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"

class FeatureLineage(Base, BaseModelMixin):
    """Feature lineage tracking model."""
    __tablename__ = "feature_lineage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source and target
    source_id = Column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=True)
    source_type = Column(String(50), nullable=False)  # "data_source", "feature", "computation"
    source_name = Column(String(255), nullable=False)
    
    target_id = Column(UUID(as_uuid=True), ForeignKey("features.id"), nullable=True)
    target_type = Column(String(50), nullable=False)  # "feature", "computation", "model"
    target_name = Column(String(255), nullable=False)
    
    # Relationship details
    lineage_type = Column(SQLEnum(LineageType), nullable=False)
    status = Column(SQLEnum(LineageStatus), default=LineageStatus.ACTIVE)
    
    # Transformation details
    transformation_logic = Column(Text, nullable=True)
    transformation_type = Column(String(50), nullable=True)  # "sql", "python", "spark"
    
    # Metadata
    confidence_score = Column(Float, nullable=True)  # 0-1, confidence in lineage
    last_verified_at = Column(DateTime, nullable=True)
    verification_method = Column(String(100), nullable=True)
    
    # Additional context
    metadata = Column(JSON, nullable=True)  # Additional lineage metadata
    tags = Column(JSON, default=list)
    
    # Relationships
    source = relationship("DataSource", back_populates="lineage_sources")
    target_feature = relationship("Feature")
    
    # Indexes
    __table_args__ = (
        Index('idx_lineage_source', 'source_type', 'source_id'),
        Index('idx_lineage_target', 'target_type', 'target_id'),
        Index('idx_lineage_type', 'lineage_type'),
        Index('idx_lineage_status', 'status'),
        Index('idx_lineage_confidence', 'confidence_score'),
    )

class DataLineage(Base, BaseModelMixin):
    """Data lineage for tracking data flow."""
    __tablename__ = "data_lineage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Data identification
    dataset_name = Column(String(255), nullable=False)
    dataset_version = Column(String(50), nullable=True)
    table_name = Column(String(255), nullable=True)
    column_name = Column(String(255), nullable=True)
    
    # Source tracking
    source_system = Column(String(100), nullable=True)
    source_table = Column(String(255), nullable=True)
    source_column = Column(String(255), nullable=True)
    
    # Processing details
    processing_job = Column(String(255), nullable=True)
    processing_timestamp = Column(DateTime, nullable=True)
    
    # Quality metrics
    data_quality_score = Column(Float, nullable=True)
    freshness_score = Column(Float, nullable=True)
    
    # Metadata
    schema_info = Column(JSON, nullable=True)
    business_metadata = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_data_lineage_dataset', 'dataset_name', 'dataset_version'),
        Index('idx_data_lineage_table', 'table_name'),
        Index('idx_data_lineage_column', 'column_name'),
        Index('idx_data_lineage_source', 'source_system'),
        Index('idx_data_lineage_processing', 'processing_job'),
    )

class ModelLineage(Base, BaseModelMixin):
    """Model lineage for tracking ML model dependencies."""
    __tablename__ = "model_lineage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Model identification
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(50), nullable=False)
    model_type = Column(String(100), nullable=True)  # "classification", "regression", etc.
    
    # Feature dependencies
    feature_dependencies = Column(JSON, nullable=True)  # List of feature IDs
    feature_versions = Column(JSON, nullable=True)      # Feature version mapping
    
    # Training details
    training_job_id = Column(String(255), nullable=True)
    training_data_sources = Column(JSON, nullable=True)
    training_parameters = Column(JSON, nullable=True)
    
    # Performance metrics
    model_performance = Column(JSON, nullable=True)
    feature_importance = Column(JSON, nullable=True)
    
    # Deployment info
    deployment_environment = Column(String(100), nullable=True)
    deployment_timestamp = Column(DateTime, nullable=True)
    
    # Relationships
    feature_lineages = relationship("FeatureLineage", backref="model_lineage")
    
    # Indexes
    __table_args__ = (
        Index('idx_model_lineage_name', 'model_name', 'model_version'),
        Index('idx_model_lineage_type', 'model_type'),
        Index('idx_model_lineage_training', 'training_job_id'),
        Index('idx_model_lineage_deployment', 'deployment_environment'),
    )

# Pydantic models for API
class FeatureLineageCreate(PydanticBaseModel):
    """Model for creating feature lineage."""
    source_id: Optional[str] = Field(None, description="Source entity ID")
    source_type: str = Field(..., description="Source entity type")
    source_name: str = Field(..., description="Source entity name")
    target_id: Optional[str] = Field(None, description="Target entity ID")
    target_type: str = Field(..., description="Target entity type")
    target_name: str = Field(..., description="Target entity name")
    lineage_type: LineageType = Field(..., description="Type of lineage relationship")
    transformation_logic: Optional[str] = Field(None, description="Transformation logic")
    transformation_type: Optional[str] = Field(None, description="Transformation type")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")
    verification_method: Optional[str] = Field(None, description="Verification method")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[list] = Field(default_factory=list, description="Lineage tags")

class FeatureLineageUpdate(PydanticBaseModel):
    """Model for updating feature lineage."""
    lineage_type: Optional[LineageType] = None
    status: Optional[LineageStatus] = None
    transformation_logic: Optional[str] = None
    transformation_type: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    verification_method: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[list] = None

class FeatureLineageResponse(PydanticBaseModel):
    """Model for feature lineage API responses."""
    id: str
    source_id: Optional[str]
    source_type: str
    source_name: str
    target_id: Optional[str]
    target_type: str
    target_name: str
    lineage_type: LineageType
    status: LineageStatus
    transformation_logic: Optional[str]
    transformation_type: Optional[str]
    confidence_score: Optional[float]
    last_verified_at: Optional[datetime]
    verification_method: Optional[str]
    metadata: Optional[Dict[str, Any]]
    tags: list
    created_at: datetime
    updated_at: datetime

class DataLineageCreate(PydanticBaseModel):
    """Model for creating data lineage."""
    dataset_name: str = Field(..., description="Dataset name")
    dataset_version: Optional[str] = Field(None, description="Dataset version")
    table_name: Optional[str] = Field(None, description="Table name")
    column_name: Optional[str] = Field(None, description="Column name")
    source_system: Optional[str] = Field(None, description="Source system")
    source_table: Optional[str] = Field(None, description="Source table")
    source_column: Optional[str] = Field(None, description="Source column")
    processing_job: Optional[str] = Field(None, description="Processing job ID")
    processing_timestamp: Optional[datetime] = Field(None, description="Processing timestamp")
    data_quality_score: Optional[float] = Field(None, ge=0, le=1, description="Data quality score")
    freshness_score: Optional[float] = Field(None, ge=0, le=1, description="Freshness score")
    schema_info: Optional[Dict[str, Any]] = Field(None, description="Schema information")
    business_metadata: Optional[Dict[str, Any]] = Field(None, description="Business metadata")

class DataLineageResponse(PydanticBaseModel):
    """Model for data lineage API responses."""
    id: str
    dataset_name: str
    dataset_version: Optional[str]
    table_name: Optional[str]
    column_name: Optional[str]
    source_system: Optional[str]
    source_table: Optional[str]
    source_column: Optional[str]
    processing_job: Optional[str]
    processing_timestamp: Optional[datetime]
    data_quality_score: Optional[float]
    freshness_score: Optional[float]
    schema_info: Optional[Dict[str, Any]]
    business_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class ModelLineageCreate(PydanticBaseModel):
    """Model for creating model lineage."""
    model_name: str = Field(..., description="Model name")
    model_version: str = Field(..., description="Model version")
    model_type: Optional[str] = Field(None, description="Model type")
    feature_dependencies: Optional[list] = Field(None, description="Feature dependency IDs")
    feature_versions: Optional[Dict[str, str]] = Field(None, description="Feature version mapping")
    training_job_id: Optional[str] = Field(None, description="Training job ID")
    training_data_sources: Optional[list] = Field(None, description="Training data sources")
    training_parameters: Optional[Dict[str, Any]] = Field(None, description="Training parameters")
    model_performance: Optional[Dict[str, Any]] = Field(None, description="Model performance metrics")
    feature_importance: Optional[Dict[str, Any]] = Field(None, description="Feature importance")
    deployment_environment: Optional[str] = Field(None, description="Deployment environment")
    deployment_timestamp: Optional[datetime] = Field(None, description="Deployment timestamp")

class ModelLineageResponse(PydanticBaseModel):
    """Model for model lineage API responses."""
    id: str
    model_name: str
    model_version: str
    model_type: Optional[str]
    feature_dependencies: Optional[list]
    feature_versions: Optional[Dict[str, str]]
    training_job_id: Optional[str]
    training_data_sources: Optional[list]
    training_parameters: Optional[Dict[str, Any]]
    model_performance: Optional[Dict[str, Any]]
    feature_importance: Optional[Dict[str, Any]]
    deployment_environment: Optional[str]
    deployment_timestamp: Optional[datetime]
    created_at: datetime
    updated_at: datetime 