import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.computation import ComputationJob, ComputationPipeline, ComputationTask, ComputationResult
from models.user import User
from models.organization import Organization


class TestComputationAPI:
    """Test suite for Computation API endpoints."""

    def test_create_computation_job_success(self, client: TestClient, auth_headers: dict, sample_computation_job_data: dict):
        """Test successful computation job creation."""
        response = client.post("/api/computation/jobs", json=sample_computation_job_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == sample_computation_job_data["name"]
        assert data["description"] == sample_computation_job_data["description"]
        assert data["job_type"] == sample_computation_job_data["job_type"]
        assert data["status"] == "pending"
        assert data["priority"] == sample_computation_job_data["priority"]
        assert "id" in data
        assert "created_at" in data

    def test_create_computation_job_validation_error(self, client: TestClient, auth_headers: dict):
        """Test computation job creation with validation errors."""
        invalid_data = {
            "name": "",  # Empty name
            "description": "Test description",
            "job_type": "invalid_type",  # Invalid job type
            "priority": "invalid_priority",  # Invalid priority
            "config": {"invalid": "config"}
        }
        
        response = client.post("/api/computation/jobs", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_computation_job_success(self, client: TestClient, auth_headers: dict, sample_computation_job_data: dict):
        """Test successful computation job retrieval."""
        # Create job first
        create_response = client.post("/api/computation/jobs", json=sample_computation_job_data, headers=auth_headers)
        assert create_response.status_code == 201
        job_id = create_response.json()["id"]
        
        # Get the job
        response = client.get(f"/api/computation/jobs/{job_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["name"] == sample_computation_job_data["name"]

    def test_get_computation_job_not_found(self, client: TestClient, auth_headers: dict):
        """Test computation job retrieval for non-existent job."""
        response = client.get("/api/computation/jobs/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_list_computation_jobs_success(self, client: TestClient, auth_headers: dict, sample_computation_job_data: dict):
        """Test successful computation job listing."""
        # Create multiple jobs
        for i in range(3):
            job_data = sample_computation_job_data.copy()
            job_data["name"] = f"{sample_computation_job_data['name']}_{i}"
            response = client.post("/api/computation/jobs", json=job_data, headers=auth_headers)
            assert response.status_code == 201
        
        # List jobs
        response = client.get("/api/computation/jobs", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert len(data["items"]) >= 3

    def test_list_computation_jobs_with_filters(self, client: TestClient, auth_headers: dict, sample_computation_job_data: dict):
        """Test computation job listing with filters."""
        # Create jobs with different types
        batch_job = sample_computation_job_data.copy()
        batch_job["name"] = "batch_job"
        batch_job["job_type"] = "batch"
        
        streaming_job = sample_computation_job_data.copy()
        streaming_job["name"] = "streaming_job"
        streaming_job["job_type"] = "streaming"
        
        client.post("/api/computation/jobs", json=batch_job, headers=auth_headers)
        client.post("/api/computation/jobs", json=streaming_job, headers=auth_headers)
        
        # Filter by job type
        response = client.get("/api/computation/jobs?job_type=batch", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["job_type"] == "batch" for item in data["items"])

    def test_update_computation_job_success(self, client: TestClient, auth_headers: dict, sample_computation_job_data: dict):
        """Test successful computation job update."""
        # Create job first
        create_response = client.post("/api/computation/jobs", json=sample_computation_job_data, headers=auth_headers)
        assert create_response.status_code == 201
        job_id = create_response.json()["id"]
        
        # Update job
        update_data = {
            "description": "Updated description",
            "priority": "high",
            "config": {"updated": True}
        }
        
        response = client.put(f"/api/computation/jobs/{job_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["priority"] == update_data["priority"]
        assert data["config"] == update_data["config"]

    def test_delete_computation_job_success(self, client: TestClient, auth_headers: dict, sample_computation_job_data: dict):
        """Test successful computation job deletion."""
        # Create job first
        create_response = client.post("/api/computation/jobs", json=sample_computation_job_data, headers=auth_headers)
        assert create_response.status_code == 201
        job_id = create_response.json()["id"]
        
        # Delete job
        response = client.delete(f"/api/computation/jobs/{job_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

    def test_create_computation_pipeline_success(self, client: TestClient, auth_headers: dict, sample_pipeline_data: dict):
        """Test successful computation pipeline creation."""
        response = client.post("/api/computation/pipelines", json=sample_pipeline_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == sample_pipeline_data["name"]
        assert data["description"] == sample_pipeline_data["description"]
        assert data["pipeline_type"] == sample_pipeline_data["pipeline_type"]
        assert data["status"] == "draft"
        assert "id" in data
        assert "created_at" in data

    def test_get_computation_pipeline_success(self, client: TestClient, auth_headers: dict, sample_pipeline_data: dict):
        """Test successful computation pipeline retrieval."""
        # Create pipeline first
        create_response = client.post("/api/computation/pipelines", json=sample_pipeline_data, headers=auth_headers)
        assert create_response.status_code == 201
        pipeline_id = create_response.json()["id"]
        
        # Get the pipeline
        response = client.get(f"/api/computation/pipelines/{pipeline_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pipeline_id
        assert data["name"] == sample_pipeline_data["name"]

    def test_list_computation_pipelines(self, client: TestClient, auth_headers: dict, sample_pipeline_data: dict):
        """Test successful computation pipeline listing."""
        # Create multiple pipelines
        for i in range(3):
            pipeline_data = sample_pipeline_data.copy()
            pipeline_data["name"] = f"{sample_pipeline_data['name']}_{i}"
            response = client.post("/api/computation/pipelines", json=pipeline_data, headers=auth_headers)
            assert response.status_code == 201
        
        # List pipelines
        response = client.get("/api/computation/pipelines", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 3

    def test_create_computation_task_success(self, client: TestClient, auth_headers: dict, sample_task_data: dict):
        """Test successful computation task creation."""
        response = client.post("/api/computation/tasks", json=sample_task_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == sample_task_data["name"]
        assert data["description"] == sample_task_data["description"]
        assert data["task_type"] == sample_task_data["task_type"]
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data

    def test_get_computation_task_success(self, client: TestClient, auth_headers: dict, sample_task_data: dict):
        """Test successful computation task retrieval."""
        # Create task first
        create_response = client.post("/api/computation/tasks", json=sample_task_data, headers=auth_headers)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]
        
        # Get the task
        response = client.get(f"/api/computation/tasks/{task_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["name"] == sample_task_data["name"]

    def test_list_computation_tasks(self, client: TestClient, auth_headers: dict, sample_task_data: dict):
        """Test successful computation task listing."""
        # Create multiple tasks
        for i in range(3):
            task_data = sample_task_data.copy()
            task_data["name"] = f"{sample_task_data['name']}_{i}"
            response = client.post("/api/computation/tasks", json=task_data, headers=auth_headers)
            assert response.status_code == 201
        
        # List tasks
        response = client.get("/api/computation/tasks", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 3

    def test_create_computation_result_success(self, client: TestClient, auth_headers: dict, sample_result_data: dict):
        """Test successful computation result creation."""
        response = client.post("/api/computation/results", json=sample_result_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["job_id"] == sample_result_data["job_id"]
        assert data["task_id"] == sample_result_data["task_id"]
        assert data["result_type"] == sample_result_data["result_type"]
        assert data["status"] == "completed"
        assert "id" in data
        assert "created_at" in data

    def test_get_computation_result_success(self, client: TestClient, auth_headers: dict, sample_result_data: dict):
        """Test successful computation result retrieval."""
        # Create result first
        create_response = client.post("/api/computation/results", json=sample_result_data, headers=auth_headers)
        assert create_response.status_code == 201
        result_id = create_response.json()["id"]
        
        # Get the result
        response = client.get(f"/api/computation/results/{result_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == result_id
        assert data["job_id"] == sample_result_data["job_id"]

    def test_list_computation_results(self, client: TestClient, auth_headers: dict, sample_result_data: dict):
        """Test successful computation result listing."""
        # Create multiple results
        for i in range(3):
            result_data = sample_result_data.copy()
            result_data["result_type"] = f"type_{i}"
            response = client.post("/api/computation/results", json=result_data, headers=auth_headers)
            assert response.status_code == 201
        
        # List results
        response = client.get("/api/computation/results", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 3

    def test_execute_computation_job(self, client: TestClient, auth_headers: dict, sample_computation_job_data: dict):
        """Test computation job execution."""
        # Create job first
        create_response = client.post("/api/computation/jobs", json=sample_computation_job_data, headers=auth_headers)
        assert create_response.status_code == 201
        job_id = create_response.json()["id"]
        
        # Execute job
        response = client.post(f"/api/computation/jobs/{job_id}/execute", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data
        assert "status" in data

    def test_get_computation_dashboard(self, client: TestClient, auth_headers: dict):
        """Test computation dashboard data retrieval."""
        response = client.get("/api/computation/dashboard", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "jobs" in data
        assert "pipelines" in data
        assert "tasks" in data

    def test_computation_unauthorized(self, client: TestClient):
        """Test computation endpoints without authentication."""
        response = client.get("/api/computation/jobs")
        assert response.status_code == 401

    def test_computation_permissions_readonly_user(self, client: TestClient, readonly_auth_headers: dict):
        """Test computation endpoints with readonly user permissions."""
        # Should be able to read
        response = client.get("/api/computation/jobs", headers=readonly_auth_headers)
        assert response.status_code == 200
        
        # Should not be able to create
        sample_data = {
            "name": "Test Job",
            "description": "Test description",
            "job_type": "batch",
            "priority": "medium",
            "config": {}
        }
        response = client.post("/api/computation/jobs", json=sample_data, headers=readonly_auth_headers)
        assert response.status_code == 403


class TestComputationValidation:
    """Test suite for computation data validation."""

    def test_computation_job_type_validation(self, client: TestClient, auth_headers: dict):
        """Test computation job type validation."""
        invalid_data = {
            "name": "Test Job",
            "description": "Test description",
            "job_type": "invalid_type",
            "priority": "medium",
            "config": {}
        }
        
        response = client.post("/api/computation/jobs", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_computation_priority_validation(self, client: TestClient, auth_headers: dict):
        """Test computation priority validation."""
        invalid_data = {
            "name": "Test Job",
            "description": "Test description",
            "job_type": "batch",
            "priority": "invalid_priority",
            "config": {}
        }
        
        response = client.post("/api/computation/jobs", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_pipeline_type_validation(self, client: TestClient, auth_headers: dict):
        """Test pipeline type validation."""
        invalid_data = {
            "name": "Test Pipeline",
            "description": "Test description",
            "pipeline_type": "invalid_type",
            "config": {}
        }
        
        response = client.post("/api/computation/pipelines", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_task_type_validation(self, client: TestClient, auth_headers: dict):
        """Test task type validation."""
        invalid_data = {
            "name": "Test Task",
            "description": "Test description",
            "task_type": "invalid_type",
            "config": {}
        }
        
        response = client.post("/api/computation/tasks", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422


class TestComputationSearchAndFiltering:
    """Test suite for computation search and filtering."""

    def test_jobs_filter_by_status(self, client: TestClient, auth_headers: dict, sample_computation_job_data: dict):
        """Test computation jobs filtering by status."""
        # Create jobs with different statuses (they start as pending)
        for i in range(3):
            job_data = sample_computation_job_data.copy()
            job_data["name"] = f"job_{i}"
            client.post("/api/computation/jobs", json=job_data, headers=auth_headers)
        
        # Filter by pending status
        response = client.get("/api/computation/jobs?status=pending", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "pending" for item in data["items"])

    def test_jobs_filter_by_job_type(self, client: TestClient, auth_headers: dict, sample_computation_job_data: dict):
        """Test computation jobs filtering by job type."""
        # Create jobs with different types
        batch_job = sample_computation_job_data.copy()
        batch_job["name"] = "batch_job"
        batch_job["job_type"] = "batch"
        
        streaming_job = sample_computation_job_data.copy()
        streaming_job["name"] = "streaming_job"
        streaming_job["job_type"] = "streaming"
        
        client.post("/api/computation/jobs", json=batch_job, headers=auth_headers)
        client.post("/api/computation/jobs", json=streaming_job, headers=auth_headers)
        
        # Filter by batch type
        response = client.get("/api/computation/jobs?job_type=batch", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["job_type"] == "batch" for item in data["items"])

    def test_pipelines_filter_by_status(self, client: TestClient, auth_headers: dict, sample_pipeline_data: dict):
        """Test computation pipelines filtering by status."""
        # Create pipelines (they start as draft)
        for i in range(3):
            pipeline_data = sample_pipeline_data.copy()
            pipeline_data["name"] = f"pipeline_{i}"
            client.post("/api/computation/pipelines", json=pipeline_data, headers=auth_headers)
        
        # Filter by draft status
        response = client.get("/api/computation/pipelines?status=draft", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "draft" for item in data["items"])

    def test_tasks_filter_by_task_type(self, client: TestClient, auth_headers: dict, sample_task_data: dict):
        """Test computation tasks filtering by task type."""
        # Create tasks with different types
        transform_task = sample_task_data.copy()
        transform_task["name"] = "transform_task"
        transform_task["task_type"] = "transform"
        
        aggregate_task = sample_task_data.copy()
        aggregate_task["name"] = "aggregate_task"
        aggregate_task["task_type"] = "aggregate"
        
        client.post("/api/computation/tasks", json=transform_task, headers=auth_headers)
        client.post("/api/computation/tasks", json=aggregate_task, headers=auth_headers)
        
        # Filter by transform type
        response = client.get("/api/computation/tasks?task_type=transform", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["task_type"] == "transform" for item in data["items"]) 