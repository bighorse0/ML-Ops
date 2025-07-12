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

class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    """Alert status."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLOSED = "closed"

class DriftType(str, Enum):
    """Types of feature drift."""
    DISTRIBUTION = "distribution"
    SCHEMA = "schema"
    FRESHNESS = "freshness"
    QUALITY = "quality"

class QualityMetricType(str, Enum):
    """Data quality metric types."""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"

class FeatureDrift(Base, BaseModelMixin):
    """Feature drift detection model."""
    __tablename__ = "feature_drift"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id"), nullable=False)
    version_id = Column(UUID(as_uuid=True), ForeignKey("feature_versions.id"), nullable=False)
    
    # Drift detection
    drift_type = Column(SQLEnum(DriftType), nullable=False)
    drift_score = Column(Float, nullable=False)  # 0-1, higher = more drift
    threshold = Column(Float, nullable=False)  # Threshold for alerting
    
    # Statistical measures
    reference_stats = Column(JSON, nullable=True)  # Reference distribution stats
    current_stats = Column(JSON, nullable=True)    # Current distribution stats
    p_value = Column(Float, nullable=True)         # Statistical significance
    
    # Detection metadata
    detection_method = Column(String(100), nullable=True)  # e.g., "ks_test", "chi_square"
    window_size = Column(String(50), nullable=True)        # e.g., "7d", "24h"
    sample_size = Column(Integer, nullable=True)
    
    # Alerting
    is_alert_triggered = Column(Boolean, default=False)
    alert_severity = Column(SQLEnum(AlertSeverity), nullable=True)
    
    # Relationships
    feature = relationship("Feature")
    version = relationship("FeatureVersion")
    
    # Indexes
    __table_args__ = (
        Index('idx_drift_feature_time', 'feature_id', 'created_at'),
        Index('idx_drift_type', 'drift_type'),
        Index('idx_drift_score', 'drift_score'),
        Index('idx_drift_alert', 'is_alert_triggered'),
    )

class DataQuality(Base, BaseModelMixin):
    """Data quality metrics model."""
    __tablename__ = "data_quality"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id"), nullable=False)
    version_id = Column(UUID(as_uuid=True), ForeignKey("feature_versions.id"), nullable=False)
    
    # Quality metrics
    metric_type = Column(SQLEnum(QualityMetricType), nullable=False)
    metric_value = Column(Float, nullable=False)  # 0-1, higher = better quality
    threshold = Column(Float, nullable=False)     # Minimum acceptable quality
    
    # Measurement details
    measurement_window = Column(String(50), nullable=True)  # e.g., "1h", "24h"
    sample_size = Column(Integer, nullable=True)
    total_records = Column(Integer, nullable=True)
    failed_records = Column(Integer, nullable=True)
    
    # Additional context
    details = Column(JSON, nullable=True)  # Additional metric-specific details
    error_messages = Column(JSON, nullable=True)  # Error details if any
    
    # Alerting
    is_alert_triggered = Column(Boolean, default=False)
    alert_severity = Column(SQLEnum(AlertSeverity), nullable=True)
    
    # Relationships
    feature = relationship("Feature")
    version = relationship("FeatureVersion")
    
    # Indexes
    __table_args__ = (
        Index('idx_quality_feature_time', 'feature_id', 'created_at'),
        Index('idx_quality_type', 'metric_type'),
        Index('idx_quality_value', 'metric_value'),
        Index('idx_quality_alert', 'is_alert_triggered'),
    )

class MonitoringAlert(Base, BaseModelMixin):
    """Monitoring alert model."""
    __tablename__ = "monitoring_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Alert identification
    alert_type = Column(String(100), nullable=False)  # "drift", "quality", "freshness", etc.
    source_id = Column(UUID(as_uuid=True), nullable=True)  # ID of the source (feature, drift, etc.)
    source_type = Column(String(50), nullable=True)        # Type of source
    
    # Alert details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.OPEN)
    
    # Alert data
    alert_data = Column(JSON, nullable=True)  # Additional alert-specific data
    metrics = Column(JSON, nullable=True)     # Related metrics
    
    # Resolution
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Notification
    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(JSON, nullable=True)  # ["email", "slack", "webhook"]
    
    # Indexes
    __table_args__ = (
        Index('idx_alert_type', 'alert_type'),
        Index('idx_alert_severity', 'severity'),
        Index('idx_alert_status', 'status'),
        Index('idx_alert_created', 'created_at'),
        Index('idx_alert_source', 'source_type', 'source_id'),
    )

class FeatureFreshness(Base, BaseModelMixin):
    """Feature freshness monitoring model."""
    __tablename__ = "feature_freshness"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("features.id"), nullable=False)
    version_id = Column(UUID(as_uuid=True), ForeignKey("feature_versions.id"), nullable=False)
    
    # Freshness metrics
    last_update_time = Column(DateTime, nullable=False)
    expected_freshness = Column(String(50), nullable=True)  # e.g., "1h", "24h"
    actual_freshness = Column(Integer, nullable=True)       # seconds since last update
    
    # SLA compliance
    sla_breach = Column(Boolean, default=False)
    sla_breach_duration = Column(Integer, nullable=True)    # seconds of SLA breach
    
    # Alerting
    is_alert_triggered = Column(Boolean, default=False)
    alert_severity = Column(SQLEnum(AlertSeverity), nullable=True)
    
    # Relationships
    feature = relationship("Feature")
    version = relationship("FeatureVersion")
    
    # Indexes
    __table_args__ = (
        Index('idx_freshness_feature_time', 'feature_id', 'created_at'),
        Index('idx_freshness_breach', 'sla_breach'),
        Index('idx_freshness_alert', 'is_alert_triggered'),
    )

# Pydantic models for API
class FeatureDriftCreate(PydanticBaseModel):
    """Model for creating feature drift records."""
    feature_id: str = Field(..., description="Feature ID")
    version_id: str = Field(..., description="Feature version ID")
    drift_type: DriftType = Field(..., description="Type of drift detected")
    drift_score: float = Field(..., ge=0, le=1, description="Drift score (0-1)")
    threshold: float = Field(..., ge=0, le=1, description="Alert threshold")
    reference_stats: Optional[Dict[str, Any]] = Field(None, description="Reference statistics")
    current_stats: Optional[Dict[str, Any]] = Field(None, description="Current statistics")
    p_value: Optional[float] = Field(None, ge=0, le=1, description="Statistical p-value")
    detection_method: Optional[str] = Field(None, description="Detection method used")
    window_size: Optional[str] = Field(None, description="Analysis window size")
    sample_size: Optional[int] = Field(None, ge=1, description="Sample size used")

class FeatureDriftResponse(PydanticBaseModel):
    """Model for feature drift API responses."""
    id: str
    feature_id: str
    version_id: str
    drift_type: DriftType
    drift_score: float
    threshold: float
    reference_stats: Optional[Dict[str, Any]]
    current_stats: Optional[Dict[str, Any]]
    p_value: Optional[float]
    detection_method: Optional[str]
    window_size: Optional[str]
    sample_size: Optional[int]
    is_alert_triggered: bool
    alert_severity: Optional[AlertSeverity]
    created_at: datetime
    updated_at: datetime

class DataQualityCreate(PydanticBaseModel):
    """Model for creating data quality records."""
    feature_id: str = Field(..., description="Feature ID")
    version_id: str = Field(..., description="Feature version ID")
    metric_type: QualityMetricType = Field(..., description="Quality metric type")
    metric_value: float = Field(..., ge=0, le=1, description="Quality score (0-1)")
    threshold: float = Field(..., ge=0, le=1, description="Quality threshold")
    measurement_window: Optional[str] = Field(None, description="Measurement window")
    sample_size: Optional[int] = Field(None, ge=1, description="Sample size")
    total_records: Optional[int] = Field(None, ge=0, description="Total records processed")
    failed_records: Optional[int] = Field(None, ge=0, description="Failed records")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    error_messages: Optional[Dict[str, Any]] = Field(None, description="Error messages")

class DataQualityResponse(PydanticBaseModel):
    """Model for data quality API responses."""
    id: str
    feature_id: str
    version_id: str
    metric_type: QualityMetricType
    metric_value: float
    threshold: float
    measurement_window: Optional[str]
    sample_size: Optional[int]
    total_records: Optional[int]
    failed_records: Optional[int]
    details: Optional[Dict[str, Any]]
    error_messages: Optional[Dict[str, Any]]
    is_alert_triggered: bool
    alert_severity: Optional[AlertSeverity]
    created_at: datetime
    updated_at: datetime

class MonitoringAlertCreate(PydanticBaseModel):
    """Model for creating monitoring alerts."""
    alert_type: str = Field(..., description="Type of alert")
    source_id: Optional[str] = Field(None, description="Source entity ID")
    source_type: Optional[str] = Field(None, description="Source entity type")
    title: str = Field(..., description="Alert title")
    description: Optional[str] = Field(None, description="Alert description")
    severity: AlertSeverity = Field(..., description="Alert severity")
    alert_data: Optional[Dict[str, Any]] = Field(None, description="Alert-specific data")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Related metrics")
    notification_channels: Optional[list] = Field(None, description="Notification channels")

class MonitoringAlertResponse(PydanticBaseModel):
    """Model for monitoring alert API responses."""
    id: str
    alert_type: str
    source_id: Optional[str]
    source_type: Optional[str]
    title: str
    description: Optional[str]
    severity: AlertSeverity
    status: AlertStatus
    alert_data: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolution_notes: Optional[str]
    notification_sent: bool
    notification_channels: Optional[list]
    created_at: datetime
    updated_at: datetime 