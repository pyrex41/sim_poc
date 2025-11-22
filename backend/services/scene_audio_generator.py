"""
Scene Audio Generator Service.

This module handles generating continuous audio tracks from scene prompts
using MusicGen with continuation features. Supports building cohesive
music tracks that match video scene sequences.
"""

import logging
import asyncio
import tempfile
import os
import base64
from typing import List, Optional, Dict, Any, Tuple
import requests

from ..config import get_settings
from ..database import save_generated_audio

logger = logging.getLogger(__name__)
settings = get_settings()


class SceneAudioGenerator:
    """Generates continuous audio tracks from scene prompts using MusicGen continuation"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "REPLICATE_API_TOKEN", None)
        if not self.api_key:
            raise ValueError("REPLICATE_API_TOKEN must be set")

    async def generate_scene_audio(
        self,
        scenes: List[Dict[str, Any]],
        default_duration: float = 4.0,
        model_id: str = "meta/musicgen",
    ) -> bytes:
        """
        Generate continuous audio track from scene prompts using continuation.

        Args:
            scenes: List of scene dictionaries with 'scene_number', 'prompt', 'duration'
            default_duration: Default duration per scene in seconds
            model_id: MusicGen model to use

        Returns:
            Combined audio data as bytes
        """
        if not scenes:
            raise ValueError("No scenes provided")

        logger.info(f"Generating audio for {len(scenes)} scenes using {model_id}")

        combined_audio = None
        total_duration = 0

        for i, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", i + 1)
            prompt = scene.get("prompt", "")
            duration = scene.get("duration", default_duration) or default_duration

            logger.info(f"Processing scene {scene_num}: {prompt[:50]}... ({duration}s)")

            if i == 0:
                # Generate initial clip
                audio_data = await self._generate_initial_clip(
                    prompt, duration, model_id
                )
            else:
                # Continue from previous audio
                if combined_audio is None:
                    raise ValueError(
                        "Cannot continue audio without previous audio data"
                    )
                audio_data = await self._continue_audio(
                    combined_audio, prompt, duration, total_duration, model_id
                )

            # Combine with previous audio
            if combined_audio:
                combined_audio = self._concatenate_audio(combined_audio, audio_data)
            else:
                combined_audio = audio_data

            total_duration += duration
            logger.info(
                f"Scene {scene_num} processed. Total duration: {total_duration}s"
            )

        logger.info(f"Audio generation complete. Final duration: {total_duration}s")
        return combined_audio

    async def _generate_initial_clip(
        self, prompt: str, duration: float, model_id: str
    ) -> bytes:
        """Generate the first audio clip without continuation"""
        payload = {
            "version": "671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
            "input": {
                "model_version": "stereo-melody-large",
                "prompt": prompt,
                "duration": duration,
                "output_format": "mp3",
            },
        }

        return await self._call_replicate_api(payload)

    async def _continue_audio(
        self,
        input_audio: bytes,
        prompt: str,
        duration: float,
        continuation_start: float,
        model_id: str,
    ) -> bytes:
        """Continue audio generation from existing clip"""
        # Encode input audio as base64
        input_audio_b64 = base64.b64encode(input_audio).decode("utf-8")

        payload = {
            "version": "671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
            "input": {
                "model_version": "stereo-melody-large",
                "prompt": prompt,
                "duration": duration,
                "input_audio": input_audio_b64,
                "continuation": True,
                "continuation_start": continuation_start,
                "continuation_end": continuation_start + duration,
                "output_format": "mp3",
            },
        }

        return await self._call_replicate_api(payload)

    async def _call_replicate_api(self, payload: Dict[str, Any]) -> bytes:
        """Call Replicate API and return audio data"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            # Create prediction
            response = requests.post(
                "https://api.replicate.com/v1/predictions",
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            prediction = response.json()

            prediction_id = prediction["id"]
            logger.info(f"Created prediction {prediction_id}")

            # Poll for completion
            audio_url = await self._poll_prediction(prediction_id)

            # Download audio
            audio_response = requests.get(audio_url, timeout=60)
            audio_response.raise_for_status()

            logger.info(f"Downloaded audio: {len(audio_response.content)} bytes")
            return audio_response.content

        except Exception as e:
            logger.error(f"Replicate API call failed: {e}")
            raise

    async def _poll_prediction(self, prediction_id: str, max_attempts: int = 60) -> str:
        """Poll prediction until complete and return audio URL"""
        headers = {"Authorization": f"Bearer {self.api_key}"}

        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"https://api.replicate.com/v1/predictions/{prediction_id}",
                    headers=headers,
                    timeout=10,
                )
                response.raise_for_status()
                prediction = response.json()

                status = prediction.get("status")

                if status == "succeeded":
                    # Extract audio URL from output
                    output = prediction.get("output")
                    if isinstance(output, str):
                        return output
                    elif isinstance(output, list) and output:
                        return output[0]
                    else:
                        raise ValueError(f"Unexpected output format: {output}")

                elif status == "failed":
                    error = prediction.get("error", "Unknown error")
                    raise Exception(f"Prediction failed: {error}")

                elif status == "canceled":
                    raise Exception("Prediction was canceled")

                # Still processing, wait and retry
                await asyncio.sleep(2)

            except Exception as e:
                logger.warning(f"Polling attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2)

        raise Exception(
            f"Prediction {prediction_id} did not complete within {max_attempts * 2} seconds"
        )

    def _concatenate_audio(self, audio1: bytes, audio2: bytes) -> bytes:
        """Concatenate two MP3 files using ffmpeg"""
        import subprocess

        with (
            tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f1,
            tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f2,
            tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as out,
        ):
            try:
                # Write input files
                f1.write(audio1)
                f2.write(audio2)
                f1.flush()
                f2.flush()

                # Use ffmpeg to concatenate
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    f1.name,
                    "-i",
                    f2.name,
                    "-filter_complex",
                    "[0:0][1:0]concat=n=2:v=0:a=1[outa]",
                    "-map",
                    "[outa]",
                    "-c:a",
                    "libmp3lame",
                    "-q:a",
                    "2",  # High quality
                    out.name,
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                if result.returncode != 0:
                    logger.error(f"ffmpeg concatenation failed: {result.stderr}")
                    raise Exception(f"Audio concatenation failed: {result.stderr}")

                # Read output
                with open(out.name, "rb") as f:
                    return f.read()

            finally:
                # Clean up temp files
                for f in [f1, f2, out]:
                    try:
                        os.unlink(f.name)
                    except:
                        pass


async def generate_scene_audio_track(
    scenes: List[Dict[str, Any]],
    default_duration: float = 4.0,
    model_id: str = "meta/musicgen",
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    High-level function to generate scene-based audio track.

    Returns dict with audio_id, audio_url, etc.
    """
    generator = SceneAudioGenerator()
    audio_data = await generator.generate_scene_audio(
        scenes, default_duration, model_id
    )

    # Save to database
    total_duration = sum(
        s.get("duration", default_duration) or default_duration for s in scenes
    )
    audio_id = save_generated_audio(
        prompt=f"Scene-based audio: {len(scenes)} scenes",
        audio_url="",  # Will be served from blob
        model_id=model_id,
        parameters={"scenes": len(scenes), "default_duration": default_duration},
        duration=total_duration,
    )

    total_duration = sum(
        s.get("duration", default_duration) or default_duration for s in scenes
    )

    return {
        "audio_id": audio_id,
        "audio_url": f"/api/audio/{audio_id}/data",
        "total_duration": total_duration,
        "scenes_processed": len(scenes),
        "model_used": model_id,
    }
