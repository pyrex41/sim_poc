from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Depends, Response, UploadFile, File, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, validator
from typing import Dict, Optional, List, Any, Union
from datetime import timedelta
from enum import Enum
import uvicorn
import os
import hashlib
import json
import requests
import asyncio
from dotenv import load_dotenv
from pathlib import Path

# Import Asset Pydantic models
from .schemas.assets import (
    Asset,
    ImageAsset,
    VideoAsset,
    AudioAsset,
    DocumentAsset,
)

# Note: replicate package has Python 3.14 compatibility issues
# We only use HTTP API calls via requests library
replicate = None
REPLICATE_AVAILABLE = False

from .config import get_settings
from .database import (
    save_generated_scene,
    get_scene_by_id,
    list_scenes,
    get_scene_count,
    get_models_list,
    delete_scene,
    save_generated_video,
    update_video_status,
    get_video_by_id,
    save_generated_image,
    update_image_status,
    get_image_by_id,
    list_images,
    delete_image,
    save_generated_audio,
    update_audio_status,
    get_audio_by_id,
    list_audio,
    delete_audio,
    create_api_key,
    list_api_keys,
    revoke_api_key,
    # V2 workflow functions
    get_job,
    update_job_progress,
    approve_storyboard,
    # Asset management functions
    save_uploaded_asset,
    get_asset_by_id,
    list_user_assets,
    delete_asset,
    # Video export and refinement functions
    increment_download_count,
    get_download_count,
    refine_scene_in_storyboard,
    reorder_storyboard_scenes,
    get_refinement_count,
    increment_estimated_cost,
    # Client-based generation queries
    get_generated_images_by_client,
    get_generated_videos_by_client,
    # Campaign-based generation queries
    get_generated_images_by_campaign,
    get_generated_videos_by_campaign
)
# Redis cache layer (optional, gracefully degrades if unavailable)
from .cache import (
    get_job_with_cache,
    update_job_progress_with_cache,
    invalidate_job_cache,
    get_cache_stats,
    redis_available
)

from .auth import (
    verify_auth,
    get_current_admin_user,
    authenticate_user,
    create_access_token,
    generate_api_key,
    hash_api_key,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Load environment variables from .env file in parent directory
# Try loading .env from backend directory, then parent directory
if not load_dotenv('.env'):
    load_dotenv('../.env')
# import genesis as gs  # Using geometric validation instead

# Initialize centralized settings
settings = get_settings()

# Import limiter for rate limiting
from .prompt_parser_service.core.limiter import limiter
from slowapi.errors import RateLimitExceeded

# Import prompt parser service router
from .prompt_parser_service.api.v1 import parse as parse_api
from .prompt_parser_service.api.v1 import briefs as briefs_api

# Import clients and campaigns router
from .api_routes import router as clients_campaigns_router

# Import logging
import logging
logger = logging.getLogger(__name__)

# Security: Allowed file extensions (prevents path traversal)
ALLOWED_FILE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'mp3', 'wav', 'pdf'}

# Magic bytes for file type validation
MAGIC_BYTES = {
    b'\x89PNG\r\n\x1a\n': 'png',
    b'\xff\xd8\xff': 'jpg',  # JPEG (various markers)
    b'GIF87a': 'gif',
    b'GIF89a': 'gif',
    b'RIFF': 'webp',  # Also WAV, need to check further
    b'\x00\x00\x00\x18ftypmp42': 'mp4',  # MP4
    b'\x00\x00\x00\x1cftypmp42': 'mp4',
    b'\x00\x00\x00\x20ftypmp42': 'mp4',
    b'\x00\x00\x00\x1cftypisom': 'mp4',
    b'ID3': 'mp3',
    b'\xff\xfb': 'mp3',  # MP3 without ID3
    b'%PDF': 'pdf',
}

def validate_and_sanitize_format(format_str: str) -> str:
    """
    Validate and sanitize file format to prevent path traversal attacks.

    Args:
        format_str: File format/extension to validate

    Returns:
        Sanitized format string

    Raises:
        HTTPException: If format is invalid or not allowed
    """
    if not format_str:
        raise HTTPException(status_code=400, detail="File format is required")

    # Remove dots and convert to lowercase
    format_clean = format_str.lower().strip().lstrip('.')

    # Check against whitelist
    if format_clean not in ALLOWED_FILE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format: {format_clean}. Allowed: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}"
        )

    return format_clean

def validate_file_type_with_magic_bytes(file_contents: bytes, claimed_type: str) -> bool:
    """
    Validate file type using magic bytes to prevent file type spoofing.

    Args:
        file_contents: First bytes of the file
        claimed_type: The MIME type claimed by the client

    Returns:
        True if validation passes, False otherwise
    """
    # Extract first 32 bytes for magic byte checking
    header = file_contents[:32]

    # Log for debugging
    logger.info(f"Validating file type: claimed={claimed_type}, magic_bytes={header[:16].hex()}")

    # Check common image formats
    if claimed_type.startswith('image/'):
        # PNG: starts with \x89PNG
        if header.startswith(b'\x89PNG'):
            return claimed_type in ['image/png', 'image/x-png']
        # JPEG: starts with \xff\xd8\xff
        elif header.startswith(b'\xff\xd8\xff'):
            return claimed_type in ['image/jpeg', 'image/jpg', 'image/pjpeg']
        # GIF
        elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
            return claimed_type in ['image/gif']
        # WebP: RIFF....WEBP
        elif header.startswith(b'RIFF') and b'WEBP' in header[:16]:
            return claimed_type in ['image/webp']
        # SVG
        elif header.startswith(b'<?xml') or header.startswith(b'<svg'):
            return claimed_type in ['image/svg+xml', 'image/svg']
        else:
            # Log the actual bytes to help debug
            logger.warning(f"Unknown image magic bytes for claimed type {claimed_type}")
            logger.warning(f"  Hex: {header[:16].hex()}")
            logger.warning(f"  ASCII: {header[:16]}")
            return False

    # Check video formats
    elif claimed_type.startswith('video/'):
        if b'ftyp' in header[:32]:  # MP4/MOV container
            return claimed_type in ['video/mp4', 'video/quicktime']
        else:
            logger.warning(f"Unknown video magic bytes for claimed type {claimed_type}")
            return False

    # Check audio formats
    elif claimed_type.startswith('audio/'):
        if header.startswith(b'ID3') or header.startswith(b'\xff\xfb') or header.startswith(b'\xff\xf3'):
            return claimed_type in ['audio/mpeg', 'audio/mp3']
        elif header.startswith(b'RIFF') and b'WAVE' in header[:16]:
            return claimed_type in ['audio/wav', 'audio/wave']
        else:
            logger.warning(f"Unknown audio magic bytes for claimed type {claimed_type}")
            return False

    # Check document formats
    elif claimed_type == 'application/pdf':
        if header.startswith(b'%PDF'):
            return True
        else:
            logger.warning(f"Invalid PDF magic bytes")
            return False

    # Unknown type
    logger.warning(f"Unrecognized content type for validation: {claimed_type}")
    return False

openapi_tags = [
    {
        "name": "Core Entities",
        "description": "Client and campaign creation (decoupled from assets)."
    },
    {
        "name": "Asset Management",
        "description": "Upload and retrieve assets with client/campaign association."
    },
    {
        "name": "clients-campaigns",
        "description": "Legacy client and campaign management endpoints."
    },
    {
        "name": "creative",
        "description": "Creative brief parsing and management."
    },
    {
        "name": "Database",
        "description": "Database administration and inspection endpoints (admin only)."
    }
]

app = FastAPI(title="Physics Simulator API", version="1.0.0", openapi_tags=openapi_tags)

# CORS middleware (for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",  # Alternative Vite port
        "http://127.0.0.1:5175"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse({"detail": "Too many requests"}, status_code=429)

app.state.limiter = limiter

# Check if static files exist (production mode)
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists() and STATIC_DIR.is_dir():
    # Mount static files
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

# Pydantic models
class Vec3(BaseModel):
    x: float
    y: float
    z: float

class Transform(BaseModel):
    position: Vec3
    rotation: Vec3
    scale: Vec3

class PhysicsProperties(BaseModel):
    mass: float
    friction: float
    restitution: float

class VisualProperties(BaseModel):
    color: str
    shape: str  # "Box", "Sphere", "Cylinder"

class PhysicsObject(BaseModel):
    id: str
    transform: Transform
    physicsProperties: PhysicsProperties
    visualProperties: VisualProperties
    description: Optional[str] = None  # Text description for LLM semantic augmentation

class Scene(BaseModel):
    objects: Dict[str, PhysicsObject]
    selectedObject: Optional[str] = None

class GenerateRequest(BaseModel):
    prompt: str
    brief_id: Optional[str] = None  # Optional link to creative brief

class ValidationResult(BaseModel):
    valid: bool
    message: str
    details: Optional[Dict] = None

# AI client initialization
if settings.REPLICATE_API_KEY:
    ai_client = {
        "api_key": settings.REPLICATE_API_KEY,
        "base_url": "https://api.replicate.com/v1"
    }
    replicate_client = replicate.Client(api_token=settings.REPLICATE_API_KEY) if REPLICATE_AVAILABLE and replicate else None
    print("AI client initialized with Replicate")
else:
    ai_client = None
    replicate_client = None
    print("Warning: Using demo scene generation (REPLICATE_API_KEY not set)")

# Demo video models for fallback
DEMO_VIDEO_MODELS = [
    {
        "id": "demo/video-1",
        "name": "Demo Text-to-Video",
        "description": "Generates video from text prompt (demo mode)",
        "input_schema": None
    },
    {
        "id": "demo/video-2",
        "name": "Demo Image-to-Video",
        "description": "Generates video from image and prompt (demo mode)",
        "input_schema": None
    }
]

# Simple in-memory cache (replace with LMDB later)
scene_cache = {}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api")
async def api_root():
    return {"message": "Physics Simulator API", "status": "running"}

@app.get("/api/v2/cache/stats")
async def cache_statistics():
    """
    Get cache performance statistics (SQLite-based for POC).

    Returns cache stats including active entries and TTL configuration.
    This endpoint is public (no auth required) for monitoring purposes.
    """
    stats = get_cache_stats()
    return {
        "cache_enabled": True,  # SQLite cache is always available
        "cache_type": "sqlite",
        "statistics": stats,
        "message": "SQLite cache is working normally"
    }

# ============================================================================
# Authentication Endpoints
# ============================================================================

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class CreateAPIKeyRequest(BaseModel):
    name: str
    expires_days: Optional[int] = None

class APIKeyResponse(BaseModel):
    api_key: str  # Only returned on creation
    name: str
    created_at: str

class APIKeyListItem(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: str
    last_used: Optional[str]
    expires_at: Optional[str]

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), response: Response = None):
    """Login with username and password. Sets HTTP-only cookie."""
    from fastapi import Response

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )

    # Create response
    if response is None:
        from fastapi import Response
        response = Response()

    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=os.getenv("ENVIRONMENT") == "production",  # HTTPS only in production
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )

    return {
        "message": "Login successful",
        "username": user["username"]
    }

@app.post("/api/auth/logout")
async def logout(response: Response = None):
    """Logout by clearing the authentication cookie."""
    from fastapi import Response

    if response is None:
        response = Response()

    # Clear the cookie
    response.delete_cookie(key="access_token", path="/")

    return {"message": "Logout successful"}

@app.post("/api/auth/api-keys", response_model=APIKeyResponse)
async def create_new_api_key(
    request: CreateAPIKeyRequest,
    current_user: Dict = Depends(verify_auth)
):
    """Create a new API key for the authenticated user."""
    from datetime import datetime

    # Generate API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)

    # Calculate expiration
    expires_at = None
    if request.expires_days:
        expires_at = (datetime.utcnow() + timedelta(days=request.expires_days)).isoformat()

    # Save to database
    key_id = create_api_key(
        key_hash=key_hash,
        name=request.name,
        user_id=current_user["id"],
        expires_at=expires_at
    )

    return {
        "api_key": api_key,  # Only shown once!
        "name": request.name,
        "created_at": datetime.utcnow().isoformat()
    }

@app.get("/api/auth/api-keys", response_model=List[APIKeyListItem])
async def get_api_keys(current_user: Dict = Depends(verify_auth)):
    """List all API keys for the authenticated user."""
    keys = list_api_keys(current_user["id"])
    return keys

