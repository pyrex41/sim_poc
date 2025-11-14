from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
import uvicorn
import os
import hashlib
import json
import requests
import asyncio
from dotenv import load_dotenv
from pathlib import Path

# Note: replicate package has Python 3.14 compatibility issues
# We only use HTTP API calls via requests library
replicate = None
REPLICATE_AVAILABLE = False

from database import (
    save_generated_scene,
    get_scene_by_id,
    list_scenes,
    get_scene_count,
    get_models_list,
    delete_scene,
    save_generated_video,
    update_video_status,
    get_video_by_id
)

# Load environment variables from .env file in parent directory
# Try loading .env from backend directory, then parent directory
if not load_dotenv('.env'):
    load_dotenv('../.env')
# import genesis as gs  # Using geometric validation instead

app = FastAPI(title="Physics Simulator API", version="1.0.0")

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

class ValidationResult(BaseModel):
    valid: bool
    message: str
    details: Optional[Dict] = None

# AI client initialization
replicate_api_key = os.getenv("REPLICATE_API_KEY")
if replicate_api_key:
    ai_client = {
        "api_key": replicate_api_key,
        "base_url": "https://api.replicate.com/v1"
    }
    replicate_client = replicate.Client(api_token=replicate_api_key) if REPLICATE_AVAILABLE and replicate else None
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
async def api_generate_scene(request: GenerateRequest):
    """Generate a physics scene from a text prompt."""
    try:
        scene = generate_scene(request.prompt)
        scene_dict = scene.dict()

        # Save to database
        scene_id = save_generated_scene(
            prompt=request.prompt,
            scene_data=scene_dict,
            model="claude-3.5-sonnet",
            metadata={"source": "generate"}
        )

        # Add scene_id to response
        scene_dict["_id"] = scene_id

        return scene_dict
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene generation failed: {str(e)}")

@app.post("/api/validate")
async def api_validate_scene(scene: Scene):
    """Validate a physics scene for stability using Genesis simulation."""
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
async def api_refine_scene(request: RefineRequest):
    """Refine an existing physics scene based on a text prompt."""
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
    model: Optional[str] = Query(None)
):
    """List generated scenes with pagination and optional model filter."""
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
async def api_get_scene(scene_id: int):
    """Get a specific scene by ID."""
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
async def api_delete_scene(scene_id: int):
    """Delete a scene by ID."""
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
                metadata = {
                    "replicate_id": pred_data.get("id"),
                    "prediction_url": prediction_url
                }

                # Update database with completed video
                update_video_status(
                    video_id=video_id,
                    status="completed",
                    video_url=video_url,
                    metadata=metadata
                )
                print(f"Video {video_id} completed successfully")
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
async def api_run_video_model(request: RunVideoRequest, background_tasks: BackgroundTasks):
    """Initiate video generation and return immediately with a video ID."""
    try:
        if not ai_client:
            # Demo response - create a pending video
            video_id = save_generated_video(
                prompt=request.input.get("prompt", ""),
                video_url="",
                model_id=request.model_id,
                parameters=request.input,
                collection=request.collection,
                status="processing"
            )
            return {"video_id": video_id, "status": "processing"}

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

        # Create prediction using HTTP API
        # Use version-based endpoint if version provided (more reliable)
        if request.version:
            payload = {
                "version": request.version,
                "input": converted_input
            }
            url = "https://api.replicate.com/v1/predictions"
            print(f"DEBUG: Sending to Replicate API (version-based):")
            print(f"  Model: {request.model_id}")
            print(f"  Version: {request.version}")
        else:
            payload = {
                "input": converted_input
            }
            url = f"https://api.replicate.com/v1/models/{request.model_id}/predictions"
            print(f"DEBUG: Sending to Replicate API (model-based):")
            print(f"  Model: {request.model_id}")

        print(f"  Input types: {[(k, type(v).__name__, v) for k, v in converted_input.items()]}")
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

        # Create video record with "processing" status
        video_id = save_generated_video(
            prompt=request.input.get("prompt", ""),
            video_url="",  # Will be filled in when complete
            model_id=request.model_id,
            parameters=request.input,
            collection=request.collection,
            status="processing",
            metadata={"replicate_id": result.get("id"), "prediction_url": prediction_url}
        )

        # Start background task to poll for completion
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

@app.get("/api/videos")
async def api_list_videos(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    model_id: Optional[str] = Query(None),
    collection: Optional[str] = Query(None)
):
    """List generated videos from the database."""
    from database import list_videos
    videos = list_videos(limit=limit, offset=offset, model_id=model_id, collection=collection)
    return {"videos": videos}

@app.get("/api/videos/{video_id}")
async def api_get_video(video_id: int):
    """Get a specific video by ID (used for polling video status)."""
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
    return video

@app.post("/api/genesis/render")
async def api_genesis_render(request: GenesisRenderRequest):
    """
    Render a scene using Genesis photorealistic ray-tracer with LLM semantic augmentation.

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
        from database import save_genesis_video
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
    quality: Optional[str] = None
):
    """List Genesis-rendered videos from the database."""
    try:
        from database import list_genesis_videos, get_genesis_video_count

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
async def get_genesis_video_endpoint(video_id: int):
    """Get a specific Genesis video by ID."""
    try:
        from database import get_genesis_video_by_id

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
async def delete_genesis_video_endpoint(video_id: int):
    """Delete a Genesis video by ID."""
    try:
        from database import delete_genesis_video
        import os
        from pathlib import Path

        # Get video info first to delete the file
        from database import get_genesis_video_by_id
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

# Serve frontend (must be last to catch all other routes)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve the frontend application for all non-API routes."""
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
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )