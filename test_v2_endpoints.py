#!/usr/bin/env python3
"""
Comprehensive test script for v2 Video Generation API endpoints
Tests all functionality without requiring real Replicate API calls
"""

import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key"  # You'll need to create this via setup_auth.py
HEADERS = {"X-API-Key": API_KEY}

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_result(test_name, success, details=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   {details}")

def test_health_check():
    """Test basic server connectivity"""
    print_section("1. Health Check")

    try:
        response = requests.get(f"{BASE_URL}/health")
        success = response.status_code == 200
        print_result("Server is running", success, f"Status: {response.status_code}")
        return success
    except Exception as e:
        print_result("Server is running", False, f"Error: {e}")
        return False

def test_cache_stats():
    """Test cache statistics endpoint"""
    print_section("2. Cache Statistics")

    try:
        response = requests.get(f"{BASE_URL}/api/v2/cache/stats")
        success = response.status_code == 200

        if success:
            data = response.json()
            details = f"Type: {data.get('cache_type')}, Active: {data.get('active_entries')}, TTL: {data.get('ttl_seconds')}s"
            print_result("Cache stats endpoint", success, details)
        else:
            print_result("Cache stats endpoint", False, f"Status: {response.status_code}")

        return success
    except Exception as e:
        print_result("Cache stats endpoint", False, f"Error: {e}")
        return False

def test_create_job():
    """Test POST /api/v2/generate - Create new video job"""
    print_section("3. Create Video Generation Job")

    payload = {
        "prompt": "Create a cinematic video about AI innovation in 2025, with futuristic visuals",
        "duration": 30,
        "style": "cinematic",
        "aspect_ratio": "16:9",
        "client_id": "test-client-123"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/generate",
            json=payload,
            headers=HEADERS
        )

        success = response.status_code == 200

        if success:
            data = response.json()
            job_id = data.get("job_id")
            status = data.get("status")
            estimated_cost = data.get("estimated_cost", 0)

            details = f"Job ID: {job_id}, Status: {status}, Est. Cost: ${estimated_cost:.2f}"
            print_result("Create job", success, details)

            return job_id
        else:
            print_result("Create job", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
            return None

    except Exception as e:
        print_result("Create job", False, f"Error: {e}")
        return None

def test_get_job(job_id):
    """Test GET /api/v2/jobs/{job_id} - Get job status"""
    print_section(f"4. Get Job Status (ID: {job_id})")

    try:
        response = requests.get(f"{BASE_URL}/api/v2/jobs/{job_id}")
        success = response.status_code == 200

        if success:
            data = response.json()
            status = data.get("status")
            progress = data.get("progress", {})
            current_stage = progress.get("current_stage")

            details = f"Status: {status}, Stage: {current_stage}"
            print_result("Get job status", success, details)
        else:
            print_result("Get job status", False, f"Status: {response.status_code}")

        return success
    except Exception as e:
        print_result("Get job status", False, f"Error: {e}")
        return False

def test_list_jobs():
    """Test GET /api/v2/jobs - List all jobs for user"""
    print_section("5. List Jobs")

    try:
        response = requests.get(
            f"{BASE_URL}/api/v2/jobs?limit=10",
            headers=HEADERS
        )

        success = response.status_code == 200

        if success:
            data = response.json()
            count = len(data)
            details = f"Found {count} jobs"
            print_result("List jobs", success, details)

            # Print first few jobs
            for i, job in enumerate(data[:3]):
                print(f"   Job {i+1}: ID={job.get('job_id')}, Status={job.get('status')}")
        else:
            print_result("List jobs", False, f"Status: {response.status_code}")

        return success
    except Exception as e:
        print_result("List jobs", False, f"Error: {e}")
        return False

def test_upload_asset():
    """Test POST /api/v2/upload-asset - Upload test image"""
    print_section("6. Upload Asset")

    # Create a simple test image file
    test_image_path = Path("test_image.png")

    try:
        # Create a minimal PNG file (1x1 pixel)
        png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

        with open(test_image_path, 'wb') as f:
            f.write(png_data)

        # Upload the file
        with open(test_image_path, 'rb') as f:
            files = {'file': ('test_image.png', f, 'image/png')}
            response = requests.post(
                f"{BASE_URL}/api/v2/upload-asset",
                files=files,
                headers=HEADERS
            )

        success = response.status_code == 200

        if success:
            data = response.json()
            asset_url = data.get("url")
            asset_id = data.get("asset_id")
            size = data.get("size_bytes", 0)

            details = f"Asset ID: {asset_id}, Size: {size} bytes"
            print_result("Upload asset", success, details)

            # Clean up test file
            test_image_path.unlink()

            return asset_id
        else:
            print_result("Upload asset", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
            test_image_path.unlink(missing_ok=True)
            return None

    except Exception as e:
        print_result("Upload asset", False, f"Error: {e}")
        test_image_path.unlink(missing_ok=True)
        return None

def test_list_assets():
    """Test GET /api/v2/assets - List user's assets"""
    print_section("7. List Assets")

    try:
        response = requests.get(
            f"{BASE_URL}/api/v2/assets",
            headers=HEADERS
        )

        success = response.status_code == 200

        if success:
            data = response.json()
            count = len(data)
            details = f"Found {count} assets"
            print_result("List assets", success, details)
        else:
            print_result("List assets", False, f"Status: {response.status_code}")

        return success
    except Exception as e:
        print_result("List assets", False, f"Error: {e}")
        return False

def test_get_job_metadata(job_id):
    """Test GET /api/v2/jobs/{job_id}/metadata - Get comprehensive metadata"""
    print_section(f"8. Get Job Metadata (ID: {job_id})")

    try:
        response = requests.get(f"{BASE_URL}/api/v2/jobs/{job_id}/metadata")
        success = response.status_code == 200

        if success:
            data = response.json()
            details = f"Scenes: {data.get('scenes_total', 0)}, Downloads: {data.get('download_count', 0)}"
            print_result("Get job metadata", success, details)
        else:
            print_result("Get job metadata", False, f"Status: {response.status_code}")

        return success
    except Exception as e:
        print_result("Get job metadata", False, f"Error: {e}")
        return False

def test_cache_performance(job_id):
    """Test cache performance with multiple requests"""
    print_section(f"9. Cache Performance Test (ID: {job_id})")

    times = []

    try:
        # Make 5 requests and measure time
        for i in range(5):
            start = time.time()
            response = requests.get(f"{BASE_URL}/api/v2/jobs/{job_id}")
            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)

            if response.status_code == 200:
                print(f"   Request {i+1}: {elapsed:.2f}ms")
            else:
                print(f"   Request {i+1}: Failed (Status: {response.status_code})")

        # Calculate stats
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"\n   Average: {avg_time:.2f}ms, Min: {min_time:.2f}ms, Max: {max_time:.2f}ms")

        # Check cache stats
        response = requests.get(f"{BASE_URL}/api/v2/cache/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   Cache: {stats.get('active_entries')} active entries")

        success = avg_time < 50  # Should be fast with caching
        print_result("Cache performance", success, f"Avg response: {avg_time:.2f}ms")

        return success
    except Exception as e:
        print_result("Cache performance", False, f"Error: {e}")
        return False

def test_database_functions():
    """Test database helper functions directly"""
    print_section("10. Database Helper Functions")

    try:
        from backend.database import (
            get_job, update_job_progress, mark_job_failed,
            increment_retry_count, get_jobs_by_status,
            approve_storyboard
        )

        # Test get_job
        job = get_job(1)
        if job:
            print_result("get_job()", True, f"Retrieved job ID: {job.get('id')}")
        else:
            print_result("get_job()", False, "No job found with ID 1")

        # Test get_jobs_by_status
        jobs = get_jobs_by_status("pending", limit=5)
        print_result("get_jobs_by_status()", True, f"Found {len(jobs)} pending jobs")

        # Test update_job_progress
        test_progress = {"current_stage": "test", "scenes_total": 5}
        if job:
            success = update_job_progress(job['id'], test_progress)
            print_result("update_job_progress()", success, "Updated progress")

        return True
    except Exception as e:
        print_result("Database functions", False, f"Error: {e}")
        return False

def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*60)
    print("  V2 Video Generation API - Comprehensive Test Suite")
    print("="*60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Using SQLite cache (no Redis required)")
    print()

    results = []

    # Test 1: Health check
    results.append(("Health Check", test_health_check()))

    # Test 2: Cache stats
    results.append(("Cache Stats", test_cache_stats()))

    # Test 3: Create job
    job_id = test_create_job()
    results.append(("Create Job", job_id is not None))

    if job_id:
        # Test 4: Get job
        results.append(("Get Job", test_get_job(job_id)))

        # Test 5: List jobs
        results.append(("List Jobs", test_list_jobs()))

        # Test 8: Get metadata
        results.append(("Get Metadata", test_get_job_metadata(job_id)))

        # Test 9: Cache performance
        results.append(("Cache Performance", test_cache_performance(job_id)))

    # Test 6: Upload asset
    asset_id = test_upload_asset()
    results.append(("Upload Asset", asset_id is not None))

    if asset_id:
        # Test 7: List assets
        results.append(("List Assets", test_list_assets()))

    # Test 10: Database functions
    results.append(("Database Functions", test_database_functions()))

    # Print summary
    print_section("TEST SUMMARY")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"{'='*60}\n")

    return passed == total

if __name__ == "__main__":
    try:
        all_passed = run_all_tests()
        exit(0 if all_passed else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        exit(1)
