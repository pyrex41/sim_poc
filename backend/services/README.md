# Replicate Client Service

A robust Python client for interacting with the Replicate API to generate images and videos with automatic polling and retry logic.

## Features

- **Image Generation**: Generate images using Flux-Schnell model ($0.003/image)
- **Video Generation**: Create videos from image sequences using SkyReels-2 model ($0.10/second)
- **Automatic Polling**: Poll prediction status with configurable timeout and interval
- **Exponential Backoff**: Retry logic with exponential backoff (5s → 15s → 45s)
- **Cost Estimation**: Calculate costs before running operations
- **Comprehensive Error Handling**: Handle timeouts, rate limits, and network errors
- **Context Manager Support**: Automatic resource cleanup

## Installation

The required dependencies are already in `backend/requirements.txt`:

```bash
pip install requests>=2.31.0
```

## Configuration

Set your Replicate API key as an environment variable:

```bash
export REPLICATE_API_KEY="your-api-key-here"
```

Or pass it directly when initializing the client:

```python
from services.replicate_client import ReplicateClient

client = ReplicateClient(api_key="your-api-key-here")
```

## Usage

### Basic Initialization

```python
from services.replicate_client import ReplicateClient

# Using environment variable
client = ReplicateClient()

# Or with explicit API key
client = ReplicateClient(api_key="your-api-key-here")

# Using context manager (recommended)
with ReplicateClient() as client:
    result = client.generate_image("a red sports car")
```

### Generate an Image

```python
result = client.generate_image("a red sports car in a futuristic city")

if result['success']:
    print(f"Image URL: {result['image_url']}")
    print(f"Prediction ID: {result['prediction_id']}")
else:
    print(f"Error: {result['error']}")
```

**Response Format:**
```python
{
    'success': bool,           # Whether the request succeeded
    'image_url': str,          # URL of generated image (if successful)
    'error': str,              # Error message (if failed)
    'prediction_id': str       # Replicate prediction ID
}
```

### Generate a Video

```python
image_urls = [
    "https://example.com/frame1.jpg",
    "https://example.com/frame2.jpg",
    "https://example.com/frame3.jpg"
]

result = client.generate_video(image_urls)

if result['success']:
    print(f"Video URL: {result['video_url']}")
    print(f"Duration: {result['duration_seconds']}s")
    print(f"Prediction ID: {result['prediction_id']}")
else:
    print(f"Error: {result['error']}")
```

**Response Format:**
```python
{
    'success': bool,           # Whether the request succeeded
    'video_url': str,          # URL of generated video (if successful)
    'error': str,              # Error message (if failed)
    'prediction_id': str,      # Replicate prediction ID
    'duration_seconds': int    # Estimated video duration
}
```

### Poll a Prediction

If you have a prediction ID and want to check its status manually:

```python
result = client.poll_prediction(
    prediction_id="abc123",
    timeout=600,    # 10 minutes
    interval=5      # Check every 5 seconds
)

if result['status'] == 'succeeded':
    print(f"Output: {result['output']}")
else:
    print(f"Status: {result['status']}, Error: {result['error']}")
```

**Response Format:**
```python
{
    'status': str,    # 'succeeded', 'failed', 'canceled', or 'timeout'
    'output': any,    # Output data (if succeeded)
    'error': str      # Error message (if failed)
}
```

### Estimate Costs

Calculate costs before running operations:

```python
# Estimate cost for 10 images and a 30-second video
cost = client.estimate_cost(num_images=10, video_duration=30)
print(f"Estimated cost: ${cost:.2f}")
# Output: Estimated cost: $3.03
```

**Pricing:**
- Flux-Schnell images: $0.003 per image
- SkyReels-2 video: $0.10 per second

## Error Handling

The client handles various error scenarios:

### Timeout Errors
```python
result = client.generate_image("prompt")
if not result['success'] and 'timeout' in result['error'].lower():
    print("Request timed out, try again later")
```

### Network Errors
```python
result = client.generate_image("prompt")
if not result['success'] and 'network' in result['error'].lower():
    print("Network error, check your connection")
```

### Rate Limiting
The client automatically handles rate limiting with exponential backoff:
- First retry: 5 seconds
- Second retry: 15 seconds
- Third+ retry: 45 seconds

### Invalid Input
```python
result = client.generate_video([])  # Empty list
# Returns: {'success': False, 'error': 'No image URLs provided', ...}
```

## Advanced Usage

### Custom Models

```python
# Use a different image generation model
result = client.generate_image(
    prompt="a sunset",
    model="your-custom-model-id"
)

# Use a different video generation model
result = client.generate_video(
    image_urls=["url1.jpg", "url2.jpg"],
    model="your-custom-video-model"
)
```

### Extended Timeouts

For long-running operations:

```python
# Generate video with 20-minute timeout
result = client.generate_video(
    image_urls=many_images,
    model="fofr/skyreels-2"
)
# Note: generate_video() already uses 1200s (20min) timeout internally
```

