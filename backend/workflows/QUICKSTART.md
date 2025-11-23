# Luigi Pipeline Quick Start Guide

## Prerequisites

- Python 3.8+
- Existing V3 pipeline backend running
- Access to the project database

## Installation

### 1. Install Luigi

```bash
pip install luigi
```

### 2. Run Database Migration

```bash
# From backend directory
python -m migrations.add_luigi_state_table
```

Or use the migration runner:

```bash
python backend/migrations/add_luigi_state_table.py
```

### 3. Start Luigi Central Scheduler

The Luigi scheduler provides the web UI and coordinates task execution across workers.

```bash
# Start in background
luigid --background --logdir logs/luigi

# Or in foreground for debugging
luigid
```

The scheduler will be available at: `http://localhost:8082`

### 4. Configure Luigi (Optional)

Copy the Luigi configuration file:

```bash
cp backend/workflows/luigi.cfg ~/.luigi/luigi.cfg
# Or set LUIGI_CONFIG_PATH environment variable
export LUIGI_CONFIG_PATH=/path/to/backend/workflows/luigi.cfg
```

## Running Workflows

### Option 1: From Command Line

```bash
# Run a complete pipeline
python -m luigi \
    --module backend.workflows.campaign_pipeline CampaignPipelineWorkflow \
    --job-id 123 \
    --campaign-id campaign-abc-123 \
    --workers 10

# Run with specific parameters
python -m luigi \
    --module backend.workflows.campaign_pipeline CampaignPipelineWorkflow \
    --job-id 124 \
    --campaign-id campaign-abc-123 \
    --clip-duration 8.0 \
    --num-pairs 15 \
    --workers 10
```

### Option 2: From Python Code

```python
from backend.workflows import run_pipeline_async

# In an async function
result = await run_pipeline_async(
    job_id=123,
    campaign_id="campaign-abc-123",
    clip_duration=6.0,
    num_pairs=10,
    workers=10,
    use_local_scheduler=False
)

print(result)
# {'success': True, 'job_id': 123, 'message': 'Pipeline completed successfully'}
```

### Option 3: Via FastAPI Endpoint

```bash
# Create a new job with Luigi
curl -X POST http://localhost:8000/api/v3/luigi/jobs/from-image-pairs \
  -H "Content-Type: application/json" \
  -d '{
    "campaignId": "campaign-abc-123",
    "clipDuration": 6.0,
    "numPairs": 10
  }'

# Response:
# {
#   "jobId": 123,
#   "status": "pipeline_started",
#   "message": "Luigi workflow initiated...",
#   "luigiDashboard": "http://localhost:8082/..."
# }
```

## Monitoring Progress

### 1. Luigi Web UI

Open `http://localhost:8082` in your browser to see:

- Real-time task dependency graph
- Task statuses (pending, running, completed, failed)
- Task execution timeline
- Worker activity
- Error messages and logs

### 2. API Endpoint

```bash
# Get job status
curl http://localhost:8000/api/v3/luigi/jobs/123

# Response:
# {
#   "job_id": 123,
#   "status": "running",
#   "progress": 45.5,
#   "tasks": [
#     {
#       "name": "AssetCollectionTask",
#       "status": "completed",
#       "created_at": "2025-01-22T10:00:00Z",
#       "completed_at": "2025-01-22T10:01:00Z"
#     },
#     ...
#   ],
#   "completed_tasks": 5,
#   "total_tasks": 11
# }
```

### 3. Database Query

```sql
SELECT task_name, status, created_at, completed_at
FROM luigi_task_state
WHERE job_id = 123
ORDER BY created_at ASC;
```

## Error Handling & Recovery

### View Failed Tasks

```bash
# In Luigi UI, failed tasks are shown in red
# Click on a task to see error details
```

### Retry Failed Pipeline

```bash
# Via API
curl -X POST http://localhost:8000/api/v3/luigi/jobs/123/retry

# Via command line (after fixing the issue)
python -m luigi \
    --module backend.workflows.campaign_pipeline CampaignPipelineWorkflow \
    --job-id 123 \
    --campaign-id campaign-abc-123
```

Luigi will automatically skip completed tasks and only re-run failed ones.

### Cancel Running Pipeline

```bash
curl -X POST http://localhost:8000/api/v3/luigi/jobs/123/cancel
```

## Integration with Existing API

### Update FastAPI Main Router

In `backend/main.py` or `backend/api_routes.py`:

