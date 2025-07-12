from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, DateTime, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
from pydantic import BaseModel, Field

Base = declarative_base()

class TimestampMixin:
    """Mixin to add timestamp fields to models."""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class TenantMixin:
    """Mixin to add multi-tenancy support to models."""
    organization_id = Column(String(36), nullable=False, index=True)
    
    @declared_attr
    def __table_args__(cls):
        return {'schema': 'public'}

class AuditMixin:
    """Mixin to add audit fields to models."""
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(255), nullable=True)

class BaseModelMixin(TimestampMixin, TenantMixin, AuditMixin):
    """Base mixin combining common functionality."""
    pass

class PydanticBaseModel(BaseModel):
    """Base Pydantic model with common configuration."""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        validate_assignment = True

class APIResponse(PydanticBaseModel):
    """Standard API response wrapper."""
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    error_code: Optional[str] = Field(None, description="Error code if applicable")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class PaginatedResponse(PydanticBaseModel):
    """Paginated response wrapper."""
    items: list = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages") 