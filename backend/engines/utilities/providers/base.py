"""
Base provider interface for utilities.
"""
from abc import ABC
from backend.engines.base import BaseProvider


class BaseUtilityProvider(BaseProvider, ABC):
    """Abstract base class for utility providers."""
    pass
