# Database Helper Functions Implementation Summary

## Overview
Successfully implemented 6 new helper functions in `backend/database.py` to support the v2 Video Generation API workflow with storyboard approval and progress tracking.

## Database Schema Updates
The migration has been completed with the following columns added to `generated_videos` table:
- `progress` (TEXT) - JSON field storing progress information
- `storyboard_data` (TEXT) - JSON field storing storyboard data
- `approved` (BOOLEAN) - Approval status flag
- `approved_at` (TIMESTAMP) - Timestamp of approval
- `estimated_cost` (REAL) - Estimated generation cost
- `actual_cost` (REAL) - Actual generation cost
- `error_message` (TEXT) - Error details for failed jobs
- `updated_at` (TIMESTAMP) - Auto-updated via trigger

## Implemented Functions

### 1. update_job_progress(job_id: int, progress: dict) -> bool
**Purpose:** Update the progress JSON field for a job

**Usage:**
```python
from backend.database import update_job_progress

success = update_job_progress(
    job_id=123,
    progress={
        "stage": "storyboard",
        "percent": 25,
        "message": "Generating storyboard..."
    }
)
```

**Returns:** `True` on success, `False` on failure

**Notes:**
- The `updated_at` timestamp is automatically updated by the database trigger
- Progress data is serialized to JSON automatically

---

### 2. get_job(job_id: int) -> dict
**Purpose:** Retrieve a complete job record by ID

**Usage:**
```python
from backend.database import get_job

job = get_job(123)
if job:
    print(f"Status: {job['status']}")
    print(f"Progress: {job['progress']}")
    print(f"Approved: {job['approved']}")
```

**Returns:** Dictionary with all job fields, or `None` if not found

**Fields returned:**
- All standard fields: id, prompt, video_url, model_id, parameters, status, created_at, etc.
- New v2 fields: progress, storyboard_data, approved, approved_at, estimated_cost, actual_cost, error_message, updated_at

**Notes:**
- JSON fields (progress, storyboard_data, parameters, metadata) are automatically deserialized
- Uses safe column access to handle missing columns gracefully

---

### 3. increment_retry_count(job_id: int) -> int
**Purpose:** Increment the retry counter for a failed job

**Usage:**
```python
from backend.database import increment_retry_count

new_count = increment_retry_count(123)
print(f"Retry count is now: {new_count}")
```

**Returns:** The new retry count value (uses `download_retries` field)

**Notes:**
- Automatically increments the counter and commits the change
- Returns 0 on error

---

### 4. mark_job_failed(job_id: int, error_message: str) -> bool
**Purpose:** Mark a job as failed with an error message

**Usage:**
```python
from backend.database import mark_job_failed

success = mark_job_failed(
    job_id=123,
    error_message="API timeout after 3 retries"
)
```

**Returns:** `True` on success, `False` on failure

**Side effects:**
- Sets `status = 'failed'`
- Sets `error_message` field
- Updates `updated_at` timestamp via trigger

---

### 5. get_jobs_by_status(status: str, limit: int = 50) -> list[dict]
**Purpose:** Get jobs with a specific status, ordered by most recently updated

**Usage:**
```python
from backend.database import get_jobs_by_status

# Get pending jobs
pending = get_jobs_by_status("pending", limit=10)

# Get failed jobs
failed = get_jobs_by_status("failed", limit=20)

# Process results
for job in pending:
    print(f"Job {job['id']}: {job['prompt']}")
```

**Parameters:**
- `status` - Status to filter by ('pending', 'processing', 'completed', 'failed', etc.)
- `limit` - Maximum records to return (default: 50)

**Returns:** List of job dictionaries (same format as `get_job()`)

**Notes:**
- Results ordered by `updated_at DESC` (most recent first)
- Returns empty list on error
- Each job dictionary contains all fields including v2 additions

---

### 6. approve_storyboard(job_id: int) -> bool
**Purpose:** Mark a job's storyboard as approved

**Usage:**
```python
from backend.database import approve_storyboard

success = approve_storyboard(123)
if success:
    print("Storyboard approved!")
```

**Returns:** `True` on success, `False` on failure

**Side effects:**
- Sets `approved = 1` (True)
- Sets `approved_at = CURRENT_TIMESTAMP`
- Updates `updated_at` via trigger

---

## Error Handling

All functions include proper error handling:
- Try/except blocks with informative error messages
- Safe column access for backward compatibility
- Returns appropriate default values on error (False, None, 0, [])
- Prints error messages to console for debugging

## Testing

A comprehensive test suite is available in `test_database_helpers.py`:

```bash
# Run tests (ensure DATA environment variable points to correct DB)
export DATA=backend/DATA
python test_database_helpers.py
```

Test coverage includes:
- All 6 functions with typical use cases
- Edge cases (non-existent jobs, etc.)
- JSON serialization/deserialization
- Timestamp updates
- Error conditions

## Code Quality

- Follows existing code patterns in `database.py`
- Uses the `get_db()` context manager for connections
- Consistent with existing function signatures
- Proper type hints in docstrings
- JSON fields automatically serialized/deserialized
- Safe handling of NULL/missing columns

## Integration Notes

### Environment Variable
The database location is determined by the `DATA` environment variable:
```python
DATA_DIR = Path(os.getenv("DATA", "./DATA"))
DB_PATH = DATA_DIR / "scenes.db"
```

For production use, ensure `DATA` is set correctly, e.g.:
```bash
export DATA=backend/DATA
```

### Database Trigger
The `update_videos_timestamp` trigger automatically updates `updated_at` on any UPDATE operation, so you don't need to manually set it.

### Backward Compatibility
The safe column access pattern ensures the functions work even if:
- The migration hasn't been run yet
- Some columns are NULL
- Old records don't have v2 fields populated

## Files Modified

- `/Users/reuben/gauntlet/video/sim_poc_worktrees/mvp/backend/database.py` - Added 6 new helper functions (lines 1200-1405)

## Files Created

- `/Users/reuben/gauntlet/video/sim_poc_worktrees/mvp/test_database_helpers.py` - Comprehensive test suite
- `/Users/reuben/gauntlet/video/sim_poc_worktrees/mvp/DATABASE_HELPERS_SUMMARY.md` - This documentation

## Next Steps

These helper functions are now ready to be integrated into the v2 API endpoints for:
1. Job creation and initialization
2. Progress tracking during video generation
3. Storyboard approval workflow
4. Error handling and retry logic
5. Job status monitoring and querying
