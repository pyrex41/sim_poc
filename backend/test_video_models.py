#!/usr/bin/env python3
"""Test script for video generation Pydantic models."""

from backend.models.video_generation import (
    VideoStatus, Scene, StoryboardEntry,
    GenerationRequest, VideoProgress, JobResponse
)
from datetime import datetime

def test_models():
    """Test all video generation models."""

    # Test VideoStatus enum
    print('Testing VideoStatus enum...')
    print(f'  PENDING: {VideoStatus.PENDING}')
    print(f'  COMPLETED: {VideoStatus.COMPLETED}')

    # Test Scene model
    print('\nTesting Scene model...')
    scene = Scene(
        scene_number=1,
        description='A beautiful sunset over mountains',
        duration=5.5,
        image_prompt='Cinematic shot of golden sunset over snow-capped mountains'
    )
    print(f'  Created scene: {scene.scene_number}, duration: {scene.duration}s')

    # Test GenerationRequest
    print('\nTesting GenerationRequest...')
    request = GenerationRequest(
        prompt='Create a promotional video about AI technology',
        duration=30,
        style='cinematic',
        aspect_ratio='16:9'
    )
    print(f'  Request prompt: {request.prompt[:50]}...')
    print(f'  Duration: {request.duration}s, Style: {request.style}')

    # Test VideoProgress
    print('\nTesting VideoProgress...')
    progress = VideoProgress(
        current_stage=VideoStatus.GENERATING_STORYBOARD,
        scenes_total=6,
        scenes_completed=3,
        current_scene=4,
        estimated_completion_seconds=120,
        message='Generating scene 4 of 6'
    )
    print(f'  Stage: {progress.current_stage}')
    print(f'  Progress: {progress.scenes_completed}/{progress.scenes_total}')

    # Test StoryboardEntry
    print('\nTesting StoryboardEntry...')
    entry = StoryboardEntry(
        scene=scene,
        image_url='https://example.com/scene1.jpg',
        generation_status='completed'
    )
    print(f'  Storyboard entry for scene {entry.scene.scene_number}: {entry.generation_status}')

    # Test JobResponse
    print('\nTesting JobResponse...')
    job = JobResponse(
        job_id=12345,
        status=VideoStatus.STORYBOARD_READY,
        progress=progress,
        storyboard=[entry],
        estimated_cost=15.50,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        approved=False
    )
    print(f'  Job ID: {job.job_id}')
    print(f'  Status: {job.status}')
    print(f'  Estimated cost: ${job.estimated_cost}')

    # Test JSON serialization
    print('\nTesting JSON serialization...')
    json_data = job.model_dump_json(indent=2)
    print(f'  JSON output length: {len(json_data)} characters')
    print('  First 200 chars:', json_data[:200])

    # Test validation errors
    print('\nTesting validation...')
    try:
        invalid_scene = Scene(
            scene_number=0,  # Invalid: must be >= 1
            description='Test',
            duration=5.0,
            image_prompt='Test prompt'
        )
    except Exception as e:
        print(f'  ✓ Caught expected validation error for scene_number: {type(e).__name__}')

    try:
        invalid_request = GenerationRequest(
            prompt='Too short',  # Invalid: must be >= 10 chars
            duration=30
        )
    except Exception as e:
        print(f'  ✓ Caught expected validation error for prompt: {type(e).__name__}')

    try:
        invalid_ratio = GenerationRequest(
            prompt='A valid prompt that is long enough',
            duration=30,
            aspect_ratio='21:9'  # Invalid ratio
        )
    except Exception as e:
        print(f'  ✓ Caught expected validation error for aspect_ratio: {type(e).__name__}')

    print('\n✓ All models validated successfully!')

if __name__ == '__main__':
    test_models()
