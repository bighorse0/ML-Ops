from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from datetime import datetime, timedelta
import json

from ..database import get_db
from ..auth import get_current_user, require_permission
from ..models.monitoring import (
    DataQualityMetric,
    PerformanceMetric,
    Alert,
    AlertRule,
    HealthCheck
)
from ..models.user import User
from ..schemas.monitoring import (
    DataQualityMetricCreate,
    DataQualityMetricResponse,
    PerformanceMetricCreate,
    PerformanceMetricResponse,
    AlertCreate,
    AlertResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    HealthCheckResponse,
    MonitoringDashboard,
    MetricQuery
)
from ..schemas.common import PaginationParams, PaginatedResponse, Status, AlertSeverity

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.post("/data-quality", response_model=DataQualityMetricResponse)
async def create_data_quality_metric(
    metric: DataQualityMetricCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new data quality metric."""
    await require_permission(current_user, "monitoring:write")
    
    db_metric = DataQualityMetric(
        feature_id=metric.feature_id,
        metric_type=metric.metric_type,
        value=metric.value,
        threshold=metric.threshold,
        status=metric.status,
        metadata=metric.metadata,
        timestamp=metric.timestamp or datetime.utcnow(),
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )
    
    db.add(db_metric)
    await db.commit()
    await db.refresh(db_metric)
    
    return DataQualityMetricResponse.from_orm(db_metric)


@router.get("/data-quality", response_model=PaginatedResponse[DataQualityMetricResponse])
async def list_data_quality_metrics(
    pagination: PaginationParams = Depends(),
    feature_id: Optional[int] = Query(None),
    metric_type: Optional[str] = Query(None),
    status: Optional[Status] = Query(None),
    start_timestamp: Optional[datetime] = Query(None),
    end_timestamp: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List data quality metrics with filtering."""
    await require_permission(current_user, "monitoring:read")
    
    query = select(DataQualityMetric).where(
        DataQualityMetric.organization_id == current_user.organization_id
    )
    
    if feature_id:
        query = query.where(DataQualityMetric.feature_id == feature_id)
    if metric_type:
        query = query.where(DataQualityMetric.metric_type == metric_type)
    if status:
        query = query.where(DataQualityMetric.status == status)
    if start_timestamp:
        query = query.where(DataQualityMetric.timestamp >= start_timestamp)
    if end_timestamp:
        query = query.where(DataQualityMetric.timestamp <= end_timestamp)
    
    query = query.order_by(desc(DataQualityMetric.timestamp))
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    # Get total count
    count_query = select(DataQualityMetric).where(
        DataQualityMetric.organization_id == current_user.organization_id
    )
    if feature_id:
        count_query = count_query.where(DataQualityMetric.feature_id == feature_id)
    if metric_type:
        count_query = count_query.where(DataQualityMetric.metric_type == metric_type)
    if status:
        count_query = count_query.where(DataQualityMetric.status == status)
    if start_timestamp:
        count_query = count_query.where(DataQualityMetric.timestamp >= start_timestamp)
    if end_timestamp:
        count_query = count_query.where(DataQualityMetric.timestamp <= end_timestamp)
    
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    return PaginatedResponse(
        items=[DataQualityMetricResponse.from_orm(m) for m in metrics],
        total=total_count,
        page=pagination.page,
        size=pagination.limit,
        pages=(total_count + pagination.limit - 1) // pagination.limit
    )


@router.post("/performance", response_model=PerformanceMetricResponse)
async def create_performance_metric(
    metric: PerformanceMetricCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new performance metric."""
    await require_permission(current_user, "monitoring:write")
    
    db_metric = PerformanceMetric(
        service_name=metric.service_name,
        metric_name=metric.metric_name,
        value=metric.value,
        unit=metric.unit,
        labels=metric.labels,
        timestamp=metric.timestamp or datetime.utcnow(),
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )
    
    db.add(db_metric)
    await db.commit()
    await db.refresh(db_metric)
    
    return PerformanceMetricResponse.from_orm(db_metric)


@router.get("/performance", response_model=PaginatedResponse[PerformanceMetricResponse])
async def list_performance_metrics(
    pagination: PaginationParams = Depends(),
    service_name: Optional[str] = Query(None),
    metric_name: Optional[str] = Query(None),
    start_timestamp: Optional[datetime] = Query(None),
    end_timestamp: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List performance metrics with filtering."""
    await require_permission(current_user, "monitoring:read")
    
    query = select(PerformanceMetric).where(
        PerformanceMetric.organization_id == current_user.organization_id
    )
    
    if service_name:
        query = query.where(PerformanceMetric.service_name == service_name)
    if metric_name:
        query = query.where(PerformanceMetric.metric_name == metric_name)
    if start_timestamp:
        query = query.where(PerformanceMetric.timestamp >= start_timestamp)
    if end_timestamp:
        query = query.where(PerformanceMetric.timestamp <= end_timestamp)
    
    query = query.order_by(desc(PerformanceMetric.timestamp))
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    # Get total count
    count_query = select(PerformanceMetric).where(
        PerformanceMetric.organization_id == current_user.organization_id
    )
    if service_name:
        count_query = count_query.where(PerformanceMetric.service_name == service_name)
    if metric_name:
        count_query = count_query.where(PerformanceMetric.metric_name == metric_name)
    if start_timestamp:
        count_query = count_query.where(PerformanceMetric.timestamp >= start_timestamp)
    if end_timestamp:
        count_query = count_query.where(PerformanceMetric.timestamp <= end_timestamp)
    
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    return PaginatedResponse(
        items=[PerformanceMetricResponse.from_orm(m) for m in metrics],
        total=total_count,
        page=pagination.page,
        size=pagination.limit,
        pages=(total_count + pagination.limit - 1) // pagination.limit
    )


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert."""
    await require_permission(current_user, "monitoring:write")
    
    db_alert = Alert(
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        source=alert.source,
        metadata=alert.metadata,
        status=alert.status,
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )
    
    db.add(db_alert)
    await db.commit()
    await db.refresh(db_alert)
    
    return AlertResponse.from_orm(db_alert)


@router.get("/alerts", response_model=PaginatedResponse[AlertResponse])
async def list_alerts(
    pagination: PaginationParams = Depends(),
    severity: Optional[AlertSeverity] = Query(None),
    status: Optional[Status] = Query(None),
    source: Optional[str] = Query(None),
    start_timestamp: Optional[datetime] = Query(None),
    end_timestamp: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List alerts with filtering."""
    await require_permission(current_user, "monitoring:read")
    
    query = select(Alert).where(
        Alert.organization_id == current_user.organization_id
    )
    
    if severity:
        query = query.where(Alert.severity == severity)
    if status:
        query = query.where(Alert.status == status)
    if source:
        query = query.where(Alert.source == source)
    if start_timestamp:
        query = query.where(Alert.created_at >= start_timestamp)
    if end_timestamp:
        query = query.where(Alert.created_at <= end_timestamp)
    
    query = query.order_by(desc(Alert.created_at))
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    # Get total count
    count_query = select(Alert).where(
        Alert.organization_id == current_user.organization_id
    )
    if severity:
        count_query = count_query.where(Alert.severity == severity)
    if status:
        count_query = count_query.where(Alert.status == status)
    if source:
        count_query = count_query.where(Alert.source == source)
    if start_timestamp:
        count_query = count_query.where(Alert.created_at >= start_timestamp)
    if end_timestamp:
        count_query = count_query.where(Alert.created_at <= end_timestamp)
    
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    return PaginatedResponse(
        items=[AlertResponse.from_orm(a) for a in alerts],
        total=total_count,
        page=pagination.page,
        size=pagination.limit,
        pages=(total_count + pagination.limit - 1) // pagination.limit
    )


@router.put("/alerts/{alert_id}/status")
async def update_alert_status(
    alert_id: int,
    status: Status,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update alert status."""
    await require_permission(current_user, "monitoring:write")
    
    alert = await db.execute(
        select(Alert).where(
            and_(
                Alert.id == alert_id,
                Alert.organization_id == current_user.organization_id
            )
        )
    )
    alert = alert.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = status
    alert.updated_at = datetime.utcnow()
    alert.updated_by = current_user.id
    
    await db.commit()
    
    return {"message": "Alert status updated successfully"}


@router.post("/alert-rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule: AlertRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert rule."""
    await require_permission(current_user, "monitoring:write")
    
    db_rule = AlertRule(
        name=rule.name,
        description=rule.description,
        condition=rule.condition,
        severity=rule.severity,
        is_active=rule.is_active,
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )
    
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    
    return AlertRuleResponse.from_orm(db_rule)


@router.get("/alert-rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all alert rules."""
    await require_permission(current_user, "monitoring:read")
    
    rules = await db.execute(
        select(AlertRule).where(
            AlertRule.organization_id == current_user.organization_id
        ).order_by(AlertRule.created_at.desc())
    )
    rules = rules.scalars().all()
    
    return [AlertRuleResponse.from_orm(r) for r in rules]


@router.get("/dashboard", response_model=MonitoringDashboard)
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get monitoring dashboard data."""
    await require_permission(current_user, "monitoring:read")
    
    # Get recent data quality metrics
    recent_quality_metrics = await db.execute(
        select(DataQualityMetric).where(
            and_(
                DataQualityMetric.organization_id == current_user.organization_id,
                DataQualityMetric.timestamp >= datetime.utcnow() - timedelta(hours=24)
            )
        ).order_by(desc(DataQualityMetric.timestamp)).limit(10)
    )
    recent_quality_metrics = recent_quality_metrics.scalars().all()
    
    # Get recent performance metrics
    recent_performance_metrics = await db.execute(
        select(PerformanceMetric).where(
            and_(
                PerformanceMetric.organization_id == current_user.organization_id,
                PerformanceMetric.timestamp >= datetime.utcnow() - timedelta(hours=24)
            )
        ).order_by(desc(PerformanceMetric.timestamp)).limit(10)
    )
    recent_performance_metrics = recent_performance_metrics.scalars().all()
    
    # Get active alerts
    active_alerts = await db.execute(
        select(Alert).where(
            and_(
                Alert.organization_id == current_user.organization_id,
                Alert.status == Status.ACTIVE
            )
        ).order_by(desc(Alert.created_at)).limit(10)
    )
    active_alerts = active_alerts.scalars().all()
    
    # Calculate summary statistics
    total_alerts = await db.execute(
        select(func.count(Alert.id)).where(
            and_(
                Alert.organization_id == current_user.organization_id,
                Alert.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        )
    )
    total_alerts = total_alerts.scalar()
    
    critical_alerts = await db.execute(
        select(func.count(Alert.id)).where(
            and_(
                Alert.organization_id == current_user.organization_id,
                Alert.severity == AlertSeverity.CRITICAL,
                Alert.created_at >= datetime.utcnow() - timedelta(days=7)
            )
        )
    )
    critical_alerts = critical_alerts.scalar()
    
    return MonitoringDashboard(
        recent_quality_metrics=[DataQualityMetricResponse.from_orm(m) for m in recent_quality_metrics],
        recent_performance_metrics=[PerformanceMetricResponse.from_orm(m) for m in recent_performance_metrics],
        active_alerts=[AlertResponse.from_orm(a) for a in active_alerts],
        summary={
            "total_alerts_7d": total_alerts,
            "critical_alerts_7d": critical_alerts,
            "data_quality_score": 95.5,  # This would be calculated from actual metrics
            "system_health": "healthy"
        }
    )


@router.get("/health", response_model=HealthCheckResponse)
async def get_system_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get system health status."""
    await require_permission(current_user, "monitoring:read")
    
    # Check database connectivity
    try:
        await db.execute(select(1))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # Check Redis connectivity (placeholder)
    redis_status = "healthy"
    
    # Check external services (placeholder)
    services = {
        "database": db_status,
        "redis": redis_status,
        "feature_serving": "healthy",
        "computation_engine": "healthy"
    }
    
    overall_status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services=services
    )


@router.get("/metrics/{metric_name}")
async def get_metric_data(
    metric_name: str,
    start_timestamp: datetime = Query(...),
    end_timestamp: datetime = Query(...),
    interval: str = Query("1h", description="Time interval for aggregation"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get time series data for a specific metric."""
    await require_permission(current_user, "monitoring:read")
    
    # This is a simplified implementation
    # In a real system, you'd want to use a time-series database like InfluxDB or TimescaleDB
    
    if metric_name == "data_quality":
        query = select(DataQualityMetric).where(
            and_(
                DataQualityMetric.organization_id == current_user.organization_id,
                DataQualityMetric.timestamp >= start_timestamp,
                DataQualityMetric.timestamp <= end_timestamp
            )
        ).order_by(DataQualityMetric.timestamp)
    elif metric_name == "performance":
        query = select(PerformanceMetric).where(
            and_(
                PerformanceMetric.organization_id == current_user.organization_id,
                PerformanceMetric.timestamp >= start_timestamp,
                PerformanceMetric.timestamp <= end_timestamp
            )
        ).order_by(PerformanceMetric.timestamp)
    else:
        raise HTTPException(status_code=400, detail="Unknown metric type")
    
    result = await db.execute(query)
    metrics = result.scalars().all()
    
    # Convert to time series format
    time_series_data = []
    for metric in metrics:
        time_series_data.append({
            "timestamp": metric.timestamp.isoformat(),
            "value": metric.value,
            "labels": getattr(metric, 'labels', {})
        })
    
    return {
        "metric_name": metric_name,
        "start_timestamp": start_timestamp.isoformat(),
        "end_timestamp": end_timestamp.isoformat(),
        "interval": interval,
        "data": time_series_data
    } 