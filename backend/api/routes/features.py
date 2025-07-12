from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
import structlog

from ..database import get_db
from ..auth import get_current_user, get_organization_context, require_permission
from ..models.base import APIResponse, PaginatedResponse
from models import Feature, FeatureVersion, FeatureValue
from models.feature import (
    FeatureCreate, FeatureUpdate, FeatureResponse,
    FeatureStatus, DataType, ServingType
)
from models.user import ResourceType, PermissionType

logger = structlog.get_logger()
router = APIRouter()

@router.post("/", response_model=APIResponse[FeatureResponse])
async def create_feature(
    feature_data: FeatureCreate,
    context: Dict[str, Any] = Depends(get_organization_context),
    db: AsyncSession = Depends(get_db)
):
    """Create a new feature."""
    try:
        # Check if feature name already exists in organization
        existing_feature = await db.execute(
            select(Feature).where(
                and_(
                    Feature.name == feature_data.name,
                    Feature.organization_id == context["organization_id"],
                    Feature.is_deleted == False
                )
            )
        )
        
        if existing_feature.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Feature with name '{feature_data.name}' already exists"
            )
        
        # Create feature
        feature = Feature(
            name=feature_data.name,
            description=feature_data.description,
            data_type=feature_data.data_type,
            tags=feature_data.tags,
            owner=feature_data.owner,
            freshness_sla=feature_data.freshness_sla,
            serving_type=feature_data.serving_type,
            schema=feature_data.schema,
            transformation=feature_data.transformation,
            transformation_type=feature_data.transformation_type,
            expected_latency_ms=feature_data.expected_latency_ms,
            expected_throughput_rps=feature_data.expected_throughput_rps,
            organization_id=context["organization_id"],
            created_by=context["user"].email
        )
        
        db.add(feature)
        await db.flush()  # Get the ID
        
        # Create initial version
        version = FeatureVersion(
            feature_id=feature.id,
            version="v1",
            description="Initial version",
            schema=feature_data.schema or {},
            transformation=feature_data.transformation,
            transformation_type=feature_data.transformation_type,
            expected_latency_ms=feature_data.expected_latency_ms,
            expected_throughput_rps=feature_data.expected_throughput_rps,
            is_active=True,
            is_default=True,
            organization_id=context["organization_id"],
            created_by=context["user"].email
        )
        
        db.add(version)
        await db.commit()
        
        logger.info(
            "Feature created",
            feature_id=str(feature.id),
            feature_name=feature.name,
            organization_id=context["organization_id"],
            created_by=context["user"].email
        )
        
        return APIResponse(
            success=True,
            data=FeatureResponse.from_orm(feature),
            message="Feature created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating feature: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create feature"
        )

