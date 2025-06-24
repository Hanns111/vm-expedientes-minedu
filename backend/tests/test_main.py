"""
Tests for main FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Government AI Platform" in data["message"]
    assert data["status"] == "active"
    assert "timestamp" in data

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "timestamp" in data
    assert "plugins_loaded" in data
    assert "models_loaded" in data

def test_plugins_endpoint():
    """Test plugins API endpoint."""
    response = client.get("/api/admin/plugins")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    if data:
        plugin = data[0]
        assert "id" in plugin
        assert "name" in plugin
        assert "description" in plugin
        assert "enabled" in plugin
        assert "capabilities" in plugin
        assert "metrics" in plugin

def test_models_endpoint():
    """Test models API endpoint."""
    response = client.get("/api/admin/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    if data:
        model = data[0]
        assert "model_name" in model
        assert "display_name" in model
        assert "provider" in model
        assert "enabled" in model
        assert "metrics" in model

def test_system_status_endpoint():
    """Test system status endpoint."""
    response = client.get("/api/admin/system-status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "system_load" in data
    assert "services" in data

def test_plugin_toggle():
    """Test plugin toggle endpoint."""
    plugin_id = "test-plugin"
    response = client.post(f"/api/admin/plugins/{plugin_id}/toggle")
    assert response.status_code == 200
    data = response.json()
    assert data["plugin_id"] == plugin_id
    assert data["action"] == "toggled"

def test_model_toggle():
    """Test model toggle endpoint."""
    model_name = "test-model"
    response = client.post(f"/api/admin/models/{model_name}/toggle")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == model_name
    assert data["action"] == "toggled"

def test_cors_headers():
    """Test CORS headers are present."""
    response = client.options("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    
def test_docs_endpoint():
    """Test API documentation endpoint."""
    response = client.get("/docs")
    assert response.status_code == 200

def test_redoc_endpoint():
    """Test ReDoc documentation endpoint."""
    response = client.get("/redoc")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_invalid_endpoint():
    """Test invalid endpoint returns 404."""
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404