# Integration Example: Using ReplicateClient in FastAPI

This guide shows how to integrate the ReplicateClient into your FastAPI application.

## Quick Integration

### 1. Import the Client

```python
from services.replicate_client import ReplicateClient
```

### 2. Create a Dependency

Add to your FastAPI app (e.g., in `main.py` or a separate `dependencies.py`):

```python
from fastapi import Depends, HTTPException
from services.replicate_client import ReplicateClient
import logging

logger = logging.getLogger(__name__)

def get_replicate_client() -> ReplicateClient:
    """
    FastAPI dependency to get Replicate client.
    """
    try:
        return ReplicateClient()
    except ValueError as e:
        logger.error(f"Failed to initialize ReplicateClient: {e}")
        raise HTTPException(
            status_code=500,
            detail="Replicate API not configured. Please set REPLICATE_API_KEY."
        )
```

### 3. Create API Endpoints

#### Generate Image Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.replicate_client import ReplicateClient

router = APIRouter(prefix="/api/generate", tags=["generation"])

class ImageGenerationRequest(BaseModel):
    prompt: str
    model: str = "black-forest-labs/flux-schnell"

class ImageGenerationResponse(BaseModel):
    success: bool
    image_url: str | None = None
    error: str | None = None
    prediction_id: str | None = None

@router.post("/image", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest,
    client: ReplicateClient = Depends(get_replicate_client)
):
    """
    Generate an image from a text prompt using Replicate API.

    - **prompt**: Text description of the image to generate
    - **model**: Model identifier (optional, defaults to flux-schnell)
    """
    logger.info(f"Generating image with prompt: {request.prompt[:50]}...")

    result = client.generate_image(
        prompt=request.prompt,
        model=request.model
    )

    if not result['success']:
        logger.error(f"Image generation failed: {result['error']}")
        raise HTTPException(status_code=500, detail=result['error'])

    return ImageGenerationResponse(**result)
```

#### Generate Video Endpoint

```python
class VideoGenerationRequest(BaseModel):
    image_urls: list[str]
    model: str = "fofr/skyreels-2"

class VideoGenerationResponse(BaseModel):
    success: bool
    video_url: str | None = None
    error: str | None = None
    prediction_id: str | None = None
    duration_seconds: int = 0

@router.post("/video", response_model=VideoGenerationResponse)
async def generate_video(
    request: VideoGenerationRequest,
    client: ReplicateClient = Depends(get_replicate_client)
):
    """
    Generate a video from a sequence of images using Replicate API.

    - **image_urls**: List of image URLs to stitch into a video
    - **model**: Model identifier (optional, defaults to skyreels-2)
    """
    if not request.image_urls:
        raise HTTPException(
            status_code=400,
            detail="At least one image URL is required"
        )

    logger.info(f"Generating video from {len(request.image_urls)} images")

    result = client.generate_video(
        image_urls=request.image_urls,
        model=request.model
    )

    if not result['success']:
        logger.error(f"Video generation failed: {result['error']}")
        raise HTTPException(status_code=500, detail=result['error'])

    return VideoGenerationResponse(**result)
```

#### Poll Prediction Endpoint

```python
class PollRequest(BaseModel):
    prediction_id: str
    timeout: int = 600
    interval: int = 5

class PollResponse(BaseModel):
    status: str
    output: Any | None = None
    error: str | None = None

@router.post("/poll", response_model=PollResponse)
async def poll_prediction(
    request: PollRequest,
    client: ReplicateClient = Depends(get_replicate_client)
):
    """
    Poll a prediction until it completes or times out.

    - **prediction_id**: The prediction ID to check
    - **timeout**: Maximum time to wait in seconds (default: 600)
    - **interval**: Polling interval in seconds (default: 5)
    """
    logger.info(f"Polling prediction: {request.prediction_id}")

    result = client.poll_prediction(
        prediction_id=request.prediction_id,
        timeout=request.timeout,
        interval=request.interval
    )

    return PollResponse(**result)
```

#### Cost Estimation Endpoint

```python
class CostEstimateRequest(BaseModel):
    num_images: int = 0
    video_duration: int = 0

class CostEstimateResponse(BaseModel):
    estimated_cost: float
    breakdown: dict[str, float]

@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_cost(
    request: CostEstimateRequest,
    client: ReplicateClient = Depends(get_replicate_client)
):
    """
    Estimate the cost of generating images and video.

    - **num_images**: Number of images to generate
    - **video_duration**: Duration of video in seconds
    """
    total_cost = client.estimate_cost(
        num_images=request.num_images,
        video_duration=request.video_duration
    )

    return CostEstimateResponse(
        estimated_cost=total_cost,
        breakdown={
            "images": request.num_images * client.FLUX_SCHNELL_PRICE_PER_IMAGE,
            "video": request.video_duration * client.SKYREELS2_PRICE_PER_SECOND
        }
    )
