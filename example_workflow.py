#!/usr/bin/env python3
"""
Example workflow demonstrating the use of new database helper functions
for the v2 Video Generation API with storyboard approval.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from database import (
    save_generated_video,
    update_job_progress,
    get_job,
    increment_retry_count,
    mark_job_failed,
    get_jobs_by_status,
    approve_storyboard
)

def example_video_generation_workflow():
    """
    Demonstrates a typical video generation workflow with progress tracking
    and storyboard approval.
    """
    print("=" * 70)
    print("Example: Video Generation Workflow with Storyboard Approval")
    print("=" * 70)

    # Step 1: Create initial job
    print("\n[STEP 1] Creating video generation job...")
    job_id = save_generated_video(
        prompt="A serene sunset over a mountain lake",
        video_url="",  # Will be populated later
        model_id="runway-gen3",
        parameters={"duration": 10, "aspect_ratio": "16:9"},
        status="pending"
    )
    print(f"Created job ID: {job_id}")

    # Step 2: Update progress - Generating storyboard
    print("\n[STEP 2] Generating storyboard...")
    update_job_progress(job_id, {
        "stage": "storyboard_generation",
        "percent": 20,
        "message": "AI is creating storyboard frames...",
        "current_frame": 1,
        "total_frames": 4
    })

    # Step 3: Storyboard ready for approval
    print("\n[STEP 3] Storyboard generated, awaiting approval...")
    update_job_progress(job_id, {
        "stage": "awaiting_approval",
        "percent": 40,
        "message": "Storyboard ready for review",
        "storyboard_frames": 4
    })

    # Get the job to show current state
    job = get_job(job_id)
    print(f"Current progress: {job['progress']}")
    print(f"Approved: {job['approved']}")

    # Step 4: Approve the storyboard
    print("\n[STEP 4] User approves storyboard...")
    approve_storyboard(job_id)

    job = get_job(job_id)
    print(f"Approved: {job['approved']}")
    print(f"Approved at: {job['approved_at']}")

    # Step 5: Start video generation
    print("\n[STEP 5] Starting video generation...")
    update_job_progress(job_id, {
        "stage": "video_generation",
        "percent": 60,
        "message": "Generating video from approved storyboard..."
    })

    # Step 6: Video generation complete
    print("\n[STEP 6] Video generation complete!")
    update_job_progress(job_id, {
        "stage": "completed",
        "percent": 100,
        "message": "Video generation successful"
    })

    # Get final job state
    job = get_job(job_id)
    print(f"Final status: {job['status']}")
    print(f"Final progress: {job['progress']}")

    return job_id

def example_error_handling_workflow():
    """
    Demonstrates error handling and retry logic.
    """
    print("\n\n" + "=" * 70)
    print("Example: Error Handling and Retry Logic")
    print("=" * 70)

    # Create a job
    print("\n[STEP 1] Creating video generation job...")
    job_id = save_generated_video(
        prompt="A futuristic cityscape at night",
        video_url="",
        model_id="runway-gen3",
        parameters={"duration": 8},
        status="processing"
    )
    print(f"Created job ID: {job_id}")

    # Simulate a failure
    print("\n[STEP 2] Simulating API failure...")
    retry_count = increment_retry_count(job_id)
    print(f"Retry count: {retry_count}")

    update_job_progress(job_id, {
        "stage": "retrying",
        "percent": 30,
        "message": f"Retrying after failure (attempt {retry_count}/3)"
    })

    # Another failure
    print("\n[STEP 3] Another failure...")
    retry_count = increment_retry_count(job_id)
    print(f"Retry count: {retry_count}")

    # Final failure - give up
    print("\n[STEP 4] Max retries exceeded, marking as failed...")
    mark_job_failed(job_id, "API timeout after 3 retry attempts")

    job = get_job(job_id)
    print(f"Final status: {job['status']}")
    print(f"Error message: {job['error_message']}")
    print(f"Retry count: {job['download_retries']}")

    return job_id

def example_job_monitoring():
    """
    Demonstrates job monitoring and status queries.
    """
    print("\n\n" + "=" * 70)
    print("Example: Job Monitoring and Status Queries")
    print("=" * 70)

    # Get all pending jobs
    print("\n[QUERY 1] Fetching pending jobs...")
    pending_jobs = get_jobs_by_status("pending", limit=5)
    print(f"Found {len(pending_jobs)} pending job(s)")
    for job in pending_jobs[:3]:  # Show first 3
        print(f"  - Job {job['id']}: {job['prompt'][:50]}...")

    # Get all failed jobs
    print("\n[QUERY 2] Fetching failed jobs...")
    failed_jobs = get_jobs_by_status("failed", limit=5)
    print(f"Found {len(failed_jobs)} failed job(s)")
    for job in failed_jobs[:3]:  # Show first 3
        print(f"  - Job {job['id']}: {job['error_message']}")

    # Get all completed jobs
    print("\n[QUERY 3] Fetching completed jobs...")
    completed_jobs = get_jobs_by_status("completed", limit=5)
    print(f"Found {len(completed_jobs)} completed job(s)")

if __name__ == "__main__":
    print("\n" + "🎬" * 35)
    print("Database Helper Functions - Workflow Examples")
    print("🎬" * 35)

    # Run example workflows
    job1 = example_video_generation_workflow()
    job2 = example_error_handling_workflow()
    example_job_monitoring()

    print("\n\n" + "=" * 70)
    print("All workflow examples completed successfully!")
    print("=" * 70)
    print(f"\nCreated example jobs: {job1}, {job2}")
    print("\nThese functions are ready for integration into the v2 API!")
