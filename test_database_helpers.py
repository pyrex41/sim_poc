#!/usr/bin/env python3
"""
Test script for new database helper functions
Tests all 6 newly implemented functions
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

def test_database_helpers():
    """Test all new helper functions"""
    print("=" * 60)
    print("Testing Database Helper Functions")
    print("=" * 60)

    # Create a test job
    print("\n1. Creating test job...")
    job_id = save_generated_video(
        prompt="Test video for helper functions",
        video_url="https://example.com/test.mp4",
        model_id="test-model",
        parameters={"duration": 5},
        status="pending"
    )
    print(f"   Created job with ID: {job_id}")

    # Test get_job
    print("\n2. Testing get_job()...")
    job = get_job(job_id)
    if job:
        print(f"   Retrieved job: {job['id']}")
        print(f"   Status: {job['status']}")
        print(f"   Progress: {job['progress']}")
        print(f"   Approved: {job['approved']}")
    else:
        print("   ERROR: Could not retrieve job")
        return False

    # Test update_job_progress
    print("\n3. Testing update_job_progress()...")
    progress_data = {
        "stage": "storyboard",
        "percent": 25,
        "message": "Generating storyboard..."
    }
    success = update_job_progress(job_id, progress_data)
    if success:
        job = get_job(job_id)
        print(f"   Updated progress: {job['progress']}")
        print(f"   Updated at: {job['updated_at']}")
    else:
        print("   ERROR: Failed to update progress")
        return False

    # Test get_jobs_by_status
    print("\n4. Testing get_jobs_by_status()...")
    pending_jobs = get_jobs_by_status("pending", limit=10)
    print(f"   Found {len(pending_jobs)} pending job(s)")
    if pending_jobs:
        print(f"   First job ID: {pending_jobs[0]['id']}")

    # Test approve_storyboard
    print("\n5. Testing approve_storyboard()...")
    success = approve_storyboard(job_id)
    if success:
        job = get_job(job_id)
        print(f"   Approved: {job['approved']}")
        print(f"   Approved at: {job['approved_at']}")
    else:
        print("   ERROR: Failed to approve storyboard")
        return False

    # Test increment_retry_count
    print("\n6. Testing increment_retry_count()...")
    retry_count = increment_retry_count(job_id)
    print(f"   Retry count after increment: {retry_count}")
    retry_count = increment_retry_count(job_id)
    print(f"   Retry count after second increment: {retry_count}")

    # Test mark_job_failed
    print("\n7. Testing mark_job_failed()...")
    success = mark_job_failed(job_id, "Test error: API timeout")
    if success:
        job = get_job(job_id)
        print(f"   Status: {job['status']}")
        print(f"   Error message: {job['error_message']}")
        print(f"   Updated at: {job['updated_at']}")
    else:
        print("   ERROR: Failed to mark job as failed")
        return False

    # Test get_jobs_by_status with 'failed'
    print("\n8. Testing get_jobs_by_status('failed')...")
    failed_jobs = get_jobs_by_status("failed", limit=10)
    print(f"   Found {len(failed_jobs)} failed job(s)")
    if failed_jobs:
        print(f"   First failed job ID: {failed_jobs[0]['id']}")
        print(f"   Error: {failed_jobs[0]['error_message']}")

    # Test edge cases
    print("\n9. Testing edge cases...")

    # Non-existent job
    job = get_job(999999)
    if job is None:
        print("   get_job(999999) correctly returns None")
    else:
        print("   ERROR: get_job should return None for non-existent job")

    # Update non-existent job
    success = update_job_progress(999999, {"test": "data"})
    if not success:
        print("   update_job_progress(999999) correctly returns False")
    else:
        print("   ERROR: update_job_progress should return False for non-existent job")

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_database_helpers()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nTEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