@app.delete("/api/auth/api-keys/{key_id}")
async def revoke_api_key_endpoint(
    key_id: int,
    current_user: Dict = Depends(verify_auth)
):
    """Revoke an API key."""
    success = revoke_api_key(key_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key revoked successfully"}

# ============================================================================
# Scene Generation Endpoints
# ============================================================================

def generate_scene(prompt: str) -> Scene:
    """Generate a physics scene from a text prompt using AI."""
    print(f"ai_client is None: {ai_client is None}")
    # For demo purposes, return a simple test scene if AI client is not configured
    if not ai_client:
        print("Warning: Using demo scene generation (AI client not configured)")
        return create_demo_scene(prompt)

    # Check cache first
    cache_key = hashlib.sha256(prompt.encode()).hexdigest()
    if cache_key in scene_cache:
        try:
            return Scene.parse_raw(scene_cache[cache_key])
        except Exception:
            pass  # Cache corrupted, regenerate

    # Create prompt template
    system_prompt = """You are a physics scene generator. Create realistic 3D physics scenes based on text descriptions.

Generate scenes with 2-8 objects that can interact physically. Each object should have:
- Realistic physics properties (mass, friction, restitution)
- Appropriate visual properties (color, shape)
- Sensible initial positions and orientations

Supported shapes: "Box", "Sphere", "Cylinder"
Colors should be hex codes like "#ff0000" for red

Return ONLY valid JSON matching this schema:
{
  "objects": {
    "object_id": {
      "id": "object_id",
      "transform": {
        "position": {"x": float, "y": float, "z": float},
        "rotation": {"x": float, "y": float, "z": float},
        "scale": {"x": float, "y": float, "z": float}
      },
      "physicsProperties": {
        "mass": float,
        "friction": float,
        "restitution": float
      },
      "visualProperties": {
        "color": "hex_color",
        "shape": "Box|Sphere|Cylinder"
      }
    }
  }
}

Make scenes physically realistic and interesting to simulate."""

    user_prompt = f"Generate a physics scene for: {prompt}"

    try:
        # Use Claude via Replicate HTTP API
        headers = {
            "Authorization": f"Bearer {ai_client['api_key']}",
            "Content-Type": "application/json"
        }

        payload = {
            "input": {
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "max_tokens": 2000,
                "temperature": 0.7
            }
        }

        response = requests.post(
            "https://api.replicate.com/v1/models/anthropic/claude-3.5-sonnet/predictions",
            headers=headers,
            json=payload,
            timeout=60
        )
        # Log the response for debugging
        print(f"Replicate API response status: {response.status_code}")
        if response.status_code != 200 and response.status_code != 201:
            print(f"Replicate API error response: {response.text}")

        response.raise_for_status()

        result = response.json()

        # Wait for the prediction to complete
        prediction_url = result.get("urls", {}).get("get")
        if not prediction_url:
            print(f"Error: No prediction URL in response: {result}")
            raise HTTPException(status_code=500, detail="No prediction URL returned")

        print(f"Polling prediction at: {prediction_url}")

        # Poll for completion
        import time
        max_attempts = 120  # Increased timeout for Claude
        for attempt in range(max_attempts):
            pred_response = requests.get(prediction_url, headers=headers)
            pred_response.raise_for_status()
            pred_data = pred_response.json()

            status = pred_data.get("status")
            print(f"Attempt {attempt + 1}/{max_attempts}: Status = {status}")

            if status == "succeeded":
                output = pred_data.get("output")
                print(f"Raw output type: {type(output)}")
                print(f"Raw output: {output}")

                if isinstance(output, list):
                    scene_json = "".join(output).strip()
                elif isinstance(output, str):
                    scene_json = output.strip()
                else:
                    print(f"Unexpected output type: {type(output)}, value: {output}")
                    raise HTTPException(status_code=500, detail=f"Unexpected output format: {type(output)}")

                print(f"Scene JSON (first 200 chars): {scene_json[:200]}")
                break
            elif status in ["failed", "canceled"]:
                error = pred_data.get("error", "Unknown error")
                print(f"Prediction failed: {error}")
                raise HTTPException(status_code=500, detail=f"Prediction failed: {error}")

            time.sleep(2)  # Poll every 2 seconds
        else:
            print(f"Prediction timed out after {max_attempts} attempts")
            raise HTTPException(status_code=500, detail="Prediction timed out")

        # Clean up JSON response (remove markdown code blocks if present)
        if scene_json.startswith("```json"):
            scene_json = scene_json[7:]
        if scene_json.endswith("```"):
            scene_json = scene_json[:-3]
        scene_json = scene_json.strip()

        # Parse and validate the scene
        scene_data = json.loads(scene_json)
        scene = Scene(**scene_data)

        # Skip validation for now - it's too strict
        # validation = validate_with_genesis(scene)
        # if not validation.valid:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Generated scene is not stable: {validation.message}"
        #     )

        # Cache the result
        scene_cache[cache_key] = scene.json()

        return scene

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON response from AI: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

def create_demo_scene(prompt: str) -> Scene:
    """Create a demo scene for testing when AI is not available."""
    # Create a simple demo scene with a few objects
    objects = {
        "box1": PhysicsObject(
            id="box1",
            transform=Transform(
                position=Vec3(x=0, y=5, z=0),
                rotation=Vec3(x=0, y=0, z=0),
                scale=Vec3(x=1, y=1, z=1)
            ),
            physicsProperties=PhysicsProperties(
                mass=1.0,
                friction=0.5,
                restitution=0.3
            ),
            visualProperties=VisualProperties(
                color="#ff0000",
                shape="Box"
            )
        ),
        "sphere1": PhysicsObject(
            id="sphere1",
            transform=Transform(
                position=Vec3(x=2, y=8, z=0),
                rotation=Vec3(x=0, y=0, z=0),
                scale=Vec3(x=1, y=1, z=1)
            ),
            physicsProperties=PhysicsProperties(
                mass=0.5,
                friction=0.2,
                restitution=0.8
            ),
            visualProperties=VisualProperties(
                color="#0000ff",
                shape="Sphere"
            )
        ),
        "ground": PhysicsObject(
            id="ground",
            transform=Transform(
                position=Vec3(x=0, y=-0.5, z=0),
                rotation=Vec3(x=0, y=0, z=0),
                scale=Vec3(x=10, y=1, z=10)
            ),
            physicsProperties=PhysicsProperties(
                mass=0.0,  # Static ground
                friction=0.8,
                restitution=0.1
            ),
            visualProperties=VisualProperties(
                color="#888888",
                shape="Box"
            )
        )
    }

    return Scene(objects=objects)

def validate_with_genesis(scene: Scene) -> ValidationResult:
    """Validate scene stability using geometric analysis."""
    try:
        # Check for unsupported shapes
        for obj_id, obj in scene.objects.items():
            if obj.visualProperties.shape not in ["Box", "Sphere"]:
                return ValidationResult(
                    valid=False,
                    message=f"Unsupported shape: {obj.visualProperties.shape}",
                    details={"unsupported_shape": obj.visualProperties.shape}
                )

        # Check for overlapping objects (simple geometric validation)
        overlapping_pairs = []
        objects_list = list(scene.objects.items())

        for i, (id1, obj1) in enumerate(objects_list):
            for j, (id2, obj2) in enumerate(objects_list[i+1:], i+1):
                # Skip ground objects (mass = 0)
                if obj1.physicsProperties.mass == 0 or obj2.physicsProperties.mass == 0:
                    continue

                # Calculate distance between centers
                dx = obj1.transform.position.x - obj2.transform.position.x
                dy = obj1.transform.position.y - obj2.transform.position.y
                dz = obj1.transform.position.z - obj2.transform.position.z
                distance = (dx**2 + dy**2 + dz**2)**0.5

                # Calculate minimum separation needed
                if obj1.visualProperties.shape == "Box" and obj2.visualProperties.shape == "Box":
                    # Box-box collision: check if bounding boxes overlap
                    min_sep_x = (obj1.transform.scale.x + obj2.transform.scale.x) / 2
                    min_sep_y = (obj1.transform.scale.y + obj2.transform.scale.y) / 2
                    min_sep_z = (obj1.transform.scale.z + obj2.transform.scale.z) / 2

                    if (abs(dx) < min_sep_x and abs(dy) < min_sep_y and abs(dz) < min_sep_z):
                        overlapping_pairs.append((id1, id2))

                elif obj1.visualProperties.shape == "Sphere" and obj2.visualProperties.shape == "Sphere":
                    # Sphere-sphere collision
                    min_distance = (obj1.transform.scale.x + obj2.transform.scale.x) / 2  # Assume uniform scale
                    if distance < min_distance:
                        overlapping_pairs.append((id1, id2))

                else:
                    # Mixed sphere-box: approximate with sphere radius
                    sphere_obj = obj1 if obj1.visualProperties.shape == "Sphere" else obj2
                    box_obj = obj2 if obj1.visualProperties.shape == "Sphere" else obj1

                    sphere_radius = sphere_obj.transform.scale.x / 2
                    box_half_size = max(box_obj.transform.scale.x, box_obj.transform.scale.y, box_obj.transform.scale.z) / 2

                    min_distance = sphere_radius + box_half_size
                    if distance < min_distance:
                        overlapping_pairs.append((id1, id2))

        # Check for objects too high (likely to fall unstably)
        high_objects = []
        for obj_id, obj in scene.objects.items():
            if obj.physicsProperties.mass > 0 and obj.transform.position.y > 5.0:
                high_objects.append(obj_id)

        # Validate results
        issues = []
        if overlapping_pairs:
            issues.append(f"Overlapping objects: {overlapping_pairs}")
        if high_objects:
            issues.append(f"Objects too high (unstable): {high_objects}")

        if issues:
            return ValidationResult(
                valid=False,
                message="Scene has stability issues: " + "; ".join(issues),
                details={
                    "overlapping_pairs": overlapping_pairs,
                    "high_objects": high_objects,
                    "max_height_threshold": 5.0
                }
            )
        else:
            return ValidationResult(
                valid=True,
                message="Scene appears geometrically stable",
                details={"checked_objects": len(scene.objects)}
            )

    except Exception as e:
        return ValidationResult(
            valid=False,
            message=f"Validation failed: {str(e)}",
            details={"error": str(e)}
        )

@app.post("/api/generate")
async def api_generate_scene(
    request: GenerateRequest,
    current_user: Dict = Depends(verify_auth)
):
    """Generate a physics scene from a text prompt. Optionally links to creative brief. Requires authentication."""
    try:
        # If brief_id is provided, validate ownership and use brief context
        brief_context = None
        if request.brief_id:
            from .database import get_creative_brief
            brief = get_creative_brief(request.brief_id, current_user["id"])
            if not brief:
                raise HTTPException(status_code=404, detail="Brief not found or access denied")
            brief_context = brief

        scene = generate_scene(request.prompt)
        scene_dict = scene.dict()

        # Save to database with brief linkage
        metadata = {
            "source": "generate",
            "user_id": current_user["id"]
        }
        if request.brief_id:
            metadata["brief_id"] = request.brief_id

        scene_id = save_generated_scene(
            prompt=request.prompt,
            scene_data=scene_dict,
            model="claude-3.5-sonnet",
            metadata=metadata
        )

        # Add scene_id to response
        scene_dict["_id"] = scene_id
        scene_dict["_brief_id"] = request.brief_id

        return scene_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene generation failed: {str(e)}")

@app.post("/api/validate")
async def api_validate_scene(
    scene: Scene,
    current_user: Dict = Depends(verify_auth)
):
    """Validate a physics scene for stability using Genesis simulation. Requires authentication."""
    try:
        result = validate_with_genesis(scene)
        return result.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene validation failed: {str(e)}")

class RefineRequest(BaseModel):
    scene: Scene
    prompt: str

class VideoModel(BaseModel):
    id: str
    name: str
    description: str
    input_schema: Optional[Dict] = None

class RunVideoRequest(BaseModel):
    model_id: str
    input: Dict[str, Any]  # Accepts strings, numbers, bools, etc.
    collection: Optional[str] = None
    version: Optional[str] = None  # Model version ID for reliable predictions
    brief_id: Optional[str] = None  # Link to creative brief for context

class RunImageRequest(BaseModel):
    model_id: str
    input: Dict[str, Any]  # Accepts strings, numbers, bools, etc.
    collection: Optional[str] = None
    version: Optional[str] = None  # Model version ID for reliable predictions
    brief_id: Optional[str] = None  # Link to creative brief for context

class ImageGenerationRequest(BaseModel):
    prompt: Optional[str] = None
    asset_id: Optional[str] = None  # Reference to uploaded asset
    image_id: Optional[int] = None  # Reference to generated image
    video_id: Optional[int] = None  # Reference to generated video (use thumbnail)
    client_id: Optional[str] = None  # For tracking ownership
    campaign_id: str  # Required - link to campaign

    @validator('prompt', 'asset_id', 'image_id', 'video_id', always=True)
    def check_at_least_one(cls, v, values):
        # Check if at least one of the required fields is provided
        has_prompt = values.get('prompt') or v
        has_asset = values.get('asset_id')
        has_image = values.get('image_id')
        has_video = values.get('video_id')

        if not any([has_prompt, has_asset, has_image, has_video]):
            raise ValueError('At least one of prompt, asset_id, image_id, or video_id must be provided')
        return v

class VideoModel(str, Enum):
    SEEDANCE = "bytedance/seedance-1-lite"
    KLING = "kwaivgi/kling-v2.1"

class AudioModel(str, Enum):
    MUSICGEN = "meta/musicgen"
    RIFFUSION = "riffusion/riffusion"

class VideoGenerationRequest(BaseModel):
    prompt: Optional[str] = None
    asset_id: Optional[str] = None  # Reference to uploaded asset
    image_id: Optional[int] = None  # Reference to generated image
    video_id: Optional[int] = None  # Reference to generated video (use thumbnail)
    client_id: Optional[str] = None  # For tracking ownership
    campaign_id: str  # Required - link to campaign
    model: VideoModel = VideoModel.SEEDANCE  # Default to seedance-1-lite

    @validator('prompt', 'asset_id', 'image_id', 'video_id', always=True)
    def check_at_least_one(cls, v, values):
        # Check if at least one of the required fields is provided
        has_prompt = values.get('prompt') or v
        has_asset = values.get('asset_id')
        has_image = values.get('image_id')
        has_video = values.get('video_id')

        if not any([has_prompt, has_asset, has_image, has_video]):
            raise ValueError('At least one of prompt, asset_id, image_id, or video_id must be provided')
        return v

class AudioGenerationRequest(BaseModel):
    prompt: str  # Required for audio generation
    client_id: Optional[str] = None  # For tracking ownership
    campaign_id: str  # Required - link to campaign
    model: AudioModel = AudioModel.MUSICGEN  # Default to MusicGen
    duration: Optional[int] = 8  # Duration in seconds (default 8)

class GenesisRenderRequest(BaseModel):
    scene: Scene
    duration: float = 5.0
    fps: int = 60
    resolution: tuple[int, int] = (1920, 1080)
    quality: str = "high"  # "draft", "high", "ultra"
    camera_config: Optional[Dict] = None
    scene_context: Optional[str] = None

def refine_scene(scene: Scene, prompt: str) -> Scene:
    """Refine an existing physics scene based on a text prompt using AI."""
    print(f"Refining scene with prompt: {prompt}")
    # For demo purposes, return the original scene if AI client is not configured
    if not ai_client:
        print("Warning: Using demo scene refinement (AI client not configured)")
        return scene

    # Create cache key from scene and prompt
    scene_str = scene.json()
    cache_key = hashlib.sha256(f"{scene_str}:{prompt}".encode()).hexdigest()

    if cache_key in scene_cache:
        try:
            return Scene.parse_raw(scene_cache[cache_key])
        except Exception:
            pass  # Cache corrupted, regenerate

    # Create prompt template for refinement
    system_prompt = """You are a physics scene refiner. Modify existing 3D physics scenes based on text instructions.

Given an existing scene JSON and a refinement prompt, modify the scene accordingly. You can:
- Change object colors, positions, scales, rotations
- Add new objects
- Remove objects
- Modify physics properties (mass, friction, restitution)
- Change object shapes

Return ONLY valid JSON matching the scene schema. Preserve the structure and only make the requested changes.

Scene schema:
{
  "objects": {
    "object_id": {
      "id": "object_id",
      "transform": {
        "position": {"x": float, "y": float, "z": float},
        "rotation": {"x": float, "y": float, "z": float},
        "scale": {"x": float, "y": float, "z": float}
      },
      "physicsProperties": {
        "mass": float,
        "friction": float,
        "restitution": float
      },
      "visualProperties": {
        "color": "hex_color",
        "shape": "Box|Sphere|Cylinder"
      }
    }
  }
}

Make minimal, targeted changes based on the prompt."""

    user_prompt = f"Original scene: {scene_str}\n\nRefinement request: {prompt}\n\nReturn the modified scene JSON:"

    try:
        # Use Claude via Replicate HTTP API
        headers = {
            "Authorization": f"Bearer {ai_client['api_key']}",
            "Content-Type": "application/json"
        }

        payload = {
            "input": {
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "max_tokens": 2000,
                "temperature": 0.7
            }
        }

        response = requests.post(
            "https://api.replicate.com/v1/models/anthropic/claude-3.5-sonnet/predictions",
            headers=headers,
            json=payload,
            timeout=60
        )
        # Log the response for debugging
        print(f"Replicate API response status: {response.status_code}")
        if response.status_code != 200 and response.status_code != 201:
            print(f"Replicate API error response: {response.text}")

        response.raise_for_status()

        result = response.json()

        # Wait for the prediction to complete
        prediction_url = result.get("urls", {}).get("get")
        if not prediction_url:
            raise HTTPException(status_code=500, detail="No prediction URL returned")

        # Poll for completion
        import time
        max_attempts = 120  # Increased timeout for Claude
        for attempt in range(max_attempts):
            pred_response = requests.get(prediction_url, headers=headers)
            pred_response.raise_for_status()
            pred_data = pred_response.json()

            status = pred_data.get("status")
            print(f"Refine attempt {attempt + 1}/{max_attempts}: Status = {status}")

            if status == "succeeded":
                output = pred_data.get("output")
                print(f"Raw output type: {type(output)}")

                if isinstance(output, list):
                    refined_scene_json = "".join(output).strip()
                elif isinstance(output, str):
                    refined_scene_json = output.strip()
                else:
                    print(f"Unexpected output type: {type(output)}, value: {output}")
                    raise HTTPException(status_code=500, detail=f"Unexpected output format: {type(output)}")

                print(f"Refined scene JSON (first 200 chars): {refined_scene_json[:200]}")
                break
            elif status in ["failed", "canceled"]:
                error = pred_data.get("error", "Unknown error")
                print(f"Prediction failed: {error}")
                raise HTTPException(status_code=500, detail=f"Prediction failed: {error}")

            time.sleep(2)  # Poll every 2 seconds
        else:
            print(f"Prediction timed out after {max_attempts} attempts")
            raise HTTPException(status_code=500, detail="Prediction timed out")

        # Clean up JSON response
        if refined_scene_json.startswith("```json"):
            refined_scene_json = refined_scene_json[7:]
        if refined_scene_json.endswith("```"):
            refined_scene_json = refined_scene_json[:-3]
        refined_scene_json = refined_scene_json.strip()

        # Parse and validate the refined scene
        refined_scene_data = json.loads(refined_scene_json)
        refined_scene = Scene(**refined_scene_data)

        # Skip validation for now - it's too strict
        # validation = validate_with_genesis(refined_scene)
        # if not validation.valid:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Refined scene is not stable: {validation.message}"
        #     )

        # Cache the result
        scene_cache[cache_key] = refined_scene.json()

        return refined_scene

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON response from AI: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene refinement failed: {str(e)}")

@app.post("/api/refine")
async def api_refine_scene(
    request: RefineRequest,
    current_user: Dict = Depends(verify_auth)
):
    """Refine an existing physics scene based on a text prompt. Requires authentication."""
    try:
        refined_scene = refine_scene(request.scene, request.prompt)
        return refined_scene.dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene refinement failed: {str(e)}")

# Scene history endpoints
@app.get("/api/scenes")
async def api_list_scenes(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    model: Optional[str] = Query(None),
    current_user: Dict = Depends(verify_auth)
):
    """List generated scenes with pagination and optional model filter. Requires authentication."""
    try:
        scenes = list_scenes(limit=limit, offset=offset, model=model)
        total = get_scene_count(model=model)
        return {
            "scenes": scenes,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list scenes: {str(e)}")

@app.get("/api/scenes/{scene_id}")
async def api_get_scene(
    scene_id: int,
    current_user: Dict = Depends(verify_auth)
):
    """Get a specific scene by ID. Requires authentication."""
    try:
        scene = get_scene_by_id(scene_id)
        if not scene:
            raise HTTPException(status_code=404, detail="Scene not found")
        return scene
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scene: {str(e)}")

@app.delete("/api/scenes/{scene_id}")
async def api_delete_scene(
    scene_id: int,
    current_user: Dict = Depends(verify_auth)
):
    """Delete a scene by ID. Requires authentication."""
    try:
        deleted = delete_scene(scene_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Scene not found")
        return {"success": True, "message": "Scene deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete scene: {str(e)}")

@app.get("/api/models")
async def api_get_models():
    """Get list of models that have generated scenes."""
    try:
        models = get_models_list()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@app.get("/api/replicate-models")
async def api_get_replicate_models(
    query: Optional[str] = Query(None, description="Search query"),
    cursor: Optional[str] = Query(None, description="Pagination cursor")
):
    """Get list of available models from Replicate."""
    try:
        if not ai_client:
            return {"results": DEMO_VIDEO_MODELS, "next": None}

        headers = {
            "Authorization": f"Bearer {ai_client['api_key']}",
            "Content-Type": "application/json"
        }

        # Build URL with query params
        params = []
        if cursor:
            params.append(f"cursor={cursor}")
        if query:
            params.append(f"query={query}")

        # Use Replicate's models API
        url = "https://api.replicate.com/v1/models"
        if params:
            url += "?" + "&".join(params)

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Format the response
        models = []
        results = data.get("results", [])

        for model_data in results:
            models.append({
                "owner": model_data.get("owner"),
                "name": model_data.get("name"),
                "description": model_data.get("description"),
                "url": model_data.get("url"),
                "cover_image_url": model_data.get("cover_image_url"),
                "latest_version": model_data.get("latest_version", {}).get("id") if model_data.get("latest_version") else None,
                "run_count": model_data.get("run_count", 0),
            })

        return {
            "results": models,
            "next": data.get("next")
        }

    except Exception as e:
        print(f"Error fetching models from Replicate: {str(e)}")
        import traceback
        traceback.print_exc()
        # Fallback to demo models
        return {"results": DEMO_VIDEO_MODELS, "next": None}

@app.get("/api/video-models")
async def api_get_video_models(
    collection: Optional[str] = Query("text-to-video", description="Collection slug: text-to-video, image-to-video, etc.")
):
    """Get video generation models from Replicate collections API."""
    try:
        if not ai_client:
            # Fallback to demo models if no API key
            return {"models": [model for model in DEMO_VIDEO_MODELS]}

        headers = {
            "Authorization": f"Bearer {ai_client['api_key']}",
            "Content-Type": "application/json"
        }

        # Use collections API with the specified collection slug
        url = f"https://api.replicate.com/v1/collections/{collection}"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Format the models from the collection
        models = []
        for model_data in data.get("models", []):
            model_id = f"{model_data.get('owner')}/{model_data.get('name')}"
            models.append({
                "id": model_id,
                "name": model_data.get("name", ""),
                "owner": model_data.get("owner", ""),
                "description": model_data.get("description"),
                "cover_image_url": model_data.get("cover_image_url"),
                "latest_version": model_data.get("latest_version", {}).get("id") if model_data.get("latest_version") else None,
                "run_count": model_data.get("run_count", 0),
                "input_schema": None  # Will be fetched when model is selected
            })

        return {"models": models}
    except Exception as e:
        print(f"Error fetching video models from collection '{collection}': {str(e)}")
        import traceback
        traceback.print_exc()
        # Fallback to demo models
        return {"models": [model for model in DEMO_VIDEO_MODELS]}

@app.get("/api/video-models/{model_owner}/{model_name}/schema")
async def api_get_model_schema(model_owner: str, model_name: str):
    """Get the input schema for a specific model."""
    try:
        if not ai_client:
            return {"input_schema": {"prompt": {"type": "string"}}}

        headers = {
            "Authorization": f"Bearer {ai_client['api_key']}",
            "Content-Type": "application/json"
        }

        # Fetch model details including schema
        url = f"https://api.replicate.com/v1/models/{model_owner}/{model_name}"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Extract input schema from latest version
        latest_version = data.get("latest_version") or {}
        version_id = latest_version.get("id")
        openapi_schema = latest_version.get("openapi_schema") or {}
        input_schema = openapi_schema.get("components", {}).get("schemas", {}).get("Input", {})

        # Extract properties and required fields
        properties = input_schema.get("properties", {})
        required_fields = input_schema.get("required", [])

        # Return schema with version ID for reliable predictions
        return {
            "input_schema": properties,
            "required": required_fields,
            "version": version_id  # Include version ID for predictions
        }
    except Exception as e:
        print(f"Error fetching model schema: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"input_schema": {"prompt": {"type": "string"}}}

def process_video_generation_background(
    video_id: int,
    prediction_url: str,
    api_key: str,
    model_id: str,
    input_params: dict,
    collection: str
):
    """Background task to poll Replicate for video generation completion."""
    import time

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = input_params.get("prompt", "")
    max_attempts = 120  # 4 minutes (2 seconds * 120)

    try:
        for attempt in range(max_attempts):
            pred_response = requests.get(prediction_url, headers=headers)
            pred_response.raise_for_status()
            pred_data = pred_response.json()

            status = pred_data.get("status")

            if status == "succeeded":
                output = pred_data.get("output", [])
                if isinstance(output, str):
                    output = [output]

                video_url = output[0] if output else ""

                if video_url:
                    # Prevent race condition: check if download already attempted
                    from .database import mark_download_attempted, mark_download_failed

                    if not mark_download_attempted(video_id):
                        print(f"Video {video_id} download already attempted by another process, skipping")
                        return

                    # Download and save video to database
                    try:
                        db_url = download_and_save_video(video_url, video_id)
                        metadata = {
                            "replicate_id": pred_data.get("id"),
                            "prediction_url": prediction_url,
                            "original_url": video_url
                        }

                        # Update database with completed video
                        update_video_status(
                            video_id=video_id,
                            status="completed",
                            video_url=db_url,
                            metadata=metadata
                        )
                        print(f"Video {video_id} completed successfully")
                        return

                    except Exception as e:
                        # Download failed after all retries - mark as permanently failed
                        error_msg = f"Failed to download video after retries: {str(e)}"
                        print(error_msg)
                        mark_download_failed(video_id, error_msg)
                        return
                else:
                    # No video URL in response
                    metadata = {
                        "replicate_id": pred_data.get("id"),
                        "prediction_url": prediction_url,
                        "error": "No video URL in Replicate response"
                    }
                    update_video_status(
                        video_id=video_id,
                        status="failed",
                        metadata=metadata
                    )
                    print(f"Video {video_id} failed: no output URL")
                    return

            elif status in ["failed", "canceled"]:
                error = pred_data.get("error", "Unknown error")
                metadata = {
                    "error": error,
                    "replicate_id": pred_data.get("id")
                }

                # Update database with failure
                update_video_status(
                    video_id=video_id,
                    status=status,
                    metadata=metadata
                )
                print(f"Video {video_id} {status}: {error}")
                return

            time.sleep(2)

        # Timeout
        update_video_status(
            video_id=video_id,
            status="timeout",
            metadata={"error": "Video generation timed out"}
        )
        print(f"Video {video_id} timed out")

    except Exception as e:
        print(f"Error processing video {video_id}: {str(e)}")
        import traceback
        traceback.print_exc()

        # Update database with error
        update_video_status(
            video_id=video_id,
            status="failed",
            metadata={"error": str(e)}
        )


@app.post("/api/run-video-model")
async def api_run_video_model(
    request: RunVideoRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth)
):
    """Initiate video generation and return immediately with a video ID. Requires authentication.

    Note: Input validation is handled by the frontend (Elm) which validates required fields
    against the model schema before submission. Replicate API also validates and will return
    clear error messages if inputs are invalid.
    """
    try:
        if not ai_client:
            # Demo response - create a pending video
            video_id = save_generated_video(
                prompt=request.input.get("prompt", ""),
                video_url="",
                model_id=request.model_id,
                parameters=request.input,
                collection=request.collection,
                status="processing",
                brief_id=request.brief_id
            )
            return {"video_id": video_id, "status": "processing"}

        # Basic validation: ensure we have at least a prompt or image parameter
        if not request.input.get("prompt") and not any(k for k in request.input.keys() if "image" in k.lower()):
            raise HTTPException(
                status_code=400,
                detail="Missing required input: must provide either 'prompt' or an image parameter"
            )

        headers = {
            "Authorization": f"Bearer {ai_client['api_key']}",
            "Content-Type": "application/json"
        }

        # Convert parameter types
        converted_input = {}
        for key, value in request.input.items():
            if isinstance(value, str):
                # Try to convert to int
                try:
                    converted_input[key] = int(value)
                    continue
                except ValueError:
                    pass

                # Try to convert to float
                try:
                    converted_input[key] = float(value)
                    continue
                except ValueError:
                    pass

                # Keep as string
                converted_input[key] = value
            else:
                converted_input[key] = value

        # Get the base URL for webhooks
        # In production, this should be the actual deployed URL
        base_url = settings.BASE_URL

        # Only use webhooks if we have an HTTPS URL (production)
        use_webhooks = base_url.startswith("https://")

        # Create prediction using HTTP API
        # Use version-based endpoint if version provided (more reliable)
        if request.version:
            payload = {
                "version": request.version,
                "input": converted_input,
            }
            if use_webhooks:
                payload["webhook"] = f"{base_url}/api/webhooks/replicate"
                payload["webhook_events_filter"] = ["completed"]
            url = "https://api.replicate.com/v1/predictions"
            print(f"DEBUG: Sending to Replicate API (version-based):")
            print(f"  Model: {request.model_id}")
            print(f"  Version: {request.version}")
        else:
            payload = {
                "input": converted_input,
            }
            if use_webhooks:
                payload["webhook"] = f"{base_url}/api/webhooks/replicate"
                payload["webhook_events_filter"] = ["completed"]
            url = f"https://api.replicate.com/v1/models/{request.model_id}/predictions"
            print(f"DEBUG: Sending to Replicate API (model-based):")
            print(f"  Model: {request.model_id}")

        print(f"  Input types: {[(k, type(v).__name__, v) for k, v in converted_input.items()]}")
        if use_webhooks:
            print(f"  Webhook URL: {base_url}/api/webhooks/replicate")
        else:
            print(f"  Webhook: Disabled (local development - using polling only)")
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        # Log the detailed error if request fails
        if response.status_code != 201:
            error_detail = response.text
            print(f"Replicate API Error ({response.status_code}): {error_detail}")

            try:
                error_json = response.json()
                error_msg = error_json.get("detail", error_detail)
            except:
                error_msg = error_detail

            raise HTTPException(status_code=400, detail=f"Replicate API error: {error_msg}")

        result = response.json()

        # Get the prediction URL
        prediction_url = result.get("urls", {}).get("get")
        if not prediction_url:
            raise HTTPException(status_code=500, detail="No prediction URL returned from Replicate")

        # Enhance prompt with brief context if provided
        enhanced_prompt = request.input.get("prompt", "")
        metadata = {"replicate_id": result.get("id"), "prediction_url": prediction_url}

        if request.brief_id:
            try:
                from .database import get_creative_brief
                brief = get_creative_brief(request.brief_id, current_user["id"])
                if brief:
                    # Add brief context to prompt
                    brief_context = f" [Style: {brief.get('creative_direction', {}).get('style', 'cinematic')}]"
                    enhanced_prompt += brief_context
                    metadata["brief_id"] = request.brief_id
                    print(f"Enhanced video prompt with brief context: {brief_context}")
            except Exception as e:
                print(f"Failed to enhance video prompt with brief context: {e}")

        # Create video record with "processing" status
        video_id = save_generated_video(
            prompt=enhanced_prompt,
            video_url="",  # Will be filled in when complete and downloaded
            model_id=request.model_id,
            parameters=request.input,
            collection=request.collection,
            status="processing",
            metadata=metadata,
            brief_id=request.brief_id
        )

        # Start background task to poll for completion (fallback if webhook fails)
        background_tasks.add_task(
            process_video_generation_background,
            video_id=video_id,
            prediction_url=prediction_url,
            api_key=ai_client['api_key'],
            model_id=request.model_id,
            input_params=request.input,
            collection=request.collection
        )

        # Return immediately with video ID
        return {"video_id": video_id, "status": "processing"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error initiating video generation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

def resolve_image_reference(
    asset_id: Optional[str] = None,
    image_id: Optional[int] = None,
    video_id: Optional[int] = None
) -> str:
    """
    Resolve an image reference (asset_id, image_id, or video_id) to a public URL for Replicate.

    Args:
        asset_id: Optional asset UUID
        image_id: Optional generated image ID
        video_id: Optional generated video ID

    Returns:
        Public URL to the image

    Raises:
        HTTPException: If reference is invalid, not found, or multiple references provided
    """
    # Count how many references are provided
    refs_provided = sum([asset_id is not None, image_id is not None, video_id is not None])

    if refs_provided == 0:
        raise HTTPException(
            status_code=400,
            detail="No image reference provided"
        )

    if refs_provided > 1:
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one image reference (asset_id, image_id, or video_id)"
        )

    base_url = settings.BASE_URL
    if not base_url:
        raise HTTPException(
            status_code=500,
            detail="BASE_URL not configured - cannot generate public URLs for Replicate"
        )

    # Handle asset_id
    if asset_id:
        asset = get_asset_by_id(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

        # Check if it's an image or video asset
        if asset.get('type') not in ['image', 'video']:
            raise HTTPException(
                status_code=400,
                detail=f"Asset must be an image or video, got {asset.get('type')}"
            )

        # For images, use data endpoint; for videos, use thumbnail if available
        if asset.get('type') == 'video':
            # Use thumbnail for videos
            return f"{base_url}/api/v2/assets/{asset_id}/thumbnail"
        else:
            return f"{base_url}/api/v2/assets/{asset_id}/data"

    # Handle image_id
    if image_id:
        image = get_image_by_id(image_id)
        if not image:
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found")

        # Check if image is completed
        if image.get('status') != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Image {image_id} is not completed (status: {image.get('status')})"
            )

        # Prefer Replicate's original URL (publicly accessible) over localhost
        # This allows external services like Replicate to fetch the image
        import json
        metadata = image.get('metadata')
        if metadata:
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    pass

            if isinstance(metadata, dict):
                original_url = metadata.get('original_url')
                if original_url:
                    return original_url

        # Fallback to local URL (only works if BASE_URL is publicly accessible)
        return f"{base_url}/api/images/{image_id}/data"

    # Handle video_id
    if video_id:
        video = get_video_by_id(video_id)
        if not video:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

        # Check if video is completed
        if video.get('status') != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Video {video_id} is not completed (status: {video.get('status')})"
            )

        # For videos, we'll use the thumbnail endpoint (images)
        # Since videos don't have thumbnails in the blob, we'll just use the data endpoint
        # and let Replicate handle it (it can extract frames from videos)
        return f"{base_url}/api/videos/{video_id}/data"

    # Should never reach here
    raise HTTPException(status_code=500, detail="Internal error resolving image reference")

def download_and_save_video(video_url: str, video_id: int, max_retries: int = 3) -> str:
    """
    Download a video from Replicate and save it locally with retry logic and validation.

    Args:
        video_url: URL of the video to download
        video_id: ID of the video in the database
        max_retries: Maximum number of download attempts (default: 3)

    Returns:
        str: Local file path of the downloaded video

    Raises:
        Exception: If download fails after all retries
    """
    import uuid
    import time
    from pathlib import Path

    # Create videos directory if it doesn't exist
    videos_dir = Path(__file__).parent / "DATA" / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = ".mp4"  # Default to mp4
    if video_url:
        url_ext = video_url.split(".")[-1].split("?")[0].lower()  # Remove query params
        if url_ext in ["mp4", "mov", "avi", "webm"]:
            file_ext = f".{url_ext}"

    filename = f"video_{video_id}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = videos_dir / filename

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Downloading video (attempt {attempt}/{max_retries}) from {video_url} to {file_path}")

            # Download with timeout
            response = requests.get(video_url, stream=True, timeout=300)
            response.raise_for_status()

            # Write to temporary file first
            temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
            bytes_downloaded = 0

            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)

            # Validate download
            if bytes_downloaded == 0:
                raise ValueError("Downloaded file is empty (0 bytes)")

            if bytes_downloaded < 1024:  # Less than 1KB is suspicious
                raise ValueError(f"Downloaded file is too small ({bytes_downloaded} bytes)")

            # Validate file is a video by checking magic bytes
            with open(temp_path, 'rb') as f:
                header = f.read(12)
                is_video = False

                # Check common video file signatures
                if header.startswith(b'\x00\x00\x00\x18ftypmp4') or \
                   header.startswith(b'\x00\x00\x00\x1cftypisom') or \
                   header.startswith(b'\x00\x00\x00\x14ftyp') or \
                   header[4:8] == b'ftyp':  # Generic MP4/MOV
                    is_video = True
                elif header.startswith(b'RIFF') and header[8:12] == b'AVI ':  # AVI
                    is_video = True
                elif header.startswith(b'\x1a\x45\xdf\xa3'):  # WebM/MKV
                    is_video = True

                if not is_video:
                    raise ValueError(f"Downloaded file does not appear to be a valid video (header: {header.hex()})")

            # Read the video data from temp file
            with open(temp_path, 'rb') as f:
                video_binary_data = f.read()

            # Store binary data in database
            from .database import get_db
            with get_db() as conn:
                conn.execute(
                    "UPDATE generated_videos SET video_data = ? WHERE id = ?",
                    (video_binary_data, video_id)
                )
                conn.commit()

            # Delete temp file - we only store in database now
            temp_path.unlink()

            print(f"Video downloaded successfully: {bytes_downloaded} bytes stored in DB (video_id={video_id})")
            # Return a database URL instead of file path
            return f"/api/videos/{video_id}/data"

        except Exception as e:
            last_error = e
            print(f"Download attempt {attempt} failed: {e}")

            # Clean up temp file if it exists
            temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
            if temp_path.exists():
                temp_path.unlink()

            if attempt < max_retries:
                # Exponential backoff: 2, 4, 8 seconds
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"All {max_retries} download attempts failed for video {video_id}")

    # All retries failed
    raise Exception(f"Failed to download video after {max_retries} attempts: {last_error}")

