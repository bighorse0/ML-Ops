from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey, 
    Index, Table, Enum as SQLEnum, Integer
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum

from .base import Base, BaseModelMixin, PydanticBaseModel, Field

class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class PermissionType(str, Enum):
    """Permission types for RBAC."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

class ResourceType(str, Enum):
    """Resource types for permissions."""
    FEATURE = "feature"
    FEATURE_VALUE = "feature_value"
    ORGANIZATION = "organization"
    USER = "user"
    MONITORING = "monitoring"
    COMPUTATION = "computation"

class Organization(Base, BaseModelMixin):
    """Organization model for multi-tenancy."""
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True, unique=True)
    
    # Organization settings
    max_features = Column(Integer, default=1000)
    max_users = Column(Integer, default=100)
    max_storage_gb = Column(Integer, default=100)
    
    # Billing and limits
    plan_type = Column(String(50), default="free")  # free, pro, enterprise
    is_active = Column(Boolean, default=True)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    roles = relationship("Role", back_populates="organization")
    
    # Indexes
    __table_args__ = (
        Index('idx_org_domain', 'domain'),
        Index('idx_org_status', 'is_active'),
    )

class User(Base, BaseModelMixin):
    """User model with authentication and profile information."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Authentication
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(255), nullable=True)
    
    # Status and preferences
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING)
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    
    # API access
    api_key = Column(String(255), nullable=True, unique=True, index=True)
    api_key_created_at = Column(DateTime, nullable=True)
    api_key_expires_at = Column(DateTime, nullable=True)
    
    # Last activity
    last_login_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_org', 'organization_id'),
        Index('idx_user_status', 'status'),
        Index('idx_user_email_verified', 'is_email_verified'),
    )

class Role(Base, BaseModelMixin):
    """Role model for RBAC."""
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False)  # Built-in roles
    is_active = Column(Boolean, default=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="roles")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_role_org_name', 'organization_id', 'name', unique=True),
        Index('idx_role_system', 'is_system_role'),
    )

class Permission(Base, BaseModelMixin):
    """Permission model for fine-grained access control."""
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    resource_type = Column(SQLEnum(ResourceType), nullable=False)
    permission_type = Column(SQLEnum(PermissionType), nullable=False)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_permission_resource', 'resource_type'),
        Index('idx_permission_type', 'permission_type'),
    )

# Association tables
class UserRole(Base, BaseModelMixin):
    """User-Role association table."""
    __tablename__ = "user_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_role_unique', 'user_id', 'role_id', unique=True),
    )

class RolePermission(Base, BaseModelMixin):
    """Role-Permission association table."""
    __tablename__ = "role_permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)
    
    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    
    # Indexes
    __table_args__ = (
        Index('idx_role_permission_unique', 'role_id', 'permission_id', unique=True),
    )

# Pydantic models for API
class OrganizationCreate(PydanticBaseModel):
    """Model for creating a new organization."""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")
    domain: Optional[str] = Field(None, description="Organization domain")
    max_features: Optional[int] = Field(1000, ge=1, description="Maximum features allowed")
    max_users: Optional[int] = Field(100, ge=1, description="Maximum users allowed")
    max_storage_gb: Optional[int] = Field(100, ge=1, description="Maximum storage in GB")
    plan_type: Optional[str] = Field("free", description="Plan type")

class OrganizationUpdate(PydanticBaseModel):
    """Model for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    domain: Optional[str] = None
    max_features: Optional[int] = Field(None, ge=1)
    max_users: Optional[int] = Field(None, ge=1)
    max_storage_gb: Optional[int] = Field(None, ge=1)
    plan_type: Optional[str] = None
    is_active: Optional[bool] = None

class OrganizationResponse(PydanticBaseModel):
    """Model for organization API responses."""
    id: str
    name: str
    description: Optional[str]
    domain: Optional[str]
    max_features: int
    max_users: int
    max_storage_gb: int
    plan_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class UserCreate(PydanticBaseModel):
    """Model for creating a new user."""
    email: str = Field(..., description="User email")
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    display_name: Optional[str] = Field(None, max_length=255, description="Display name")

class UserUpdate(PydanticBaseModel):
    """Model for updating a user."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=255)
    status: Optional[UserStatus] = None

class UserResponse(PydanticBaseModel):
    """Model for user API responses."""
    id: str
    organization_id: str
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    status: UserStatus
    is_email_verified: bool
    last_login_at: Optional[datetime]
    last_activity_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class RoleCreate(PydanticBaseModel):
    """Model for creating a new role."""
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    permissions: List[str] = Field(default_factory=list, description="Permission IDs")

class RoleUpdate(PydanticBaseModel):
    """Model for updating a role."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[str]] = None

class RoleResponse(PydanticBaseModel):
    """Model for role API responses."""
    id: str
    organization_id: str
    name: str
    description: Optional[str]
    is_system_role: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime 