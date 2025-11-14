# Prompt Parser REST API - Product Requirements Document

**Version:** 1.0  
**Status:** Draft for Review  
**Target Release:** MVP (48 hours), Full (8 days)  
**Competition:** AI Video Generation Pipeline Challenge

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Overview](#2-product-overview)
3. [Technical Architecture](#3-technical-architecture)
4. [API Endpoints](#4-api-endpoints)
5. [Request/Response Schemas](#5-requestresponse-schemas)
6. [Multi-Modal Input Processing](#6-multi-modal-input-processing)
7. [LLM Provider Interface](#7-llm-provider-interface)
8. [Caching Strategy](#8-caching-strategy)
9. [Integration Contracts](#9-integration-contracts)
10. [Error Handling](#10-error-handling)
11. [Validation & Quality](#11-validation--quality)
12. [Deployment](#12-deployment)
13. [Testing Strategy](#13-testing-strategy)
14. [Security](#14-security)
15. [Success Metrics](#15-success-metrics)
16. [Appendix](#16-appendix)

---

## 1. Executive Summary

### 1.1 Purpose

The Prompt Parser API transforms unstructured user prompts (text, images, video) into structured creative direction for AI video generation. It acts as the intelligence layer that bridges user intent with the video generation pipeline.

### 1.2 Key Value Propositions

- **Upscales amateur prompts** into professional creative briefs
- **Extracts visual style** from reference images/videos
- **Fills gaps intelligently** with platform-specific defaults
- **Validates feasibility** before expensive generation
- **Estimates costs** for transparency

### 1.3 Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API Pattern | Synchronous | Simpler MVP, faster iteration |
| State Management | Stateless | Easier scaling, more robust |
| Clarification Flow | Auto-resolve with confidence scores | Minimal user interruption |
| LLM Provider | Swappable (default OpenAI) | Flexibility + fallback resilience |
| Caching | 30-minute TTL | Balance cost vs freshness |
| Image/Video Priority | Visual is primary when provided | Style extraction from reference |
| Cost Estimation | Optional parameter | Transparency without overhead |
| Infrastructure | Fly.io | Fast global edge deployment |

---

## 2. Product Overview

### 2.1 Core Responsibilities

1. **Parse** natural language prompts into structured JSON
2. **Extract** visual style from reference images/videos  
3. **Enrich** with intelligent defaults based on product category and platform
4. **Generate** scene-by-scene breakdowns with generation prompts
5. **Validate** technical feasibility and timing coherence
6. **Estimate** downstream generation costs

### 2.2 Out of Scope

- Actual video/image/audio generation (handled by partner services)
- User authentication/authorization (handled upstream)
- Long-term storage of user data
- Real-time streaming responses
- Payment processing

### 2.3 Integration Context

```
User Input (text/image/video)
         ↓
   Prompt Parser API  ← [this PRD]
         ↓
   Creative Direction JSON
         ↓
   Partner Video Generation API (gauntlet-video-server.fly.dev)
         ↓
   Final Video Output
```

---

## 3. Technical Architecture

### 3.1 Technology Stack

- **Framework:** FastAPI (Python 3.11+)
- **Deployment:** Fly.io (multi-region edge)
- **Cache:** Redis (30-minute TTL)
- **LLM:** OpenAI GPT-4o (default), Claude Sonnet 4 (fallback)
- **Image Processing:** PIL, CLIP embeddings
- **Video Processing:** OpenCV (frame extraction)
- **API Style:** REST, synchronous

### 3.2 System Components

```
┌─────────────────────────────────────────┐
│          FastAPI Application            │
├─────────────────────────────────────────┤
│  ┌────────────────┐  ┌───────────────┐  │
│  │ Input Processor│  │ Cache Manager │  │
│  │ - Text         │  │ - Redis       │  │
│  │ - Image        │  │ - 30min TTL   │  │
│  │ - Video        │  └───────────────┘  │
│  └────────────────┘                     │
│  ┌────────────────┐  ┌───────────────┐  │
│  │ LLM Orchestrator│ │ Validator     │  │
│  │ - OpenAI (1°)  │  │ - Timing      │  │
│  │ - Claude (2°)  │  │ - Feasibility │  │
│  └────────────────┘  └───────────────┘  │
│  ┌────────────────┐  ┌───────────────┐  │
│  │ Scene Generator│  │ Cost Estimator│  │
│  └────────────────┘  └───────────────┘  │
└─────────────────────────────────────────┘
         ↓                        ↑
    Redis Cache           Monitoring/Logs
```

### 3.3 Design Principles

- **Stateless:** Each request contains full context
- **Fail-fast:** Return errors quickly with actionable messages  
- **Idempotent:** Same input → same output (via caching)
- **Transparent:** Return confidence scores and reasoning
- **Resilient:** Provider fallback chains, retry logic

---

## 4. API Endpoints

### 4.1 Endpoint Overview

| Method | Path | Purpose | MVP |
|--------|------|---------|-----|
| POST | `/v1/parse` | Parse single prompt into creative direction | ✅ |
| POST | `/v1/parse/batch` | Parse multiple prompts in parallel | ⚠️ |
| GET | `/v1/health` | Health check for load balancers | ✅ |
| GET | `/v1/providers` | List available LLM providers | ⚠️ |
| POST | `/v1/cache/clear` | Clear cache (debug only) | ⚠️ |

**Legend:** ✅ MVP Required | ⚠️ Nice-to-have | ❌ Post-MVP

---

## 5. Request/Response Schemas

### 5.1 POST /v1/parse

**Purpose:** Primary endpoint for parsing prompts into creative direction

#### 5.1.1 Request Schema

```json
{
  "prompt": {
    "text": "string (optional if media provided)",
    "image_url": "string (optional)",
    "image_base64": "string (optional, mutually exclusive with image_url)",
    "video_url": "string (optional)",
    "video_base64": "string (optional, mutually exclusive with video_url)"
  },
  "options": {
    "llm_provider": "openai | claude (default: openai)",
    "include_cost_estimate": "boolean (default: false)",
    "target_category": "music_video | ad_creative | explainer | null (default: null)",
    "skip_validation": "boolean (default: false)",
    "cache_ttl": "integer (seconds, default: 1800, max: 3600)"
  },
  "context": {
    "previous_config": "object (optional, for iterations)",
    "brand_guidelines": {
      "colors": ["#hexcode"],
      "fonts": ["string"],
      "tone": "string",
      "logo_url": "string (optional)"
    }
  }
}
```

**Field Descriptions:**

- `prompt.text`: Natural language description of desired ad/video
- `prompt.image_url`: Reference image URL for style extraction (primary when provided)
- `prompt.video_url`: Reference video URL for style extraction (extracts first + last frame)
- `options.include_cost_estimate`: Calculate estimated generation cost
- `options.target_category`: Hint at intended use case for better defaults
- `context.previous_config`: For iterative edits, provide previous creative_direction

**Constraints:**

- At least one of `text`, `image_url`, or `video_url` required
- Max text length: 5000 characters
- Max image size: 10MB
- Max video size: 50MB, max duration: 60 seconds
- Video processing extracts first + last frame only

#### 5.1.2 Response Schema (Success - 200)

```json
{
  "status": "success",
  "request_id": "string (uuid)",
  "creative_direction": {
    "product": {
      "name": "string",
      "category": "string",
      "description": "string",
      "price_tier": "budget | mid_range | premium | luxury"
    },
    "technical_specs": {
      "duration": "integer (seconds)",
      "aspect_ratio": "string (e.g., '9:16', '16:9', '1:1')",
      "platform": "instagram | tiktok | youtube | facebook | generic",
      "resolution": "string (e.g., '1080x1920')",
      "fps": "integer (default: 30)"
    },
    "visual_direction": {
      "aesthetic": "string (e.g., 'modern_luxury')",
      "style_source": "text | image | video | hybrid",
      "color_palette": [
        {
          "hex": "string",
          "role": "primary | secondary | accent | background"
        }
      ],
      "lighting_style": "string (e.g., 'dramatic_soft_shadows')",
      "camera_style": "string (e.g., 'smooth_gimbal_cinematic')",
      "scene_types": ["string"]
    },
    "audio_direction": {
      "music_genre": "string",
      "mood": ["string"],
      "tempo": "string | integer (bpm)",
      "intensity_curve": "building | sustained | wave",
      "instruments": ["string"]
    },
    "text_strategy": {
      "overlays": [
        {
          "text": "string",
          "start_time": "float (seconds)",
          "end_time": "float (seconds)",
          "style": "string",
          "position": "top_third | center | bottom_third | custom",
          "font_size": "small | medium | large",
          "animation": "fade_in | slide_in | none"
        }
      ],
      "font_family": "string",
      "text_color": "string (hex)",
      "outline_color": "string (hex, optional)"
    },
    "pacing": {
      "overall": "slow | moderate | fast | dynamic",
      "scene_duration_avg": "float (seconds)",
      "transition_style": "cut | dissolve | fade | wipe",
      "cuts_per_minute": "integer",
      "energy_curve": "flat | building | wave"
    },
    "cta": {
      "text": "string",
      "start_time": "float (seconds)",
      "duration": "float (seconds)",
      "style": "button | text | badge",
      "action": "shop_now | learn_more | sign_up | visit | custom"
    }
  },
  "scenes": [
    {
      "id": "string (e.g., 'scene_1_hook')",
      "scene_number": "integer",
      "start_time": "float (seconds)",
      "duration": "float (seconds)",
      "end_time": "float (seconds, computed)",
      "purpose": "hook | context | product_showcase | benefit | cta | transition",
      "visual": {
        "shot_type": "extreme_close_up | close_up | medium_shot | wide_shot | establishing",
        "subject": "string (what's in the shot)",
        "camera_movement": "static | pan | tilt | dolly | crane | handheld | orbital",
        "environment": "string (setting/background)",
        "generation_prompt": "string (detailed prompt for video/image generation)",
        "reference_image_index": "integer | null (if using extracted frame)"
      },
      "audio": {
        "music_intensity": "float (0.0-1.0)",
        "sound_effects": ["string"],
        "voiceover_text": "string | null"
      },
      "text_overlay": {
        "text": "string",
        "style": "string",
        "position": "string",
        "animation": "string"
      } | null,
      "transition_to_next": {
        "type": "cut | dissolve | fade | wipe | zoom",
        "duration": "float (seconds, default: 0.5)"
      }
    }
  ],
  "extracted_references": {
    "images": [
      {
        "source": "user_upload | video_frame",
        "frame_type": "first | last | key_frame | null",
        "base64": "string (optional)",
        "analysis": {
          "dominant_colors": ["#hexcode"],
          "lighting": "string",
          "composition": "string",
          "mood": "string"
        }
      }
    ]
  },
  "metadata": {
    "confidence_score": "float (0.0-1.0, overall confidence)",
    "confidence_breakdown": {
      "product_understanding": "float (0.0-1.0)",
      "style_clarity": "float (0.0-1.0)",
      "technical_feasibility": "float (0.0-1.0)"
    },
    "defaults_used": ["string (list of fields using defaults)"],
    "warnings": ["string (potential issues)"],
    "llm_provider_used": "string",
    "processing_time_ms": "integer",
    "cache_hit": "boolean",
    "input_summary": {
      "had_text": "boolean",
      "had_image": "boolean",
      "had_video": "boolean"
    }
  },
  "cost_estimate": {
    "total_usd": "float",
    "breakdown": {
      "video_generation": "float",
      "image_generation": "float",
      "audio_generation": "float",
      "text_to_speech": "float"
    },
    "assumptions": ["string"],
    "confidence": "low | medium | high"
  } | null
}
```

**Key Output Fields:**

- `creative_direction`: High-level creative brief
- `scenes`: Scene-by-scene breakdown with generation prompts
- `extracted_references`: Visual references extracted from input
- `metadata.confidence_score`: 0.0-1.0, how confident the parser is
- `cost_estimate`: Optional, estimated downstream generation cost

#### 5.1.3 Response Schema (Error - 4xx/5xx)

```json
{
  "status": "error",
  "request_id": "string (uuid)",
  "error": {
    "code": "string (error code)",
    "message": "string (human-readable)",
    "details": "object | string | null (additional context)",
    "retry_after": "integer | null (seconds, if rate limited)",
    "documentation_url": "string (link to docs)"
  },
  "timestamp": "string (ISO 8601)"
}
```

**Error Codes:**

| Code | HTTP | Description | Retryable |
|------|------|-------------|-----------|
| `INVALID_PROMPT` | 400 | No text/image/video provided | No |
| `PROMPT_TOO_LONG` | 400 | Text exceeds 5000 chars | No |
| `IMAGE_TOO_LARGE` | 400 | Image exceeds 10MB | No |
| `VIDEO_TOO_LARGE` | 400 | Video exceeds 50MB | No |
| `VIDEO_TOO_LONG` | 400 | Video exceeds 60 seconds | No |
| `IMAGE_PROCESSING_FAILED` | 400 | Could not decode image | No |
| `VIDEO_PROCESSING_FAILED` | 400 | Could not extract frames | No |
| `INVALID_URL` | 400 | URL not accessible | No |
| `INVALID_PARAMETERS` | 400 | Invalid options provided | No |
| `CONTENT_VIOLATION` | 403 | Prompt violates content policy | No |
| `LLM_RATE_LIMIT` | 429 | Rate limited by provider | Yes (with backoff) |
| `LLM_TIMEOUT` | 504 | Provider timed out | Yes |
| `LLM_PROVIDER_ERROR` | 502 | Provider returned error | Maybe |
| `CACHE_ERROR` | 500 | Cache unavailable (degraded) | Yes |
| `INTERNAL_ERROR` | 500 | Unhandled error | Maybe |

#### 5.1.4 Example Requests

**Example 1: Text-only prompt**

```bash
curl -X POST https://api.yourservice.fly.dev/v1/parse \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "text": "Create a 30 second Instagram ad for luxury watches with elegant gold aesthetics"
    },
    "options": {
      "include_cost_estimate": true
    }
  }'
```

**Example 2: Image-primary with text context**

```bash
curl -X POST https://api.yourservice.fly.dev/v1/parse \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "text": "Make an energetic ad for athletic shoes",
      "image_url": "https://example.com/reference-style.jpg"
    },
    "options": {
      "llm_provider": "openai",
      "include_cost_estimate": true,
      "target_category": "ad_creative"
    }
  }'
```

**Example 3: Video reference with style extraction**

```bash
curl -X POST https://api.yourservice.fly.dev/v1/parse \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "text": "Create a similar vibe for my skincare product",
      "video_url": "https://example.com/competitor-ad.mp4"
    },
    "options": {
      "include_cost_estimate": true
    }
  }'
```

**Example 4: Iteration on previous config**

```bash
curl -X POST https://api.yourservice.fly.dev/v1/parse \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": {
      "text": "Make it faster-paced and add blue colors instead of gold"
    },
    "context": {
      "previous_config": {
        "product": {"name": "luxury watch"},
        "visual_direction": {"aesthetic": "modern_luxury"},
        "technical_specs": {"duration": 30, "platform": "instagram"}
      }
    }
  }'
```

---

### 5.2 POST /v1/parse/batch

**Purpose:** Parse multiple prompts in parallel for A/B testing

#### 5.2.1 Request Schema

```json
{
  "prompts": [
    {
      "id": "string (client-provided identifier)",
      "prompt": {
        "text": "string",
        "image_url": "string (optional)"
      },
      "options": {
        "include_cost_estimate": "boolean (default: false)"
      }
    }
  ],
  "batch_options": {
    "fail_fast": "boolean (default: false)",
    "max_parallel": "integer (default: 5, max: 10)"
  }
}
```

#### 5.2.2 Response Schema

```json
{
  "status": "success | partial_success | error",
  "batch_id": "string (uuid)",
  "results": [
    {
      "id": "string (matches request id)",
      "status": "success | error",
      "response": {
        "// Same structure as /v1/parse": {}
      } | null,
      "error": {
        "// Same as error schema": {}
      } | null
    }
  ],
  "metadata": {
    "total": "integer",
    "successful": "integer",
    "failed": "integer",
    "processing_time_ms": "integer"
  }
}
```

**Limits:**
- Max 10 prompts per batch
- Same 30-second timeout as single parse
- Each prompt billed separately for cost estimation

---

### 5.3 GET /v1/health

**Purpose:** Health check for load balancers and monitoring

#### Response Schema

```json
{
  "status": "healthy | degraded | unhealthy",
  "checks": {
    "api": "ok | error",
    "redis_cache": "ok | error | degraded",
    "llm_openai": "ok | error | rate_limited",
    "llm_claude": "ok | error | rate_limited"
  },
  "version": "string (e.g., '1.0.0')",
  "uptime_seconds": "integer",
  "timestamp": "string (ISO 8601)"
}
```

**Health Status Logic:**
- `healthy`: All checks OK
- `degraded`: Cache or secondary LLM down (still functional)
- `unhealthy`: API or primary LLM down (cannot process)

---

### 5.4 GET /v1/providers

**Purpose:** List available LLM providers and their current status

#### Response Schema

```json
{
  "providers": [
    {
      "id": "openai",
      "name": "OpenAI GPT-4o",
      "status": "available | unavailable | rate_limited",
      "is_default": "boolean",
      "capabilities": {
        "text": true,
        "vision": true,
        "max_tokens": 4096
      },
      "estimated_latency_ms": "integer"
    },
    {
      "id": "claude",
      "name": "Claude Sonnet 4",
      "status": "available | unavailable | rate_limited",
      "is_default": false,
      "capabilities": {
        "text": true,
        "vision": true,
        "max_tokens": 8192
      },
      "estimated_latency_ms": "integer"
    }
  ],
  "default_provider": "string (id)"
}
```

---

### 5.5 POST /v1/cache/clear

**Purpose:** Clear cache for debugging (auth required in production)

#### Request Schema

```json
{
  "prompt_hash": "string (optional, clear specific entry)",
  "clear_all": "boolean (default: false, requires admin)"
}
```

#### Response Schema

```json
{
  "status": "success",
  "cleared_count": "integer",
  "message": "string"
}
```

---

## 6. Multi-Modal Input Processing

### 6.1 Processing Priority

**When multiple inputs provided:**

1. **Video** → Extract first + last frame → Treat as primary visual reference
2. **Image** → Use as primary visual reference
3. **Text** → Provides context, modifications, or fills gaps

**Priority Logic:**
```
if video_provided:
    extract_frames(first, last)
    visual_style = analyze_video_frames()
    text_context = parse_text_for_modifications()
    merge(visual_style as primary, text_context as modifiers)

elif image_provided:
    visual_style = analyze_image()
    text_context = parse_text_for_modifications()
    merge(visual_style as primary, text_context as modifiers)

else:
    parse_text_fully()
```

### 6.2 Video Processing

**Video Input Handling:**

```python
async def process_video_input(video_data: bytes) -> dict:
    """
    Extract first and last frames from video for style analysis.
    Max video: 50MB, 60 seconds
    """
    
    # 1. Validate video
    if len(video_data) > 50 * 1024 * 1024:
        raise VideoTooLargeError("Video exceeds 50MB")
    
    # 2. Extract frames using OpenCV
    video = cv2.VideoCapture(video_data)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = video.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps
    
    if duration > 60:
        raise VideoTooLongError("Video exceeds 60 seconds")
    
    # 3. Extract first frame
    video.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, first_frame = video.read()
    
    # 4. Extract last frame
    video.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    ret, last_frame = video.read()
    
    video.release()
    
    # 5. Analyze both frames
    first_analysis = await analyze_frame_style(first_frame)
    last_analysis = await analyze_frame_style(last_frame)
    
    return {
        "first_frame": {
            "base64": encode_frame_base64(first_frame),
            "analysis": first_analysis
        },
        "last_frame": {
            "base64": encode_frame_base64(last_frame),
            "analysis": last_analysis
        },
        "video_metadata": {
            "duration": duration,
            "fps": fps,
            "total_frames": total_frames
        }
    }
```

**Why First + Last Frame:**
- **First frame**: Captures opening hook style, initial aesthetic
- **Last frame**: Captures ending/CTA style, may show evolution
- **Together**: Shows if style is consistent or transitions
- **Efficient**: No need to analyze entire video (cost/time savings)

### 6.3 Image Processing

**Image Input Handling:**

```python
async def process_image_primary(image_data: bytes, text_context: str = None) -> dict:
    """
    Extract visual style from image (primary), use text as context.
    Max image: 10MB
    Supported: JPEG, PNG, WebP, GIF
    """
    
    # 1. Validate and process image
    image = Image.open(BytesIO(image_data))
    
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize if too large (max 1024px longest side)
    if max(image.size) > 1024:
        image.thumbnail((1024, 1024), Image.LANCZOS)
    
    # 2. Extract visual features with CLIP
    clip_embedding = clip_model.encode_image(image)
    
    # 3. Detailed analysis with GPT-4V
    vision_prompt = f"""
    Analyze this reference image in detail:
    
    Extract:
    1. Color palette (5-7 dominant colors with hex codes)
    2. Lighting style (natural, studio, dramatic, soft, etc.)
    3. Composition style (rule of thirds, centered, asymmetric, etc.)
    4. Mood/atmosphere (energetic, calm, luxurious, minimal, etc.)
    5. Visual elements present (product, people, environment, text, etc.)
    6. Photography/art style (realistic, stylized, illustrated, cinematic, etc.)
    
    {"Additional context from user: " + text_context if text_context else ""}
    
    Return as structured JSON.
    """
    
    vision_analysis = await llm.analyze_image(image, vision_prompt)
    
    # 4. Merge with text context if provided
    if text_context:
        merged_prompt = f"""
        Visual style from reference image:
        {json.dumps(vision_analysis, indent=2)}
        
        User's text modifications/additions:
        {text_context}
        
        Create complete creative direction where:
        - Image style is PRIMARY (colors, lighting, mood from image)
        - Text provides CONTEXT (product details, platform, modifications)
        
        Merge intelligently and return complete creative_direction JSON.
        """
    else:
        merged_prompt = f"""
        Visual style from reference image:
        {json.dumps(vision_analysis, indent=2)}
        
        Create complete creative direction based on this visual style.
        Infer product category and intent from the image.
        
        Return complete creative_direction JSON.
        """
    
    creative_direction = await llm.complete(merged_prompt)
    
    return {
        "creative_direction": creative_direction,
        "extracted_reference": {
            "source": "user_upload",
            "analysis": vision_analysis
        }
    }
```

### 6.4 Text-Only Processing

**Text-Only Prompt Handling:**

When no visual references provided, rely on text prompt and smart defaults.

```python
async def process_text_only(text: str) -> dict:
    """
    Parse text prompt, apply smart defaults based on product category.
    """
    
    # 1. Fast parameter extraction (regex + simple NLP)
    extracted = fast_extract_parameters(text)
    
    # 2. Apply category-specific defaults
    defaults = smart_defaults.get_defaults(extracted)
    
    # 3. Use LLM to enrich and fill creative gaps
    enrichment_prompt = f"""
    You are an expert ad creative director.
    
    User prompt: "{text}"
    
    Extracted parameters: {json.dumps(extracted, indent=2)}
    Applied defaults: {json.dumps(defaults, indent=2)}
    
    Generate complete creative direction including:
    - Visual style (colors, lighting, camera style)
    - Audio direction (music genre, mood, tempo)
    - Text overlays strategy (what text, when, where)
    - Scene-by-scene breakdown (5-8 scenes)
    - Pacing and transitions
    
    Return as complete JSON matching the creative_direction schema.
    """
    
    creative_direction = await llm.complete(enrichment_prompt)
    
    return {
        "creative_direction": creative_direction,
        "metadata": {
            "style_source": "text",
            "defaults_used": list(defaults.keys())
        }
    }
```

---

## 7. LLM Provider Interface

### 7.1 Provider Abstraction

```python
from abc import ABC, abstractmethod
from typing import Optional

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def complete(self, prompt: str, system: str = None, 
                      temperature: float = 0.7) -> str:
        """Generate text completion"""
        pass
    
    @abstractmethod
    async def analyze_image(self, image_data: bytes, 
                           question: str) -> dict:
        """Analyze image and extract information"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider is currently available"""
        pass
    
    @abstractmethod
    def get_estimated_latency(self) -> int:
        """Return estimated latency in milliseconds"""
        pass
```

### 7.2 OpenAI Implementation (Default)

```python
from openai import AsyncOpenAI
import json
import base64

class OpenAIProvider(LLMProvider):
    """OpenAI GPT-4o implementation"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # Vision-capable
        self._available = True
        self._avg_latency_ms = 3000
    
    async def complete(self, prompt: str, system: str = None, 
                      temperature: float = 0.7) -> str:
        """Generate completion"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": system or "You are an expert ad creative director. Return only valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except RateLimitError as e:
            self._available = False
            raise LLMRateLimitError(f"OpenAI rate limit: {e}")
        except TimeoutError as e:
            raise LLMTimeoutError(f"OpenAI timeout: {e}")
    
    async def analyze_image(self, image_data: bytes, question: str) -> dict:
        """Analyze image with vision model"""
        
        # Encode image as base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def is_available(self) -> bool:
        """Check availability"""
        return self._available
    
    def get_estimated_latency(self) -> int:
        """Return estimated latency"""
        return self._avg_latency_ms
```

### 7.3 Claude Implementation (Fallback)

```python
from anthropic import AsyncAnthropic

class ClaudeProvider(LLMProvider):
    """Claude Sonnet 4 implementation"""
    
    def __init__(self):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-20250514"
        self._available = True
        self._avg_latency_ms = 4000
    
    async def complete(self, prompt: str, system: str = None, 
                      temperature: float = 0.7) -> str:
        """Generate completion"""
        
        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                system=system or "You are an expert ad creative director. Return only valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )
            
            return message.content[0].text
            
        except RateLimitError as e:
            self._available = False
            raise LLMRateLimitError(f"Claude rate limit: {e}")
        except TimeoutError as e:
            raise LLMTimeoutError(f"Claude timeout: {e}")
    
    async def analyze_image(self, image_data: bytes, question: str) -> dict:
        """Analyze image with vision"""
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64
                            }
                        },
                        {"type": "text", "text": question}
                    ]
                }
            ]
        )
        
        return json.loads(message.content[0].text)
    
    async def is_available(self) -> bool:
        return self._available
    
    def get_estimated_latency(self) -> int:
        return self._avg_latency_ms
```

### 7.4 Provider Fallback Chain

```python
async def parse_with_fallback(request: dict, 
                              preferred_provider: str = "openai") -> dict:
    """
    Try primary provider, fall back to secondary on failure.
    """
    
    providers = {
        "openai": openai_provider,
        "claude": claude_provider
    }
    
    primary = providers.get(preferred_provider, openai_provider)
    fallback = claude_provider if preferred_provider == "openai" else openai_provider
    
    try:
        logger.info(f"Attempting parse with {preferred_provider}")
        return await primary.parse(request)
        
    except LLMRateLimitError as e:
        logger.warning(f"{preferred_provider} rate limited, falling back")
        return await fallback.parse(request)
        
    except LLMTimeoutError as e:
        logger.error(f"{preferred_provider} timed out, falling back")
        return await fallback.parse(request)
        
    except Exception as e:
        logger.error(f"All providers failed: {e}")
        raise ParserError("Unable to parse prompt with any provider")
```

---

## 8. Caching Strategy

### 8.1 Cache Key Generation

```python
import hashlib
import json

def generate_cache_key(request: dict) -> str:
    """
    Generate deterministic cache key from request.
    Ignores fields that don't affect output.
    """
    
    # Extract cacheable fields
    cacheable = {
        "text": request.get("prompt", {}).get("text"),
        "image_url": request.get("prompt", {}).get("image_url"),
        "video_url": request.get("prompt", {}).get("video_url"),
        "target_category": request.get("options", {}).get("target_category"),
        "llm_provider": request.get("options", {}).get("llm_provider", "openai"),
    }
    
    # Remove None values
    cacheable = {k: v for k, v in cacheable.items() if v is not None}
    
    # Sort for determinism
    normalized = json.dumps(cacheable, sort_keys=True)
    
    # Hash
    hash_digest = hashlib.sha256(normalized.encode()).hexdigest()
    
    return f"prompt_parse:v1:{hash_digest}"
```

### 8.2 Cache Operations

```python
import redis.asyncio as redis
import json

class CacheManager:
    """Redis cache manager"""
    
    def __init__(self, redis_url: str, default_ttl: int = 1800):
        self.redis = redis.from_url(redis_url)
        self.default_ttl = default_ttl  # 30 minutes
    
    async def get(self, key: str) -> Optional[dict]:
        """Get cached result"""
        try:
            cached = await self.redis.get(key)
            if cached:
                logger.info(f"Cache hit: {key}")
                return json.loads(cached)
            logger.info(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache error on get: {e}")
            return None  # Graceful degradation
    
    async def set(self, key: str, value: dict, ttl: int = None) -> bool:
        """Set cached result"""
        try:
            ttl = ttl or self.default_ttl
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value)
            )
            logger.info(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache error on set: {e}")
            return False  # Non-fatal
    
    async def delete(self, key: str) -> bool:
        """Delete cached result"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache error on delete: {e}")
            return False
    
    async def clear_all(self, pattern: str = "prompt_parse:*") -> int:
        """Clear all matching keys (admin only)"""
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            return await self.redis.delete(*keys)
        return 0
```

### 8.3 Cache Policy

**TTL (Time To Live):**
- Default: 30 minutes (1800 seconds)
- Configurable per request: 1-3600 seconds
- Rationale: Balance freshness vs cost savings

**Invalidation:**
- Automatic: TTL expiration
- Manual: POST /v1/cache/clear (requires auth)
- Version bump: Clear all on parser version change

**Cache Miss Behavior:**
1. Generate cache key
2. Check Redis
3. If miss: Call LLM (5-30 seconds)
4. Store in Redis with TTL
5. Return to client
6. Set `metadata.cache_hit: false`

**Cache Hit Behavior:**
1. Generate cache key
2. Check Redis
3. If hit: Return immediately (< 500ms)
4. Set `metadata.cache_hit: true`

---

## 9. Integration Contracts

### 9.1 Integration with Partner Video Generation API

The Prompt Parser outputs a `creative_direction` and `scenes` array that should integrate seamlessly with the partner video generation service at `gauntlet-video-server.fly.dev`.

**Key Integration Points:**

```python
# 1. Parser outputs structured creative direction
parser_response = await parse_prompt(user_input)

# 2. Creative direction maps to partner API parameters
video_generation_request = {
    "scenes": [
        {
            "prompt": scene["visual"]["generation_prompt"],
            "duration": scene["duration"],
            "aspect_ratio": parser_response["creative_direction"]["technical_specs"]["aspect_ratio"],
            "fps": parser_response["creative_direction"]["technical_specs"]["fps"],
            # ... other partner API params
        }
        for scene in parser_response["scenes"]
    ],
    "audio": {
        "genre": parser_response["creative_direction"]["audio_direction"]["music_genre"],
        "mood": parser_response["creative_direction"]["audio_direction"]["mood"],
        # ... other audio params
    }
}

# 3. Submit to partner video generation API
video_result = await partner_api.generate_video(video_generation_request)
```

### 9.2 Parameter Mapping Convention

**Common Parameter Names (for interoperability):**

| Parser Output | Partner API Input | Type |
|---------------|-------------------|------|
| `technical_specs.duration` | `duration` | integer (seconds) |
| `technical_specs.aspect_ratio` | `aspect_ratio` | string ("9:16") |
| `technical_specs.fps` | `fps` | integer |
| `technical_specs.resolution` | `resolution` | string ("1080x1920") |
| `scenes[].visual.generation_prompt` | `prompt` | string |
| `scenes[].duration` | `scene_duration` | float |
| `audio_direction.music_genre` | `music_genre` | string |
| `audio_direction.mood` | `music_mood` | array[string] |

### 9.3 Scene-Level Contract

Each scene in the parser output should contain everything needed for generation:

```json
{
  "scene_number": 1,
  "start_time": 0.0,
  "duration": 3.0,
  "visual": {
    "generation_prompt": "extreme close-up of luxury watch mechanism...",
    "shot_type": "extreme_close_up",
    "camera_movement": "slow_push_in"
  },
  "audio": {
    "music_intensity": 0.6
  }
}
```

**This maps to partner API scene:**

```json
{
  "scene_index": 1,
  "prompt": "extreme close-up of luxury watch mechanism...",
  "duration": 3.0,
  "shot_type": "extreme_close_up",
  "camera_movement": "slow_push_in",
  "music_volume": 0.6
}
```

### 9.4 Content Planner Integration

The Content Planner (next service in pipeline) receives:

```python
content_planner_input = {
    "creative_direction": parser_response["creative_direction"],
    "scenes": parser_response["scenes"],
    "metadata": {
        "total_duration": sum(s["duration"] for s in parser_response["scenes"]),
        "scene_count": len(parser_response["scenes"]),
        "estimated_cost": parser_response["cost_estimate"]["total_usd"]
    }
}

# Content Planner orchestrates:
# 1. Generation Engine calls (per scene)
# 2. Audio generation
# 3. Text overlay rendering
# 4. Composition/stitching
# 5. Final output
```

---

## 10. Error Handling

### 10.1 Retry Strategy

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((LLMTimeoutError, LLMProviderError))
)
async def call_llm_with_retry(prompt: str, provider: LLMProvider):
    """
    Retry LLM calls with exponential backoff.
    Do NOT retry on rate limits (handle separately).
    """
    return await provider.complete(prompt)
```

### 10.2 Error Response Format

All errors follow consistent schema:

```json
{
  "status": "error",
  "request_id": "uuid",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {},
    "retry_after": 60,
    "documentation_url": "https://docs.yourservice.com/errors/ERROR_CODE"
  },
  "timestamp": "2025-11-14T10:30:00Z"
}
```

### 10.3 Graceful Degradation

**Cache Failure:**
- If Redis unavailable: Continue without cache
- Log warning, set `metadata.cache_available: false`
- Still process request (slower but functional)

**Secondary LLM Failure:**
- If OpenAI rate limited: Fall back to Claude
- If both fail: Return error with clear message
- Track provider availability for health checks

**Validation Warnings:**
- Non-fatal issues return in `metadata.warnings`
- User can decide to proceed or modify
- Examples: "Text may be too fast to read", "Scene timing mismatch"

---

## 11. Validation & Quality

### 11.1 Input Validation

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class PromptRequest(BaseModel):
    """Request validation model"""
    
    text: Optional[str] = Field(None, max_length=5000)
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    
    @validator('text', 'image_url', 'video_url')
    def at_least_one_input(cls, v, values):
        """Ensure at least one input provided"""
        if not any([values.get('text'), values.get('image_url'), v]):
            raise ValueError("At least one of text, image_url, or video_url required")
        return v
    
    @validator('text')
    def validate_text_length(cls, v):
        if v and len(v) > 5000:
            raise ValueError("Text prompt exceeds 5000 characters")
        return v
```

### 11.2 Output Validation

```python
def validate_creative_direction(config: dict) -> List[str]:
    """
    Validate output quality and return warnings.
    """
    warnings = []
    
    # Check scene timing
    scenes = config["scenes"]
    total_duration = sum(s["duration"] for s in scenes)
    target_duration = config["creative_direction"]["technical_specs"]["duration"]
    
    if abs(total_duration - target_duration) > 2:
        warnings.append(
            f"Scene timing mismatch: {total_duration}s total vs {target_duration}s target"
        )
    
    # Check text readability
    for scene in scenes:
        text_overlay = scene.get("text_overlay")
        if text_overlay and scene["duration"] < 2:
            warnings.append(
                f"Scene {scene['scene_number']}: Text may be too fast to read "
                f"({scene['duration']}s duration)"
            )
        
        if text_overlay and len(text_overlay.get("text", "")) > 50:
            warnings.append(
                f"Scene {scene['scene_number']}: Text overlay very long "
                f"({len(text_overlay['text'])} chars), may not fit on screen"
            )
    
    # Check aspect ratio consistency
    aspect_ratio = config["creative_direction"]["technical_specs"]["aspect_ratio"]
    if aspect_ratio == "9:16":  # Vertical
        for scene in scenes:
            prompt = scene["visual"]["generation_prompt"].lower()
            if any(word in prompt for word in ["wide", "landscape", "panorama"]):
                warnings.append(
                    f"Scene {scene['scene_number']}: Vertical format but prompt "
                    f"mentions landscape elements"
                )
    
    # Check color palette size
    colors = config["creative_direction"]["visual_direction"]["color_palette"]
    if len(colors) > 6:
        warnings.append(
            f"Large color palette ({len(colors)} colors) may lack visual cohesion"
        )
    
    # Check scene count vs duration
    avg_scene_duration = target_duration / len(scenes)
    if avg_scene_duration < 2:
        warnings.append(
            f"Very short scenes (avg {avg_scene_duration:.1f}s), "
            f"may feel rushed or jarring"
        )
    
    return warnings
```

### 11.3 Confidence Scoring

```python
def calculate_confidence(extracted_params: dict, 
                        enriched_config: dict,
                        input_sources: dict) -> dict:
    """
    Calculate confidence scores for transparency.
    """
    
    # Product understanding confidence
    product_confidence = 1.0
    if not extracted_params.get("product"):
        product_confidence = 0.5
    elif len(extracted_params.get("product", "").split()) < 2:
        product_confidence = 0.7
    
    # Style clarity confidence
    style_confidence = 0.6  # Base for text-only
    
    if input_sources.get("had_image"):
        style_confidence = 0.9  # High confidence with image
    elif input_sources.get("had_video"):
        style_confidence = 0.85  # High confidence with video
    elif extracted_params.get("aesthetic_keywords"):
        style_confidence = min(
            0.6 + (len(extracted_params["aesthetic_keywords"]) * 0.1),
            0.8
        )
    
    # Technical feasibility confidence
    feasibility = 1.0
    warnings = enriched_config.get("metadata", {}).get("warnings", [])
    feasibility = max(0.5, 1.0 - (len(warnings) * 0.08))
    
    # Overall confidence (weighted average)
    overall = (
        product_confidence * 0.3 +
        style_confidence * 0.4 +
        feasibility * 0.3
    )
    
    return {
        "confidence_score": round(overall, 2),
        "confidence_breakdown": {
            "product_understanding": round(product_confidence, 2),
            "style_clarity": round(style_confidence, 2),
            "technical_feasibility": round(feasibility, 2)
        }
    }
```

### 11.4 Content Safety Check

```python
async def check_content_safety(prompt_text: str) -> None:
    """
    Check for harmful content using OpenAI moderation API.
    Raises ContentViolationError if flagged.
    """
    
    try:
        moderation = await openai_client.moderations.create(
            input=prompt_text
        )
        
        result = moderation.results[0]
        
        if result.flagged:
            categories = [
                cat for cat, flagged in result.categories.dict().items()
                if flagged
            ]
            
            raise ContentViolationError(
                f"Content violates policy: {', '.join(categories)}"
            )
            
    except ContentViolationError:
        raise
    except Exception as e:
        logger.warning(f"Content safety check failed: {e}")
        # Don't block on moderation API failures
```

---

## 12. Deployment

### 12.1 Fly.io Configuration

**fly.toml**

```toml
app = "prompt-parser-api"
primary_region = "iad"  # US East

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8080"
  REDIS_URL = "redis://prompt-parser-redis.internal:6379"
  LOG_LEVEL = "INFO"
  ENVIRONMENT = "production"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1
  
  [http_service.concurrency]
    type = "requests"
    hard_limit = 25
    soft_limit = 20

[[services]]
  protocol = "tcp"
  internal_port = 8080

  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [services.concurrency]
    type = "requests"
    hard_limit = 25
    soft_limit = 20

[checks]
  [checks.health]
    grace_period = "10s"
    interval = "30s"
    method = "GET"
    path = "/v1/health"
    timeout = "5s"
    type = "http"

[[vm]]
  cpu_kind = "shared"
  cpus = 2
  memory_mb = 2048

[metrics]
  port = 9091
  path = "/metrics"
```

### 12.2 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/v1/health')"

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 12.3 Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...
REDIS_URL=redis://prompt-parser-redis.internal:6379

# Optional
ANTHROPIC_API_KEY=sk-ant-...
LOG_LEVEL=INFO
CACHE_TTL_SECONDS=1800
MAX_WORKERS=4
TIMEOUT_SECONDS=30
ENVIRONMENT=production

# Feature flags
ENABLE_VIDEO_INPUT=true
ENABLE_BATCH_ENDPOINT=true
```

### 12.4 Scaling Strategy

**Autoscaling Rules:**
- **Scale up:** CPU > 70% for 2 minutes
- **Scale down:** CPU < 30% for 5 minutes
- **Min instances:** 1 (MVP), 2 (production)
- **Max instances:** 10

**Load Balancing:**
- Fly.io handles automatic load balancing
- Round-robin across healthy instances
- Health checks every 30 seconds

**Regional Deployment:**
- Primary: US East (iad)
- Secondary: EU West (ams) - if global traffic
- Tertiary: Asia Pacific (sin) - if global traffic

---

## 13. Testing Strategy

### 13.1 Unit Tests

```python
import pytest
from unittest.mock import Mock, patch

def test_extract_parameters_basic():
    """Test basic parameter extraction"""
    prompt = "30 sec Instagram ad for luxury watches with gold aesthetic"
    
    extracted = extract_parameters(prompt)
    
    assert extracted["duration"] == 30
    assert extracted["platform"] == "instagram"
    assert "luxury" in extracted["aesthetic_keywords"]
    assert "gold" in extracted["aesthetic_keywords"]

def test_extract_parameters_minimal():
    """Test minimal prompt handling"""
    prompt = "ad for coffee"
    
    extracted = extract_parameters(prompt)
    
    assert extracted["product"] == "coffee"
    # Should apply defaults
    assert "platform" not in extracted or extracted["platform"] is None

def test_smart_defaults_luxury_product():
    """Test defaults for luxury products"""
    minimal_input = {
        "product": "luxury handbags",
        "platform": "instagram"
    }
    
    config = apply_smart_defaults(minimal_input)
    
    assert config["pacing"]["overall"] == "slow"
    assert config["audio_direction"]["music_genre"] in ["classical", "neo_classical"]
    assert any(color["role"] == "primary" for color in config["visual_direction"]["color_palette"])

def test_confidence_calculation_high_quality():
    """Test confidence with high-quality input"""
    high_quality = {
        "product": "premium Italian leather handbags",
        "aesthetic_keywords": ["luxury", "elegant", "minimal"],
        "platform": "instagram",
        "duration": 30
    }
    
    confidence = calculate_confidence(high_quality, {}, {"had_image": False})
    
    assert confidence["confidence_score"] > 0.7
    assert confidence["confidence_breakdown"]["product_understanding"] > 0.9

def test_confidence_calculation_with_image():
    """Test confidence boost with image input"""
    with_image = {
        "product": "shoes",
        "platform": "tiktok"
    }
    
    confidence = calculate_confidence(
        with_image, 
        {}, 
        {"had_image": True}
    )
    
    # Image should boost style clarity
    assert confidence["confidence_breakdown"]["style_clarity"] >= 0.9

def test_validation_timing_mismatch():
    """Test validation catches timing issues"""
    config = {
        "creative_direction": {
            "technical_specs": {"duration": 30}
        },
        "scenes": [
            {"duration": 10},
            {"duration": 10},
            {"duration": 5}
        ]
    }
    
    warnings = validate_creative_direction(config)
    
    assert any("timing mismatch" in w.lower() for w in warnings)

def test_cache_key_generation_deterministic():
    """Test cache keys are deterministic"""
    request1 = {
        "prompt": {"text": "luxury watch ad"},
        "options": {"llm_provider": "openai"}
    }
    
    request2 = {
        "prompt": {"text": "luxury watch ad"},
        "options": {"llm_provider": "openai"}
    }
    
    key1 = generate_cache_key(request1)
    key2 = generate_cache_key(request2)
    
    assert key1 == key2

def test_cache_key_generation_different():
    """Test cache keys differ for different inputs"""
    request1 = {"prompt": {"text": "watch ad"}}
    request2 = {"prompt": {"text": "shoe ad"}}
    
    key1 = generate_cache_key(request1)
    key2 = generate_cache_key(request2)
    
    assert key1 != key2
```

### 13.2 Integration Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_parse_endpoint_success():
    """Test full parse flow"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/parse",
            json={
                "prompt": {
                    "text": "Create a 15 second TikTok ad for energy drinks"
                },
                "options": {
                    "include_cost_estimate": True
                }
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "creative_direction" in data
    assert len(data["scenes"]) > 0
    assert data["creative_direction"]["technical_specs"]["platform"] == "tiktok"
    assert data["cost_estimate"]["total_usd"] > 0

@pytest.mark.asyncio
async def test_parse_with_image():
    """Test image-primary parsing"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/parse",
            json={
                "prompt": {
                    "text": "Make an ad for my product",
                    "image_url": "https://picsum.photos/800/600"
                }
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["creative_direction"]["visual_direction"]["style_source"] in ["image", "hybrid"]
    assert len(data["extracted_references"]["images"]) > 0

@pytest.mark.asyncio
async def test_parse_error_no_input():
    """Test error handling for missing input"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v1/parse",
            json={
                "prompt": {},
                "options": {}
            }
        )
    
    assert response.status_code == 400
    data = response.json()
    
    assert data["status"] == "error"
    assert data["error"]["code"] == "INVALID_PROMPT"

@pytest.mark.asyncio
async def test_cache_behavior():
    """Test caching works"""
    request_data = {
        "prompt": {"text": "test prompt for caching"},
        "options": {"include_cost_estimate": False}
    }
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First request - cache miss
        response1 = await client.post("/v1/parse", json=request_data)
        assert response1.json()["metadata"]["cache_hit"] is False
        time1 = response1.json()["metadata"]["processing_time_ms"]
        
        # Second request - cache hit
        response2 = await client.post("/v1/parse", json=request_data)
        assert response2.json()["metadata"]["cache_hit"] is True
        time2 = response2.json()["metadata"]["processing_time_ms"]
        
        # Cache hit should be significantly faster
        assert time2 < time1 / 2

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] in ["healthy", "degraded"]
    assert "checks" in data
```

### 13.3 Load Tests

**Using k6:**

```javascript
// load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 10 },  // Ramp up to 10 users
    { duration: '3m', target: 10 },  // Stay at 10 users
    { duration: '1m', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<10000'], // 95% under 10s
    http_req_failed: ['rate<0.05'],     // < 5% errors
  },
};

export default function () {
  const url = 'https://prompt-parser-api.fly.dev/v1/parse';
  
  const payload = JSON.stringify({
    prompt: {
      text: 'Create a 30 second Instagram ad for luxury watches'
    },
    options: {
      include_cost_estimate: true
    }
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const response = http.post(url, payload, params);
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response has creative_direction': (r) => {
      const body = JSON.parse(r.body);
      return body.creative_direction !== undefined;
    },
    'response time < 10s': (r) => r.timings.duration < 10000,
  });
  
  sleep(5);  // 5 second delay between requests
}
```

**Run load test:**

```bash
k6 run load_test.js
```

**Success Criteria:**
- 95% of requests complete in < 10 seconds
- Error rate < 5%
- Cache hit ratio > 30% during test
- No memory leaks over 5-minute test

---

## 14. Security

### 14.1 Input Validation

**Text Input:**
- Max length: 5000 characters
- Sanitize for control characters
- Check for injection attempts

**Image/Video Input:**
- Max file size: Images 10MB, Videos 50MB
- Validate file headers (magic bytes)
- Timeout downloads after 10 seconds
- Only accept: JPEG, PNG, WebP, GIF, MP4, MOV

**URL Validation:**
```python
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    """Validate URL is safe to fetch"""
    
    parsed = urlparse(url)
    
    # Must have http/https scheme
    if parsed.scheme not in ['http', 'https']:
        raise InvalidURLError("Only HTTP/HTTPS URLs allowed")
    
    # Block internal/private IPs
    if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
        raise InvalidURLError("Cannot fetch from localhost")
    
    # Block private IP ranges
    # 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
    # ... implement IP range checking
    
    return True
```

### 14.2 Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/v1/parse")
@limiter.limit("60/minute")  # 60 requests per minute per IP
async def parse_endpoint(request: Request):
    # ... endpoint logic
```

**Rate Limits:**
- Parse endpoint: 60 requests/minute per IP
- Batch endpoint: 10 requests/minute per IP
- Burst allowance: 10 requests

### 14.3 API Key Management

```python
def get_llm_client(provider: str) -> LLMProvider:
    """
    Get LLM client with secure key management.
    Never log full API keys.
    """
    
    key = os.getenv(f"{provider.upper()}_API_KEY")
    
    if not key:
        raise ConfigurationError(f"Missing API key for {provider}")
    
    # Log only last 4 characters for debugging
    logger.info(f"Using {provider} key ending in {key[-4:]}")
    
    return create_provider_client(provider, key)
```

**Key Rotation:**
- Rotate OpenAI/Claude keys monthly
- Use environment variables, never hardcode
- Separate keys for dev/staging/production

### 14.4 Content Safety

```python
async def validate_prompt_safety(prompt: str) -> None:
    """
    Check prompt for harmful content before processing.
    """
    
    # Use OpenAI moderation API
    moderation = await openai_client.moderations.create(input=prompt)
    
    if moderation.results[0].flagged:
        categories = [
            cat for cat, val in moderation.results[0].categories.dict().items()
            if val
        ]
        
        logger.warning(f"Flagged prompt for: {categories}")
        
        raise ContentViolationError(
            "Prompt violates content policy",
            details={"categories": categories}
        )
```

---

## 15. Success Metrics

### 15.1 MVP Success Criteria (48 hours)

**Functionality:**
- ✅ Parse text prompts into structured JSON
- ✅ Return valid creative_direction + scenes
- ✅ Basic image style extraction working
- ✅ Deployed to Fly.io and accessible

**Performance:**
- ✅ Response time p95 < 10 seconds
- ✅ Error rate < 10% (allowing for early bugs)
- ✅ Handle 3 test prompts successfully

**Integration:**
- ✅ Output format compatible with downstream services
- ✅ Cost estimates within reasonable range

### 15.2 Full Release Success Criteria (8 days)

**Functionality:**
- ✅ Image processing (style extraction from reference images)
- ✅ Video processing (extract first + last frame)
- ✅ Iterative editing (context.previous_config support)
- ✅ Provider fallback working (OpenAI → Claude)

**Performance:**
- ✅ Response time p95 < 8 seconds
- ✅ Response time p50 < 3 seconds
- ✅ Cache hit ratio > 30%
- ✅ Error rate < 2%

**Quality:**
- ✅ Confidence scores accurate (validated against manual review)
- ✅ Cost estimates within 20% of actual generation costs
- ✅ Validation warnings catch real issues

**Scale:**
- ✅ Handle 10 concurrent requests without degradation
- ✅ Process 100 requests/hour without issues

### 15.3 Competition Success Metrics

**Direct Impact on Scoring:**

| Scoring Category | Weight | Parser Contribution |
|------------------|--------|---------------------|
| Output Quality | 40% | High - Parser directly affects scene quality |
| Pipeline Architecture | 25% | High - Clean API contracts, error handling |
| Cost Effectiveness | 20% | Medium - Accurate cost estimates |
| User Experience | 15% | High - Prompt flexibility, confidence scores |

**Deliverables:**
- 3 winning ad submissions rely on high-quality parser output
- Demo video shows parser in action
- Technical deep dive explains parser innovation

---

## 16. Appendix

### 16.1 Example Full API Response

```json
{
  "status": "success",
  "request_id": "req_abc123xyz",
  "creative_direction": {
    "product": {
      "name": "luxury watch",
      "category": "accessories_jewelry",
      "description": "High-end timepiece with elegant gold design",
      "price_tier": "luxury"
    },
    "technical_specs": {
      "duration": 30,
      "aspect_ratio": "9:16",
      "platform": "instagram",
      "resolution": "1080x1920",
      "fps": 30
    },
    "visual_direction": {
      "aesthetic": "modern_luxury",
      "style_source": "text",
      "color_palette": [
        {"hex": "#D4AF37", "role": "primary"},
        {"hex": "#1A1A1A", "role": "secondary"},
        {"hex": "#FFFFFF", "role": "accent"},
        {"hex": "#2C3E50", "role": "background"}
      ],
      "lighting_style": "dramatic_soft_shadows",
      "camera_style": "smooth_gimbal_cinematic",
      "scene_types": ["macro_detail", "lifestyle_context", "hero_product"]
    },
    "audio_direction": {
      "music_genre": "neo_classical",
      "mood": ["sophisticated", "aspirational", "confident"],
      "tempo": 72,
      "intensity_curve": "building",
      "instruments": ["piano", "strings", "subtle_percussion"]
    },
    "text_strategy": {
      "overlays": [
        {
          "text": "Timeless Elegance",
          "start_time": 0.0,
          "end_time": 3.0,
          "style": "serif_fade_in",
          "position": "bottom_third",
          "font_size": "large",
          "animation": "fade_in"
        },
        {
          "text": "Since 1885",
          "start_time": 8.0,
          "end_time": 12.0,
          "style": "minimal_subtitle",
          "position": "bottom_third",
          "font_size": "small",
          "animation": "fade_in"
        },
        {
          "text": "SHOP NOW",
          "start_time": 26.0,
          "end_time": 30.0,
          "style": "bold_cta",
          "position": "center",
          "font_size": "large",
          "animation": "slide_in"
        }
      ],
      "font_family": "Playfair Display",
      "text_color": "#D4AF37",
      "outline_color": "#000000"
    },
    "pacing": {
      "overall": "deliberate",
      "scene_duration_avg": 5.0,
      "transition_style": "dissolve",
      "cuts_per_minute": 12,
      "energy_curve": "building"
    },
    "cta": {
      "text": "SHOP NOW",
      "start_time": 26.0,
      "duration": 4.0,
      "style": "button",
      "action": "shop_now"
    }
  },
  "scenes": [
    {
      "id": "scene_1_hook",
      "scene_number": 1,
      "start_time": 0.0,
      "duration": 3.0,
      "end_time": 3.0,
      "purpose": "hook",
      "visual": {
        "shot_type": "extreme_close_up",
        "subject": "watch_mechanism_gears",
        "camera_movement": "slow_push_in",
        "environment": "black_background",
        "generation_prompt": "extreme close-up macro shot of luxury watch mechanism, intricate gold gears rotating smoothly, shallow depth of field with dramatic side lighting creating strong shadows and highlights on metal surfaces, 8k ultra sharp focus on gear teeth with soft bokeh background, cinematic product photography"
      },
      "audio": {
        "music_intensity": 0.6,
        "sound_effects": ["subtle_mechanical_ticking"],
        "voiceover_text": null
      },
      "text_overlay": {
        "text": "Timeless Elegance",
        "style": "serif_fade_in",
        "position": "bottom_third",
        "animation": "fade_in"
      },
      "transition_to_next": {
        "type": "quick_cut",
        "duration": 0.3
      }
    },
    {
      "id": "scene_2_lifestyle",
      "scene_number": 2,
      "start_time": 3.0,
      "duration": 5.0,
      "end_time": 8.0,
      "purpose": "context",
      "visual": {
        "shot_type": "medium_shot",
        "subject": "businessman_wrist_with_watch",
        "camera_movement": "slow_dolly_right",
        "environment": "luxury_car_interior",
        "generation_prompt": "medium shot of elegant businessman's wrist wearing luxury gold watch, adjusting cufflinks inside premium leather car interior, natural window light from passenger side creating soft rim lighting, shallow depth of field focusing on watch with blurred leather seats in background, refined cinematic aesthetic with warm color grading"
      },
      "audio": {
        "music_intensity": 0.7,
        "sound_effects": [],
        "voiceover_text": null
      },
      "text_overlay": null,
      "transition_to_next": {
        "type": "dissolve",
        "duration": 0.5
      }
    },
    {
      "id": "scene_3_product_hero",
      "scene_number": 3,
      "start_time": 8.0,
      "duration": 8.0,
      "end_time": 16.0,
      "purpose": "product_showcase",
      "visual": {
        "shot_type": "close_up",
        "subject": "watch_rotating_display",
        "camera_movement": "orbital",
        "environment": "black_marble_pedestal",
        "generation_prompt": "luxury gold watch positioned on polished black marble pedestal, camera slowly orbiting 360 degrees around watch, dramatic lighting from 45-degree angle creating elegant reflections on watch face and marble surface, rich gold tones contrasting with deep black background, high-end product photography with perfect focus throughout rotation, photorealistic rendering"
      },
      "audio": {
        "music_intensity": 0.9,
        "sound_effects": [],
        "voiceover_text": null
      },
      "text_overlay": {
        "text": "Since 1885",
        "style": "minimal_subtitle",
        "position": "bottom_third",
        "animation": "fade_in"
      },
      "transition_to_next": {
        "type": "dissolve",
        "duration": 0.5
      }
    },
    {
      "id": "scene_4_detail",
      "scene_number": 4,
      "start_time": 16.0,
      "duration": 6.0,
      "end_time": 22.0,
      "purpose": "product_showcase",
      "visual": {
        "shot_type": "extreme_close_up",
        "subject": "watch_face_details",
        "camera_movement": "slow_pan",
        "environment": "neutral_background",
        "generation_prompt": "extreme close-up shot slowly panning across luxury watch face, showing intricate hour markers with diamond settings, engraved brand logo, sapphire crystal clarity revealing layered dial details, gold hands reflecting soft studio light, exquisite craftsmanship visible in every component, professional product photography with perfect sharpness and color accuracy"
      },
      "audio": {
        "music_intensity": 0.8,
        "sound_effects": [],
        "voiceover_text": null
      },
      "text_overlay": null,
      "transition_to_next": {
        "type": "fade",
        "duration": 0.8
      }
    },
    {
      "id": "scene_5_cta",
      "scene_number": 5,
      "start_time": 22.0,
      "duration": 8.0,
      "end_time": 30.0,
      "purpose": "cta",
      "visual": {
        "shot_type": "medium_close_up",
        "subject": "watch_on_wrist_final",
        "camera_movement": "static",
        "environment": "clean_black_background",
        "generation_prompt": "medium close-up of luxury gold watch on elegant wrist against pure black background, watch face clearly visible showing time, perfect three-point lighting highlighting gold finish and creating subtle reflections, refined pose displaying watch prominently, premium studio product shot with flawless execution, commercial photography quality"
      },
      "audio": {
        "music_intensity": 1.0,
        "sound_effects": [],
        "voiceover_text": null
      },
      "text_overlay": {
        "text": "SHOP NOW",
        "style": "bold_cta",
        "position": "center",
        "animation": "slide_in"
      },
      "transition_to_next": {
        "type": "fade",
        "duration": 1.0
      }
    }
  ],
  "extracted_references": {
    "images": []
  },
  "metadata": {
    "confidence_score": 0.87,
    "confidence_breakdown": {
      "product_understanding": 0.95,
      "style_clarity": 0.80,
      "technical_feasibility": 0.86
    },
    "defaults_used": ["fps", "resolution"],
    "warnings": [],
    "llm_provider_used": "openai",
    "processing_time_ms": 4823,
    "cache_hit": false,
    "input_summary": {
      "had_text": true,
      "had_image": false,
      "had_video": false
    }
  },
  "cost_estimate": {
    "total_usd": 1.60,
    "breakdown": {
      "video_generation": 1.50,
      "image_generation": 0.00,
      "audio_generation": 0.10,
      "text_to_speech": 0.00
    },
    "assumptions": [
      "Using mid-tier video models (~$0.30 per scene)",
      "5 scenes total at 30 seconds duration",
      "Background music generation included",
      "No custom voiceover or TTS"
    ],
    "confidence": "medium"
  }
}
```

### 16.2 Smart Defaults Reference

**Platform Defaults:**

```json
{
  "instagram": {
    "aspect_ratio": "9:16",
    "duration": 30,
    "fps": 30,
    "pacing": "moderate",
    "cuts_per_minute": 12,
    "text_style": "minimal_serif"
  },
  "tiktok": {
    "aspect_ratio": "9:16",
    "duration": 15,
    "fps": 30,
    "pacing": "fast",
    "cuts_per_minute": 20,
    "text_style": "bold_sans"
  },
  "youtube": {
    "aspect_ratio": "16:9",
    "duration": 30,
    "fps": 30,
    "pacing": "moderate",
    "cuts_per_minute": 10,
    "text_style": "clean_sans"
  },
  "facebook": {
    "aspect_ratio": "1:1",
    "duration": 15,
    "fps": 30,
    "pacing": "moderate",
    "cuts_per_minute": 15,
    "text_style": "readable_sans"
  }
}
```

**Product Category Defaults:**

```json
{
  "luxury": {
    "pacing": "slow",
    "transition_style": "dissolve",
    "lighting": "dramatic_soft",
    "music_genre": "classical",
    "color_palette": ["#D4AF37", "#1A1A1A", "#FFFFFF"]
  },
  "tech": {
    "pacing": "dynamic",
    "transition_style": "cut",
    "lighting": "clean_studio",
    "music_genre": "electronic",
    "color_palette": ["#0066FF", "#000000", "#FFFFFF"]
  },
  "food": {
    "pacing": "moderate",
    "transition_style": "dissolve",
    "lighting": "natural_warm",
    "music_genre": "acoustic",
    "color_palette": ["#FF6B35", "#F7931E", "#FFFFFF"]
  },
  "fitness": {
    "pacing": "fast",
    "transition_style": "cut",
    "lighting": "high_contrast",
    "music_genre": "edm",
    "color_palette": ["#FF0000", "#000000", "#00FF00"]
  }
}
```

### 16.3 Glossary

**Terms:**

- **Creative Direction**: High-level structured guide for video generation (colors, mood, pacing)
- **Scene**: Individual segment of video with specific visual/audio characteristics
- **Generation Prompt**: Detailed text prompt passed to video/image generation models
- **Confidence Score**: 0.0-1.0 metric indicating parser's certainty about output quality
- **Style Source**: Origin of visual style (text, image, video, or hybrid)
- **CTA**: Call To Action - final prompt for user action (Shop Now, Learn More, etc.)
- **Aspect Ratio**: Width:height ratio (9:16 vertical, 16:9 horizontal, 1:1 square)

---

## Sign-off

**Document Owner:** Engineering Team  
**Last Updated:** November 14, 2025  
**Status:** Ready for Implementation

**Target Milestones:**
- MVP: Sunday, November 16, 2025 10:59 PM CT
- Full Release: Saturday, November 22, 2025 10:59 PM CT

**Approved for Development:** ✅

---

**Questions or feedback?** Contact the team for clarifications or suggested improvements.
