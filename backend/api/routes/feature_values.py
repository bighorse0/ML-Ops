from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import asyncio
import json
from datetime import datetime, timedelta

from ..database import get_db
from ..auth import get_current_user, require_permission
from ..models.feature import Feature, FeatureValue
from ..models.user import User
from ..schemas.feature_values import (
    FeatureValueCreate,
    FeatureValueUpdate,
    FeatureValueResponse,
    FeatureValueBatchCreate,
    FeatureValueBatchResponse,
    FeatureValueQuery,
    FeatureValueServingResponse
)
from ..schemas.common import PaginationParams, PaginatedResponse

router = APIRouter(prefix="/feature-values", tags=["feature-values"])


@router.post("/", response_model=FeatureValueResponse)
async def create_feature_value(
    feature_value: FeatureValueCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new feature value."""
    await require_permission(current_user, "feature_values:write")
    
    # Verify feature exists and user has access
    feature = await db.execute(
        select(Feature).where(
            and_(
                Feature.id == feature_value.feature_id,
                Feature.organization_id == current_user.organization_id
            )
        )
    )
    feature = feature.scalar_one_or_none()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    # Check if value already exists for this entity and timestamp
    existing = await db.execute(
        select(FeatureValue).where(
            and_(
                FeatureValue.feature_id == feature_value.feature_id,
                FeatureValue.entity_id == feature_value.entity_id,
                FeatureValue.timestamp == feature_value.timestamp
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Feature value already exists for this entity and timestamp")
    
    # Create new feature value
    db_feature_value = FeatureValue(
        feature_id=feature_value.feature_id,
        entity_id=feature_value.entity_id,
        value=feature_value.value,
        timestamp=feature_value.timestamp,
        metadata=feature_value.metadata,
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )
    
    db.add(db_feature_value)
    await db.commit()
    await db.refresh(db_feature_value)
    
    return FeatureValueResponse.from_orm(db_feature_value)


@router.post("/batch", response_model=FeatureValueBatchResponse)
async def create_feature_values_batch(
    batch: FeatureValueBatchCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create multiple feature values in batch."""
    await require_permission(current_user, "feature_values:write")
    
    # Verify all features exist and user has access
    feature_ids = {fv.feature_id for fv in batch.feature_values}
    features = await db.execute(
        select(Feature).where(
            and_(
                Feature.id.in_(feature_ids),
                Feature.organization_id == current_user.organization_id
            )
        )
    )
    features = features.scalars().all()
    
    if len(features) != len(feature_ids):
        raise HTTPException(status_code=404, detail="One or more features not found")
    
    # Check for existing values to avoid conflicts
    existing_values = []
    for fv in batch.feature_values:
        existing = await db.execute(
            select(FeatureValue).where(
                and_(
                    FeatureValue.feature_id == fv.feature_id,
                    FeatureValue.entity_id == fv.entity_id,
                    FeatureValue.timestamp == fv.timestamp
                )
            )
        )
        if existing.scalar_one_or_none():
            existing_values.append(f"{fv.feature_id}:{fv.entity_id}:{fv.timestamp}")
    
    if existing_values:
        raise HTTPException(
            status_code=409, 
            detail=f"Feature values already exist: {', '.join(existing_values)}"
        )
    
    # Create all feature values
    db_feature_values = []
    for fv in batch.feature_values:
        db_feature_value = FeatureValue(
            feature_id=fv.feature_id,
            entity_id=fv.entity_id,
            value=fv.value,
            timestamp=fv.timestamp,
            metadata=fv.metadata,
            created_by=current_user.id,
            organization_id=current_user.organization_id
        )
        db_feature_values.append(db_feature_value)
    
    db.add_all(db_feature_values)
    await db.commit()
    
    # Refresh all objects to get IDs
    for fv in db_feature_values:
        await db.refresh(fv)
    
    return FeatureValueBatchResponse(
        created_count=len(db_feature_values),
        feature_values=[FeatureValueResponse.from_orm(fv) for fv in db_feature_values]
    )


@router.get("/", response_model=PaginatedResponse[FeatureValueResponse])
async def list_feature_values(
    pagination: PaginationParams = Depends(),
    feature_id: Optional[int] = Query(None, description="Filter by feature ID"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    start_timestamp: Optional[datetime] = Query(None, description="Start timestamp filter"),
    end_timestamp: Optional[datetime] = Query(None, description="End timestamp filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List feature values with filtering and pagination."""
    await require_permission(current_user, "feature_values:read")
    
    query = select(FeatureValue).where(
        FeatureValue.organization_id == current_user.organization_id
    )
    
    if feature_id:
        query = query.where(FeatureValue.feature_id == feature_id)
    
    if entity_id:
        query = query.where(FeatureValue.entity_id == entity_id)
    
    if start_timestamp:
        query = query.where(FeatureValue.timestamp >= start_timestamp)
    
    if end_timestamp:
        query = query.where(FeatureValue.timestamp <= end_timestamp)
    
    # Add ordering
    query = query.order_by(FeatureValue.timestamp.desc())
    
    # Add pagination
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    feature_values = result.scalars().all()
    
    # Get total count
    count_query = select(FeatureValue).where(
        FeatureValue.organization_id == current_user.organization_id
    )
    if feature_id:
        count_query = count_query.where(FeatureValue.feature_id == feature_id)
    if entity_id:
        count_query = count_query.where(FeatureValue.entity_id == entity_id)
    if start_timestamp:
        count_query = count_query.where(FeatureValue.timestamp >= start_timestamp)
    if end_timestamp:
        count_query = count_query.where(FeatureValue.timestamp <= end_timestamp)
    
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    return PaginatedResponse(
        items=[FeatureValueResponse.from_orm(fv) for fv in feature_values],
        total=total_count,
        page=pagination.page,
        size=pagination.limit,
        pages=(total_count + pagination.limit - 1) // pagination.limit
    )


@router.get("/{feature_value_id}", response_model=FeatureValueResponse)
async def get_feature_value(
    feature_value_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific feature value by ID."""
    await require_permission(current_user, "feature_values:read")
    
    feature_value = await db.execute(
        select(FeatureValue).where(
            and_(
                FeatureValue.id == feature_value_id,
                FeatureValue.organization_id == current_user.organization_id
            )
        )
    )
    feature_value = feature_value.scalar_one_or_none()
    
    if not feature_value:
        raise HTTPException(status_code=404, detail="Feature value not found")
    
    return FeatureValueResponse.from_orm(feature_value)


@router.put("/{feature_value_id}", response_model=FeatureValueResponse)
async def update_feature_value(
    feature_value_id: int,
    feature_value_update: FeatureValueUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a feature value."""
    await require_permission(current_user, "feature_values:write")
    
    feature_value = await db.execute(
        select(FeatureValue).where(
            and_(
                FeatureValue.id == feature_value_id,
                FeatureValue.organization_id == current_user.organization_id
            )
        )
    )
    feature_value = feature_value.scalar_one_or_none()
    
    if not feature_value:
        raise HTTPException(status_code=404, detail="Feature value not found")
    
    # Update fields
    update_data = feature_value_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(feature_value, field, value)
    
    feature_value.updated_at = datetime.utcnow()
    feature_value.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(feature_value)
    
    return FeatureValueResponse.from_orm(feature_value)


@router.delete("/{feature_value_id}")
async def delete_feature_value(
    feature_value_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a feature value."""
    await require_permission(current_user, "feature_values:write")
    
    feature_value = await db.execute(
        select(FeatureValue).where(
            and_(
                FeatureValue.id == feature_value_id,
                FeatureValue.organization_id == current_user.organization_id
            )
        )
    )
    feature_value = feature_value.scalar_one_or_none()
    
    if not feature_value:
        raise HTTPException(status_code=404, detail="Feature value not found")
    
    await db.delete(feature_value)
    await db.commit()
    
    return {"message": "Feature value deleted successfully"}


@router.post("/serve", response_model=List[FeatureValueServingResponse])
async def serve_feature_values(
    query: FeatureValueQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Serve feature values for online inference."""
    await require_permission(current_user, "feature_values:read")
    
    # Verify all features exist and user has access
    feature_ids = query.feature_ids
    features = await db.execute(
        select(Feature).where(
            and_(
                Feature.id.in_(feature_ids),
                Feature.organization_id == current_user.organization_id
            )
        )
    )
    features = features.scalars().all()
    
    if len(features) != len(feature_ids):
        raise HTTPException(status_code=404, detail="One or more features not found")
    
    # Get feature values for each entity
    results = []
    for entity_id in query.entity_ids:
        entity_values = {}
        
        for feature_id in feature_ids:
            # Get the latest value for this feature and entity
            feature_value = await db.execute(
                select(FeatureValue).where(
                    and_(
                        FeatureValue.feature_id == feature_id,
                        FeatureValue.entity_id == entity_id,
                        FeatureValue.timestamp <= query.timestamp
                    )
                ).order_by(FeatureValue.timestamp.desc()).limit(1)
            )
            feature_value = feature_value.scalar_one_or_none()
            
            if feature_value:
                entity_values[feature_id] = {
                    "value": feature_value.value,
                    "timestamp": feature_value.timestamp,
                    "metadata": feature_value.metadata
                }
            else:
                entity_values[feature_id] = None
        
        results.append(FeatureValueServingResponse(
            entity_id=entity_id,
            features=entity_values,
            timestamp=query.timestamp
        ))
    
    return results


@router.get("/stats/feature/{feature_id}")
async def get_feature_value_stats(
    feature_id: int,
    start_timestamp: Optional[datetime] = Query(None),
    end_timestamp: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for a feature's values."""
    await require_permission(current_user, "feature_values:read")
    
    # Verify feature exists and user has access
    feature = await db.execute(
        select(Feature).where(
            and_(
                Feature.id == feature_id,
                Feature.organization_id == current_user.organization_id
            )
        )
    )
    feature = feature.scalar_one_or_none()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    # Build query for feature values
    query = select(FeatureValue).where(
        and_(
            FeatureValue.feature_id == feature_id,
            FeatureValue.organization_id == current_user.organization_id
        )
    )
    
    if start_timestamp:
        query = query.where(FeatureValue.timestamp >= start_timestamp)
    if end_timestamp:
        query = query.where(FeatureValue.timestamp <= end_timestamp)
    
    feature_values = await db.execute(query)
    feature_values = feature_values.scalars().all()
    
    if not feature_values:
        return {
            "feature_id": feature_id,
            "total_values": 0,
            "unique_entities": 0,
            "date_range": None,
            "value_stats": None
        }
    
    # Calculate statistics
    unique_entities = len(set(fv.entity_id for fv in feature_values))
    timestamps = [fv.timestamp for fv in feature_values]
    date_range = {
        "start": min(timestamps),
        "end": max(timestamps)
    }
    
    # Basic value statistics (assuming numeric values)
    try:
        numeric_values = [float(fv.value) for fv in feature_values if fv.value is not None]
        if numeric_values:
            value_stats = {
                "count": len(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values),
                "mean": sum(numeric_values) / len(numeric_values),
                "null_count": len([fv for fv in feature_values if fv.value is None])
            }
        else:
            value_stats = None
    except (ValueError, TypeError):
        value_stats = None
    
    return {
        "feature_id": feature_id,
        "total_values": len(feature_values),
        "unique_entities": unique_entities,
        "date_range": date_range,
        "value_stats": value_stats
    } 