@app.post("/api/webhooks/replicate")
async def replicate_webhook(request: dict, background_tasks: BackgroundTasks):
    """Handle webhook from Replicate when a prediction completes."""
    try:
        print(f"Received Replicate webhook: {json.dumps(request, indent=2)}")

        replicate_id = request.get("id")
        status = request.get("status")
        output = request.get("output")

        if not replicate_id:
            print("No replicate_id in webhook")
            return {"status": "ignored"}

        # Find the video, image, or audio by replicate_id in metadata
        from .database import get_db
        video_id = None
        image_id = None
        audio_id = None

        with get_db() as conn:
            # Check videos first
            row = conn.execute(
                """
                SELECT id FROM generated_videos
                WHERE json_extract(metadata, '$.replicate_id') = ?
                """,
                (replicate_id,)
            ).fetchone()

            if row:
                video_id = row["id"]
            else:
                # Check images
                row = conn.execute(
                    """
                    SELECT id FROM generated_images
                    WHERE json_extract(metadata, '$.replicate_id') = ?
                    """,
                    (replicate_id,)
                ).fetchone()

                if row:
                    image_id = row["id"]
                else:
                    # Check audio
                    row = conn.execute(
                        """
                        SELECT id FROM generated_audio
                        WHERE json_extract(metadata, '$.replicate_id') = ?
                        """,
                        (replicate_id,)
                    ).fetchone()

                    if row:
                        audio_id = row["id"]

            if not video_id and not image_id and not audio_id:
                print(f"No video, image, or audio found for replicate_id: {replicate_id}")
                return {"status": "ignored"}

        if video_id:
            print(f"Found video_id: {video_id} for replicate_id: {replicate_id}")

            if status == "succeeded" and output:
                # Get video URL from output
                video_url = output[0] if isinstance(output, list) else output

                if video_url:
                    # Download and save video in background with race condition prevention
                    def download_video_task():
                        from .database import mark_download_attempted, mark_download_failed

                        # Prevent race condition: check if download already attempted
                        if not mark_download_attempted(video_id):
                            print(f"Video {video_id} download already attempted by another process (webhook), skipping")
                            return

                        try:
                            db_url = download_and_save_video(video_url, video_id)
                            # Update database with DB URL
                            update_video_status(
                                video_id=video_id,
                                status="completed",
                                video_url=db_url,
                                metadata={"replicate_id": replicate_id, "original_url": video_url}
                            )
                            print(f"Video {video_id} saved to database via webhook")
                        except Exception as e:
                            # Download failed after all retries - mark as permanently failed
                            error_msg = f"Failed to download video after retries: {str(e)}"
                            print(f"Webhook: {error_msg}")
                            mark_download_failed(video_id, error_msg)

                    background_tasks.add_task(download_video_task)

            elif status in ["failed", "canceled"]:
                error = request.get("error", "Unknown error")
                update_video_status(
                    video_id=video_id,
                    status=status,
                    metadata={"error": error, "replicate_id": replicate_id}
                )

        elif image_id:
            print(f"Found image_id: {image_id} for replicate_id: {replicate_id}")

            if status == "succeeded" and output:
                # Get image URL from output
                image_url = output[0] if isinstance(output, list) else output

                if image_url:
                    # Download and save image in background with race condition prevention
                    def download_image_task():
                        from .database import mark_image_download_attempted, mark_image_download_failed

                        # Prevent race condition: check if download already attempted
                        if not mark_image_download_attempted(image_id):
                            print(f"Image {image_id} download already attempted by another process (webhook), skipping")
                            return

                        try:
                            db_url = download_and_save_image(image_url, image_id)
                            # Update database with DB URL
                            update_image_status(
                                image_id=image_id,
                                status="completed",
                                image_url=db_url,
                                metadata={"replicate_id": replicate_id, "original_url": image_url}
                            )
                            print(f"Image {image_id} saved to database via webhook")
                        except Exception as e:
                            # Download failed after all retries - mark as permanently failed
                            error_msg = f"Failed to download image after retries: {str(e)}"
                            print(f"Webhook: {error_msg}")
                            mark_image_download_failed(image_id, error_msg)

                    background_tasks.add_task(download_image_task)

            elif status in ["failed", "canceled"]:
                error = request.get("error", "Unknown error")
                update_image_status(
                    image_id=image_id,
                    status=status,
                    metadata={"error": error, "replicate_id": replicate_id}
                )

        elif audio_id:
            print(f"Found audio_id: {audio_id} for replicate_id: {replicate_id}")

            if status == "succeeded" and output:
                # Get audio URL from output (handle different formats)
                audio_url = None
                if isinstance(output, str):
                    audio_url = output
                elif isinstance(output, list) and len(output) > 0:
                    audio_url = output[0]
                elif isinstance(output, dict):
                    audio_url = output.get("audio") or output.get("file") or output.get("output")

                if audio_url:
                    # Download and save audio in background with race condition prevention
                    def download_audio_task():
                        from .database import mark_audio_download_attempted, mark_audio_download_failed

                        # Prevent race condition: check if download already attempted
                        if not mark_audio_download_attempted(audio_id):
                            print(f"Audio {audio_id} download already attempted by another process (webhook), skipping")
                            return

                        try:
                            db_url = download_and_save_audio(audio_url, audio_id)
                            # Update database with DB URL
                            update_audio_status(
                                audio_id=audio_id,
                                status="completed",
                                audio_url=db_url,
                                metadata={"replicate_id": replicate_id, "original_url": audio_url}
                            )
                            print(f"Audio {audio_id} saved to database via webhook")
                        except Exception as e:
                            # Download failed after all retries - mark as permanently failed
                            error_msg = f"Failed to download audio after retries: {str(e)}"
                            print(f"Webhook: {error_msg}")
                            mark_audio_download_failed(audio_id, error_msg)

                    background_tasks.add_task(download_audio_task)

            elif status in ["failed", "canceled"]:
                error = request.get("error", "Unknown error")
                update_audio_status(
                    audio_id=audio_id,
                    status=status,
                    metadata={"error": error, "replicate_id": replicate_id}
                )

        return {"status": "processed"}

    except Exception as e:
        print(f"Error processing webhook: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.get("/api/videos")
async def api_list_videos(
    background_tasks: BackgroundTasks,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    model_id: Optional[str] = Query(None),
    collection: Optional[str] = Query(None),
    current_user: Dict = Depends(verify_auth)
):
    """
    List generated videos from the database. Requires authentication.

    Automatically retries fetching videos stuck in 'processing' status when gallery refreshes.
    """
    from .database import list_videos
    from datetime import datetime, timedelta

    videos = list_videos(limit=limit, offset=offset, model_id=model_id, collection=collection)

    # Auto-retry any videos in 'processing' status on gallery refresh
    for video in videos:
        if video.get("status") != "processing":
            continue

        # Get metadata
        metadata = video.get("metadata", {})
        if isinstance(metadata, str):
            try:
                import json
                metadata = json.loads(metadata)
            except:
                metadata = {}

        prediction_url = metadata.get("prediction_url")
        replicate_id = metadata.get("replicate_id")

        if not prediction_url and not replicate_id:
            continue

        # Construct prediction URL if we only have ID
        if not prediction_url and replicate_id:
            prediction_url = f"https://api.replicate.com/v1/predictions/{replicate_id}"

        video_id = video["id"]

        # Auto-retry in background
        def auto_retry_task(vid_id, pred_url):
            import requests

            api_key = settings.REPLICATE_API_KEY
            if not api_key:
                return

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            try:
                # Check prediction status
                response = requests.get(pred_url, headers=headers, timeout=10)
                response.raise_for_status()
                pred_data = response.json()

                status = pred_data.get("status")

                if status == "succeeded":
                    output = pred_data.get("output", [])
                    if isinstance(output, str):
                        output = [output]

                    video_url = output[0] if output else ""

                    if video_url:
                        # Download and save
                        db_url = download_and_save_video(video_url, vid_id)
                        update_video_status(
                            video_id=vid_id,
                            status="completed",
                            video_url=db_url,
                            metadata={
                                "replicate_id": pred_data.get("id"),
                                "prediction_url": pred_url,
                                "original_url": video_url,
                                "auto_retried": True
                            }
                        )
                        print(f"Auto-retry: Video {vid_id} completed")
                elif status in ["failed", "canceled"]:
                    error = pred_data.get("error", "Unknown error")
                    update_video_status(
                        video_id=vid_id,
                        status=status,
                        metadata={"error": error, "replicate_id": pred_data.get("id"), "auto_retried": True}
                    )
                    print(f"Auto-retry: Video {vid_id} {status}")
                # If still processing, leave as-is

            except Exception as e:
                print(f"Auto-retry error for video {vid_id}: {e}")

        background_tasks.add_task(auto_retry_task, video_id, prediction_url)

    return {"videos": videos}

@app.get("/api/videos/{video_id}")
async def api_get_video(
    video_id: int,
    current_user: Dict = Depends(verify_auth)
):
    """Get a specific video by ID (used for polling video status). Requires authentication."""
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
    return video

# ============================================================================
# Image Generation Endpoints
# ============================================================================

@app.get("/api/image-models")
async def api_get_image_models(
    collection: Optional[str] = Query("text-to-image", description="Collection slug: text-to-image, super-resolution, etc.")
):
    """Get image generation models from Replicate collections API."""
    try:
        if not ai_client:
            # Fallback to demo models if no API key
            return {"models": []}

        headers = {
            "Authorization": f"Bearer {ai_client['api_key']}",
            "Content-Type": "application/json"
        }

        # Use collections API with the specified collection slug
        url = f"https://api.replicate.com/v1/collections/{collection}"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Format the models from the collection
        models = []
        for model_data in data.get("models", []):
            model_id = f"{model_data.get('owner')}/{model_data.get('name')}"
            models.append({
                "id": model_id,
                "name": model_data.get("name", ""),
                "owner": model_data.get("owner", ""),
                "description": model_data.get("description"),
                "cover_image_url": model_data.get("cover_image_url"),
                "latest_version": model_data.get("latest_version", {}).get("id") if model_data.get("latest_version") else None,
                "run_count": model_data.get("run_count", 0),
                "input_schema": None  # Will be fetched when model is selected
            })

        # If the collection is super-resolution, ensure the configured upscaler is included
        # This allows flexibility to change upscaler models via UPSCALER_MODEL env variable
        if collection == "super-resolution":
            upscaler_model_id = settings.UPSCALER_MODEL
            # Check if it's already in the list
            if not any(m["id"] == upscaler_model_id for m in models):
                # Add it manually with dynamic name based on model ID
                owner, name = upscaler_model_id.split("/")
                display_name = name.replace("-", " ").replace("_", " ").title()
                models.insert(0, {
                    "id": upscaler_model_id,
                    "name": display_name,
                    "owner": owner,
                    "description": "High-resolution AI image upscaler with stunning detail and quality",
                    "cover_image_url": None,
                    "latest_version": None,
                    "run_count": 0,
                    "input_schema": None
                })

        return {"models": models}
    except Exception as e:
        print(f"Error fetching image models from collection '{collection}': {str(e)}")
        import traceback
        traceback.print_exc()
        # Fallback to empty list
        return {"models": []}

@app.get("/api/image-models/{model_owner}/{model_name}/schema")
async def api_get_image_model_schema(model_owner: str, model_name: str):
    """Get the input schema for a specific image model."""
    try:
        if not ai_client:
            return {"input_schema": {"prompt": {"type": "string"}}}

        headers = {
            "Authorization": f"Bearer {ai_client['api_key']}",
            "Content-Type": "application/json"
        }

        # Fetch model details including schema
        url = f"https://api.replicate.com/v1/models/{model_owner}/{model_name}"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Extract input schema from latest version
        latest_version = data.get("latest_version") or {}
        version_id = latest_version.get("id")
        openapi_schema = latest_version.get("openapi_schema") or {}
        input_schema = openapi_schema.get("components", {}).get("schemas", {}).get("Input", {})

        # Extract properties and required fields
        properties = input_schema.get("properties", {})
        required_fields = input_schema.get("required", [])

        # Return schema with version ID for reliable predictions
        return {
            "input_schema": properties,
            "required": required_fields,
            "version": version_id  # Include version ID for predictions
        }
    except Exception as e:
        print(f"Error fetching image model schema: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"input_schema": {"prompt": {"type": "string"}}}

def process_image_generation_background(
    image_id: int,
    prediction_url: str,
    api_key: str,
    model_id: str,
    input_params: dict,
    collection: str
):
    """Background task to poll Replicate for image generation completion."""
    import time

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = input_params.get("prompt", "")
    max_attempts = 120  # 4 minutes (2 seconds * 120)

    try:
        for attempt in range(max_attempts):
            pred_response = requests.get(prediction_url, headers=headers)
            pred_response.raise_for_status()
            pred_data = pred_response.json()

            status = pred_data.get("status")

            if status == "succeeded":
                output = pred_data.get("output", [])
                if isinstance(output, str):
                    output = [output]

                image_url = output[0] if output else ""

                if image_url:
                    # Prevent race condition: check if download already attempted
                    from .database import mark_image_download_attempted, mark_image_download_failed

                    if not mark_image_download_attempted(image_id):
                        print(f"Image {image_id} download already attempted by another process, skipping")
                        return

                    # Download and save image to database
                    try:
                        db_url = download_and_save_image(image_url, image_id)
                        metadata = {
                            "replicate_id": pred_data.get("id"),
                            "prediction_url": prediction_url,
                            "original_url": image_url
                        }

                        # Update database with completed image
                        update_image_status(
                            image_id=image_id,
                            status="completed",
                            image_url=db_url,
                            metadata=metadata
                        )
                        print(f"Image {image_id} completed successfully")
                        return

                    except Exception as e:
                        # Download failed after all retries - mark as permanently failed
                        error_msg = f"Failed to download image after retries: {str(e)}"
                        print(error_msg)
                        mark_image_download_failed(image_id, error_msg)
                        return
                else:
                    # No image URL in response
                    metadata = {
                        "replicate_id": pred_data.get("id"),
                        "prediction_url": prediction_url,
                        "error": "No image URL in Replicate response"
                    }
                    update_image_status(
                        image_id=image_id,
                        status="failed",
                        metadata=metadata
                    )
                    print(f"Image {image_id} failed: no output URL")
                    return

            elif status in ["failed", "canceled"]:
                error = pred_data.get("error", "Unknown error")
                metadata = {
                    "error": error,
                    "replicate_id": pred_data.get("id")
                }

                # Update database with failure
                update_image_status(
                    image_id=image_id,
                    status=status,
                    metadata=metadata
                )
                print(f"Image {image_id} {status}: {error}")
                return

            time.sleep(2)

        # Timeout
        update_image_status(
            image_id=image_id,
            status="timeout",
            metadata={"error": "Image generation timed out"}
        )
        print(f"Image {image_id} timed out")

    except Exception as e:
        print(f"Error processing image {image_id}: {str(e)}")
        import traceback
        traceback.print_exc()

        # Update database with error
        update_image_status(
            image_id=image_id,
            status="failed",
            metadata={"error": str(e)}
        )

def process_audio_generation_background(
    audio_id: int,
    prediction_url: str,
    api_key: str,
    model_id: str,
    input_params: dict,
    collection: str
):
    """Background task to poll Replicate for audio generation completion."""
    import time

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = input_params.get("prompt", "")
    max_attempts = 180  # 6 minutes (2 seconds * 180) - audio generation can take longer

    try:
        for attempt in range(max_attempts):
            pred_response = requests.get(prediction_url, headers=headers)
            pred_response.raise_for_status()
            pred_data = pred_response.json()

            status = pred_data.get("status")

            if status == "succeeded":
                output = pred_data.get("output")

                # Handle different output formats
                audio_url = None
                if isinstance(output, str):
                    audio_url = output
                elif isinstance(output, list) and len(output) > 0:
                    audio_url = output[0]
                elif isinstance(output, dict):
                    # Some models return output as dict with 'audio' or 'file' key
                    audio_url = output.get("audio") or output.get("file") or output.get("output")

                if audio_url:
                    # Prevent race condition: check if download already attempted
                    from .database import mark_audio_download_attempted, mark_audio_download_failed

                    if not mark_audio_download_attempted(audio_id):
                        print(f"Audio {audio_id} download already attempted by another process, skipping")
                        return

                    # Download and save audio to database
                    try:
                        db_url = download_and_save_audio(audio_url, audio_id)

                        # Extract duration if available
                        duration = pred_data.get("metrics", {}).get("predict_time")

                        metadata = {
                            "replicate_id": pred_data.get("id"),
                            "prediction_url": prediction_url,
                            "original_url": audio_url,
                            "metrics": pred_data.get("metrics", {})
                        }

                        # Update database with completed audio
                        update_audio_status(
                            audio_id=audio_id,
                            status="completed",
                            audio_url=db_url,
                            metadata=metadata
                        )
                        print(f"Audio {audio_id} completed successfully")
                        return

                    except Exception as e:
                        # Download failed after all retries - mark as permanently failed
                        error_msg = f"Failed to download audio after retries: {str(e)}"
                        print(error_msg)
                        mark_audio_download_failed(audio_id, error_msg)
                        return
                else:
                    # No audio URL in response
                    metadata = {
                        "replicate_id": pred_data.get("id"),
                        "prediction_url": prediction_url,
                        "error": "No audio URL in Replicate response"
                    }
                    update_audio_status(
                        audio_id=audio_id,
                        status="failed",
                        metadata=metadata
                    )
                    print(f"Audio {audio_id} failed: no output URL")
                    return

            elif status in ["failed", "canceled"]:
                error = pred_data.get("error", "Unknown error")
                metadata = {
                    "error": error,
                    "replicate_id": pred_data.get("id")
                }

                # Update database with failure
                update_audio_status(
                    audio_id=audio_id,
                    status=status,
                    metadata=metadata
                )
                print(f"Audio {audio_id} {status}: {error}")
                return

            time.sleep(2)

        # Timeout
        update_audio_status(
            audio_id=audio_id,
            status="timeout",
            metadata={"error": "Audio generation timed out"}
        )
        print(f"Audio {audio_id} timed out")

    except Exception as e:
        print(f"Error processing audio {audio_id}: {str(e)}")
        import traceback
        traceback.print_exc()

        # Update database with error
        update_audio_status(
            audio_id=audio_id,
            status="failed",
            metadata={"error": str(e)}
        )

@app.post("/api/run-image-model")
async def api_run_image_model(
    request: RunImageRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth)
):
    """Initiate image generation and return immediately with an image ID. Requires authentication.

    This endpoint handles all image generation models including:
    - Text-to-image models (prompt -> image)
    - Image-to-image models (image + prompt -> image)
    - Super-resolution/upscaler models (image + scale/dynamic/sharpen -> upscaled image)

    The upscaling functionality is integrated into the standard image generation workflow.
    Upscaler models from the 'super-resolution' collection accept an 'image' input parameter
    along with upscaling-specific parameters instead of just 'prompt'.

    Note: Input validation is handled by the frontend (Elm) which validates required fields
    against the model schema before submission. Additional validation for super-resolution
    models is performed below. Replicate API also validates and will return clear error messages
    if inputs are invalid.
    """
    try:
        if not ai_client:
            # Demo response - create a pending image
            image_id = save_generated_image(
                prompt=request.input.get("prompt", ""),
                image_url="",
                model_id=request.model_id,
                parameters=request.input,
                collection=request.collection,
                status="processing"
            )
            return {"image_id": image_id, "status": "processing"}

        # Basic validation: ensure we have at least a prompt or image parameter
        if not request.input.get("prompt") and not any(k for k in request.input.keys() if "image" in k.lower()):
            raise HTTPException(
                status_code=400,
                detail="Missing required input: must provide either 'prompt' or an image parameter"
            )

        headers = {
            "Authorization": f"Bearer {ai_client['api_key']}",
            "Content-Type": "application/json"
        }

        # Convert parameter types
        converted_input = {}
        for key, value in request.input.items():
            if isinstance(value, str):
                # Try to convert to int
                try:
                    converted_input[key] = int(value)
                    continue
                except ValueError:
                    pass

                # Try to convert to float
                try:
                    converted_input[key] = float(value)
                    continue
                except ValueError:
                    pass

                # Keep as string
                converted_input[key] = value
            else:
                converted_input[key] = value

        # Validate parameters for super-resolution models
        # Super-resolution models (upscalers) have specific parameter constraints
        if request.collection == "super-resolution":
            # Validate scale parameter (if provided)
            if "scale" in converted_input:
                scale = converted_input["scale"]
                if not isinstance(scale, (int, float)) or not (1 <= scale <= 4):
                    raise HTTPException(
                        status_code=400,
                        detail="Scale parameter must be between 1 and 4"
                    )

            # Validate dynamic/HDR parameter (if provided)
            if "dynamic" in converted_input:
                dynamic = converted_input["dynamic"]
                if not isinstance(dynamic, (int, float)) or not (3 <= dynamic <= 9):
                    raise HTTPException(
                        status_code=400,
                        detail="Dynamic (HDR) parameter must be between 3 and 9"
                    )

            # Validate sharpen parameter (if provided)
            if "sharpen" in converted_input:
                sharpen = converted_input["sharpen"]
                if not isinstance(sharpen, (int, float)) or not (0 <= sharpen <= 10):
                    raise HTTPException(
                        status_code=400,
                        detail="Sharpen parameter must be between 0 and 10"
                    )

            # Validate image URL parameter (required for upscaling)
            if "image" in converted_input:
                image_url = converted_input["image"]
                if not isinstance(image_url, str) or not image_url.startswith(('http://', 'https://')):
                    raise HTTPException(
                        status_code=400,
                        detail="Image parameter must be a valid HTTP/HTTPS URL"
                    )

        # Get the base URL for webhooks
        base_url = settings.BASE_URL

        # Only use webhooks if we have an HTTPS URL (production)
        use_webhooks = base_url.startswith("https://")

        # Create prediction using HTTP API
        if request.version:
            payload = {
                "version": request.version,
                "input": converted_input,
            }
            if use_webhooks:
                payload["webhook"] = f"{base_url}/api/webhooks/replicate"
                payload["webhook_events_filter"] = ["completed"]
            url = "https://api.replicate.com/v1/predictions"
            print(f"DEBUG: Sending to Replicate API (version-based) for image:")
            print(f"  Model: {request.model_id}")
            print(f"  Version: {request.version}")
        else:
            payload = {
                "input": converted_input,
            }
            if use_webhooks:
                payload["webhook"] = f"{base_url}/api/webhooks/replicate"
                payload["webhook_events_filter"] = ["completed"]
            url = f"https://api.replicate.com/v1/models/{request.model_id}/predictions"
            print(f"DEBUG: Sending to Replicate API (model-based) for image:")
            print(f"  Model: {request.model_id}")

        print(f"  Input types: {[(k, type(v).__name__, v) for k, v in converted_input.items()]}")
        if use_webhooks:
            print(f"  Webhook URL: {base_url}/api/webhooks/replicate")
        else:
            print(f"  Webhook: Disabled (local development - using polling only)")
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        # Log the detailed error if request fails
        if response.status_code != 201:
            error_detail = response.text
            print(f"Replicate API Error ({response.status_code}): {error_detail}")

            try:
                error_json = response.json()
                error_msg = error_json.get("detail", error_detail)
            except:
                error_msg = error_detail

            raise HTTPException(status_code=400, detail=f"Replicate API error: {error_msg}")

        result = response.json()

        # Get the prediction URL
        prediction_url = result.get("urls", {}).get("get")
        if not prediction_url:
            raise HTTPException(status_code=500, detail="No prediction URL returned from Replicate")

        # Enhance prompt with brief context if provided
        enhanced_prompt = request.input.get("prompt", "")
        metadata = {"replicate_id": result.get("id"), "prediction_url": prediction_url}

        if request.brief_id:
            try:
                from .database import get_creative_brief
                brief = get_creative_brief(request.brief_id, current_user["id"])
                if brief:
                    # Add brief context to prompt
                    brief_context = f" [Style: {brief.get('creative_direction', {}).get('style', 'modern')}]"
                    enhanced_prompt += brief_context
                    metadata["brief_id"] = request.brief_id
                    print(f"Enhanced prompt with brief context: {brief_context}")
            except Exception as e:
                print(f"Failed to enhance prompt with brief context: {e}")

        # Create image record with "processing" status
        image_id = save_generated_image(
            prompt=enhanced_prompt,
            image_url="",  # Will be filled in when complete and downloaded
            model_id=request.model_id,
            parameters=request.input,
            collection=request.collection,
            status="processing",
            metadata=metadata,
            brief_id=request.brief_id
        )

        # Start background task to poll for completion (fallback if webhook fails)
        background_tasks.add_task(
            process_image_generation_background,
            image_id=image_id,
            prediction_url=prediction_url,
            api_key=ai_client['api_key'],
            model_id=request.model_id,
            input_params=request.input,
            collection=request.collection
        )

        # Return immediately with image ID
        return {"image_id": image_id, "status": "processing"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error initiating image generation: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/generate-images-from-brief")
async def api_generate_images_from_brief(
    request: Dict,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth)
):
    """Generate images from all scenes in a creative brief.

    Expects:
        - briefId: The creative brief ID
        - modelName: The image generation model to use (e.g., "flux-schnell")

    Returns:
        - imageIds: List of created image IDs
    """
    try:
        brief_id = request.get("briefId")
        model_name = request.get("modelName")

        if not brief_id:
            raise HTTPException(status_code=400, detail="Missing briefId")
        if not model_name:
            raise HTTPException(status_code=400, detail="Missing modelName")

        # Fetch the brief
        from database import get_brief
        brief = get_brief(brief_id, current_user["id"])

        if not brief:
            raise HTTPException(status_code=404, detail="Brief not found")

        # Extract scenes from brief
        scenes = brief.get("scenes", [])
        if not scenes:
            raise HTTPException(status_code=400, detail="No scenes found in brief")

        # Find the model to get owner/name
        # Model name comes as just the name, need to look it up from image models
        image_ids = []

        # For each scene, extract the generation prompt and create an image
        for scene in scenes:
            visual = scene.get("visual", {})
            if not visual:
                continue

            generation_prompt = visual.get("generation_prompt")
            if not generation_prompt:
                continue

            # Model name should now be in format "owner/model"
            # If not, skip this scene
            if "/" not in model_name:
                print(f"Warning: Invalid model format '{model_name}', expected 'owner/model', skipping scene")
                continue

            model_id = model_name

            # Create image generation request
            image_request = RunImageRequest(
                model_id=model_id,
                input={"prompt": generation_prompt},
                collection="text-to-image",
                version=None,
                brief_id=brief_id
            )

            # Call the existing image generation endpoint logic
            try:
                result = await api_run_image_model(image_request, background_tasks, current_user)
                image_ids.append(result["image_id"])
                print(f"Created image {result['image_id']} for scene prompt: {generation_prompt[:50]}...")
            except Exception as e:
                print(f"Error generating image for scene: {str(e)}")
                # Continue with other scenes even if one fails

        if not image_ids:
            raise HTTPException(status_code=500, detail="Failed to generate any images from brief")

        return {"imageIds": image_ids, "count": len(image_ids)}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating images from brief: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


def download_and_save_image(image_url: str, image_id: int, max_retries: int = 3) -> str:
    """
    Download an image from Replicate and save it locally with retry logic.

    Args:
        image_url: URL of the image to download
        image_id: ID of the image in the database
        max_retries: Maximum number of download attempts (default: 3)

    Returns:
        str: Local file path of the downloaded image
    """
    import time
    from .database import increment_image_download_retries

    images_dir = Path(__file__).parent / "DATA" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Determine file extension from URL
    ext = ".png"  # Default extension
    if "." in image_url:
        url_ext = image_url.split(".")[-1].split("?")[0].lower()
        if url_ext in ["jpg", "jpeg", "png", "gif", "webp"]:
            ext = f".{url_ext}"

    filename = f"image_{image_id}{ext}"
    file_path = images_dir / filename

    last_error = None
    for attempt in range(max_retries):
        try:
            print(f"Downloading image {image_id} (attempt {attempt + 1}/{max_retries}): {image_url}")

            # Download with timeout
            response = requests.get(image_url, timeout=60, stream=True)
            response.raise_for_status()

            # Verify it's an image
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                raise ValueError(f"Invalid content type: {content_type}, expected image/*")

            # Download to temp file and collect binary data
            image_binary_data = bytearray()
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    image_binary_data.extend(chunk)

            # Verify file was created and has content
            if not file_path.exists():
                raise FileNotFoundError(f"File was not created: {file_path}")

            file_size = file_path.stat().st_size
            if file_size == 0:
                raise ValueError("Downloaded image file is empty")

            # Store binary data in database
            from .database import get_db
            with get_db() as conn:
                conn.execute(
                    "UPDATE generated_images SET image_data = ?, status = 'completed' WHERE id = ?",
                    (bytes(image_binary_data), image_id)
                )
                conn.commit()

            # Delete temp file - we only store in database now
            file_path.unlink()

            print(f"Image {image_id} downloaded successfully: {file_size} bytes stored in DB")
            # Return a database URL instead of file path
            # Use BASE_URL for full URLs
            base_url = os.getenv("BASE_URL", "").strip()
            if base_url:
                return f"{base_url}/api/images/{image_id}/data"
            else:
                return f"/api/images/{image_id}/data"

        except Exception as e:
            last_error = e
            print(f"Image {image_id} download attempt {attempt + 1} failed: {str(e)}")

            # Clean up partial file if it exists
            if file_path.exists():
                file_path.unlink()

            # Increment retry counter in database
            retry_count = increment_image_download_retries(image_id)
            print(f"Image {image_id} retry count: {retry_count}")

            # Wait before retrying (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s, etc.
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

    # All retries failed
    raise Exception(f"Failed to download image after {max_retries} attempts. Last error: {str(last_error)}")

def download_and_save_audio(audio_url: str, audio_id: int, max_retries: int = 3) -> str:
    """
    Download an audio file from Replicate and save it locally with retry logic.

    Args:
        audio_url: URL of the audio file to download
        audio_id: ID of the audio in the database
        max_retries: Maximum number of download attempts (default: 3)

    Returns:
        str: Local database URL of the downloaded audio
    """
    import time
    from .database import increment_audio_download_retries

    audio_dir = Path(__file__).parent / "DATA" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Determine file extension from URL
    ext = ".mp3"  # Default extension
    if "." in audio_url:
        url_ext = audio_url.split(".")[-1].split("?")[0].lower()
        if url_ext in ["mp3", "wav", "ogg", "m4a", "flac"]:
            ext = f".{url_ext}"

    filename = f"audio_{audio_id}{ext}"
    file_path = audio_dir / filename

    last_error = None
    for attempt in range(max_retries):
        try:
            print(f"Downloading audio {audio_id} (attempt {attempt + 1}/{max_retries}): {audio_url}")

            # Download with timeout
            response = requests.get(audio_url, timeout=120, stream=True)
            response.raise_for_status()

            # Verify it's an audio file
            content_type = response.headers.get("content-type", "")
            if not (content_type.startswith("audio/") or content_type == "application/octet-stream"):
                raise ValueError(f"Invalid content type: {content_type}, expected audio/*")

            # Download to temp file and collect binary data
            audio_binary_data = bytearray()
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    audio_binary_data.extend(chunk)

            # Verify file was created and has content
            if not file_path.exists():
                raise FileNotFoundError(f"File was not created: {file_path}")

            file_size = file_path.stat().st_size
            if file_size == 0:
                raise ValueError("Downloaded audio file is empty")

            # Store binary data in database
            from .database import get_db
            with get_db() as conn:
                conn.execute(
                    "UPDATE generated_audio SET audio_data = ?, status = 'completed' WHERE id = ?",
                    (bytes(audio_binary_data), audio_id)
                )
                conn.commit()

            # Delete temp file - we only store in database now
            file_path.unlink()

            print(f"Audio {audio_id} downloaded successfully: {file_size} bytes stored in DB")
            # Return a database URL instead of file path
            base_url = os.getenv("BASE_URL", "").strip()
            if base_url:
                return f"{base_url}/api/audio/{audio_id}/data"
            else:
                return f"/api/audio/{audio_id}/data"

        except Exception as e:
            last_error = e
            print(f"Audio {audio_id} download attempt {attempt + 1} failed: {str(e)}")

            # Clean up partial file if it exists
            if file_path.exists():
                file_path.unlink()

            # Increment retry counter in database
            retry_count = increment_audio_download_retries(audio_id)
            print(f"Audio {audio_id} retry count: {retry_count}")

            # Wait before retrying (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s, etc.
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

    # All retries failed
    raise Exception(f"Failed to download audio after {max_retries} attempts. Last error: {str(last_error)}")

@app.get("/api/images")
async def api_get_images(
    background_tasks: BackgroundTasks,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    model_id: Optional[str] = None,
    collection: Optional[str] = None,
    current_user: Dict = Depends(verify_auth)
):
    """
    Get generated images. Requires authentication.

    Automatically retries fetching images stuck in 'processing' status when gallery refreshes.
    """
    images = list_images(limit=limit, offset=offset, model_id=model_id, collection=collection)

    # Auto-retry any images in 'processing' status on gallery refresh
    for image in images:
        if image.get("status") != "processing":
            continue

        # Get metadata
        metadata = image.get("metadata", {})
        if isinstance(metadata, str):
            try:
                import json
                metadata = json.loads(metadata)
            except:
                metadata = {}

        prediction_url = metadata.get("prediction_url")
        replicate_id = metadata.get("replicate_id")

        if not prediction_url and not replicate_id:
            continue

        # Construct prediction URL if we only have ID
        if not prediction_url and replicate_id:
            prediction_url = f"https://api.replicate.com/v1/predictions/{replicate_id}"

        image_id = image["id"]

        # Auto-retry in background
        def auto_retry_image_task(img_id, pred_url):
            import requests

            api_key = settings.REPLICATE_API_KEY
            if not api_key:
                return

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            try:
                # Check prediction status
                response = requests.get(pred_url, headers=headers, timeout=10)
                response.raise_for_status()
                pred_data = response.json()

                status = pred_data.get("status")

                if status == "succeeded":
                    output = pred_data.get("output", [])
                    if isinstance(output, str):
                        output = [output]

                    image_url = output[0] if output else ""

                    if image_url:
                        # Download and save
                        db_url = download_and_save_image(image_url, img_id)
                        update_image_status(
                            image_id=img_id,
                            status="completed",
                            image_url=db_url,
                            metadata={
                                "replicate_id": pred_data.get("id"),
                                "prediction_url": pred_url,
                                "original_url": image_url,
                                "auto_retried": True
                            }
                        )
                        print(f"Auto-retry: Image {img_id} completed")
                elif status in ["failed", "canceled"]:
                    error = pred_data.get("error", "Unknown error")
                    update_image_status(
                        image_id=img_id,
                        status=status,
                        metadata={"error": error, "replicate_id": pred_data.get("id"), "auto_retried": True}
                    )
                    print(f"Auto-retry: Image {img_id} {status}")
                # If still processing, leave as-is

            except Exception as e:
                print(f"Auto-retry error for image {img_id}: {e}")

        background_tasks.add_task(auto_retry_image_task, image_id, prediction_url)

    return {"images": images}

@app.get("/api/images/{image_id}")
async def api_get_image(
    image_id: int,
    current_user: Dict = Depends(verify_auth)
):
    """Get a specific image by ID (used for polling image status). Requires authentication."""
    image = get_image_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
    return image

@app.get("/api/audio")
async def api_get_audio(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    model_id: Optional[str] = None,
    collection: Optional[str] = None,
    client_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Dict = Depends(verify_auth)
):
    """
    Get generated audio/music. Requires authentication.

    Query parameters:
    - limit: Maximum number of audio files to return (1-100, default: 50)
    - offset: Number of audio files to skip (default: 0)
    - model_id: Filter by model ID (e.g., 'meta/musicgen', 'riffusion/riffusion')
    - collection: Filter by collection name
    - client_id: Filter by client ID
    - campaign_id: Filter by campaign ID
    - status: Filter by status (processing, completed, failed, canceled)
    """
    audio_files = list_audio(
        limit=limit,
        offset=offset,
        collection=collection,
        status=status,
        client_id=client_id,
        campaign_id=campaign_id
    )

    # Additional model_id filtering (since list_audio doesn't support it yet)
    if model_id:
        audio_files = [a for a in audio_files if a.get("model_id") == model_id]

    return {"audio": audio_files, "count": len(audio_files)}

@app.get("/api/audio/{audio_id}")
async def api_get_audio_by_id(
    audio_id: int,
    current_user: Dict = Depends(verify_auth)
):
    """Get a specific audio by ID. Requires authentication."""
    audio = get_audio_by_id(audio_id)
    if not audio:
        raise HTTPException(status_code=404, detail=f"Audio {audio_id} not found")
    return audio

@app.delete("/api/audio/{audio_id}")
async def api_delete_audio(
    audio_id: int,
    current_user: Dict = Depends(verify_auth)
):
    """Delete an audio by ID. Requires authentication."""
    if delete_audio(audio_id):
        return {"success": True, "message": f"Audio {audio_id} deleted"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete audio from database")

@app.get("/api/audio/{audio_id}/data")
async def api_get_audio_data(
    audio_id: int
):
    """Get the binary audio data from database. Public endpoint for audio playback."""
    from .database import get_db

    with get_db() as conn:
        row = conn.execute(
            "SELECT audio_data, model_id FROM generated_audio WHERE id = ?",
            (audio_id,)
        ).fetchone()

        if not row or not row["audio_data"]:
            raise HTTPException(status_code=404, detail=f"Audio data not found for ID {audio_id}")

        # Determine media type from model or default to mp3
        media_type = "audio/mpeg"  # Default to MP3
        model_id = row.get("model_id", "")

        # Riffusion might output WAV, MusicGen outputs MP3
        if "riffusion" in model_id.lower():
            media_type = "audio/wav"

        # Return binary audio data
        from fastapi.responses import Response
        return Response(
            content=row["audio_data"],
            media_type=media_type,
            headers={
                "Content-Disposition": f"inline; filename=audio_{audio_id}.mp3",
                "Accept-Ranges": "bytes"
            }
        )

@app.get("/api/images/{image_id}/data")
async def api_get_image_data(
    image_id: int
):
    """Get the binary image data from database. Public endpoint for external services."""
    from .database import get_db

    with get_db() as conn:
        row = conn.execute(
            "SELECT image_data FROM generated_images WHERE id = ?",
            (image_id,)
        ).fetchone()

        if not row or not row["image_data"]:
            raise HTTPException(status_code=404, detail=f"Image data not found for ID {image_id}")

        # Return binary image data
        from fastapi.responses import Response
        return Response(content=row["image_data"], media_type="image/png")

@app.get("/api/images/{image_id}/thumbnail")
async def api_get_image_thumbnail(
    image_id: int
):
    """Get a thumbnail (400px width) of the image for gallery display. Public endpoint."""
    from .database import get_db
    from PIL import Image
    import io

    with get_db() as conn:
        row = conn.execute(
            "SELECT image_data FROM generated_images WHERE id = ?",
            (image_id,)
        ).fetchone()

        if not row or not row["image_data"]:
            raise HTTPException(status_code=404, detail=f"Image data not found for ID {image_id}")

        # Load image and create thumbnail
        image = Image.open(io.BytesIO(row["image_data"]))

        # Resize to max width of 400px, maintaining aspect ratio
        max_width = 400
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

        # Convert to bytes
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        thumbnail_data = output.getvalue()

        # Return thumbnail
        from fastapi.responses import Response
        return Response(content=thumbnail_data, media_type="image/jpeg")

@app.get("/api/videos/{video_id}/data")
async def api_get_video_data(
    video_id: int
):
    """Get the binary video data from database. Public endpoint for external services."""
    from .database import get_db

    with get_db() as conn:
        row = conn.execute(
            "SELECT video_data FROM generated_videos WHERE id = ?",
            (video_id,)
        ).fetchone()

        if not row or not row["video_data"]:
            raise HTTPException(status_code=404, detail=f"Video data not found for ID {video_id}")

        # Return binary video data
        from fastapi.responses import Response
        return Response(content=row["video_data"], media_type="video/mp4")

@app.get("/api/admin/storage/stats")
async def api_get_storage_stats(
    current_user: Dict = Depends(get_current_admin_user)
):
    """Get video storage statistics. Admin only."""
    from pathlib import Path
    import os

    videos_dir = Path(__file__).parent / "DATA" / "videos"

    if not videos_dir.exists():
        return {
            "total_videos": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "total_size_gb": 0,
            "videos_directory": str(videos_dir),
            "directory_exists": False
        }

    # Count files and calculate total size
    video_files = list(videos_dir.glob("*.mp4")) + list(videos_dir.glob("*.mov")) + \
                  list(videos_dir.glob("*.avi")) + list(videos_dir.glob("*.webm"))

    total_size = sum(f.stat().st_size for f in video_files if f.is_file())

    return {
        "total_videos": len(video_files),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
        "videos_directory": str(videos_dir),
        "directory_exists": True,
        "files": [
            {
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                "created": f.stat().st_ctime
            }
            for f in sorted(video_files, key=lambda x: x.stat().st_ctime, reverse=True)[:20]
        ]
    }

@app.delete("/api/admin/storage/videos/{video_id}")
async def api_delete_video_file(
    video_id: int,
    current_user: Dict = Depends(get_current_admin_user)
):
    """Delete a video file and database record. Admin only."""
    from pathlib import Path
    import os

    # Get video from database
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

    # Delete file if it exists
    video_url = video.get("video_url", "")
    if video_url and video_url.startswith("/data/videos/"):
        filename = video_url.split("/")[-1]
        videos_dir = Path(__file__).parent / "DATA" / "videos"
        file_path = videos_dir / filename

        if file_path.exists():
            file_path.unlink()
            print(f"Deleted video file: {file_path}")

    # Delete database record
    from .database import delete_video
    if delete_video(video_id):
        return {"success": True, "message": f"Video {video_id} deleted"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete video from database")

@app.post("/api/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: Dict = Depends(verify_auth)
):
    """Upload an image file and return its URL. Requires authentication."""
    import uuid
    from pathlib import Path

    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed types: {', '.join(allowed_types)}"
        )

    # Create uploads directory
    uploads_dir = Path(__file__).parent / "DATA" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower()
    if not file_ext:
        file_ext = ".jpg"  # Default extension

    unique_filename = f"upload_{uuid.uuid4().hex[:12]}{file_ext}"
    file_path = uploads_dir / unique_filename

    # Save file
    try:
        contents = await file.read()

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(contents) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_size / (1024 * 1024)}MB"
            )

        with open(file_path, "wb") as f:
            f.write(contents)

        # Return full URL (required for Replicate API)
        base_url = settings.BASE_URL

        # For local development, return data URL since Replicate can't access localhost
        # For production (HTTPS), return HTTP URL
        if base_url.startswith("http://localhost") or base_url.startswith("http://127.0.0.1"):
            import base64
            # Create data URL for Replicate API (works in local dev)
            data_url = f"data:{file.content_type};base64,{base64.b64encode(contents).decode()}"
            print(f"Uploaded image (local dev): {file_path} -> data URL ({len(contents)} bytes)")
            return {
                "success": True,
                "url": data_url,
                "filename": unique_filename
            }
        else:
            # Production: return HTTP URL
            image_url = f"{base_url}/data/uploads/{unique_filename}"
            print(f"Uploaded image: {file_path} -> {image_url}")
            return {
                "success": True,
                "url": image_url,
                "filename": unique_filename
            }

    except Exception as e:
        # Clean up file if it was created
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

