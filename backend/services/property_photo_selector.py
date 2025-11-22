"""
Property Photo Selection Service for Luxury Lodging Video Generation.

This service uses xAI Grok to intelligently select optimal image pairs
from crawled property photos based on 7 predefined scene types for
luxury hospitality marketing videos.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from .xai_client import XAIClient

logger = logging.getLogger(__name__)

# Scene type definitions for luxury lodging videos
LUXURY_LODGING_SCENE_TYPES = [
    {
        "scene_number": 1,
        "scene_type": "Grand Arrival",
        "duration": 5,
        "purpose": "Establish property exterior, architectural style, sense of arrival",
        "visual_priority": "Wide establishing shots, impressive architecture, welcoming entrance",
        "mood": "Aspirational, luxurious, inviting",
        "ideal_tags": ["exterior", "architecture", "entrance", "facade", "driveway", "landscape"],
        "first_image_guidance": "Distant/approach view showing full property context",
        "last_image_guidance": "Closer view of entrance or architectural detail",
        "transition_goal": "Viewer feels they're 'arriving' at the property"
    },
    {
        "scene_number": 2,
        "scene_type": "Refined Interiors",
        "duration": 5,
        "purpose": "Showcase lobby/common areas, interior design excellence",
        "visual_priority": "Sophisticated design, attention to detail, spatial luxury",
        "mood": "Elegant, refined, comfortable",
        "ideal_tags": ["lobby", "interior", "lounge", "reception", "design", "furniture", "chandelier"],
        "first_image_guidance": "Wide interior shot showing overall ambiance",
        "last_image_guidance": "Design detail or inviting seating area",
        "transition_goal": "Smooth flow through interior spaces"
    },
    {
        "scene_number": 3,
        "scene_type": "Guest Room Sanctuary",
        "duration": 5,
        "purpose": "Highlight guest room luxury, comfort, amenities",
        "visual_priority": "Bed quality, room spaciousness, view from room, premium finishes",
        "mood": "Serene, comfortable, intimate luxury",
        "ideal_tags": ["bedroom", "suite", "bed", "room_view", "balcony", "bathroom", "amenities"],
        "first_image_guidance": "Room overview showing bed and overall layout",
        "last_image_guidance": "View from room or bathroom luxury detail",
        "transition_goal": "Convey comfort and private retreat feeling"
    },
    {
        "scene_number": 4,
        "scene_type": "Culinary Excellence",
        "duration": 5,
        "purpose": "Feature dining experiences, food quality, restaurant ambiance",
        "visual_priority": "Plated dishes, dining atmosphere, chef craftsmanship",
        "mood": "Sophisticated, appetizing, experiential",
        "ideal_tags": ["restaurant", "dining", "food", "plating", "bar", "wine", "chef", "cuisine"],
        "first_image_guidance": "Restaurant ambiance or beautifully plated dish",
        "last_image_guidance": "Dining detail or culinary presentation",
        "transition_goal": "Evoke desire and culinary anticipation"
    },
    {
        "scene_number": 5,
        "scene_type": "Wellness & Recreation",
        "duration": 5,
        "purpose": "Showcase amenities (pool, spa, fitness, activities)",
        "visual_priority": "Premium facilities, relaxation spaces, activity options",
        "mood": "Rejuvenating, active, leisurely",
        "ideal_tags": ["pool", "spa", "fitness", "yoga", "massage", "wellness", "recreation", "activities"],
        "first_image_guidance": "Wide shot of pool/spa area",
        "last_image_guidance": "Close-up of wellness detail or activity",
        "transition_goal": "Communicate relaxation and vitality"
    },
    {
        "scene_number": 6,
        "scene_type": "Unique Experiences",
        "duration": 5,
        "purpose": "Highlight distinctive property features, local culture, special offerings",
        "visual_priority": "Differentiators, authentic experiences, memorable moments",
        "mood": "Distinctive, experiential, authentic",
        "ideal_tags": ["experience", "unique", "culture", "local", "activity", "sunset", "beach", "nature"],
        "first_image_guidance": "Signature experience or unique property feature",
        "last_image_guidance": "Guest enjoying experience or stunning natural context",
        "transition_goal": "Showcase what makes this property special"
    },
    {
        "scene_number": 7,
        "scene_type": "Lasting Impression",
        "duration": 5,
        "purpose": "Close with memorable hero shot, emotional resonance",
        "visual_priority": "Stunning vista, iconic property angle, sunset/golden hour",
        "mood": "Inspirational, memorable, desire-to-return",
        "ideal_tags": ["sunset", "view", "landscape", "ocean", "mountains", "hero_shot", "panorama"],
        "first_image_guidance": "Beautiful wide shot of property in context",
        "last_image_guidance": "Ultimate 'hero shot' - most stunning property moment",
        "transition_goal": "Leave viewer inspired and wanting to book"
    }
]


class PropertyPhotoSelector:
    """Selects optimal image pairs from property photos using AI."""

    def __init__(self, xai_api_key: Optional[str] = None):
        """
        Initialize the property photo selector.

        Args:
            xai_api_key: Optional xAI API key. If not provided, uses env variable.
        """
        self.xai_client = XAIClient(api_key=xai_api_key)

    def select_scene_image_pairs(
        self,
        property_info: Dict[str, Any],
        photos: List[Dict[str, Any]],
        scene_types: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Select optimal image pairs for each scene type from property photos.

        Args:
            property_info: Dict with keys:
                - name: Property name
                - location: Property location
                - property_type: Type of property (e.g., "boutique hotel")
                - positioning: Brand positioning (e.g., "eco-luxury")
            photos: List of photo dicts with keys:
                - id: Unique photo identifier
                - filename: Photo filename
                - url: URL to photo
                - tags: List of tags (optional)
                - dominant_colors: List of colors (optional)
                - detected_objects: List of objects (optional)
                - composition: Composition style (optional)
                - lighting: Lighting conditions (optional)
                - resolution: Resolution (optional)
                - aspect_ratio: Aspect ratio (optional)
            scene_types: Optional custom scene types. Defaults to luxury lodging scenes.

        Returns:
            Dict with structure:
            {
                "property_name": str,
                "selection_metadata": {...},
                "scene_pairs": [
                    {
                        "scene_number": int,
                        "scene_type": str,
                        "first_image": {...},
                        "last_image": {...},
                        "transition_analysis": {...}
                    }
                ],
                "recommendations": {...}
            }
        """
        if not photos or len(photos) < 14:
            raise ValueError(f"Need at least 14 photos to select 7 pairs, got {len(photos)}")

        scene_types = scene_types or LUXURY_LODGING_SCENE_TYPES

        if len(scene_types) != 7:
            raise ValueError(f"Expected 7 scene types, got {len(scene_types)}")

        logger.info(
            f"Selecting image pairs for property '{property_info.get('name')}' "
            f"from {len(photos)} photos across {len(scene_types)} scenes"
        )

        # Call Grok with custom prompt
        try:
            result = self.xai_client.select_property_scene_pairs(
                property_info=property_info,
                photos=photos,
                scene_types=scene_types
            )

            # Validate result
            if not result.get("scene_pairs"):
                raise ValueError("Grok returned no scene pairs")

            if len(result["scene_pairs"]) != 7:
                logger.warning(
                    f"Expected 7 scene pairs, got {len(result['scene_pairs'])}. "
                    "Filling missing scenes with best available photos."
                )

            # Ensure we have exactly 7 pairs
            result["scene_pairs"] = self._ensure_seven_pairs(
                result["scene_pairs"],
                photos,
                scene_types
            )

            # Validate no duplicate images
            self._validate_no_duplicates(result["scene_pairs"])

            logger.info(
                f"Successfully selected {len(result['scene_pairs'])} scene pairs "
                f"with confidence {result.get('selection_metadata', {}).get('selection_confidence', 'unknown')}"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to select property scene pairs: {e}", exc_info=True)
            raise

    def _ensure_seven_pairs(
        self,
        scene_pairs: List[Dict[str, Any]],
        photos: List[Dict[str, Any]],
        scene_types: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Ensure exactly 7 scene pairs exist, filling gaps with fallback selections.

        Args:
            scene_pairs: Existing scene pairs from Grok
            photos: Available photos
            scene_types: Scene type definitions

        Returns:
            List of exactly 7 scene pairs
        """
        if len(scene_pairs) == 7:
            return scene_pairs

        # Get scene numbers that are missing
        existing_scene_nums = {pair["scene_number"] for pair in scene_pairs}
        missing_scene_nums = set(range(1, 8)) - existing_scene_nums

        # Get IDs of already used photos
        used_photo_ids = set()
        for pair in scene_pairs:
            used_photo_ids.add(pair["first_image"]["id"])
            used_photo_ids.add(pair["last_image"]["id"])

        # Fill missing scenes with available photos
        available_photos = [p for p in photos if p["id"] not in used_photo_ids]

        for scene_num in sorted(missing_scene_nums):
            if len(available_photos) < 2:
                logger.warning(f"Not enough photos to fill scene {scene_num}")
                break

            scene_type = scene_types[scene_num - 1]

            # Simple fallback: take first two available photos
            first_photo = available_photos.pop(0)
            last_photo = available_photos.pop(0)

            scene_pairs.append({
                "scene_number": scene_num,
                "scene_type": scene_type["scene_type"],
                "first_image": {
                    "id": first_photo["id"],
                    "filename": first_photo.get("filename", ""),
                    "reasoning": "Fallback selection - insufficient Grok coverage",
                    "quality_score": 7.0,
                    "tag_match_score": 7.0
                },
                "last_image": {
                    "id": last_photo["id"],
                    "filename": last_photo.get("filename", ""),
                    "reasoning": "Fallback selection - insufficient Grok coverage",
                    "quality_score": 7.0,
                    "tag_match_score": 7.0
                },
                "transition_analysis": {
                    "color_compatibility": "unknown",
                    "lighting_consistency": "unknown",
                    "compositional_flow": "fallback",
                    "interpolation_confidence": 7.0
                }
            })

            used_photo_ids.add(first_photo["id"])
            used_photo_ids.add(last_photo["id"])

        # Sort by scene number
        scene_pairs.sort(key=lambda x: x["scene_number"])

        return scene_pairs

    def _validate_no_duplicates(self, scene_pairs: List[Dict[str, Any]]) -> None:
        """
        Validate that no image is used more than once across all scene pairs.

        Args:
            scene_pairs: List of scene pair dicts

        Raises:
            ValueError: If duplicate images are found
        """
        used_images = set()

        for pair in scene_pairs:
            first_id = pair["first_image"]["id"]
            last_id = pair["last_image"]["id"]

            if first_id in used_images:
                raise ValueError(f"Duplicate image detected: {first_id} used in multiple scenes")
            if last_id in used_images:
                raise ValueError(f"Duplicate image detected: {last_id} used in multiple scenes")

            used_images.add(first_id)
            used_images.add(last_id)

        logger.debug(f"Validated {len(used_images)} unique images across {len(scene_pairs)} scene pairs")

    def convert_to_video_generation_format(
        self,
        selection_result: Dict[str, Any]
    ) -> List[Tuple[str, str, float, str]]:
        """
        Convert Grok's selection result to video generation format.

        Args:
            selection_result: Result from select_scene_image_pairs()

        Returns:
            List of tuples: (image1_id, image2_id, score, reasoning)
            Ordered by scene number (1-7)
        """
        pairs = []

        for scene_pair in selection_result["scene_pairs"]:
            image1_id = scene_pair["first_image"]["id"]
            image2_id = scene_pair["last_image"]["id"]

            # Use interpolation confidence as score
            score = scene_pair.get("transition_analysis", {}).get("interpolation_confidence", 8.0) / 10.0

            # Combine reasoning from both images and transition
            reasoning = (
                f"Scene {scene_pair['scene_number']}: {scene_pair['scene_type']}. "
                f"{scene_pair['first_image'].get('reasoning', '')} → "
                f"{scene_pair['last_image'].get('reasoning', '')} "
                f"[{scene_pair.get('transition_analysis', {}).get('compositional_flow', 'unknown')}]"
            )

            pairs.append((image1_id, image2_id, score, reasoning))

        return pairs
