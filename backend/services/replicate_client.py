"""
Replicate API client for video generation with polling logic.

This module handles all interactions with the Replicate API for image and video generation,
including polling for prediction status with exponential backoff retry logic.
"""

import logging
import time
from os import environ
from typing import Dict, List, Optional, Any
import requests

# Configure logging
logger = logging.getLogger(__name__)


class ReplicateClient:
    """
    Client for interacting with Replicate API for image and video generation.

    This client provides methods for:
    - Generating images using Flux-Schnell model (or other image models)
    - Generating videos using SkyReels-2 model
    - Polling prediction status with automatic retries
    - Estimating costs for operations

    Note: Image upscaling is handled through the standard image generation
    workflow via generate_image(). Upscaler models from the 'super-resolution'
    collection accept an 'image' input parameter along with upscaling parameters
    (scale, dynamic, sharpen, etc.) instead of just 'prompt'.

    Attributes:
        api_key (str): Replicate API key for authentication
        base_url (str): Base URL for Replicate API
        session (requests.Session): HTTP session for API requests
    """

    # Model pricing (in USD)
    FLUX_SCHNELL_PRICE_PER_IMAGE = 0.003
    SKYREELS2_PRICE_PER_SECOND = 0.10
    UPSCALER_PRICE_PER_IMAGE = 0.016  # Reference pricing for clarity-upscaler

    # Default models
    DEFAULT_IMAGE_MODEL = "black-forest-labs/flux-schnell"
    DEFAULT_VIDEO_MODEL = "fofr/skyreels-2"
    DEFAULT_UPSCALER_MODEL = "philz1337x/clarity-upscaler"  # Configurable via settings

    # Polling configuration
    DEFAULT_POLL_INTERVAL = 5  # seconds
    DEFAULT_TIMEOUT = 600  # 10 minutes
    MAX_BACKOFF_DELAY = 45  # seconds

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Replicate client.

        Args:
            api_key (str, optional): Replicate API key. If None, will attempt to
                                    read from REPLICATE_API_KEY environment variable.

        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.api_key = api_key or environ.get('REPLICATE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Replicate API key not provided. Either pass api_key parameter "
                "or set REPLICATE_API_KEY environment variable."
            )

        self.base_url = "https://api.replicate.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        })

        logger.info("ReplicateClient initialized successfully")

    def generate_image(
        self,
        prompt: str,
        model: str = DEFAULT_IMAGE_MODEL
    ) -> Dict[str, Any]:
        """
        Generate an image using Replicate's Flux-Schnell model.

        Args:
            prompt (str): Text description of the image to generate
            model (str): Model identifier (default: black-forest-labs/flux-schnell)

        Returns:
            dict: Response containing:
                - success (bool): Whether the request was successful
                - image_url (str): URL of the generated image (if successful)
                - error (str): Error message (if failed)
                - prediction_id (str): Replicate prediction ID for polling

        Example:
            >>> client = ReplicateClient()
            >>> result = client.generate_image("a red sports car")
            >>> if result['success']:
            ...     print(f"Image URL: {result['image_url']}")
        """
        logger.info(f"Generating image with prompt: '{prompt[:50]}...'")

        try:
            # Create prediction
            response = self.session.post(
                f"{self.base_url}/predictions",
                json={
                    "version": self._get_model_version(model),
                    "input": {"prompt": prompt}
                },
                timeout=30
            )
            response.raise_for_status()

            prediction_data = response.json()
            prediction_id = prediction_data.get('id')

            if not prediction_id:
                logger.error("No prediction ID returned from API")
                return {
                    "success": False,
                    "image_url": None,
                    "error": "No prediction ID returned from API",
                    "prediction_id": None
                }

            logger.info(f"Image generation started, prediction ID: {prediction_id}")

            # Poll for completion
            poll_result = self.poll_prediction(prediction_id)

            if poll_result['status'] == 'succeeded':
                # Extract image URL from output
                output = poll_result.get('output')
                image_url = output[0] if isinstance(output, list) else output

                logger.info(f"Image generation succeeded: {image_url}")
                return {
                    "success": True,
                    "image_url": image_url,
                    "error": None,
                    "prediction_id": prediction_id
                }
            else:
                error_msg = poll_result.get('error', f"Generation failed with status: {poll_result['status']}")
                logger.error(f"Image generation failed: {error_msg}")
                return {
                    "success": False,
                    "image_url": None,
                    "error": error_msg,
                    "prediction_id": prediction_id
                }

        except requests.exceptions.Timeout:
            logger.error("Request timeout while generating image")
            return {
                "success": False,
                "image_url": None,
                "error": "Request timeout",
                "prediction_id": None
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while generating image: {str(e)}")
            return {
                "success": False,
                "image_url": None,
                "error": f"Network error: {str(e)}",
                "prediction_id": None
            }
        except Exception as e:
            logger.error(f"Unexpected error while generating image: {str(e)}")
            return {
                "success": False,
                "image_url": None,
                "error": f"Unexpected error: {str(e)}",
                "prediction_id": None
            }

    def generate_video(
        self,
        image_urls: List[str],
        model: str = DEFAULT_VIDEO_MODEL
    ) -> Dict[str, Any]:
        """
        Generate a video by stitching together images using SkyReels-2 model.

        Args:
            image_urls (list[str]): List of image URLs to stitch into a video
            model (str): Model identifier (default: fofr/skyreels-2)

        Returns:
            dict: Response containing:
                - success (bool): Whether the request was successful
                - video_url (str): URL of the generated video (if successful)
                - error (str): Error message (if failed)
                - prediction_id (str): Replicate prediction ID for polling
                - duration_seconds (int): Duration of the generated video

        Example:
            >>> client = ReplicateClient()
            >>> images = ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]
            >>> result = client.generate_video(images)
            >>> if result['success']:
            ...     print(f"Video URL: {result['video_url']}")
        """
        if not image_urls:
            logger.error("No image URLs provided for video generation")
            return {
                "success": False,
                "video_url": None,
                "error": "No image URLs provided",
                "prediction_id": None,
                "duration_seconds": 0
            }

        logger.info(f"Generating video from {len(image_urls)} images")

        try:
            # Create prediction for video generation
            response = self.session.post(
                f"{self.base_url}/predictions",
                json={
                    "version": self._get_model_version(model),
                    "input": {
                        "image_urls": image_urls
                    }
                },
                timeout=30
            )
            response.raise_for_status()

            prediction_data = response.json()
            prediction_id = prediction_data.get('id')

            if not prediction_id:
                logger.error("No prediction ID returned from API")
                return {
                    "success": False,
                    "video_url": None,
                    "error": "No prediction ID returned from API",
                    "prediction_id": None,
                    "duration_seconds": 0
                }

            logger.info(f"Video generation started, prediction ID: {prediction_id}")

            # Poll for completion (videos take longer, so use extended timeout)
            poll_result = self.poll_prediction(prediction_id, timeout=1200)  # 20 minutes

            if poll_result['status'] == 'succeeded':
                # Extract video URL from output
                output = poll_result.get('output')
                video_url = output[0] if isinstance(output, list) else output

                # Estimate duration based on number of images (rough estimate)
                duration_seconds = len(image_urls) * 2  # Assume ~2 seconds per image

                logger.info(f"Video generation succeeded: {video_url}")
                return {
                    "success": True,
                    "video_url": video_url,
                    "error": None,
                    "prediction_id": prediction_id,
                    "duration_seconds": duration_seconds
                }
            else:
                error_msg = poll_result.get('error', f"Generation failed with status: {poll_result['status']}")
                logger.error(f"Video generation failed: {error_msg}")
                return {
                    "success": False,
                    "video_url": None,
                    "error": error_msg,
                    "prediction_id": prediction_id,
                    "duration_seconds": 0
                }

        except requests.exceptions.Timeout:
            logger.error("Request timeout while generating video")
            return {
                "success": False,
                "video_url": None,
                "error": "Request timeout",
                "prediction_id": None,
                "duration_seconds": 0
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while generating video: {str(e)}")
            return {
                "success": False,
                "video_url": None,
                "error": f"Network error: {str(e)}",
                "prediction_id": None,
                "duration_seconds": 0
            }
        except Exception as e:
            logger.error(f"Unexpected error while generating video: {str(e)}")
            return {
                "success": False,
                "video_url": None,
                "error": f"Unexpected error: {str(e)}",
                "prediction_id": None,
                "duration_seconds": 0
            }

    def poll_prediction(
        self,
        prediction_id: str,
        timeout: int = DEFAULT_TIMEOUT,
        interval: int = DEFAULT_POLL_INTERVAL
    ) -> Dict[str, Any]:
        """
        Poll a prediction until it completes or times out.

        Implements exponential backoff on errors:
        - First retry: 5 seconds
        - Second retry: 15 seconds
        - Third+ retry: 45 seconds

        Args:
            prediction_id (str): The prediction ID to poll
            timeout (int): Maximum time to wait in seconds (default: 600)
            interval (int): Polling interval in seconds (default: 5)

        Returns:
            dict: Prediction result containing:
                - status (str): Final status (succeeded, failed, canceled, timeout)
                - output (any): Output data if succeeded
                - error (str): Error message if failed

        Example:
            >>> client = ReplicateClient()
            >>> result = client.poll_prediction("abc123")
            >>> if result['status'] == 'succeeded':
            ...     print(result['output'])
        """
        logger.info(f"Polling prediction {prediction_id} (timeout: {timeout}s, interval: {interval}s)")

        start_time = time.time()
        retry_count = 0
        backoff_delays = [5, 15, 45]  # Exponential backoff sequence

        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.error(f"Polling timeout after {elapsed:.1f}s")
                return {
                    "status": "timeout",
                    "output": None,
                    "error": f"Polling timeout after {timeout} seconds"
                }

            try:
                # Get prediction status
                response = self.session.get(
                    f"{self.base_url}/predictions/{prediction_id}",
                    timeout=30
                )
                response.raise_for_status()

                data = response.json()
                status = data.get('status')

                logger.debug(f"Prediction {prediction_id} status: {status}")

                # Check if prediction is complete
                if status == 'succeeded':
                    logger.info(f"Prediction {prediction_id} succeeded")
                    return {
                        "status": "succeeded",
                        "output": data.get('output'),
                        "error": None
                    }
                elif status == 'failed':
                    error_msg = data.get('error', 'Unknown error')
                    logger.error(f"Prediction {prediction_id} failed: {error_msg}")
                    return {
                        "status": "failed",
                        "output": None,
                        "error": error_msg
                    }
                elif status == 'canceled':
                    logger.warning(f"Prediction {prediction_id} was canceled")
                    return {
                        "status": "canceled",
                        "output": None,
                        "error": "Prediction was canceled"
                    }

                # Still processing, wait before next poll
                time.sleep(interval)
                retry_count = 0  # Reset retry count on successful poll

            except requests.exceptions.HTTPError as e:
                # Handle rate limiting (429) specially
                if e.response.status_code == 429:
                    logger.warning(f"Rate limit hit, backing off...")
                    delay = backoff_delays[min(retry_count, len(backoff_delays) - 1)]
                    time.sleep(delay)
                    retry_count += 1
                    continue
                else:
                    logger.error(f"HTTP error while polling: {str(e)}")
                    return {
                        "status": "failed",
                        "output": None,
                        "error": f"HTTP error: {str(e)}"
                    }

            except requests.exceptions.Timeout:
                logger.warning(f"Poll request timeout, retrying with backoff...")
                delay = backoff_delays[min(retry_count, len(backoff_delays) - 1)]
                time.sleep(delay)
                retry_count += 1
                continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Network error while polling: {str(e)}")
                # Apply backoff for network errors
                if retry_count < 3:
                    delay = backoff_delays[retry_count]
                    logger.warning(f"Retrying after {delay}s backoff...")
                    time.sleep(delay)
                    retry_count += 1
                    continue
                else:
                    # Max retries exceeded
                    return {
                        "status": "failed",
                        "output": None,
                        "error": f"Network error after {retry_count} retries: {str(e)}"
                    }

            except Exception as e:
                logger.error(f"Unexpected error while polling: {str(e)}")
                return {
                    "status": "failed",
                    "output": None,
                    "error": f"Unexpected error: {str(e)}"
                }

    def estimate_cost(self, num_images: int, video_duration: int) -> float:
        """
        Calculate estimated cost for image and video generation.

        Pricing:
        - Flux-Schnell: $0.003 per image
        - SkyReels-2: $0.10 per second of video

        Args:
            num_images (int): Number of images to generate
            video_duration (int): Duration of video in seconds

        Returns:
            float: Total estimated cost in USD

        Example:
            >>> client = ReplicateClient()
            >>> cost = client.estimate_cost(num_images=10, video_duration=20)
            >>> print(f"Estimated cost: ${cost:.2f}")
            Estimated cost: $2.03
        """
        image_cost = num_images * self.FLUX_SCHNELL_PRICE_PER_IMAGE
        video_cost = video_duration * self.SKYREELS2_PRICE_PER_SECOND
        total_cost = image_cost + video_cost

        logger.info(
            f"Cost estimate - Images: {num_images} x ${self.FLUX_SCHNELL_PRICE_PER_IMAGE} = ${image_cost:.3f}, "
            f"Video: {video_duration}s x ${self.SKYREELS2_PRICE_PER_SECOND} = ${video_cost:.2f}, "
            f"Total: ${total_cost:.2f}"
        )

        return total_cost

    def _get_model_version(self, model: str) -> str:
        """
        Get the model version string for Replicate API.

        For simplicity, this returns the model string as-is. In production,
        you would maintain a mapping of model names to their version hashes.

        Args:
            model (str): Model identifier

        Returns:
            str: Model version identifier
        """
        # In a real implementation, you would query the Replicate API
        # to get the latest version hash for the model, or maintain
        # a mapping of model names to version hashes
        return model

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.session.close()
        logger.info("ReplicateClient session closed")
