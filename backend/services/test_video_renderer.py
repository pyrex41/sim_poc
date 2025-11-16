"""
Unit tests for video rendering background task.

Tests cover:
- Happy path rendering workflow
- Error handling and retry logic
- Progress tracking
- Cost calculation
- Video download and validation
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

from backend.services.video_renderer import (
    render_video_task,
    download_video,
    _render_video_with_retry,
    _calculate_actual_cost,
    _update_status,
    _update_progress,
    EXPONENTIAL_BACKOFF_BASE,
    MAX_RETRIES
)
from backend.models.video_generation import VideoStatus, VideoProgress


# ===== Fixtures =====

@pytest.fixture
def mock_job_approved():
    """Mock job data with approved storyboard."""
    return {
        "id": 123,
        "prompt": "Test video prompt",
        "parameters": {"duration": 30, "style": "cinematic"},
        "approved": True,
        "estimated_cost": 2.5,
        "storyboard_data": json.dumps([
            {
                "scene": {
                    "scene_number": 1,
                    "description": "Opening scene",
                    "duration": 5.0,
                    "image_prompt": "Opening shot"
                },
                "image_url": "https://example.com/image1.jpg",
                "generation_status": "completed",
                "error": None
            },
            {
                "scene": {
                    "scene_number": 2,
                    "description": "Middle scene",
                    "duration": 5.0,
                    "image_prompt": "Middle shot"
                },
                "image_url": "https://example.com/image2.jpg",
                "generation_status": "completed",
                "error": None
            }
        ])
    }


@pytest.fixture
def mock_job_not_approved():
    """Mock job data without storyboard approval."""
    return {
        "id": 456,
        "prompt": "Test video prompt",
        "parameters": {},
        "approved": False,
        "storyboard_data": json.dumps([])
    }


@pytest.fixture
def mock_replicate_client():
    """Mock ReplicateClient for testing."""
    with patch('backend.services.video_renderer.ReplicateClient') as mock:
        client = Mock()
        client.generate_video.return_value = {
            "success": True,
            "video_url": "https://replicate.delivery/test-video.mp4",
            "error": None,
            "prediction_id": "pred123",
            "duration_seconds": 10
        }
        mock.return_value = client
        yield mock


# ===== Test render_video_task =====

def test_render_video_task_success(mock_job_approved, mock_replicate_client):
    """Test successful video rendering workflow."""
    with patch('backend.services.video_renderer.get_job') as mock_get_job, \
         patch('backend.services.video_renderer.download_video') as mock_download, \
         patch('backend.services.video_renderer.get_db') as mock_db, \
         patch('backend.services.video_renderer._update_status') as mock_status, \
         patch('backend.services.video_renderer._update_progress') as mock_progress:

        mock_get_job.return_value = mock_job_approved
        mock_download.return_value = "/api/videos/123/data"

        # Mock database connection
        mock_conn = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_conn

        # Execute
        render_video_task(123)

        # Verify job was fetched
        mock_get_job.assert_called_once_with(123)

        # Verify video was generated
        client = mock_replicate_client.return_value
        client.generate_video.assert_called_once()
        image_urls = client.generate_video.call_args[0][0]
        assert len(image_urls) == 2
        assert image_urls[0] == "https://example.com/image1.jpg"
        assert image_urls[1] == "https://example.com/image2.jpg"

        # Verify video was downloaded
        mock_download.assert_called_once_with(
            "https://replicate.delivery/test-video.mp4",
            123
        )

        # Verify database was updated with video URL and cost
        assert mock_conn.execute.called
        # Find the UPDATE call
        update_calls = [c for c in mock_conn.execute.call_args_list
                       if 'UPDATE generated_videos' in str(c)]
        assert len(update_calls) > 0

        # Verify status updates
        status_calls = mock_status.call_args_list
        assert any(VideoStatus.RENDERING in str(c) for c in status_calls)


def test_render_video_task_not_approved(mock_job_not_approved):
    """Test that rendering fails if storyboard is not approved."""
    with patch('backend.services.video_renderer.get_job') as mock_get_job, \
         patch('backend.services.video_renderer.mark_job_failed') as mock_fail:

        mock_get_job.return_value = mock_job_not_approved

        # Execute
        render_video_task(456)

        # Verify job was marked as failed
        mock_fail.assert_called_once()
        args = mock_fail.call_args[0]
        assert args[0] == 456
        assert "approved" in args[1].lower()


def test_render_video_task_missing_storyboard():
    """Test that rendering fails if storyboard data is missing."""
    job = {
        "id": 789,
        "approved": True,
        "storyboard_data": None
    }

    with patch('backend.services.video_renderer.get_job') as mock_get_job, \
         patch('backend.services.video_renderer.mark_job_failed') as mock_fail:

        mock_get_job.return_value = job

        # Execute
        render_video_task(789)

        # Verify job was marked as failed
        mock_fail.assert_called_once()
        args = mock_fail.call_args[0]
        assert args[0] == 789
        assert "storyboard" in args[1].lower()


def test_render_video_task_missing_image_url(mock_replicate_client):
    """Test that rendering fails if any scene is missing image_url."""
    job = {
        "id": 999,
        "approved": True,
        "estimated_cost": 1.0,
        "storyboard_data": json.dumps([
            {
                "scene": {"scene_number": 1, "description": "Scene 1", "duration": 5.0, "image_prompt": "Test"},
                "image_url": "https://example.com/image1.jpg",
                "generation_status": "completed",
                "error": None
            },
            {
                "scene": {"scene_number": 2, "description": "Scene 2", "duration": 5.0, "image_prompt": "Test"},
                "image_url": None,  # Missing!
                "generation_status": "failed",
                "error": "Generation failed"
            }
        ])
    }

    with patch('backend.services.video_renderer.get_job') as mock_get_job, \
         patch('backend.services.video_renderer.mark_job_failed') as mock_fail:

        mock_get_job.return_value = job

        # Execute
        render_video_task(999)

        # Verify job was marked as failed
        mock_fail.assert_called_once()
        args = mock_fail.call_args[0]
        assert args[0] == 999
        assert "scene 2" in args[1].lower()
        assert "missing" in args[1].lower()


# ===== Test _render_video_with_retry =====

def test_render_video_with_retry_success(mock_replicate_client):
    """Test successful video rendering on first attempt."""
    with patch('backend.services.video_renderer._update_progress'):
        result = _render_video_with_retry(
            123,
            ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
            max_retries=2
        )

        assert result["success"] is True
        assert result["video_url"] == "https://replicate.delivery/test-video.mp4"
        assert result["duration_seconds"] == 10


def test_render_video_with_retry_eventual_success(mock_replicate_client):
    """Test video rendering succeeds after retries."""
    with patch('backend.services.video_renderer._update_progress'), \
         patch('backend.services.video_renderer.increment_retry_count'), \
         patch('time.sleep'):  # Mock sleep to speed up test

        client = mock_replicate_client.return_value

        # Fail first attempt, succeed on second
        client.generate_video.side_effect = [
            {"success": False, "error": "Temporary failure"},
            {
                "success": True,
                "video_url": "https://replicate.delivery/test-video.mp4",
                "duration_seconds": 10
            }
        ]

        result = _render_video_with_retry(
            123,
            ["https://example.com/img1.jpg"],
            max_retries=2
        )

        assert result["success"] is True
        assert client.generate_video.call_count == 2


def test_render_video_with_retry_max_retries_exceeded(mock_replicate_client):
    """Test video rendering fails after max retries."""
    with patch('backend.services.video_renderer._update_progress'), \
         patch('backend.services.video_renderer.increment_retry_count'), \
         patch('time.sleep'):

        client = mock_replicate_client.return_value

        # Always fail
        client.generate_video.return_value = {
            "success": False,
            "error": "Persistent failure"
        }

        result = _render_video_with_retry(
            123,
            ["https://example.com/img1.jpg"],
            max_retries=2
        )

        assert result["success"] is False
        assert "Persistent failure" in result["error"]
        assert client.generate_video.call_count == 3  # Initial + 2 retries


def test_render_video_with_retry_exponential_backoff(mock_replicate_client):
    """Test that retry logic uses exponential backoff."""
    with patch('backend.services.video_renderer._update_progress'), \
         patch('backend.services.video_renderer.increment_retry_count'), \
         patch('time.sleep') as mock_sleep:

        client = mock_replicate_client.return_value

        # Fail first two attempts
        client.generate_video.side_effect = [
            {"success": False, "error": "Fail 1"},
            {"success": False, "error": "Fail 2"},
            {"success": True, "video_url": "https://test.mp4", "duration_seconds": 5}
        ]

        _render_video_with_retry(123, ["https://img.jpg"], max_retries=2)

        # Verify sleep was called with exponential backoff
        # First retry: 30s, Second retry: 90s (30 * 3^1)
        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        assert 30 in sleep_calls  # First backoff
        assert 90 in sleep_calls  # Second backoff (30 * 3)


# ===== Test download_video =====

def test_download_video_success(tmp_path):
    """Test successful video download and validation."""
    # Create mock video data with MP4 signature
    mock_video_data = b'\x00\x00\x00\x18ftypmp4\x20' + b'\x00' * 1024

    with patch('requests.get') as mock_get, \
         patch('backend.services.video_renderer.Path') as mock_path_class:

        # Mock response
        mock_response = Mock()
        mock_response.iter_content.return_value = [mock_video_data]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Mock Path operations
        mock_video_dir = tmp_path / "videos" / "123"
        mock_video_dir.mkdir(parents=True, exist_ok=True)
        mock_video_path = mock_video_dir / "final.mp4"
        mock_temp_path = mock_video_dir / "final.tmp"

        mock_path_instance = Mock()
        mock_path_instance.__truediv__ = lambda self, other: mock_video_dir / other if other != "final.mp4" else mock_video_path
        mock_path_instance.mkdir = Mock()
        mock_path_class.return_value.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_video_dir

        # Patch open to write to temp file
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = mock_video_data
            mock_open.return_value.__enter__.return_value = mock_file

            with patch.object(Path, 'with_suffix', return_value=mock_temp_path), \
                 patch.object(Path, 'replace'), \
                 patch.object(Path, 'exists', return_value=False):

                result = download_video("https://example.com/video.mp4", 123)

                assert result == "/api/videos/123/data"
                mock_get.assert_called_once()


def test_download_video_empty_file():
    """Test that download fails for empty files."""
    with patch('requests.get') as mock_get, \
         patch('builtins.open', create=True):

        mock_response = Mock()
        mock_response.iter_content.return_value = []  # Empty
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="empty"):
            download_video("https://example.com/video.mp4", 123)


def test_download_video_invalid_format():
    """Test that download fails for invalid video format."""
    # Create data with invalid magic bytes
    invalid_data = b'INVALID_VIDEO_DATA' + b'\x00' * 1024

    with patch('requests.get') as mock_get, \
         patch('builtins.open', create=True) as mock_open, \
         patch('backend.services.video_renderer.Path'):

        mock_response = Mock()
        mock_response.iter_content.return_value = [invalid_data]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        mock_file = MagicMock()
        mock_file.read.return_value = invalid_data
        mock_open.return_value.__enter__.return_value = mock_file

        with pytest.raises(ValueError, match="valid video"):
            download_video("https://example.com/video.mp4", 123)


def test_download_video_network_error():
    """Test that download handles network errors."""
    import requests

    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

        with pytest.raises(ValueError, match="Network error"):
            download_video("https://example.com/video.mp4", 123)


# ===== Test _calculate_actual_cost =====

def test_calculate_actual_cost():
    """Test cost calculation."""
    # 10 images * $0.003 = $0.03
    # 20 seconds * $0.10 = $2.00
    # Total = $2.03
    cost = _calculate_actual_cost(num_images=10, video_duration=20)
    assert cost == 2.03


def test_calculate_actual_cost_zero():
    """Test cost calculation with zero values."""
    cost = _calculate_actual_cost(num_images=0, video_duration=0)
    assert cost == 0.0


def test_calculate_actual_cost_rounding():
    """Test that cost is rounded to 2 decimal places."""
    # 3 images * $0.003 = $0.009
    # 7 seconds * $0.10 = $0.70
    # Total = $0.709 -> $0.71
    cost = _calculate_actual_cost(num_images=3, video_duration=7)
    assert cost == 0.71


# ===== Test helper functions =====

def test_update_status():
    """Test status update function."""
    with patch('backend.services.video_renderer.get_db') as mock_db, \
         patch('backend.services.video_renderer.update_job_progress') as mock_progress:

        mock_conn = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_conn

        _update_status(123, VideoStatus.RENDERING, "Test message")

        # Verify database update
        mock_conn.execute.assert_called_once()
        sql = mock_conn.execute.call_args[0][0]
        assert "UPDATE generated_videos" in sql
        assert "status" in sql

        # Verify progress update
        mock_progress.assert_called_once()


def test_update_progress():
    """Test progress update function."""
    with patch('backend.services.video_renderer.update_job_progress') as mock_progress:

        _update_progress(
            123,
            current_stage=VideoStatus.RENDERING,
            message="Rendering in progress"
        )

        mock_progress.assert_called_once()
        progress_data = mock_progress.call_args[0][1]
        assert progress_data["current_stage"] == VideoStatus.RENDERING
        assert progress_data["message"] == "Rendering in progress"


# ===== Integration-style tests =====

def test_full_workflow_integration(mock_job_approved, mock_replicate_client):
    """Test complete workflow from start to finish."""
    with patch('backend.services.video_renderer.get_job') as mock_get_job, \
         patch('backend.services.video_renderer.download_video') as mock_download, \
         patch('backend.services.video_renderer.get_db') as mock_db, \
         patch('backend.services.video_renderer._update_status'), \
         patch('backend.services.video_renderer._update_progress'):

        mock_get_job.return_value = mock_job_approved
        mock_download.return_value = "/api/videos/123/data"
        mock_conn = MagicMock()
        mock_db.return_value.__enter__.return_value = mock_conn

        # Execute
        render_video_task(123)

        # Verify complete workflow
        assert mock_get_job.called
        assert mock_replicate_client.return_value.generate_video.called
        assert mock_download.called
        assert mock_conn.execute.called
        assert mock_conn.commit.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
