"""
Unit tests for scene generation service.

Tests the AI-powered scene generation functionality including:
- Scene generation from ad basics and creative direction
- Scene count calculation based on duration
- Scene regeneration with feedback
- Error handling and validation
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from backend.services.scene_generator import (
    generate_scenes,
    regenerate_scene,
    SceneGenerationError,
    _calculate_optimal_scenes,
    _build_scene_generation_prompt,
    _post_process_scenes
)


class TestSceneGeneration:
    """Test suite for scene generation functionality."""

    @pytest.fixture
    def sample_ad_basics(self):
        """Sample ad basics data for testing."""
        return {
            "product": "EcoBottle - Sustainable Water Bottle",
            "targetAudience": "Environmentally conscious millennials",
            "keyMessage": "Stay hydrated, save the planet",
            "callToAction": "Shop Now at ecobottle.com"
        }

    @pytest.fixture
    def sample_creative_direction(self):
        """Sample creative direction data for testing."""
        return {
            "style": "modern",
            "tone": "inspiring",
            "visualElements": ["nature", "lifestyle", "product shots"]
        }

    @pytest.fixture
    def sample_assets(self):
        """Sample asset IDs for testing."""
        return [
            "asset-001-product-shot",
            "asset-002-lifestyle",
            "asset-003-nature"
        ]

    def test_calculate_optimal_scenes_30_seconds(self):
        """Test optimal scene calculation for 30-second video."""
        result = _calculate_optimal_scenes(30.0)
        assert result >= 3
        assert result <= 7
        assert isinstance(result, int)

    def test_calculate_optimal_scenes_15_seconds(self):
        """Test optimal scene calculation for 15-second video."""
        result = _calculate_optimal_scenes(15.0)
        assert result >= 3
        assert result <= 5

    def test_calculate_optimal_scenes_60_seconds(self):
        """Test optimal scene calculation for 60-second video."""
        result = _calculate_optimal_scenes(60.0)
        assert result >= 5
        assert result <= 7

    @patch('backend.services.scene_generator.OpenAI')
    def test_generate_scenes_success(self, mock_openai, sample_ad_basics, sample_creative_direction, sample_assets):
        """Test successful scene generation."""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "scenes": [
                {
                    "sceneNumber": 1,
                    "duration": 5.0,
                    "description": "Opening shot of pristine nature",
                    "script": "Imagine a world without plastic waste",
                    "shotType": "wide",
                    "transition": "fade",
                    "assets": ["asset-003-nature"]
                },
                {
                    "sceneNumber": 2,
                    "duration": 8.0,
                    "description": "Product showcase in natural setting",
                    "script": "Meet EcoBottle, your sustainable companion",
                    "shotType": "close-up",
                    "transition": "cut",
                    "assets": ["asset-001-product-shot"]
                },
                {
                    "sceneNumber": 3,
                    "duration": 7.0,
                    "description": "Lifestyle shot with product",
                    "script": "Stay hydrated, stay sustainable",
                    "shotType": "medium",
                    "transition": "dissolve",
                    "assets": ["asset-002-lifestyle"]
                },
                {
                    "sceneNumber": 4,
                    "duration": 6.0,
                    "description": "Environmental impact message",
                    "script": "Every bottle saves 100 plastic bottles from landfills",
                    "shotType": "wide",
                    "transition": "fade",
                    "assets": ["asset-003-nature"]
                },
                {
                    "sceneNumber": 5,
                    "duration": 4.0,
                    "description": "Call to action",
                    "script": "Shop Now at ecobottle.com",
                    "shotType": "close-up",
                    "transition": "cut",
                    "assets": ["asset-001-product-shot"]
                }
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response

        # Generate scenes
        scenes = generate_scenes(
            ad_basics=sample_ad_basics,
            creative_direction=sample_creative_direction,
            assets=sample_assets,
            duration=30.0
        )

        # Assertions
        assert len(scenes) == 5
        assert all(isinstance(s, dict) for s in scenes)
        assert all('sceneNumber' in s for s in scenes)
        assert all('duration' in s for s in scenes)
        assert all('description' in s for s in scenes)
        assert scenes[0]['sceneNumber'] == 1
        assert sum(s['duration'] for s in scenes) == 30.0

    @patch('backend.services.scene_generator.OpenAI')
    def test_generate_scenes_with_auto_scene_count(self, mock_openai, sample_ad_basics, sample_creative_direction):
        """Test scene generation with automatic scene count calculation."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "scenes": [
                {"sceneNumber": i, "duration": 10.0, "description": f"Scene {i}",
                 "script": f"Script {i}", "shotType": "medium", "transition": "cut"}
                for i in range(1, 4)
            ]
        })
        mock_client.chat.completions.create.return_value = mock_response

        scenes = generate_scenes(
            ad_basics=sample_ad_basics,
            creative_direction=sample_creative_direction,
            duration=30.0,
            num_scenes=None  # Auto-calculate
        )

        assert len(scenes) >= 3
        mock_client.chat.completions.create.assert_called_once()

    def test_generate_scenes_missing_ad_basics(self):
        """Test that missing ad_basics raises error."""
        with pytest.raises(SceneGenerationError, match="ad_basics is required"):
            generate_scenes(
                ad_basics=None,
                creative_direction={},
                duration=30.0
            )

    @patch('backend.services.scene_generator.OpenAI')
    def test_regenerate_scene_success(self, mock_openai, sample_ad_basics, sample_creative_direction):
        """Test successful scene regeneration with feedback."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        original_scene = {
            "sceneNumber": 2,
            "duration": 8.0,
            "description": "Product showcase",
            "script": "Original script",
            "shotType": "close-up",
            "transition": "cut"
        }

        all_scenes = [
            {"sceneNumber": 1, "duration": 7.0, "description": "Scene 1"},
            original_scene,
            {"sceneNumber": 3, "duration": 15.0, "description": "Scene 3"}
        ]

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "sceneNumber": 2,
            "duration": 8.0,
            "description": "Enhanced product showcase with emotional appeal",
            "script": "Regenerated script with more impact",
            "shotType": "medium",
            "transition": "dissolve",
            "assets": []
        })
        mock_client.chat.completions.create.return_value = mock_response

        regenerated = regenerate_scene(
            scene_number=2,
            original_scene=original_scene,
            all_scenes=all_scenes,
            ad_basics=sample_ad_basics,
            creative_direction=sample_creative_direction,
            feedback="Make it more emotional and impactful",
            constraints={"duration": 8.0}
        )

        assert regenerated['sceneNumber'] == 2
        assert regenerated['duration'] == 8.0
        assert 'Enhanced' in regenerated['description']
        assert regenerated['script'] != original_scene['script']
        mock_client.chat.completions.create.assert_called_once()

    def test_post_process_scenes_duration_adjustment(self):
        """Test that post-processing adjusts scene durations to match total."""
        scenes = [
            {"sceneNumber": 1, "duration": 10.0, "description": "Scene 1", "assets": []},
            {"sceneNumber": 2, "duration": 10.0, "description": "Scene 2", "assets": []},
            {"sceneNumber": 3, "duration": 10.0, "description": "Scene 3", "assets": []}
        ]

        processed = _post_process_scenes(scenes, target_duration=25.0, available_assets=[])

        # Total duration should be close to target
        total_duration = sum(s['duration'] for s in processed)
        assert abs(total_duration - 25.0) < 0.5  # Allow small rounding differences
        assert len(processed) == 3

    def test_post_process_scenes_asset_distribution(self):
        """Test that post-processing distributes assets if scenes have none."""
        scenes = [
            {"sceneNumber": 1, "duration": 10.0, "description": "Scene 1", "assets": []},
            {"sceneNumber": 2, "duration": 10.0, "description": "Scene 2", "assets": []},
            {"sceneNumber": 3, "duration": 10.0, "description": "Scene 3", "assets": []}
        ]

        available_assets = ["asset-001", "asset-002", "asset-003"]
        processed = _post_process_scenes(scenes, target_duration=30.0, available_assets=available_assets)

        # Check that at least some assets were distributed
        total_assets = sum(len(s.get('assets', [])) for s in processed)
        assert total_assets > 0

    def test_build_scene_generation_prompt(self, sample_ad_basics, sample_creative_direction, sample_assets):
        """Test that prompt building includes all necessary information."""
        prompt = _build_scene_generation_prompt(
            ad_basics=sample_ad_basics,
            creative_direction=sample_creative_direction,
            assets=sample_assets,
            video_duration=30.0,
            num_scenes=5
        )

        # Check that prompt contains key information
        assert sample_ad_basics['product'] in prompt
        assert sample_ad_basics['targetAudience'] in prompt
        assert sample_ad_basics['keyMessage'] in prompt
        assert str(30.0) in prompt or '30' in prompt
        assert '5' in prompt
        assert sample_creative_direction['style'] in prompt

    @patch('backend.services.scene_generator.OpenAI')
    def test_generate_scenes_openai_error(self, mock_openai, sample_ad_basics, sample_creative_direction):
        """Test handling of OpenAI API errors."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(SceneGenerationError):
            generate_scenes(
                ad_basics=sample_ad_basics,
                creative_direction=sample_creative_direction,
                duration=30.0
            )

    @patch('backend.services.scene_generator.OpenAI')
    def test_generate_scenes_invalid_json_response(self, mock_openai, sample_ad_basics, sample_creative_direction):
        """Test handling of invalid JSON in OpenAI response."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON"
        mock_client.chat.completions.create.return_value = mock_response

        with pytest.raises(SceneGenerationError):
            generate_scenes(
                ad_basics=sample_ad_basics,
                creative_direction=sample_creative_direction,
                duration=30.0
            )

    def test_scene_number_validation(self):
        """Test that scene numbers are sequential."""
        scenes = [
            {"sceneNumber": 1, "duration": 10.0, "description": "Scene 1", "assets": []},
            {"sceneNumber": 2, "duration": 10.0, "description": "Scene 2", "assets": []},
            {"sceneNumber": 3, "duration": 10.0, "description": "Scene 3", "assets": []}
        ]

        processed = _post_process_scenes(scenes, target_duration=30.0, available_assets=[])

        for i, scene in enumerate(processed, 1):
            assert scene['sceneNumber'] == i


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
