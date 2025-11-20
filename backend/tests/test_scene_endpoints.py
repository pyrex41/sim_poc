"""
Integration tests for scene management API endpoints.

Tests the V3 scene management endpoints including:
- List scenes for a job
- Get individual scene details
- Update scene properties
- Regenerate scene with AI
- Delete scene
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app
from backend.database_helpers import (
    create_job_scene,
    delete_scenes_by_job,
    get_scenes_by_job
)


client = TestClient(app)


class TestSceneEndpoints:
    """Integration tests for scene management endpoints."""

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers."""
        return {"Authorization": "Bearer test-token"}

    @pytest.fixture
    def sample_job_id(self):
        """Sample job ID for testing."""
        return "123"

    @pytest.fixture
    def sample_scenes(self, sample_job_id):
        """Create sample scenes in database for testing."""
        # Clean up any existing scenes
        delete_scenes_by_job(int(sample_job_id))

        # Create test scenes
        scene_ids = []
        scenes_data = [
            {
                "job_id": int(sample_job_id),
                "scene_number": 1,
                "duration": 7.0,
                "description": "Opening shot of pristine nature",
                "script": "Imagine a world without plastic waste",
                "shot_type": "wide",
                "transition": "fade",
                "assets": ["asset-001"],
                "metadata": {"mood": "inspiring"}
            },
            {
                "job_id": int(sample_job_id),
                "scene_number": 2,
                "duration": 10.0,
                "description": "Product showcase",
                "script": "Meet EcoBottle",
                "shot_type": "close-up",
                "transition": "cut",
                "assets": ["asset-002", "asset-003"],
                "metadata": {"mood": "energetic"}
            },
            {
                "job_id": int(sample_job_id),
                "scene_number": 3,
                "duration": 13.0,
                "description": "Lifestyle integration",
                "script": "Stay hydrated, stay sustainable",
                "shot_type": "medium",
                "transition": "dissolve",
                "assets": ["asset-004"],
                "metadata": {"mood": "uplifting"}
            }
        ]

        for scene_data in scenes_data:
            scene_id = create_job_scene(**scene_data)
            scene_ids.append(scene_id)

        yield scene_ids

        # Cleanup
        delete_scenes_by_job(int(sample_job_id))

    @patch('backend.api.v3.router.verify_auth')
    def test_list_scenes_success(self, mock_auth, auth_headers, sample_job_id, sample_scenes):
        """Test listing all scenes for a job."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}

        response = client.get(
            f"/api/v3/jobs/{sample_job_id}/scenes",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "scenes" in data["data"]
        assert len(data["data"]["scenes"]) == 3
        assert data["data"]["scenes"][0]["sceneNumber"] == 1
        assert data["data"]["scenes"][0]["duration"] == 7.0

    @patch('backend.api.v3.router.verify_auth')
    def test_list_scenes_empty_job(self, mock_auth, auth_headers):
        """Test listing scenes for job with no scenes."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}

        response = client.get(
            "/api/v3/jobs/999/scenes",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["scenes"]) == 0

    @patch('backend.api.v3.router.verify_auth')
    def test_get_scene_success(self, mock_auth, auth_headers, sample_job_id, sample_scenes):
        """Test getting a specific scene by ID."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}
        scene_id = sample_scenes[0]

        response = client.get(
            f"/api/v3/jobs/{sample_job_id}/scenes/{scene_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == scene_id
        assert data["data"]["sceneNumber"] == 1
        assert data["data"]["description"] == "Opening shot of pristine nature"

    @patch('backend.api.v3.router.verify_auth')
    def test_get_scene_not_found(self, mock_auth, auth_headers, sample_job_id):
        """Test getting non-existent scene."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}

        response = client.get(
            f"/api/v3/jobs/{sample_job_id}/scenes/non-existent-id",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    @patch('backend.api.v3.router.verify_auth')
    def test_get_scene_wrong_job(self, mock_auth, auth_headers, sample_scenes):
        """Test getting scene with mismatched job ID."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}
        scene_id = sample_scenes[0]

        response = client.get(
            f"/api/v3/jobs/999/scenes/{scene_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "does not belong" in data["error"].lower()

    @patch('backend.api.v3.router.verify_auth')
    def test_update_scene_success(self, mock_auth, auth_headers, sample_job_id, sample_scenes):
        """Test updating scene properties."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}
        scene_id = sample_scenes[1]

        update_data = {
            "description": "Updated product showcase with emotional appeal",
            "script": "Meet EcoBottle - your partner in sustainability",
            "duration": 12.0,
            "shotType": "medium"
        }

        response = client.put(
            f"/api/v3/jobs/{sample_job_id}/scenes/{scene_id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["description"] == update_data["description"]
        assert data["data"]["script"] == update_data["script"]
        assert data["data"]["duration"] == update_data["duration"]
        assert data["data"]["shotType"] == update_data["shotType"]

    @patch('backend.api.v3.router.verify_auth')
    def test_update_scene_partial(self, mock_auth, auth_headers, sample_job_id, sample_scenes):
        """Test partial update of scene (only some fields)."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}
        scene_id = sample_scenes[0]

        update_data = {
            "script": "Updated script only"
        }

        response = client.put(
            f"/api/v3/jobs/{sample_job_id}/scenes/{scene_id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["script"] == "Updated script only"
        # Original fields should remain unchanged
        assert data["data"]["description"] == "Opening shot of pristine nature"

    @patch('backend.api.v3.router.regenerate_scene')
    @patch('backend.api.v3.router.get_job')
    @patch('backend.api.v3.router.verify_auth')
    def test_regenerate_scene_success(self, mock_auth, mock_get_job, mock_regenerate, auth_headers, sample_job_id, sample_scenes):
        """Test regenerating a scene with AI."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}
        scene_id = sample_scenes[1]

        # Mock job data
        mock_get_job.return_value = {
            "id": int(sample_job_id),
            "parameters": json.dumps({
                "ad_basics": {
                    "product": "EcoBottle",
                    "targetAudience": "Millennials",
                    "keyMessage": "Save the planet",
                    "callToAction": "Shop Now"
                },
                "creative": {
                    "direction": {
                        "style": "modern",
                        "tone": "inspiring"
                    }
                }
            })
        }

        # Mock regenerated scene
        mock_regenerate.return_value = {
            "sceneNumber": 2,
            "duration": 10.0,
            "description": "Enhanced product showcase",
            "script": "Regenerated script with more emotional impact",
            "shotType": "medium",
            "transition": "dissolve",
            "assets": ["asset-002"]
        }

        regenerate_request = {
            "feedback": "Make it more emotional and impactful",
            "constraints": {"duration": 10.0}
        }

        response = client.post(
            f"/api/v3/jobs/{sample_job_id}/scenes/{scene_id}/regenerate",
            headers=auth_headers,
            json=regenerate_request
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Enhanced" in data["data"]["description"]
        mock_regenerate.assert_called_once()

    @patch('backend.api.v3.router.verify_auth')
    def test_delete_scene_success(self, mock_auth, auth_headers, sample_job_id, sample_scenes):
        """Test deleting a scene."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}
        scene_id = sample_scenes[2]

        response = client.delete(
            f"/api/v3/jobs/{sample_job_id}/scenes/{scene_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["data"]["message"].lower()

        # Verify scene was deleted
        scenes = get_scenes_by_job(int(sample_job_id))
        assert len(scenes) == 2

    @patch('backend.api.v3.router.verify_auth')
    def test_delete_scene_not_found(self, mock_auth, auth_headers, sample_job_id):
        """Test deleting non-existent scene."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}

        response = client.delete(
            f"/api/v3/jobs/{sample_job_id}/scenes/non-existent-id",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    @patch('backend.api.v3.router.verify_auth')
    def test_scene_operations_require_auth(self, mock_auth, sample_job_id, sample_scenes):
        """Test that scene endpoints require authentication."""
        mock_auth.side_effect = Exception("Unauthorized")

        # Test all endpoints without auth
        endpoints = [
            ("GET", f"/api/v3/jobs/{sample_job_id}/scenes"),
            ("GET", f"/api/v3/jobs/{sample_job_id}/scenes/{sample_scenes[0]}"),
            ("PUT", f"/api/v3/jobs/{sample_job_id}/scenes/{sample_scenes[0]}"),
            ("POST", f"/api/v3/jobs/{sample_job_id}/scenes/{sample_scenes[0]}/regenerate"),
            ("DELETE", f"/api/v3/jobs/{sample_job_id}/scenes/{sample_scenes[0]}")
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)

            # Should fail due to auth error
            assert response.status_code in [401, 500]  # Depending on how auth is handled

    @patch('backend.api.v3.router.verify_auth')
    def test_update_scene_with_metadata(self, mock_auth, auth_headers, sample_job_id, sample_scenes):
        """Test updating scene with custom metadata."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}
        scene_id = sample_scenes[0]

        update_data = {
            "metadata": {
                "mood": "dramatic",
                "color_palette": "warm",
                "music_cue": "uplifting-strings"
            }
        }

        response = client.put(
            f"/api/v3/jobs/{sample_job_id}/scenes/{scene_id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["metadata"]["mood"] == "dramatic"
        assert "color_palette" in data["data"]["metadata"]


class TestJobStatusWithScenes:
    """Test job status endpoint includes scenes."""

    @pytest.fixture
    def sample_job_with_scenes(self, sample_job_id, sample_scenes):
        """Job with scenes for testing."""
        return sample_job_id

    @patch('backend.api.v3.router.get_job')
    @patch('backend.api.v3.router.verify_auth')
    def test_job_status_includes_scenes(self, mock_auth, mock_get_job, auth_headers):
        """Test that GET /api/v3/jobs/{id} includes scenes."""
        mock_auth.return_value = {"id": 1, "email": "test@example.com"}

        job_id = "123"
        mock_get_job.return_value = {
            "id": int(job_id),
            "status": "storyboard_ready",
            "progress": None,
            "video_url": None,
            "error_message": None,
            "estimated_cost": 5.0,
            "actual_cost": None,
            "created_at": "2025-11-19T22:00:00Z",
            "updated_at": "2025-11-19T22:05:00Z",
            "storyboard_data": None,
            "parameters": "{}"
        }

        # Create test scenes
        delete_scenes_by_job(int(job_id))
        create_job_scene(
            job_id=int(job_id),
            scene_number=1,
            duration=15.0,
            description="Test scene",
            script="Test script"
        )

        response = client.get(
            f"/api/v3/jobs/{job_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "scenes" in data["data"]
        assert len(data["data"]["scenes"]) == 1
        assert data["data"]["scenes"][0]["sceneNumber"] == 1

        # Cleanup
        delete_scenes_by_job(int(job_id))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
