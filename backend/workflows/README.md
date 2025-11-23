# Luigi Workflow Integration for V3 Campaign Pipeline

## Overview

This directory contains Luigi workflow definitions for the V3 campaign video generation pipeline. Luigi provides dependency management, checkpointing, failure recovery, and workflow visualization.

## Architecture

### Current Pipeline → Luigi Task Mapping

The V3 pipeline consists of the following stages, each mapped to a Luigi task:

```
Campaign Request
    ↓
[AssetCollectionTask] ← Fetch campaign assets
    ↓
[ImagePairSelectionTask] ← Use xAI Grok to select optimal pairs
    ↓
[SubJobCreationTask] ← Create sub-jobs for each pair
    ↓
[ParallelVideoGenerationTask] ← Launch all Replicate predictions
    ↓
[VideoDownloadTask] ← Download all generated videos
    ↓
[AudioGenerationTask] ← Generate background music
    ↓
[VideoCombinationTask] ← Combine all clips
    ↓
[AudioMergingTask] ← Merge audio with video
    ↓
[VideoStorageTask] ← Store final video in database
```

### Luigi Benefits for This Pipeline

1. **Dependency Management**: Automatic resolution ensures tasks run in correct order
2. **Checkpointing**: Completed tasks are marked, allowing resume from failures
3. **Parallel Execution**: Luigi can run independent sub-jobs concurrently
4. **Visualization**: Web UI shows real-time pipeline status
5. **Retry Logic**: Built-in retry mechanism for failed tasks
6. **Atomic Operations**: Target-based completion ensures clean state

## Task Structure

### Base Task Class

All pipeline tasks inherit from `CampaignPipelineTask`:

```python
class CampaignPipelineTask(luigi.Task):
    job_id = luigi.IntParameter()
    campaign_id = luigi.Parameter()

    def output(self):
        # Returns a Target that marks completion
        return CampaignStateTarget(self.job_id, self.__class__.__name__)
```

### Task Dependencies

Each task declares its dependencies using `requires()`:

```python
class ImagePairSelectionTask(CampaignPipelineTask):
    def requires(self):
        return AssetCollectionTask(
            job_id=self.job_id,
            campaign_id=self.campaign_id
        )
```

### Parallel Sub-Tasks

For parallel video generation, Luigi supports dynamic task generation:

```python
class ParallelVideoGenerationTask(CampaignPipelineTask):
    def requires(self):
        # Returns list of sub-job tasks
        pairs = self.load_image_pairs()
        return [
            VideoGenerationSubTask(
                job_id=self.job_id,
                sub_job_id=pair['id']
            )
            for pair in pairs
        ]
```

## Integration with FastAPI

### Triggering Luigi Workflows

FastAPI endpoints trigger Luigi workflows using `luigi.build()`:

```python
@router.post("/jobs/from-image-pairs")
async def create_job_from_image_pairs(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    # Create job record
    job_id = create_video_job(...)

    # Launch Luigi workflow in background
    background_tasks.add_task(
        run_luigi_workflow,
        job_id,
        request.get("campaignId")
    )

    return {"jobId": job_id, "status": "pipeline_started"}
```

### Async Integration

Luigi tasks wrap async operations using `asyncio`:

```python
class VideoGenerationSubTask(luigi.Task):
    def run(self):
        # Run async operation synchronously
        asyncio.run(self._async_run())

    async def _async_run(self):
        # Existing async video generation logic
        result = await replicate_client.generate_video_from_pair(...)
```

## Configuration

### luigi.cfg

```ini
[core]
default-scheduler-host=localhost
default-scheduler-port=8082
logging_conf_file=logging.conf

[worker]
keep_alive=true
count_uniques=true
count_last_params=true
max_reschedules=3

[scheduler]
record_task_history=true
state_path=/var/luigi-state
```

### Database State Storage

Pipeline state is stored in the existing database:

