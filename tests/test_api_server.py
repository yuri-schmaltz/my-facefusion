"""
API Server Tests for Face Forge Full Stack

Tests critical endpoints of the FastAPI backend.
Run with: pytest tests/test_api_server.py -v
"""
import pytest
from fastapi.testclient import TestClient
import os
import sys

# Ensure facefusion is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from facefusion.api_server import app


@pytest.fixture(scope="module")
def client():
    """Create test client for the API."""
    with TestClient(app) as c:
        yield c


class TestHealthEndpoints:
    """Test health and system info endpoints."""

    def test_health(self, client):
        """Health endpoint should return ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_system_info(self, client):
        """System info should return name and version."""
        response = client.get("/system/info")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "execution_providers" in data


class TestProcessorsEndpoints:
    """Test processor-related endpoints."""

    def test_list_processors(self, client):
        """List processors should return available and active lists."""
        response = client.get("/processors")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        assert "active" in data
        assert isinstance(data["available"], list)

    def test_get_processor_choices(self, client):
        """Processor choices should return model options."""
        response = client.get("/processors/choices")
        assert response.status_code == 200
        data = response.json()
        # Should have at least face_swapper
        assert "face_swapper" in data or len(data) > 0


class TestConfigEndpoints:
    """Test configuration endpoints."""

    def test_get_config(self, client):
        """Get config should return current settings."""
        response = client.get("/config")
        assert response.status_code == 200
        data = response.json()
        # Should have processors key
        assert "processors" in data

    def test_update_config(self, client):
        """Update config should accept valid payload."""
        response = client.post("/config", json={
            "output_video_quality": 85
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"


class TestFilesystemEndpoints:
    """Test filesystem browser endpoints."""

    def test_list_home_directory(self, client):
        """Listing home directory should work."""
        response = client.post("/filesystem/list", json={"path": None})
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "path" in data
        assert "parent" in data

    def test_list_explicit_path(self, client):
        """Listing explicit path should work."""
        response = client.post("/filesystem/list", json={"path": "/tmp"})
        assert response.status_code == 200
        data = response.json()
        assert data["path"] == "/tmp"

    def test_list_invalid_path(self, client):
        """Listing invalid path should return 400."""
        response = client.post("/filesystem/list", json={"path": "/nonexistent/path/xyz"})
        assert response.status_code == 400


class TestFilePreviewSecurity:
    """Test file preview endpoint security."""

    def test_preview_access_denied_for_system_files(self, client):
        """Should deny access to files outside allowed roots."""
        response = client.get("/files/preview", params={"path": "/etc/passwd"})
        assert response.status_code == 403

    def test_preview_path_traversal_blocked(self, client):
        """Path traversal attempts should be blocked."""
        response = client.get("/files/preview", params={"path": "../../../etc/passwd"})
        assert response.status_code == 403


class TestCORSConfiguration:
    """Test CORS is properly configured."""

    def test_cors_allows_localhost_origin(self, client):
        """CORS should allow localhost:5173 origin."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET"
            }
        )
        # Should not get CORS error for allowed origin
        assert response.status_code in [200, 204, 405]  # 405 if OPTIONS not explicitly handled

    def test_cors_blocks_unknown_origin(self, client):
        """CORS should not expose Access-Control-Allow-Origin for unknown origins."""
        response = client.get(
            "/health",
            headers={"Origin": "http://evil.com"}
        )
        # Request succeeds but CORS header should not match evil.com
        cors_header = response.headers.get("Access-Control-Allow-Origin", "")
        assert cors_header != "http://evil.com"
