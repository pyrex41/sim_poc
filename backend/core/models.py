"""
Base Pydantic models for the generation platform.
"""
from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field, ConfigDict
from .types import TaskStatus, EngineType


# Base Request Model
class BaseRequest(BaseModel):
    """Base class for all generation requests."""
    model_config = ConfigDict(use_enum_values=True)

    client_id: Optional[str] = Field(None, description="Client ID for organization")
    campaign_id: Optional[str] = Field(None, description="Campaign ID for grouping")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


# Base Response Model
class BaseResponse(BaseModel):
    """Base class for all generation responses."""
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# Task Model
class Task(BaseModel):
    """Represents an async generation task."""
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Task unique identifier")
    engine: EngineType = Field(..., description="Engine type that created this task")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current task status")
    provider: str = Field(..., description="Provider used for generation")
    provider_task_id: Optional[str] = Field(None, description="External provider's task ID")

    # User context
    user_id: str = Field(..., description="User who created the task")
    client_id: Optional[str] = Field(None, description="Client ID")
    campaign_id: Optional[str] = Field(None, description="Campaign ID")

    # Task details
    params: Dict[str, Any] = Field(default_factory=dict, description="Generation parameters")
    result: Optional[Dict[str, Any]] = Field(None, description="Generation result data")
    error: Optional[str] = Field(None, description="Error message if failed")

    # Timestamps
    created_at: datetime = Field(..., description="Task creation time")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")

    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        return self.status in {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELED}

    @property
    def is_processing(self) -> bool:
        """Check if task is currently processing."""
        return self.status == TaskStatus.PROCESSING

    @property
    def is_pending(self) -> bool:
        """Check if task is pending."""
        return self.status == TaskStatus.PENDING


# Generic typed response wrapper
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    model_config = ConfigDict(use_enum_values=True)

    items: list[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Items per page")
    has_more: bool = Field(..., description="Whether more items exist")

    @classmethod
    def create(cls, items: list[T], total: int, page: int = 1, page_size: int = 50):
        """Helper to create paginated response."""
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(page * page_size) < total
        )


class ErrorResponse(BaseModel):
    """Standard error response format."""
    model_config = ConfigDict(use_enum_values=True)

    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class HealthResponse(BaseModel):
    """Health check response."""
    model_config = ConfigDict(use_enum_values=True)

    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Health check timestamp")
    services: Dict[str, str] = Field(default_factory=dict, description="Service statuses")


# Asset Model Base
class AssetBase(BaseResponse):
    """Base model for assets (uploaded or generated)."""

    asset_type: str = Field(..., description="Type of asset")
    filename: str = Field(..., description="Original or generated filename")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")
    url: Optional[str] = Field(None, description="Access URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")

    # Context
    user_id: str = Field(..., description="Owner user ID")
    client_id: Optional[str] = Field(None, description="Client ID")
    campaign_id: Optional[str] = Field(None, description="Campaign ID")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata")
    tags: list[str] = Field(default_factory=list, description="Asset tags")


# Filter Models
class BaseFilter(BaseModel):
    """Base filter for list queries."""
    model_config = ConfigDict(use_enum_values=True)

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")

    user_id: Optional[str] = Field(None, description="Filter by user ID")
    client_id: Optional[str] = Field(None, description="Filter by client ID")
    campaign_id: Optional[str] = Field(None, description="Filter by campaign ID")


class TaskFilter(BaseFilter):
    """Filter for task queries."""

    engine: Optional[EngineType] = Field(None, description="Filter by engine type")
    status: Optional[TaskStatus] = Field(None, description="Filter by status")
    provider: Optional[str] = Field(None, description="Filter by provider")