```

### 4. Register Router

In your `main.py`:

```python
from fastapi import FastAPI
from your_module import router as generation_router

app = FastAPI(title="Video Generation API")

# Register the generation router
app.include_router(generation_router)
```

## Complete Example with Background Tasks

For long-running operations, use FastAPI's BackgroundTasks:

```python
from fastapi import BackgroundTasks
import asyncio

class AsyncVideoGenerationRequest(BaseModel):
    image_urls: list[str]
    callback_url: str | None = None

def generate_video_background(
    image_urls: list[str],
    callback_url: str | None,
    client: ReplicateClient
):
    """
    Generate video in background and optionally call webhook when done.
    """
    result = client.generate_video(image_urls)

    if callback_url and result['success']:
        # Send webhook notification
        import requests
        requests.post(callback_url, json=result)

    logger.info(f"Background video generation complete: {result['success']}")

@router.post("/video/async")
async def generate_video_async(
    request: AsyncVideoGenerationRequest,
    background_tasks: BackgroundTasks,
    client: ReplicateClient = Depends(get_replicate_client)
):
    """
    Start video generation in the background.

    Returns immediately with a 202 Accepted status.
    """
    background_tasks.add_task(
        generate_video_background,
        request.image_urls,
        request.callback_url,
        client
    )

    return {
        "status": "accepted",
        "message": "Video generation started in background"
    }
```

## Error Handling Middleware

Add global error handling:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if app.debug else "An error occurred"
        }
    )
```

## Testing the Endpoints

### Using cURL

```bash
# Generate an image
curl -X POST "http://localhost:8000/api/generate/image" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a red sports car"}'

# Generate a video
curl -X POST "http://localhost:8000/api/generate/video" \
  -H "Content-Type: application/json" \
  -d '{
    "image_urls": [
      "https://example.com/img1.jpg",
      "https://example.com/img2.jpg"
    ]
  }'

# Estimate cost
curl -X POST "http://localhost:8000/api/generate/estimate-cost" \
  -H "Content-Type: application/json" \
  -d '{"num_images": 10, "video_duration": 30}'

# Poll prediction
curl -X POST "http://localhost:8000/api/generate/poll" \
  -H "Content-Type: application/json" \
  -d '{"prediction_id": "abc123"}'
```

### Using Python requests

```python
import requests

# Generate image
response = requests.post(
    "http://localhost:8000/api/generate/image",
    json={"prompt": "a red sports car"}
)
result = response.json()
print(f"Image URL: {result['image_url']}")

# Generate video
response = requests.post(
    "http://localhost:8000/api/generate/video",
    json={
        "image_urls": [
            "https://example.com/img1.jpg",
            "https://example.com/img2.jpg"
        ]
    }
)
result = response.json()
print(f"Video URL: {result['video_url']}")
```

## Environment Setup

Create a `.env` file:

```bash
# .env
REPLICATE_API_KEY=r8_your_api_key_here
```

Load in your application:

```python
from dotenv import load_dotenv
load_dotenv()
```

## Performance Optimization

### 1. Use Connection Pooling

The client already uses a session for connection pooling. For multiple clients:

```python
from functools import lru_cache

@lru_cache()
def get_replicate_client() -> ReplicateClient:
    """Cached client instance for connection reuse."""
    return ReplicateClient()
```

### 2. Add Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/image")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def generate_image(...):
    ...
```

### 3. Add Request Timeout

```python
from fastapi import Request
import asyncio

@router.post("/image")
async def generate_image(
    request: ImageGenerationRequest,
    client: ReplicateClient = Depends(get_replicate_client)
):
    try:
        # Run with timeout
        result = await asyncio.wait_for(
            asyncio.to_thread(
                client.generate_image,
                request.prompt,
                request.model
            ),
            timeout=300  # 5 minutes
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timeout")
```

## Monitoring and Logging

### Add Structured Logging

```python
import structlog

logger = structlog.get_logger()

@router.post("/image")
async def generate_image(...):
    logger.info(
        "image_generation_started",
        prompt=request.prompt[:50],
        model=request.model
    )

    result = client.generate_image(...)

    logger.info(
        "image_generation_completed",
        success=result['success'],
        prediction_id=result['prediction_id']
    )

    return result
```

### Add Metrics

```python
from prometheus_client import Counter, Histogram

image_requests = Counter(
    'replicate_image_requests_total',
    'Total image generation requests'
)

image_duration = Histogram(
    'replicate_image_duration_seconds',
    'Image generation duration'
)

@router.post("/image")
async def generate_image(...):
    image_requests.inc()

    with image_duration.time():
        result = client.generate_image(...)

    return result
```

## Next Steps

1. Add authentication to protect endpoints
2. Implement webhook callbacks for async operations
3. Add request validation and sanitization
4. Set up monitoring and alerting
5. Add caching for repeated requests
6. Implement request queuing for rate limiting

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Replicate API Reference](https://replicate.com/docs/reference/http)
- [ReplicateClient README](./README.md)
