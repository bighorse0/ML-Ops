from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import structlog

from .database import get_db
from .config import settings
from models import User, Organization, Role, Permission, UserRole, RolePermission
from models.user import UserStatus, PermissionType, ResourceType

logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

class AuthService:
    """Authentication and authorization service."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        try:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            if not AuthService.verify_password(password, user.hashed_password):
                return None
            
            if user.status != UserStatus.ACTIVE:
                logger.warning(f"Login attempt for inactive user: {email}")
                return None
            
            # Update last login
            user.last_login_at = datetime.utcnow()
            user.last_activity_at = datetime.utcnow()
            await db.commit()
            
            return user
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    @staticmethod
    async def authenticate_api_key(db: AsyncSession, api_key: str) -> Optional[User]:
        """Authenticate a user with API key."""
        try:
            result = await db.execute(select(User).where(User.api_key == api_key))
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            if user.status != UserStatus.ACTIVE:
                return None
            
            # Check if API key is expired
            if user.api_key_expires_at and user.api_key_expires_at < datetime.utcnow():
                logger.warning(f"Expired API key used: {api_key}")
                return None
            
            # Update last activity
            user.last_activity_at = datetime.utcnow()
            await db.commit()
            
            return user
        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            return None
    
    @staticmethod
    async def get_user_permissions(db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
        """Get user permissions through roles."""
        try:
            # Get user roles
            result = await db.execute(
                select(Role, Permission)
                .join(UserRole, Role.id == UserRole.role_id)
                .join(RolePermission, Role.id == RolePermission.role_id)
                .join(Permission, RolePermission.permission_id == Permission.id)
                .where(UserRole.user_id == user_id, Role.is_active == True)
            )
            
            permissions = []
            for role, permission in result.all():
                permissions.append({
                    "role": role.name,
                    "resource_type": permission.resource_type,
                    "permission_type": permission.permission_type,
                    "permission_name": permission.name
                })
            
            return permissions
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return []
    
    @staticmethod
    async def check_permission(
        db: AsyncSession, 
        user_id: str, 
        resource_type: ResourceType, 
        permission_type: PermissionType,
        resource_id: Optional[str] = None
    ) -> bool:
        """Check if user has specific permission."""
        try:
            permissions = await AuthService.get_user_permissions(db, user_id)
            
            for perm in permissions:
                if (perm["resource_type"] == resource_type and 
                    perm["permission_type"] == permission_type):
                    return True
                
                # Check for admin permission
                if (perm["resource_type"] == resource_type and 
                    perm["permission_type"] == PermissionType.ADMIN):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False

# Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = AuthService.verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Check if it's a refresh token
        token_type = payload.get("type")
        if token_type == "refresh":
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active"
        )
    
    return user

async def get_current_user_api_key(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from API key."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    user = await AuthService.authenticate_api_key(db, api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user

async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    # Try JWT token first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = AuthService.verify_token(token)
            if payload and payload.get("type") != "refresh":
                user_id = payload.get("sub")
                if user_id:
                    result = await db.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                    if user and user.status == UserStatus.ACTIVE:
                        return user
        except Exception:
            pass
    
    # Try API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        try:
            user = await AuthService.authenticate_api_key(db, api_key)
            if user:
                return user
        except Exception:
            pass
    
    return None

# Permission decorators
def require_permission(resource_type: ResourceType, permission_type: PermissionType):
    """Decorator to require specific permission."""
    async def permission_checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        has_permission = await AuthService.check_permission(
            db, str(current_user.id), resource_type, permission_type
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {permission_type} on {resource_type}"
            )
        
        return current_user
    
    return permission_checker

def require_admin():
    """Decorator to require admin permission."""
    return require_permission(ResourceType.ORGANIZATION, PermissionType.ADMIN)

# Organization context
async def get_organization_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get organization context for the current user."""
    try:
        result = await db.execute(
            select(Organization).where(Organization.id == current_user.organization_id)
        )
        organization = result.scalar_one_or_none()
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        return {
            "user": current_user,
            "organization": organization,
            "organization_id": str(organization.id)
        }
    except Exception as e:
        logger.error(f"Error getting organization context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting organization context"
        )

# Rate limiting context
async def get_rate_limit_context(
    context: Dict[str, Any] = Depends(get_organization_context)
) -> Dict[str, Any]:
    """Get rate limiting context based on organization plan."""
    organization = context["organization"]
    
    # Set rate limit based on plan
    if organization.plan_type == "enterprise":
        rate_limit = settings.RATE_LIMIT_ENTERPRISE_TIER
    elif organization.plan_type == "pro":
        rate_limit = settings.RATE_LIMIT_PRO_TIER
    else:
        rate_limit = settings.RATE_LIMIT_FREE_TIER
    
    context["rate_limit"] = rate_limit
    return context 