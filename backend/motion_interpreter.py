"""
Motion Interpretation Module - AI-Assisted Motion Description to Animation

Uses LLM to interpret natural language motion descriptions into Genesis animation
parameters including keyframes, velocities, forces, and trajectories.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class MotionInterpreter:
    """Interprets motion descriptions into Genesis animation parameters"""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        logger.info(f"Initialized MotionInterpreter with model: {model}")

    async def interpret_motion(
        self,
        motion_prompt: str,
        objects: Dict,
        duration: float = 5.0,
        fps: int = 60
    ) -> Dict:
        """
        Convert motion description into Genesis animation parameters.

        Args:
            motion_prompt: Natural language description of motion
            objects: Scene objects that can be animated
            duration: Total duration in seconds
            fps: Frames per second

        Returns:
            Animation data with keyframes, forces, and trajectories per object
        """
        logger.info(f"Interpreting motion: '{motion_prompt[:50]}...'")

        # Generate motion parameters using LLM
        motion_data = await self._generate_motion(
            motion_prompt=motion_prompt,
            objects=objects,
            duration=duration,
            fps=fps
        )

        logger.info(f"Generated motion for {len(motion_data.get('animations', {}))} objects")
        return motion_data

    async def _generate_motion(
        self,
        motion_prompt: str,
        objects: Dict,
        duration: float,
        fps: int
    ) -> Dict:
        """Use LLM to generate motion parameters"""

        # Build object context
        object_summaries = self._summarize_objects(objects)

        # Construct prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            motion_prompt=motion_prompt,
            object_summaries=object_summaries,
            duration=duration,
            fps=fps
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

            # Validate and normalize
            validated = self._validate_motion(result, objects, duration, fps)

            logger.info(f"LLM motion generation successful")
            return validated

        except Exception as e:
            logger.error(f"Error generating motion with LLM: {e}")
            # Fallback to simple motion
            return self._fallback_motion(objects, duration, fps)

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM"""
        return """You are an expert in physics simulation and 3D animation.
Generate realistic motion parameters for Genesis physics engine based on natural language descriptions.

YOUR TASK:
Convert motion descriptions into precise animation data including:
- Keyframe animations (position, rotation over time)
- Physics forces (impulses, continuous forces, torques)
- Velocity/angular velocity changes
- Trajectory paths for smooth motion

MOTION TYPES TO GENERATE:

1. KEYFRAME ANIMATION:
   - Position keyframes: [[time, [x, y, z]], ...]
   - Rotation keyframes: [[time, [rx, ry, rz]], ...]
   - Scale keyframes (optional): [[time, [sx, sy, sz]], ...]
   - Interpolation: "linear", "ease-in-out", "bezier"

2. PHYSICS FORCES:
   - Initial velocity: [vx, vy, vz] m/s
   - Initial angular velocity: [wx, wy, wz] rad/s
   - Applied forces: [[time, [fx, fy, fz]], ...] in Newtons
   - Impulses: [[time, [ix, iy, iz]], ...] in N⋅s
   - Torques: [[time, [tx, ty, tz]], ...] in N⋅m

3. CONSTRAINTS:
   - Keep object grounded: fixedY = true
   - Lock rotation: lockRotation = [x, y, z] bools
   - Follow path: pathPoints = [[x,y,z], ...]

REALISM GUIDELINES:
- Car acceleration: 0-60mph in ~6s = 4.5 m/s² → use gradual force application
- Gravity: 9.81 m/s² downward (automatically applied)
- Friction/drag: objects naturally decelerate
- Rotation: smooth angular velocities (avoid sudden spins)
- Timing: realistic speeds (walking ~1.5 m/s, car ~13 m/s city driving)

COORDINATE SYSTEM:
- X: left/right, Y: up/down, Z: forward/backward
- Rotations in radians (π rad = 180°)
- Right-hand rule for rotations

OUTPUT FORMAT (JSON):
{
  "animations": {
    "object_id": {
      "type": "keyframe" | "physics" | "hybrid",
      "positionKeyframes": [[0.0, [0, 0, 0]], [2.0, [5, 0, 0]]],
      "rotationKeyframes": [[0.0, [0, 0, 0]], [2.0, [0, 1.57, 0]]],
      "interpolation": "ease-in-out",
      "initialVelocity": [2.0, 0, 0],
      "initialAngularVelocity": [0, 0, 0],
      "forces": [[1.0, [10, 0, 0]], [3.0, [-5, 0, 0]]],
      "impulses": [[0.5, [50, 0, 0]]],
      "constraints": {
        "fixedY": false,
        "lockRotation": [false, true, false],
        "pathPoints": []
      }
    }
  },
  "cameraAnimation": {
    "positionKeyframes": [[0.0, [8, 6, 8]], [5.0, [10, 8, 10]]],
    "lookatKeyframes": [[0.0, [0, 2, 0]], [5.0, [5, 2, 0]]],
    "interpolation": "ease-in-out"
  },
  "description": "Technical description of the motion choreography"
}"""

    def _build_user_prompt(
        self,
        motion_prompt: str,
        object_summaries: List[str],
        duration: float,
        fps: int
    ) -> str:
        """Build user prompt with motion context"""

        objects_list = "\n".join(f"- {summary}" for summary in object_summaries)
        num_frames = int(duration * fps)

        return f"""Generate animation parameters for this motion:

MOTION DESCRIPTION: {motion_prompt}

SCENE OBJECTS:
{objects_list}

ANIMATION PARAMETERS:
- Duration: {duration} seconds
- Frame rate: {fps} fps ({num_frames} total frames)
- Coordinate system: Y-up, X-right, Z-forward

REQUIREMENTS:
1. Identify which objects should animate based on the description
2. Choose appropriate animation type (keyframe for precise control, physics for realistic dynamics)
3. Generate smooth, realistic motion with proper timing
4. Include camera animation if the description implies camera movement
5. Ensure motion fits within the duration
6. Use realistic physics values (forces, velocities)
7. Provide detailed technical description of what happens

EXAMPLES:
- "car drives forward 10 meters" → physics with initial velocity [3.33, 0, 0] over 3s
- "ball bounces 3 times" → physics with initial velocity [0, 8, 0] and restitution
- "camera circles around object" → camera keyframes in arc pattern
- "robot arm reaches for cube" → keyframe animation with smooth interpolation

Generate the animation parameters as JSON."""

    def _summarize_objects(self, objects: Dict) -> List[str]:
        """Create human-readable object summaries"""
        summaries = []
        for obj_id, obj in objects.items():
            if isinstance(obj, dict):
                pos = obj.get("transform", {}).get("position", [0, 0, 0])
                scale = obj.get("transform", {}).get("scale", [1, 1, 1])
                shape = obj.get("physicsProperties", {}).get("shape", "box")
                mass = obj.get("physicsProperties", {}).get("mass", 1.0)
                desc = obj.get("description", "")

                summary = f"{obj_id} ({shape}, mass={mass}kg, size={scale}, pos={pos})"
                if desc:
                    summary += f" - {desc}"
                summaries.append(summary)

        return summaries

    def _validate_motion(
        self,
        result: Dict,
        objects: Dict,
        duration: float,
        fps: int
    ) -> Dict:
        """Validate and normalize motion data"""

        validated = {
            "animations": {},
            "cameraAnimation": result.get("cameraAnimation", {}),
            "description": result.get("description", "")
        }

        animations = result.get("animations", {})

        for obj_id, anim in animations.items():
            # Ensure object exists
            if obj_id not in objects:
                logger.warning(f"Animation for non-existent object: {obj_id}")
                continue

            # Normalize animation structure
            normalized = {
                "type": anim.get("type", "hybrid"),
                "positionKeyframes": anim.get("positionKeyframes", []),
                "rotationKeyframes": anim.get("rotationKeyframes", []),
                "scaleKeyframes": anim.get("scaleKeyframes", []),
                "interpolation": anim.get("interpolation", "ease-in-out"),
                "initialVelocity": anim.get("initialVelocity", [0, 0, 0]),
                "initialAngularVelocity": anim.get("initialAngularVelocity", [0, 0, 0]),
                "forces": anim.get("forces", []),
                "impulses": anim.get("impulses", []),
                "torques": anim.get("torques", []),
                "constraints": anim.get("constraints", {})
            }

            # Validate keyframe times are within duration
            for keyframe_list in [normalized["positionKeyframes"],
                                 normalized["rotationKeyframes"],
                                 normalized["scaleKeyframes"]]:
                for kf in keyframe_list:
                    if len(kf) >= 1 and kf[0] > duration:
                        kf[0] = duration

            # Validate force/impulse times
            for force_list in [normalized["forces"], normalized["impulses"], normalized["torques"]]:
                for force in force_list:
                    if len(force) >= 1 and force[0] > duration:
                        force[0] = duration

            validated["animations"][obj_id] = normalized

        return validated

    def _fallback_motion(
        self,
        objects: Dict,
        duration: float,
        fps: int
    ) -> Dict:
        """Fallback motion generation if LLM fails"""
        logger.warning("Using fallback motion generation")

        # Simple forward motion for first dynamic object
        animations = {}

        for obj_id, obj in objects.items():
            if isinstance(obj, dict):
                is_dynamic = obj.get("physicsProperties", {}).get("isDynamic", False)
                if is_dynamic:
                    # Simple forward motion
                    animations[obj_id] = {
                        "type": "physics",
                        "positionKeyframes": [],
                        "rotationKeyframes": [],
                        "scaleKeyframes": [],
                        "interpolation": "linear",
                        "initialVelocity": [2.0, 0, 0],  # 2 m/s forward
                        "initialAngularVelocity": [0, 0, 0],
                        "forces": [],
                        "impulses": [],
                        "torques": [],
                        "constraints": {}
                    }
                    break  # Only animate first dynamic object

        return {
            "animations": animations,
            "cameraAnimation": {},
            "description": "Simple forward motion (fallback)"
        }


# Utility function for API endpoint
async def interpret_motion(
    motion_prompt: str,
    objects: Dict,
    duration: float = 5.0,
    fps: int = 60
) -> Dict:
    """
    Convenience function for API endpoint.

    Args:
        motion_prompt: Natural language motion description
        objects: Scene objects
        duration: Animation duration
        fps: Frames per second

    Returns:
        Animation data for Genesis
    """
    interpreter = MotionInterpreter()
    return await interpreter.interpret_motion(
        motion_prompt=motion_prompt,
        objects=objects,
        duration=duration,
        fps=fps
    )
