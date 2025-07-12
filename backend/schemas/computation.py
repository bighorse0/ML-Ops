from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from .common import Status, ComputationType


class JobScheduleType(str, Enum):
    """Enum for job schedule types."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"


class ComputationJobCreate(BaseModel):
    """Schema for creating a computation job."""
    name: str = Field(..., description="Job name")
    description: str = Field(..., description="Job description")
    job_type: ComputationType = Field(..., description="Type of computation job")
    config: Dict[str, Any] = Field(..., description="Job configuration")
    schedule: Optional[Dict[str, Any]] = Field(default=None, description="Job schedule")

    @validator('name', 'description')
    def validate_required_fields(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Field cannot be empty')
        return v.strip()

    @validator('config')
    def validate_config(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Config must be a dictionary')
        return v


class ComputationJobUpdate(BaseModel):
    """Schema for updating a computation job."""
    name: Optional[str] = Field(None, description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    job_type: Optional[ComputationType] = Field(None, description="Type of computation job")
    config: Optional[Dict[str, Any]] = Field(None, description="Job configuration")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Job schedule")
    status: Optional[Status] = Field(None, description="Job status")

    @validator('name', 'description')
    def validate_required_fields(cls, v):
        if v is not None and (not v or len(v.strip()) == 0):
            raise ValueError('Field cannot be empty')
        return v.strip() if v else v


class ComputationJobResponse(BaseModel):
    """Schema for computation job response."""
    id: int
    name: str
    description: str
    job_type: ComputationType
    config: Dict[str, Any]
    schedule: Optional[Dict[str, Any]]
    status: Status
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    organization_id: int

    class Config:
        from_attributes = True


class ComputationPipelineCreate(BaseModel):
    """Schema for creating a computation pipeline."""
    name: str = Field(..., description="Pipeline name")
    description: str = Field(..., description="Pipeline description")
    steps: List[Dict[str, Any]] = Field(..., description="Pipeline steps")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Pipeline configuration")

    @validator('name', 'description')
    def validate_required_fields(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Field cannot be empty')
        return v.strip()

    @validator('steps')
    def validate_steps(cls, v):
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError('Steps must be a non-empty list')
        for step in v:
            if not isinstance(step, dict):
                raise ValueError('Each step must be a dictionary')
            if 'name' not in step or 'type' not in step:
                raise ValueError('Each step must have name and type')
        return v


class ComputationPipelineResponse(BaseModel):
    """Schema for computation pipeline response."""
    id: int
    name: str
    description: str
    steps: List[Dict[str, Any]]
    config: Optional[Dict[str, Any]]
    status: Status
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    organization_id: int

    class Config:
        from_attributes = True


class ComputationTaskCreate(BaseModel):
    """Schema for creating a computation task."""
    job_id: Optional[int] = Field(None, description="Associated job ID")
    name: str = Field(..., description="Task name")
    task_type: ComputationType = Field(..., description="Type of computation task")
    config: Dict[str, Any] = Field(..., description="Task configuration")

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        return v.strip()

    @validator('config')
    def validate_config(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Config must be a dictionary')
        return v


class ComputationTaskResponse(BaseModel):
    """Schema for computation task response."""
    id: int
    job_id: Optional[int]
    name: str
    task_type: ComputationType
    config: Dict[str, Any]
    status: Status
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    organization_id: int

    class Config:
        from_attributes = True


class ComputationResultResponse(BaseModel):
    """Schema for computation result response."""
    id: int
    task_id: int
    job_id: Optional[int]
    result_type: str
    data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: int
    updated_by: Optional[int]
    organization_id: int

    class Config:
        from_attributes = True


class JobExecutionRequest(BaseModel):
    """Schema for job execution request."""
    config: Optional[Dict[str, Any]] = Field(default=None, description="Override job configuration")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Execution parameters")
    priority: Optional[int] = Field(default=0, ge=0, le=10, description="Execution priority")

    @validator('priority')
    def validate_priority(cls, v):
        if v < 0 or v > 10:
            raise ValueError('Priority must be between 0 and 10')
        return v


class PipelineExecutionRequest(BaseModel):
    """Schema for pipeline execution request."""
    config: Optional[Dict[str, Any]] = Field(default=None, description="Override pipeline configuration")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Execution parameters")
    parallel: bool = Field(default=False, description="Execute steps in parallel")

    @validator('config')
    def validate_config(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('Config must be a dictionary')
        return v


class ComputationConfig(BaseModel):
    """Schema for computation configuration."""
    max_concurrent_jobs: int = Field(default=10, ge=1, le=100)
    max_concurrent_tasks: int = Field(default=50, ge=1, le=500)
    job_timeout_minutes: int = Field(default=60, ge=1, le=1440)
    task_timeout_minutes: int = Field(default=30, ge=1, le=720)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=60, ge=1, le=3600)


class ComputationMetrics(BaseModel):
    """Schema for computation metrics."""
    total_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_job_duration: float
    average_task_duration: float
    success_rate: float


class ComputationDashboard(BaseModel):
    """Schema for computation dashboard data."""
    recent_jobs: List[ComputationJobResponse]
    recent_tasks: List[ComputationTaskResponse]
    job_status_counts: Dict[str, int]
    task_status_counts: Dict[str, int]
    summary: Dict[str, Any]


class PipelineStep(BaseModel):
    """Schema for pipeline step."""
    name: str
    type: ComputationType
    config: Dict[str, Any]
    dependencies: Optional[List[str]] = Field(default=None, description="Step dependencies")
    timeout_minutes: Optional[int] = Field(default=None, ge=1, le=720)
    retry_attempts: Optional[int] = Field(default=None, ge=0, le=10)

    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Step name cannot be empty')
        return v.strip()

    @validator('config')
    def validate_config(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Step config must be a dictionary')
        return v


class PipelineDefinition(BaseModel):
    """Schema for pipeline definition."""
    name: str
    description: str
    version: str = Field(default="1.0.0")
    steps: List[PipelineStep]
    config: Optional[Dict[str, Any]] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None)

    @validator('name', 'description')
    def validate_required_fields(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Field cannot be empty')
        return v.strip()

    @validator('steps')
    def validate_steps(cls, v):
        if not isinstance(v, list) or len(v) == 0:
            raise ValueError('Steps must be a non-empty list')
        return v 