# ============================================================================
# V2 Asset Upload Endpoints
# ============================================================================

@app.post("/api/v2/upload-asset", tags=["Asset Management"], response_model=Union[ImageAsset, VideoAsset, AudioAsset, DocumentAsset])
@limiter.limit("10/minute")
async def upload_asset_v2(
    request: Request,
    file: UploadFile = File(...),
    clientId: str = Form(...),  # REQUIRED - every asset must be associated with a client
    campaignId: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    type: Optional[str] = Form(None),  # Optional: "image", "video", "audio", or "document" - if empty, inferred from filetype
    tags: Optional[str] = Form(None),  # Optional: JSON array string of tags, e.g., '["brand", "logo"]'
    current_user: Dict = Depends(verify_auth)
) -> Asset:
    """
    Upload a media asset (image, video, audio, or document).

    Form-data parameters:
    - file: The binary file (required)
    - clientId: Associate with a client (REQUIRED - every asset must have a client)
    - campaignId: Associate with a campaign (optional)
    - name: Custom display name (optional, defaults to filename)
    - type: Asset type override (optional) - one of: "image", "video", "audio", "document"
      If not provided, type is inferred from file content type (fallback: "document")
    - tags: JSON array of tags as string (optional) - e.g., '["brand", "product"]'

    Supports: jpg, jpeg, png, gif, webp, mp4, mov, mp3, wav, pdf
    Max file size: 50MB
    Rate limit: 10 uploads per minute per user

    Returns: Full Asset object with discriminated union type
    """
    import uuid
    import mimetypes
    import json
    from pathlib import Path
    from backend.database_helpers import create_asset
    from backend.asset_metadata import extract_file_metadata, generate_video_thumbnail

    # Validate optional type parameter if provided
    if type:
        allowed_asset_types = {"image", "video", "audio", "document"}
        if type not in allowed_asset_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid type: {type}. Must be one of: {', '.join(allowed_asset_types)}"
            )

    # Parse tags if provided
    parsed_tags = None
    if tags:
        try:
            parsed_tags = json.loads(tags)
            if not isinstance(parsed_tags, list):
                raise HTTPException(
                    status_code=400,
                    detail="Tags must be a JSON array of strings, e.g., '[\"brand\", \"logo\"]'"
                )
            # Validate all tags are strings
            if not all(isinstance(tag, str) for tag in parsed_tags):
                raise HTTPException(
                    status_code=400,
                    detail="All tags must be strings"
                )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid tags format. Must be valid JSON array, e.g., '[\"brand\", \"logo\"]'"
            )

    # Validate file type
    allowed_types = {
        "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
        "video/mp4", "video/quicktime",
        "audio/mpeg", "audio/mp3", "audio/wav",
        "application/pdf"
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: images (jpg, png, gif, webp), videos (mp4, mov), audio (mp3, wav), documents (pdf)"
        )

    # Read file contents
    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Log upload details for debugging
    logger.info(f"Upload: filename={file.filename}, content_type={file.content_type}, size={len(contents)} bytes")

    # Validate file size (max 50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    size_bytes = len(contents)
    if size_bytes > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {max_size / (1024 * 1024)}MB"
        )

    # Determine file extension
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if not file_ext:
        # Guess from content type
        ext_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
            "video/quicktime": ".mov",
            "audio/mpeg": ".mp3",
            "audio/mp3": ".mp3",
            "audio/wav": ".wav",
            "application/pdf": ".pdf"
        }
        file_ext = ext_map.get(file.content_type, ".bin")

    # Generate unique asset ID
    asset_id = str(uuid.uuid4())
    user_id = current_user["id"]

    logger.info(f"Asset upload started: {asset_id} ({size_bytes} bytes) by user {user_id}")

    # Extract metadata from bytes (use temp file only for video/audio which need ffprobe)
    metadata = {}
    temp_file_path = None

    try:
        # Determine asset type from content type
        from backend.asset_metadata import determine_asset_type, get_file_format

        file_format = get_file_format("", file.content_type)
        if file_ext:
            file_format = file_ext.lstrip('.')

        inferred_asset_type = determine_asset_type(file.content_type, file_format)

        metadata = {
            'asset_type': inferred_asset_type,
            'format': file_format,
            'size': size_bytes
        }

        # Extract type-specific metadata
        if inferred_asset_type == 'image':
            # Extract image metadata from bytes using PIL
            try:
                from PIL import Image
                from io import BytesIO

                img = Image.open(BytesIO(contents))
                width, height = img.size
                metadata['width'] = width
                metadata['height'] = height
                img.close()
                logger.info(f"Extracted image metadata: {width}x{height}")
            except Exception as e:
                logger.warning(f"Failed to extract image metadata: {e}")

        elif inferred_asset_type in ['video', 'audio']:
            # For video/audio, we need a temp file for ffprobe
            # Create temp file, extract metadata, then delete
            import tempfile

            try:
                with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
                    temp_file.write(contents)
                    temp_file_path = temp_file.name

                # Extract metadata using the temp file
                if inferred_asset_type == 'video':
                    from backend.asset_metadata import extract_video_metadata
                    video_meta = extract_video_metadata(temp_file_path)
                    metadata.update(video_meta)
                    logger.info(f"Extracted video metadata: {video_meta}")
                else:  # audio
                    from backend.asset_metadata import extract_audio_metadata
                    audio_meta = extract_audio_metadata(temp_file_path)
                    metadata.update(audio_meta)
                    logger.info(f"Extracted audio metadata: {audio_meta}")

            except Exception as e:
                logger.warning(f"Failed to extract {inferred_asset_type} metadata: {e}")
            finally:
                # Clean up temp file
                if temp_file_path and Path(temp_file_path).exists():
                    Path(temp_file_path).unlink()
                    temp_file_path = None

    except Exception as e:
        logger.warning(f"Metadata extraction failed: {e}")
        metadata = {
            'asset_type': 'document',
            'format': file_ext.lstrip('.'),
            'size': size_bytes
        }

    # Use provided type parameter if given, otherwise use inferred type (fallback to 'document')
    asset_type = type if type else metadata.get('asset_type', 'document')

    # Note: Thumbnail generation for videos is skipped in blob-only mode
    # Videos are stored entirely in database, thumbnails would require complex temp file handling
    # TODO: Implement thumbnail extraction from blob_data if needed
    thumbnail_url = None

    # Determine display name
    display_name = name or file.filename or (f"{asset_id}{file_ext}")

    # Save to database with blob storage (NO filesystem storage)
    base_url = settings.BASE_URL
    asset_url = f"{base_url}/api/v2/assets/{asset_id}/data"  # Serve from blob endpoint

    try:
        db_asset_id = create_asset(
            name=display_name,
            asset_type=asset_type,  # Use the determined asset_type (from param or inferred)
            url=asset_url,
            format=metadata.get('format', file_ext.lstrip('.')),
            size=size_bytes,
            user_id=user_id,
            client_id=clientId,
            campaign_id=campaignId,
            tags=parsed_tags,  # Pass the parsed tags array
            width=metadata.get('width'),
            height=metadata.get('height'),
            duration=metadata.get('duration'),
            thumbnail_url=thumbnail_url,
            waveform_url=None,  # TODO: Implement waveform generation for audio
            page_count=metadata.get('pageCount'),
            asset_id=asset_id,  # Pass the pre-generated asset_id
            blob_data=contents  # CRITICAL: Store file contents in database BLOB
        )

        logger.info(f"Asset saved to database: {asset_id} (blob: {len(contents)} bytes)")
    except Exception as e:
        # No filesystem cleanup needed - everything is in memory/database
        logger.error(f"Failed to save asset to database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save asset: {str(e)}")

    # Fetch the created asset to return full discriminated union object
    from backend.database_helpers import get_asset_by_id as get_asset_by_id_helper
    created_asset = get_asset_by_id_helper(db_asset_id)

    if not created_asset:
        raise HTTPException(status_code=500, detail="Failed to retrieve created asset")

    return created_asset