```sql
CREATE TABLE luigi_task_state (
    task_id VARCHAR(255) PRIMARY KEY,
    job_id INTEGER,
    task_name VARCHAR(100),
    status VARCHAR(20),
    output_data TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

## Monitoring & Visualization

### Luigi Web UI

Start the Luigi scheduler with visualization:

```bash
luigid --background --logdir logs
```

Access the UI at `http://localhost:8082`

### Integration with Existing API

Pipeline status is exposed through existing v3 endpoints:

```python
@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    # Check Luigi task states
    task_states = get_luigi_task_states(job_id)

    return {
        "jobId": job_id,
        "status": compute_overall_status(task_states),
        "pipeline": task_states,
        "luigiDashboard": f"http://localhost:8082/static/visualiser/index.html#task/{job_id}"
    }
```

## Error Handling & Retry

### Automatic Retries

```python
class VideoGenerationSubTask(CampaignPipelineTask):
    retry_count = 3

    def on_failure(self, exception):
        logger.error(f"Sub-task failed: {exception}")
        # Update job status in database
        update_sub_job_status(self.sub_job_id, "failed", str(exception))
```

### Manual Rerun

Failed tasks can be manually rerun from the UI or API:

```bash
# Rerun specific task
luigi --module workflows.campaign_pipeline VideoGenerationSubTask \
    --job-id 123 --sub-job-id abc123 --local-scheduler
```

## Migration Strategy

### Phase 1: Parallel Operation (Week 1-2)
- Deploy Luigi alongside existing orchestrator
- Add feature flag to route requests to Luigi
- Test with subset of campaigns

### Phase 2: Gradual Migration (Week 3-4)
- Increase traffic to Luigi pipeline
- Monitor performance and reliability
- Fix any integration issues

### Phase 3: Full Cutover (Week 5)
- Route 100% of traffic to Luigi
- Remove old orchestration code
- Keep existing API interface unchanged

## Development & Testing

### Running Locally

```bash
# Install dependencies
pip install luigi

# Run single task
python -m luigi --module workflows.campaign_pipeline \
    CampaignPipelineWorkflow \
    --job-id 1 \
    --campaign-id camp123 \
    --local-scheduler

# Run with central scheduler
luigid --background
python -m luigi --module workflows.campaign_pipeline \
    CampaignPipelineWorkflow \
    --job-id 1 \
    --campaign-id camp123
```

### Testing

```python
# Unit test for task
class TestImagePairSelectionTask(unittest.TestCase):
    def test_image_pair_selection(self):
        task = ImagePairSelectionTask(job_id=1, campaign_id="test")
        luigi.build([task], local_scheduler=True)

        self.assertTrue(task.output().exists())
        pairs = task.load_output()
        self.assertGreater(len(pairs), 0)
```

## Performance Considerations

### Concurrency

Luigi supports configurable worker concurrency:

```python
# In FastAPI background task
luigi.build(
    [CampaignPipelineWorkflow(job_id=job_id)],
    workers=10,  # Number of parallel workers
    local_scheduler=False
)
```

### Resource Management

For expensive operations (video generation), use Luigi's resource management:

```python
class VideoGenerationSubTask(CampaignPipelineTask):
    resources = {'replicate_api': 1}  # Limit concurrent API calls
```

## Comparison: Current vs. Luigi

| Feature | Current (asyncio) | Luigi |
|---------|------------------|-------|
| Dependency Management | Manual | Automatic |
| Checkpointing | Custom code | Built-in |
| Retry Logic | Manual | Built-in |
| Visualization | None | Web UI |
| Resume Failed Jobs | Difficult | Easy |
| Parallel Execution | asyncio.gather | Luigi workers |
| State Management | Database + code | Targets + database |

## References

- [Luigi Documentation](https://luigi.readthedocs.io/)
- [Spotify Luigi GitHub](https://github.com/spotify/luigi)
- [Luigi Best Practices](https://luigi.readthedocs.io/en/stable/design_and_limitations.html)
