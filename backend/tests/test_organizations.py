import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.organization import Organization
from models.user import User


class TestOrganizationsAPI:
    """Test suite for Organizations API endpoints."""

    def test_create_organization_success(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test successful organization creation."""
        response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == sample_organization_data["name"]
        assert data["description"] == sample_organization_data["description"]
        assert data["domain"] == sample_organization_data["domain"]
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data

    def test_create_organization_validation_error(self, client: TestClient, auth_headers: dict):
        """Test organization creation with validation errors."""
        invalid_data = {
            "name": "",  # Empty name
            "description": "Test description",
            "domain": "invalid_domain",  # Invalid domain format
            "settings": {"invalid": "settings"}
        }
        
        response = client.post("/api/organizations", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_organization_duplicate_name(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test organization creation with duplicate name."""
        # Create first organization
        response1 = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Try to create second organization with same name
        response2 = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert response2.status_code == 409
        data = response2.json()
        assert "already exists" in data["detail"]

    def test_get_organization_success(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test successful organization retrieval."""
        # Create organization first
        create_response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert create_response.status_code == 201
        org_id = create_response.json()["id"]
        
        # Get the organization
        response = client.get(f"/api/organizations/{org_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == org_id
        assert data["name"] == sample_organization_data["name"]

    def test_get_organization_not_found(self, client: TestClient, auth_headers: dict):
        """Test organization retrieval for non-existent organization."""
        response = client.get("/api/organizations/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_list_organizations_success(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test successful organization listing."""
        # Create multiple organizations
        for i in range(3):
            org_data = sample_organization_data.copy()
            org_data["name"] = f"{sample_organization_data['name']}_{i}"
            org_data["domain"] = f"org{i}.example.com"
            response = client.post("/api/organizations", json=org_data, headers=auth_headers)
            assert response.status_code == 201
        
        # List organizations
        response = client.get("/api/organizations", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert len(data["items"]) >= 3

    def test_list_organizations_with_pagination(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test organization listing with pagination."""
        # Create multiple organizations
        for i in range(5):
            org_data = sample_organization_data.copy()
            org_data["name"] = f"{sample_organization_data['name']}_{i}"
            org_data["domain"] = f"org{i}.example.com"
            response = client.post("/api/organizations", json=org_data, headers=auth_headers)
            assert response.status_code == 201
        
        # Test pagination
        response = client.get("/api/organizations?page=1&limit=2", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["size"] == 2

    def test_list_organizations_with_filters(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test organization listing with filters."""
        # Create organizations with different statuses
        active_org = sample_organization_data.copy()
        active_org["name"] = "active_org"
        active_org["domain"] = "active.example.com"
        active_org["status"] = "active"
        
        inactive_org = sample_organization_data.copy()
        inactive_org["name"] = "inactive_org"
        inactive_org["domain"] = "inactive.example.com"
        inactive_org["status"] = "inactive"
        
        client.post("/api/organizations", json=active_org, headers=auth_headers)
        client.post("/api/organizations", json=inactive_org, headers=auth_headers)
        
        # Filter by active status
        response = client.get("/api/organizations?status=active", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["status"] == "active" for item in data["items"])

    def test_update_organization_success(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test successful organization update."""
        # Create organization first
        create_response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert create_response.status_code == 201
        org_id = create_response.json()["id"]
        
        # Update organization
        update_data = {
            "description": "Updated description",
            "domain": "updated.example.com",
            "settings": {"updated": True}
        }
        
        response = client.put(f"/api/organizations/{org_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["domain"] == update_data["domain"]
        assert data["settings"] == update_data["settings"]

    def test_update_organization_not_found(self, client: TestClient, auth_headers: dict):
        """Test organization update for non-existent organization."""
        update_data = {"description": "Updated"}
        
        response = client.put("/api/organizations/99999", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_delete_organization_success(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test successful organization deletion."""
        # Create organization first
        create_response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert create_response.status_code == 201
        org_id = create_response.json()["id"]
        
        # Delete organization
        response = client.delete(f"/api/organizations/{org_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        # Verify organization is deleted
        get_response = client.get(f"/api/organizations/{org_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_organization_not_found(self, client: TestClient, auth_headers: dict):
        """Test organization deletion for non-existent organization."""
        response = client.delete("/api/organizations/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_add_user_to_organization(self, client: TestClient, auth_headers: dict, sample_organization_data: dict, sample_user_data: dict):
        """Test adding user to organization."""
        # Create organization first
        org_response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]
        
        # Create user first
        user_response = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]
        
        # Add user to organization
        add_data = {
            "user_id": user_id,
            "role": "member"
        }
        
        response = client.post(f"/api/organizations/{org_id}/users", json=add_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user added successfully" in data["message"]

    def test_remove_user_from_organization(self, client: TestClient, auth_headers: dict, sample_organization_data: dict, sample_user_data: dict):
        """Test removing user from organization."""
        # Create organization first
        org_response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]
        
        # Create user first
        user_response = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]
        
        # Add user to organization first
        add_data = {"user_id": user_id, "role": "member"}
        client.post(f"/api/organizations/{org_id}/users", json=add_data, headers=auth_headers)
        
        # Remove user from organization
        response = client.delete(f"/api/organizations/{org_id}/users/{user_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "user removed successfully" in data["message"]

    def test_get_organization_users(self, client: TestClient, auth_headers: dict, sample_organization_data: dict, sample_user_data: dict):
        """Test getting organization users."""
        # Create organization first
        org_response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]
        
        # Create user first
        user_response = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert user_response.status_code == 201
        user_id = user_response.json()["id"]
        
        # Add user to organization
        add_data = {"user_id": user_id, "role": "member"}
        client.post(f"/api/organizations/{org_id}/users", json=add_data, headers=auth_headers)
        
        # Get organization users
        response = client.get(f"/api/organizations/{org_id}/users", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1

    def test_get_organization_settings(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test getting organization settings."""
        # Create organization first
        org_response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]
        
        # Get organization settings
        response = client.get(f"/api/organizations/{org_id}/settings", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "settings" in data

    def test_update_organization_settings(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test updating organization settings."""
        # Create organization first
        org_response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]
        
        # Update organization settings
        settings_data = {
            "settings": {
                "feature_flags": {"new_feature": True},
                "limits": {"max_features": 1000},
                "notifications": {"email_alerts": True}
            }
        }
        
        response = client.put(f"/api/organizations/{org_id}/settings", json=settings_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["settings"] == settings_data["settings"]

    def test_get_organization_statistics(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test getting organization statistics."""
        # Create organization first
        org_response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert org_response.status_code == 201
        org_id = org_response.json()["id"]
        
        # Get organization statistics
        response = client.get(f"/api/organizations/{org_id}/statistics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_features" in data
        assert "total_datasets" in data
        assert "active_projects" in data

    def test_organizations_unauthorized(self, client: TestClient):
        """Test organizations endpoints without authentication."""
        response = client.get("/api/organizations")
        assert response.status_code == 401

    def test_organizations_permissions_readonly_user(self, client: TestClient, readonly_auth_headers: dict):
        """Test organizations endpoints with readonly user permissions."""
        # Should be able to read
        response = client.get("/api/organizations", headers=readonly_auth_headers)
        assert response.status_code == 200
        
        # Should not be able to create
        sample_data = {
            "name": "Test Organization",
            "description": "Test description",
            "domain": "test.example.com"
        }
        response = client.post("/api/organizations", json=sample_data, headers=readonly_auth_headers)
        assert response.status_code == 403


class TestOrganizationValidation:
    """Test suite for organization data validation."""

    def test_organization_name_validation(self, client: TestClient, auth_headers: dict):
        """Test organization name validation."""
        invalid_data = {
            "name": "",  # Empty name
            "description": "Test description",
            "domain": "test.example.com"
        }
        
        response = client.post("/api/organizations", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_organization_domain_validation(self, client: TestClient, auth_headers: dict):
        """Test organization domain validation."""
        invalid_data = {
            "name": "Test Organization",
            "description": "Test description",
            "domain": "invalid_domain"  # Invalid domain format
        }
        
        response = client.post("/api/organizations", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_organization_status_validation(self, client: TestClient, auth_headers: dict):
        """Test organization status validation."""
        invalid_data = {
            "name": "Test Organization",
            "description": "Test description",
            "domain": "test.example.com",
            "status": "invalid_status"  # Invalid status
        }
        
        response = client.post("/api/organizations", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422


class TestOrganizationSearchAndFiltering:
    """Test suite for organization search and filtering."""

    def test_organization_search_by_name(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test organization search by name."""
        # Create organization first
        create_response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        # Search by name
        response = client.get(f"/api/organizations?search={sample_organization_data['name']}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(org["name"] == sample_organization_data["name"] for org in data["items"])

    def test_organization_search_by_domain(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test organization search by domain."""
        # Create organization first
        create_response = client.post("/api/organizations", json=sample_organization_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        # Search by domain
        response = client.get(f"/api/organizations?search={sample_organization_data['domain']}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(org["domain"] == sample_organization_data["domain"] for org in data["items"])

    def test_organization_filter_by_status(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test organization filtering by status."""
        # Create organizations with different statuses
        active_org = sample_organization_data.copy()
        active_org["name"] = "active_org"
        active_org["domain"] = "active.example.com"
        active_org["status"] = "active"
        
        inactive_org = sample_organization_data.copy()
        inactive_org["name"] = "inactive_org"
        inactive_org["domain"] = "inactive.example.com"
        inactive_org["status"] = "inactive"
        
        client.post("/api/organizations", json=active_org, headers=auth_headers)
        client.post("/api/organizations", json=inactive_org, headers=auth_headers)
        
        # Filter by active status
        response = client.get("/api/organizations?status=active", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(org["status"] == "active" for org in data["items"])

    def test_organization_filter_by_created_date(self, client: TestClient, auth_headers: dict, sample_organization_data: dict):
        """Test organization filtering by created date."""
        # Create organizations
        for i in range(3):
            org_data = sample_organization_data.copy()
            org_data["name"] = f"org_{i}"
            org_data["domain"] = f"org{i}.example.com"
            client.post("/api/organizations", json=org_data, headers=auth_headers)
        
        # Filter by created date (this would need proper date handling)
        response = client.get("/api/organizations?created_after=2023-01-01", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Note: This test assumes proper date filtering is implemented 