"""
xAI Grok-4-fast-1 client for AI-powered image pair selection.

This service uses Grok's vision capabilities to intelligently select
and order image pairs from campaign assets for video generation.
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import requests

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class XAIClient:
    """Client for interacting with xAI's Grok API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the xAI client.

        Args:
            api_key: Optional API key. If not provided, will use XAI_API_KEY from settings.
        """
        self.api_key = api_key or settings.XAI_API_KEY
        if not self.api_key:
            raise ValueError("XAI_API_KEY must be set in environment or passed to XAIClient")

        self.base_url = "https://api.x.ai/v1"
        self.model = "grok-4-1-fast-non-reasoning"

    def _group_assets_by_room(self, assets: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group assets by room type extracted from tags.

        For tags like ["Bedroom 1 2"], extracts "Bedroom" as the room type.
        For tags like ["Ensuite Bathroom 1 1"], extracts "Ensuite Bathroom".
        """
        from collections import defaultdict
        import json

        room_groups = defaultdict(list)

        for asset in assets:
            tags = asset.get('tags', [])

            # Handle tags stored as JSON string
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []

            if tags and len(tags) > 0:
                tag = tags[0]  # Use first tag

                # Extract room type from tag
                parts = tag.split()
                if len(parts) >= 1:
                    # Handle multi-word room types
                    if parts[0] in ['Ensuite', 'Half', 'Dining', 'Living', 'Laundry', 'Tv']:
                        room_type = ' '.join(parts[:2]) if len(parts) >= 2 else parts[0]
                    else:
                        room_type = parts[0]

                    room_groups[room_type].append(asset)

        return dict(room_groups)

    def select_image_pairs(
        self,
        assets: List[Dict[str, Any]],
        campaign_context: Optional[Dict[str, Any]] = None,
        client_brand_guidelines: Optional[Dict[str, Any]] = None,
        num_pairs: Optional[int] = None,
    ) -> List[Tuple[str, str, float, str]]:
        """
        Two-stage selection process for luxury property videos:

        Stage 1: Select which room types to feature (e.g., best 7 rooms)
        Stage 2: For each selected room, pick best 2 images to form a pair

        Args:
            assets: List of asset dicts with keys: id, name, description, tags, url, type
            campaign_context: Optional campaign info (goal, targetAudience, keyMessage, etc.)
            client_brand_guidelines: Optional brand guidelines (colors, tone, restrictions)
            num_pairs: Optional target number of pairs. If not specified, Grok decides.

        Returns:
            List of tuples: (image1_id, image2_id, score, reasoning)
            Ordered by quality score (highest first)
        """
        import concurrent.futures

        if not assets or len(assets) < 2:
            raise ValueError("Need at least 2 assets to create pairs")

        # Filter to only image assets
        image_assets = [a for a in assets if a.get("type") == "image"]
        if len(image_assets) < 2:
            raise ValueError(f"Need at least 2 image assets, but only got {len(image_assets)}")

        logger.info(
            f"[TWO-STAGE] Selecting image pairs from {len(image_assets)} images "
            f"(filtered from {len(assets)} total assets)"
        )

        # Detect if we should use two-stage room-based selection
        # Use two-stage if: num_pairs == 7 (luxury property video) and we have room-tagged images
        num_pairs = num_pairs or 7  # Default to 7
        use_two_stage = num_pairs == 7

        if not use_two_stage:
            # Fall back to original single-stage selection
            logger.info("[TWO-STAGE] Using single-stage selection (not a 7-pair property video)")
            return self._single_stage_selection(image_assets, campaign_context, client_brand_guidelines, num_pairs)

        # STAGE 1: Group assets by room type
        room_groups = self._group_assets_by_room(image_assets)

        # Adjust num_pairs if we have fewer room types
        actual_pairs = min(num_pairs, len(room_groups))
        if len(room_groups) < num_pairs:
            logger.info(
                f"[TWO-STAGE] Only {len(room_groups)} room types available, "
                f"adjusting from {num_pairs} to {actual_pairs} pairs."
            )

        logger.info(f"[TWO-STAGE STAGE 1] Grouped {len(image_assets)} images into {len(room_groups)} room types")
        for room_type, room_assets in room_groups.items():
            logger.info(f"[TWO-STAGE STAGE 1]   {room_type}: {len(room_assets)} images")

        # STAGE 1: Select which room types to use
        try:
            selected_room_types = self._select_room_types(room_groups, actual_pairs, campaign_context)
            logger.info(f"[TWO-STAGE STAGE 1] Selected {len(selected_room_types)} room types: {selected_room_types}")
        except Exception as e:
            logger.error(f"[TWO-STAGE STAGE 1] Room selection failed: {e}. Falling back to single-stage.")
            return self._single_stage_selection(image_assets, campaign_context, client_brand_guidelines, num_pairs)

        # STAGE 2: For each selected room, select best 2 images (parallel)
        pairs = []
        logger.info(f"[TWO-STAGE STAGE 2] Selecting image pairs for {len(selected_room_types)} rooms (parallel)")

        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            future_to_room = {
                executor.submit(
                    self._select_pair_from_room,
                    room_type,
                    room_groups[room_type],
                    campaign_context
                ): room_type
                for room_type in selected_room_types
                if room_type in room_groups
            }

            for future in concurrent.futures.as_completed(future_to_room):
                room_type = future_to_room[future]
                try:
                    pair = future.result()
                    if pair:
                        pairs.append(pair)
                        logger.info(f"[TWO-STAGE STAGE 2] ✓ {room_type}: Selected pair")
                except Exception as e:
                    logger.error(f"[TWO-STAGE STAGE 2] ✗ {room_type}: Failed - {e}")

        if len(pairs) < actual_pairs:
            logger.warning(
                f"[TWO-STAGE] Only got {len(pairs)} pairs from {actual_pairs} rooms. "
                f"Some room selections failed."
            )

        logger.info(f"[TWO-STAGE] Successfully selected {len(pairs)} pairs using two-stage approach")
        return pairs

    def _single_stage_selection(
        self,
        image_assets: List[Dict[str, Any]],
        campaign_context: Optional[Dict[str, Any]],
        brand_guidelines: Optional[Dict[str, Any]],
        num_pairs: Optional[int],
    ) -> List[Tuple[str, str, float, str]]:
        """Original single-stage selection (fallback for non-property videos)."""
        prompt = self._build_selection_prompt(
            image_assets, campaign_context, brand_guidelines, num_pairs
        )

        logger.info(f"[SINGLE-STAGE] Prompt length: {len(prompt)} characters")

        response = self._call_grok_api(prompt, image_assets)
        pairs = self._parse_pairs_response(response, image_assets)

        logger.info(f"[SINGLE-STAGE] Successfully selected {len(pairs)} pairs")
        return pairs

    def _select_room_types(
        self,
        room_groups: Dict[str, List[Dict[str, Any]]],
        num_rooms: int,
        campaign_context: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Stage 1: Select which room types to feature in the video.

        Args:
            room_groups: Dict mapping room type to list of assets
            num_rooms: Number of room types to select (e.g., 7 for property video)
            campaign_context: Optional campaign info

        Returns:
            List of selected room type names
        """
        # Build room selection prompt
        prompt = f"""You are an expert luxury real estate videographer planning a property showcase video.

You need to select {num_rooms} room types to feature in a {num_rooms}-scene video (one scene per room type).

AVAILABLE ROOM TYPES:
"""

        for room_type, assets in sorted(room_groups.items(), key=lambda x: -len(x[1])):
            prompt += f"- {room_type}: {len(assets)} images available\n"

        if campaign_context:
            prompt += f"""
CAMPAIGN CONTEXT:
- Goal: {campaign_context.get('goal', 'Showcase premium property')}
- Target Audience: {campaign_context.get('targetAudience', 'Luxury buyers')}
"""

        prompt += f"""
SELECTION CRITERIA:
1. Visual Appeal: Choose rooms with most compelling imagery potential
2. Narrative Flow: Select rooms that create a cohesive property tour
3. Diversity: Balance between public spaces (living, dining, kitchen) and private (bedroom, bathroom)
4. Luxury Features: Prioritize rooms that showcase high-end finishes and unique features

REQUIRED ROOM TYPES (must include if available):
- At least 1 bedroom type (Bedroom, etc.)
- At least 1 bathroom type (Bathroom, Ensuite Bathroom, etc.)
- At least 1 exterior/outdoor type (Exterior, Pool, Patio, etc.)

RESPONSE FORMAT (JSON):
{{
  "selected_rooms": ["Room Type 1", "Room Type 2", "Room Type 3", ...]
}}

Select exactly {num_rooms} room types that will create the most compelling property video.
"""

        # Call Grok for room selection with retry logic
        logger.info(f"[ROOM SELECTION] Asking Grok to select {num_rooms} rooms from {len(room_groups)} options")

        data = self._call_grok_api(prompt, temperature=0.3)
        content = data["choices"][0]["message"]["content"].strip()

        # Parse JSON response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)
        selected_rooms = result.get("selected_rooms", [])

        # Validate selected rooms exist
        valid_rooms = [r for r in selected_rooms if r in room_groups]

        if len(valid_rooms) < num_rooms:
            logger.warning(
                f"[ROOM SELECTION] Only {len(valid_rooms)} valid rooms selected, "
                f"filling remainder from available rooms"
            )
            # Fill with remaining rooms sorted by image count
            remaining = [r for r in sorted(room_groups.keys(), key=lambda x: -len(room_groups[x]))
                        if r not in valid_rooms]
            valid_rooms.extend(remaining[:num_rooms - len(valid_rooms)])

        return valid_rooms[:num_rooms]

    def _select_pair_from_room(
        self,
        room_type: str,
        room_assets: List[Dict[str, Any]],
        campaign_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Tuple[str, str, float, str]]:
        """
        Stage 2: Select best 2 images from a specific room to form a pair.

        Args:
            room_type: Name of the room type (e.g., "Bedroom", "Kitchen")
            room_assets: List of assets for this room
            campaign_context: Optional campaign info

        Returns:
            Tuple of (image1_id, image2_id, score, reasoning) or None if failed
        """
        if len(room_assets) < 2:
            logger.warning(f"[PAIR SELECTION {room_type}] Only {len(room_assets)} images, need at least 2 for interpolation")
            return None  # Can't create a valid pair without 2 different images

        # Build pair selection prompt
        prompt = f"""You are an expert luxury real estate cinematographer selecting images for video generation.

Select the BEST 2 images from this {room_type} to create a smooth video transition.

The video will interpolate between Image 1 (start frame) and Image 2 (end frame) to create motion.

AVAILABLE {room_type.upper()} IMAGES ({len(room_assets)} total):
"""

        for i, asset in enumerate(room_assets, 1):
            tags_str = ', '.join(asset.get('tags', []))
            prompt += f"""
{i}. ID: {asset['id']}
   Name: {asset.get('name', 'Unnamed')}
   Description: {asset.get('description', 'No description')}
   Tags: {tags_str}
"""

        prompt += f"""
SELECTION CRITERIA:
1. Visual Continuity: Choose images with similar lighting, color palette, and composition
2. Camera Movement Potential: Select images that suggest natural camera motion (e.g., wide to close-up)
3. Feature Showcase: Highlight the best features of this {room_type}
4. Transition Quality: Images should interpolate smoothly without jarring changes

RESPONSE FORMAT (JSON):
{{
  "image1_id": "uuid-of-first-image",
  "image2_id": "uuid-of-second-image",
  "score": 0.95,
  "reasoning": "Brief explanation of why this pair works well"
}}

Select the 2 images that will create the most compelling {room_type} scene.
"""

        # Call Grok with retry logic
        try:
            data = self._call_grok_api(prompt, temperature=0.3)
            content = data["choices"][0]["message"]["content"].strip()

            # Parse JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)

            image1_id = result["image1_id"]
            image2_id = result["image2_id"]
            score = float(result.get("score", 0.8))
            reasoning = result.get("reasoning", f"Selected pair for {room_type}")

            # Validate IDs exist in room_assets
            valid_ids = {a['id'] for a in room_assets}
            if image1_id not in valid_ids or image2_id not in valid_ids:
                raise ValueError(f"Selected image IDs not in {room_type} assets")

            return (image1_id, image2_id, score, reasoning)

        except Exception as e:
            logger.error(f"[PAIR SELECTION {room_type}] Failed: {e}")
            # Fallback: use first 2 images
            if len(room_assets) >= 2:
                return (
                    room_assets[0]['id'],
                    room_assets[1]['id'],
                    0.5,
                    f"Fallback selection for {room_type} after error"
                )
            return None

    def _build_selection_prompt(
        self,
        assets: List[Dict[str, Any]],
        campaign_context: Optional[Dict[str, Any]],
        brand_guidelines: Optional[Dict[str, Any]],
        num_pairs: Optional[int],
    ) -> str:
        """Build the prompt for Grok to select image pairs."""

        # Detect if this is a luxury property video (7 pairs requested)
        is_property_video = num_pairs == 7

        if is_property_video:
            return self._build_property_scene_prompt(assets, campaign_context, brand_guidelines)
        else:
            return self._build_generic_selection_prompt(assets, campaign_context, brand_guidelines, num_pairs)

    def _build_generic_selection_prompt(
        self,
        assets: List[Dict[str, Any]],
        campaign_context: Optional[Dict[str, Any]],
        brand_guidelines: Optional[Dict[str, Any]],
        num_pairs: Optional[int],
    ) -> str:
        """Build the generic prompt for image pair selection."""

        prompt = """You are an expert creative director selecting image pairs for video generation.

Your task is to analyze the provided images and select optimal pairs that will create compelling video transitions.

SELECTION CRITERIA:
1. Visual Continuity: Colors, lighting, and composition should flow smoothly
2. Thematic Coherence: Images should tell a cohesive narrative
3. Brand Consistency: Align with brand guidelines if provided
4. Transition Potential: Consider how well images will interpolate into video

"""

        # Add campaign context if provided
        if campaign_context:
            prompt += f"""
CAMPAIGN CONTEXT:
- Goal: {campaign_context.get('goal', 'Not specified')}
- Target Audience: {campaign_context.get('targetAudience', 'Not specified')}
- Key Message: {campaign_context.get('keyMessage', 'Not specified')}
"""

        # Add brand guidelines if provided
        if brand_guidelines:
            colors = brand_guidelines.get('colors') or []
            restrictions = brand_guidelines.get('restrictions') or []
            prompt += f"""
BRAND GUIDELINES:
- Colors: {', '.join(colors) if colors else 'Not specified'}
- Tone: {brand_guidelines.get('tone', 'Not specified')}
- Restrictions: {', '.join(restrictions) if restrictions else 'None'}
"""

        # Add asset information
        prompt += f"""
AVAILABLE IMAGES ({len(assets)} total):
"""
        for i, asset in enumerate(assets, 1):
            tags = ', '.join(asset.get('tags', [])) if asset.get('tags') else 'None'
            prompt += f"""
{i}. ID: {asset['id']}
   Name: {asset.get('name', 'Unnamed')}
   Description: {asset.get('description', 'No description')}
   Tags: {tags}
"""

        # Add instructions
        target_pairs = num_pairs if num_pairs else "an appropriate number of"
        prompt += f"""
INSTRUCTIONS:
Select {target_pairs} image pairs that will create the best video sequence.
Each pair should be ordered (first image → second image) for smooth transitions.
Consider the overall narrative flow across all pairs.

RESPONSE FORMAT (JSON):
{{
  "pairs": [
    {{
      "image1_id": "asset-uuid-1",
      "image2_id": "asset-uuid-2",
      "score": 0.95,
      "reasoning": "Brief explanation of why this pair works well"
    }}
  ]
}}

Important:
- Order pairs by score (highest first)
- Scores should be 0.0 to 1.0 (1.0 = perfect pair)
- Each image can appear in multiple pairs if it makes sense narratively
- Consider the sequence: pairs should flow into each other when combined
"""

        return prompt

    def _build_property_scene_prompt(
        self,
        assets: List[Dict[str, Any]],
        campaign_context: Optional[Dict[str, Any]],
        brand_guidelines: Optional[Dict[str, Any]],
    ) -> str:
        """
        Build specialized prompt for luxury property scene-based pair selection.

        This prompt analyzes photos to select optimal first/last image pairs for
        each of 7 distinct cinematographic scenes in a luxury property video.
        """

        prompt = """You are an expert luxury real estate cinematographer and creative director.

Your task is to analyze a collection of property photos and select the BEST image pairs (first frame + last frame) for generating 7 distinct video scenes. Each scene has specific cinematography requirements and camera movements.

CRITICAL: You must select EXACTLY 7 pairs - one pair per scene type. Each pair consists of:
- First Image: The starting frame that the camera movement begins from
- Last Image: The ending frame that the camera movement ends on

The video generation AI will interpolate between these two images using the specified camera movement.

═══════════════════════════════════════════════════════════════════════════════
SCENE 1: THE HOOK (Exterior Feature) - Duration: 1.5s
═══════════════════════════════════════════════════════════════════════════════
Camera Movement: Dolly forward (push-in) with low angle
Ideal Tags: exterior, pool, courtyard, terrace, water, outdoor, landscape
Motion Goal: Immediate visual interest with water/surface movement

Selection Criteria:
- First Image: Wide shot showing water feature, pool, or reflective surface at a distance
- Last Image: Closer view of the same feature, revealing detail and texture
- Both images should have bright natural lighting with glistening highlights
- Must have clear water or reflective surfaces that suggest gentle movement
- Low angle perspective preferred (eye-level or slightly below)

Visual Requirements:
- Similar lighting conditions between first and last image
- Maintain same time of day (both daytime with similar sun position)
- Progressive reveal of architectural detail as camera moves forward
- Water/surface should be central focus in both frames

═══════════════════════════════════════════════════════════════════════════════
SCENE 2: THE HERO BEDROOM (Parallax) - Duration: 1.0s
═══════════════════════════════════════════════════════════════════════════════
Camera Movement: Lateral truck (sideways slide left or right)
Ideal Tags: bedroom, master bedroom, interior, windows, glass walls, view
Motion Goal: Create parallax effect with foreground/background depth

Selection Criteria:
- First Image: Bedroom with bed visible and windows/view in background
- Last Image: Similar view from laterally shifted position (2-4 feet sideways)
- Both images must show clear foreground (bed/furniture) and background (windows/view)
- Large windows or glass walls essential for parallax effect
- Soft natural light streaming in

Visual Requirements:
- Bed and foreground elements should be clearly separated from background
- Windows/views should be prominent in both frames
- Same room, different lateral position (NOT different angles)
- Depth between foreground and background must be visible
- Avoid head-on symmetrical shots - prefer angled compositions

Alternative Selection (if no perfect lateral pair exists):
- Use two photos from slightly different positions in the same bedroom
- Ensure both show the bed and window view from angles that suggest lateral movement

═══════════════════════════════════════════════════════════════════════════════
SCENE 3: BATHROOM VANITY (Symmetry) - Duration: 1.0s
═══════════════════════════════════════════════════════════════════════════════
Camera Movement: Lateral truck (opposite direction to Scene 2)
Ideal Tags: bathroom, vanity, mirror, sink, interior, spa
Motion Goal: Smooth sliding movement with natural reflection shifts

Selection Criteria:
- First Image: Bathroom vanity with mirror clearly visible
- Last Image: Same vanity from laterally shifted position
- Mirrors and reflective surfaces essential
- Clean, bright lighting showcasing fixtures
- Sharp focus on surfaces and textures

Visual Requirements:
- Both images should show the same vanity/mirror setup
- Reflections should be visible and prominent
- Movement direction should feel opposite to Scene 2 (if Scene 2 went left, this goes right)
- Modern, spa-like aesthetic
- Symmetrical or semi-symmetrical composition in at least one image

Alternative Selection:
- Can use double vanity if available (better for lateral movement)
- Single vanity with large mirror also works
- Ensure lighting is consistent between images

═══════════════════════════════════════════════════════════════════════════════
SCENE 4: THE FEATURE TUB/SHOWER (Depth) - Duration: 1.0s
═══════════════════════════════════════════════════════════════════════════════
Camera Movement: Dolly forward (push-in toward centerpiece)
Ideal Tags: bathroom, tub, bathtub, shower, freestanding, spa, luxury
Motion Goal: Intimate reveal emphasizing the luxury fixture

Selection Criteria:
- First Image: Wide/medium shot showing tub or shower with surrounding context
- Last Image: Closer view highlighting the fixture's textures and materials
- Background window or view strongly preferred (adds depth)
- Serene, spa-like atmosphere
- High detail on materials (stone, marble, metal)

Visual Requirements:
- Both images must feature the SAME centerpiece fixture
- Progressive zoom/approach toward the fixture
- Background elements (windows, views) should remain relatively stable
- Soft, balanced lighting creating spa atmosphere
- Texture and material quality should be prominent in closer shot

Alternative Selection:
- If no perfect tub pair exists, feature shower can substitute
- Ensure fixture is visually distinctive and photogenic
- Maintain sense of luxury and tranquility

═══════════════════════════════════════════════════════════════════════════════
SCENE 5: LIVING ROOM (The Sweep) - Duration: 1.0s
═══════════════════════════════════════════════════════════════════════════════
Camera Movement: Lateral pan or truck following room layout
Ideal Tags: living room, lounge, seating, interior, furniture, windows
Motion Goal: Sweeping reveal of space, scale, and flow

Selection Criteria:
- First Image: Wide shot capturing one end/section of living area
- Last Image: View showing connected or adjacent section (swept perspective)
- Both images should show prominent seating arrangements
- Natural light streaming in from windows
- Spacious, open feel

Visual Requirements:
- Movement should follow natural lines of furniture arrangement
- Both images in same room but from positions suggesting lateral sweep
- Maintain consistent lighting (same time of day)
- Architectural flow should be evident
- Sense of space and scale important

Alternative Selection:
- Can use open-concept living/dining if no dedicated living room
- Ensure both images convey spaciousness and luxury
- Furniture layout should guide the eye across the frame

═══════════════════════════════════════════════════════════════════════════════
SCENE 6: LIFESTYLE/DINING AREA (Atmosphere) - Duration: 1.0s
═══════════════════════════════════════════════════════════════════════════════
Camera Movement: Minimal (near-static with subtle drift)
Ideal Tags: dining, kitchen, dining room, indoor-outdoor, lifestyle, entertaining
Motion Goal: Let lighting and ambiance breathe (atmospheric moment)

Selection Criteria:
- First Image: Elegant dining area or lifestyle space with warm lighting
- Last Image: Very similar view with subtle atmospheric differences
- Warm, inviting lighting essential (golden hour or evening preferred)
- Minimal movement required (nearly identical images work well)
- Indoor-outdoor connection ideal but not required

Visual Requirements:
- Both images should be nearly identical (static scene)
- Lighting should be warm and atmospheric
- Can be same image used twice if it's perfect for atmosphere
- Dining table, outdoor dining, or entertaining space
- Lifestyle elements (table settings, candles, ambiance) valued

Alternative Selection:
- Kitchen with great lighting can substitute if no formal dining
- Outdoor terrace with dining setup works well
- Focus on mood and atmosphere over movement

═══════════════════════════════════════════════════════════════════════════════
SCENE 7: THE OUTRO (Establishing Wide) - Duration: 3.5s
═══════════════════════════════════════════════════════════════════════════════
Camera Movement: Dolly backward (pull-out) or drone pull-back
Ideal Tags: exterior, wide, establishing, view, landscape, deck, entrance, architecture
Motion Goal: Final impression - gentle retreat revealing full context

Selection Criteria:
- First Image: Closer view of signature property feature (deck, entrance, or view)
- Last Image: Wide establishing shot showing full property context
- Signature view or architectural highlight essential
- Golden hour or evening lighting preferred (warm interior glow visible)
- Most inviting time of day

Visual Requirements:
- Both images should show exterior or exterior-facing views
- Progressive reveal of property's full context
- Warm interior lighting visible through windows (if applicable)
- Final image should be THE hero shot of the property
- Calm, peaceful, aspirational feeling
- Sense of arrival or welcome

Alternative Selection:
- Can use two different wide exterior shots if perfect pull-back pair unavailable
- Evening/twilight shots highly valued for this scene
- Entrance, deck, or signature view all work well

"""

        # Add available images
        prompt += f"""
═══════════════════════════════════════════════════════════════════════════════
AVAILABLE IMAGES ({len(assets)} total photos from property):
═══════════════════════════════════════════════════════════════════════════════
"""
        logger.info(f"[PROMPT BUILDER] Building image list for {len(assets)} assets")

        for i, asset in enumerate(assets, 1):
            tags = asset.get('tags', [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            tags_str = ', '.join(tags) if tags else 'No tags'

            description = asset.get('description', 'No description')
            name = asset.get('name', 'Unnamed')
            asset_id = asset['id']

            logger.info(
                f"[PROMPT BUILDER] Image {i}: "
                f"id={asset_id[:12]}... name='{name}' tags=[{tags_str}]"
            )

            prompt += f"""
Image {i}:
  ID: {asset_id}
  Name: {name}
  Tags: {tags_str}
  Description: {description}
"""

        # Add output format instructions
        prompt += """
═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT (JSON):
═══════════════════════════════════════════════════════════════════════════════

You must return EXACTLY 7 pairs in this order:

{{
  "pairs": [
    {{
      "image1_id": "asset-uuid-for-first-frame",
      "image2_id": "asset-uuid-for-last-frame",
      "score": 0.95,
      "scene_number": 1,
      "scene_name": "The Hook (Exterior Feature)",
      "reasoning": "Wide pool shot to close-up of water edge. Perfect for dolly forward with glistening water highlights. Both images show bright natural lighting."
    }},
    {{
      "image1_id": "asset-uuid-for-first-frame",
      "image2_id": "asset-uuid-for-last-frame",
      "score": 0.88,
      "scene_number": 2,
      "scene_name": "The Hero Bedroom (Parallax)",
      "reasoning": "Master bedroom photos from slightly different lateral positions. Clear foreground (bed) and background (windows) separation for parallax effect."
    }},
    // ... continue for all 7 scenes
  ]
}}

CRITICAL REQUIREMENTS:
✓ MUST select exactly 7 pairs (one per scene, in order)
✓ Each pair should have distinct first_image and last_image (except Scene 6 which can reuse)
✓ Score each pair 0.0-1.0 based on how well it matches scene requirements
✓ Include scene_number (1-7) and scene_name for each pair
✓ Reasoning should explain why these specific images work for this scene's camera movement
✓ Prioritize pairs that will create smooth, professional video transitions
✓ Consider the cinematography requirements (camera movement, lighting, composition)
✓ Use image tags and descriptions to identify suitable candidates
✓ If perfect pairs don't exist, select the closest matches and note compromises in reasoning

SCENE ORDER (MUST FOLLOW):
1. The Hook (Exterior Feature) - 1.5s
2. The Hero Bedroom (Parallax) - 1.0s
3. Bathroom Vanity (Symmetry) - 1.0s
4. The Feature Tub/Shower (Depth) - 1.0s
5. Living Room (The Sweep) - 1.0s
6. Lifestyle/Dining Area (Atmosphere) - 1.0s
7. The Outro (Establishing Wide) - 3.5s

Begin your analysis and selection now.
"""

        return prompt

    def _call_grok_api(
        self, prompt: str, image_assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Call the xAI Grok API.

        Args:
            prompt: The text prompt
            image_assets: List of image assets (for potential vision API support)

        Returns:
            API response dict
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Build messages - for now using text-only
        # Future: Can enhance with image URLs if Grok vision API supports it
        messages = [
            {
                "role": "system",
                "content": "You are an expert creative director and video producer.",
            },
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,  # Some creativity but mostly consistent
            "response_format": {"type": "json_object"},  # Request JSON response
        }

        logger.debug(f"Calling Grok API with model {self.model}")

        # Retry logic with exponential backoff
        max_retries = 3
        base_delay = 1.0  # seconds

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))
                    logger.info(f"[GROK RETRY] Attempt {attempt + 1}/{max_retries} after {delay}s delay")
                    time.sleep(delay)

                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60,
                )
                response.raise_for_status()

                # Try to parse JSON response
                try:
                    result = response.json()
                    logger.debug(f"Grok API response: {result}")

                    # Validate the response has the expected structure
                    if not result.get("choices") or not result["choices"][0].get("message"):
                        raise ValueError("Response missing expected structure")

                    return result

                except (json.JSONDecodeError, ValueError) as parse_error:
                    logger.warning(
                        f"[GROK RETRY] Attempt {attempt + 1}/{max_retries} failed to parse response: {parse_error}\n"
                        f"Response text: {response.text[:500]}"
                    )
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"Failed to parse Grok API response after {max_retries} attempts: {parse_error}")
                    continue

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"[GROK RETRY] Attempt {attempt + 1}/{max_retries} failed with request error: {e}"
                )
                if attempt == max_retries - 1:
                    logger.error(f"Grok API request failed after {max_retries} attempts: {e}")
                    raise RuntimeError(f"Failed to call Grok API after {max_retries} attempts: {e}")
                continue

        # Should never reach here, but just in case
        raise RuntimeError(f"Failed to call Grok API after {max_retries} attempts")

    def _parse_pairs_response(
        self, response: Dict[str, Any], assets: List[Dict[str, Any]]
    ) -> List[Tuple[str, str, float, str]]:
        """
        Parse the Grok API response into image pairs.

        Args:
            response: Raw API response
            assets: Original asset list for validation

        Returns:
            List of tuples: (image1_id, image2_id, score, reasoning)
        """
        try:
            # Extract content from response
            logger.info(f"[GROK RAW RESPONSE] ===== FULL API RESPONSE START =====")
            logger.info(json.dumps(response, indent=2))
            logger.info(f"[GROK RAW RESPONSE] ===== FULL API RESPONSE END =====")

            content = response["choices"][0]["message"]["content"]
            logger.info(f"[GROK RAW RESPONSE] Content length: {len(content)} characters")

            # Parse JSON
            data = json.loads(content)
            logger.info(f"[GROK PARSED JSON] ===== PARSED JSON START =====")
            logger.info(json.dumps(data, indent=2))
            logger.info(f"[GROK PARSED JSON] ===== PARSED JSON END =====")

            # Write parsed response to debug file
            debug_log_path = "/tmp/image_pairing_debug.log"
            with open(debug_log_path, "a") as debug_file:
                debug_file.write(f"\n{'='*80}\n")
                debug_file.write(f"GROK RESPONSE\n")
                debug_file.write(f"{'='*80}\n")
                debug_file.write(json.dumps(data, indent=2))
                debug_file.write(f"\n{'='*80}\n\n")

            pairs_data = data.get("pairs", [])

            if not pairs_data:
                raise ValueError("No pairs found in response")

            # Validate and convert to tuples
            asset_ids = {a["id"] for a in assets}
            logger.info(f"[GROK VALIDATION] Available asset IDs: {len(asset_ids)} total")
            logger.info(f"[GROK VALIDATION] Sample IDs: {list(asset_ids)[:3]}")

            pairs = []

            for i, pair in enumerate(pairs_data, 1):
                logger.info(f"[GROK VALIDATION] Processing pair {i}/{len(pairs_data)}")
                logger.info(f"[GROK VALIDATION] Pair data: {json.dumps(pair, indent=2)}")

                image1_id = pair.get("image1_id")
                image2_id = pair.get("image2_id")
                score = pair.get("score", 0.5)
                reasoning = pair.get("reasoning", "No reasoning provided")
                scene_number = pair.get("scene_number")
                scene_name = pair.get("scene_name")

                logger.info(
                    f"[GROK VALIDATION] Pair {i}: "
                    f"scene={scene_number} ({scene_name}) "
                    f"img1={image1_id[:12] if image1_id else 'None'}... "
                    f"img2={image2_id[:12] if image2_id else 'None'}... "
                    f"score={score}"
                )

                # Validate asset IDs exist
                if image1_id not in asset_ids:
                    logger.warning(
                        f"[GROK VALIDATION] REJECTED Pair {i}: "
                        f"Invalid image1_id: {image1_id}, not in asset list"
                    )
                    continue
                if image2_id not in asset_ids:
                    logger.warning(
                        f"[GROK VALIDATION] REJECTED Pair {i}: "
                        f"Invalid image2_id: {image2_id}, not in asset list"
                    )
                    continue

                # Reject same-image pairs - video interpolation requires 2 different images
                if image1_id == image2_id:
                    logger.warning(
                        f"[GROK VALIDATION] REJECTED Pair {i}: "
                        f"Same image used twice: {image1_id} (need 2 different images for interpolation)"
                    )
                    continue

                logger.info(f"[GROK VALIDATION] ACCEPTED Pair {i}")
                pairs.append((image1_id, image2_id, float(score), reasoning))

                # Write accepted pair to debug file
                debug_log_path = "/tmp/image_pairing_debug.log"
                with open(debug_log_path, "a") as debug_file:
                    debug_file.write(f"ACCEPTED Pair {i}:\n")
                    debug_file.write(f"  Scene: {scene_number} - {scene_name}\n")
                    debug_file.write(f"  Image 1: {image1_id}\n")
                    debug_file.write(f"  Image 2: {image2_id}\n")
                    debug_file.write(f"  Score: {score}\n")
                    debug_file.write(f"  Reasoning: {reasoning}\n\n")

            if not pairs:
                raise ValueError("No valid pairs after validation")

            # Sort by score (highest first)
            pairs.sort(key=lambda x: x[2], reverse=True)

            return pairs

        except (KeyError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Grok response: {e}", exc_info=True)
            raise ValueError(f"Invalid response format from Grok: {e}")

    def select_property_scene_pairs(
        self,
        property_info: Dict[str, Any],
        photos: List[Dict[str, Any]],
        scene_types: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Select optimal image pairs for luxury lodging property scenes using Grok.

        Args:
            property_info: Dict with name, location, property_type, positioning
            photos: List of photo dicts with id, filename, url, tags, metadata
            scene_types: List of 7 scene type definitions

        Returns:
            Dict with scene_pairs, selection_metadata, recommendations
        """
        if len(scene_types) != 7:
            raise ValueError(f"Expected 7 scene types, got {len(scene_types)}")

        logger.info(
            f"Selecting scene pairs for '{property_info.get('name')}' "
            f"from {len(photos)} photos"
        )

        # Build comprehensive prompt
        prompt = self._build_property_selection_prompt(
            property_info, photos, scene_types
        )

        # Call Grok API
        try:
            response = self._call_grok_api(prompt, [])
            result = self._parse_property_scene_response(response, photos, scene_types)

            logger.info(f"Successfully selected {len(result['scene_pairs'])} scene pairs")
            return result

        except Exception as e:
            logger.error(f"Failed to select property scene pairs: {e}", exc_info=True)
            raise

    def _build_property_selection_prompt(
        self,
        property_info: Dict[str, Any],
        photos: List[Dict[str, Any]],
        scene_types: List[Dict[str, Any]]
    ) -> str:
        """Build the comprehensive Grok prompt for property photo selection."""

        prompt = f"""# Luxury Lodging Video Scene Image Selection

You are an expert creative director specializing in luxury hospitality marketing. Your task is to select the optimal image pairs for a 7-scene promotional video showcasing a luxury lodging property.

## Property Information
**Property Name:** {property_info.get('name', 'Unknown')}
**Location:** {property_info.get('location', 'Not specified')}
**Property Type:** {property_info.get('property_type', 'Luxury lodging')}
**Brand Positioning:** {property_info.get('positioning', 'High-end hospitality')}

## Available Photos
You have access to {len(photos)} photos crawled from the property website.

"""

        # Add photo catalog
        prompt += "### Photo Catalog\n```json\n{\n  \"photos\": [\n"
        for i, photo in enumerate(photos):
            photo_entry = {
                "id": photo.get("id"),
                "filename": photo.get("filename", ""),
                "tags": photo.get("tags", []),
                "dominant_colors": photo.get("dominant_colors", []),
                "detected_objects": photo.get("detected_objects", []),
                "composition": photo.get("composition", "unknown"),
                "lighting": photo.get("lighting", "unknown")
            }
            prompt += "    " + json.dumps(photo_entry)
            if i < len(photos) - 1:
                prompt += ","
            prompt += "\n"
        prompt += "  ]\n}\n```\n\n"

        # Add scene type requirements
        prompt += "## Scene Types & Requirements\n\n"
        prompt += "You must select exactly **2 images per scene** (first frame + last frame) for smooth video interpolation.\n\n"

        for scene in scene_types:
            prompt += f"""### Scene {scene['scene_number']}: {scene['scene_type']} ({scene['duration']} seconds)
**Purpose:** {scene['purpose']}
**Visual Priority:** {scene['visual_priority']}
**Mood:** {scene['mood']}
**Ideal Tags:** {', '.join(scene['ideal_tags'])}
**First Image:** {scene['first_image_guidance']}
**Last Image:** {scene['last_image_guidance']}
**Transition Goal:** {scene['transition_goal']}

"""

        # Add selection criteria
        prompt += """## Selection Criteria

For each scene type, evaluate images based on:

### 1. Visual Quality (30%)
- High resolution and sharpness
- Professional composition (rule of thirds, leading lines, symmetry)
- Optimal lighting (natural light preferred, golden hour highly valued)
- Color harmony and aesthetic appeal

### 2. Tag Alignment (25%)
- Strong match with scene type's ideal tags
- Relevant detected objects for scene narrative
- Appropriate setting and context

### 3. Transition Potential (25%)
- **Critical for AI video generation success**
- Similar lighting conditions between first/last image
- Compatible color palettes (smooth gradient possible)
- Compositional flow (wide → medium, or establishing → detail)
- Avoid jarring jumps in perspective or subject matter

### 4. Brand Consistency (20%)
- Aligns with property positioning and target market
- Represents property's unique character
- Appeals to luxury hospitality audience
- Authentic representation (not generic stock-photo feel)

## Output Format

Return your selections as JSON with the following structure:

```json
{
  "property_name": "{property_info.get('name', 'Unknown')}",
  "selection_metadata": {
    "total_photos_evaluated": {len(photos)},
    "selection_confidence": "high|medium|low",
    "overall_visual_quality_score": 8.5,
    "brand_coherence_score": 9.2
  },
  "scene_pairs": [
    {
      "scene_number": 1,
      "scene_type": "Grand Arrival",
      "first_image": {
        "id": "photo_id",
        "filename": "filename.jpg",
        "reasoning": "Why this image works as first frame",
        "quality_score": 9.1,
        "tag_match_score": 9.5
      },
      "last_image": {
        "id": "photo_id",
        "filename": "filename.jpg",
        "reasoning": "Why this image works as last frame",
        "quality_score": 8.8,
        "tag_match_score": 9.0
      },
      "transition_analysis": {
        "color_compatibility": "excellent|good|fair|poor",
        "lighting_consistency": "description",
        "compositional_flow": "description",
        "interpolation_confidence": 9.2
      }
    }
  ],
  "recommendations": {
    "missing_content_gaps": [],
    "photo_crawl_improvements": []
  }
}
```

## Critical Constraints

1. **Exactly 2 images per scene** (14 images total across 7 scenes)
2. **No image reuse** - each of the 14 images must be unique
3. **Transition smoothness is paramount** - prioritize interpolation success
4. **Scene progression** - consider narrative flow across all 7 scenes
5. **Color story** - maintain visual cohesion across the full 35-second video
6. **Authentic representation** - select real property photos only

Analyze all {len(photos)} photos carefully and select the optimal pairs for each scene type.
"""

        return prompt

    def _parse_property_scene_response(
        self,
        response: Dict[str, Any],
        photos: List[Dict[str, Any]],
        scene_types: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Parse Grok's property scene selection response.

        Args:
            response: Raw API response from Grok
            photos: Original photo list for validation
            scene_types: Scene type definitions

        Returns:
            Parsed and validated result dict
        """
        try:
            # Extract content from response
            content = response["choices"][0]["message"]["content"]

            # Parse JSON
            data = json.loads(content)

            if not data.get("scene_pairs"):
                raise ValueError("No scene_pairs in Grok response")

            # Validate photo IDs exist
            photo_ids = {p["id"] for p in photos}

            validated_pairs = []
            for pair in data["scene_pairs"]:
                scene_num = pair.get("scene_number")
                if not scene_num or scene_num < 1 or scene_num > 7:
                    logger.warning(f"Invalid scene_number: {scene_num}, skipping")
                    continue

                first_img = pair.get("first_image", {})
                last_img = pair.get("last_image", {})

                first_id = first_img.get("id")
                last_id = last_img.get("id")

                # Validate IDs exist
                if first_id not in photo_ids:
                    logger.warning(f"Invalid first_image id: {first_id}, skipping scene {scene_num}")
                    continue
                if last_id not in photo_ids:
                    logger.warning(f"Invalid last_image id: {last_id}, skipping scene {scene_num}")
                    continue

                # Validate images are different
                if first_id == last_id:
                    logger.warning(f"Scene {scene_num} has same image twice, skipping")
                    continue

                validated_pairs.append(pair)

            if not validated_pairs:
                raise ValueError("No valid scene pairs after validation")

            # Sort by scene number
            validated_pairs.sort(key=lambda x: x["scene_number"])

            return {
                "property_name": data.get("property_name", "Unknown"),
                "selection_metadata": data.get("selection_metadata", {}),
                "scene_pairs": validated_pairs,
                "recommendations": data.get("recommendations", {})
            }

        except (KeyError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse property scene response: {e}", exc_info=True)
            raise ValueError(f"Invalid response format from Grok: {e}")