### Custom Polling

```python
# Start an operation and get prediction ID
response = client.session.post(
    f"{client.base_url}/predictions",
    json={"version": "model-version", "input": {"prompt": "test"}}
)
prediction_id = response.json()['id']

# Poll with custom settings
result = client.poll_prediction(
    prediction_id=prediction_id,
    timeout=1800,  # 30 minutes
    interval=10    # Check every 10 seconds
)
```

## Testing

Run the test suite:

```bash
cd backend
python services/test_replicate_client.py
```

This will run:
- Initialization tests
- Cost estimation tests
- Error handling tests
- Context manager tests
- Usage examples

## API Reference

### ReplicateClient

#### `__init__(api_key: Optional[str] = None)`
Initialize the client with an API key.

**Parameters:**
- `api_key` (str, optional): Replicate API key. Falls back to `REPLICATE_API_KEY` env var.

**Raises:**
- `ValueError`: If no API key is provided or found.

---

#### `generate_image(prompt: str, model: str = "black-forest-labs/flux-schnell") -> dict`
Generate an image from a text prompt.

**Parameters:**
- `prompt` (str): Text description of the image
- `model` (str): Model identifier (default: flux-schnell)

**Returns:** Dict with `success`, `image_url`, `error`, `prediction_id`

---

#### `generate_video(image_urls: List[str], model: str = "fofr/skyreels-2") -> dict`
Generate a video from a sequence of images.

**Parameters:**
- `image_urls` (List[str]): List of image URLs to stitch
- `model` (str): Model identifier (default: skyreels-2)

**Returns:** Dict with `success`, `video_url`, `error`, `prediction_id`, `duration_seconds`

---

#### `poll_prediction(prediction_id: str, timeout: int = 600, interval: int = 5) -> dict`
Poll a prediction until completion or timeout.

**Parameters:**
- `prediction_id` (str): Prediction ID to poll
- `timeout` (int): Max wait time in seconds (default: 600)
- `interval` (int): Polling interval in seconds (default: 5)

**Returns:** Dict with `status`, `output`, `error`

---

#### `estimate_cost(num_images: int, video_duration: int) -> float`
Calculate estimated cost for operations.

**Parameters:**
- `num_images` (int): Number of images to generate
- `video_duration` (int): Video duration in seconds

**Returns:** Total cost in USD

## Architecture

```
backend/services/
├── __init__.py                  # Package initialization
├── replicate_client.py          # Main client implementation
├── test_replicate_client.py     # Test suite
└── README.md                    # This file
```

## Implementation Details

### Polling Logic

The polling mechanism works as follows:

1. **Initial Request**: Create a prediction via Replicate API
2. **Poll Loop**: Check status every N seconds
3. **Status Check**:
   - `starting/processing` → Continue polling
   - `succeeded` → Return output
   - `failed/canceled` → Return error
   - Timeout → Return timeout error
4. **Retry Logic**: On network errors, apply exponential backoff

### Retry Strategy

```
Error Type       | Retry Delay | Max Retries
----------------|-------------|------------
Rate Limit (429)| 5s→15s→45s  | Unlimited
Network Error   | 5s→15s→45s  | 3
Timeout         | 5s→15s→45s  | 3
HTTP Error      | No retry    | 0
```

### Logging

The client uses Python's standard logging module:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or configure for your app
logger = logging.getLogger('services.replicate_client')
logger.setLevel(logging.INFO)
```

## Troubleshooting

### "API key not provided" Error

**Solution:** Set the `REPLICATE_API_KEY` environment variable:
```bash
export REPLICATE_API_KEY="your-key-here"
```

### Polling Timeout

**Symptoms:** Operations timing out before completion.

**Solutions:**
- Increase timeout parameter
- Check Replicate API status
- Verify prediction ID is valid

### Rate Limiting

**Symptoms:** Frequent 429 errors or backoff delays.

**Solutions:**
- Reduce request frequency
- Implement request queuing
- Upgrade Replicate plan

### Network Errors

**Symptoms:** Connection errors or timeouts.

**Solutions:**
- Check internet connectivity
- Verify firewall settings
- Check if Replicate API is accessible

## Performance Considerations

- **Image Generation**: Typically completes in 5-30 seconds
- **Video Generation**: Can take 2-10 minutes depending on length
- **Polling Overhead**: Minimal (~1 request per 5 seconds)
- **Memory Usage**: Low (only stores URLs, not actual media)

## Security Notes

- **API Key Storage**: Never commit API keys to version control
- **Environment Variables**: Use `.env` files (not committed to git)
- **URL Validation**: Validate image URLs before passing to video generation
- **Error Messages**: Don't log API keys in error messages

## License

This service is part of the backend application and follows the same license.

## Support

For issues or questions:
1. Check the test suite for examples
2. Review Replicate API docs: https://replicate.com/docs
3. Check application logs for detailed error messages
