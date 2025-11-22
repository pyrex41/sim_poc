# LangSmith Observability Setup

This document explains how to set up and use LangSmith for monitoring LLM and Replicate API calls in this project.

## Overview

LangSmith provides observability for:
- **OpenAI API calls** (GPT-4o, GPT-4o-mini) - scene generation, semantic augmentation, prompt parsing
- **Anthropic API calls** (Claude) - prompt parsing, creative direction
- **XAI API calls** (Grok-4) - AI-powered image pair selection, property scene analysis
- **Replicate API calls** - image generation (Flux), video generation (SkyReels, Veo3, Hailuo), audio generation
- **HTTP requests** - all FastAPI endpoints in backend and promptparser services

## Quick Start

### 1. Sign Up for LangSmith Cloud

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Sign up for a free account
3. Create a new project (e.g., "video-sim-poc")
4. Generate an API key from Settings → API Keys

### 2. Configure Environment Variables

Add the following to your `.env` file or environment:

```bash
# Enable LangSmith tracing
LANGCHAIN_TRACING_V2=true

# Your LangSmith API key (required)
LANGCHAIN_API_KEY=<your-api-key-here>

# Project name (optional, defaults to "video-sim-poc")
LANGCHAIN_PROJECT=video-sim-poc

# LangSmith API endpoint (optional, defaults to cloud)
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

For **promptparser** service, also add these to `promptparser/.env`:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your-api-key-here>
LANGCHAIN_PROJECT=video-sim-poc
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### 3. Install Dependencies

Dependencies are already added to `pyproject.toml`. Install them with:

```bash
# If using uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### 4. Run the Application

Start your application as usual:

```bash
# Docker Compose
docker-compose up

# Or locally
uvicorn backend.main:app --reload
```

### 5. View Traces

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Navigate to your project
3. You'll see traces for all API calls automatically

## What Gets Traced

### LLM Calls

All OpenAI and Anthropic API calls are automatically traced with:
- **Input prompts** and system messages
- **Model** and parameters (temperature, max_tokens, etc.)
- **Responses** and token usage
- **Latency** and timing
- **Errors** with full stack traces

**Instrumented functions:**
- `backend/services/scene_generator.py`: `generate_scenes()`, `regenerate_scene()`
- `backend/llm_interpreter.py`: `augment_object()`, `augment_scene()`
- `backend/services/xai_client.py`: `select_image_pairs()`, `select_property_scene_pairs()`
- `promptparser/app/services/llm/openai_provider.py`: `complete()`, `analyze_image()`
- `promptparser/app/services/llm/claude_provider.py`: `complete()`, `analyze_image()`

### Replicate API Calls

All Replicate API calls are traced with:
- **Model** and version
- **Input parameters** (prompt, images, duration, etc.)
- **Prediction ID** and status
- **Polling** behavior and timing
- **Output URLs** and results
- **Errors** and failures

**Instrumented functions:**
- `backend/services/replicate_client.py`: `generate_image()`, `generate_video()`, `generate_video_from_pair()`, `poll_prediction()`

### HTTP Requests

All HTTP requests to your FastAPI endpoints are traced with:
- **Method** and path (e.g., `POST /api/scenes`)
- **Query parameters**
- **Nested LLM/Replicate calls** automatically grouped under the parent request
- **Response time** and status

**Middleware:**
- `backend/main.py`: `LangSmithMiddleware`
- `promptparser/app/main.py`: `LangSmithMiddleware`

## Viewing Traces

### Trace Hierarchy

Traces are organized hierarchically:

```
POST /api/scenes (HTTP request)
├─ generate_scenes (scene generation)
│  ├─ openai_generate_scenes (OpenAI API call)
│  │  └─ Input: prompt, model, temperature
│  │  └─ Output: scenes JSON, tokens used
│  └─ replicate_generate_image (Replicate API call)
│     └─ Input: prompt, model
│     └─ Output: image URL, prediction ID
└─ Response: 200 OK
```

### Filtering and Searching

Use LangSmith's UI to:
- **Filter by tags**: `openai`, `anthropic`, `xai`, `grok`, `replicate`, `http_request`, `scene_generation`, `image_selection`, etc.
- **Search by prompt**: Find specific scenes or prompts
- **Filter by status**: Find errors or slow requests
- **View costs**: Track spending per model
- **Compare runs**: See how prompts changed over time

## Disabling Tracing

To temporarily disable tracing:

```bash
# Set to false or remove the variable
LANGCHAIN_TRACING_V2=false
```

Or remove the `LANGCHAIN_API_KEY` environment variable.

## Docker Compose

The `docker-compose.yml` already includes all necessary environment variables with defaults:

```yaml
environment:
  - LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2:-false}
  - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
  - LANGCHAIN_PROJECT=${LANGCHAIN_PROJECT:-video-sim-poc}
  - LANGCHAIN_ENDPOINT=${LANGCHAIN_ENDPOINT:-https://api.smith.langchain.com}
```

Just set `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY=<key>` in your `.env` file.

## Troubleshooting

### No traces appearing

1. **Check environment variables**: Ensure `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` is set
2. **Check API key**: Verify the API key is valid in LangSmith settings
3. **Check project name**: Ensure the project exists in LangSmith
4. **Check logs**: Look for any LangSmith-related errors in application logs

### Traces are incomplete

- Ensure all services are using the same `LANGCHAIN_PROJECT` name
- Verify middleware is registered (check `backend/main.py` and `promptparser/app/main.py`)

### Performance concerns

- Tracing adds minimal overhead (~5-20ms per trace)
- For high-throughput production, consider:
  - Using sampling (trace only % of requests)
  - Disabling tracing for health checks (already implemented)
  - Using LangSmith's batch mode

## Advanced Configuration

### Custom Tags

Add custom tags to traces for better organization:

```python
@traceable(name="my_function", tags=["custom_tag", "production"])
def my_function():
    # Your code here
```

### Metadata

Add metadata to provide additional context:

```python
@traceable(
    name="process_user_request",
    metadata={
        "user_id": user_id,
        "campaign_id": campaign_id,
        "version": "v2"
    }
)
def process_user_request(user_id, campaign_id):
    # Your code here
```

## Cost Tracking

LangSmith automatically tracks costs for:
- **OpenAI** models (based on token usage and pricing)
- **Anthropic** models (based on token usage and pricing)
- **Replicate** models (if pricing info is available)

View costs in the LangSmith dashboard under your project.

## Further Reading

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Python SDK](https://github.com/langchain-ai/langsmith-sdk)
- [Tracing Reference](https://docs.smith.langchain.com/tracing)
