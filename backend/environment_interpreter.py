"""
Environment Interpretation Module - AI-Assisted Scene Context to Genesis Parameters

Uses LLM to interpret environment settings, narrative, and lighting into detailed
Genesis rendering parameters for photorealistic scene composition.
"""

import json
import logging
from typing import Dict, List, Optional
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class EnvironmentInterpreter:
    """Interprets scene context into Genesis rendering parameters"""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        logger.info(f"Initialized EnvironmentInterpreter with model: {model}")

    async def interpret_scene_context(
        self,
        scene_context: Dict,
        objects: Dict
    ) -> Dict:
        """
        Convert scene context into detailed Genesis rendering parameters.

        Args:
            scene_context: Contains environment, narrative, lighting, renderQuality
            objects: Scene objects for context-aware interpretation

        Returns:
            Detailed rendering parameters for Genesis
        """
        logger.info(f"Interpreting scene context: {scene_context.get('environment', {}).get('timeOfDay', 'unknown')}")

        # Extract scene context components
        environment = scene_context.get("environment", {})
        narrative = scene_context.get("narrative", "")
        lighting = scene_context.get("lighting", {})
        render_quality = scene_context.get("renderQuality", "high")

        # Generate detailed interpretation using LLM
        interpretation = await self._generate_interpretation(
            environment=environment,
            narrative=narrative,
            lighting=lighting,
            render_quality=render_quality,
            object_count=len(objects)
        )

        logger.info(f"Generated environment interpretation with {len(interpretation)} parameters")
        return interpretation

    async def _generate_interpretation(
        self,
        environment: Dict,
        narrative: str,
        lighting: Dict,
        render_quality: str,
        object_count: int
    ) -> Dict:
        """Use LLM to generate detailed rendering parameters"""

        # Construct system prompt
        system_prompt = self._build_system_prompt()

        # Construct user prompt
        user_prompt = self._build_user_prompt(
            environment=environment,
            narrative=narrative,
            lighting=lighting,
            render_quality=render_quality,
            object_count=object_count
        )

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Validate and normalize the interpretation
            validated = self._validate_interpretation(result)

            logger.info(f"LLM interpretation successful")
            return validated

        except Exception as e:
            logger.error(f"Error generating interpretation with LLM: {e}")
            # Fallback to basic interpretation
            return self._fallback_interpretation(environment, lighting, render_quality)

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM"""
        return """You are an expert in photorealistic 3D rendering and cinematography.
Generate detailed rendering parameters for Genesis physics simulation based on scene context.

YOUR TASK:
Convert high-level environment settings into specific rendering parameters including:
- Sky and atmospheric properties
- Lighting configuration (sun/moon position, intensity, color temperature)
- Camera settings (exposure, white balance, depth of field)
- Post-processing effects (bloom, ambient occlusion, color grading)
- Material augmentation (how environment affects object appearance)

RENDERING PARAMETERS TO GENERATE:

1. SKY & ATMOSPHERE:
   - Sky type (procedural, HDRI, gradient)
   - Sun/moon position (altitude, azimuth in degrees)
   - Atmospheric density, haze, fog
   - Cloud coverage and type
   - Sky color and gradient

2. LIGHTING:
   - Directional light (sun/moon) intensity, color temperature (Kelvin), angle
   - Ambient light intensity and color
   - Environment light contribution
   - Shadow quality and softness
   - Indirect lighting / global illumination strength

3. CAMERA:
   - Exposure compensation (EV)
   - White balance (Kelvin)
   - Depth of field (f-stop, focus distance)
   - Tone mapping curve

4. POST-PROCESSING:
   - Bloom intensity and threshold
   - Ambient occlusion strength
   - Color grading (highlights, midtones, shadows tint)
   - Vignette strength
   - Film grain

5. MATERIAL AUGMENTATION:
   - How time of day affects material appearance
   - Weather impact on surfaces (wet, dusty, etc.)
   - Seasonal color shifts

