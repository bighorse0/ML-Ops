from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class FeatureValueCreate(BaseModel):
    """Schema for creating a feature value."""
    feature_id: int = Field(..., description="ID of the feature")
    entity_id: str = Field(..., description="Entity identifier")
    value: Union[str, int, float, bool, Dict[str, Any]] = Field(..., description="Feature value")
    timestamp: datetime = Field(..., description="Timestamp when the value was recorded")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    @validator('entity_id')
    def validate_entity_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Entity ID cannot be empty')
        return v.strip()

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v > datetime.utcnow():
            raise ValueError('Timestamp cannot be in the future')
        return v


class FeatureValueUpdate(BaseModel):
    """Schema for updating a feature value."""
    value: Optional[Union[str, int, float, bool, Dict[str, Any]]] = Field(None, description="Feature value")
    timestamp: Optional[datetime] = Field(None, description="Timestamp when the value was recorded")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v and v > datetime.utcnow():
            raise ValueError('Timestamp cannot be in the future')
        return v


class FeatureValueResponse(BaseModel):
    """Schema for feature value response."""
    id: int
    feature_id: int
    entity_id: str
    value: Union[str, int, float, bool, Dict[str, Any]]
    timestamp: datetime
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    organization_id: int

    class Config:
        from_attributes = True


class FeatureValueBatchCreate(BaseModel):
    """Schema for batch creating feature values."""
    feature_values: List[FeatureValueCreate] = Field(..., description="List of feature values to create")

    @validator('feature_values')
    def validate_batch_size(cls, v):
        if len(v) > 1000:
            raise ValueError('Batch size cannot exceed 1000 values')
        if len(v) == 0:
            raise ValueError('Batch cannot be empty')
        return v

    @validator('feature_values')
    def validate_unique_combinations(cls, v):
        """Ensure no duplicate feature_id, entity_id, timestamp combinations."""
        combinations = set()
        for fv in v:
            key = (fv.feature_id, fv.entity_id, fv.timestamp)
            if key in combinations:
                raise ValueError(f'Duplicate feature value: feature_id={fv.feature_id}, entity_id={fv.entity_id}, timestamp={fv.timestamp}')
            combinations.add(key)
        return v


class FeatureValueBatchResponse(BaseModel):
    """Schema for batch feature value response."""
    created_count: int
    feature_values: List[FeatureValueResponse]


class FeatureValueQuery(BaseModel):
    """Schema for querying feature values for serving."""
    feature_ids: List[int] = Field(..., description="List of feature IDs to retrieve")
    entity_ids: List[str] = Field(..., description="List of entity IDs to retrieve values for")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Point-in-time for feature values")

    @validator('feature_ids')
    def validate_feature_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one feature ID must be provided')
        if len(v) > 100:
            raise ValueError('Cannot query more than 100 features at once')
        return v

    @validator('entity_ids')
    def validate_entity_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one entity ID must be provided')
        if len(v) > 1000:
            raise ValueError('Cannot query more than 1000 entities at once')
        return v

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v > datetime.utcnow():
            raise ValueError('Timestamp cannot be in the future')
        return v


class FeatureValueServingResponse(BaseModel):
    """Schema for feature value serving response."""
    entity_id: str
    features: Dict[int, Optional[Dict[str, Any]]]  # feature_id -> {value, timestamp, metadata} or None
    timestamp: datetime


class FeatureValueStats(BaseModel):
    """Schema for feature value statistics."""
    feature_id: int
    total_values: int
    unique_entities: int
    date_range: Optional[Dict[str, datetime]]
    value_stats: Optional[Dict[str, Any]]


class FeatureValueFilter(BaseModel):
    """Schema for filtering feature values."""
    feature_id: Optional[int] = None
    entity_id: Optional[str] = None
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    value_type: Optional[str] = None  # 'numeric', 'categorical', 'text', etc.

    @validator('start_timestamp', 'end_timestamp')
    def validate_timestamp_range(cls, v, values):
        if 'start_timestamp' in values and 'end_timestamp' in values:
            if values['start_timestamp'] and values['end_timestamp']:
                if values['start_timestamp'] > values['end_timestamp']:
                    raise ValueError('Start timestamp must be before end timestamp')
        return v


class FeatureValueExport(BaseModel):
    """Schema for feature value export request."""
    feature_ids: List[int]
    entity_ids: Optional[List[str]] = None
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    format: str = Field(default="csv", regex="^(csv|json|parquet)$")
    include_metadata: bool = Field(default=True)

    @validator('feature_ids')
    def validate_feature_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one feature ID must be provided')
        return v

    @validator('format')
    def validate_format(cls, v):
        if v not in ['csv', 'json', 'parquet']:
            raise ValueError('Format must be one of: csv, json, parquet')
        return v 