"""
Tests for health check endpoints.
"""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """
    Test health check endpoint.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_redis_health_check(client: TestClient):
    """
    Test Redis health check endpoint.
    """
    # This might fail if Redis is not running, but that's expected in tests
    response = client.get("/api/v1/health/redis")
    # Either healthy or service unavailable
    assert response.status_code in [200, 503]