OUTPUT FORMAT (JSON):
{
  "sky": {
    "type": "procedural",
    "sunPosition": {"altitude": 45, "azimuth": 180},
    "atmosphericDensity": 0.5,
    "cloudCoverage": 0.3,
    "skyColor": "#87CEEB"
  },
  "lighting": {
    "directional": {
      "intensity": 1.0,
      "colorTemperature": 5500,
      "angle": [45, 180],
      "castShadows": true,
      "shadowSoftness": 0.3
    },
    "ambient": {
      "intensity": 0.4,
      "color": "#FFFFFF"
    },
    "globalIllumination": 0.7
  },
  "camera": {
    "exposure": 0.0,
    "whiteBalance": 6500,
    "depthOfField": {
      "enabled": true,
      "fStop": 5.6,
      "focusDistance": 10.0
    }
  },
  "postProcessing": {
    "bloom": {"enabled": true, "intensity": 0.2},
    "ambientOcclusion": {"enabled": true, "strength": 0.5},
    "colorGrading": {
      "highlights": "#FFFAED",
      "midtones": "#FFFFFF",
      "shadows": "#0A0F1A"
    },
    "vignette": 0.2,
    "filmGrain": 0.05
  },
  "materialAugmentation": {
    "wetness": 0.0,
    "dust": 0.0,
    "colorShift": "#FFFFFF"
  },
  "description": "Detailed narrative description for Genesis renderer"
}"""

    def _build_user_prompt(
        self,
        environment: Dict,
        narrative: str,
        lighting: Dict,
        render_quality: str,
        object_count: int
    ) -> str:
        """Build user prompt with scene context"""

        time_of_day = environment.get("timeOfDay", "midday")
        weather = environment.get("weather", "clear")
        season = environment.get("season", "summer")
        atmosphere = environment.get("atmosphere", 0.5)

        ambient_intensity = lighting.get("ambientIntensity", 0.4)
        ambient_color = lighting.get("ambientColor", "#FFFFFF")
        directional_intensity = lighting.get("directionalIntensity", 0.8)
        directional_color = lighting.get("directionalColor", "#FFFFCC")
        directional_angle = lighting.get("directionalAngle", 45.0)
        shadows = lighting.get("shadows", True)

        quality_settings = {
            "draft": "Low quality, fast rendering, minimal effects",
            "high": "Balanced quality and performance, standard effects",
            "ultra": "Maximum quality, photorealistic, all effects enabled"
        }
        quality_desc = quality_settings.get(render_quality, quality_settings["high"])

        narrative_section = ""
        if narrative and narrative.strip():
            narrative_section = f"\n\nSCENE NARRATIVE:\n{narrative}"

        return f"""Generate photorealistic rendering parameters for this scene:

ENVIRONMENT:
- Time of Day: {time_of_day}
- Weather: {weather}
- Season: {season}
- Atmospheric Intensity: {atmosphere} (0.0 = crisp/clear, 1.0 = hazy/atmospheric)

LIGHTING (User Preferences):
- Ambient: intensity={ambient_intensity}, color={ambient_color}
- Directional: intensity={directional_intensity}, color={directional_color}, angle={directional_angle}°
- Shadows: {"enabled" if shadows else "disabled"}

RENDER QUALITY: {render_quality}
- {quality_desc}{narrative_section}

SCENE INFO:
- Objects in scene: {object_count}

REQUIREMENTS:
1. Interpret the time of day into realistic sun/moon position and color temperature
2. Apply weather effects (clear = no clouds, rainy = dark clouds + wetness, etc.)
3. Use season to influence color grading and atmospheric qualities
4. Respect user's lighting preferences while enhancing realism
5. Adjust post-processing based on render quality setting
6. If narrative is provided, use it to inform the overall mood and aesthetic
7. Provide a detailed description that combines all elements for the renderer

