import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.feature import Feature
from models.user import User
from models.organization import Organization


class TestFeaturesAPI:
    """Test suite for Features API endpoints."""

    def test_create_feature_success(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test successful feature creation."""
        response = client.post("/api/features", json=sample_feature_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == sample_feature_data["name"]
        assert data["description"] == sample_feature_data["description"]
        assert data["data_type"] == sample_feature_data["data_type"]
        assert data["feature_type"] == sample_feature_data["feature_type"]
        assert data["entity_type"] == sample_feature_data["entity_type"]
        assert data["serving_mode"] == sample_feature_data["serving_mode"]
        assert data["storage_type"] == sample_feature_data["storage_type"]
        assert data["tags"] == sample_feature_data["tags"]
        assert data["metadata"] == sample_feature_data["metadata"]
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_feature_validation_error(self, client: TestClient, auth_headers: dict):
        """Test feature creation with validation errors."""
        invalid_data = {
            "name": "",  # Empty name should fail
            "description": "Test description",
            "data_type": "invalid_type",  # Invalid data type
            "feature_type": "numeric",
            "entity_type": "user",
            "serving_mode": "online",
            "storage_type": "postgresql"
        }
        
        response = client.post("/api/features", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_feature_duplicate_name(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test feature creation with duplicate name."""
        # Create first feature
        response1 = client.post("/api/features", json=sample_feature_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Try to create second feature with same name
        response2 = client.post("/api/features", json=sample_feature_data, headers=auth_headers)
        assert response2.status_code == 409
        data = response2.json()
        assert "already exists" in data["detail"]

    def test_get_feature_success(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test successful feature retrieval."""
        # Create feature first
        create_response = client.post("/api/features", json=sample_feature_data, headers=auth_headers)
        assert create_response.status_code == 201
        feature_id = create_response.json()["id"]
        
        # Get the feature
        response = client.get(f"/api/features/{feature_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == feature_id
        assert data["name"] == sample_feature_data["name"]

    def test_get_feature_not_found(self, client: TestClient, auth_headers: dict):
        """Test feature retrieval for non-existent feature."""
        response = client.get("/api/features/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_list_features_success(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test successful feature listing."""
        # Create multiple features
        for i in range(3):
            feature_data = sample_feature_data.copy()
            feature_data["name"] = f"{sample_feature_data['name']}_{i}"
            response = client.post("/api/features", json=feature_data, headers=auth_headers)
            assert response.status_code == 201
        
        # List features
        response = client.get("/api/features", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert len(data["items"]) >= 3

    def test_list_features_with_pagination(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test feature listing with pagination."""
        # Create multiple features
        for i in range(5):
            feature_data = sample_feature_data.copy()
            feature_data["name"] = f"{sample_feature_data['name']}_{i}"
            response = client.post("/api/features", json=feature_data, headers=auth_headers)
            assert response.status_code == 201
        
        # Test pagination
        response = client.get("/api/features?page=1&limit=2", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["size"] == 2

    def test_list_features_with_filters(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test feature listing with filters."""
        # Create features with different types
        numeric_feature = sample_feature_data.copy()
        numeric_feature["name"] = "numeric_feature"
        numeric_feature["feature_type"] = "numeric"
        
        categorical_feature = sample_feature_data.copy()
        categorical_feature["name"] = "categorical_feature"
        categorical_feature["feature_type"] = "categorical"
        
        client.post("/api/features", json=numeric_feature, headers=auth_headers)
        client.post("/api/features", json=categorical_feature, headers=auth_headers)
        
        # Filter by feature type
        response = client.get("/api/features?feature_type=numeric", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["feature_type"] == "numeric" for item in data["items"])

    def test_update_feature_success(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test successful feature update."""
        # Create feature first
        create_response = client.post("/api/features", json=sample_feature_data, headers=auth_headers)
        assert create_response.status_code == 201
        feature_id = create_response.json()["id"]
        
        # Update feature
        update_data = {
            "description": "Updated description",
            "tags": ["updated", "tags"],
            "metadata": {"updated": True}
        }
        
        response = client.put(f"/api/features/{feature_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["tags"] == update_data["tags"]
        assert data["metadata"] == update_data["metadata"]

    def test_update_feature_not_found(self, client: TestClient, auth_headers: dict):
        """Test feature update for non-existent feature."""
        update_data = {"description": "Updated description"}
        
        response = client.put("/api/features/99999", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_delete_feature_success(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test successful feature deletion."""
        # Create feature first
        create_response = client.post("/api/features", json=sample_feature_data, headers=auth_headers)
        assert create_response.status_code == 201
        feature_id = create_response.json()["id"]
        
        # Delete feature
        response = client.delete(f"/api/features/{feature_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        # Verify feature is deleted
        get_response = client.get(f"/api/features/{feature_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_feature_not_found(self, client: TestClient, auth_headers: dict):
        """Test feature deletion for non-existent feature."""
        response = client.delete("/api/features/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_feature_permissions_readonly_user(self, client: TestClient, readonly_auth_headers: dict, sample_feature_data: dict):
        """Test that readonly users cannot create/update/delete features."""
        # Try to create feature
        response = client.post("/api/features", json=sample_feature_data, headers=readonly_auth_headers)
        assert response.status_code == 403
        
        # Try to update feature (if it existed)
        response = client.put("/api/features/1", json={"description": "Updated"}, headers=readonly_auth_headers)
        assert response.status_code == 403
        
        # Try to delete feature (if it existed)
        response = client.delete("/api/features/1", headers=readonly_auth_headers)
        assert response.status_code == 403
        
        # Should be able to read features
        response = client.get("/api/features", headers=readonly_auth_headers)
        assert response.status_code == 200

    def test_feature_unauthorized(self, client: TestClient, sample_feature_data: dict):
        """Test feature endpoints without authentication."""
        # Try to create feature without auth
        response = client.post("/api/features", json=sample_feature_data)
        assert response.status_code == 401
        
        # Try to get features without auth
        response = client.get("/api/features")
        assert response.status_code == 401
        
        # Try to update feature without auth
        response = client.put("/api/features/1", json={"description": "Updated"})
        assert response.status_code == 401
        
        # Try to delete feature without auth
        response = client.delete("/api/features/1")
        assert response.status_code == 401


class TestFeatureValuesAPI:
    """Test suite for Feature Values API endpoints."""

    def test_create_feature_value_success(self, client: TestClient, auth_headers: dict, sample_feature_value_data: dict):
        """Test successful feature value creation."""
        # First create a feature
        feature_data = {
            "name": "test_feature",
            "description": "Test feature",
            "data_type": "integer",
            "feature_type": "numeric",
            "entity_type": "user",
            "serving_mode": "online",
            "storage_type": "postgresql",
            "tags": ["test"],
            "metadata": {}
        }
        feature_response = client.post("/api/features", json=feature_data, headers=auth_headers)
        assert feature_response.status_code == 201
        feature_id = feature_response.json()["id"]
        
        # Create feature value
        value_data = sample_feature_value_data.copy()
        value_data["feature_id"] = feature_id
        
        response = client.post("/api/feature-values", json=value_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["feature_id"] == feature_id
        assert data["entity_id"] == value_data["entity_id"]
        assert data["value"] == value_data["value"]
        assert data["timestamp"] == value_data["timestamp"]
        assert data["metadata"] == value_data["metadata"]
        assert "id" in data
        assert "created_at" in data

    def test_create_feature_value_duplicate(self, client: TestClient, auth_headers: dict, sample_feature_value_data: dict):
        """Test feature value creation with duplicate entity and timestamp."""
        # First create a feature
        feature_data = {
            "name": "test_feature",
            "description": "Test feature",
            "data_type": "integer",
            "feature_type": "numeric",
            "entity_type": "user",
            "serving_mode": "online",
            "storage_type": "postgresql",
            "tags": ["test"],
            "metadata": {}
        }
        feature_response = client.post("/api/features", json=feature_data, headers=auth_headers)
        assert feature_response.status_code == 201
        feature_id = feature_response.json()["id"]
        
        # Create first feature value
        value_data = sample_feature_value_data.copy()
        value_data["feature_id"] = feature_id
        
        response1 = client.post("/api/feature-values", json=value_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = client.post("/api/feature-values", json=value_data, headers=auth_headers)
        assert response2.status_code == 409
        data = response2.json()
        assert "already exists" in data["detail"]

    def test_batch_create_feature_values(self, client: TestClient, auth_headers: dict):
        """Test batch creation of feature values."""
        # First create a feature
        feature_data = {
            "name": "test_feature",
            "description": "Test feature",
            "data_type": "integer",
            "feature_type": "numeric",
            "entity_type": "user",
            "serving_mode": "online",
            "storage_type": "postgresql",
            "tags": ["test"],
            "metadata": {}
        }
        feature_response = client.post("/api/features", json=feature_data, headers=auth_headers)
        assert feature_response.status_code == 201
        feature_id = feature_response.json()["id"]
        
        # Create batch of feature values
        batch_data = {
            "feature_values": [
                {
                    "feature_id": feature_id,
                    "entity_id": "user_1",
                    "value": 25,
                    "timestamp": "2024-01-01T00:00:00Z",
                    "metadata": {"source": "batch1"}
                },
                {
                    "feature_id": feature_id,
                    "entity_id": "user_2",
                    "value": 30,
                    "timestamp": "2024-01-01T00:00:00Z",
                    "metadata": {"source": "batch2"}
                }
            ]
        }
        
        response = client.post("/api/feature-values/batch", json=batch_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["created_count"] == 2
        assert len(data["feature_values"]) == 2

    def test_serve_feature_values(self, client: TestClient, auth_headers: dict):
        """Test feature value serving endpoint."""
        # First create a feature
        feature_data = {
            "name": "test_feature",
            "description": "Test feature",
            "data_type": "integer",
            "feature_type": "numeric",
            "entity_type": "user",
            "serving_mode": "online",
            "storage_type": "postgresql",
            "tags": ["test"],
            "metadata": {}
        }
        feature_response = client.post("/api/features", json=feature_data, headers=auth_headers)
        assert feature_response.status_code == 201
        feature_id = feature_response.json()["id"]
        
        # Create some feature values
        value_data = {
            "feature_id": feature_id,
            "entity_id": "user_123",
            "value": 25,
            "timestamp": "2024-01-01T00:00:00Z",
            "metadata": {}
        }
        client.post("/api/feature-values", json=value_data, headers=auth_headers)
        
        # Serve feature values
        serve_data = {
            "feature_ids": [feature_id],
            "entity_ids": ["user_123"],
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        response = client.post("/api/feature-values/serve", json=serve_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["entity_id"] == "user_123"
        assert feature_id in data[0]["features"]
        assert data[0]["features"][feature_id]["value"] == 25

    def test_get_feature_value_stats(self, client: TestClient, auth_headers: dict):
        """Test feature value statistics endpoint."""
        # First create a feature
        feature_data = {
            "name": "test_feature",
            "description": "Test feature",
            "data_type": "integer",
            "feature_type": "numeric",
            "entity_type": "user",
            "serving_mode": "online",
            "storage_type": "postgresql",
            "tags": ["test"],
            "metadata": {}
        }
        feature_response = client.post("/api/features", json=feature_data, headers=auth_headers)
        assert feature_response.status_code == 201
        feature_id = feature_response.json()["id"]
        
        # Create some feature values
        for i in range(3):
            value_data = {
                "feature_id": feature_id,
                "entity_id": f"user_{i}",
                "value": 20 + i * 5,
                "timestamp": "2024-01-01T00:00:00Z",
                "metadata": {}
            }
            client.post("/api/feature-values", json=value_data, headers=auth_headers)
        
        # Get statistics
        response = client.get(f"/api/feature-values/stats/feature/{feature_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["feature_id"] == feature_id
        assert data["total_values"] == 3
        assert data["unique_entities"] == 3
        assert "date_range" in data
        assert "value_stats" in data


class TestFeatureValidation:
    """Test suite for feature validation logic."""

    def test_feature_name_validation(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test feature name validation."""
        # Test empty name
        invalid_data = sample_feature_data.copy()
        invalid_data["name"] = ""
        
        response = client.post("/api/features", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
        
        # Test name with invalid characters
        invalid_data["name"] = "invalid name with spaces"
        response = client.post("/api/features", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
        
        # Test name too long
        invalid_data["name"] = "a" * 256
        response = client.post("/api/features", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_feature_data_type_validation(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test feature data type validation."""
        invalid_data = sample_feature_data.copy()
        invalid_data["data_type"] = "invalid_type"
        
        response = client.post("/api/features", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_feature_type_validation(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test feature type validation."""
        invalid_data = sample_feature_data.copy()
        invalid_data["feature_type"] = "invalid_type"
        
        response = client.post("/api/features", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_serving_mode_validation(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test serving mode validation."""
        invalid_data = sample_feature_data.copy()
        invalid_data["serving_mode"] = "invalid_mode"
        
        response = client.post("/api/features", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422


class TestFeatureSearchAndFiltering:
    """Test suite for feature search and filtering functionality."""

    def test_feature_search_by_name(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test feature search by name."""
        # Create features with different names
        feature1 = sample_feature_data.copy()
        feature1["name"] = "user_age_feature"
        
        feature2 = sample_feature_data.copy()
        feature2["name"] = "user_income_feature"
        
        client.post("/api/features", json=feature1, headers=auth_headers)
        client.post("/api/features", json=feature2, headers=auth_headers)
        
        # Search for age feature
        response = client.get("/api/features?name=age", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "age" in data["items"][0]["name"]

    def test_feature_filter_by_type(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test feature filtering by type."""
        # Create features with different types
        numeric_feature = sample_feature_data.copy()
        numeric_feature["name"] = "numeric_feature"
        numeric_feature["feature_type"] = "numeric"
        
        categorical_feature = sample_feature_data.copy()
        categorical_feature["name"] = "categorical_feature"
        categorical_feature["feature_type"] = "categorical"
        
        client.post("/api/features", json=numeric_feature, headers=auth_headers)
        client.post("/api/features", json=categorical_feature, headers=auth_headers)
        
        # Filter by numeric type
        response = client.get("/api/features?feature_type=numeric", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(item["feature_type"] == "numeric" for item in data["items"])

    def test_feature_filter_by_serving_mode(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test feature filtering by serving mode."""
        # Create features with different serving modes
        online_feature = sample_feature_data.copy()
        online_feature["name"] = "online_feature"
        online_feature["serving_mode"] = "online"
        
        offline_feature = sample_feature_data.copy()
        offline_feature["name"] = "offline_feature"
        offline_feature["serving_mode"] = "offline"
        
        client.post("/api/features", json=online_feature, headers=auth_headers)
        client.post("/api/features", json=offline_feature, headers=auth_headers)
        
        # Filter by online serving mode
        response = client.get("/api/features?serving_mode=online", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(item["serving_mode"] == "online" for item in data["items"])

    def test_feature_filter_by_tags(self, client: TestClient, auth_headers: dict, sample_feature_data: dict):
        """Test feature filtering by tags."""
        # Create features with different tags
        demographic_feature = sample_feature_data.copy()
        demographic_feature["name"] = "demographic_feature"
        demographic_feature["tags"] = ["demographic", "user"]
        
        financial_feature = sample_feature_data.copy()
        financial_feature["name"] = "financial_feature"
        financial_feature["tags"] = ["financial", "user"]
        
        client.post("/api/features", json=demographic_feature, headers=auth_headers)
        client.post("/api/features", json=financial_feature, headers=auth_headers)
        
        # Filter by demographic tag
        response = client.get("/api/features?tags=demographic", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all("demographic" in item["tags"] for item in data["items"]) 