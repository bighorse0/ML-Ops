import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.lineage import FeatureLineage, DataLineage, LineageNode, LineageEdge
from models.user import User
from models.organization import Organization


class TestLineageAPI:
    """Test suite for Lineage API endpoints."""

    def test_create_feature_lineage_success(self, client: TestClient, auth_headers: dict, sample_feature_lineage_data: dict):
        """Test successful feature lineage creation."""
        response = client.post("/api/lineage/features", json=sample_feature_lineage_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["feature_id"] == sample_feature_lineage_data["feature_id"]
        assert data["source_type"] == sample_feature_lineage_data["source_type"]
        assert data["source_id"] == sample_feature_lineage_data["source_id"]
        assert data["transformation_type"] == sample_feature_lineage_data["transformation_type"]
        assert "id" in data
        assert "created_at" in data

    def test_create_feature_lineage_validation_error(self, client: TestClient, auth_headers: dict):
        """Test feature lineage creation with validation errors."""
        invalid_data = {
            "feature_id": 0,  # Invalid feature ID
            "source_type": "invalid_type",  # Invalid source type
            "source_id": "invalid_id",
            "transformation_type": "invalid_transformation"  # Invalid transformation type
        }
        
        response = client.post("/api/lineage/features", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_get_feature_lineage_success(self, client: TestClient, auth_headers: dict, sample_feature_lineage_data: dict):
        """Test successful feature lineage retrieval."""
        # Create lineage first
        create_response = client.post("/api/lineage/features", json=sample_feature_lineage_data, headers=auth_headers)
        assert create_response.status_code == 201
        lineage_id = create_response.json()["id"]
        
        # Get the lineage
        response = client.get(f"/api/lineage/features/{lineage_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lineage_id
        assert data["feature_id"] == sample_feature_lineage_data["feature_id"]

    def test_get_feature_lineage_not_found(self, client: TestClient, auth_headers: dict):
        """Test feature lineage retrieval for non-existent lineage."""
        response = client.get("/api/lineage/features/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_list_feature_lineage(self, client: TestClient, auth_headers: dict, sample_feature_lineage_data: dict):
        """Test successful feature lineage listing."""
        # Create multiple lineage records
        for i in range(3):
            lineage_data = sample_feature_lineage_data.copy()
            lineage_data["source_id"] = f"source_{i}"
            response = client.post("/api/lineage/features", json=lineage_data, headers=auth_headers)
            assert response.status_code == 201
        
        # List lineage
        response = client.get("/api/lineage/features", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 3

    def test_create_data_lineage_success(self, client: TestClient, auth_headers: dict, sample_data_lineage_data: dict):
        """Test successful data lineage creation."""
        response = client.post("/api/lineage/data", json=sample_data_lineage_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["source_dataset"] == sample_data_lineage_data["source_dataset"]
        assert data["target_dataset"] == sample_data_lineage_data["target_dataset"]
        assert data["transformation_type"] == sample_data_lineage_data["transformation_type"]
        assert "id" in data
        assert "created_at" in data

    def test_get_data_lineage_success(self, client: TestClient, auth_headers: dict, sample_data_lineage_data: dict):
        """Test successful data lineage retrieval."""
        # Create lineage first
        create_response = client.post("/api/lineage/data", json=sample_data_lineage_data, headers=auth_headers)
        assert create_response.status_code == 201
        lineage_id = create_response.json()["id"]
        
        # Get the lineage
        response = client.get(f"/api/lineage/data/{lineage_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == lineage_id
        assert data["source_dataset"] == sample_data_lineage_data["source_dataset"]

    def test_list_data_lineage(self, client: TestClient, auth_headers: dict, sample_data_lineage_data: dict):
        """Test successful data lineage listing."""
        # Create multiple lineage records
        for i in range(3):
            lineage_data = sample_data_lineage_data.copy()
            lineage_data["source_dataset"] = f"dataset_{i}"
            lineage_data["target_dataset"] = f"target_dataset_{i}"
            response = client.post("/api/lineage/data", json=lineage_data, headers=auth_headers)
            assert response.status_code == 201
        
        # List lineage
        response = client.get("/api/lineage/data", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 3

    def test_get_lineage_graph(self, client: TestClient, auth_headers: dict):
        """Test lineage graph retrieval."""
        response = client.get("/api/lineage/graph", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "metadata" in data

    def test_get_lineage_graph_for_feature(self, client: TestClient, auth_headers: dict, sample_feature_lineage_data: dict):
        """Test lineage graph retrieval for specific feature."""
        # Create lineage first
        create_response = client.post("/api/lineage/features", json=sample_feature_lineage_data, headers=auth_headers)
        assert create_response.status_code == 201
        feature_id = create_response.json()["feature_id"]
        
        # Get lineage graph for feature
        response = client.get(f"/api/lineage/graph/feature/{feature_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "metadata" in data

    def test_get_lineage_graph_for_dataset(self, client: TestClient, auth_headers: dict, sample_data_lineage_data: dict):
        """Test lineage graph retrieval for specific dataset."""
        # Create lineage first
        create_response = client.post("/api/lineage/data", json=sample_data_lineage_data, headers=auth_headers)
        assert create_response.status_code == 201
        dataset_name = create_response.json()["source_dataset"]
        
        # Get lineage graph for dataset
        response = client.get(f"/api/lineage/graph/dataset/{dataset_name}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "metadata" in data

    def test_get_lineage_impact_analysis(self, client: TestClient, auth_headers: dict, sample_feature_lineage_data: dict):
        """Test lineage impact analysis."""
        # Create lineage first
        create_response = client.post("/api/lineage/features", json=sample_feature_lineage_data, headers=auth_headers)
        assert create_response.status_code == 201
        feature_id = create_response.json()["feature_id"]
        
        # Get impact analysis
        response = client.get(f"/api/lineage/impact/{feature_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "impacted_features" in data
        assert "impacted_datasets" in data
        assert "impact_level" in data

    def test_get_lineage_trace(self, client: TestClient, auth_headers: dict, sample_feature_lineage_data: dict):
        """Test lineage trace retrieval."""
        # Create lineage first
        create_response = client.post("/api/lineage/features", json=sample_feature_lineage_data, headers=auth_headers)
        assert create_response.status_code == 201
        feature_id = create_response.json()["feature_id"]
        
        # Get lineage trace
        response = client.get(f"/api/lineage/trace/{feature_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "trace_path" in data
        assert "steps" in data
        assert "metadata" in data

    def test_create_lineage_node_success(self, client: TestClient, auth_headers: dict, sample_lineage_node_data: dict):
        """Test successful lineage node creation."""
        response = client.post("/api/lineage/nodes", json=sample_lineage_node_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["node_id"] == sample_lineage_node_data["node_id"]
        assert data["node_type"] == sample_lineage_node_data["node_type"]
        assert data["name"] == sample_lineage_node_data["name"]
        assert "id" in data
        assert "created_at" in data

    def test_create_lineage_edge_success(self, client: TestClient, auth_headers: dict, sample_lineage_edge_data: dict):
        """Test successful lineage edge creation."""
        response = client.post("/api/lineage/edges", json=sample_lineage_edge_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["source_node_id"] == sample_lineage_edge_data["source_node_id"]
        assert data["target_node_id"] == sample_lineage_edge_data["target_node_id"]
        assert data["edge_type"] == sample_lineage_edge_data["edge_type"]
        assert "id" in data
        assert "created_at" in data

    def test_get_lineage_statistics(self, client: TestClient, auth_headers: dict):
        """Test lineage statistics retrieval."""
        response = client.get("/api/lineage/statistics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_features" in data
        assert "total_datasets" in data
        assert "total_transformations" in data
        assert "lineage_coverage" in data

    def test_lineage_unauthorized(self, client: TestClient):
        """Test lineage endpoints without authentication."""
        response = client.get("/api/lineage/graph")
        assert response.status_code == 401

    def test_lineage_permissions_readonly_user(self, client: TestClient, readonly_auth_headers: dict):
        """Test lineage endpoints with readonly user permissions."""
        # Should be able to read
        response = client.get("/api/lineage/graph", headers=readonly_auth_headers)
        assert response.status_code == 200
        
        # Should not be able to create
        sample_data = {
            "feature_id": 1,
            "source_type": "dataset",
            "source_id": "test_dataset",
            "transformation_type": "aggregation"
        }
        response = client.post("/api/lineage/features", json=sample_data, headers=readonly_auth_headers)
        assert response.status_code == 403


class TestLineageValidation:
    """Test suite for lineage data validation."""

    def test_feature_lineage_source_type_validation(self, client: TestClient, auth_headers: dict):
        """Test feature lineage source type validation."""
        invalid_data = {
            "feature_id": 1,
            "source_type": "invalid_type",
            "source_id": "test_source",
            "transformation_type": "aggregation"
        }
        
        response = client.post("/api/lineage/features", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_feature_lineage_transformation_type_validation(self, client: TestClient, auth_headers: dict):
        """Test feature lineage transformation type validation."""
        invalid_data = {
            "feature_id": 1,
            "source_type": "dataset",
            "source_id": "test_source",
            "transformation_type": "invalid_transformation"
        }
        
        response = client.post("/api/lineage/features", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_data_lineage_transformation_type_validation(self, client: TestClient, auth_headers: dict):
        """Test data lineage transformation type validation."""
        invalid_data = {
            "source_dataset": "test_source",
            "target_dataset": "test_target",
            "transformation_type": "invalid_transformation"
        }
        
        response = client.post("/api/lineage/data", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_lineage_node_type_validation(self, client: TestClient, auth_headers: dict):
        """Test lineage node type validation."""
        invalid_data = {
            "node_id": "test_node",
            "node_type": "invalid_type",
            "name": "Test Node"
        }
        
        response = client.post("/api/lineage/nodes", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_lineage_edge_type_validation(self, client: TestClient, auth_headers: dict):
        """Test lineage edge type validation."""
        invalid_data = {
            "source_node_id": "source_node",
            "target_node_id": "target_node",
            "edge_type": "invalid_type"
        }
        
        response = client.post("/api/lineage/edges", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422


class TestLineageSearchAndFiltering:
    """Test suite for lineage search and filtering."""

    def test_feature_lineage_filter_by_source_type(self, client: TestClient, auth_headers: dict, sample_feature_lineage_data: dict):
        """Test feature lineage filtering by source type."""
        # Create lineage with different source types
        dataset_lineage = sample_feature_lineage_data.copy()
        dataset_lineage["source_type"] = "dataset"
        
        feature_lineage = sample_feature_lineage_data.copy()
        feature_lineage["source_type"] = "feature"
        
        client.post("/api/lineage/features", json=dataset_lineage, headers=auth_headers)
        client.post("/api/lineage/features", json=feature_lineage, headers=auth_headers)
        
        # Filter by dataset source type
        response = client.get("/api/lineage/features?source_type=dataset", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["source_type"] == "dataset" for item in data["items"])

    def test_data_lineage_filter_by_transformation_type(self, client: TestClient, auth_headers: dict, sample_data_lineage_data: dict):
        """Test data lineage filtering by transformation type."""
        # Create lineage with different transformation types
        aggregation_lineage = sample_data_lineage_data.copy()
        aggregation_lineage["transformation_type"] = "aggregation"
        
        join_lineage = sample_data_lineage_data.copy()
        join_lineage["transformation_type"] = "join"
        
        client.post("/api/lineage/data", json=aggregation_lineage, headers=auth_headers)
        client.post("/api/lineage/data", json=join_lineage, headers=auth_headers)
        
        # Filter by aggregation transformation type
        response = client.get("/api/lineage/data?transformation_type=aggregation", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["transformation_type"] == "aggregation" for item in data["items"])

    def test_lineage_search_by_feature_name(self, client: TestClient, auth_headers: dict):
        """Test lineage search by feature name."""
        response = client.get("/api/lineage/search?query=test_feature", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    def test_lineage_search_by_dataset_name(self, client: TestClient, auth_headers: dict):
        """Test lineage search by dataset name."""
        response = client.get("/api/lineage/search?query=test_dataset", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data 