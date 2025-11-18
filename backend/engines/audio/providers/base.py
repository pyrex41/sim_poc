"""
Base provider interface for audio generation.
"""
from abc import ABC
from backend.engines.base import BaseProvider


class BaseAudioProvider(BaseProvider, ABC):
    """Abstract base class for audio generation providers."""
    pass