@app.get("/api/v2/assets/{asset_id}/data", tags=["Asset Management"])
async def get_asset_data_v2(
    asset_id: str,
    current_user: Dict = Depends(verify_auth)
):
    """
    Serve uploaded asset binary data from database blob storage.

    This endpoint serves assets stored entirely in the database (blob_data column).
    NO filesystem storage - all assets are stored as BLOBs.

    Requires authentication - only asset owner can access.
    """
    from fastapi.responses import Response
    from backend.database_helpers import get_asset_by_id as get_asset_helper

    # Get asset metadata AND blob data from database
    asset = get_asset_helper(asset_id, include_blob=True)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # No ownership check - all dev team members can access all assets

    # Get blob data from database
    from backend.database import get_db
    with get_db() as conn:
        row = conn.execute(
            "SELECT blob_data FROM assets WHERE id = ?",
            (asset_id,)
        ).fetchone()

        if not row or not row["blob_data"]:
            raise HTTPException(
                status_code=404,
                detail="Asset binary data not found in database. Asset may have been uploaded before blob storage migration."
            )

        blob_data = row["blob_data"]

    # Determine media type from asset type and format
    type_map = {
        'image': 'image',
        'video': 'video',
        'audio': 'audio',
        'document': 'application'
    }
    base_type = type_map.get(asset.type, 'application')

    # Format-specific media types
    format_lower = asset.format.lower()
    media_type_map = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'mp4': 'video/mp4',
        'mov': 'video/quicktime',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'pdf': 'application/pdf',
    }

    media_type = media_type_map.get(format_lower, f"{base_type}/{format_lower}")

    # Return binary data with appropriate headers
    return Response(
        content=blob_data,
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{asset.name}"',
            "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
        }
    )


