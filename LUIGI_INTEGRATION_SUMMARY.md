# Luigi Workflow Integration - Implementation Summary

## Overview

I've successfully adapted your V3 campaign pipeline to use Spotify's Luigi workflow orchestration library. This implementation provides dependency management, checkpointing, failure recovery, and workflow visualization.

## What Was Created

### 1. Core Workflow Infrastructure (`backend/workflows/`)

- **`__init__.py`** - Package initialization with public API
- **`base.py`** - Base classes for all Luigi tasks
  - `CampaignStateTarget` - Custom target for database state tracking
  - `CampaignPipelineTask` - Base class for all pipeline tasks
  - `AsyncCampaignTask` - Base class for async operations

- **`tasks.py`** - Individual pipeline tasks
  - `AssetCollectionTask` - Fetch campaign assets
  - `ImagePairSelectionTask` - Use xAI Grok to select pairs
  - `SubJobCreationTask` - Create sub-jobs in database
  - `VideoGenerationSubTask` - Generate individual videos
  - `ParallelVideoGenerationTask` - Coordinate parallel generation
  - `AudioGenerationTask` - Generate background music
  - `VideoCombinationTask` - Combine video clips
  - `AudioMergingTask` - Merge audio with video
  - `VideoStorageTask` - Store final video in database

- **`campaign_pipeline.py`** - Main workflow definitions
  - `CampaignPipelineWorkflow` - Complete end-to-end workflow
  - `CampaignPipelineWorkflowWithParams` - Configurable variant
  - `PropertyVideoPipelineWorkflow` - Property video specialization

- **`runner.py`** - FastAPI integration utilities
  - `run_pipeline_async()` - Run workflow from FastAPI
  - `get_pipeline_status()` - Query pipeline progress
  - `cancel_pipeline()` - Cancel running workflows
  - `retry_failed_pipeline()` - Retry from last checkpoint

- **`fastapi_integration.py`** - Example API endpoints
  - POST `/api/v3/luigi/jobs/from-image-pairs` - Create job
  - GET `/api/v3/luigi/jobs/{job_id}` - Get status
  - GET `/api/v3/luigi/jobs` - List all jobs
  - POST `/api/v3/luigi/jobs/{job_id}/cancel` - Cancel job
  - POST `/api/v3/luigi/jobs/{job_id}/retry` - Retry job

### 2. Configuration & Setup

- **`luigi.cfg`** - Luigi configuration with:
  - Scheduler settings (port 8082)
  - Worker configuration
  - Task history tracking
  - Resource management
  - Retry policies

### 3. Database Migration

- **`migrations/add_luigi_state_table.py`** - Creates:
  - `luigi_task_state` table for tracking task states
  - Indexes for performance
  - Foreign key to `generated_videos` table

### 4. Documentation

- **`workflows/README.md`** - Comprehensive architecture guide
  - Task structure and dependencies
  - Integration with FastAPI
  - Monitoring and visualization
  - Error handling and retry
  - Performance considerations

- **`workflows/QUICKSTART.md`** - Step-by-step getting started guide
  - Installation instructions
  - Running workflows (CLI, Python, API)
  - Monitoring progress
  - Error recovery
  - Troubleshooting

- **`workflows/requirements.txt`** - Luigi dependencies

## How It Works

### Task Dependencies

Luigi automatically resolves dependencies:

```
CampaignPipelineWorkflow
    └─ VideoStorageTask
        └─ AudioMergingTask
            ├─ VideoCombinationTask
            │   └─ ParallelVideoGenerationTask
            │       ├─ SubJobCreationTask
            │       │   └─ ImagePairSelectionTask
            │       │       └─ AssetCollectionTask
            │       └─ VideoGenerationSubTask (x N)
            └─ AudioGenerationTask
                └─ ParallelVideoGenerationTask
                    └─ ...
```

Each task declares its dependencies in `requires()`, and Luigi handles the rest.

### State Management

Tasks use `CampaignStateTarget` to track completion:

```python
class AssetCollectionTask(AsyncCampaignTask):
    def output(self):
        return CampaignStateTarget(self.job_id, "AssetCollectionTask")

    async def async_run(self):
        # Fetch assets...
        return {"asset_count": len(assets)}
```

When a task completes, it marks its target as complete in the database. Luigi checks this before running to enable resume from failures.

### Parallel Execution

Sub-tasks run in parallel automatically:

```python
class ParallelVideoGenerationTask(CampaignPipelineTask):
    def requires(self):
        # Returns list of VideoGenerationSubTask instances
        return [
            VideoGenerationSubTask(..., sub_job_id=id)
            for id in sub_job_ids
        ]
```

Luigi's worker pool executes these concurrently up to the worker limit.

## Integration with Existing Code

### Minimal Changes Required

The Luigi implementation **wraps** your existing async functions - it doesn't replace them:

```python
# Your existing code in sub_job_orchestrator.py stays the same!
async def _process_single_sub_job(job_id, sub_job_id, clip_duration):
    # ... existing implementation ...

# Luigi task just calls it
class VideoGenerationSubTask(AsyncCampaignTask):
    async def async_run(self):
        # Reuse existing logic
        result = await _process_single_sub_job(...)
        return result
```

### Feature Flag Pattern

You can run both systems side-by-side:

