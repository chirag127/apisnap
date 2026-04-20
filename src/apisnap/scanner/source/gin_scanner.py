"""Gin scanner."""

import re
from pathlib import Path
from apisnap.schema import RouteManifest, Route, Param
from apisnap.scanner.base import BaseScanner


METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]


class GinScanner(BaseScanner):
    """Scanner for Gin (Go) projects."""

    def can_handle(self, path: str) -> bool:
        """Check if path is a Gin project."""
        directory = Path(path)
        if not directory.is_dir():
            directory = directory.parent

        go_files = list(directory.rglob("*.go"))

        for go_file in go_files[:5]:
            try:
                content = go_file.read_text(encoding="utf-8")
                if (
                    "gin := gin.New()" in content
                    or "r.GET(" in content
                    or "r.POST(" in content
                ):
                    return True
            except Exception:
                continue

        return False

    def scan(self, path: str, **kwargs) -> RouteManifest:
        """Scan for Gin routes."""
        routes = []
        directory = Path(path)

        if not directory.is_dir():
            directory = directory.parent

        # Find Go files to scan
        go_files = list(directory.rglob("*.go"))

        for go_file in go_files:
            if self._should_skip(go_file):
                continue
            try:
                content = go_file.read_text(encoding="utf-8")
                file_routes = self._extract_routes(content, str(go_file))
                routes.extend(file_routes)
            except Exception:
                continue

        return RouteManifest(
            routes=routes,
            framework="gin",
            project_name=directory.name,
            source_mode="scanned",
            detected_at=path,
        )

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped."""
        skip_dirs = [".git", "vendor"]
        for skip_dir in skip_dirs:
            if skip_dir in path.parts:
                return True
        return False

    def _extract_routes(self, content: str, filename: str) -> list[Route]:
        """Extract routes from Go content."""
        routes = []

        for method in METHODS:
            # Match r.GET("/path", handler) patterns
            pattern = rf'r\.{method}\((["\'])(.+?)\1'

            for match in re.finditer(pattern, content):
                path = match.group(2)
                route = Route(
                    method=method,
                    path=path,
                    source="scanned",
                    confidence=0.9,
                )

                # Extract path parameters
                params = self._extract_params(path)
                route.params = params
                routes.append(route)

        return routes

    def _extract_params(self, path: str) -> list[Param]:
        """Extract parameters from path."""
        params = []

        # Match :param patterns
        param_pattern = r":(\w+)"
        for match in re.finditer(param_pattern, path):
            param_name = match.group(1)
            params.append(
                Param(
                    name=param_name,
                    location="path",
                    type="string",
                    required=True,
                )
            )

        return params
