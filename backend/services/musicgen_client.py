"""
MusicGen client for generating scene-appropriate music with continuation.

Uses Meta's MusicGen model via Replicate to create progressive audio
that builds across multiple scenes using the continuation feature.
"""

import logging
import requests
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import os

logger = logging.getLogger(__name__)


class MusicGenClient:
    """Client for generating music with Meta's MusicGen model."""

    # MusicGen model on Replicate
    MUSICGEN_MODEL = "meta/musicgen"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize MusicGen client.

        Args:
            api_key: Replicate API key (defaults to env var REPLICATE_API_KEY)
        """
        self.api_key = api_key or os.getenv("REPLICATE_API_KEY")
        if not self.api_key:
            raise ValueError("REPLICATE_API_KEY not found in environment or parameters")

        self.base_url = "https://api.replicate.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        })

        logger.info("MusicGen client initialized")

    def generate_initial_scene_audio(
        self,
        prompt: str,
        duration: int = 4,
        model_version: str = "stereo-large",
        temperature: float = 1.0,
        top_k: int = 250,
        top_p: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Generate the first audio clip for Scene 1.

        Args:
            prompt: Music generation prompt (mood, style, instruments)
            duration: Duration in seconds (default: 4)
            model_version: MusicGen model variant (stereo-large, stereo-melody-large, etc.)
            temperature: Sampling temperature (0.0-1.5)
            top_k: Top-k sampling parameter
            top_p: Top-p sampling parameter

        Returns:
            dict: {
                "success": bool,
                "audio_url": str,
                "duration": int,
                "prediction_id": str,
                "error": str or None
            }
        """
        logger.info(f"Generating initial scene audio: '{prompt}' ({duration}s)")

        try:
            input_params = {
                "prompt": prompt,
                "duration": duration,
                "model_version": model_version,
                "temperature": temperature,
                "top_k": top_k,
                "top_p": top_p,
                "output_format": "mp3",
                "normalization_strategy": "peak",
            }

            # Create prediction
            response = self.session.post(
                f"{self.base_url}/predictions",
                json={
                    "version": self._get_model_version(),
                    "input": input_params,
                },
                timeout=30,
            )
            response.raise_for_status()

            prediction_data = response.json()
            prediction_id = prediction_data.get("id")

            if not prediction_id:
                return {
                    "success": False,
                    "audio_url": None,
                    "duration": 0,
                    "prediction_id": None,
                    "error": "No prediction ID returned from MusicGen API",
                }

            logger.info(f"MusicGen prediction started: {prediction_id}")

            # Poll for completion
            result = self._poll_prediction(prediction_id, timeout=300)

            if result["status"] == "succeeded":
                audio_url = result.get("output")
                logger.info(f"Initial audio generated successfully: {audio_url}")
                return {
                    "success": True,
                    "audio_url": audio_url,
                    "duration": duration,
                    "prediction_id": prediction_id,
                    "error": None,
                }
            else:
                error_msg = result.get("error", f"Generation failed with status: {result['status']}")
                logger.error(f"MusicGen generation failed: {error_msg}")
                return {
                    "success": False,
                    "audio_url": None,
                    "duration": 0,
                    "prediction_id": prediction_id,
                    "error": error_msg,
                }

        except Exception as e:
            logger.error(f"MusicGen initial generation error: {e}", exc_info=True)
            return {
                "success": False,
                "audio_url": None,
                "duration": 0,
                "prediction_id": None,
                "error": str(e),
            }

    def continue_scene_audio(
        self,
        prompt: str,
        input_audio_url: str,
        duration: int = 4,
        model_version: str = "stereo-large",
        temperature: float = 1.0,
        top_k: int = 250,
        top_p: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Generate continuation audio for subsequent scenes.

        This takes the previous scene's audio and extends it with new music
        matching the next scene's mood/style.

        Args:
            prompt: Music generation prompt for this scene
            input_audio_url: URL of previous scene's audio to continue from
            duration: Duration to add (default: 4)
            model_version: MusicGen model variant
            temperature: Sampling temperature
            top_k: Top-k sampling parameter
            top_p: Top-p sampling parameter

        Returns:
            dict: {
                "success": bool,
                "audio_url": str (combined previous + new audio),
                "duration": int (total duration),
                "prediction_id": str,
                "error": str or None
            }
        """
        logger.info(f"Generating continuation audio: '{prompt}' ({duration}s)")
        logger.info(f"Input audio: {input_audio_url}")

        try:
            input_params = {
                "prompt": prompt,
                "input_audio": input_audio_url,  # Previous scene's audio
                "duration": duration,  # Additional duration to add
                "model_version": model_version,
                "temperature": temperature,
                "top_k": top_k,
                "top_p": top_p,
                "output_format": "mp3",
                "normalization_strategy": "peak",
                "continuation": True,  # Enable continuation mode
                "continuation_start": 0,  # Continue from end of input
            }

            # Create prediction
            response = self.session.post(
                f"{self.base_url}/predictions",
                json={
                    "version": self._get_model_version(),
                    "input": input_params,
                },
                timeout=30,
            )
            response.raise_for_status()

            prediction_data = response.json()
            prediction_id = prediction_data.get("id")

            if not prediction_id:
                return {
                    "success": False,
                    "audio_url": None,
                    "duration": 0,
                    "prediction_id": None,
                    "error": "No prediction ID returned from MusicGen API",
                }

            logger.info(f"MusicGen continuation started: {prediction_id}")

            # Poll for completion
            result = self._poll_prediction(prediction_id, timeout=300)

            if result["status"] == "succeeded":
                audio_url = result.get("output")
                logger.info(f"Continuation audio generated: {audio_url}")
                return {
                    "success": True,
                    "audio_url": audio_url,
                    "duration": duration,  # Just the added duration
                    "prediction_id": prediction_id,
                    "error": None,
                }
            else:
                error_msg = result.get("error", f"Continuation failed with status: {result['status']}")
                logger.error(f"MusicGen continuation failed: {error_msg}")
                return {
                    "success": False,
                    "audio_url": None,
                    "duration": 0,
                    "prediction_id": prediction_id,
                    "error": error_msg,
                }

        except Exception as e:
            logger.error(f"MusicGen continuation error: {e}", exc_info=True)
            return {
                "success": False,
                "audio_url": None,
                "duration": 0,
                "prediction_id": None,
                "error": str(e),
            }

    def generate_progressive_audio(
        self,
        scene_prompts: List[Dict[str, Any]],
        duration_per_scene: int = 4,
    ) -> Dict[str, Any]:
        """
        Generate progressive audio across all scenes using continuation.

        This creates a seamless audio track that evolves through all scenes.

        Args:
            scene_prompts: List of scene dictionaries with 'music_prompt' field
            duration_per_scene: Seconds of audio per scene (default: 4)

        Returns:
            dict: {
                "success": bool,
                "final_audio_url": str (full audio for all scenes),
                "total_duration": int,
                "scene_audio_urls": List[str] (audio after each scene),
                "error": str or None
            }

        Example scene_prompts:
            [
                {"scene_number": 1, "music_prompt": "Cinematic ambient, gentle water"},
                {"scene_number": 2, "music_prompt": "Soft luxurious bedroom ambiance"},
                ...
            ]
        """
        logger.info(f"Generating progressive audio for {len(scene_prompts)} scenes")

        scene_audio_urls = []
        current_audio_url = None

        try:
            for i, scene in enumerate(scene_prompts, 1):
                music_prompt = scene.get("music_prompt", "Cinematic background music")

                logger.info(f"Scene {i}/{len(scene_prompts)}: {music_prompt}")

                if i == 1:
                    # First scene: generate initial audio
                    result = self.generate_initial_scene_audio(
                        prompt=music_prompt,
                        duration=duration_per_scene,
                    )
                else:
                    # Subsequent scenes: continue from previous audio
                    result = self.continue_scene_audio(
                        prompt=music_prompt,
                        input_audio_url=current_audio_url,
                        duration=duration_per_scene,
                    )

                if not result["success"]:
                    logger.error(f"Failed to generate audio for scene {i}: {result['error']}")
                    return {
                        "success": False,
                        "final_audio_url": None,
                        "total_duration": 0,
                        "scene_audio_urls": scene_audio_urls,
                        "error": f"Scene {i} audio generation failed: {result['error']}",
                    }

                current_audio_url = result["audio_url"]
                scene_audio_urls.append(current_audio_url)

                logger.info(f"Scene {i} audio complete. Cumulative URL: {current_audio_url}")

            # Final audio URL contains all scenes
            total_duration = len(scene_prompts) * duration_per_scene

            logger.info(f"Progressive audio generation complete. Total: {total_duration}s")
            return {
                "success": True,
                "final_audio_url": current_audio_url,  # Last continuation has all scenes
                "total_duration": total_duration,
                "scene_audio_urls": scene_audio_urls,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Progressive audio generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "final_audio_url": None,
                "total_duration": 0,
                "scene_audio_urls": scene_audio_urls,
                "error": str(e),
            }

    def _get_model_version(self) -> str:
        """Get the MusicGen model version hash from Replicate."""
        # This would need to be updated periodically or fetched from API
        # For now, using a placeholder
        return "b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38"

    def _poll_prediction(
        self,
        prediction_id: str,
        timeout: int = 300,
        poll_interval: int = 2,
    ) -> Dict[str, Any]:
        """
        Poll prediction until completion or timeout.

        Args:
            prediction_id: Replicate prediction ID
            timeout: Max seconds to wait
            poll_interval: Seconds between polls

        Returns:
            dict: Final prediction data with status and output
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            response = self.session.get(
                f"{self.base_url}/predictions/{prediction_id}",
                timeout=10,
            )
            response.raise_for_status()

            data = response.json()
            status = data.get("status")

            if status in ["succeeded", "failed", "canceled"]:
                return data

            logger.debug(f"Prediction {prediction_id} status: {status}")
            time.sleep(poll_interval)

        # Timeout
        logger.error(f"Prediction {prediction_id} timed out after {timeout}s")
        return {
            "status": "timeout",
            "error": f"Prediction timed out after {timeout} seconds",
        }