@router.get("/", response_model=APIResponse[PaginatedResponse[FeatureResponse]])
async def list_features(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search term"),
    status_filter: Optional[FeatureStatus] = Query(None, description="Filter by status"),
    data_type: Optional[DataType] = Query(None, description="Filter by data type"),
    serving_type: Optional[ServingType] = Query(None, description="Filter by serving type"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    owner: Optional[str] = Query(None, description="Filter by owner"),
    context: Dict[str, Any] = Depends(get_organization_context),
    db: AsyncSession = Depends(get_db)
):
    """List features with pagination and filtering."""
    try:
        # Build query
        query = select(Feature).where(
            and_(
                Feature.organization_id == context["organization_id"],
                Feature.is_deleted == False
            )
        )
        
        # Apply filters
        if search:
            search_filter = or_(
                Feature.name.ilike(f"%{search}%"),
                Feature.description.ilike(f"%{search}%"),
                Feature.tags.contains([search])
            )
            query = query.where(search_filter)
        
        if status_filter:
            query = query.where(Feature.status == status_filter)
        
        if data_type:
            query = query.where(Feature.data_type == data_type)
        
        if serving_type:
            query = query.where(Feature.serving_type == serving_type)
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            for tag in tag_list:
                query = query.where(Feature.tags.contains([tag]))
        
        if owner:
            query = query.where(Feature.owner == owner)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        # Execute query
        result = await db.execute(query)
        features = result.scalars().all()
        
        # Calculate pagination info
        pages = (total + size - 1) // size
        has_next = page < pages
        has_prev = page > 1
        
        logger.info(
            "Features listed",
            organization_id=context["organization_id"],
            total=total,
            page=page,
            size=size
        )
        
        return APIResponse(
            success=True,
            data=PaginatedResponse(
                items=[FeatureResponse.from_orm(feature) for feature in features],
                total=total,
                page=page,
                size=size,
                pages=pages,
                has_next=has_next,
                has_prev=has_prev
            ),
            message="Features retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error listing features: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve features"
        )

@router.get("/{feature_id}", response_model=APIResponse[FeatureResponse])
async def get_feature(
    feature_id: str,
    context: Dict[str, Any] = Depends(get_organization_context),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific feature by ID."""
    try:
        result = await db.execute(
            select(Feature).where(
                and_(
                    Feature.id == feature_id,
                    Feature.organization_id == context["organization_id"],
                    Feature.is_deleted == False
                )
            )
        )
        
        feature = result.scalar_one_or_none()
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feature not found"
            )
        
        logger.info(
            "Feature retrieved",
            feature_id=feature_id,
            organization_id=context["organization_id"]
        )
        
        return APIResponse(
            success=True,
            data=FeatureResponse.from_orm(feature),
            message="Feature retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feature: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feature"
        )

@router.put("/{feature_id}", response_model=APIResponse[FeatureResponse])
async def update_feature(
    feature_id: str,
    feature_data: FeatureUpdate,
    context: Dict[str, Any] = Depends(get_organization_context),
    db: AsyncSession = Depends(get_db)
):
    """Update a feature."""
    try:
        # Get feature
        result = await db.execute(
            select(Feature).where(
                and_(
                    Feature.id == feature_id,
                    Feature.organization_id == context["organization_id"],
                    Feature.is_deleted == False
                )
            )
        )
        
        feature = result.scalar_one_or_none()
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feature not found"
            )
        
        # Update fields
        update_data = feature_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(feature, field, value)
        
        feature.updated_by = context["user"].email
        
        await db.commit()
        
        logger.info(
            "Feature updated",
            feature_id=feature_id,
            organization_id=context["organization_id"],
            updated_by=context["user"].email
        )
        
        return APIResponse(
            success=True,
            data=FeatureResponse.from_orm(feature),
            message="Feature updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feature: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feature"
        )

@router.delete("/{feature_id}", response_model=APIResponse)
async def delete_feature(
    feature_id: str,
    context: Dict[str, Any] = Depends(get_organization_context),
    db: AsyncSession = Depends(get_db)
):
    """Delete a feature (soft delete)."""
    try:
        # Get feature
        result = await db.execute(
            select(Feature).where(
                and_(
                    Feature.id == feature_id,
                    Feature.organization_id == context["organization_id"],
                    Feature.is_deleted == False
                )
            )
        )
        
        feature = result.scalar_one_or_none()
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feature not found"
            )
        
        # Soft delete
        feature.is_deleted = True
        feature.deleted_at = func.now()
        feature.deleted_by = context["user"].email
        
        await db.commit()
        
        logger.info(
            "Feature deleted",
            feature_id=feature_id,
            organization_id=context["organization_id"],
            deleted_by=context["user"].email
        )
        
        return APIResponse(
            success=True,
            message="Feature deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feature: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete feature"
        )

@router.get("/{feature_id}/versions", response_model=APIResponse[List[Dict[str, Any]]])
async def get_feature_versions(
    feature_id: str,
    context: Dict[str, Any] = Depends(get_organization_context),
    db: AsyncSession = Depends(get_db)
):
    """Get all versions of a feature."""
    try:
        # Verify feature exists and belongs to organization
        feature_result = await db.execute(
            select(Feature).where(
                and_(
                    Feature.id == feature_id,
                    Feature.organization_id == context["organization_id"],
                    Feature.is_deleted == False
                )
            )
        )
        
        if not feature_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feature not found"
            )
        
        # Get versions
        versions_result = await db.execute(
            select(FeatureVersion).where(
                and_(
                    FeatureVersion.feature_id == feature_id,
                    FeatureVersion.organization_id == context["organization_id"]
                )
            ).order_by(FeatureVersion.created_at.desc())
        )
        
        versions = versions_result.scalars().all()
        
        return APIResponse(
            success=True,
            data=[
                {
                    "id": str(version.id),
                    "version": version.version,
                    "description": version.description,
                    "is_active": version.is_active,
                    "is_default": version.is_default,
                    "created_at": version.created_at,
                    "updated_at": version.updated_at
                }
                for version in versions
            ],
            message="Feature versions retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feature versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feature versions"
        )

@router.get("/{feature_id}/stats", response_model=APIResponse[Dict[str, Any]])
async def get_feature_stats(
    feature_id: str,
    context: Dict[str, Any] = Depends(get_organization_context),
    db: AsyncSession = Depends(get_db)
):
    """Get feature statistics."""
    try:
        # Verify feature exists
        feature_result = await db.execute(
            select(Feature).where(
                and_(
                    Feature.id == feature_id,
                    Feature.organization_id == context["organization_id"],
                    Feature.is_deleted == False
                )
            )
        )
        
        feature = feature_result.scalar_one_or_none()
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feature not found"
            )
        
        # Get statistics
        stats = {
            "feature_id": str(feature.id),
            "feature_name": feature.name,
            "total_versions": 0,
            "total_values": 0,
            "last_updated": None,
            "status": feature.status.value
        }
        
        # Count versions
        versions_count = await db.execute(
            select(func.count(FeatureVersion.id)).where(
                FeatureVersion.feature_id == feature_id
            )
        )
        stats["total_versions"] = versions_count.scalar()
        
        # Count values
        values_count = await db.execute(
            select(func.count(FeatureValue.id)).where(
                FeatureValue.feature_id == feature_id
            )
        )
        stats["total_values"] = values_count.scalar()
        
        # Get last updated
        if stats["total_values"] > 0:
            last_value = await db.execute(
                select(FeatureValue).where(
                    FeatureValue.feature_id == feature_id
                ).order_by(FeatureValue.created_at.desc()).limit(1)
            )
            last_value = last_value.scalar_one_or_none()
            if last_value:
                stats["last_updated"] = last_value.created_at
        
        return APIResponse(
            success=True,
            data=stats,
            message="Feature statistics retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving feature stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feature statistics"
        ) 