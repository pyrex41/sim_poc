"""
Scene Generation Service.

This module handles AI-powered scene generation for video ad creation.
Uses LLM to generate scene descriptions, scripts, and shot suggestions.
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

# Configuration from environment
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")  # openai, anthropic, etc.
AI_API_KEY = os.getenv("OPENAI_API_KEY")  # Default to OpenAI key
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")  # Default model
SCENES_PER_VIDEO_MIN = int(os.getenv("SCENES_PER_VIDEO_MIN", "3"))
SCENES_PER_VIDEO_MAX = int(os.getenv("SCENES_PER_VIDEO_MAX", "7"))
DEFAULT_VIDEO_DURATION = float(os.getenv("DEFAULT_VIDEO_DURATION", "30.0"))


class SceneGenerationError(Exception):
    """Exception raised when scene generation fails."""
    pass


def generate_scenes(
    ad_basics: Dict[str, Any],
    creative_direction: Dict[str, Any],
    assets: Optional[List[str]] = None,
    duration: Optional[float] = None,
    num_scenes: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate scenes for a video ad using AI/LLM.

    Args:
        ad_basics: Ad basics containing product, target audience, key message, CTA
        creative_direction: Creative direction with style, tone, visual elements
        assets: Optional list of asset IDs to incorporate
        duration: Total video duration in seconds (default: 30.0)
        num_scenes: Number of scenes to generate (default: auto-determine)

    Returns:
        List of scene dictionaries with structure:
        {
            "sceneNumber": int,
            "duration": float,
            "description": str,
            "script": str,
            "shotType": str,
            "transition": str,
            "assets": List[str],
            "metadata": dict
        }

    Raises:
        SceneGenerationError: If generation fails
    """
    logger.info("Generating scenes with AI/LLM")

    # Validate inputs
    if not ad_basics:
        raise SceneGenerationError("ad_basics is required")

    # Set defaults
    video_duration = duration or DEFAULT_VIDEO_DURATION
    target_num_scenes = num_scenes or _calculate_optimal_scenes(video_duration)

    # Ensure target within bounds
    target_num_scenes = max(SCENES_PER_VIDEO_MIN, min(target_num_scenes, SCENES_PER_VIDEO_MAX))

    # Build prompt for LLM
    prompt = _build_scene_generation_prompt(
        ad_basics=ad_basics,
        creative_direction=creative_direction,
        assets=assets,
        video_duration=video_duration,
        num_scenes=target_num_scenes
    )

    # Call AI provider
    try:
        if AI_PROVIDER == "openai":
            scenes = _generate_scenes_openai(prompt, target_num_scenes)
        else:
            raise SceneGenerationError(f"Unsupported AI provider: {AI_PROVIDER}")

        # Post-process and validate scenes
        scenes = _post_process_scenes(scenes, video_duration, assets or [])

        logger.info(f"Successfully generated {len(scenes)} scenes")
        return scenes

    except Exception as e:
        logger.error(f"Scene generation failed: {e}")
        raise SceneGenerationError(f"Failed to generate scenes: {str(e)}")


