"""
xAI Grok-4-fast-1 client for AI-powered image pair selection.

This service uses Grok's vision capabilities to intelligently select
and order image pairs from campaign assets for video generation.
"""

import json
import logging
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

    def select_image_pairs(
        self,
        assets: List[Dict[str, Any]],
        campaign_context: Optional[Dict[str, Any]] = None,
        client_brand_guidelines: Optional[Dict[str, Any]] = None,
        num_pairs: Optional[int] = None,
    ) -> List[Tuple[str, str, float, str]]:
        """
        Select optimal image pairs for video generation using Grok.

        Args:
            assets: List of asset dicts with keys: id, name, description, tags, url, type
            campaign_context: Optional campaign info (goal, targetAudience, keyMessage, etc.)
            client_brand_guidelines: Optional brand guidelines (colors, tone, restrictions)
            num_pairs: Optional target number of pairs. If not specified, Grok decides.

        Returns:
            List of tuples: (image1_id, image2_id, score, reasoning)
            Ordered by quality score (highest first)
        """
        if not assets or len(assets) < 2:
            raise ValueError("Need at least 2 assets to create pairs")

        # Filter to only image assets
        image_assets = [a for a in assets if a.get("type") == "image"]
        if len(image_assets) < 2:
            raise ValueError(f"Need at least 2 image assets, but only got {len(image_assets)}")

        logger.info(
            f"Selecting image pairs from {len(image_assets)} images "
            f"(filtered from {len(assets)} total assets)"
        )

        # Build the prompt
        prompt = self._build_selection_prompt(
            image_assets, campaign_context, client_brand_guidelines, num_pairs
        )

        # Call Grok API
        try:
            response = self._call_grok_api(prompt, image_assets)
            pairs = self._parse_pairs_response(response, image_assets)

            logger.info(f"Successfully selected {len(pairs)} image pairs")
            return pairs

        except Exception as e:
            logger.error(f"Failed to select image pairs: {e}", exc_info=True)
            raise

    def _build_selection_prompt(
        self,
        assets: List[Dict[str, Any]],
        campaign_context: Optional[Dict[str, Any]],
        brand_guidelines: Optional[Dict[str, Any]],
        num_pairs: Optional[int],
    ) -> str:
        """Build the prompt for Grok to select image pairs."""

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

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

            result = response.json()
            logger.debug(f"Grok API response: {result}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Grok API request failed: {e}")
            raise RuntimeError(f"Failed to call Grok API: {e}")

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
            logger.error(f"[DEBUG XAI] Full API response: {json.dumps(response, indent=2)}")
            content = response["choices"][0]["message"]["content"]
            logger.error(f"[DEBUG XAI] Extracted content string: {content}")
            logger.error(f"[DEBUG XAI] Content length: {len(content)}")
            logger.error(f"[DEBUG XAI] Content type: {type(content)}")

            # Parse JSON
            data = json.loads(content)
            print(f"[DEBUG XAI] Full Grok response: {json.dumps(data, indent=2)}")
            pairs_data = data.get("pairs", [])

            if not pairs_data:
                raise ValueError("No pairs found in response")

            # Validate and convert to tuples
            asset_ids = {a["id"] for a in assets}
            print(f"[DEBUG XAI] Available asset IDs ({len(asset_ids)}): {list(asset_ids)[:5]}...")
            pairs = []

            for pair in pairs_data:
                print(f"[DEBUG XAI] Processing pair: {pair}")
                image1_id = pair.get("image1_id")
                image2_id = pair.get("image2_id")
                score = pair.get("score", 0.5)
                reasoning = pair.get("reasoning", "No reasoning provided")

                print(f"[DEBUG XAI] Checking if {image1_id} in asset_ids: {image1_id in asset_ids}")
                print(f"[DEBUG XAI] Checking if {image2_id} in asset_ids: {image2_id in asset_ids}")

                # Validate asset IDs exist
                if image1_id not in asset_ids:
                    print(f"[DEBUG XAI] Invalid image1_id: {image1_id}, skipping pair")
                    logger.warning(f"Invalid image1_id: {image1_id}, skipping pair")
                    continue
                if image2_id not in asset_ids:
                    print(f"[DEBUG XAI] Invalid image2_id: {image2_id}, skipping pair")
                    logger.warning(f"Invalid image2_id: {image2_id}, skipping pair")
                    continue

                # Validate images are different
                if image1_id == image2_id:
                    logger.warning(f"Pair has same image twice: {image1_id}, skipping")
                    continue

                pairs.append((image1_id, image2_id, float(score), reasoning))

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
