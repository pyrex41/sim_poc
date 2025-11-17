"""
Unit tests for storyboard_generator module.

Tests the background task for generating storyboards from video prompts,
including prompt parsing, image generation, progress tracking, and error handling.
"""

import unittest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.storyboard_generator import (
    generate_storyboard_task,
    parse_prompt_to_scenes,
    _generate_image_with_retry,
    _update_status,
    _update_progress,
    _save_storyboard
)
from backend.models.video_generation import Scene, StoryboardEntry, VideoStatus, VideoProgress


class TestParsePromptToScenes(unittest.TestCase):
    """Test the parse_prompt_to_scenes function."""

    def test_basic_parsing(self):
        """Test basic prompt parsing with default parameters."""
        prompt = "A robot exploring Mars with dramatic red landscapes"
        duration = 30

        scenes = parse_prompt_to_scenes(prompt, duration)

        # Should generate appropriate number of scenes
        self.assertGreaterEqual(len(scenes), 3)
        self.assertLessEqual(len(scenes), 10)

        # Each scene should be valid
        for scene in scenes:
            self.assertIsInstance(scene, Scene)
            self.assertGreater(scene.scene_number, 0)
            self.assertGreater(scene.duration, 0)
            self.assertIsNotNone(scene.description)
            self.assertIsNotNone(scene.image_prompt)

    def test_duration_distribution(self):
        """Test that scene durations sum to total duration."""
        prompt = "Test video"
        duration = 30

        scenes = parse_prompt_to_scenes(prompt, duration)

        total_scene_duration = sum(s.duration for s in scenes)

        # Allow small rounding error
        self.assertAlmostEqual(total_scene_duration, duration, delta=0.1)

    def test_short_duration(self):
        """Test minimum scene count for short videos."""
        prompt = "Quick video"
        duration = 5

        scenes = parse_prompt_to_scenes(prompt, duration)

        # Should generate at least 3 scenes
        self.assertGreaterEqual(len(scenes), 3)

    def test_long_duration(self):
        """Test maximum scene count for long videos."""
        prompt = "Long video"
        duration = 120

        scenes = parse_prompt_to_scenes(prompt, duration)

        # Should cap at 10 scenes
        self.assertLessEqual(len(scenes), 10)

    def test_style_modifier(self):
        """Test that style is included in image prompts."""
        prompt = "A sunset over mountains"
        duration = 30
        style = "cinematic"

        scenes = parse_prompt_to_scenes(prompt, duration, style)

        # Style should appear in image prompts
        for scene in scenes:
            self.assertIn(style, scene.image_prompt.lower())

    def test_scene_numbering(self):
        """Test that scenes are numbered sequentially."""
        prompt = "Test video"
        duration = 30

        scenes = parse_prompt_to_scenes(prompt, duration)

        for idx, scene in enumerate(scenes):
            self.assertEqual(scene.scene_number, idx + 1)


