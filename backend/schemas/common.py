from typing import List, Optional, Any, Generic, TypeVar, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=50, ge=1, le=1000, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Schema for paginated responses."""
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class APIResponse(BaseModel, Generic[T]):
    """Schema for standard API responses."""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    error_code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResponse(BaseModel):
    """Schema for health check responses."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]


class SortOrder(str, Enum):
    """Enum for sort order."""
    ASC = "asc"
    DESC = "desc"


class SortField(BaseModel):
    """Schema for sort field."""
    field: str
    order: SortOrder = SortOrder.ASC


class FilterOperator(str, Enum):
    """Enum for filter operators."""
    EQ = "eq"  # equals
    NE = "ne"  # not equals
    GT = "gt"  # greater than
    GTE = "gte"  # greater than or equal
    LT = "lt"  # less than
    LTE = "lte"  # less than or equal
    IN = "in"  # in list
    NOT_IN = "not_in"  # not in list
    LIKE = "like"  # like (for strings)
    ILIKE = "ilike"  # case insensitive like
    IS_NULL = "is_null"  # is null
    IS_NOT_NULL = "is_not_null"  # is not null


class FilterCondition(BaseModel):
    """Schema for filter condition."""
    field: str
    operator: FilterOperator
    value: Optional[Any] = None


class QueryParams(BaseModel):
    """Schema for query parameters."""
    pagination: Optional[PaginationParams] = None
    sort: Optional[List[SortField]] = None
    filters: Optional[List[FilterCondition]] = None
    search: Optional[str] = None


class AuditInfo(BaseModel):
    """Schema for audit information."""
    created_at: datetime
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class Metadata(BaseModel):
    """Schema for metadata."""
    key: str
    value: Any
    type: str = "string"  # string, number, boolean, json


class Tag(BaseModel):
    """Schema for tags."""
    key: str
    value: str


class Permission(str, Enum):
    """Enum for permissions."""
    # Feature permissions
    FEATURES_READ = "features:read"
    FEATURES_WRITE = "features:write"
    FEATURES_DELETE = "features:delete"
    
    # Feature value permissions
    FEATURE_VALUES_READ = "feature_values:read"
    FEATURE_VALUES_WRITE = "feature_values:write"
    FEATURE_VALUES_DELETE = "feature_values:delete"
    
    # User permissions
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"
    
    # Organization permissions
    ORGANIZATIONS_READ = "organizations:read"
    ORGANIZATIONS_WRITE = "organizations:write"
    ORGANIZATIONS_DELETE = "organizations:delete"
    
    # Monitoring permissions
    MONITORING_READ = "monitoring:read"
    MONITORING_WRITE = "monitoring:write"
    
    # Computation permissions
    COMPUTATION_READ = "computation:read"
    COMPUTATION_WRITE = "computation:write"
    COMPUTATION_EXECUTE = "computation:execute"
    
    # Lineage permissions
    LINEAGE_READ = "lineage:read"
    LINEAGE_WRITE = "lineage:write"


class Role(str, Enum):
    """Enum for user roles."""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"
    DEVELOPER = "developer"
    DATA_SCIENTIST = "data_scientist"
    MLOPS_ENGINEER = "mlops_engineer"


class Status(str, Enum):
    """Enum for status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    FAILED = "failed"
    SUCCESS = "success"
    RUNNING = "running"
    CANCELLED = "cancelled"


class DataType(str, Enum):
    """Enum for data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    ARRAY = "array"


class FeatureType(str, Enum):
    """Enum for feature types."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    EMBEDDING = "embedding"
    TIME_SERIES = "time_series"
    COMPLEX = "complex"


class ServingMode(str, Enum):
    """Enum for serving modes."""
    ONLINE = "online"
    OFFLINE = "offline"
    BATCH = "batch"
    STREAMING = "streaming"


class StorageType(str, Enum):
    """Enum for storage types."""
    POSTGRESQL = "postgresql"
    REDIS = "redis"
    CLICKHOUSE = "clickhouse"
    S3 = "s3"
    LOCAL = "local"


class ComputationType(str, Enum):
    """Enum for computation types."""
    AGGREGATION = "aggregation"
    TRANSFORMATION = "transformation"
    JOIN = "join"
    FILTER = "filter"
    CUSTOM = "custom"


class MonitoringMetric(str, Enum):
    """Enum for monitoring metrics."""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    DATA_QUALITY = "data_quality"
    FRESHNESS = "freshness"
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"


class AlertSeverity(str, Enum):
    """Enum for alert severities."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical" 