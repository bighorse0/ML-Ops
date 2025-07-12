from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime, timedelta
import json
import asyncio

from ..database import get_db
from ..auth import get_current_user, require_permission
from ..models.computation import (
    ComputationJob,
    ComputationPipeline,
    ComputationTask,
    ComputationResult
)
from ..models.user import User
from ..schemas.computation import (
    ComputationJobCreate,
    ComputationJobResponse,
    ComputationJobUpdate,
    ComputationPipelineCreate,
    ComputationPipelineResponse,
    ComputationTaskCreate,
    ComputationTaskResponse,
    ComputationResultResponse,
    JobExecutionRequest,
    PipelineExecutionRequest
)
from ..schemas.common import PaginationParams, PaginatedResponse, Status, ComputationType

router = APIRouter(prefix="/computation", tags=["computation"])


@router.post("/jobs", response_model=ComputationJobResponse)
async def create_computation_job(
    job: ComputationJobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new computation job."""
    await require_permission(current_user, "computation:write")
    
    db_job = ComputationJob(
        name=job.name,
        description=job.description,
        job_type=job.job_type,
        config=job.config,
        schedule=job.schedule,
        status=Status.PENDING,
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )
    
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    
    return ComputationJobResponse.from_orm(db_job)


@router.get("/jobs", response_model=PaginatedResponse[ComputationJobResponse])
async def list_computation_jobs(
    pagination: PaginationParams = Depends(),
    status: Optional[Status] = Query(None),
    job_type: Optional[ComputationType] = Query(None),
    created_by: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List computation jobs with filtering."""
    await require_permission(current_user, "computation:read")
    
    query = select(ComputationJob).where(
        ComputationJob.organization_id == current_user.organization_id
    )
    
    if status:
        query = query.where(ComputationJob.status == status)
    if job_type:
        query = query.where(ComputationJob.job_type == job_type)
    if created_by:
        query = query.where(ComputationJob.created_by == created_by)
    
    query = query.order_by(desc(ComputationJob.created_at))
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    # Get total count
    count_query = select(ComputationJob).where(
        ComputationJob.organization_id == current_user.organization_id
    )
    if status:
        count_query = count_query.where(ComputationJob.status == status)
    if job_type:
        count_query = count_query.where(ComputationJob.job_type == job_type)
    if created_by:
        count_query = count_query.where(ComputationJob.created_by == created_by)
    
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    return PaginatedResponse(
        items=[ComputationJobResponse.from_orm(j) for j in jobs],
        total=total_count,
        page=pagination.page,
        size=pagination.limit,
        pages=(total_count + pagination.limit - 1) // pagination.limit
    )


@router.get("/jobs/{job_id}", response_model=ComputationJobResponse)
async def get_computation_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific computation job."""
    await require_permission(current_user, "computation:read")
    
    job = await db.execute(
        select(ComputationJob).where(
            and_(
                ComputationJob.id == job_id,
                ComputationJob.organization_id == current_user.organization_id
            )
        )
    )
    job = job.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Computation job not found")
    
    return ComputationJobResponse.from_orm(job)


@router.put("/jobs/{job_id}", response_model=ComputationJobResponse)
async def update_computation_job(
    job_id: int,
    job_update: ComputationJobUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a computation job."""
    await require_permission(current_user, "computation:write")
    
    job = await db.execute(
        select(ComputationJob).where(
            and_(
                ComputationJob.id == job_id,
                ComputationJob.organization_id == current_user.organization_id
            )
        )
    )
    job = job.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Computation job not found")
    
    # Update fields
    update_data = job_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    job.updated_at = datetime.utcnow()
    job.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(job)
    
    return ComputationJobResponse.from_orm(job)


@router.delete("/jobs/{job_id}")
async def delete_computation_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a computation job."""
    await require_permission(current_user, "computation:write")
    
    job = await db.execute(
        select(ComputationJob).where(
            and_(
                ComputationJob.id == job_id,
                ComputationJob.organization_id == current_user.organization_id
            )
        )
    )
    job = job.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Computation job not found")
    
    await db.delete(job)
    await db.commit()
    
    return {"message": "Computation job deleted successfully"}


@router.post("/jobs/{job_id}/execute")
async def execute_computation_job(
    job_id: int,
    execution_request: JobExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a computation job."""
    await require_permission(current_user, "computation:execute")
    
    job = await db.execute(
        select(ComputationJob).where(
            and_(
                ComputationJob.id == job_id,
                ComputationJob.organization_id == current_user.organization_id
            )
        )
    )
    job = job.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Computation job not found")
    
    # Create a new task for this execution
    task = ComputationTask(
        job_id=job_id,
        name=f"Execution of {job.name}",
        task_type=job.job_type,
        config=execution_request.config or job.config,
        status=Status.PENDING,
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # Add background task to execute the job
    background_tasks.add_task(execute_job_task, task.id, db)
    
    return {
        "message": "Job execution started",
        "task_id": task.id,
        "status": task.status
    }


async def execute_job_task(task_id: int, db: AsyncSession):
    """Background task to execute a computation job."""
    # This is a simplified implementation
    # In a real system, you'd want to use a proper task queue like Celery
    
    task = await db.execute(
        select(ComputationTask).where(ComputationTask.id == task_id)
    )
    task = task.scalar_one_or_none()
    
    if not task:
        return
    
    try:
        # Update task status to running
        task.status = Status.RUNNING
        task.started_at = datetime.utcnow()
        await db.commit()
        
        # Simulate job execution
        await asyncio.sleep(5)  # Simulate work
        
        # Update task status to completed
        task.status = Status.SUCCESS
        task.completed_at = datetime.utcnow()
        task.result = {"message": "Job completed successfully"}
        
        # Create computation result
        result = ComputationResult(
            task_id=task_id,
            job_id=task.job_id,
            result_type="success",
            data=task.result,
            created_by=task.created_by,
            organization_id=task.organization_id
        )
        
        db.add(result)
        await db.commit()
        
    except Exception as e:
        # Update task status to failed
        task.status = Status.FAILED
        task.completed_at = datetime.utcnow()
        task.error_message = str(e)
        await db.commit()


@router.post("/pipelines", response_model=ComputationPipelineResponse)
async def create_computation_pipeline(
    pipeline: ComputationPipelineCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new computation pipeline."""
    await require_permission(current_user, "computation:write")
    
    db_pipeline = ComputationPipeline(
        name=pipeline.name,
        description=pipeline.description,
        steps=pipeline.steps,
        config=pipeline.config,
        status=Status.ACTIVE,
        created_by=current_user.id,
        organization_id=current_user.organization_id
    )
    
    db.add(db_pipeline)
    await db.commit()
    await db.refresh(db_pipeline)
    
    return ComputationPipelineResponse.from_orm(db_pipeline)


@router.get("/pipelines", response_model=List[ComputationPipelineResponse])
async def list_computation_pipelines(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all computation pipelines."""
    await require_permission(current_user, "computation:read")
    
    pipelines = await db.execute(
        select(ComputationPipeline).where(
            ComputationPipeline.organization_id == current_user.organization_id
        ).order_by(desc(ComputationPipeline.created_at))
    )
    pipelines = pipelines.scalars().all()
    
    return [ComputationPipelineResponse.from_orm(p) for p in pipelines]


@router.post("/pipelines/{pipeline_id}/execute")
async def execute_computation_pipeline(
    pipeline_id: int,
    execution_request: PipelineExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute a computation pipeline."""
    await require_permission(current_user, "computation:execute")
    
    pipeline = await db.execute(
        select(ComputationPipeline).where(
            and_(
                ComputationPipeline.id == pipeline_id,
                ComputationPipeline.organization_id == current_user.organization_id
            )
        )
    )
    pipeline = pipeline.scalar_one_or_none()
    
    if not pipeline:
        raise HTTPException(status_code=404, detail="Computation pipeline not found")
    
    # Create tasks for each pipeline step
    tasks = []
    for i, step in enumerate(pipeline.steps):
        task = ComputationTask(
            job_id=None,  # Pipeline tasks don't have a job_id
            name=f"{pipeline.name} - Step {i+1}: {step.get('name', 'Unknown')}",
            task_type=step.get('type', 'custom'),
            config=step.get('config', {}),
            status=Status.PENDING,
            created_by=current_user.id,
            organization_id=current_user.organization_id
        )
        tasks.append(task)
    
    db.add_all(tasks)
    await db.commit()
    
    # Refresh tasks to get IDs
    for task in tasks:
        await db.refresh(task)
    
    # Add background task to execute the pipeline
    background_tasks.add_task(execute_pipeline_task, [t.id for t in tasks], db)
    
    return {
        "message": "Pipeline execution started",
        "task_ids": [t.id for t in tasks],
        "total_steps": len(tasks)
    }


async def execute_pipeline_task(task_ids: List[int], db: AsyncSession):
    """Background task to execute a computation pipeline."""
    # This is a simplified implementation
    # In a real system, you'd want proper pipeline orchestration
    
    for task_id in task_ids:
        task = await db.execute(
            select(ComputationTask).where(ComputationTask.id == task_id)
        )
        task = task.scalar_one_or_none()
        
        if not task:
            continue
        
        try:
            # Update task status to running
            task.status = Status.RUNNING
            task.started_at = datetime.utcnow()
            await db.commit()
            
            # Simulate step execution
            await asyncio.sleep(3)  # Simulate work
            
            # Update task status to completed
            task.status = Status.SUCCESS
            task.completed_at = datetime.utcnow()
            task.result = {"message": f"Step {task.name} completed successfully"}
            
            await db.commit()
            
        except Exception as e:
            # Update task status to failed
            task.status = Status.FAILED
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)
            await db.commit()
            break  # Stop pipeline on first failure


@router.get("/tasks", response_model=PaginatedResponse[ComputationTaskResponse])
async def list_computation_tasks(
    pagination: PaginationParams = Depends(),
    status: Optional[Status] = Query(None),
    job_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List computation tasks with filtering."""
    await require_permission(current_user, "computation:read")
    
    query = select(ComputationTask).where(
        ComputationTask.organization_id == current_user.organization_id
    )
    
    if status:
        query = query.where(ComputationTask.status == status)
    if job_id:
        query = query.where(ComputationTask.job_id == job_id)
    
    query = query.order_by(desc(ComputationTask.created_at))
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # Get total count
    count_query = select(ComputationTask).where(
        ComputationTask.organization_id == current_user.organization_id
    )
    if status:
        count_query = count_query.where(ComputationTask.status == status)
    if job_id:
        count_query = count_query.where(ComputationTask.job_id == job_id)
    
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    return PaginatedResponse(
        items=[ComputationTaskResponse.from_orm(t) for t in tasks],
        total=total_count,
        page=pagination.page,
        size=pagination.limit,
        pages=(total_count + pagination.limit - 1) // pagination.limit
    )


@router.get("/tasks/{task_id}", response_model=ComputationTaskResponse)
async def get_computation_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific computation task."""
    await require_permission(current_user, "computation:read")
    
    task = await db.execute(
        select(ComputationTask).where(
            and_(
                ComputationTask.id == task_id,
                ComputationTask.organization_id == current_user.organization_id
            )
        )
    )
    task = task.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Computation task not found")
    
    return ComputationTaskResponse.from_orm(task)


@router.get("/results", response_model=PaginatedResponse[ComputationResultResponse])
async def list_computation_results(
    pagination: PaginationParams = Depends(),
    task_id: Optional[int] = Query(None),
    job_id: Optional[int] = Query(None),
    result_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List computation results with filtering."""
    await require_permission(current_user, "computation:read")
    
    query = select(ComputationResult).where(
        ComputationResult.organization_id == current_user.organization_id
    )
    
    if task_id:
        query = query.where(ComputationResult.task_id == task_id)
    if job_id:
        query = query.where(ComputationResult.job_id == job_id)
    if result_type:
        query = query.where(ComputationResult.result_type == result_type)
    
    query = query.order_by(desc(ComputationResult.created_at))
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    results = result.scalars().all()
    
    # Get total count
    count_query = select(ComputationResult).where(
        ComputationResult.organization_id == current_user.organization_id
    )
    if task_id:
        count_query = count_query.where(ComputationResult.task_id == task_id)
    if job_id:
        count_query = count_query.where(ComputationResult.job_id == job_id)
    if result_type:
        count_query = count_query.where(ComputationResult.result_type == result_type)
    
    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())
    
    return PaginatedResponse(
        items=[ComputationResultResponse.from_orm(r) for r in results],
        total=total_count,
        page=pagination.page,
        size=pagination.limit,
        pages=(total_count + pagination.limit - 1) // pagination.limit
    )


@router.get("/dashboard")
async def get_computation_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get computation dashboard data."""
    await require_permission(current_user, "computation:read")
    
    # Get recent jobs
    recent_jobs = await db.execute(
        select(ComputationJob).where(
            ComputationJob.organization_id == current_user.organization_id
        ).order_by(desc(ComputationJob.created_at)).limit(5)
    )
    recent_jobs = recent_jobs.scalars().all()
    
    # Get recent tasks
    recent_tasks = await db.execute(
        select(ComputationTask).where(
            ComputationTask.organization_id == current_user.organization_id
        ).order_by(desc(ComputationTask.created_at)).limit(10)
    )
    recent_tasks = recent_tasks.scalars().all()
    
    # Get status counts
    job_status_counts = {
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0
    }
    
    task_status_counts = {
        "pending": 0,
        "running": 0,
        "completed": 0,
        "failed": 0
    }
    
    for job in recent_jobs:
        if job.status in job_status_counts:
            job_status_counts[job.status] += 1
    
    for task in recent_tasks:
        if task.status in task_status_counts:
            task_status_counts[task.status] += 1
    
    return {
        "recent_jobs": [ComputationJobResponse.from_orm(j) for j in recent_jobs],
        "recent_tasks": [ComputationTaskResponse.from_orm(t) for t in recent_tasks],
        "job_status_counts": job_status_counts,
        "task_status_counts": task_status_counts,
        "summary": {
            "total_jobs": len(recent_jobs),
            "total_tasks": len(recent_tasks),
            "success_rate": 85.5  # This would be calculated from actual data
        }
    } 