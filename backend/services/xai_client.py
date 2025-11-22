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
            prompt += f"""
BRAND GUIDELINES:
- Colors: {', '.join(brand_guidelines.get('colors', [])) or 'Not specified'}
- Tone: {brand_guidelines.get('tone', 'Not specified')}
- Restrictions: {', '.join(brand_guidelines.get('restrictions', [])) or 'None'}
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
            content = response["choices"][0]["message"]["content"]

            # Parse JSON
            data = json.loads(content)
            pairs_data = data.get("pairs", [])

            if not pairs_data:
                raise ValueError("No pairs found in response")

            # Validate and convert to tuples
            asset_ids = {a["id"] for a in assets}
            pairs = []

            for pair in pairs_data:
                image1_id = pair.get("image1_id")
                image2_id = pair.get("image2_id")
                score = pair.get("score", 0.5)
                reasoning = pair.get("reasoning", "No reasoning provided")

                # Validate asset IDs exist
                if image1_id not in asset_ids:
                    logger.warning(f"Invalid image1_id: {image1_id}, skipping pair")
                    continue
                if image2_id not in asset_ids:
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
