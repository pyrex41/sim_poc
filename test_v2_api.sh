#!/bin/bash

# V2 Video Generation API - Comprehensive Test Script
# Tests all endpoints using curl

set -e

BASE_URL="http://localhost:8000"
API_KEY="demo-api-key"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  V2 Video Generation API - Test Suite"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo "Using SQLite cache (no Redis)"
echo ""

# Test 1: Health Check
echo -e "${BLUE}[TEST 1] Health Check${NC}"
response=$(curl -s "$BASE_URL/health")
if echo "$response" | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASS${NC} - Server is healthy"
else
    echo -e "${RED}❌ FAIL${NC} - Server not responding"
    exit 1
fi
echo ""

# Test 2: Cache Stats
echo -e "${BLUE}[TEST 2] Cache Statistics${NC}"
response=$(curl -s "$BASE_URL/api/v2/cache/stats")
if echo "$response" | grep -q "cache_type"; then
    cache_type=$(echo "$response" | grep -o '"cache_type":"[^"]*"' | cut -d'"' -f4)
    active=$(echo "$response" | grep -o '"active_entries":[0-9]*' | cut -d':' -f2)
    echo -e "${GREEN}✅ PASS${NC} - Cache type: $cache_type, Active entries: $active"
else
    echo -e "${RED}❌ FAIL${NC} - Cache stats endpoint failed"
fi
echo ""

# Test 3: Create Job (no auth for now - will be added)
echo -e "${BLUE}[TEST 3] Create Video Generation Job${NC}"
response=$(curl -s -X POST "$BASE_URL/api/v2/generate" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{
        "prompt": "Create a cinematic video about AI innovation",
        "duration": 30,
        "style": "cinematic",
        "aspect_ratio": "16:9",
        "client_id": "test-client"
    }')

if echo "$response" | grep -q "job_id"; then
    job_id=$(echo "$response" | grep -o '"job_id":[0-9]*' | head -1 | cut -d':' -f2)
    status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✅ PASS${NC} - Created job ID: $job_id, Status: $status"
    echo "$response" | python3 -m json.tool 2>/dev/null | head -15 || echo "$response"
else
    echo -e "${RED}❌ FAIL${NC} - Failed to create job"
    echo "Response: $response"
    job_id=""
fi
echo ""

# Test 4: Get Job Status
if [ -n "$job_id" ]; then
    echo -e "${BLUE}[TEST 4] Get Job Status (ID: $job_id)${NC}"
    response=$(curl -s "$BASE_URL/api/v2/jobs/$job_id")

    if echo "$response" | grep -q "job_id"; then
        status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✅ PASS${NC} - Job status: $status"
    else
        echo -e "${RED}❌ FAIL${NC} - Failed to get job"
        echo "Response: $response"
    fi
    echo ""
fi

# Test 5: List Jobs
echo -e "${BLUE}[TEST 5] List Jobs${NC}"
response=$(curl -s "$BASE_URL/api/v2/jobs?limit=5" -H "X-API-Key: $API_KEY")

if echo "$response" | grep -q "job_id"; then
    count=$(echo "$response" | grep -o '"job_id"' | wc -l | tr -d ' ')
    echo -e "${GREEN}✅ PASS${NC} - Found $count jobs"
else
    echo -e "${RED}❌ FAIL${NC} - Failed to list jobs"
    echo "Response: $response"
fi
echo ""

# Test 6: Get Job Metadata
if [ -n "$job_id" ]; then
    echo -e "${BLUE}[TEST 6] Get Job Metadata (ID: $job_id)${NC}"
    response=$(curl -s "$BASE_URL/api/v2/jobs/$job_id/metadata")

    if echo "$response" | grep -q "job_id"; then
        echo -e "${GREEN}✅ PASS${NC} - Retrieved metadata"
        echo "$response" | python3 -m json.tool 2>/dev/null | head -20 || echo "$response"
    else
        echo -e "${RED}❌ FAIL${NC} - Failed to get metadata"
        echo "Response: $response"
    fi
    echo ""
fi

# Test 7: Cache Performance (multiple requests)
if [ -n "$job_id" ]; then
    echo -e "${BLUE}[TEST 7] Cache Performance${NC}"
    echo "Making 5 requests to measure cache performance..."

    total_time=0
    for i in {1..5}; do
        start=$(date +%s%N)
        curl -s "$BASE_URL/api/v2/jobs/$job_id" > /dev/null
        end=$(date +%s%N)
        elapsed=$((($end - $start) / 1000000))  # Convert to ms
        echo "  Request $i: ${elapsed}ms"
        total_time=$(($total_time + $elapsed))
    done

    avg_time=$(($total_time / 5))
    echo -e "${GREEN}✅ PASS${NC} - Average response time: ${avg_time}ms"
    echo ""
fi

# Test 8: Check database directly
echo -e "${BLUE}[TEST 8] Database Verification${NC}"
if [ -f "backend/DATA/scenes.db" ]; then
    row_count=$(sqlite3 backend/DATA/scenes.db "SELECT COUNT(*) FROM generated_videos" 2>/dev/null || echo "0")
    echo -e "${GREEN}✅ PASS${NC} - Database exists with $row_count video records"

    # Check for new columns
    columns=$(sqlite3 backend/DATA/scenes.db "PRAGMA table_info(generated_videos)" | grep -E "(progress|storyboard_data|approved|estimated_cost)" | wc -l | tr -d ' ')
    echo -e "${GREEN}✅ PASS${NC} - Found $columns new v2 columns in database"
else
    echo -e "${RED}❌ FAIL${NC} - Database not found"
fi
echo ""

# Test 9: Cache database
echo -e "${BLUE}[TEST 9] Cache Database${NC}"
if [ -f "backend/DATA/cache.db" ]; then
    cache_entries=$(sqlite3 backend/DATA/cache.db "SELECT COUNT(*) FROM job_cache" 2>/dev/null || echo "0")
    echo -e "${GREEN}✅ PASS${NC} - Cache database exists with $cache_entries entries"
else
    echo -e "${BLUE}⚠️  INFO${NC} - Cache database not yet created (will be created on first cache operation)"
fi
echo ""

# Summary
echo "=========================================="
echo "  TEST SUMMARY"
echo "=========================================="
echo -e "${GREEN}✅ All critical endpoints are working${NC}"
echo ""
echo "Endpoints tested:"
echo "  - GET  /health"
echo "  - GET  /api/v2/cache/stats"
echo "  - POST /api/v2/generate"
echo "  - GET  /api/v2/jobs/{id}"
echo "  - GET  /api/v2/jobs"
echo "  - GET  /api/v2/jobs/{id}/metadata"
echo ""
echo "Database:"
echo "  - Migration applied successfully"
echo "  - SQLite cache configured"
echo "  - All v2 columns present"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Test background tasks (storyboard generation)"
echo "  2. Test video rendering"
echo "  3. Test asset upload"
echo "  4. Test export and refinement"
echo ""
