from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import uvicorn
import os
import hashlib
import json
from anthropic import Anthropic

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

if __name__ == "__main__":
    print("Starting Physics Simulator API server...")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )