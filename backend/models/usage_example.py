#!/usr/bin/env python3
"""
Usage examples for video generation Pydantic models.

This demonstrates how the models will be used in the actual API implementation.
"""

from datetime import datetime
from backend.models.video_generation import (
    VideoStatus,
    Scene,
    StoryboardEntry,
    GenerationRequest,
    VideoProgress,
    JobResponse,
)


def example_1_create_generation_request():
    """Example 1: Creating a video generation request."""
    print("=" * 60)
    print("Example 1: Creating a Generation Request")
    print("=" * 60)

    request = GenerationRequest(
        prompt="Create a promotional video showcasing our new AI-powered analytics platform. "
               "Show data visualizations, team collaboration, and business insights.",
        duration=45,
        style="cinematic",
        aspect_ratio="16:9",
        client_id="acme-analytics",
        brand_guidelines={
            "primary_color": "#0066CC",
            "secondary_color": "#FF6B35",
            "logo_url": "https://example.com/logo.png",
            "tone": "professional yet approachable"
        }
    )

    print(f"Prompt: {request.prompt[:80]}...")
    print(f"Duration: {request.duration}s")
    print(f"Style: {request.style}")
    print(f"Aspect Ratio: {request.aspect_ratio}")
    print(f"Client: {request.client_id}")
    print(f"Brand Guidelines: {request.brand_guidelines}")
    print()


def example_2_build_storyboard():
    """Example 2: Building a storyboard with scenes."""
    print("=" * 60)
    print("Example 2: Building a Storyboard")
    print("=" * 60)

    scenes_data = [
        {
            "scene_number": 1,
            "description": "Opening shot showing modern office with data dashboards",
            "duration": 5.0,
            "image_prompt": "Modern tech office, large screens displaying colorful data analytics dashboards, professional lighting, wide angle shot"
        },
        {
            "scene_number": 2,
            "description": "Close-up of AI processing data in real-time",
            "duration": 4.5,
            "image_prompt": "Futuristic AI visualization, flowing data streams, neural network graphics, blue and purple color scheme"
        },
        {
            "scene_number": 3,
            "description": "Team collaborating around interactive display",
            "duration": 6.0,
            "image_prompt": "Diverse business team gathered around large touchscreen display, collaborative atmosphere, modern office setting"
        }
    ]

    storyboard = []
    for scene_data in scenes_data:
        scene = Scene(**scene_data)
        entry = StoryboardEntry(
            scene=scene,
            generation_status="pending"
        )
        storyboard.append(entry)

    print(f"Created storyboard with {len(storyboard)} scenes:")
    for entry in storyboard:
        print(f"  Scene {entry.scene.scene_number}: {entry.scene.description[:60]}...")
        print(f"    Duration: {entry.scene.duration}s | Status: {entry.generation_status}")
    print()


def example_3_track_progress():
    """Example 3: Tracking video generation progress."""
    print("=" * 60)
    print("Example 3: Progress Tracking")
    print("=" * 60)

    # Initial state
    progress1 = VideoProgress(
        current_stage=VideoStatus.PARSING,
        scenes_total=0,
        scenes_completed=0,
        message="Analyzing prompt and extracting requirements..."
    )
    print(f"Stage 1: {progress1.current_stage}")
    print(f"  {progress1.message}")
    print()

    # Storyboard generation
    progress2 = VideoProgress(
        current_stage=VideoStatus.GENERATING_STORYBOARD,
        scenes_total=6,
        scenes_completed=3,
        current_scene=4,
        estimated_completion_seconds=45,
        message="Generating scene 4 of 6"
    )
    print(f"Stage 2: {progress2.current_stage}")
    print(f"  Progress: {progress2.scenes_completed}/{progress2.scenes_total} scenes")
    print(f"  Current: Scene {progress2.current_scene}")
    print(f"  ETA: {progress2.estimated_completion_seconds}s")
    print(f"  {progress2.message}")
    print()

    # Rendering
    progress3 = VideoProgress(
        current_stage=VideoStatus.RENDERING,
        scenes_total=6,
        scenes_completed=6,
        estimated_completion_seconds=120,
        message="Rendering final video..."
    )
    print(f"Stage 3: {progress3.current_stage}")
    print(f"  All {progress3.scenes_completed} scenes completed")
    print(f"  {progress3.message}")
    print(f"  ETA: {progress3.estimated_completion_seconds}s")
    print()