```python
from backend.workflows.fastapi_integration import luigi_router

# Add Luigi routes
app.include_router(luigi_router)
```

### Feature Flag for Gradual Migration

```python
from backend.config import get_settings

settings = get_settings()

@router.post("/api/v3/jobs/from-image-pairs")
async def create_job_from_image_pairs(request: Dict[str, Any], ...):
    # Check feature flag
    if settings.USE_LUIGI_PIPELINE:
        # Route to Luigi workflow
        return await create_job_with_luigi(request, background_tasks)
    else:
        # Use existing orchestrator
        return await create_job_from_image_pairs_original(request, ...)
```

## Architecture Comparison

### Current AsyncIO Orchestrator

```python
# Manual dependency management
async def process_image_pairs_to_videos(job_id, image_pairs):
    # Step 1: Create sub-jobs
    sub_job_ids = []
    for pair in image_pairs:
        sub_job_id = create_sub_job(...)
        sub_job_ids.append(sub_job_id)

    # Step 2: Launch all in parallel
    results = await _launch_all_sub_jobs(job_id, sub_job_ids)

    # Step 3: Combine clips
    clip_paths = [r["clip_path"] for r in results if r["success"]]
    combined_path = await _combine_clips(job_id, clip_paths)

    # Step 4: Generate audio
    audio_path = await _add_music_to_video(job_id, combined_path)

    # Step 5: Store final video
    video_url = await _store_final_video(job_id, audio_path)

    return {"video_url": video_url}
```

**Issues:**
- Manual orchestration logic
- No checkpointing (can't resume from failures)
- No visualization
- Hard to add new stages

### Luigi Workflow

```python
# Automatic dependency management
class CampaignPipelineWorkflow(luigi.WrapperTask):
    job_id = luigi.IntParameter()
    campaign_id = luigi.Parameter()

    def requires(self):
        return VideoStorageTask(
            job_id=self.job_id,
            campaign_id=self.campaign_id
        )

# VideoStorageTask automatically requires AudioMergingTask
# AudioMergingTask requires VideoCombinationTask and AudioGenerationTask
# VideoCombinationTask requires ParallelVideoGenerationTask
# ... and so on

# Luigi resolves all dependencies automatically!
```

**Benefits:**
- Declarative dependency management
- Automatic checkpointing and resume
- Built-in visualization
- Easy to extend with new tasks

## Performance Tuning

### Adjust Worker Count

```python
# More workers = more parallelism
await run_pipeline_async(
    job_id=123,
    campaign_id="...",
    workers=20  # Default: 10
)
```

### Resource Limits

In `luigi.cfg`:

```ini
[resources]
# Limit concurrent Replicate API calls
replicate_api=10

# Limit concurrent video downloads
video_download=5
```

Then in tasks:

```python
class VideoGenerationSubTask(AsyncCampaignTask):
    resources = {'replicate_api': 1, 'video_download': 1}
```

### Task Priorities

```python
class AssetCollectionTask(AsyncCampaignTask):
    priority = 100  # Higher priority runs first

class VideoGenerationSubTask(AsyncCampaignTask):
    priority = 50   # Lower priority
```

## Troubleshooting

### Luigi Scheduler Not Running

```bash
# Check if luigid is running
ps aux | grep luigid

# Restart if needed
pkill luigid
luigid --background --logdir logs/luigi
```

### Tasks Stuck in "PENDING"

This usually means dependencies haven't completed yet. Check the dependency graph in the UI.

### Database Connection Errors

Ensure the database path is correct:

```python
# In backend/database.py
DATABASE_PATH = Path(__file__).parent / "database.db"
```

### Import Errors

```bash
# Make sure backend is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/project"

# Or install in development mode
pip install -e .
```

## Next Steps

1. **Test with a Small Campaign**: Start with 2-3 image pairs
2. **Monitor in Luigi UI**: Watch the dependency graph as tasks execute
3. **Compare Performance**: Run same campaign with both orchestrators
4. **Gradually Increase Load**: Scale up to production workloads
5. **Add Custom Tasks**: Extend the pipeline with new functionality

## Additional Resources

- [Luigi Documentation](https://luigi.readthedocs.io/)
- [Luigi Best Practices](https://luigi.readthedocs.io/en/stable/design_and_limitations.html)
- [Task Dependencies](https://luigi.readthedocs.io/en/stable/tasks.html)
- [Central Scheduler](https://luigi.readthedocs.io/en/stable/central_scheduler.html)
