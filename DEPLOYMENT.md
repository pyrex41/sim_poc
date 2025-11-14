# Deployment Guide

## Quick Start with Docker

1. **Set up environment variables**:
   ```bash
   export REPLICATE_AI_KEY=your_key_here
   ```

2. **Build and run**:
   ```bash
   docker-compose up -d
   ```

The API will be available at `http://localhost:8000`

## Environment Variables

- `REPLICATE_AI_KEY` - Required for AI scene generation
- `DATA` - Directory for SQLite database (default: `./DATA`)

## Data Storage

Generated scenes are stored in SQLite database at `$DATA/scenes.db`

### Database Schema

```sql
CREATE TABLE generated_scenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    scene_data TEXT NOT NULL,
    model TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);
```

## API Endpoints

### Scene Generation
- `POST /api/generate` - Generate new scene from prompt
- `POST /api/refine` - Refine existing scene

### Scene History
- `GET /api/scenes` - List all generated scenes
  - Query params: `limit` (default: 50), `offset` (default: 0), `model` (optional filter)
- `GET /api/scenes/{id}` - Get specific scene by ID
- `DELETE /api/scenes/{id}` - Delete scene by ID
- `GET /api/models` - List all models that have generated scenes

### Video Models
- `GET /api/video-models` - List available video generation models
- `POST /api/run-video-model` - Run video generation model

## Production Deployment

### Using Docker

```bash
# Build image
docker build -t physics-simulator .

# Run with persistent data
docker run -d \
  -p 8000:8000 \
  -e REPLICATE_AI_KEY=$REPLICATE_AI_KEY \
  -v $(pwd)/data:/data \
  physics-simulator
```

### Without Docker

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment
export DATA=/path/to/data/directory
export REPLICATE_AI_KEY=your_key_here

# Run
python main.py
```

## Frontend Development

The frontend is built with Elm, Three.js, and Vite.

```bash
npm install
npm run dev  # Development server on port 5173
npm run build  # Production build
```

## Health Check

Check if the API is running:
```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "message": "Physics Simulator API",
  "status": "running"
}
```

## Backup

To backup your data:
```bash
cp $DATA/scenes.db $DATA/scenes.db.backup
```

## Monitoring

View logs:
```bash
docker-compose logs -f api
```
