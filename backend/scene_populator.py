"""
Scene Population Module - AI-Assisted Object Placement

Uses LLM to intelligently populate scenes with objects based on natural language descriptions.
Generates realistic spatial arrangements and object placements.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ScenePopulator:
    """Populates scenes with AI-generated object placements"""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        logger.info(f"Initialized ScenePopulator with model: {model}")

    async def populate_scene(
        self,
        current_scene: Dict,
        prompt: str,
        num_objects: int = 5,
        placement_strategy: str = "natural",
        bounds: Optional[Dict] = None
    ) -> Dict:
        """
        Populate scene with objects based on natural language description.

        Args:
            current_scene: Existing scene data (may be empty)
            prompt: Natural language description (e.g., "a parking lot with cars and lights")
            num_objects: Target number of objects to add
            placement_strategy: "natural", "grid", or "random"
            bounds: Optional spatial bounds {"min": [x,y,z], "max": [x,y,z]}

        Returns:
            Updated scene with new objects added
        """
        logger.info(f"Populating scene with prompt: '{prompt}', strategy: {placement_strategy}")

        # Default bounds if not provided
        if bounds is None:
            bounds = {"min": [-20, 0, -20], "max": [20, 0, 20]}

        # Get existing object count and types for context
        existing_objects = current_scene.get("objects", {})
        if isinstance(existing_objects, list):
            existing_objects = {f"obj_{i}": obj for i, obj in enumerate(existing_objects)}

        existing_count = len(existing_objects)
        existing_types = self._get_object_types(existing_objects)

        # Generate objects with LLM
        new_objects = await self._generate_objects(
            prompt=prompt,
            num_objects=num_objects,
            placement_strategy=placement_strategy,
            bounds=bounds,
            existing_types=existing_types,
            existing_count=existing_count
        )

        # Merge with existing scene
        updated_scene = current_scene.copy()

        # Convert to dict format if needed
        if "objects" not in updated_scene:
            updated_scene["objects"] = {}
        elif isinstance(updated_scene["objects"], list):
            updated_scene["objects"] = {f"obj_{i}": obj for i, obj in enumerate(updated_scene["objects"])}

        # Add new objects with unique IDs
        for i, obj in enumerate(new_objects):
            obj_id = f"generated_{existing_count + i}"
            updated_scene["objects"][obj_id] = obj

        logger.info(f"Added {len(new_objects)} objects to scene")
        return updated_scene

    def _get_object_types(self, objects: Dict) -> List[str]:
        """Extract object types from existing scene"""
        types = []
        for obj in objects.values():
            if isinstance(obj, dict):
                # Try to get type from description or shape
                desc = obj.get("description", "")
                shape = obj.get("shape", obj.get("physicsProperties", {}).get("shape", "box"))
                types.append(f"{shape}: {desc}" if desc else shape)
        return types

    async def _generate_objects(
        self,
        prompt: str,
        num_objects: int,
        placement_strategy: str,
        bounds: Dict,
        existing_types: List[str],
        existing_count: int
    ) -> List[Dict]:
        """Use LLM to generate object placements"""

        # Construct system prompt
        system_prompt = self._build_system_prompt(placement_strategy, bounds)

        # Construct user prompt with context
        user_prompt = self._build_user_prompt(
            prompt=prompt,
            num_objects=num_objects,
            existing_types=existing_types,
            existing_count=existing_count,
            bounds=bounds
        )

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            objects = result.get("objects", [])

            # Validate and normalize objects
            validated_objects = self._validate_objects(objects, bounds)

            logger.info(f"Generated {len(validated_objects)} objects from LLM")
            return validated_objects

        except Exception as e:
            logger.error(f"Error generating objects with LLM: {e}")
            # Fallback to basic generation
            return self._fallback_generation(prompt, num_objects, bounds)

    def _build_system_prompt(self, placement_strategy: str, bounds: Dict) -> str:
        """Build system prompt for LLM"""
        return f"""You are an expert 3D scene designer. Generate realistic object placements for physics simulations.

PLACEMENT STRATEGY: {placement_strategy}
- "natural": Realistic spacing, consider real-world layouts (e.g., parking spaces are ~2.5m wide)
- "grid": Regular grid pattern with even spacing
- "random": Random but non-overlapping placements

SPATIAL BOUNDS:
- Min: {bounds['min']} (x, y, z in meters)
- Max: {bounds['max']} (x, y, z in meters)
- Y is vertical axis (use 0 for ground level, or height/2 for objects above ground)

OBJECT PROPERTIES TO GENERATE:
1. Position: [x, y, z] within bounds, y should be object height/2 for ground-placed objects
2. Rotation: [rx, ry, rz] in radians (typically 0 for most objects, vary ry for orientation)
3. Shape: "box", "sphere", "cylinder", "capsule"
4. Scale: [sx, sy, sz] in meters (realistic sizes!)
5. Description: Detailed text description for LLM rendering (e.g., "red sports car, Ferrari style")
6. Physics: mass (kg), friction (0-1), restitution (0-1)

