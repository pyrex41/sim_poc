"""
LLM Interpreter for Semantic Scene Augmentation

Takes simple geometry + text descriptions and uses an LLM to generate
detailed Genesis properties (materials, colors, scales, etc.)
"""

import os
import json
from typing import Dict, List, Optional
from openai import OpenAI
from pydantic import BaseModel
from langsmith import traceable


class GenesisProperties(BaseModel):
    """Enhanced properties for Genesis rendering"""
    # Visual properties
    color: tuple[float, float, float]  # RGB 0-1
    metallic: float  # 0-1
    roughness: float  # 0-1
    opacity: float = 1.0
    emissive: tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Geometry adjustments
    scale_multiplier: tuple[float, float, float] = (1.0, 1.0, 1.0)
    suggested_dimensions: Optional[Dict[str, float]] = None  # Real-world dimensions

    # Additional details
    add_details: List[str] = []  # e.g., ["wheels", "windows", "headlights"]
    material_type: str = "generic"  # "metal", "plastic", "glass", "wood", etc.

    # Contextual info
    object_category: str = "unknown"  # "vehicle", "furniture", "building", etc.
    reasoning: str = ""  # LLM's reasoning for choices


class LLMInterpreter:
    """Interprets text descriptions and generates Genesis properties"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # or gpt-4-turbo, gpt-4, gpt-3.5-turbo

    @traceable(name="llm_augment_object", tags=["openai", "genesis", "semantic_augmentation"])
    async def augment_object(
        self,
        shape: str,
        base_dimensions: Dict[str, float],
        description: str,
        context: Optional[str] = None
    ) -> GenesisProperties:
        """
        Augment a simple shape with semantic properties based on description

        Args:
            shape: Base shape type ("Box", "Sphere", "Cylinder", "Capsule")
            base_dimensions: Current dimensions (e.g., {"x": 2.0, "y": 1.0, "z": 4.0})
            description: User's text description (e.g., "blue corvette")
            context: Optional scene context for better interpretation

        Returns:
            GenesisProperties with enhanced rendering properties
        """

        prompt = self._build_augmentation_prompt(
            shape, base_dimensions, description, context
        )

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.3,  # Lower for consistency
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse LLM response
        response_text = response.choices[0].message.content
        properties = self._parse_llm_response(response_text)

        return properties

    def _build_augmentation_prompt(
        self,
        shape: str,
        base_dimensions: Dict[str, float],
        description: str,
        context: Optional[str] = None
    ) -> str:
        """Build the prompt for the LLM"""

        return f"""You are helping create a photorealistic 3D scene. A user has placed a simple {shape} shape and wants it rendered as: "{description}"

Base shape dimensions:
{json.dumps(base_dimensions, indent=2)}

Your task: Generate PBR (Physically Based Rendering) properties to make this shape look like the described object.

Respond with a JSON object containing:
{{
  "color": [R, G, B],  // RGB values 0.0-1.0
  "metallic": 0.0-1.0,  // 0=non-metallic, 1=fully metallic
  "roughness": 0.0-1.0,  // 0=mirror smooth, 1=rough/matte
  "opacity": 0.0-1.0,    // 1=opaque, 0=transparent
  "emissive": [R, G, B], // Self-illumination (usually [0,0,0])
  "scale_multiplier": [x, y, z],  // Adjust proportions (1.0 = no change)
  "suggested_dimensions": {{"length": X, "width": Y, "height": Z}},  // Real-world meters
  "add_details": ["detail1", "detail2"],  // Visual details to emphasize
  "material_type": "metal|plastic|glass|wood|fabric|concrete|ceramic",
  "object_category": "vehicle|furniture|building|nature|electronics|sports",
  "reasoning": "Brief explanation of your choices"
}}

Examples for reference:

"blue corvette" on a Box:
{{
  "color": [0.0, 0.27, 0.67],  // Deep blue
  "metallic": 0.9,  // Car paint is metallic
  "roughness": 0.2,  // Glossy finish
  "scale_multiplier": [1.0, 0.65, 2.25],  // Car proportions (wider, lower, longer)
  "suggested_dimensions": {{"length": 4.5, "width": 1.8, "height": 1.3}},
  "add_details": ["wheels", "windows", "headlights", "spoiler"],
  "material_type": "metal",
  "object_category": "vehicle",
  "reasoning": "Corvette is a sports car with metallic blue paint, low profile, and distinctive aerodynamic shape"
}}

