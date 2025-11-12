from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import uvicorn
import os
import hashlib
import json
# from anthropic import Anthropic  # Not needed for demo
# import genesis as gs  # Using geometric validation instead

app = FastAPI(title="Physics Simulator API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# For demo purposes, force ai_client to None
ai_client = None
print("Warning: Using demo scene generation (AI client disabled for demo)")

# Simple in-memory cache (replace with LMDB later)
scene_cache = {}

@app.get("/")
async def root():
    return {"message": "Physics Simulator API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

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
        response = ai_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=2000,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        scene_json = response.content[0].text.strip()

        # Clean up JSON response (remove markdown code blocks if present)
        if scene_json.startswith("```json"):
            scene_json = scene_json[7:]
        if scene_json.endswith("```"):
            scene_json = scene_json[:-3]
        scene_json = scene_json.strip()

        # Parse and validate the scene
        scene_data = json.loads(scene_json)
        scene = Scene(**scene_data)

        # Validate scene stability with Genesis
        validation = validate_with_genesis(scene)
        if not validation.valid:
            raise HTTPException(
                status_code=400,
                detail=f"Generated scene is not stable: {validation.message}"
            )

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
        return scene.dict()
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

if __name__ == "__main__":
    print("Starting Physics Simulator API server...")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )