"""
Base image provider interface.
"""
from abc import ABC
from backend.engines.base import BaseProvider


class BaseImageProvider(BaseProvider, ABC):
    """
    Base class for image generation providers.

    All image providers (Replicate, Stability, etc.) should inherit from this.
    """
    pass