```python
@router.post("/api/v3/jobs/from-image-pairs")
async def create_job_from_image_pairs(request, background_tasks):
    if settings.USE_LUIGI_PIPELINE:
        return await create_job_with_luigi(request, background_tasks)
    else:
        return await create_job_original(request, background_tasks)
```

## Getting Started

### 1. Install Luigi

```bash
pip install luigi
```

### 2. Run Migration

```bash
python backend/migrations/add_luigi_state_table.py
```

### 3. Start Luigi Scheduler

```bash
luigid --background --logdir logs/luigi
```

Access the web UI at http://localhost:8082

### 4. Run a Test Workflow

```bash
python -m luigi \
    --module backend.workflows.campaign_pipeline CampaignPipelineWorkflow \
    --job-id 1 \
    --campaign-id test-campaign \
    --workers 10
```

### 5. Monitor in Web UI

Open http://localhost:8082 to see:
- Task dependency graph
- Real-time task statuses
- Execution timeline
- Error messages

## Key Benefits

### 1. Dependency Management
- **Before**: Manual orchestration with hardcoded sequence
- **After**: Declarative dependencies, Luigi resolves automatically

### 2. Checkpointing
- **Before**: If pipeline fails, start from scratch
- **After**: Resume from last successful task

### 3. Visualization
- **Before**: No visibility into pipeline progress
- **After**: Real-time web UI with dependency graph

### 4. Retry Logic
- **Before**: Manual retry code for each step
- **After**: Built-in retry with configurable policies

### 5. Parallel Execution
- **Before**: asyncio.gather with manual coordination
- **After**: Luigi worker pool handles concurrency

### 6. Extensibility
- **Before**: Hard to add new pipeline stages
- **After**: Create new task class, declare dependencies, done!

## Performance Comparison

| Metric | Current (AsyncIO) | Luigi |
|--------|------------------|-------|
| Setup Complexity | Medium | Low |
| Dependency Management | Manual | Automatic |
| Failure Recovery | Hard | Easy |
| Monitoring | Custom code | Web UI |
| Adding New Stages | Edit orchestrator | Add task class |
| Parallel Execution | Manual gather | Worker pool |
| State Persistence | Custom | Built-in |

## Migration Strategy

### Phase 1: Parallel Testing (Week 1-2)
- Deploy Luigi alongside existing orchestrator
- Add feature flag to route subset of traffic
- Compare performance and reliability

### Phase 2: Gradual Rollout (Week 3-4)
- Increase Luigi traffic to 25% → 50% → 75%
- Monitor error rates and performance
- Fix any integration issues

### Phase 3: Full Cutover (Week 5)
- Route 100% to Luigi
- Keep existing code as fallback
- Remove old orchestrator after stability period

## Example Usage

### From Python Code

```python
from backend.workflows import run_pipeline_async

# Run workflow
result = await run_pipeline_async(
    job_id=123,
    campaign_id="camp-abc",
    clip_duration=6.0,
    num_pairs=10,
    workers=10
)

print(result)
# {'success': True, 'job_id': 123, 'message': 'Pipeline completed'}
```

### From FastAPI Endpoint

```python
from backend.workflows.fastapi_integration import luigi_router

# Add to your FastAPI app
app.include_router(luigi_router)

# Then clients can call:
# POST /api/v3/luigi/jobs/from-image-pairs
# GET /api/v3/luigi/jobs/{job_id}
# POST /api/v3/luigi/jobs/{job_id}/retry
```

### From Command Line

```bash
# Run complete pipeline
python -m luigi \
    --module backend.workflows.campaign_pipeline CampaignPipelineWorkflow \
    --job-id 123 \
    --campaign-id campaign-abc
```

## Next Steps

1. **Review the Code**: Check `backend/workflows/` for implementation details
2. **Run the Migration**: Execute `add_luigi_state_table.py`
3. **Start the Scheduler**: `luigid --background`
4. **Test with a Small Job**: Use a campaign with 2-3 images
5. **Monitor in Web UI**: Watch tasks execute at http://localhost:8082
6. **Compare Results**: Run same campaign with both orchestrators
7. **Plan Rollout**: Decide on gradual migration timeline

## Questions & Support

- **Luigi Docs**: https://luigi.readthedocs.io/
- **Quickstart Guide**: `backend/workflows/QUICKSTART.md`
- **Architecture Guide**: `backend/workflows/README.md`
- **Task Examples**: `backend/workflows/tasks.py`

## Files Created

```
backend/
├── workflows/
│   ├── __init__.py                 # Package exports
│   ├── base.py                     # Base task classes
│   ├── tasks.py                    # Individual pipeline tasks
│   ├── campaign_pipeline.py        # Main workflows
│   ├── runner.py                   # FastAPI integration
│   ├── fastapi_integration.py      # Example API endpoints
│   ├── luigi.cfg                   # Luigi configuration
│   ├── requirements.txt            # Dependencies
│   ├── README.md                   # Architecture guide
│   └── QUICKSTART.md               # Getting started guide
└── migrations/
    └── add_luigi_state_table.py    # Database migration
```

---

**Summary**: I've created a complete Luigi integration for your V3 pipeline that provides automatic dependency management, checkpointing, failure recovery, and workflow visualization while preserving your existing code. The implementation is production-ready and can be deployed alongside your current orchestrator for gradual migration.
