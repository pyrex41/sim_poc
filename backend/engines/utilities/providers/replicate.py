"""
Replicate provider for utilities.
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
from .base import BaseUtilityProvider
from ..models import UtilityRequest


logger = logging.getLogger(__name__)


# Tool to model identifier mapping
TOOL_TO_MODEL = {
    "upscale": "clarity-upscaler",
    "remove-background": "rembg",
    "restore-face": "gfpgan",
}


class ReplicateUtilityProvider(BaseUtilityProvider):
    """Replicate implementation for utilities."""

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

        logger.info("ReplicateUtilityProvider initialized")

    async def submit_task(self, params: Dict[str, Any]) -> str:
        """
        Submit a utility task to Replicate.

        Args:
            params: Replicate-formatted parameters

        Returns:
            Replicate prediction ID

        Raises:
            ProviderError: If submission fails
        """
        try:
            logger.info(f"Submitting utility task to Replicate: {params.get('tool', 'unknown')}")

            model_identifier = self._get_model_identifier(params.get('tool'))

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

            logger.info(f"Replicate utility task submitted: {prediction_id}")
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
                # Replicate utility output can be a URL or array of URLs
                output_url = output[0] if isinstance(output, list) else output

                result_data['result'] = {
                    'url': output_url,
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
        Transform our UtilityRequest to Replicate format.

        Args:
            request: Our UtilityRequest object

        Returns:
            Replicate-formatted parameters
        """
        if not isinstance(request, UtilityRequest):
            raise ValueError("Request must be a UtilityRequest")

        # Get tool-specific model
        tool_name = TOOL_TO_MODEL.get(request.tool, request.tool)
        model_config = self.registry.get(tool_name)

        # Build Replicate input based on tool and model requirements
        replicate_input = {}

        # All utilities require an input image
        if request.image:
            replicate_input["image"] = request.image
        elif request.video:
            # Some utilities might support video in the future
            replicate_input["video"] = request.video
        else:
            raise ValueError("Either image or video must be provided")

        # Add tool-specific parameters based on model support
        if model_config:
            optional_inputs = model_config.optional_inputs or []

            # Upscaler parameters
            if "scale" in optional_inputs and request.scale is not None:
                replicate_input["scale"] = request.scale

            if "dynamic" in optional_inputs and request.dynamic is not None:
                replicate_input["dynamic"] = request.dynamic

            if "sharpen" in optional_inputs and request.sharpen is not None:
                replicate_input["sharpen"] = request.sharpen

            if "creativity" in optional_inputs and request.creativity is not None:
                replicate_input["creativity"] = request.creativity

            if "resemblance" in optional_inputs and request.resemblance is not None:
                replicate_input["resemblance"] = request.resemblance

            if "sd_model" in optional_inputs and request.sd_model:
                replicate_input["sd_model"] = request.sd_model

            # Background removal parameters
            if "model" in optional_inputs and request.model:
                replicate_input["model"] = request.model

            if "return_mask" in optional_inputs and request.return_mask is not None:
                replicate_input["return_mask"] = request.return_mask

            # Face restoration parameters
            if "version" in optional_inputs and request.version:
                replicate_input["version"] = request.version

        return {
            "tool": request.tool,
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

    def _get_model_identifier(self, tool: str) -> str:
        """
        Get the Replicate model identifier for a tool.

        Args:
            tool: Tool name

        Returns:
            Replicate model version hash or full identifier
        """
        # Map tool to model name
        model_name = TOOL_TO_MODEL.get(tool, tool)

        # Try to get from registry
        model_config = self.registry.get(model_name)
        if model_config and model_config.category == ModelCategory.UTILITIES:
            # If version is specified in config, use it
            if model_config.version:
                return model_config.version
            # Otherwise return the full identifier
            return model_config.identifier

        # Fallback to using the tool string as-is
        logger.warning(f"Tool {tool} (model {model_name}) not found in registry, using as-is")
        return tool

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
