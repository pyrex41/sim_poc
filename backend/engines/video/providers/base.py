"""
Base provider interface for video generation.
"""
from abc import ABC
from backend.engines.base import BaseProvider


class BaseVideoProvider(BaseProvider, ABC):
    """Abstract base class for video generation providers."""
    pass
