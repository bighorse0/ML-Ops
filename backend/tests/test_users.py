import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.organization import Organization


class TestUsersAPI:
    """Test suite for Users API endpoints."""

    def test_create_user_success(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test successful user creation."""
        response = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]
        assert data["first_name"] == sample_user_data["first_name"]
        assert data["last_name"] == sample_user_data["last_name"]
        assert data["role"] == sample_user_data["role"]
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data
        # Password should not be returned
        assert "password" not in data

    def test_create_user_validation_error(self, client: TestClient, auth_headers: dict):
        """Test user creation with validation errors."""
        invalid_data = {
            "email": "invalid_email",  # Invalid email format
            "username": "",  # Empty username
            "password": "short",  # Too short password
            "first_name": "Test",
            "last_name": "User",
            "role": "invalid_role"  # Invalid role
        }
        
        response = client.post("/api/users", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_user_duplicate_email(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test user creation with duplicate email."""
        # Create first user
        response1 = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Try to create second user with same email
        response2 = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert response2.status_code == 409
        data = response2.json()
        assert "already exists" in data["detail"]

    def test_create_user_duplicate_username(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test user creation with duplicate username."""
        # Create first user
        response1 = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Try to create second user with same username but different email
        duplicate_data = sample_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        response2 = client.post("/api/users", json=duplicate_data, headers=auth_headers)
        assert response2.status_code == 409
        data = response2.json()
        assert "already exists" in data["detail"]

    def test_get_user_success(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test successful user retrieval."""
        # Create user first
        create_response = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Get the user
        response = client.get(f"/api/users/{user_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]

    def test_get_user_not_found(self, client: TestClient, auth_headers: dict):
        """Test user retrieval for non-existent user."""
        response = client.get("/api/users/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_list_users_success(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test successful user listing."""
        # Create multiple users
        for i in range(3):
            user_data = sample_user_data.copy()
            user_data["email"] = f"user{i}@example.com"
            user_data["username"] = f"user{i}"
            response = client.post("/api/users", json=user_data, headers=auth_headers)
            assert response.status_code == 201
        
        # List users
        response = client.get("/api/users", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert len(data["items"]) >= 3

    def test_list_users_with_pagination(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test user listing with pagination."""
        # Create multiple users
        for i in range(5):
            user_data = sample_user_data.copy()
            user_data["email"] = f"user{i}@example.com"
            user_data["username"] = f"user{i}"
            response = client.post("/api/users", json=user_data, headers=auth_headers)
            assert response.status_code == 201
        
        # Test pagination
        response = client.get("/api/users?page=1&limit=2", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["size"] == 2

    def test_list_users_with_filters(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test user listing with filters."""
        # Create users with different roles
        admin_user = sample_user_data.copy()
        admin_user["email"] = "admin@example.com"
        admin_user["username"] = "admin"
        admin_user["role"] = "admin"
        
        regular_user = sample_user_data.copy()
        regular_user["email"] = "user@example.com"
        regular_user["username"] = "user"
        regular_user["role"] = "user"
        
        client.post("/api/users", json=admin_user, headers=auth_headers)
        client.post("/api/users", json=regular_user, headers=auth_headers)
        
        # Filter by role
        response = client.get("/api/users?role=admin", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(item["role"] == "admin" for item in data["items"])

    def test_update_user_success(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test successful user update."""
        # Create user first
        create_response = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Update user
        update_data = {
            "first_name": "Updated First",
            "last_name": "Updated Last",
            "role": "admin"
        }
        
        response = client.put(f"/api/users/{user_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]
        assert data["role"] == update_data["role"]

    def test_update_user_not_found(self, client: TestClient, auth_headers: dict):
        """Test user update for non-existent user."""
        update_data = {"first_name": "Updated"}
        
        response = client.put("/api/users/99999", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_delete_user_success(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test successful user deletion."""
        # Create user first
        create_response = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Delete user
        response = client.delete(f"/api/users/{user_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        # Verify user is deleted
        get_response = client.get(f"/api/users/{user_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_user_not_found(self, client: TestClient, auth_headers: dict):
        """Test user deletion for non-existent user."""
        response = client.delete("/api/users/99999", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_change_user_password(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test user password change."""
        # Create user first
        create_response = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Change password
        password_data = {
            "current_password": sample_user_data["password"],
            "new_password": "new_secure_password123"
        }
        
        response = client.post(f"/api/users/{user_id}/change-password", json=password_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "password changed successfully" in data["message"]

    def test_reset_user_password(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test user password reset."""
        # Create user first
        create_response = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # Reset password
        response = client.post(f"/api/users/{user_id}/reset-password", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "password reset successfully" in data["message"]
        assert "temporary_password" in data

    def test_get_user_profile(self, client: TestClient, auth_headers: dict):
        """Test user profile retrieval."""
        response = client.get("/api/users/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "username" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "role" in data

    def test_update_user_profile(self, client: TestClient, auth_headers: dict):
        """Test user profile update."""
        update_data = {
            "first_name": "Updated First",
            "last_name": "Updated Last"
        }
        
        response = client.put("/api/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]

    def test_users_unauthorized(self, client: TestClient):
        """Test users endpoints without authentication."""
        response = client.get("/api/users")
        assert response.status_code == 401

    def test_users_permissions_readonly_user(self, client: TestClient, readonly_auth_headers: dict):
        """Test users endpoints with readonly user permissions."""
        # Should be able to read
        response = client.get("/api/users", headers=readonly_auth_headers)
        assert response.status_code == 200
        
        # Should not be able to create
        sample_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "secure_password123",
            "first_name": "Test",
            "last_name": "User",
            "role": "user"
        }
        response = client.post("/api/users", json=sample_data, headers=readonly_auth_headers)
        assert response.status_code == 403


class TestUserValidation:
    """Test suite for user data validation."""

    def test_user_email_validation(self, client: TestClient, auth_headers: dict):
        """Test user email validation."""
        invalid_data = {
            "email": "invalid_email",
            "username": "testuser",
            "password": "secure_password123",
            "first_name": "Test",
            "last_name": "User",
            "role": "user"
        }
        
        response = client.post("/api/users", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_user_password_validation(self, client: TestClient, auth_headers: dict):
        """Test user password validation."""
        invalid_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "short",  # Too short
            "first_name": "Test",
            "last_name": "User",
            "role": "user"
        }
        
        response = client.post("/api/users", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_user_role_validation(self, client: TestClient, auth_headers: dict):
        """Test user role validation."""
        invalid_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "secure_password123",
            "first_name": "Test",
            "last_name": "User",
            "role": "invalid_role"
        }
        
        response = client.post("/api/users", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422

    def test_user_username_validation(self, client: TestClient, auth_headers: dict):
        """Test user username validation."""
        invalid_data = {
            "email": "test@example.com",
            "username": "",  # Empty username
            "password": "secure_password123",
            "first_name": "Test",
            "last_name": "User",
            "role": "user"
        }
        
        response = client.post("/api/users", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422


class TestUserSearchAndFiltering:
    """Test suite for user search and filtering."""

    def test_user_search_by_email(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test user search by email."""
        # Create user first
        create_response = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        # Search by email
        response = client.get(f"/api/users?search={sample_user_data['email']}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(user["email"] == sample_user_data["email"] for user in data["items"])

    def test_user_search_by_username(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test user search by username."""
        # Create user first
        create_response = client.post("/api/users", json=sample_user_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        # Search by username
        response = client.get(f"/api/users?search={sample_user_data['username']}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any(user["username"] == sample_user_data["username"] for user in data["items"])

    def test_user_filter_by_role(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test user filtering by role."""
        # Create users with different roles
        admin_user = sample_user_data.copy()
        admin_user["email"] = "admin@example.com"
        admin_user["username"] = "admin"
        admin_user["role"] = "admin"
        
        regular_user = sample_user_data.copy()
        regular_user["email"] = "user@example.com"
        regular_user["username"] = "user"
        regular_user["role"] = "user"
        
        client.post("/api/users", json=admin_user, headers=auth_headers)
        client.post("/api/users", json=regular_user, headers=auth_headers)
        
        # Filter by admin role
        response = client.get("/api/users?role=admin", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(user["role"] == "admin" for user in data["items"])

    def test_user_filter_by_status(self, client: TestClient, auth_headers: dict, sample_user_data: dict):
        """Test user filtering by status."""
        # Create users (they start as active)
        for i in range(3):
            user_data = sample_user_data.copy()
            user_data["email"] = f"user{i}@example.com"
            user_data["username"] = f"user{i}"
            client.post("/api/users", json=user_data, headers=auth_headers)
        
        # Filter by active status
        response = client.get("/api/users?status=active", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert all(user["status"] == "active" for user in data["items"]) 