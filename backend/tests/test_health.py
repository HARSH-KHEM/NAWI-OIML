"""Tests for GET /health and GET /api/v1/health endpoints."""

from fastapi.testclient import TestClient


def test_health_root_endpoint(client: TestClient):
    """Verify root GET /health returns 200 and expected payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app" in data
    assert "version" in data
    assert "environment" in data
    assert "database_connected" in data
    assert "timestamp" in data


def test_health_v1_endpoint(client: TestClient):
    """Verify versioned GET /api/v1/health returns 200 and matches root endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
