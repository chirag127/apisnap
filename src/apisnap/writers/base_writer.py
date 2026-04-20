"""Base writer interface."""

from abc import ABC, abstractmethod
from apisnap.schema import RouteManifest


class BaseWriter(ABC):
    """Abstract base class for test writers."""

    @abstractmethod
    def write(self, manifest: RouteManifest, output_dir: str) -> dict:
        """Write tests to files.

        Args:
            manifest: RouteManifest with routes
            output_dir: Directory to write tests to

        Returns:
            Dict mapping route path to generated test file content
        """
        pass

    @abstractmethod
    def write_file(self, manifest: RouteManifest, output_path: str) -> str:
        """Write a single test file.

        Args:
            manifest: RouteManifest with routes
            output_path: Path to write test file

        Returns:
            Generated test code
        """
        pass
