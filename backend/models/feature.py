from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import (
    Column, String, Text, JSON, Float, Integer, DateTime, 
    ForeignKey, Index, Boolean, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

from .base import Base, BaseModelMixin, PydanticBaseModel, Field

class DataType(str, Enum):
    """Supported data types for features."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    ARRAY = "array"
    OBJECT = "object"

class FeatureStatus(str, Enum):
    """Feature lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"

class ServingType(str, Enum):
    """Feature serving types."""
    ONLINE = "online"
    BATCH = "batch"
    STREAMING = "streaming"

class Feature(Base, BaseModelMixin):
    """Core feature definition model."""
    __tablename__ = "features"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    data_type = Column(SQLEnum(DataType), nullable=False)
    tags = Column(JSON, default=list)
    owner = Column(String(255), nullable=False)
    freshness_sla = Column(String(50), nullable=True)  # e.g., "1h", "24h"
    status = Column(SQLEnum(FeatureStatus), default=FeatureStatus.DRAFT)
    serving_type = Column(SQLEnum(ServingType), nullable=False)
    
    # Schema definition
    schema = Column(JSON, nullable=True)
    
    # Transformation logic
    transformation = Column(Text, nullable=True)
    transformation_type = Column(String(50), nullable=True)  # "sql", "python", "spark"
    
    # Performance and monitoring
    expected_latency_ms = Column(Integer, nullable=True)
    expected_throughput_rps = Column(Integer, nullable=True)
    
    # Relationships
    versions = relationship("FeatureVersion", back_populates="feature", cascade="all, delete-orphan")
    values = relationship("FeatureValue", back_populates="feature", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_feature_org_name', 'organization_id', 'name', unique=True),
        Index('idx_feature_status', 'status'),
        Index('idx_feature_owner', 'owner'),
    )

class FeatureVersion(Base, BaseModelMixin):
    """Feature versioning model."""
    __tablename__ = "feature_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id"), nullable=False)
    version = Column(String(50), nullable=False)  # e.g., "v1", "v2"
    description = Column(Text, nullable=True)
    
    # Version-specific configuration
    schema = Column(JSON, nullable=False)
    transformation = Column(Text, nullable=True)
    transformation_type = Column(String(50), nullable=True)
    
    # Performance metrics
    expected_latency_ms = Column(Integer, nullable=True)
    expected_throughput_rps = Column(Integer, nullable=True)
    
    # Version status
    is_active = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    
    # Relationships
    feature = relationship("Feature", back_populates="versions")
    
    # Indexes
    __table_args__ = (
        Index('idx_feature_version', 'feature_id', 'version', unique=True),
        Index('idx_version_active', 'is_active'),
    )

class FeatureValue(Base, BaseModelMixin):
    """Feature value storage model."""
    __tablename__ = "feature_values"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id"), nullable=False)
    version_id = Column(UUID(as_uuid=True), ForeignKey("feature_versions.id"), nullable=False)
    
    # Entity identification
    entity_id = Column(String(255), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    
    # Value storage
    value = Column(JSON, nullable=False)
    value_type = Column(SQLEnum(DataType), nullable=False)
    
    # Timestamp for point-in-time queries
    effective_timestamp = Column(DateTime, nullable=False, index=True)
    created_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Metadata
    source = Column(String(255), nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Relationships
    feature = relationship("Feature", back_populates="values")
    version = relationship("FeatureVersion")
    
    # Indexes
    __table_args__ = (
        Index('idx_feature_entity_time', 'feature_id', 'entity_id', 'effective_timestamp'),
        Index('idx_entity_type_time', 'entity_type', 'effective_timestamp'),
        Index('idx_value_timestamp', 'effective_timestamp'),
    )

# Pydantic models for API
class FeatureCreate(PydanticBaseModel):
    """Model for creating a new feature."""
    name: str = Field(..., min_length=1, max_length=255, description="Feature name")
    description: Optional[str] = Field(None, description="Feature description")
    data_type: DataType = Field(..., description="Feature data type")
    tags: List[str] = Field(default_factory=list, description="Feature tags")
    owner: str = Field(..., description="Feature owner")
    freshness_sla: Optional[str] = Field(None, description="Freshness SLA")
    serving_type: ServingType = Field(..., description="Serving type")
    schema: Optional[Dict[str, Any]] = Field(None, description="Feature schema")
    transformation: Optional[str] = Field(None, description="Transformation logic")
    transformation_type: Optional[str] = Field(None, description="Transformation type")
    expected_latency_ms: Optional[int] = Field(None, ge=0, description="Expected latency in ms")
    expected_throughput_rps: Optional[int] = Field(None, ge=0, description="Expected throughput in RPS")

class FeatureUpdate(PydanticBaseModel):
    """Model for updating a feature."""
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    owner: Optional[str] = None
    freshness_sla: Optional[str] = None
    status: Optional[FeatureStatus] = None
    schema: Optional[Dict[str, Any]] = None
    transformation: Optional[str] = None
    transformation_type: Optional[str] = None
    expected_latency_ms: Optional[int] = Field(None, ge=0)
    expected_throughput_rps: Optional[int] = Field(None, ge=0)

class FeatureResponse(PydanticBaseModel):
    """Model for feature API responses."""
    id: str
    name: str
    description: Optional[str]
    data_type: DataType
    tags: List[str]
    owner: str
    freshness_sla: Optional[str]
    status: FeatureStatus
    serving_type: ServingType
    schema: Optional[Dict[str, Any]]
    transformation: Optional[str]
    transformation_type: Optional[str]
    expected_latency_ms: Optional[int]
    expected_throughput_rps: Optional[int]
    created_at: datetime
    updated_at: datetime
    organization_id: str

class FeatureValueCreate(PydanticBaseModel):
    """Model for creating feature values."""
    entity_id: str = Field(..., description="Entity identifier")
    entity_type: str = Field(..., description="Entity type")
    value: Any = Field(..., description="Feature value")
    value_type: DataType = Field(..., description="Value data type")
    effective_timestamp: datetime = Field(..., description="Effective timestamp")
    source: Optional[str] = Field(None, description="Value source")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")

class FeatureValueResponse(PydanticBaseModel):
    """Model for feature value API responses."""
    id: str
    feature_id: str
    version_id: str
    entity_id: str
    entity_type: str
    value: Any
    value_type: DataType
    effective_timestamp: datetime
    created_timestamp: datetime
    source: Optional[str]
    confidence_score: Optional[float]
    created_at: datetime
    updated_at: datetime 