def regenerate_scene(
    scene_number: int,
    original_scene: Dict[str, Any],
    all_scenes: List[Dict[str, Any]],
    ad_basics: Dict[str, Any],
    creative_direction: Dict[str, Any],
    feedback: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Regenerate a single scene with optional user feedback.

    Args:
        scene_number: The scene number to regenerate (1-indexed)
        original_scene: The original scene data
        all_scenes: All scenes for context
        ad_basics: Ad basics for context
        creative_direction: Creative direction for context
        feedback: Optional user feedback (e.g., "make it more energetic")
        constraints: Optional constraints (e.g., {"duration": 10.0})

    Returns:
        Updated scene dictionary

    Raises:
        SceneGenerationError: If regeneration fails
    """
    logger.info(f"Regenerating scene {scene_number} with feedback: {feedback}")

    # Build regeneration prompt
    prompt = _build_scene_regeneration_prompt(
        scene_number=scene_number,
        original_scene=original_scene,
        all_scenes=all_scenes,
        ad_basics=ad_basics,
        creative_direction=creative_direction,
        feedback=feedback,
        constraints=constraints
    )

    try:
        if AI_PROVIDER == "openai":
            new_scene = _regenerate_scene_openai(prompt, original_scene)
        else:
            raise SceneGenerationError(f"Unsupported AI provider: {AI_PROVIDER}")

        # Apply constraints
        if constraints:
            if "duration" in constraints:
                new_scene["duration"] = constraints["duration"]

        logger.info(f"Successfully regenerated scene {scene_number}")
        return new_scene

    except Exception as e:
        logger.error(f"Scene regeneration failed: {e}")
        raise SceneGenerationError(f"Failed to regenerate scene: {str(e)}")


def _calculate_optimal_scenes(duration: float) -> int:
    """Calculate optimal number of scenes based on video duration."""
    if duration <= 15:
        return 3
    elif duration <= 30:
        return 4
    elif duration <= 45:
        return 5
    elif duration <= 60:
        return 6
    else:
        return 7


def _build_scene_generation_prompt(
    ad_basics: Dict[str, Any],
    creative_direction: Dict[str, Any],
    assets: Optional[List[str]],
    video_duration: float,
    num_scenes: int
) -> str:
    """Build the prompt for initial scene generation."""
    prompt = f"""Generate a {num_scenes}-scene storyboard for a {video_duration}-second video advertisement.

**Ad Basics:**
- Product: {ad_basics.get('product', 'N/A')}
- Target Audience: {ad_basics.get('targetAudience', 'N/A')}
- Key Message: {ad_basics.get('keyMessage', 'N/A')}
- Call to Action: {ad_basics.get('callToAction', 'N/A')}

**Creative Direction:**
- Style: {creative_direction.get('style', 'Modern')}
- Tone: {creative_direction.get('tone', 'Professional')}
- Visual Elements: {', '.join(creative_direction.get('visualElements', [])) if creative_direction.get('visualElements') else 'N/A'}
- Music Style: {creative_direction.get('musicStyle', 'Upbeat')}

**Available Assets:**
{len(assets) if assets else 0} assets provided for use

**Requirements:**
- Each scene should have a clear description
- Include suggested script/voiceover text
- Specify shot type (wide, medium, close-up, product, etc.)
- Specify transition (cut, fade, dissolve, etc.)
- Scenes should flow naturally and tell a cohesive story
- Total duration should sum to approximately {video_duration} seconds
- Each scene should be 4-10 seconds

Return ONLY a valid JSON array with this exact structure (no markdown, no explanation):
[
  {{
    "sceneNumber": 1,
    "duration": 6.0,
    "description": "detailed scene description",
    "script": "voiceover text",
    "shotType": "wide|medium|close-up|product",
    "transition": "cut|fade|dissolve",
    "metadata": {{
      "setting": "description",
      "mood": "description"
    }}
  }}
]"""
    return prompt


def _build_scene_regeneration_prompt(
    scene_number: int,
    original_scene: Dict[str, Any],
    all_scenes: List[Dict[str, Any]],
    ad_basics: Dict[str, Any],
    creative_direction: Dict[str, Any],
    feedback: Optional[str],
    constraints: Optional[Dict[str, Any]]
) -> str:
    """Build the prompt for scene regeneration."""
    context_before = [s for s in all_scenes if s["sceneNumber"] < scene_number]
    context_after = [s for s in all_scenes if s["sceneNumber"] > scene_number]

    prompt = f"""Regenerate scene {scene_number} for a video advertisement.

**Original Scene:**
```json
{json.dumps(original_scene, indent=2)}
```

**Context (Previous Scenes):**
{json.dumps(context_before[-2:], indent=2) if context_before else 'N/A'}

**Context (Following Scenes):**
{json.dumps(context_after[:2], indent=2) if context_after else 'N/A'}

**Ad Basics:**
- Product: {ad_basics.get('product')}
- Key Message: {ad_basics.get('keyMessage')}

**Creative Direction:**
- Style: {creative_direction.get('style')}
- Tone: {creative_direction.get('tone')}

**User Feedback:**
{feedback or 'No specific feedback - just provide fresh variation'}

**Constraints:**
{json.dumps(constraints, indent=2) if constraints else 'Maintain similar duration and flow'}

**Requirements:**
- Maintain continuity with surrounding scenes
- Apply user feedback if provided
- Keep the same scene structure
- Ensure natural flow with adjacent scenes

Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{{
  "sceneNumber": {scene_number},
  "duration": 6.0,
  "description": "updated scene description",
  "script": "updated voiceover text",
  "shotType": "wide|medium|close-up|product",
  "transition": "cut|fade|dissolve",
  "metadata": {{
    "setting": "description",
    "mood": "description"
  }}
}}"""
    return prompt


def _generate_scenes_openai(prompt: str, num_scenes: int) -> List[Dict[str, Any]]:
    """Generate scenes using OpenAI API."""
    if not AI_API_KEY:
        raise SceneGenerationError("OPENAI_API_KEY not configured")

    try:
        client = OpenAI(api_key=AI_API_KEY)

        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert video storyboard creator. Return ONLY valid JSON arrays/objects with no markdown formatting or explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000,
            response_format={"type": "json_object"} if "gpt-4" in AI_MODEL or "gpt-3.5" in AI_MODEL else None
        )

        content = response.choices[0].message.content
        logger.debug(f"OpenAI response: {content[:200]}...")

        # Parse JSON response
        try:
            # Try direct parse first
            scenes = json.loads(content)

            # If response is wrapped in an object, extract the array
            if isinstance(scenes, dict):
                # Look for array keys
                for key in ["scenes", "storyboard", "data", "result"]:
                    if key in scenes and isinstance(scenes[key], list):
                        scenes = scenes[key]
                        break

            if not isinstance(scenes, list):
                raise ValueError("Response is not a list")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Response content: {content}")
            raise SceneGenerationError("AI response was not valid JSON")

        return scenes

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise SceneGenerationError(f"OpenAI API error: {str(e)}")


def _regenerate_scene_openai(prompt: str, original_scene: Dict[str, Any]) -> Dict[str, Any]:
    """Regenerate a single scene using OpenAI API."""
    if not AI_API_KEY:
        raise SceneGenerationError("OPENAI_API_KEY not configured")

    try:
        client = OpenAI(api_key=AI_API_KEY)

        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert video storyboard creator. Return ONLY valid JSON objects with no markdown formatting or explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,  # Higher temperature for more variation
            max_tokens=1000
        )

        content = response.choices[0].message.content
        logger.debug(f"OpenAI regeneration response: {content[:200]}...")

        # Parse JSON response
        scene = json.loads(content)

        # Ensure scene has required fields
        if not isinstance(scene, dict):
            raise ValueError("Response is not a dictionary")

        return scene

    except Exception as e:
        logger.error(f"OpenAI API error during regeneration: {e}")
        raise SceneGenerationError(f"OpenAI API error: {str(e)}")


def _post_process_scenes(
    scenes: List[Dict[str, Any]],
    target_duration: float,
    available_assets: List[str]
) -> List[Dict[str, Any]]:
    """Post-process and validate generated scenes."""
    processed_scenes = []

    # Calculate total duration
    total_duration = sum(s.get("duration", 0) for s in scenes)

    for i, scene in enumerate(scenes):
        # Ensure scene number
        scene["sceneNumber"] = i + 1

        # Adjust duration proportionally if needed
        if total_duration > 0:
            duration_ratio = target_duration / total_duration
            scene["duration"] = round(scene.get("duration", 5.0) * duration_ratio, 1)
        else:
            scene["duration"] = round(target_duration / len(scenes), 1)

        # Ensure required fields
        scene.setdefault("description", f"Scene {i + 1}")
        scene.setdefault("script", "")
        scene.setdefault("shotType", "medium")
        scene.setdefault("transition", "cut" if i > 0 else "fade")
        scene.setdefault("assets", [])
        scene.setdefault("metadata", {})

        # Assign assets if available (simple distribution for now)
        if available_assets and not scene["assets"]:
            asset_index = i % len(available_assets)
            scene["assets"] = [available_assets[asset_index]]

        processed_scenes.append(scene)

    return processed_scenes
