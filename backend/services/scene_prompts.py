"""
Scene-specific prompts for luxury property video generation.

Provides professional cinematography prompts for different property scenes.
"""

from typing import Dict, List, Any

# Professional luxury real estate scene templates
LUXURY_PROPERTY_SCENES = [
    {
        "scene_number": 1,
        "name": "The Hook (Exterior Feature)",
        "duration": 1.5,
        "ideal_tags": ["exterior", "pool", "courtyard", "terrace", "water"],
        "motion_goal": "Immediate visual interest with subtle water or surface movement + gentle forward motion",
        "prompt": (
            "Cinematic wide shot, low angle. Clear water or reflective surface gently rippling. "
            "Subtle, smooth camera push-in (dolly forward). Bright natural lighting with glistening "
            "highlights on the water/surface. Photorealistic 4K, high fidelity, sharp focus on the edge detail."
        ),
        "music_prompt": (
            "Cinematic ambient opening, gentle water sounds, soft synthesizer pads, "
            "subtle orchestral strings, uplifting and inviting, 120 BPM"
        )
    },
    {
        "scene_number": 2,
        "name": "The Hero Bedroom (Parallax)",
        "duration": 1.0,
        "ideal_tags": ["bedroom", "master bedroom", "interior", "windows"],
        "motion_goal": "Lateral movement to reveal depth between foreground and background",
        "prompt": (
            "Smooth sideways camera truck (left or right – choose direction that creates natural parallax). "
            "Luxurious bedroom with large windows or glass walls. Parallax effect: bed and foreground elements "
            "move slightly faster than the background view. Soft natural light, no zoom, pure linear sideways motion."
        ),
        "music_prompt": (
            "Soft luxurious ambiance, gentle piano melody, warm pad atmosphere, "
            "elegant and serene, subtle string harmonies"
        )
    },
    {
        "scene_number": 3,
        "name": "Bathroom Vanity (Symmetry)",
        "duration": 1.0,
        "ideal_tags": ["bathroom", "vanity", "interior", "mirror"],
        "motion_goal": "Smooth sliding movement (opposite direction to Scene 2 for flow)",
        "prompt": (
            "Cinematic sideways truck (left or right – opposite of Scene 2). Modern bathroom vanity with mirror. "
            "Reflections shift naturally as camera moves. Clean, bright lighting, sharp focus on surfaces and fixtures."
        ),
        "music_prompt": (
            "Clean spa-like ambiance, subtle chimes, flowing water undertones, "
            "peaceful and modern, minimal percussion"
        )
    },
    {
        "scene_number": 4,
        "name": "The Feature Tub / Shower (Depth)",
        "duration": 1.0,
        "ideal_tags": ["bathroom", "tub", "shower", "spa"],
        "motion_goal": "Intimate push-in to emphasize the luxury fixture",
        "prompt": (
            "Slow, smooth dolly forward toward the centerpiece tub or shower. Background view through window "
            "or opening remains steady. Serene spa-like atmosphere, soft balanced lighting, high detail on "
            "textures and materials."
        ),
        "music_prompt": (
            "Serene spa atmosphere, gentle harp arpeggios, soft ambient pads, "
            "tranquil and meditative, nature sounds"
        )
    },
    {
        "scene_number": 5,
        "name": "Living Room (The Sweep)",
        "duration": 1.0,
        "ideal_tags": ["living room", "interior", "seating", "lounge"],
        "motion_goal": "Sweeping movement to reveal scale and flow of the space",
        "prompt": (
            "Wide shot, smooth sideways pan or truck (choose direction that follows the natural lines of "
            "furniture/layout). Spacious living room with prominent seating. Natural light streaming in, "
            "subtle atmospheric particles in the air. Fluid, steady camera motion."
        ),
        "music_prompt": (
            "Spacious orchestral sweep, warm string section, elegant movement, "
            "building energy, sophisticated and grand"
        )
    },
    {
        "scene_number": 6,
        "name": "Lifestyle / Dining Area (Atmosphere)",
        "duration": 1.0,
        "ideal_tags": ["dining", "kitchen", "lifestyle", "indoor-outdoor"],
        "motion_goal": "Near-static shot that lets the lighting and ambiance breathe",
        "prompt": (
            "Almost static tripod shot with very subtle handheld float or gentle drift. Elegant dining or "
            "lifestyle area. Warm, inviting lighting. Minimal natural movement (candles, slight breeze, "
            "or soft fabric sway if present)."
        ),
        "music_prompt": (
            "Warm inviting atmosphere, acoustic guitar fingerpicking, soft jazz undertones, "
            "intimate and cozy, evening ambiance"
        )
    },
    {
        "scene_number": 7,
        "name": "The Outro (Establishing Wide)",
        "duration": 3.5,  # Adjusted to fit 10s total (1.5 + 1.0*5 + 3.5 = 10.0)
        "ideal_tags": ["exterior", "deck", "entrance", "view", "establishing"],
        "motion_goal": "Gentle pull-back to leave the viewer with a lasting impression",
        "prompt": (
            "Smooth dolly outward or subtle drone-style pull-back. Establishing shot of the property at its "
            "most inviting time of day. Warm interior glow visible through windows (if applicable). "
            "Calm, cinematic, and peaceful closing moment."
        ),
        "music_prompt": (
            "Grand cinematic finale, full orchestral swell, inspiring and aspirational, "
            "peaceful resolution, warm golden hour feeling, uplifting conclusion"
        )
    }
]


def get_scene_prompt(scene_number: int) -> Dict[str, Any]:
    """
    Get the prompt template for a specific scene number.

    Args:
        scene_number: Scene number (1-7)

    Returns:
        Dictionary containing scene metadata and prompt
    """
    if 1 <= scene_number <= len(LUXURY_PROPERTY_SCENES):
        return LUXURY_PROPERTY_SCENES[scene_number - 1]
    else:
        # Fallback to generic transition
        return {
            "scene_number": scene_number,
            "name": "Generic Transition",
            "duration": 1.0,
            "ideal_tags": [],
            "motion_goal": "Smooth transition",
            "prompt": "Smooth cinematic transition between images"
        }


def get_all_scenes() -> List[Dict[str, Any]]:
    """
    Get all luxury property scene templates.

    Returns:
        List of all scene dictionaries
    """
    return LUXURY_PROPERTY_SCENES


def match_scene_to_tags(tags: List[str]) -> int:
    """
    Match asset tags to the most appropriate scene number.

    Args:
        tags: List of asset tags

    Returns:
        Best matching scene number (1-7)
    """
    if not tags:
        return 1  # Default to Scene 1

    tag_set = set(tag.lower() for tag in tags)

    best_match = 1
    best_score = 0

    for scene in LUXURY_PROPERTY_SCENES:
        # Calculate overlap score
        ideal_tags_set = set(tag.lower() for tag in scene["ideal_tags"])
        overlap = len(tag_set & ideal_tags_set)

        if overlap > best_score:
            best_score = overlap
            best_match = scene["scene_number"]

    return best_match


def get_total_duration() -> float:
    """
    Get total duration of all scenes.

    Returns:
        Total duration in seconds
    """
    return sum(scene["duration"] for scene in LUXURY_PROPERTY_SCENES)