@app.get("/api/v2/assets/{asset_id}/thumbnail", tags=["Asset Management"])
async def get_asset_thumbnail_v2(
    asset_id: str,
    current_user: Dict = Depends(verify_auth)
):
    """
    Serve the thumbnail for a video or document asset.
    Requires authentication - only asset owner can access.
    """
    from fastapi.responses import FileResponse
    from backend.database_helpers import get_asset_by_id as get_asset_helper
    import re

    # Get asset metadata
    asset = get_asset_helper(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Security: Verify ownership
    if asset.userId != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if asset has a thumbnail (only VideoAsset and DocumentAsset have thumbnailUrl)
    if not hasattr(asset, 'thumbnailUrl') or not asset.thumbnailUrl:
        raise HTTPException(status_code=404, detail="Asset does not have a thumbnail")

    # Security: Validate asset_id is a valid UUID (prevents path traversal)
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if not uuid_pattern.match(asset_id):
        raise HTTPException(status_code=400, detail="Invalid asset ID format")

    # Thumbnail is stored as {asset_id}_thumb.jpg
    uploads_base = Path(__file__).parent / "DATA" / "assets"
    thumbnail_path = uploads_base / f"{asset_id}_thumb.jpg"

    # Security: Verify the resolved path is still within uploads_base
    try:
        thumbnail_path = thumbnail_path.resolve()
        uploads_base_resolved = uploads_base.resolve()
        if not str(thumbnail_path).startswith(str(uploads_base_resolved)):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        logger.error(f"Path resolution error: {e}")
        raise HTTPException(status_code=403, detail="Access denied")

    if not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found on disk")

    return FileResponse(
        path=str(thumbnail_path),
        media_type="image/jpeg",
        filename=f"{asset.name}_thumbnail.jpg"
    )

@app.delete("/api/v2/assets/{asset_id}", tags=["Asset Management"])
async def delete_asset_v2(
    asset_id: str,
    current_user: Dict = Depends(verify_auth)
):
    """
    Delete an uploaded asset.
    Only the owner can delete their assets.
    """
    import os
    import re
    from backend.database_helpers import get_asset_by_id as get_asset_helper, delete_asset as delete_asset_helper

    # Get asset metadata to verify ownership
    asset = get_asset_helper(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Verify ownership
    if asset.userId != str(current_user["id"]):
        raise HTTPException(status_code=403, detail="You don't have permission to delete this asset")

    # Security: Validate and sanitize file format (prevents path traversal)
    format_clean = validate_and_sanitize_format(asset.format)

    # Security: Validate asset_id is a valid UUID (prevents path traversal)
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    if not uuid_pattern.match(asset_id):
        raise HTTPException(status_code=400, detail="Invalid asset ID format")

    # Delete from database first
    deleted = delete_asset_helper(asset_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete asset from database")

    # Delete file from disk with sanitized path
    uploads_base = Path(__file__).parent / "DATA" / "assets"
    file_path = uploads_base / f"{asset_id}.{format_clean}"

    # Security: Verify the resolved path is still within uploads_base
    try:
        file_path_resolved = file_path.resolve()
        uploads_base_resolved = uploads_base.resolve()
        if not str(file_path_resolved).startswith(str(uploads_base_resolved)):
            logger.error(f"Attempted path traversal: {file_path}")
            raise HTTPException(status_code=403, detail="Access denied")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Path resolution error during deletion: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete asset file")

    if file_path.exists():
        try:
            os.remove(file_path)
            logger.info(f"Deleted asset file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete asset file {file_path}: {e}")

    # Delete thumbnail if it exists
    thumbnail_path = uploads_base / f"{asset_id}_thumb.jpg"
    try:
        thumbnail_path_resolved = thumbnail_path.resolve()
        if str(thumbnail_path_resolved).startswith(str(uploads_base_resolved)) and thumbnail_path.exists():
            os.remove(thumbnail_path)
            logger.info(f"Deleted thumbnail: {thumbnail_path}")
    except Exception as e:
        logger.warning(f"Failed to delete thumbnail {thumbnail_path}: {e}")

    return {
        "success": True,
        "message": f"Asset {asset_id} deleted successfully"
    }

@app.get("/api/v2/assets", tags=["Asset Management"], response_model=List[Union[ImageAsset, VideoAsset, AudioAsset, DocumentAsset]])
async def list_assets_v2(
    current_user: Dict = Depends(verify_auth),
    clientId: Optional[str] = Query(None),
    campaignId: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> List[Asset]:
    """
    List assets with optional filtering.

    Query parameters:
    - clientId: Filter by client ID
    - campaignId: Filter by campaign ID
    - asset_type: Filter by type ('image', 'video', 'audio', 'document')
    - limit: Maximum results (default: 50, max: 100)
    - offset: Pagination offset (default: 0)

    Returns: Array of Asset objects (discriminated union)
    """
    from backend.database_helpers import list_assets as list_assets_helper

    # Get filtered assets (no user filter - all dev team can access)
    assets = list_assets_helper(
        client_id=clientId,
        campaign_id=campaignId,
        asset_type=asset_type,
        limit=limit,
        offset=offset
    )

    return assets


@app.get("/api/v2/clients/{client_id}/assets", tags=["Asset Management"], response_model=List[Union[ImageAsset, VideoAsset, AudioAsset, DocumentAsset]])
async def get_client_assets(
    client_id: str,
    current_user: Dict = Depends(verify_auth),
    asset_type: Optional[str] = Query(None, description="Filter by type: image, video, audio, document"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
) -> List[Asset]:
    """
    Get all assets associated with a specific client.

    Every asset MUST be associated with a client, so this endpoint
    returns all assets for the given client.

    Query parameters:
    - asset_type: Optional filter by type ('image', 'video', 'audio', 'document')
    - limit: Maximum results (default: 50, max: 100)
    - offset: Pagination offset (default: 0)

    Returns: Array of Asset objects (discriminated union)
    """
    from backend.database_helpers import list_assets as list_assets_helper

    # Get all assets for this client (no user filter - all dev team can access)
    assets = list_assets_helper(
        client_id=client_id,
        campaign_id=None,  # Get all assets for client regardless of campaign
        asset_type=asset_type,
        limit=limit,
        offset=offset
    )

    return assets


@app.get("/api/v2/campaigns/{campaign_id}/assets", tags=["Asset Management"], response_model=List[Union[ImageAsset, VideoAsset, AudioAsset, DocumentAsset]])
async def get_campaign_assets(
    campaign_id: str,
    current_user: Dict = Depends(verify_auth),
    asset_type: Optional[str] = Query(None, description="Filter by type: image, video, audio, document"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
) -> List[Asset]:
    """
    Get all assets associated with a specific campaign.

    Assets may optionally be associated with a campaign, so this endpoint
    returns only assets that have been tagged to the given campaign.

    Query parameters:
    - asset_type: Optional filter by type ('image', 'video', 'audio', 'document')
    - limit: Maximum results (default: 50, max: 100)
    - offset: Pagination offset (default: 0)

    Returns: Array of Asset objects (discriminated union)
    """
    from backend.database_helpers import list_assets as list_assets_helper

    # Get all assets for this campaign (no user filter - all dev team can access)
    assets = list_assets_helper(
        client_id=None,  # Don't filter by client (campaign may have assets from different clients)
        campaign_id=campaign_id,
        asset_type=asset_type,
        limit=limit,
        offset=offset
    )

    return assets


@app.post("/api/genesis/render")
async def api_genesis_render(
    request: GenesisRenderRequest,
    current_user: Dict = Depends(verify_auth)
):
    """
    Render a scene using Genesis photorealistic ray-tracer with LLM semantic augmentation.
    Requires authentication.

    This endpoint:
    1. Takes scene data with simple shapes and text descriptions
    2. Uses LLM to augment objects with photorealistic properties
    3. Renders using Genesis ray-tracer
    4. Returns path to rendered video
    """
    try:
        from genesis_renderer import create_renderer

        # Convert scene to dict with description field
        scene_data = request.scene.dict()

        # Ensure each object has a description field (can be empty)
        for obj_id, obj in scene_data.get("objects", {}).items():
            if "description" not in obj:
                obj["description"] = ""

        # Create renderer with specified quality
        renderer = create_renderer(
            quality=request.quality,
            output_dir="./backend/DATA/genesis_videos"
        )

        # Render the scene
        video_path = await renderer.render_scene(
            scene_data=scene_data,
            duration=request.duration,
            fps=request.fps,
            resolution=request.resolution,
            camera_config=request.camera_config,
            scene_context=request.scene_context
        )

        # Clean up
        renderer.cleanup()

        # Extract object descriptions for database
        object_descriptions = {}
        for obj_id, obj in scene_data.get("objects", {}).items():
            if obj.get("description"):
                object_descriptions[obj_id] = obj.get("description")

        # Save to database
        from .database import save_genesis_video
        video_id = save_genesis_video(
            scene_data=scene_data,
            video_path=video_path,
            quality=request.quality,
            duration=request.duration,
            fps=request.fps,
            resolution=request.resolution,
            scene_context=request.scene_context,
            object_descriptions=object_descriptions if object_descriptions else None,
            metadata={
                "camera_config": request.camera_config,
                "renderer": "Genesis Rasterizer"  # or RayTracer when available
            }
        )

        # Return video URL (relative to backend)
        video_url = video_path.replace("./backend/DATA/", "/data/")

        return {
            "success": True,
            "video_id": video_id,
            "video_path": video_path,
            "video_url": video_url,
            "quality": request.quality,
            "duration": request.duration,
            "fps": request.fps
        }

    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Genesis not available. Install with: pip install genesis-world==0.3.7. Error: {str(e)}"
        )
    except Exception as e:
        print(f"Genesis rendering error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Genesis rendering failed: {str(e)}"
        )

@app.get("/api/genesis/videos")
async def list_genesis_videos_endpoint(
    limit: int = 50,
    offset: int = 0,
    quality: Optional[str] = None,
    current_user: Dict = Depends(verify_auth)
):
    """List Genesis-rendered videos from the database. Requires authentication."""
    try:
        from .database import list_genesis_videos, get_genesis_video_count

        videos = list_genesis_videos(limit=limit, offset=offset, quality=quality)
        total = get_genesis_video_count(quality=quality)

        return {
            "success": True,
            "videos": videos,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list videos: {e}")

@app.get("/api/genesis/videos/{video_id}")
async def get_genesis_video_endpoint(
    video_id: int,
    current_user: Dict = Depends(verify_auth)
):
    """Get a specific Genesis video by ID. Requires authentication."""
    try:
        from .database import get_genesis_video_by_id

        video = get_genesis_video_by_id(video_id)
        if not video:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

        return {
            "success": True,
            "video": video
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get video: {e}")

@app.delete("/api/genesis/videos/{video_id}")
async def delete_genesis_video_endpoint(
    video_id: int,
    current_user: Dict = Depends(verify_auth)
):
    """Delete a Genesis video by ID. Requires authentication."""
    try:
        from .database import delete_genesis_video
        import os
        from pathlib import Path

        # Get video info first to delete the file
        from .database import get_genesis_video_by_id
        video = get_genesis_video_by_id(video_id)

        if not video:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

        # Delete from database
        deleted = delete_genesis_video(video_id)

        # Delete video file if it exists
        if deleted and video.get("video_path"):
            video_path = Path(video["video_path"])
            if video_path.exists():
                os.remove(video_path)

        return {
            "success": True,
            "deleted": deleted
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {e}")

# Serve rendered videos
from fastapi.staticfiles import StaticFiles
GENESIS_VIDEO_DIR = Path(__file__).parent / "DATA" / "genesis_videos"
if GENESIS_VIDEO_DIR.exists():
    app.mount("/data/genesis_videos", StaticFiles(directory=str(GENESIS_VIDEO_DIR)), name="genesis_videos")

# Serve generated videos from Replicate
VIDEOS_DIR = Path(__file__).parent / "DATA" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/data/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")

# Serve uploaded images
UPLOADS_DIR = Path(__file__).parent / "DATA" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/data/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Serve generated images from Replicate
IMAGES_DIR = Path(__file__).parent / "DATA" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/data/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

# ============================================================================
# V2 Video Generation Endpoints
# ============================================================================

from .models.video_generation import (
    GenerationRequest,
    JobResponse,
    VideoProgress,
    VideoStatus,
    StoryboardEntry,
    Scene
)
from .database import (
    create_video_job,
    update_storyboard_data,
    get_jobs_by_client
)
from .services.replicate_client import ReplicateClient
import logging

logger = logging.getLogger(__name__)

def db_job_to_response(job: Dict[str, Any]) -> JobResponse:
    """Convert database job record to JobResponse model."""
    # Parse progress
    progress_data = job.get("progress", {})
    if isinstance(progress_data, str):
        try:
            progress_data = json.loads(progress_data)
        except:
            progress_data = {}

    progress = VideoProgress(
        current_stage=VideoStatus(job.get("status", "pending")),
        scenes_total=progress_data.get("scenes_total", 0),
        scenes_completed=progress_data.get("scenes_completed", 0),
        current_scene=progress_data.get("current_scene"),
        estimated_completion_seconds=progress_data.get("estimated_completion_seconds"),
        message=progress_data.get("message")
    )

    # Parse storyboard
    storyboard = None
    storyboard_data = job.get("storyboard_data")
    if storyboard_data:
        if isinstance(storyboard_data, str):
            try:
                storyboard_data = json.loads(storyboard_data)
            except:
                storyboard_data = None

        if storyboard_data and isinstance(storyboard_data, list):
            storyboard = [StoryboardEntry(**entry) for entry in storyboard_data]

    # Handle datetime fields
    from datetime import datetime
    created_at = job["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))

    updated_at = job.get("updated_at") or job["created_at"]
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))

    return JobResponse(
        job_id=job["id"],
        status=VideoStatus(job.get("status", "pending")),
        progress=progress,
        storyboard=storyboard,
        video_url=job.get("video_url") if job.get("video_url") else None,
        estimated_cost=job.get("estimated_cost", 0.0),
        actual_cost=job.get("actual_cost"),
        created_at=created_at,
        updated_at=updated_at,
        approved=job.get("approved", False),
        error_message=job.get("error_message")
    )

@app.post("/api/v2/generate", response_model=JobResponse)
@limiter.limit("5/minute")
async def create_generation_job(
    request: Request,
    gen_request: GenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth)
):
    """
    Create a new video generation job.

    This endpoint initiates the v2 video generation workflow:
    1. Creates a job record with 'pending' status
    2. Estimates the cost based on duration and scene count
    3. Queues a background task for storyboard generation
    4. Returns the job ID and initial status

    Rate limit: 5 requests per minute per user
    """
    try:
        # Estimate number of scenes (roughly 1 scene per 5 seconds)
        estimated_scenes = max(1, gen_request.duration // 5)

        # Estimate cost (use ReplicateClient if available, otherwise mock for POC)
        try:
            replicate_client = ReplicateClient()
            estimated_cost = replicate_client.estimate_cost(
                num_images=estimated_scenes,
                video_duration=gen_request.duration
            )
        except ValueError as e:
            # Replicate API key not set - use mock cost for POC
            logger.warning(f"Replicate not available: {e}. Using mock cost estimation.")
            estimated_cost = (estimated_scenes * 0.003) + (gen_request.duration * 0.10)

        # Get client_id from request or user
        client_id = gen_request.client_id or current_user.get("username")

        # Create job in database
        job_id = create_video_job(
            prompt=gen_request.prompt,
            model_id="v2-workflow",
            parameters={
                "duration": gen_request.duration,
                "style": gen_request.style,
                "aspect_ratio": gen_request.aspect_ratio,
                "brand_guidelines": gen_request.brand_guidelines
            },
            estimated_cost=estimated_cost,
            client_id=client_id,
            status="pending"
        )

        if not job_id:
            raise HTTPException(status_code=500, detail="Failed to create job")

        # Queue background task for storyboard generation (placeholder)
        # TODO: Implement actual storyboard generation
        logger.info(f"Job {job_id} created, queuing storyboard generation")

        # Fetch and return job
        job = get_job(job_id)
        if not job:
            raise HTTPException(status_code=500, detail="Job created but not found")

        return db_job_to_response(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating generation job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.get("/api/v2/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: int):
    """
    Get the current status and progress of a video generation job.

    This is a public endpoint (no authentication required) to allow
    clients to check job status using just the job ID.

    Uses Redis cache to reduce database load from frequent polling.
    """
    try:
        # Use cache if available, falls back to database automatically
        job = get_job_with_cache(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return db_job_to_response(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch job: {str(e)}")

@app.get("/api/v2/jobs", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    current_user: Dict = Depends(verify_auth)
):
    """
    List video generation jobs for the authenticated user.

    Query parameters:
    - status: Filter by job status (optional)
    - limit: Maximum number of jobs to return (default: 50, max: 100)

    Returns jobs ordered by creation date (newest first).
    """
    try:
        client_id = current_user.get("username")

        if status:
            # Validate status
            try:
                VideoStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}. Must be one of: {', '.join([s.value for s in VideoStatus])}"
                )
            jobs = get_jobs_by_client(client_id, status=status, limit=limit)
        else:
            jobs = get_jobs_by_client(client_id, limit=limit)

        return [db_job_to_response(job) for job in jobs]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")

@app.post("/api/v2/jobs/{job_id}/approve", response_model=JobResponse)
async def approve_job_storyboard(
    job_id: int,
    current_user: Dict = Depends(verify_auth)
):
    """
    Approve a job's storyboard for rendering.

    This endpoint marks the storyboard as approved, allowing the
    rendering process to proceed. The job must:
    - Be in 'storyboard_ready' status
    - Have a valid storyboard
    - Belong to the current user
    """
    try:
        # Fetch job (use cache)
        job = get_job_with_cache(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Verify ownership
        client_id = current_user.get("username")
        if job.get("client_id") != client_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Verify status
        if job.get("status") != "storyboard_ready":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve job in status '{job.get('status')}'. Must be 'storyboard_ready'."
            )

        # Verify storyboard exists
        if not job.get("storyboard_data"):
            raise HTTPException(status_code=400, detail="No storyboard available to approve")

        # Approve storyboard
        success = approve_storyboard(job_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to approve storyboard")

        # Invalidate cache after modification
        invalidate_job_cache(job_id)

        # Fetch updated job from database
        updated_job = get_job(job_id)
        if not updated_job:
            raise HTTPException(status_code=500, detail="Job approved but not found")

        return db_job_to_response(updated_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to approve job: {str(e)}")

@app.post("/api/v2/jobs/{job_id}/render", response_model=JobResponse)
@limiter.limit("5/minute")
async def render_approved_video(
    request: Request,
    job_id: int,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth)
):
    """
    Trigger video rendering from an approved storyboard.

    This endpoint starts the video rendering process. The job must:
    - Have an approved storyboard
    - Be in 'storyboard_ready' status
    - Belong to the current user

    The rendering process runs as a background task.
    """
    try:
        # Fetch job (use cache)
        job = get_job_with_cache(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Verify ownership
        client_id = current_user.get("username")
        if job.get("client_id") != client_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Verify approved
        if not job.get("approved"):
            raise HTTPException(status_code=400, detail="Storyboard must be approved before rendering")

        # Verify storyboard exists
        if not job.get("storyboard_data"):
            raise HTTPException(status_code=400, detail="No storyboard available to render")

        # Update status to rendering
        from .database import update_video_status
        update_video_status(job_id, status="rendering")

        # Invalidate cache after status change
        invalidate_job_cache(job_id)

        # Update progress (uses cache-aware function)
        update_job_progress_with_cache(job_id, {
            "current_stage": "rendering",
            "scenes_total": 0,
            "scenes_completed": 0,
            "message": "Starting video rendering..."
        })

        # Queue background task for rendering (placeholder)
        # TODO: Implement actual video rendering
        logger.info(f"Job {job_id} queued for rendering")

        # Fetch updated job
        updated_job = get_job(job_id)
        if not updated_job:
            raise HTTPException(status_code=500, detail="Job updated but not found")

        return db_job_to_response(updated_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rendering job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start rendering: {str(e)}")

@app.get("/api/v2/jobs/{job_id}/video")
async def get_job_video(job_id: int):
    """
    Get the final rendered video for a completed job.

    This endpoint returns the video URL or redirects to the video file.
    Returns 404 if the video is not ready yet.

    This is a public endpoint (no authentication required).
    """
    try:
        # Use cache for job lookup
        job = get_job_with_cache(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Check if video is ready
        if job.get("status") != "completed":
            raise HTTPException(
                status_code=404,
                detail=f"Video not ready. Current status: {job.get('status')}"
            )

        video_url = job.get("video_url")
        if not video_url:
            raise HTTPException(status_code=404, detail="Video URL not available")

        # Increment download count
        increment_download_count(job_id)

        # If it's a local path, serve the file
        if video_url.startswith("/data/"):
            from pathlib import Path
            video_path = Path(__file__).parent / video_url.lstrip("/")
            if video_path.exists():
                return FileResponse(str(video_path))

        # Otherwise redirect to external URL
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=video_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching video for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch video: {str(e)}")

@app.get("/api/v2/jobs/{job_id}/export")
@limiter.limit("5/minute")
async def export_job_video(
    request: Request,
    job_id: int,
    format: str = Query("mp4", pattern="^(mp4|mov|webm)$"),
    quality: str = Query("medium", pattern="^(low|medium|high)$"),
    current_user: dict = Depends(verify_auth)
):
    """
    Export completed video in requested format and quality.

    Query Parameters:
    - format: Output format (mp4, mov, webm)
    - quality: Quality preset (low=480p, medium=720p, high=1080p)

    Returns:
    - The exported video file

    Authentication: Required
    """
    from .services.video_exporter import export_video, get_export_path, check_ffmpeg_available
    from pathlib import Path

    try:
        # Check if ffmpeg is available
        if not check_ffmpeg_available():
            raise HTTPException(
                status_code=503,
                detail="Video export service unavailable (ffmpeg not installed)"
            )

        # Get job and validate
        job = get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Check if video is completed
        if job.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Video not ready for export. Current status: {job.get('status')}"
            )

        video_url = job.get("video_url")
        if not video_url:
            raise HTTPException(status_code=404, detail="Video not available")

        # Determine input video path
        if video_url.startswith("/data/"):
            input_path = str(Path(__file__).parent / video_url.lstrip("/"))
        elif video_url.startswith("http"):
            # For remote URLs, we'd need to download first (not implemented in MVP)
            raise HTTPException(
                status_code=400,
                detail="Export is only available for locally stored videos"
            )
        else:
            input_path = video_url

        # Check if input file exists
        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="Source video file not found")

        # Generate output path
        output_path = get_export_path(settings.VIDEO_STORAGE_PATH, job_id, format, quality)

        # Check if export already exists
        if not os.path.exists(output_path):
            # Export the video
            logger.info(f"Exporting job {job_id} to {format}/{quality}")
            success, error_msg = export_video(input_path, output_path, format, quality)

            if not success:
                raise HTTPException(status_code=500, detail=f"Export failed: {error_msg}")

        # Increment download count
        increment_download_count(job_id)

        # Return the exported file
        return FileResponse(
            output_path,
            media_type=f"video/{format}",
            filename=f"video_{job_id}.{format}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting video for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export video: {str(e)}")

@app.post("/api/v2/jobs/{job_id}/refine", response_model=JobResponse)
async def refine_job_scene(
    job_id: int,
    scene_number: int = Query(..., ge=1),
    new_image_prompt: Optional[str] = Query(None, min_length=10, max_length=2000),
    new_description: Optional[str] = Query(None, min_length=10, max_length=1000),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(verify_auth)
):
    """
    Refine a specific scene in the storyboard.

    This endpoint allows regenerating a scene image with a new prompt or
    updating the scene description. After refinement, the storyboard must
    be re-approved before rendering.

    Query Parameters:
    - scene_number: Scene number to refine (1-indexed)
    - new_image_prompt: New prompt for image regeneration (optional)
    - new_description: New scene description (optional)

    Rate Limiting: Maximum 5 refinements per job

    Authentication: Required
    """
    from .services.replicate_client import ReplicateClient

    try:
        # Get job and validate
        job = get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Check if storyboard exists
        storyboard_data = job.get("storyboard_data")
        if not storyboard_data:
            raise HTTPException(
                status_code=400,
                detail="No storyboard available for refinement"
            )

        # Check refinement limit
        refinement_count = get_refinement_count(job_id)
        if refinement_count >= 5:
            raise HTTPException(
                status_code=429,
                detail="Maximum refinement limit (5) reached for this job"
            )

        # Validate at least one refinement type is provided
        if not new_image_prompt and not new_description:
            raise HTTPException(
                status_code=400,
                detail="Must provide either new_image_prompt or new_description"
            )

        # If regenerating image, do it now
        new_image_url = None
        if new_image_prompt:
            try:
                logger.info(f"Regenerating image for job {job_id}, scene {scene_number}")
                replicate_client = ReplicateClient()

                # Get aspect ratio from job parameters
                parameters = job.get("parameters", {})
                aspect_ratio = parameters.get("aspect_ratio", "16:9")

                # Generate new image
                image_url = replicate_client.generate_image(new_image_prompt, aspect_ratio)
                new_image_url = image_url

                # Increment estimated cost (approximate cost for one image)
                increment_estimated_cost(job_id, 0.02)

                logger.info(f"Generated new image: {image_url}")
            except Exception as e:
                logger.error(f"Failed to regenerate image: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to regenerate image: {str(e)}"
                )

        # Update the scene in storyboard
        success = refine_scene_in_storyboard(
            job_id,
            scene_number,
            new_image_url=new_image_url,
            new_description=new_description,
            new_image_prompt=new_image_prompt
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update storyboard"
            )

        # Fetch updated job
        updated_job = get_job(job_id)
        if not updated_job:
            raise HTTPException(status_code=500, detail="Failed to fetch updated job")

        # Return the updated job response
        return db_job_to_response(updated_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refining scene for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refine scene: {str(e)}")

@app.post("/api/v2/jobs/{job_id}/reorder", response_model=JobResponse)
async def reorder_job_scenes(
    job_id: int,
    scene_order: List[int] = Query(..., description="New order of scene numbers"),
    current_user: dict = Depends(verify_auth)
):
    """
    Reorder scenes in the storyboard.

    This endpoint allows changing the sequence of scenes. After reordering,
    the storyboard must be re-approved before rendering.

    Request Body:
    - scene_order: List of scene numbers in desired order (e.g., [1, 3, 2, 4])

    Authentication: Required
    """
    try:
        # Get job and validate
        job = get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Check if storyboard exists
        storyboard_data = job.get("storyboard_data")
        if not storyboard_data:
            raise HTTPException(
                status_code=400,
                detail="No storyboard available for reordering"
            )

        # Validate scene_order
        if not scene_order:
            raise HTTPException(status_code=400, detail="scene_order cannot be empty")

        # Reorder the scenes
        success = reorder_storyboard_scenes(job_id, scene_order)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="Failed to reorder scenes. Check that all scene numbers are valid."
            )

        # Fetch updated job
        updated_job = get_job(job_id)
        if not updated_job:
            raise HTTPException(status_code=500, detail="Failed to fetch updated job")

        # Return the updated job response
        return db_job_to_response(updated_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering scenes for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reorder scenes: {str(e)}")

@app.get("/api/v2/jobs/{job_id}/metadata")
async def get_job_metadata(job_id: int):
    """
    Get comprehensive metadata for a video generation job.

    Returns detailed information including:
    - Scene count and details
    - Cost information (estimated and actual)
    - Generation times and statistics
    - Refinement count
    - Download count

    This is a public endpoint (no authentication required).
    """
    try:
        # Get job
        job = get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Build metadata response
        storyboard_data = job.get("storyboard_data", [])

        metadata = {
            "job_id": job_id,
            "status": job.get("status"),
            "created_at": job.get("created_at"),
            "updated_at": job.get("updated_at"),
            "approved": job.get("approved", False),
            "approved_at": job.get("approved_at"),

            # Scene information
            "scenes": {
                "total": len(storyboard_data),
                "completed": sum(1 for s in storyboard_data if s.get("generation_status") == "completed"),
                "failed": sum(1 for s in storyboard_data if s.get("generation_status") == "failed"),
                "details": [
                    {
                        "scene_number": s.get("scene", {}).get("scene_number"),
                        "duration": s.get("scene", {}).get("duration"),
                        "status": s.get("generation_status"),
                        "has_image": bool(s.get("image_url"))
                    }
                    for s in storyboard_data
                ]
            },

            # Cost information
            "costs": {
                "estimated": job.get("estimated_cost", 0.0),
                "actual": job.get("actual_cost", 0.0),
                "currency": "USD"
            },

            # Generation metrics
            "metrics": {
                "refinement_count": get_refinement_count(job_id),
                "download_count": get_download_count(job_id),
            },

            # Video information
            "video": {
                "available": job.get("status") == "completed",
                "url": job.get("video_url") if job.get("status") == "completed" else None,
                "parameters": job.get("parameters", {})
            },

            # Error information (if any)
            "error": job.get("error_message")
        }

        return metadata

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metadata for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch metadata: {str(e)}")

# ============================================================================
# Simple Image/Video Generation Endpoints
# ============================================================================

@app.post("/api/v2/generate/image")
@limiter.limit("10/minute")
async def generate_image(
    request: Request,
    gen_request: ImageGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth)
):
    """
    Generate an image using nano-banana model.

    Supports text-to-image and image-to-image workflows.
    At least one of (prompt, asset_id, image_id, video_id) must be provided.

    Rate limit: 10 requests per minute per user
    """
    try:
        # Build nano-banana input parameters
        nano_banana_input = {}

        # Handle prompt
        if gen_request.prompt:
            nano_banana_input["prompt"] = gen_request.prompt
        else:
            # Default prompt if only image reference is provided
            nano_banana_input["prompt"] = "high quality image"

        # Handle image reference (if provided)
        image_url = None
        if any([gen_request.asset_id, gen_request.image_id, gen_request.video_id]):
            image_url = resolve_image_reference(
                asset_id=gen_request.asset_id,
                image_id=gen_request.image_id,
                video_id=gen_request.video_id
            )
            nano_banana_input["image_input"] = [image_url]
            nano_banana_input["aspect_ratio"] = "match_input_image"
        else:
            # No image reference, use default aspect ratio
            nano_banana_input["image_input"] = []
            nano_banana_input["aspect_ratio"] = "1:1"

        # Set output format
        nano_banana_input["output_format"] = "jpg"

        # Create run request for nano-banana
        run_request = RunImageRequest(
            model_id="google/nano-banana",
            input=nano_banana_input,
            collection=None,
            version=None,
            brief_id=None
        )

        # Call the existing run-image-model endpoint logic
        # Get the base URL for webhooks
        base_url = settings.BASE_URL

        # Only use webhooks if we have an HTTPS URL (production)
        use_webhooks = base_url.startswith("https://")

        # Create prediction using HTTP API
        payload = {
            "input": nano_banana_input,
        }
        if use_webhooks:
            payload["webhook"] = f"{base_url}/api/webhooks/replicate"
            payload["webhook_events_filter"] = ["completed"]

        url = "https://api.replicate.com/v1/models/google/nano-banana/predictions"

        headers = {
            "Authorization": f"Token {settings.REPLICATE_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        prediction = response.json()

        # Save to database with client_id and campaign_id
        image_id = save_generated_image(
            prompt=nano_banana_input["prompt"],
            image_url="pending",
            model_id="google/nano-banana",
            parameters=nano_banana_input,
            collection=None,
            metadata={"replicate_id": prediction["id"], "prediction_url": prediction.get("urls", {}).get("get")},
            status="processing",
            brief_id=None,
            client_id=gen_request.client_id,
            campaign_id=gen_request.campaign_id
        )

        # Queue background processing
        background_tasks.add_task(
            process_image_generation_background,
            image_id=image_id,
            prediction_url=prediction.get("urls", {}).get("get"),
            api_key=settings.REPLICATE_API_KEY,
            model_id="google/nano-banana",
            input_params=nano_banana_input,
            collection=None
        )

        # Return immediately with image ID
        return {"image_id": image_id, "status": "processing"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")

@app.post("/api/v2/generate/video")
@limiter.limit("5/minute")
async def generate_video(
    request: Request,
    gen_request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth)
):
    """
    Generate a video using the selected model (default: bytedance/seedance-1-lite).

    Supports:
    - bytedance/seedance-1-lite (default)
    - kwaivgi/kling-v2.1

    Requires a start_image. If only a prompt is provided, an image will be auto-generated first.
    At least one of (prompt, asset_id, image_id, video_id) must be provided.

    Rate limit: 5 requests per minute per user
    """
    try:
        # Determine if we have an image reference
        has_image_ref = any([gen_request.asset_id, gen_request.image_id, gen_request.video_id])

        intermediate_image_id = None

        # If no image reference, auto-generate one using nano-banana
        if not has_image_ref:
            if not gen_request.prompt:
                raise HTTPException(
                    status_code=400,
                    detail="Either provide a prompt (for auto-image generation) or an image reference"
                )

            logger.info("No image reference provided, auto-generating image for video")

            # Generate image synchronously (with timeout)
            image_gen_request = ImageGenerationRequest(
                prompt=gen_request.prompt,
                client_id=gen_request.client_id,
                campaign_id=gen_request.campaign_id
            )

            # Build nano-banana input
            nano_banana_input = {
                "prompt": gen_request.prompt,
                "image_input": [],
                "aspect_ratio": "16:9",  # Good for video
                "output_format": "jpg"
            }

            # Call Replicate for image generation
            payload = {"input": nano_banana_input}
            url = "https://api.replicate.com/v1/models/google/nano-banana/predictions"
            headers = {
                "Authorization": f"Token {settings.REPLICATE_API_KEY}",
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            prediction = response.json()

            # Save intermediate image
            intermediate_image_id = save_generated_image(
                prompt=gen_request.prompt,
                image_url="pending",
                model_id="google/nano-banana",
                parameters=nano_banana_input,
                collection=None,
                metadata={"replicate_id": prediction["id"], "prediction_url": prediction.get("urls", {}).get("get")},
                status="processing",
                brief_id=None,
                client_id=gen_request.client_id,
                campaign_id=gen_request.campaign_id
            )

            # Wait for image completion (with timeout)
            import time
            max_wait = 60  # 60 seconds
            wait_interval = 2  # Check every 2 seconds
            elapsed = 0

            while elapsed < max_wait:
                prediction_url = prediction.get("urls", {}).get("get")
                pred_response = requests.get(prediction_url, headers=headers)
                pred_response.raise_for_status()
                pred_data = pred_response.json()

                if pred_data.get("status") == "succeeded":
                    # Download and save image
                    image_url = pred_data.get("output")
                    if isinstance(image_url, list):
                        image_url = image_url[0]

                    # Download image
                    download_url = download_and_save_image(image_url, intermediate_image_id)
                    break
                elif pred_data.get("status") in ["failed", "canceled"]:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Image generation failed: {pred_data.get('error')}"
                    )

                time.sleep(wait_interval)
                elapsed += wait_interval

            if elapsed >= max_wait:
                raise HTTPException(
                    status_code=500,
                    detail="Image generation timed out after 60 seconds"
                )

            # Use the generated image as reference
            gen_request.image_id = intermediate_image_id

        # Now we have an image reference, resolve it
        start_image_url = resolve_image_reference(
            asset_id=gen_request.asset_id,
            image_id=gen_request.image_id,
            video_id=gen_request.video_id
        )

        # Build model-specific input parameters
        model_id = gen_request.model.value

        if gen_request.model == VideoModel.SEEDANCE:
            # ByteDance Seedance-1-lite parameters
            model_input = {
                "prompt": gen_request.prompt or "high quality video",
                "image": start_image_url,
                "duration": 5,  # 2-12 seconds, default 5
                "resolution": "720p",  # 480p, 720p, or 1080p
                "aspect_ratio": "16:9",  # 16:9, 4:3, 1:1, 3:4, 9:16, 21:9, 9:21
                "fps": 24,  # Fixed at 24fps
                "camera_fixed": False,  # Whether to fix camera position
            }
        elif gen_request.model == VideoModel.KLING:
            # Kling v2.1 parameters
            model_input = {
                "prompt": gen_request.prompt or "high quality video",
                "start_image": start_image_url,
                "mode": "pro",
                "duration": 5,
                "negative_prompt": ""
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model: {gen_request.model}")

        # Call Replicate for video generation
        base_url = settings.BASE_URL
        use_webhooks = base_url.startswith("https://")

        payload = {
            "input": model_input,
        }
        if use_webhooks:
            payload["webhook"] = f"{base_url}/api/webhooks/replicate"
            payload["webhook_events_filter"] = ["completed"]

        url = f"https://api.replicate.com/v1/models/{model_id}/predictions"
        headers = {
            "Authorization": f"Token {settings.REPLICATE_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        prediction = response.json()

        # Save to database with client_id and campaign_id
        video_id = save_generated_video(
            prompt=model_input["prompt"],
            video_url="pending",
            model_id=model_id,
            parameters=model_input,
            collection=None,
            metadata={"replicate_id": prediction["id"], "prediction_url": prediction.get("urls", {}).get("get")},
            status="processing",
            brief_id=None,
            client_id=gen_request.client_id,
            campaign_id=gen_request.campaign_id
        )

        # Queue background processing
        background_tasks.add_task(
            process_video_generation_background,
            video_id=video_id,
            prediction_url=prediction.get("urls", {}).get("get"),
            api_key=settings.REPLICATE_API_KEY,
            model_id=model_id,
            input_params=model_input,
            collection=None
        )

        # Return immediately with video ID
        result = {"video_id": video_id, "status": "processing"}
        if intermediate_image_id:
            result["intermediate_image_id"] = intermediate_image_id

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate video: {str(e)}")

@app.post("/api/v2/generate/audio")
@limiter.limit("10/minute")
async def generate_audio(
    request: Request,
    gen_request: AudioGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth)
):
    """
    Generate audio/music using the selected model (default: meta/musicgen).

    Supports:
    - meta/musicgen (default)
    - riffusion/riffusion

    Rate limit: 10 requests per minute per user
    """
    try:
        # Build model-specific input parameters
        model_id = gen_request.model.value

        if gen_request.model == AudioModel.MUSICGEN:
            # MusicGen parameters
            model_input = {
                "prompt": gen_request.prompt,
                "model_version": "stereo-melody-large",
                "duration": gen_request.duration or 8,
                "temperature": 1,
                "top_k": 250,
                "top_p": 0,
                "classifier_free_guidance": 3,
                "output_format": "mp3"
            }
        elif gen_request.model == AudioModel.RIFFUSION:
            # Riffusion parameters
            model_input = {
                "prompt_a": gen_request.prompt,
                "denoising": 0.75,
                "num_inference_steps": 50,
                "seed_image_id": "vibes"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model: {gen_request.model}")

        # Call Replicate for audio generation
        base_url = settings.BASE_URL
        use_webhooks = base_url.startswith("https://")

        payload = {
            "input": model_input,
        }
        if use_webhooks:
            payload["webhook"] = f"{base_url}/api/webhooks/replicate"
            payload["webhook_events_filter"] = ["completed"]

        url = f"https://api.replicate.com/v1/models/{model_id}/predictions"
        headers = {
            "Authorization": f"Token {settings.REPLICATE_API_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        prediction = response.json()

        # Save to database with client_id and campaign_id
        audio_id = save_generated_audio(
            prompt=model_input.get("prompt") or model_input.get("prompt_a"),
            audio_url="pending",
            model_id=model_id,
            parameters=model_input,
            collection=None,
            metadata={"replicate_id": prediction["id"], "prediction_url": prediction.get("urls", {}).get("get")},
            status="processing",
            brief_id=None,
            client_id=gen_request.client_id,
            campaign_id=gen_request.campaign_id,
            duration=gen_request.duration
        )

        # Launch background task to poll for completion and download audio
        background_tasks.add_task(
            process_audio_generation_background,
            audio_id=audio_id,
            prediction_url=prediction.get("urls", {}).get("get"),
            api_key=settings.REPLICATE_API_KEY,
            model_id=model_id,
            input_params=model_input,
            collection=None
        )

        logger.info(f"Audio generation started: audio_id={audio_id}, model={model_id}, replicate_id={prediction['id']}")

        # Return immediately with audio ID
        return {"audio_id": audio_id, "status": "processing", "model": model_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

@app.get("/api/v2/clients/{client_id}/generated-images")
async def get_client_generated_images(
    client_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: Dict = Depends(verify_auth)
):
    """
    Get all generated images for a specific client.

    Query parameters:
    - status: Optional filter by status (processing, completed, failed, canceled)
    - limit: Maximum number of images to return (default: 50)
    """
    try:
        images = get_generated_images_by_client(client_id, status, limit)
        return {"client_id": client_id, "count": len(images), "images": images}
    except Exception as e:
        logger.error(f"Error fetching images for client {client_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch images: {str(e)}")

@app.get("/api/v2/clients/{client_id}/generated-videos")
async def get_client_generated_videos(
    client_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: Dict = Depends(verify_auth)
):
    """
    Get all generated videos for a specific client.

    Query parameters:
    - status: Optional filter by status (processing, completed, failed, canceled)
    - limit: Maximum number of videos to return (default: 50)
    """
    try:
        videos = get_generated_videos_by_client(client_id, status, limit)
        return {"client_id": client_id, "count": len(videos), "videos": videos}
    except Exception as e:
        logger.error(f"Error fetching videos for client {client_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch videos: {str(e)}")

@app.get("/api/v2/campaigns/{campaign_id}/generated-images")
async def get_campaign_generated_images(
    campaign_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: Dict = Depends(verify_auth)
):
    """
    Get all generated images for a specific campaign.

    Query parameters:
    - status: Optional filter by status (processing, completed, failed, canceled)
    - limit: Maximum number of images to return (default: 50)
    """
    try:
        images = get_generated_images_by_campaign(campaign_id, status, limit)
        return {"campaign_id": campaign_id, "count": len(images), "images": images}
    except Exception as e:
        logger.error(f"Error fetching images for campaign {campaign_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch images: {str(e)}")

@app.get("/api/v2/campaigns/{campaign_id}/generated-videos")
async def get_campaign_generated_videos(
    campaign_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: Dict = Depends(verify_auth)
):
    """
    Get all generated videos for a specific campaign.

    Query parameters:
    - status: Optional filter by status (processing, completed, failed, canceled)
    - limit: Maximum number of videos to return (default: 50)
    """
    try:
        videos = get_generated_videos_by_campaign(campaign_id, status, limit)
        return {"campaign_id": campaign_id, "count": len(videos), "videos": videos}
    except Exception as e:
        logger.error(f"Error fetching videos for campaign {campaign_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch videos: {str(e)}")

# ============================================================================
# Creative Brief Parsing Endpoints
# ============================================================================

# Include the prompt parser router
app.include_router(parse_api.router, prefix="/api/creative", tags=["creative"])
app.include_router(briefs_api.router, prefix="/api/creative", tags=["creative"])

# Include clients and campaigns router (for ad-video-gen frontend)
app.include_router(clients_campaigns_router, prefix="/api", tags=["Core Entities"])

# ============================================
# Video/Image Retry Endpoints
# ============================================

@app.post("/api/videos/{video_id}/retry")
async def retry_video_processing(
    video_id: int,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(verify_auth)
):
    """
    Retry fetching a video from Replicate that may have failed webhook processing.
    Checks the Replicate prediction status and downloads the video if ready.
    """
    from .database import get_video_by_id

    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Get replicate prediction URL from metadata
    metadata = video.get("metadata", {})
    prediction_url = metadata.get("prediction_url")
    replicate_id = metadata.get("replicate_id")

    if not prediction_url and not replicate_id:
        raise HTTPException(
            status_code=400,
            detail="Video has no Replicate prediction URL or ID in metadata"
        )

    # Construct prediction URL if we only have ID
    if not prediction_url and replicate_id:
        prediction_url = f"https://api.replicate.com/v1/predictions/{replicate_id}"

    # Check current status
    if video["status"] == "completed":
        return {
            "message": "Video already completed",
            "video_id": video_id,
            "status": "completed"
        }

    # Retry the download in background
    def retry_task():
        import requests

        api_key = settings.REPLICATE_API_KEY
        if not api_key:
            print(f"Cannot retry video {video_id}: No Replicate API key")
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            # Check prediction status
            response = requests.get(prediction_url, headers=headers)
            response.raise_for_status()
            pred_data = response.json()

            status = pred_data.get("status")

            if status == "succeeded":
                output = pred_data.get("output", [])
                if isinstance(output, str):
                    output = [output]

                video_url = output[0] if output else ""

                if video_url:
                    # Try to download
                    db_url = download_and_save_video(video_url, video_id)
                    update_video_status(
                        video_id=video_id,
                        status="completed",
                        video_url=db_url,
                        metadata={
                            "replicate_id": pred_data.get("id"),
                            "prediction_url": prediction_url,
                            "original_url": video_url,
                            "retried": True
                        }
                    )
                    print(f"Video {video_id} retry successful")
                else:
                    update_video_status(
                        video_id=video_id,
                        status="failed",
                        metadata={"error": "No video URL in response", "retried": True}
                    )
            elif status in ["failed", "canceled"]:
                error = pred_data.get("error", "Unknown error")
                update_video_status(
                    video_id=video_id,
                    status=status,
                    metadata={"error": error, "replicate_id": pred_data.get("id"), "retried": True}
                )
            elif status == "processing":
                # Still processing, don't change status
                print(f"Video {video_id} still processing on Replicate")

        except Exception as e:
            print(f"Error retrying video {video_id}: {e}")
            import traceback
            traceback.print_exc()

    background_tasks.add_task(retry_task)

    return {
        "message": "Retry initiated",
        "video_id": video_id,
        "prediction_url": prediction_url
    }

@app.post("/api/videos/retry-all-stuck")
async def retry_all_stuck_videos(
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_admin_user)
):
    """
    Admin endpoint: Retry all videos stuck in 'processing' status.
    Useful for recovering from webhook failures.
    """
    from .database import get_db

    # Find all videos stuck in processing
    stuck_videos = []
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, metadata FROM generated_videos
            WHERE status = 'processing'
            AND (json_extract(metadata, '$.prediction_url') IS NOT NULL
                 OR json_extract(metadata, '$.replicate_id') IS NOT NULL)
            """
        ).fetchall()

        for row in rows:
            stuck_videos.append({
                "id": row["id"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            })

    if not stuck_videos:
        return {
            "message": "No stuck videos found",
            "count": 0
        }

    # Retry each one
    def retry_all_task():
        import requests

        api_key = settings.REPLICATE_API_KEY
        if not api_key:
            print("Cannot retry videos: No Replicate API key")
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        for video in stuck_videos:
            video_id = video["id"]
            metadata = video["metadata"]

            prediction_url = metadata.get("prediction_url")
            replicate_id = metadata.get("replicate_id")

            if not prediction_url and replicate_id:
                prediction_url = f"https://api.replicate.com/v1/predictions/{replicate_id}"

            if not prediction_url:
                print(f"Skipping video {video_id}: no prediction URL")
                continue

            try:
                response = requests.get(prediction_url, headers=headers)
                response.raise_for_status()
                pred_data = response.json()

                status = pred_data.get("status")

                if status == "succeeded":
                    output = pred_data.get("output", [])
                    if isinstance(output, str):
                        output = [output]

                    video_url = output[0] if output else ""

                    if video_url:
                        db_url = download_and_save_video(video_url, video_id)
                        update_video_status(
                            video_id=video_id,
                            status="completed",
                            video_url=db_url,
                            metadata={
                                "replicate_id": pred_data.get("id"),
                                "prediction_url": prediction_url,
                                "original_url": video_url,
                                "bulk_retried": True
                            }
                        )
                        print(f"Bulk retry: Video {video_id} completed")
                elif status in ["failed", "canceled"]:
                    error = pred_data.get("error", "Unknown error")
                    update_video_status(
                        video_id=video_id,
                        status=status,
                        metadata={"error": error, "replicate_id": pred_data.get("id"), "bulk_retried": True}
                    )
                    print(f"Bulk retry: Video {video_id} {status}")

            except Exception as e:
                print(f"Error bulk retrying video {video_id}: {e}")

    background_tasks.add_task(retry_all_task)

    return {
        "message": f"Retry initiated for {len(stuck_videos)} stuck videos",
        "count": len(stuck_videos),
        "video_ids": [v["id"] for v in stuck_videos]
    }

# ============================================
# Database Administration Endpoints
# ============================================

@app.get("/api/db/schema", tags=["Database"])
async def get_database_schema(
    current_user: Dict = Depends(get_current_admin_user)
):
    """
    Get the complete database schema (all tables and their columns).
    Requires admin authentication.
    """
    from .database import get_db

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]

            schema = {}
            for table in tables:
                # Get table info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = []
                for row in cursor.fetchall():
                    columns.append({
                        "cid": row[0],
                        "name": row[1],
                        "type": row[2],
                        "notnull": bool(row[3]),
                        "default_value": row[4],
                        "primary_key": bool(row[5])
                    })

                # Get indexes
                cursor.execute(f"PRAGMA index_list({table})")
                indexes = [{"name": row[1], "unique": bool(row[2])} for row in cursor.fetchall()]

                # Get foreign keys
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                foreign_keys = []
                for row in cursor.fetchall():
                    foreign_keys.append({
                        "id": row[0],
                        "table": row[2],
                        "from": row[3],
                        "to": row[4]
                    })

                schema[table] = {
                    "columns": columns,
                    "indexes": indexes,
                    "foreign_keys": foreign_keys
                }

            # Get triggers
            cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger' ORDER BY name")
            triggers = [{"name": row[0], "table": row[1], "sql": row[2]} for row in cursor.fetchall()]

            return {
                "tables": schema,
                "triggers": triggers,
                "total_tables": len(tables)
            }
    except Exception as e:
        logger.error(f"Failed to get database schema: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get database schema: {str(e)}")

@app.get("/api/db/download", tags=["Database"])
async def download_database(
    current_user: Dict = Depends(get_current_admin_user)
):
    """
    Download the complete SQLite database file.
    Requires admin authentication.
    """
    from .database import DB_PATH
    import shutil
    from tempfile import NamedTemporaryFile

    try:
        # Create a temporary copy to avoid locking issues
        with NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            shutil.copy2(DB_PATH, tmp_file.name)
            tmp_path = tmp_file.name

        # Return the database file
        return FileResponse(
            path=tmp_path,
            media_type="application/x-sqlite3",
            filename="scenes.db",
            headers={
                "Content-Disposition": "attachment; filename=scenes.db"
            }
        )
    except Exception as e:
        logger.error(f"Failed to download database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download database: {str(e)}")

class SQLQueryRequest(BaseModel):
    query: str
    params: Optional[List[Any]] = None

@app.post("/api/db/query", tags=["Database"])
async def execute_sql_query(
    request: SQLQueryRequest,
    current_user: Dict = Depends(get_current_admin_user)
):
    """
    Execute a raw SQL query against the database.

    ⚠️ WARNING: This is a powerful endpoint. Only SELECT queries are allowed for safety.

    Supports parameterized queries using ? placeholders.

    Example:
    ```json
    {
        "query": "SELECT * FROM users WHERE id = ?",
        "params": [1]
    }
    ```

    Requires admin authentication.
    """
    from .database import get_db

    # Security: Only allow SELECT queries (read-only)
    query_upper = request.query.strip().upper()
    if not query_upper.startswith('SELECT'):
        raise HTTPException(
            status_code=403,
            detail="Only SELECT queries are allowed. Use database tools for modifications."
        )

    # Additional safety checks
    dangerous_keywords = ['ATTACH', 'DETACH', 'PRAGMA']
    if any(keyword in query_upper for keyword in dangerous_keywords):
        raise HTTPException(
            status_code=403,
            detail=f"Query contains forbidden keywords: {', '.join(dangerous_keywords)}"
        )

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Execute query with parameters if provided
            if request.params:
                cursor.execute(request.query, request.params)
            else:
                cursor.execute(request.query)

            # Fetch results
            rows = cursor.fetchall()

            # Get column names
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
            else:
                columns = []

            # Convert rows to list of dicts
            results = []
            for row in rows:
                results.append(dict(zip(columns, row)))

            return {
                "query": request.query,
                "row_count": len(results),
                "columns": columns,
                "results": results
            }

    except Exception as e:
        logger.error(f"SQL query failed: {e}")
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")

# ============================================================================
# Frontend Serving (catch-all route - must be last)
# ============================================================================

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve the frontend application for all non-API routes."""
    # Don't intercept API routes - they should be handled by their specific endpoints
    if full_path.startswith("api/") or full_path.startswith("data/"):
        raise HTTPException(status_code=404, detail="Not found")

    # Check if we're in production mode with static files
    if STATIC_DIR.exists() and STATIC_DIR.is_dir():
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

    # Fallback for development or if static files don't exist
    return {"message": "Frontend not built. Run 'npm run build' to build the frontend."}

if __name__ == "__main__":
    print("Starting Physics Simulator API server...")
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False  # Disable reload in production
    )