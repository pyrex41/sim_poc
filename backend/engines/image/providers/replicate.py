"""
Replicate provider for image generation.
"""
import logging
import os
from typing import Dict, Any
import requests

from backend.core import (
    BaseRequest,
    ProviderError,
    TaskStatus,
)
from backend.models_registry import get_model_registry, ModelCategory
from .base import BaseImageProvider
from ..models import ImageRequest


logger = logging.getLogger(__name__)


class ReplicateImageProvider(BaseImageProvider):
    """Replicate implementation for image generation."""

    def __init__(self, api_key: str = None):
        """
        Initialize Replicate provider.

        Args:
            api_key: Replicate API key (optional, reads from env if not provided)
        """
        self.api_key = api_key or os.environ.get('REPLICATE_API_KEY')
        if not self.api_key:
            raise ProviderError(
                "Replicate",
                "API key not provided. Set REPLICATE_API_KEY environment variable."
            )

        self.base_url = "https://api.replicate.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        })

        # Get the model registry
        self.registry = get_model_registry()

        logger.info("ReplicateImageProvider initialized")

    async def submit_task(self, params: Dict[str, Any]) -> str:
        """
        Submit an image generation task to Replicate.

        Args:
            params: Replicate-formatted parameters

        Returns:
            Replicate prediction ID

        Raises:
            ProviderError: If submission fails
        """
        try:
            logger.info(f"Submitting image task to Replicate: {params.get('model', 'unknown')}")

            version_hash = self._get_model_version(params.get('model', 'flux'))

            response = self.session.post(
                f"{self.base_url}/predictions",
                json={
                    "version": version_hash,
                    "input": params.get('input', {})
                },
                timeout=30
            )
            response.raise_for_status()

            prediction_data = response.json()
            prediction_id = prediction_data.get('id')

            if not prediction_id:
                raise ProviderError("Replicate", "No prediction ID returned from API")

            logger.info(f"Replicate task submitted: {prediction_id}")
            return prediction_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Replicate API error: {e}")
            raise ProviderError("Replicate", f"API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error submitting to Replicate: {e}")
            raise ProviderError("Replicate", f"Unexpected error: {str(e)}")

    async def get_task_status(self, provider_task_id: str) -> Dict[str, Any]:
        """
        Get the status of a Replicate prediction.

        Args:
            provider_task_id: Replicate prediction ID

        Returns:
            Status dictionary with keys: status, result, error
        """
        try:
            response = self.session.get(
                f"{self.base_url}/predictions/{provider_task_id}",
                timeout=30
            )
            response.raise_for_status()

            prediction = response.json()
            status = prediction.get('status')

            result_data = {
                'status': self._map_status(status),
                'result': None,
                'error': None,
            }

            if status == 'succeeded':
                output = prediction.get('output')
                # Replicate returns array of URLs for images
                image_url = output[0] if isinstance(output, list) else output

                result_data['result'] = {
                    'url': image_url,
                    'format': 'png',  # Default, could be extracted from URL
                }

            elif status in ['failed', 'canceled']:
                result_data['error'] = prediction.get('error', f'Task {status}')

            return result_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking Replicate status: {e}")
            raise ProviderError("Replicate", f"Status check failed: {str(e)}")

    async def cancel_task(self, provider_task_id: str) -> bool:
        """
        Cancel a Replicate prediction.

        Args:
            provider_task_id: Replicate prediction ID

        Returns:
            True if canceled successfully
        """
        try:
            response = self.session.post(
                f"{self.base_url}/predictions/{provider_task_id}/cancel",
                timeout=30
            )
            response.raise_for_status()

            logger.info(f"Canceled Replicate prediction: {provider_task_id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error canceling Replicate prediction: {e}")
            return False

    def transform_request(self, request: BaseRequest) -> Dict[str, Any]:
        """
        Transform our ImageRequest to Replicate format.

        Args:
            request: Our ImageRequest object

        Returns:
            Replicate-formatted parameters
        """
        if not isinstance(request, ImageRequest):
            raise ValueError("Request must be an ImageRequest")

        # Build Replicate input
        # Start with just prompt - flux-schnell has minimal parameters
        replicate_input = {
            "prompt": request.prompt,
        }

        # Add optional parameters (check model support)
        # flux-schnell supports: prompt, go_fast, megapixels, num_outputs, aspect_ratio, output_format, output_quality, seed

        if request.aspect_ratio:
            replicate_input["aspect_ratio"] = request.aspect_ratio if isinstance(request.aspect_ratio, str) else request.aspect_ratio.value

        if request.num_outputs and request.num_outputs > 1:
            replicate_input["num_outputs"] = request.num_outputs

        if request.seed is not None:
            replicate_input["seed"] = request.seed

        return {
            "model": request.model if isinstance(request.model, str) else request.model.value,
            "input": replicate_input
        }

    def transform_response(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Replicate response to our format.

        Args:
            provider_data: Replicate response data

        Returns:
            Our standardized response data
        """
        return provider_data  # Already in the right format from get_task_status

    def _get_model_version(self, model: str) -> str:
        """
        Get the Replicate model version hash.

        Args:
            model: Model name or identifier

        Returns:
            Replicate model version hash
        """
        # Try to get from registry
        model_config = self.registry.get(model)
        if model_config and model_config.category == ModelCategory.IMAGE:
            # If version is specified in config, use it
            if model_config.version:
                return model_config.version
            # Otherwise return the full identifier
            return model_config.identifier

        # Fallback to using the model string as-is
        logger.warning(f"Model {model} not found in registry, using as-is")
        return model

    def _map_status(self, replicate_status: str) -> str:
        """
        Map Replicate status to our TaskStatus.

        Args:
            replicate_status: Replicate's status string

        Returns:
            Our TaskStatus value
        """
        status_map = {
            'starting': TaskStatus.PROCESSING.value,
            'processing': TaskStatus.PROCESSING.value,
            'succeeded': TaskStatus.SUCCEEDED.value,
            'failed': TaskStatus.FAILED.value,
            'canceled': TaskStatus.CANCELED.value,
        }

        return status_map.get(replicate_status, TaskStatus.PENDING.value)