class TestGenerateImageWithRetry(unittest.TestCase):
    """Test the _generate_image_with_retry function."""

    @patch('backend.services.storyboard_generator.time.sleep')
    def test_success_on_first_attempt(self, mock_sleep):
        """Test successful image generation on first try."""
        mock_client = Mock()
        mock_client.generate_image.return_value = {
            "success": True,
            "image_url": "https://example.com/image.jpg",
            "error": None
        }

        result = _generate_image_with_retry(
            mock_client,
            "test prompt",
            job_id=1,
            scene_num=1,
            max_retries=3
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["image_url"], "https://example.com/image.jpg")
        self.assertEqual(mock_client.generate_image.call_count, 1)
        mock_sleep.assert_not_called()

    @patch('backend.services.storyboard_generator.time.sleep')
    def test_success_after_retries(self, mock_sleep):
        """Test successful image generation after retries."""
        mock_client = Mock()
        mock_client.generate_image.side_effect = [
            {"success": False, "error": "Temporary error"},
            {"success": False, "error": "Temporary error"},
            {"success": True, "image_url": "https://example.com/image.jpg", "error": None}
        ]

        result = _generate_image_with_retry(
            mock_client,
            "test prompt",
            job_id=1,
            scene_num=1,
            max_retries=3
        )

        self.assertTrue(result["success"])
        self.assertEqual(mock_client.generate_image.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Slept between retries

    @patch('backend.services.storyboard_generator.time.sleep')
    def test_failure_after_max_retries(self, mock_sleep):
        """Test failure after exhausting all retries."""
        mock_client = Mock()
        mock_client.generate_image.return_value = {
            "success": False,
            "error": "Persistent error"
        }

        result = _generate_image_with_retry(
            mock_client,
            "test prompt",
            job_id=1,
            scene_num=1,
            max_retries=3
        )

        self.assertFalse(result["success"])
        self.assertEqual(mock_client.generate_image.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('backend.services.storyboard_generator.time.sleep')
    def test_exponential_backoff(self, mock_sleep):
        """Test exponential backoff delays between retries."""
        mock_client = Mock()
        mock_client.generate_image.return_value = {
            "success": False,
            "error": "Temporary error"
        }

        _generate_image_with_retry(
            mock_client,
            "test prompt",
            job_id=1,
            scene_num=1,
            max_retries=3
        )

        # Check backoff delays: 2s, 4s
        calls = mock_sleep.call_args_list
        self.assertEqual(calls[0][0][0], 2)  # First retry: 2s
        self.assertEqual(calls[1][0][0], 4)  # Second retry: 4s


class TestStoryboardGenerator(unittest.TestCase):
    """Test the main generate_storyboard_task function."""

    @patch('backend.services.storyboard_generator.ReplicateClient')
    @patch('backend.services.storyboard_generator.get_job')
    @patch('backend.services.storyboard_generator.mark_job_failed')
    @patch('backend.services.storyboard_generator._update_status')
    @patch('backend.services.storyboard_generator._save_storyboard')
    @patch('backend.services.storyboard_generator._update_progress')
    def test_successful_storyboard_generation(
        self,
        mock_update_progress,
        mock_save_storyboard,
        mock_update_status,
        mock_mark_failed,
        mock_get_job,
        mock_replicate_client
    ):
        """Test successful end-to-end storyboard generation."""
        # Mock job data
        mock_get_job.return_value = {
            "id": 1,
            "prompt": "A robot exploring Mars",
            "parameters": {"duration": 15, "style": "cinematic"},
            "status": "pending"
        }

        # Mock image generation
        mock_client_instance = Mock()
        mock_client_instance.generate_image.return_value = {
            "success": True,
            "image_url": "https://example.com/image.jpg",
            "error": None
        }
        mock_replicate_client.return_value = mock_client_instance

        # Run task
        generate_storyboard_task(1)

        # Verify status updates
        self.assertGreaterEqual(mock_update_status.call_count, 2)  # At least parsing and storyboard_ready

        # Verify storyboard was saved
        self.assertGreater(mock_save_storyboard.call_count, 0)

        # Verify no failure
        mock_mark_failed.assert_not_called()

    @patch('backend.services.storyboard_generator.get_job')
    @patch('backend.services.storyboard_generator.mark_job_failed')
    def test_job_not_found(self, mock_mark_failed, mock_get_job):
        """Test handling of missing job."""
        mock_get_job.return_value = None

        generate_storyboard_task(999)

        # Should not mark as failed (job doesn't exist)
        mock_mark_failed.assert_not_called()

    @patch('backend.services.storyboard_generator.get_job')
    @patch('backend.services.storyboard_generator.mark_job_failed')
    @patch('backend.services.storyboard_generator.parse_prompt_to_scenes')
    def test_parsing_failure(self, mock_parse, mock_mark_failed, mock_get_job):
        """Test handling of prompt parsing failure."""
        mock_get_job.return_value = {
            "id": 1,
            "prompt": "Test prompt",
            "parameters": {"duration": 30},
            "status": "pending"
        }

        # Simulate parsing error
        mock_parse.side_effect = Exception("Parsing failed")

        generate_storyboard_task(1)

        # Should mark job as failed
        mock_mark_failed.assert_called_once()
        error_msg = mock_mark_failed.call_args[0][1]
        self.assertIn("parse", error_msg.lower())


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions."""

    @patch('backend.services.storyboard_generator.get_db')
    @patch('backend.services.storyboard_generator.update_job_progress')
    def test_update_status(self, mock_update_progress, mock_get_db):
        """Test _update_status function."""
        mock_conn = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_conn

        _update_status(1, VideoStatus.PARSING, "Parsing prompt...")

        # Verify database update
        mock_conn.execute.assert_called()
        mock_conn.commit.assert_called()

        # Verify progress update
        mock_update_progress.assert_called_once()

    @patch('backend.services.storyboard_generator.update_job_progress')
    def test_update_progress(self, mock_update_progress):
        """Test _update_progress function."""
        _update_progress(
            job_id=1,
            current_stage=VideoStatus.GENERATING_STORYBOARD,
            scenes_total=5,
            scenes_completed=2,
            current_scene=3,
            message="Generating image..."
        )

        mock_update_progress.assert_called_once()
        progress_data = mock_update_progress.call_args[0][1]

        self.assertEqual(progress_data["scenes_total"], 5)
        self.assertEqual(progress_data["scenes_completed"], 2)
        self.assertEqual(progress_data["current_scene"], 3)

    @patch('backend.services.storyboard_generator.get_db')
    def test_save_storyboard(self, mock_get_db):
        """Test _save_storyboard function."""
        mock_conn = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_conn

        # Create sample storyboard
        scene = Scene(
            scene_number=1,
            description="Test scene",
            duration=5.0,
            image_prompt="A test scene"
        )
        entry = StoryboardEntry(
            scene=scene,
            image_url="https://example.com/image.jpg",
            generation_status="completed",
            error=None
        )

        _save_storyboard(1, [entry])

        # Verify database update
        mock_conn.execute.assert_called()
        mock_conn.commit.assert_called()

        # Verify JSON serialization
        call_args = mock_conn.execute.call_args[0]
        storyboard_json = call_args[1][0]
        storyboard_data = json.loads(storyboard_json)

        self.assertEqual(len(storyboard_data), 1)
        self.assertEqual(storyboard_data[0]["scene"]["scene_number"], 1)
        self.assertEqual(storyboard_data[0]["generation_status"], "completed")


def run_tests():
    """Run all tests."""
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
