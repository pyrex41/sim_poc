"""
Base generation engine abstract class.

All generation engines (Image, Video, Audio, Prompt) inherit from this base.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

from backend.core import (
    BaseRequest,
    BaseResponse,
    Task,
    TaskStatus,
    EngineType,
    TaskFilter,
    PaginatedResponse,
    ResourceNotFoundError,
    TaskNotReadyError,
    TaskFailedError,
    TaskCanceledError,
)


logger = logging.getLogger(__name__)


# Type variables for generic request/response types
TRequest = TypeVar('TRequest', bound=BaseRequest)
TResponse = TypeVar('TResponse', bound=BaseResponse)


class BaseProvider(ABC):
    """Base class for all providers (Replicate, Runway, etc.)."""

    @abstractmethod
    async def submit_task(self, params: Dict[str, Any]) -> str:
        """
        Submit a generation task to the provider.

        Args:
            params: Provider-specific parameters

        Returns:
            Provider's task ID
        """
        pass

    @abstractmethod
    async def get_task_status(self, provider_task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task from the provider.

        Args:
            provider_task_id: Provider's task ID

        Returns:
            Task status data including status, result, error
        """
        pass

    @abstractmethod
    async def cancel_task(self, provider_task_id: str) -> bool:
        """
        Cancel a task on the provider.

        Args:
            provider_task_id: Provider's task ID

        Returns:
            True if canceled successfully
        """
        pass

    @abstractmethod
    def transform_request(self, request: BaseRequest) -> Dict[str, Any]:
        """
        Transform our request format to provider's format.

        Args:
            request: Our standardized request

        Returns:
            Provider-specific parameters
        """
        pass

    @abstractmethod
    def transform_response(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform provider's response to our format.

        Args:
            provider_data: Provider's response data

        Returns:
            Our standardized response data
        """
        pass


class BaseGenerationEngine(ABC, Generic[TRequest, TResponse]):
    """
    Abstract base class for all generation engines.

    Provides standard interface for:
    - Submitting generation tasks
    - Checking task status
    - Retrieving results
    - Canceling tasks
    - Listing tasks
    """

    def __init__(
        self,
        engine_type: EngineType,
        provider: BaseProvider,
        repository: Any  # Will be typed more specifically in concrete implementations
    ):
        """
        Initialize generation engine.

        Args:
            engine_type: Type of engine (image, video, audio, prompt)
            provider: Provider implementation for external API
            repository: Database repository for persistence
        """
        self.engine_type = engine_type
        self.provider = provider
        self.repository = repository

    async def generate(
        self,
        request: TRequest,
        user_id: str
    ) -> Task:
        """
        Start a new generation task.

        Args:
            request: Generation request parameters
            user_id: ID of the user making the request

        Returns:
            Task object with task ID and initial status
        """
        try:
            # Create task ID
            task_id = str(uuid.uuid4())

            # Transform request to provider format
            provider_params = self.provider.transform_request(request)

            # Submit to provider
            logger.info(f"Submitting {self.engine_type} task {task_id} to provider")
            provider_task_id = await self.provider.submit_task(provider_params)

            # Create task object
            task = Task(
                id=task_id,
                engine=self.engine_type,
                status=TaskStatus.PENDING,
                provider=self.provider.__class__.__name__,
                provider_task_id=provider_task_id,
                user_id=user_id,
                client_id=request.client_id,
                campaign_id=request.campaign_id,
                params=request.model_dump(exclude={'client_id', 'campaign_id', 'metadata'}),
                metadata=request.metadata,
                created_at=datetime.now(),
            )

            # Save to database
            await self.repository.create_task(task)

            logger.info(
                f"Created {self.engine_type} task {task_id} "
                f"(provider_task_id: {provider_task_id})"
            )

            return task

        except Exception as e:
            logger.error(f"Failed to create {self.engine_type} task: {e}", exc_info=True)
            raise

    async def get_task(self, task_id: str, user_id: str) -> Task:
        """
        Get task by ID.

        Args:
            task_id: Task ID
            user_id: User ID (for authorization)

        Returns:
            Task object

        Raises:
            ResourceNotFoundError: If task doesn't exist
        """
        task = await self.repository.get_task(task_id)

        if not task:
            raise ResourceNotFoundError("Task", task_id)

        # Verify ownership (unless admin)
        if task.user_id != user_id:
            raise ResourceNotFoundError("Task", task_id)  # Don't reveal existence

        return task

    async def get_result(self, task_id: str, user_id: str) -> TResponse:
        """
        Get the result of a completed task.

        Args:
            task_id: Task ID
            user_id: User ID (for authorization)

        Returns:
            Result object

        Raises:
            ResourceNotFoundError: If task doesn't exist
            TaskNotReadyError: If task hasn't completed
            TaskFailedError: If task failed
            TaskCanceledError: If task was canceled
        """
        task = await self.get_task(task_id, user_id)

        if task.status == TaskStatus.FAILED:
            raise TaskFailedError(task_id, task.error or "Unknown error")

        if task.status == TaskStatus.CANCELED:
            raise TaskCanceledError(task_id)

        if task.status != TaskStatus.SUCCEEDED:
            raise TaskNotReadyError(task_id, task.status.value)

        # Transform result to response object
        return self._create_response(task)

    async def update_task_status(self, task_id: str) -> Task:
        """
        Update task status from provider.

        Args:
            task_id: Task ID

        Returns:
            Updated task object
        """
        task = await self.repository.get_task(task_id)

        if not task:
            raise ResourceNotFoundError("Task", task_id)

        # Skip if already terminal
        if task.is_terminal:
            return task

        try:
            # Get status from provider
            provider_status = await self.provider.get_task_status(task.provider_task_id)

            # Update task based on provider response
            updates = self._process_provider_status(provider_status)

            # Update in database
            task = await self.repository.update_task(task_id, updates)

            logger.info(
                f"Updated {self.engine_type} task {task_id} "
                f"status: {task.status}"
            )

            return task

        except Exception as e:
            logger.error(
                f"Failed to update {self.engine_type} task {task_id}: {e}",
                exc_info=True
            )
            # Mark task as failed
            await self.repository.update_task(
                task_id,
                {
                    "status": TaskStatus.FAILED,
                    "error": f"Status update failed: {str(e)}",
                    "completed_at": datetime.now()
                }
            )
            raise

    async def cancel(self, task_id: str, user_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: Task ID
            user_id: User ID (for authorization)

        Returns:
            True if canceled successfully
        """
        task = await self.get_task(task_id, user_id)

        # Can't cancel terminal tasks
        if task.is_terminal:
            return False

        try:
            # Cancel on provider
            canceled = await self.provider.cancel_task(task.provider_task_id)

            if canceled:
                # Update in database
                await self.repository.update_task(
                    task_id,
                    {
                        "status": TaskStatus.CANCELED,
                        "completed_at": datetime.now()
                    }
                )

                logger.info(f"Canceled {self.engine_type} task {task_id}")

            return canceled

        except Exception as e:
            logger.error(f"Failed to cancel {self.engine_type} task {task_id}: {e}")
            return False

    async def list_tasks(
        self,
        filters: TaskFilter
    ) -> PaginatedResponse[Task]:
        """
        List tasks with filtering and pagination.

        Args:
            filters: Filter parameters

        Returns:
            Paginated list of tasks
        """
        # Add engine type to filters
        filters_dict = filters.model_dump()
        filters_dict['engine'] = self.engine_type

        tasks, total = await self.repository.list_tasks(filters_dict)

        return PaginatedResponse.create(
            items=tasks,
            total=total,
            page=filters.page,
            page_size=filters.page_size
        )

    @abstractmethod
    def _create_response(self, task: Task) -> TResponse:
        """
        Create response object from task result.

        Args:
            task: Completed task

        Returns:
            Typed response object
        """
        pass

    @abstractmethod
    def _process_provider_status(self, provider_status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process provider status and return database updates.

        Args:
            provider_status: Status data from provider

        Returns:
            Dictionary of fields to update in database
        """
        pass