def example_4_complete_job_response():
    """Example 4: Complete job response."""
    print("=" * 60)
    print("Example 4: Complete Job Response")
    print("=" * 60)

    # Create scenes
    scene1 = Scene(
        scene_number=1,
        description="Opening corporate shot",
        duration=5.0,
        image_prompt="Professional corporate office environment, cinematic lighting"
    )

    scene2 = Scene(
        scene_number=2,
        description="Product showcase",
        duration=7.5,
        image_prompt="Modern AI analytics dashboard, sleek interface, data visualization"
    )

    # Create storyboard
    storyboard = [
        StoryboardEntry(
            scene=scene1,
            image_url="https://storage.example.com/jobs/12345/scene_1.jpg",
            generation_status="completed"
        ),
        StoryboardEntry(
            scene=scene2,
            image_url="https://storage.example.com/jobs/12345/scene_2.jpg",
            generation_status="completed"
        )
    ]

    # Create progress
    progress = VideoProgress(
        current_stage=VideoStatus.COMPLETED,
        scenes_total=2,
        scenes_completed=2,
        message="Video generation complete!"
    )

    # Create complete job response
    job = JobResponse(
        job_id=12345,
        status=VideoStatus.COMPLETED,
        progress=progress,
        storyboard=storyboard,
        video_url="https://storage.example.com/jobs/12345/final_video.mp4",
        estimated_cost=24.50,
        actual_cost=23.75,
        created_at=datetime(2025, 11, 15, 14, 30, 0),
        updated_at=datetime(2025, 11, 15, 14, 45, 0),
        approved=True
    )

    print(f"Job ID: {job.job_id}")
    print(f"Status: {job.status}")
    print(f"Created: {job.created_at.isoformat()}")
    print(f"Updated: {job.updated_at.isoformat()}")
    print(f"Approved: {job.approved}")
    print(f"Estimated Cost: ${job.estimated_cost:.2f}")
    print(f"Actual Cost: ${job.actual_cost:.2f}")
    print(f"Savings: ${job.estimated_cost - job.actual_cost:.2f}")
    print(f"\nStoryboard: {len(job.storyboard)} scenes")
    for entry in job.storyboard:
        print(f"  Scene {entry.scene.scene_number}: {entry.generation_status}")
        print(f"    Image: {entry.image_url}")
    print(f"\nVideo URL: {job.video_url}")
    print()


def example_5_json_serialization():
    """Example 5: JSON serialization and deserialization."""
    print("=" * 60)
    print("Example 5: JSON Serialization")
    print("=" * 60)

    request = GenerationRequest(
        prompt="Create a video about sustainable technology innovations",
        duration=30,
        style="documentary",
        aspect_ratio="16:9"
    )

    # Serialize to JSON
    json_str = request.model_dump_json(indent=2)
    print("Serialized to JSON:")
    print(json_str)
    print()

    # Deserialize from JSON
    restored = GenerationRequest.model_validate_json(json_str)
    print("Restored from JSON:")
    print(f"  Prompt: {restored.prompt[:60]}...")
    print(f"  Duration: {restored.duration}s")
    print(f"  Style: {restored.style}")
    print()


def example_6_validation_errors():
    """Example 6: Validation error handling."""
    print("=" * 60)
    print("Example 6: Validation Error Handling")
    print("=" * 60)

    from pydantic import ValidationError

    # Invalid prompt (too short)
    try:
        GenerationRequest(prompt="Short", duration=30)
    except ValidationError as e:
        print("Error 1: Prompt too short")
        print(f"  {e.errors()[0]['msg']}")
        print()

    # Invalid duration (too long)
    try:
        GenerationRequest(
            prompt="A valid prompt that is long enough",
            duration=500  # Exceeds 300s limit
        )
    except ValidationError as e:
        print("Error 2: Duration too long")
        print(f"  {e.errors()[0]['msg']}")
        print()

    # Invalid aspect ratio
    try:
        GenerationRequest(
            prompt="A valid prompt that is long enough",
            duration=30,
            aspect_ratio="21:9"  # Not in allowed list
        )
    except ValidationError as e:
        print("Error 3: Invalid aspect ratio")
        print(f"  {e.errors()[0]['msg']}")
        print()

    # Invalid scene number
    try:
        Scene(
            scene_number=0,  # Must be >= 1
            description="Test scene",
            duration=5.0,
            image_prompt="Test prompt"
        )
    except ValidationError as e:
        print("Error 4: Invalid scene number")
        print(f"  {e.errors()[0]['msg']}")
        print()


def main():
    """Run all examples."""
    print("\n")
    print("*" * 60)
    print("VIDEO GENERATION PYDANTIC MODELS - USAGE EXAMPLES")
    print("*" * 60)
    print("\n")

    example_1_create_generation_request()
    example_2_build_storyboard()
    example_3_track_progress()
    example_4_complete_job_response()
    example_5_json_serialization()
    example_6_validation_errors()

    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
