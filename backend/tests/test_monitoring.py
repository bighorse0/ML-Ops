import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.monitoring import DataQualityMetric, PerformanceMetric, Alert, AlertRule
from models.user import User
from models.organization import Organization


class TestMonitoringAPI:
    """Test suite for Monitoring API endpoints."""

    def test_create_data_quality_metric_success(self, client: TestClient, auth_headers: dict, sample_data_quality_data: dict):
        """Test successful data quality metric creation."""
        response = client.post("/api/monitoring/data-quality", json=sample_data_quality_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["feature_id"] == sample_data_quality_data["feature_id"]
        assert data["metric_type"] == sample_data_quality_data["metric_type"]
        assert data["value"] == sample_data_quality_data["value"]
        assert data["threshold"] == sample_data_quality_data["threshold"]
        assert data["status"] == sample_data_quality_data["status"]
        assert "id" in data
        assert "created_at" in data

    def test_create_data_quality_metric_validation_error(self, client: TestClient, auth_headers: dict):
        """Test data quality metric creation with validation errors."""
        invalid_data = {
            "feature_id": 0,  # Invalid feature ID
            "metric_type": "invalid_type",  # Invalid metric type
            "value": -1,  # Invalid value
            "threshold": -1,  # Invalid threshold
            "status": "invalid_status"  # Invalid status
        }
        
        response = client.post("/api/monitoring/data-quality", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_data_quality_metrics(self, client: TestClient, auth_headers: dict, sample_data_quality_data: dict):
        """Test successful data quality metrics retrieval."""
        # Create metric first
        create_response = client.post("/api/monitoring/data-quality", json=sample_data_quality_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        # Get metrics
        response = client.get("/api/monitoring/data-quality", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    def test_create_performance_metric_success(self, client: TestClient, auth_headers: dict, sample_performance_data: dict):
        """Test successful performance metric creation."""
        response = client.post("/api/monitoring/performance", json=sample_performance_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["feature_id"] == sample_performance_data["feature_id"]
        assert data["metric_type"] == sample_performance_data["metric_type"]
        assert data["value"] == sample_performance_data["value"]
        assert data["unit"] == sample_performance_data["unit"]
        assert "id" in data
        assert "created_at" in data

    def test_get_performance_metrics(self, client: TestClient, auth_headers: dict, sample_performance_data: dict):
        """Test successful performance metrics retrieval."""
        # Create metric first
        create_response = client.post("/api/monitoring/performance", json=sample_performance_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        # Get metrics
        response = client.get("/api/monitoring/performance", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    def test_create_alert_rule_success(self, client: TestClient, auth_headers: dict, sample_alert_rule_data: dict):
        """Test successful alert rule creation."""
        response = client.post("/api/monitoring/alerts/rules", json=sample_alert_rule_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == sample_alert_rule_data["name"]
        assert data["description"] == sample_alert_rule_data["description"]
        assert data["metric_type"] == sample_alert_rule_data["metric_type"]
        assert data["condition"] == sample_alert_rule_data["condition"]
        assert data["threshold"] == sample_alert_rule_data["threshold"]
        assert data["severity"] == sample_alert_rule_data["severity"]
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data

    def test_create_alert_rule_validation_error(self, client: TestClient, auth_headers: dict):
        """Test alert rule creation with validation errors."""
        invalid_data = {
            "name": "",  # Empty name
            "description": "Test description",
            "metric_type": "invalid_type",  # Invalid metric type
            "condition": "invalid_condition",  # Invalid condition
            "threshold": -1,  # Invalid threshold
            "severity": "invalid_severity"  # Invalid severity
        }
        
        response = client.post("/api/monitoring/alerts/rules", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_alert_rules(self, client: TestClient, auth_headers: dict, sample_alert_rule_data: dict):
        """Test successful alert rules retrieval."""
        # Create rule first
        create_response = client.post("/api/monitoring/alerts/rules", json=sample_alert_rule_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        # Get rules
        response = client.get("/api/monitoring/alerts/rules", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    def test_update_alert_rule_success(self, client: TestClient, auth_headers: dict, sample_alert_rule_data: dict):
        """Test successful alert rule update."""
        # Create rule first
        create_response = client.post("/api/monitoring/alerts/rules", json=sample_alert_rule_data, headers=auth_headers)
        assert create_response.status_code == 201
        rule_id = create_response.json()["id"]
        
        # Update rule
        update_data = {
            "description": "Updated description",
            "threshold": 0.95,
            "severity": "high"
        }
        
        response = client.put(f"/api/monitoring/alerts/rules/{rule_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["threshold"] == update_data["threshold"]
        assert data["severity"] == update_data["severity"]

    def test_delete_alert_rule_success(self, client: TestClient, auth_headers: dict, sample_alert_rule_data: dict):
        """Test successful alert rule deletion."""
        # Create rule first
        create_response = client.post("/api/monitoring/alerts/rules", json=sample_alert_rule_data, headers=auth_headers)
        assert create_response.status_code == 201
        rule_id = create_response.json()["id"]
        
        # Delete rule
        response = client.delete(f"/api/monitoring/alerts/rules/{rule_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]

    def test_get_alerts(self, client: TestClient, auth_headers: dict):
        """Test successful alerts retrieval."""
        response = client.get("/api/monitoring/alerts", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_alerts_with_filters(self, client: TestClient, auth_headers: dict):
        """Test alerts retrieval with filters."""
        response = client.get("/api/monitoring/alerts?severity=high&status=active", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_monitoring_dashboard(self, client: TestClient, auth_headers: dict):
        """Test monitoring dashboard data retrieval."""
        response = client.get("/api/monitoring/dashboard", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "data_quality" in data
        assert "performance" in data
        assert "alerts" in data

    def test_get_health_checks(self, client: TestClient, auth_headers: dict):
        """Test health checks endpoint."""
        response = client.get("/api/monitoring/health", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data

    def test_get_metric_data(self, client: TestClient, auth_headers: dict):
        """Test metric data retrieval."""
        response = client.get("/api/monitoring/metrics/data?metric_type=data_quality&time_range=24h", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "time_range" in data

    def test_monitoring_unauthorized(self, client: TestClient):
        """Test monitoring endpoints without authentication."""
        response = client.get("/api/monitoring/dashboard")
        assert response.status_code == 401

    def test_monitoring_permissions_readonly_user(self, client: TestClient, readonly_auth_headers: dict):
        """Test monitoring endpoints with readonly user permissions."""
        # Should be able to read
        response = client.get("/api/monitoring/dashboard", headers=readonly_auth_headers)
        assert response.status_code == 200
        
        # Should not be able to create
        sample_data = {
            "feature_id": 1,
            "metric_type": "completeness",
            "value": 0.95,
            "threshold": 0.9,
            "status": "pass"
        }
        response = client.post("/api/monitoring/data-quality", json=sample_data, headers=readonly_auth_headers)
        assert response.status_code == 403


class TestMonitoringValidation:
    """Test suite for monitoring data validation."""

    def test_data_quality_metric_type_validation(self, client: TestClient, auth_headers: dict):
        """Test data quality metric type validation."""
        invalid_data = {
            "feature_id": 1,
            "metric_type": "invalid_type",
            "value": 0.95,
            "threshold": 0.9,
            "status": "pass"
        }
        
        response = client.post("/api/monitoring/data-quality", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_performance_metric_type_validation(self, client: TestClient, auth_headers: dict):
        """Test performance metric type validation."""
        invalid_data = {
            "feature_id": 1,
            "metric_type": "invalid_type",
            "value": 100,
            "unit": "ms"
        }
        
        response = client.post("/api/monitoring/performance", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_alert_rule_condition_validation(self, client: TestClient, auth_headers: dict):
        """Test alert rule condition validation."""
        invalid_data = {
            "name": "Test Rule",
            "description": "Test description",
            "metric_type": "data_quality",
            "condition": "invalid_condition",
            "threshold": 0.9,
            "severity": "medium"
        }
        
        response = client.post("/api/monitoring/alerts/rules", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422


class TestMonitoringSearchAndFiltering:
    """Test suite for monitoring search and filtering."""

    def test_data_quality_filter_by_status(self, client: TestClient, auth_headers: dict, sample_data_quality_data: dict):
        """Test data quality metrics filtering by status."""
        # Create metrics with different statuses
        pass_data = sample_data_quality_data.copy()
        pass_data["status"] = "pass"
        
        fail_data = sample_data_quality_data.copy()
        fail_data["status"] = "fail"
        
        client.post("/api/monitoring/data-quality", json=pass_data, headers=auth_headers)
        client.post("/api/monitoring/data-quality", json=fail_data, headers=auth_headers)
        
        # Filter by pass status
        response = client.get("/api/monitoring/data-quality?status=pass", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "pass" for item in data["items"])

    def test_performance_filter_by_metric_type(self, client: TestClient, auth_headers: dict, sample_performance_data: dict):
        """Test performance metrics filtering by metric type."""
        # Create metrics with different types
        latency_data = sample_performance_data.copy()
        latency_data["metric_type"] = "latency"
        
        throughput_data = sample_performance_data.copy()
        throughput_data["metric_type"] = "throughput"
        
        client.post("/api/monitoring/performance", json=latency_data, headers=auth_headers)
        client.post("/api/monitoring/performance", json=throughput_data, headers=auth_headers)
        
        # Filter by latency
        response = client.get("/api/monitoring/performance?metric_type=latency", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["metric_type"] == "latency" for item in data["items"])

    def test_alerts_filter_by_severity(self, client: TestClient, auth_headers: dict):
        """Test alerts filtering by severity."""
        response = client.get("/api/monitoring/alerts?severity=high", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Note: This test assumes alerts exist or handles empty results appropriately 