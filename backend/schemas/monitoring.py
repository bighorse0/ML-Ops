from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from .common import Status, AlertSeverity


class DataQualityMetricType(str, Enum):
    """Enum for data quality metric types."""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    INTEGRITY = "integrity"
    FRESHNESS = "freshness"


class DataQualityMetricCreate(BaseModel):
    """Schema for creating a data quality metric."""
    feature_id: int = Field(..., description="ID of the feature")
    metric_type: DataQualityMetricType = Field(..., description="Type of quality metric")
    value: float = Field(..., ge=0, le=100, description="Quality score (0-100)")
    threshold: float = Field(..., ge=0, le=100, description="Quality threshold")
    status: Status = Field(default=Status.ACTIVE, description="Metric status")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    timestamp: Optional[datetime] = Field(default=None, description="Metric timestamp")

    @validator('value', 'threshold')
    def validate_quality_score(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Quality score must be between 0 and 100')
        return v


class DataQualityMetricResponse(BaseModel):
    """Schema for data quality metric response."""
    id: int
    feature_id: int
    metric_type: DataQualityMetricType
    value: float
    threshold: float
    status: Status
    metadata: Optional[Dict[str, Any]]
    timestamp: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    organization_id: int

    class Config:
        from_attributes = True


class PerformanceMetricCreate(BaseModel):
    """Schema for creating a performance metric."""
    service_name: str = Field(..., description="Name of the service")
    metric_name: str = Field(..., description="Name of the metric")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Unit of measurement")
    labels: Optional[Dict[str, str]] = Field(default=None, description="Metric labels")
    timestamp: Optional[datetime] = Field(default=None, description="Metric timestamp")

    @validator('service_name', 'metric_name')
    def validate_names(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        return v.strip()


class PerformanceMetricResponse(BaseModel):
    """Schema for performance metric response."""
    id: int
    service_name: str
    metric_name: str
    value: float
    unit: str
    labels: Optional[Dict[str, str]]
    timestamp: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    organization_id: int

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    """Schema for creating an alert."""
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")
    severity: AlertSeverity = Field(..., description="Alert severity")
    source: str = Field(..., description="Alert source")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    status: Status = Field(default=Status.ACTIVE, description="Alert status")

    @validator('title', 'description', 'source')
    def validate_required_fields(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Field cannot be empty')
        return v.strip()


class AlertResponse(BaseModel):
    """Schema for alert response."""
    id: int
    title: str
    description: str
    severity: AlertSeverity
    source: str
    metadata: Optional[Dict[str, Any]]
    status: Status
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    organization_id: int

    class Config:
        from_attributes = True


class AlertRuleCreate(BaseModel):
    """Schema for creating an alert rule."""
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    condition: Dict[str, Any] = Field(..., description="Alert condition")
    severity: AlertSeverity = Field(..., description="Alert severity")
    is_active: bool = Field(default=True, description="Whether rule is active")

    @validator('name', 'description')
    def validate_required_fields(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Field cannot be empty')
        return v.strip()

    @validator('condition')
    def validate_condition(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Condition must be a dictionary')
        required_keys = ['metric', 'operator', 'threshold']
        for key in required_keys:
            if key not in v:
                raise ValueError(f'Condition must contain {key}')
        return v


class AlertRuleResponse(BaseModel):
    """Schema for alert rule response."""
    id: int
    name: str
    description: str
    condition: Dict[str, Any]
    severity: AlertSeverity
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    organization_id: int

    class Config:
        from_attributes = True


class MonitoringDashboard(BaseModel):
    """Schema for monitoring dashboard data."""
    recent_quality_metrics: List[DataQualityMetricResponse]
    recent_performance_metrics: List[PerformanceMetricResponse]
    active_alerts: List[AlertResponse]
    summary: Dict[str, Any]


class MetricQuery(BaseModel):
    """Schema for metric query parameters."""
    metric_name: str
    start_timestamp: datetime
    end_timestamp: datetime
    interval: str = Field(default="1h", description="Time interval for aggregation")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")

    @validator('interval')
    def validate_interval(cls, v):
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '6h', '12h', '1d', '7d']
        if v not in valid_intervals:
            raise ValueError(f'Interval must be one of: {", ".join(valid_intervals)}')
        return v

    @validator('end_timestamp')
    def validate_timestamp_range(cls, v, values):
        if 'start_timestamp' in values:
            if v <= values['start_timestamp']:
                raise ValueError('End timestamp must be after start timestamp')
        return v


class TimeSeriesData(BaseModel):
    """Schema for time series data."""
    timestamp: datetime
    value: float
    labels: Optional[Dict[str, str]] = None


class MetricResponse(BaseModel):
    """Schema for metric response."""
    metric_name: str
    start_timestamp: datetime
    end_timestamp: datetime
    interval: str
    data: List[TimeSeriesData]


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]


class DataQualityReport(BaseModel):
    """Schema for data quality report."""
    feature_id: int
    report_date: datetime
    overall_score: float
    metrics: Dict[str, float]
    issues: List[Dict[str, Any]]
    recommendations: List[str]


class PerformanceReport(BaseModel):
    """Schema for performance report."""
    service_name: str
    report_date: datetime
    metrics: Dict[str, List[TimeSeriesData]]
    summary: Dict[str, Any]
    alerts: List[AlertResponse]


class MonitoringConfig(BaseModel):
    """Schema for monitoring configuration."""
    data_quality_enabled: bool = True
    performance_monitoring_enabled: bool = True
    alerting_enabled: bool = True
    retention_days: int = Field(default=90, ge=1, le=365)
    sampling_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    thresholds: Dict[str, float] = Field(default_factory=dict) 