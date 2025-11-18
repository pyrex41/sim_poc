"""
Custom exception hierarchy for the generation platform.
"""
from typing import Any, Dict, Optional


class PlatformException(Exception):
    """Base exception for all platform errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# Authentication & Authorization
class AuthenticationError(PlatformException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(PlatformException):
    """Raised when user lacks permission for an action."""

    def __init__(self, message: str = "Unauthorized access", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, details=details)


# Validation
class ValidationError(PlatformException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class InvalidParameterError(ValidationError):
    """Raised when a parameter has an invalid value."""
    pass


class MissingParameterError(ValidationError):
    """Raised when a required parameter is missing."""
    pass


# Resource Errors
class NotFoundError(PlatformException):
    """Raised when a resource is not found (simple version)."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, details=details)


class ResourceNotFoundError(PlatformException):
    """Raised when a requested resource doesn't exist."""

    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource_type} with id '{resource_id}' not found"
        super().__init__(message, status_code=404, details=details)


class ResourceAlreadyExistsError(PlatformException):
    """Raised when trying to create a resource that already exists."""

    def __init__(self, resource_type: str, identifier: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource_type} with identifier '{identifier}' already exists"
        super().__init__(message, status_code=409, details=details)


class ResourceConflictError(PlatformException):
    """Raised when a resource operation conflicts with current state."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, details=details)


# Generation Errors
class GenerationError(PlatformException):
    """Base class for generation-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class ProviderError(GenerationError):
    """Raised when a provider (Replicate, Runway, etc.) fails."""

    def __init__(self, provider: str, message: str, details: Optional[Dict[str, Any]] = None):
        full_message = f"Provider '{provider}' error: {message}"
        super().__init__(full_message, details=details)


class TaskNotReadyError(PlatformException):
    """Raised when trying to access task results before completion."""

    def __init__(self, task_id: str, current_status: str, details: Optional[Dict[str, Any]] = None):
        message = f"Task '{task_id}' is not ready (status: {current_status})"
        super().__init__(message, status_code=202, details=details)


class TaskFailedError(GenerationError):
    """Raised when a generation task fails."""

    def __init__(self, task_id: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Task '{task_id}' failed: {reason}"
        super().__init__(message, details=details)


class TaskCanceledError(PlatformException):
    """Raised when a task has been canceled."""

    def __init__(self, task_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Task '{task_id}' was canceled"
        super().__init__(message, status_code=410, details=details)


# Storage Errors
class StorageError(PlatformException):
    """Raised when storage operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class FileNotFoundError(StorageError):
    """Raised when a file cannot be found in storage."""

    def __init__(self, file_path: str, details: Optional[Dict[str, Any]] = None):
        message = f"File not found: {file_path}"
        super().__init__(message, details=details)


class FileUploadError(StorageError):
    """Raised when file upload fails."""
    pass


class FileTooLargeError(ValidationError):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, size: int, max_size: int, details: Optional[Dict[str, Any]] = None):
        message = f"File size ({size} bytes) exceeds maximum ({max_size} bytes)"
        super().__init__(message, details=details)


class InvalidFileTypeError(ValidationError):
    """Raised when file type is not allowed."""

    def __init__(self, file_type: str, allowed_types: list, details: Optional[Dict[str, Any]] = None):
        message = f"File type '{file_type}' not allowed. Allowed types: {', '.join(allowed_types)}"
        super().__init__(message, details=details)


# Pipeline Errors
class PipelineError(PlatformException):
    """Base class for pipeline execution errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class PipelineValidationError(PipelineError):
    """Raised when pipeline configuration is invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details=details)


class PipelineExecutionError(PipelineError):
    """Raised when pipeline execution fails."""
    pass


class CircularDependencyError(PipelineValidationError):
    """Raised when pipeline has circular dependencies."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        message = "Pipeline contains circular dependencies"
        super().__init__(message, details=details)


# Database Errors
class DatabaseError(PlatformException):
    """Raised when database operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class TransactionError(DatabaseError):
    """Raised when database transaction fails."""
    pass


# Rate Limiting
class RateLimitError(PlatformException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, status_code=429, details=details)


# External Service Errors
class ExternalServiceError(PlatformException):
    """Raised when external service fails."""

    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        full_message = f"External service '{service}' error: {message}"
        super().__init__(full_message, status_code=502, details=details)


# Configuration Errors
class ConfigurationError(PlatformException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details)
