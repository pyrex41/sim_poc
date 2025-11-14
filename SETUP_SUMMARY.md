# Physics Simulator Deployment Setup

## What Was Added

### 1. Database Layer (`backend/database.py`)
- SQLite database for storing generated scenes
- Tables: `generated_scenes` with fields:
  - `id`: Primary key
  - `prompt`: User's text prompt
  - `scene_data`: JSON of the generated scene
  - `model`: AI model used (e.g., "claude-3.5-sonnet")
  - `created_at`: Timestamp
  - `metadata`: Additional metadata (source, etc.)
- Functions for CRUD operations:
  - `save_generated_scene()` - Save new scene
  - `get_scene_by_id()` - Retrieve specific scene
  - `list_scenes()` - List with pagination and filtering
  - `get_scene_count()` - Count total scenes
  - `get_models_list()` - List unique models
  - `delete_scene()` - Delete by ID

### 2. Updated API Endpoints (`backend/main.py`)
**New endpoints added:**
- `GET /api/scenes` - List all generated scenes (supports pagination & model filter)
- `GET /api/scenes/{id}` - Get specific scene by ID
- `DELETE /api/scenes/{id}` - Delete scene
- `GET /api/models` - List all models that have generated scenes

**Modified:**
- `POST /api/generate` - Now saves to database and returns `_id`

### 3. Docker Setup
- **Dockerfile** - Ready for production deployment
  - Python 3.11 base image
  - Installs dependencies
  - Creates `/data` volume for database
  - Exposes port 8000

- **docker-compose.yml** - Easy local deployment
  - Maps port 8000
  - Mounts `./data` for persistence
  - Passes `REPLICATE_API_KEY` from environment

- **.dockerignore** - Excludes unnecessary files from build

### 4. Documentation
- **DEPLOYMENT.md** - Complete deployment guide with:
  - Docker quick start
  - Environment variables
  - API endpoints documentation
  - Production deployment instructions
  - Health checks and monitoring

## Environment Variables

```bash
DATA=/data                    # Directory for SQLite database
REPLICATE_AI_KEY=your_key    # Replicate API token
```

## Quick Start

```bash
# Set API key
export REPLICATE_AI_KEY=r8_...

# Using Docker Compose
docker-compose up -d

# Or without Docker
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATA=./DATA
python main.py
```

## API Usage Examples

### Generate and Store Scene
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A car driving on a road"}'
```

Response includes `_id` field with database ID.

### List Stored Scenes
```bash
# All scenes
curl http://localhost:8000/api/scenes

# With pagination
curl "http://localhost:8000/api/scenes?limit=10&offset=0"

# Filter by model
curl "http://localhost:8000/api/scenes?model=claude-3.5-sonnet"
```

### Get Specific Scene
```bash
curl http://localhost:8000/api/scenes/1
```

### Delete Scene
```bash
curl -X DELETE http://localhost:8000/api/scenes/1
```

### List Models
```bash
curl http://localhost:8000/api/models
```

## Database Location

- Development: `./DATA/scenes.db` (or `$DATA/scenes.db`)
- Docker: `/data/scenes.db` (mounted to `./data` on host)

## Next Steps for UI

To add scene browsing to the UI, you would need to:

1. Add a new Elm page/module for browsing scene history
2. Create API calls to `/api/scenes` endpoint
3. Display scenes in a list/grid with:
   - Thumbnail/preview
   - Prompt text
   - Model name
   - Timestamp
   - Load/Delete buttons
4. Add filtering by model and date range
5. Implement pagination controls

Example UI features:
- Scene library/gallery view
- Search and filter scenes
- Click to load scene into simulator
- View scene details (prompt, model, timestamp)
- Delete unwanted scenes
- Export scene data

## Files Modified/Created

**Created:**
- `backend/database.py` - Database operations
- `Dockerfile` - Docker build configuration
- `docker-compose.yml` - Docker Compose setup
- `.dockerignore` - Docker build exclusions
- `DEPLOYMENT.md` - Deployment documentation
- `SETUP_SUMMARY.md` - This file

**Modified:**
- `backend/main.py` - Added database imports, scene history endpoints, save on generate
- Fixed replicate library compatibility (commented out, using HTTP API directly)

## Current Status

✅ Backend API ready for deployment
✅ Database layer implemented
✅ Docker configuration complete
✅ Documentation written
✅ Scene storage on generation working
✅ History API endpoints functional

⏳ UI for browsing scenes (not yet implemented)
⏳ Frontend deployment setup (needs Vite build config)
