"""
Image generation engine.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from backend.core import (
    Task,
    EngineType,
    TaskStatus,
    ImageProvider,
)
from backend.engines.base import BaseGenerationEngine
from .models import ImageRequest, ImageResponse
from .repository import ImageRepository
from .providers import ReplicateImageProvider


logger = logging.getLogger(__name__)


class ImageEngine(BaseGenerationEngine[ImageRequest, ImageResponse]):
    """
    Image generation engine.

    Handles image generation through various providers (Replicate, Stability, etc.)
    with a unified interface.
    """

    def __init__(
        self,
        provider: ImageProvider = ImageProvider.REPLICATE,
        repository: ImageRepository = None
    ):
        """
        Initialize image generation engine.

        Args:
            provider: Provider to use (default: Replicate)
            repository: Database repository (optional, creates default if not provided)
        """
        # Initialize repository
        if repository is None:
            repository = ImageRepository()

        # Initialize provider
        provider_instance = self._create_provider(provider)

        # Call parent constructor
        super().__init__(
            engine_type=EngineType.IMAGE,
            provider=provider_instance,
            repository=repository
        )

        logger.info(f"ImageEngine initialized with provider: {provider}")

    def _create_provider(self, provider: ImageProvider):
        """
        Create provider instance based on enum.

        Args:
            provider: Provider enum value

        Returns:
            Provider instance
        """
        if provider == ImageProvider.REPLICATE:
            return ReplicateImageProvider()
        elif provider == ImageProvider.STABILITY:
            # TODO: Implement Stability provider
            raise NotImplementedError("Stability provider not yet implemented")
        elif provider == ImageProvider.MIDJOURNEY:
            # TODO: Implement Midjourney provider
            raise NotImplementedError("Midjourney provider not yet implemented")
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _create_response(self, task: Task) -> ImageResponse:
        """
        Create ImageResponse from completed task.

        Args:
            task: Completed task with result data

        Returns:
            ImageResponse object
        """
        result = task.result or {}

        return ImageResponse(
            id=task.id,
            created_at=task.created_at,
            updated_at=task.completed_at or task.created_at,
            prompt=task.params.get('prompt', ''),
            model=task.params.get('model', 'unknown'),
            provider=task.provider,
            url=result.get('url', ''),
            thumbnail_url=result.get('thumbnail_url'),
            width=result.get('width', 1024),
            height=result.get('height', 1024),
            file_size=result.get('file_size'),
            format=result.get('format', 'png'),
            seed=task.params.get('seed'),
            num_inference_steps=task.params.get('num_inference_steps', 50),
            guidance_scale=task.params.get('guidance_scale', 7.5),
            user_id=task.user_id,
            client_id=task.client_id,
            campaign_id=task.campaign_id,
            local_path=result.get('local_path'),
        )

    def _process_provider_status(self, provider_status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process provider status update and return database updates.

        Args:
            provider_status: Status data from provider

        Returns:
            Dictionary of fields to update in database
        """
        updates = {}

        # Update status
        status_str = provider_status.get('status')
        if status_str:
            updates['status'] = TaskStatus(status_str)

        # Update result if succeeded
        if provider_status.get('result'):
            updates['result'] = provider_status['result']

        # Update error if failed
        if provider_status.get('error'):
            updates['error'] = provider_status['error']

        # Set timestamps
        if updates.get('status') == TaskStatus.PROCESSING and not updates.get('started_at'):
            updates['started_at'] = datetime.now()

        if updates.get('status') in [TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELED]:
            updates['completed_at'] = datetime.now()

        return updates


# Factory function for easy instantiation
def create_image_engine(provider: ImageProvider = ImageProvider.REPLICATE) -> ImageEngine:
    """
    Create an image generation engine.

    Args:
        provider: Provider to use (default: Replicate)

    Returns:
        Configured ImageEngine instance
    """
    return ImageEngine(provider=provider)
