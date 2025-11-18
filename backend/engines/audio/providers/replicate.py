"""
Replicate provider for audio generation.
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
from .base import BaseAudioProvider
from ..models import AudioRequest


logger = logging.getLogger(__name__)


class ReplicateAudioProvider(BaseAudioProvider):
    """Replicate implementation for audio generation."""

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

        logger.info("ReplicateAudioProvider initialized")

    async def submit_task(self, params: Dict[str, Any]) -> str:
        """
        Submit an audio generation task to Replicate.

        Args:
            params: Replicate-formatted parameters

        Returns:
            Replicate prediction ID

        Raises:
            ProviderError: If submission fails
        """
        try:
            logger.info(f"Submitting audio task to Replicate: {params.get('model', 'unknown')}")

            model_identifier = self._get_model_identifier(params.get('model', 'musicgen'))

            response = self.session.post(
                f"{self.base_url}/predictions",
                json={
                    "version": model_identifier,
                    "input": params.get('input', {})
                },
                timeout=60
            )
            response.raise_for_status()

            prediction_data = response.json()
            prediction_id = prediction_data.get('id')

            if not prediction_id:
                raise ProviderError("Replicate", "No prediction ID returned from API")

            logger.info(f"Replicate audio task submitted: {prediction_id}")
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
                # Replicate audio output can be a URL or array of URLs
                audio_url = output[0] if isinstance(output, list) else output

                result_data['result'] = {
                    'url': audio_url,
                    'format': 'mp3',  # Default, could be extracted from URL
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
        Transform our AudioRequest to Replicate format.

        Args:
            request: Our AudioRequest object

        Returns:
            Replicate-formatted parameters
        """
        if not isinstance(request, AudioRequest):
            raise ValueError("Request must be an AudioRequest")

        # Get model config from registry to understand required inputs
        model_name = request.model if isinstance(request.model, str) else request.model.value
        model_config = self.registry.get(model_name)

        # Build Replicate input based on model requirements
        replicate_input = {
            "prompt": request.prompt,
        }

        # Add optional parameters based on what model supports
        if model_config:
            optional_inputs = model_config.optional_inputs or []

            if "model_version" in optional_inputs and request.model_version:
                replicate_input["model_version"] = request.model_version

            if "duration" in optional_inputs and request.duration:
                replicate_input["duration"] = request.duration

            if "temperature" in optional_inputs and request.temperature is not None:
                replicate_input["temperature"] = request.temperature

            if "top_k" in optional_inputs and request.top_k is not None:
                replicate_input["top_k"] = request.top_k

            if "top_p" in optional_inputs and request.top_p is not None:
                replicate_input["top_p"] = request.top_p

            if "text_temp" in optional_inputs and request.text_temp is not None:
                replicate_input["text_temp"] = request.text_temp

            if "waveform_temp" in optional_inputs and request.waveform_temp is not None:
                replicate_input["waveform_temp"] = request.waveform_temp

        if request.seed is not None:
            replicate_input["seed"] = request.seed

        return {
            "model": model_name,
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

    def _get_model_identifier(self, model: str) -> str:
        """
        Get the Replicate model version hash or identifier.

        Args:
            model: Model name or identifier

        Returns:
            Replicate model version hash or full identifier
        """
        # Try to get from registry
        model_config = self.registry.get(model)
        if model_config and model_config.category == ModelCategory.AUDIO:
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