REALISM GUIDELINES:
- Cars: ~4.5m long, 1.8m wide, 1.5m tall, mass ~1500kg
- Street lights: ~0.3m diameter, 6m tall, position at y=3m
- Tables: ~1.2m wide, 0.8m tall, mass ~20kg
- Chairs: ~0.5m wide, 1m tall, mass ~5kg
- Ensure objects don't overlap (check positions)
- Use realistic materials (cars are metallic, furniture is wood/metal)

OUTPUT FORMAT (JSON):
{{
  "objects": [
    {{
      "position": [x, y, z],
      "rotation": [rx, ry, rz],
      "shape": "box",
      "scale": [sx, sy, sz],
      "description": "detailed description for rendering",
      "mass": 100.0,
      "friction": 0.5,
      "restitution": 0.3,
      "color": "#RRGGBB"
    }}
  ],
  "reasoning": "brief explanation of placement decisions"
}}"""

    def _build_user_prompt(
        self,
        prompt: str,
        num_objects: int,
        existing_types: List[str],
        existing_count: int,
        bounds: Dict
    ) -> str:
        """Build user prompt with scene context"""
        existing_context = ""
        if existing_count > 0:
            existing_context = f"\n\nEXISTING SCENE OBJECTS ({existing_count}):\n" + "\n".join(f"- {t}" for t in existing_types[:10])

        return f"""Generate {num_objects} objects for this scene:

SCENE DESCRIPTION: {prompt}

REQUIREMENTS:
- Add exactly {num_objects} new objects
- All positions must be within bounds: {bounds['min']} to {bounds['max']}
- Objects should not overlap with each other{existing_context}
- Use realistic scales and physics properties
- Provide detailed descriptions for each object (for AI rendering)

Generate the objects as JSON."""

    def _validate_objects(self, objects: List[Dict], bounds: Dict) -> List[Dict]:
        """Validate and normalize generated objects"""
        validated = []

        for obj in objects:
            try:
                # Ensure required fields
                if "position" not in obj or "shape" not in obj:
                    logger.warning(f"Skipping invalid object: {obj}")
                    continue

                # Normalize structure to match expected format
                normalized = {
                    "transform": {
                        "position": obj.get("position", [0, 0, 0]),
                        "rotation": obj.get("rotation", [0, 0, 0]),
                        "scale": obj.get("scale", [1, 1, 1])
                    },
                    "physicsProperties": {
                        "shape": obj.get("shape", "box"),
                        "mass": obj.get("mass", 10.0),
                        "friction": obj.get("friction", 0.5),
                        "restitution": obj.get("restitution", 0.3),
                        "isDynamic": obj.get("isDynamic", True)
                    },
                    "visualProperties": {
                        "color": obj.get("color", "#808080"),
                        "opacity": obj.get("opacity", 1.0)
                    },
                    "description": obj.get("description", "")
                }

                # Clamp position to bounds
                pos = normalized["transform"]["position"]
                min_bounds = bounds["min"]
                max_bounds = bounds["max"]
                pos[0] = max(min_bounds[0], min(max_bounds[0], pos[0]))
                pos[1] = max(min_bounds[1], min(max_bounds[1], pos[1]))
                pos[2] = max(min_bounds[2], min(max_bounds[2], pos[2]))

                validated.append(normalized)

            except Exception as e:
                logger.warning(f"Error validating object: {e}, object: {obj}")
                continue

        return validated

    def _fallback_generation(self, prompt: str, num_objects: int, bounds: Dict) -> List[Dict]:
        """Fallback object generation if LLM fails"""
        logger.warning("Using fallback object generation")

        import random
        objects = []

        # Simple grid placement
        grid_size = int(num_objects ** 0.5) + 1
        x_min, y_min, z_min = bounds["min"]
        x_max, y_max, z_max = bounds["max"]
        x_step = (x_max - x_min) / (grid_size + 1)
        z_step = (z_max - z_min) / (grid_size + 1)

        for i in range(num_objects):
            row = i // grid_size
            col = i % grid_size

            obj = {
                "transform": {
                    "position": [
                        x_min + (col + 1) * x_step,
                        1.0,  # 1m above ground
                        z_min + (row + 1) * z_step
                    ],
                    "rotation": [0, 0, 0],
                    "scale": [2, 2, 2]
                },
                "physicsProperties": {
                    "shape": random.choice(["box", "sphere", "cylinder"]),
                    "mass": 10.0,
                    "friction": 0.5,
                    "restitution": 0.3,
                    "isDynamic": True
                },
                "visualProperties": {
                    "color": f"#{random.randint(0, 0xFFFFFF):06x}",
                    "opacity": 1.0
                },
                "description": f"object {i+1}"
            }
            objects.append(obj)

        return objects


# Utility function for API endpoint
async def populate_scene_from_prompt(
    current_scene: Dict,
    prompt: str,
    num_objects: int = 5,
    placement_strategy: str = "natural",
    bounds: Optional[Dict] = None
) -> Dict:
    """
    Convenience function for API endpoint.

    Args:
        current_scene: Current scene data
        prompt: Natural language scene description
        num_objects: Number of objects to add
        placement_strategy: How to place objects
        bounds: Spatial constraints

    Returns:
        Updated scene with populated objects
    """
    populator = ScenePopulator()
    return await populator.populate_scene(
        current_scene=current_scene,
        prompt=prompt,
        num_objects=num_objects,
        placement_strategy=placement_strategy,
        bounds=bounds
    )
