"""
Integration tests for authentication API
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.auth_service import AuthService


class TestAuthAPI:
    def test_register_success(self, client: TestClient, db_session: Session):
        """Test successful user registration"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }

        response = client.post("/api/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "created_at" in data

    def test_register_duplicate_username(self, client: TestClient):
        """Test registration with duplicate username"""
        user_data = {
            "username": "duplicate",
            "email": "test1@example.com",
            "password": "password123"
        }

        # First registration
        response1 = client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 200

        # Second registration with same username
        user_data["email"] = "test2@example.com"
        response2 = client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]

    def test_register_duplicate_email(self, client: TestClient):
        """Test registration with duplicate email"""
        user_data = {
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "password123"
        }

        # First registration
        response1 = client.post("/api/auth/register", json=user_data)
        assert response1.status_code == 200

        # Second registration with same email
        user_data["username"] = "user2"
        response2 = client.post("/api/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]

    def test_login_success(self, client: TestClient):
        """Test successful login"""
        # First register user
        user_data = {
            "username": "loginuser",
            "email": "login@example.com",
            "password": "password123"
        }
        client.post("/api/auth/register", json=user_data)

        # Then login
        login_data = {
            "username": "loginuser",
            "password": "password123"
        }
        response = client.post("/api/auth/login", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient):
        """Test login with wrong password"""
        # First register user
        user_data = {
            "username": "wrongpass",
            "email": "wrongpass@example.com",
            "password": "correctpassword"
        }
        client.post("/api/auth/register", json=user_data)

        # Try login with wrong password
        login_data = {
            "username": "wrongpass",
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", data=login_data)

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login for non-existent user"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        response = client.post("/api/auth/login", data=login_data)

        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_get_current_user_authenticated(self, client: TestClient):
        """Test getting current user when authenticated"""
        # Register and login
        user_data = {
            "username": "currentuser",
            "email": "current@example.com",
            "password": "password123"
        }
        client.post("/api/auth/register", json=user_data)

        login_data = {
            "username": "currentuser",
            "password": "password123"
        }
        login_response = client.post("/api/auth/login", data=login_data)
        token = login_response.json()["access_token"]

        # Get current user
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "currentuser"
        assert data["email"] == "current@example.com"

    def test_get_current_user_unauthenticated(self, client: TestClient):
        """Test getting current user without authentication"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
