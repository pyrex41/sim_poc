"""
Utilities engine implementation for image/video processing tools.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from backend.core import (
    Task,
    TaskStatus,
    EngineType,
    TaskFilter,
    PaginatedResponse,
    ProviderError,
)
from backend.engines.base import BaseGenerationEngine
from .models import UtilityRequest, UtilityResponse
from .repository import UtilitiesRepository
from .providers import ReplicateUtilityProvider


logger = logging.getLogger(__name__)


class UtilitiesEngine(BaseGenerationEngine[UtilityRequest, UtilityResponse]):
    """Utilities engine for image/video processing with provider abstraction."""

    def __init__(self, repository: Optional[UtilitiesRepository] = None):
        """
        Initialize utilities engine.

        Args:
            repository: Optional repository for dependency injection
        """
        self.repository = repository or UtilitiesRepository()
        self.providers = {
            'replicate': ReplicateUtilityProvider(),
        }

        logger.info("UtilitiesEngine initialized")

    async def generate(self, request: UtilityRequest, user_id: str) -> Task:
        """
        Start a utility processing task.

        Args:
            request: Utility processing request
            user_id: User ID

        Returns:
            Task object with pending status
        """
        # Create task ID
        task_id = str(uuid.uuid4())

        # Get provider
        provider_name = 'replicate'  # Default for now
        provider = self.providers.get(provider_name)

        if not provider:
            raise ProviderError(provider_name, f"Provider {provider_name} not available")

        # Transform request to provider format
        provider_params = provider.transform_request(request)

        # Create task record
        task = Task(
            id=task_id,
            engine=EngineType.UTILITIES,
            status=TaskStatus.PENDING,
            provider=provider_name,
            provider_task_id=None,
            user_id=user_id,
            client_id=request.client_id,
            campaign_id=request.campaign_id,
            params=request.model_dump(),
            result=None,
            error=None,
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            metadata=request.metadata or {},
        )

        # Save to database
        task = await self.repository.create_task(task)

        # Submit to provider
        try:
            provider_task_id = await provider.submit_task(provider_params)

            # Update task with provider ID and processing status
            task = await self.repository.update_task(
                task_id,
                {
                    'provider_task_id': provider_task_id,
                    'status': TaskStatus.PROCESSING,
                    'started_at': datetime.now(),
                }
            )

            logger.info(f"Utility task {task_id} submitted to {provider_name}: {provider_task_id}")

        except Exception as e:
            # Update task with error
            logger.error(f"Failed to submit utility task {task_id}: {e}")
            task = await self.repository.update_task(
                task_id,
                {
                    'status': TaskStatus.FAILED,
                    'error': str(e),
                    'completed_at': datetime.now(),
                }
            )

        return task

    async def get_task(self, task_id: str, user_id: str) -> Task:
        """
        Get task status and details.

        Args:
            task_id: Task ID
            user_id: User ID

        Returns:
            Task object
        """
        task = await self.repository.get_task(task_id)

        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Check if task is still processing and needs status update
        if task.status == TaskStatus.PROCESSING and task.provider_task_id:
            provider = self.providers.get(task.provider)
            if provider:
                try:
                    status_data = await provider.get_task_status(task.provider_task_id)

                    # Update task if status changed
                    if status_data['status'] != task.status.value:
                        updates = {'status': status_data['status']}

                        if status_data['status'] == TaskStatus.SUCCEEDED.value:
                            updates['result'] = status_data['result']
                            updates['completed_at'] = datetime.now()

                        elif status_data['status'] == TaskStatus.FAILED.value:
                            updates['error'] = status_data['error']
                            updates['completed_at'] = datetime.now()

                        task = await self.repository.update_task(task_id, updates)

                except Exception as e:
                    logger.error(f"Error checking provider status for task {task_id}: {e}")

        return task

    async def get_result(self, task_id: str, user_id: str) -> UtilityResponse:
        """
        Get the final utility result.

        Args:
            task_id: Task ID
            user_id: User ID

        Returns:
            UtilityResponse with processed data

        Raises:
            ValueError: If task not found or not ready
        """
        task = await self.get_task(task_id, user_id)

        if task.status != TaskStatus.SUCCEEDED:
            raise ValueError(f"Task {task_id} is not complete (status: {task.status.value})")

        if not task.result:
            raise ValueError(f"Task {task_id} has no result")

        # Create response from task
        return await self.repository.save_utility_result(task_id, task.result)

    async def cancel(self, task_id: str, user_id: str) -> bool:
        """
        Cancel a running task.

        Args:
            task_id: Task ID
            user_id: User ID

        Returns:
            True if canceled successfully
        """
        task = await self.repository.get_task(task_id)

        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            logger.warning(f"Cannot cancel task {task_id} with status {task.status.value}")
            return False

        # Try to cancel with provider
        if task.provider_task_id:
            provider = self.providers.get(task.provider)
            if provider:
                await provider.cancel_task(task.provider_task_id)

        # Update task status
        await self.repository.update_task(
            task_id,
            {
                'status': TaskStatus.CANCELED,
                'completed_at': datetime.now(),
            }
        )

        logger.info(f"Canceled utility task {task_id}")
        return True

    async def list_tasks(self, filters: TaskFilter) -> PaginatedResponse[Task]:
        """
        List utility processing tasks.

        Args:
            filters: Filter parameters

        Returns:
            Paginated list of tasks
        """
        tasks, total = await self.repository.list_tasks(filters.model_dump())

        return PaginatedResponse(
            items=tasks,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            pages=(total + filters.page_size - 1) // filters.page_size,
        )
