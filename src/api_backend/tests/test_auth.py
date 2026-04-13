"""
Tests for authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from ..models.user import UserCreate


def test_register_user(client: TestClient):
    """
    Test user registration.
    """
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }

    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data


def test_register_duplicate_username(client: TestClient):
    """
    Test registration with duplicate username.
    """
    user_data = {
        "email": "test1@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }

    # First registration
    response1 = client.post("/api/v1/auth/register", json=user_data)
    assert response1.status_code == 200

    # Second registration with same username
    user_data["email"] = "test2@example.com"
    response2 = client.post("/api/v1/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "Username already registered" in response2.json()["detail"]


def test_register_duplicate_email(client: TestClient):
    """
    Test registration with duplicate email.
    """
    user_data = {
        "email": "test@example.com",
        "username": "testuser1",
        "password": "testpassword123"
    }

    # First registration
    response1 = client.post("/api/v1/auth/register", json=user_data)
    assert response1.status_code == 200

    # Second registration with same email
    user_data["username"] = "testuser2"
    response2 = client.post("/api/v1/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "Email already registered" in response2.json()["detail"]


def test_login_success(client: TestClient):
    """
    Test successful login.
    """
    # First register a user
    user_data = {
        "email": "login@example.com",
        "username": "loginuser",
        "password": "testpassword123"
    }
    client.post("/api/v1/auth/register", json=user_data)

    # Then login
    login_data = {
        "username": "loginuser",
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    """
    Test login with wrong password.
    """
    # First register a user
    user_data = {
        "email": "wrongpass@example.com",
        "username": "wrongpassuser",
        "password": "correctpassword"
    }
    client.post("/api/v1/auth/register", json=user_data)

    # Try to login with wrong password
    login_data = {
        "username": "wrongpassuser",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]