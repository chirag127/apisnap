"""Base scanner interface."""

from abc import ABC, abstractmethod
from apisnap.schema import RouteManifest


class BaseScanner(ABC):
    """Abstract base class for scanners."""

    @abstractmethod
    def scan(self, path: str, **kwargs) -> RouteManifest:
        """Scan the given path and return a route manifest.

        Args:
            path: Path to scan (local directory or URL)
            **kwargs: Additional scanner-specific options

        Returns:
            RouteManifest with discovered routes
        """
        pass

    def can_handle(self, path: str) -> bool:
        """Check if this scanner can handle the given path.

        Args:
            path: Path to check

        Returns:
            True if this scanner can handle the path
        """
        return False
