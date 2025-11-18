# Generation Platform v3

Clean, modular architecture for composable AI generation engines.

## 🎯 What's New

### Architecture
- **Composable Engines**: Image, Video, Audio, and Prompt engines with unified interface
- **Provider Pattern**: Easy to swap providers (Replicate, Runway, Stability, etc.)
- **Type Safety**: Strong Pydantic models with validation
- **Async Tasks**: All generation happens asynchronously with task tracking
- **Clean Separation**: Core → Engines → API layers

### New Structure
```
backend/
├── core/                    # Shared infrastructure
│   ├── types.py            # All enums and types
│   ├── exceptions.py       # Exception hierarchy
│   ├── models.py           # Base Pydantic models
│   ├── database.py         # DB connection management
│   └── middleware.py       # Request logging, error handling
│
├── engines/                 # Generation engines
│   ├── base.py             # BaseGenerationEngine abstract class
│   └── image/              # Image generation engine
│       ├── engine.py       # ImageEngine implementation
│       ├── models.py       # ImageRequest, ImageResponse
│       ├── repository.py   # Database operations
│       └── providers/      # Provider implementations
│           ├── base.py
│           └── replicate.py
│
├── api/v3/                  # Clean v3 API
│   ├── generation.py       # /generate endpoints
│   └── health.py           # Health check
│
└── main_v3.py              # App factory (50 lines!)
```

## 🚀 Quick Start

### 1. Set up environment
```bash
# Set your Replicate API key
export REPLICATE_API_KEY='your-key-here'
```

### 2. Run migration (first time only)
```bash
# Create v3 database from scratch
python3 backend/migrate_to_v3.py

# Or migrate data from old database
python3 backend/migrate_to_v3.py --old-db backend/simulator.db
```

### 3. Start the server
```bash
# Using the startup script
./start_v3.sh

# Or manually
python3 -m uvicorn backend.main_v3:app --reload
```

### 4. Access the API
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API Usage

### Generate an Image

```bash
# Submit generation task
curl -X POST http://localhost:8000/api/v3/generate/image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A serene mountain landscape at sunset",
    "model": "flux",
    "size": "1024x1024",
    "num_outputs": 1
  }'

# Returns:
{
  "id": "abc-123",
  "engine": "image",
  "status": "pending",
  "provider": "ReplicateImageProvider",
  "created_at": "2025-01-17T10:00:00",
  ...
}
```

### Check Task Status

```bash
curl http://localhost:8000/api/v3/tasks/abc-123

# Returns:
{
  "id": "abc-123",
  "status": "processing",  # or "succeeded", "failed"
  ...
}
```

### Get Result

```bash
curl http://localhost:8000/api/v3/tasks/abc-123/result

# When complete, returns:
{
  "id": "abc-123",
  "url": "https://replicate.delivery/...",
  "width": 1024,
  "height": 1024,
  "prompt": "A serene mountain landscape at sunset",
  ...
}
```

## 🏗️ Database Schema

### New Tables

**`generation_tasks`** - Central task tracking
- All async generation tasks across all engines
- Tracks status, provider, results, errors

**`generated_content`** - Final results
- Images, videos, audio with full metadata
- Links to original task

**`pipeline_executions`** - Pipeline runs (coming soon)
- Multi-step workflows
- Sequential, parallel, or DAG execution

**`pipeline_steps`** - Individual pipeline steps
- Step-by-step execution tracking

### Existing Tables (Preserved)
- `users` - User accounts
- `api_keys` - API key management
- `clients` - Client organizations
- `campaigns` - Marketing campaigns
- `assets` - Uploaded files

## 🔧 Engine Pattern

All engines follow the same interface:

```python
from backend.engines.image import create_image_engine

# Create engine
engine = create_image_engine(provider="replicate")

# Generate (async)
task = await engine.generate(request, user_id="123")

# Check status
task = await engine.get_task(task.id, user_id="123")

# Get result (when complete)
result = await engine.get_result(task.id, user_id="123")

# Cancel
canceled = await engine.cancel(task.id, user_id="123")

# List tasks
tasks = await engine.list_tasks(filters)
```

## 🎨 Adding a New Provider

```python
# 1. Create provider class
class StabilityImageProvider(BaseImageProvider):
    async def submit_task(self, params): ...
    async def get_task_status(self, task_id): ...
    async def cancel_task(self, task_id): ...
    def transform_request(self, request): ...
    def transform_response(self, data): ...

# 2. Update engine factory
def _create_provider(self, provider: ImageProvider):
    if provider == ImageProvider.STABILITY:
        return StabilityImageProvider()
    ...

# 3. Done! Provider is now available
engine = create_image_engine(provider="stability")
```

## 📦 Adding a New Engine

```python
# 1. Create engine directory
backend/engines/video/
├── engine.py          # VideoEngine(BaseGenerationEngine)
├── models.py          # VideoRequest, VideoResponse
├── repository.py      # Database operations
└── providers/
    ├── base.py
    └── replicate.py

# 2. Implement BaseGenerationEngine
class VideoEngine(BaseGenerationEngine[VideoRequest, VideoResponse]):
    def _create_response(self, task): ...
    def _process_provider_status(self, status): ...

# 3. Add to core types
class EngineType(str, Enum):
    VIDEO = "video"

# 4. Create API endpoint
@router.post("/generate/video")
async def generate_video(request: VideoRequest): ...
```

## 🧪 Testing

```bash
# Run migration tests
python3 backend/migrate_to_v3.py --no-data --no-backup

# Test API
curl http://localhost:8000/api/v3/health

# Test image generation
curl -X POST http://localhost:8000/api/v3/generate/image \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test image"}'
```

## 🔜 Coming Soon

- [ ] Video Engine (following same pattern)
- [ ] Audio Engine (following same pattern)
- [ ] Prompt Engine (refactored to match)
- [ ] Pipeline Orchestrator
- [ ] Unified webhook handler
- [ ] Legacy API compatibility layer
- [ ] Comprehensive test suite

## 🎯 Benefits

**For Development:**
- ✅ Each engine is ~500 lines (vs 5,950 line monolith)
- ✅ Test engines independently
- ✅ Work on different engines in parallel
- ✅ No merge conflicts

**For Operations:**
- ✅ Clear error messages with custom exceptions
- ✅ Request logging and tracing
- ✅ Health checks
- ✅ Easy to add monitoring

**For Users:**
- ✅ Consistent API across all generation types
- ✅ Clear task status tracking
- ✅ Async by default (no timeouts)
- ✅ Strong type safety

## 📖 Documentation

- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Schema: `backend/schema_v3.sql`
- Migration: `backend/migrate_to_v3.py`

## 🆘 Troubleshooting

**Database not found:**
```bash
python3 backend/migrate_to_v3.py
```

**Import errors:**
```bash
pip install -r backend/requirements.txt
```

**Replicate API errors:**
```bash
export REPLICATE_API_KEY='your-key-here'
```

**Port already in use:**
```bash
# Change port in start_v3.sh or:
uvicorn backend.main_v3:app --port 8001
```