Generate the rendering parameters as JSON."""

    def _validate_interpretation(self, result: Dict) -> Dict:
        """Validate and normalize LLM interpretation"""

        # Ensure required sections exist
        validated = {
            "sky": result.get("sky", {}),
            "lighting": result.get("lighting", {}),
            "camera": result.get("camera", {}),
            "postProcessing": result.get("postProcessing", {}),
            "materialAugmentation": result.get("materialAugmentation", {}),
            "description": result.get("description", "")
        }

        # Ensure nested structures
        if "directional" not in validated["lighting"]:
            validated["lighting"]["directional"] = {}
        if "ambient" not in validated["lighting"]:
            validated["lighting"]["ambient"] = {}

        # Clamp values to reasonable ranges
        if "atmosphericDensity" in validated["sky"]:
            validated["sky"]["atmosphericDensity"] = max(0.0, min(1.0, validated["sky"]["atmosphericDensity"]))

        if "intensity" in validated["lighting"].get("directional", {}):
            validated["lighting"]["directional"]["intensity"] = max(0.0, validated["lighting"]["directional"]["intensity"])

        if "intensity" in validated["lighting"].get("ambient", {}):
            validated["lighting"]["ambient"]["intensity"] = max(0.0, min(2.0, validated["lighting"]["ambient"]["intensity"]))

        return validated

    def _fallback_interpretation(
        self,
        environment: Dict,
        lighting: Dict,
        render_quality: str
    ) -> Dict:
        """Fallback interpretation if LLM fails"""
        logger.warning("Using fallback environment interpretation")

        time_of_day = environment.get("timeOfDay", "midday")
        weather = environment.get("weather", "clear")

        # Basic time of day mapping
        time_mapping = {
            "dawn": {"altitude": 5, "azimuth": 90, "temp": 3500, "intensity": 0.6},
            "morning": {"altitude": 30, "azimuth": 120, "temp": 4500, "intensity": 0.8},
            "midday": {"altitude": 80, "azimuth": 180, "temp": 5500, "intensity": 1.0},
            "afternoon": {"altitude": 40, "azimuth": 240, "temp": 5000, "intensity": 0.9},
            "evening": {"altitude": 10, "azimuth": 270, "temp": 3000, "intensity": 0.5},
            "dusk": {"altitude": -5, "azimuth": 270, "temp": 2500, "intensity": 0.3},
            "night": {"altitude": -30, "azimuth": 0, "temp": 4000, "intensity": 0.1}
        }

        time_params = time_mapping.get(time_of_day, time_mapping["midday"])

        # Weather effects
        cloud_coverage = 0.0 if weather == "clear" else 0.8 if weather == "rainy" else 0.5
        wetness = 0.8 if weather == "rainy" else 0.0

        return {
            "sky": {
                "type": "procedural",
                "sunPosition": {
                    "altitude": time_params["altitude"],
                    "azimuth": time_params["azimuth"]
                },
                "atmosphericDensity": environment.get("atmosphere", 0.5),
                "cloudCoverage": cloud_coverage,
                "skyColor": "#87CEEB"
            },
            "lighting": {
                "directional": {
                    "intensity": time_params["intensity"] * lighting.get("directionalIntensity", 0.8),
                    "colorTemperature": time_params["temp"],
                    "angle": [lighting.get("directionalAngle", 45.0), time_params["azimuth"]],
                    "castShadows": lighting.get("shadows", True),
                    "shadowSoftness": 0.3
                },
                "ambient": {
                    "intensity": lighting.get("ambientIntensity", 0.4),
                    "color": lighting.get("ambientColor", "#FFFFFF")
                },
                "globalIllumination": 0.7
            },
            "camera": {
                "exposure": 0.0,
                "whiteBalance": time_params["temp"],
                "depthOfField": {
                    "enabled": render_quality == "ultra",
                    "fStop": 5.6,
                    "focusDistance": 10.0
                }
            },
            "postProcessing": {
                "bloom": {"enabled": render_quality != "draft", "intensity": 0.2},
                "ambientOcclusion": {"enabled": render_quality != "draft", "strength": 0.5},
                "colorGrading": {
                    "highlights": "#FFFAED",
                    "midtones": "#FFFFFF",
                    "shadows": "#0A0F1A"
                },
                "vignette": 0.2,
                "filmGrain": 0.05 if render_quality == "ultra" else 0.0
            },
            "materialAugmentation": {
                "wetness": wetness,
                "dust": 0.0,
                "colorShift": "#FFFFFF"
            },
            "description": f"{time_of_day} scene with {weather} weather"
        }


# Utility function for API endpoint
async def interpret_scene_context(
    scene_context: Dict,
    objects: Dict
) -> Dict:
    """
    Convenience function for API endpoint.

    Args:
        scene_context: Scene context with environment, narrative, lighting
        objects: Scene objects

    Returns:
        Detailed rendering parameters for Genesis
    """
    interpreter = EnvironmentInterpreter()
    return await interpreter.interpret_scene_context(
        scene_context=scene_context,
        objects=objects
    )