"light pole" on a Cylinder:
{{
  "color": [0.5, 0.5, 0.52],  // Galvanized steel gray
  "metallic": 0.7,  // Metal pole
  "roughness": 0.6,  // Weathered metal
  "scale_multiplier": [1.0, 6.0, 1.0],  // Tall and thin
  "suggested_dimensions": {{"diameter": 0.25, "height": 8.0}},
  "add_details": ["light_bulb", "base_plate", "electrical_box"],
  "material_type": "metal",
  "object_category": "building",
  "reasoning": "Street light poles are typically 8m tall, galvanized steel, with weathered finish"
}}

"wooden coffee table" on a Box:
{{
  "color": [0.55, 0.35, 0.2],  // Walnut brown
  "metallic": 0.0,  // Wood is non-metallic
  "roughness": 0.4,  // Polished wood
  "scale_multiplier": [1.2, 0.4, 0.8],  // Table proportions
  "suggested_dimensions": {{"length": 1.2, "width": 0.6, "height": 0.45}},
  "add_details": ["wood_grain", "table_legs", "surface_reflection"],
  "material_type": "wood",
  "object_category": "furniture",
  "reasoning": "Coffee tables are low, wide, with polished wood finish showing natural grain"
}}

Now generate properties for: "{description}"
Shape: {shape}
Current dimensions: {json.dumps(base_dimensions)}
{f"Scene context: {context}" if context else ""}

Respond with ONLY the JSON object, no other text.
"""

    def _parse_llm_response(self, response: str) -> GenesisProperties:
        """Parse LLM JSON response into GenesisProperties"""

        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            # Convert to GenesisProperties
            return GenesisProperties(
                color=tuple(data["color"]),
                metallic=data["metallic"],
                roughness=data["roughness"],
                opacity=data.get("opacity", 1.0),
                emissive=tuple(data.get("emissive", [0.0, 0.0, 0.0])),
                scale_multiplier=tuple(data.get("scale_multiplier", [1.0, 1.0, 1.0])),
                suggested_dimensions=data.get("suggested_dimensions"),
                add_details=data.get("add_details", []),
                material_type=data.get("material_type", "generic"),
                object_category=data.get("object_category", "unknown"),
                reasoning=data.get("reasoning", "")
            )

        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Response was: {response}")

            # Return default properties on error
            return GenesisProperties(
                color=(0.7, 0.7, 0.7),
                metallic=0.2,
                roughness=0.7,
                reasoning=f"Failed to parse LLM response: {e}"
            )

    @traceable(name="llm_augment_scene", tags=["openai", "genesis", "scene_augmentation"])
    async def augment_scene(
        self,
        scene_objects,
        scene_context: Optional[str] = None
    ):
        """
        Augment all objects in a scene

        Args:
            scene_objects: Dictionary or list of objects with shape, dimensions, and description
            scene_context: Overall scene description for context

        Returns:
            Objects with added 'genesis_properties' field (same type as input)
        """

        # Handle both dict and list inputs
        is_dict = isinstance(scene_objects, dict)
        objects_to_process = scene_objects.values() if is_dict else scene_objects
        augmented_objects = {} if is_dict else []

        for obj in objects_to_process:
            # Skip if no description provided
            if not obj.get("description"):
                if is_dict:
                    augmented_objects[obj["id"]] = obj
                else:
                    augmented_objects.append(obj)
                continue

            # Extract dimensions from object
            shape = obj.get("visualProperties", {}).get("shape", "Box")
            scale = obj.get("transform", {}).get("scale", {"x": 1, "y": 1, "z": 1})

            # Get augmented properties
            properties = await self.augment_object(
                shape=shape,
                base_dimensions=scale,
                description=obj["description"],
                context=scene_context
            )

            # Add to object
            obj["genesis_properties"] = properties.model_dump()

            if is_dict:
                augmented_objects[obj["id"]] = obj
            else:
                augmented_objects.append(obj)

        return augmented_objects


# Singleton instance
_interpreter = None

def get_interpreter() -> LLMInterpreter:
    """Get or create the LLM interpreter singleton"""
    global _interpreter
    if _interpreter is None:
        _interpreter = LLMInterpreter()
    return _interpreter
