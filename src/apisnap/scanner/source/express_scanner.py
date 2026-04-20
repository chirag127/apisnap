"""Express scanner."""

import re
from pathlib import Path
from apisnap.schema import RouteManifest, Route, Param
from apisnap.scanner.base import BaseScanner


METHODS = ["get", "post", "put", "delete", "patch", "options", "head"]


class ExpressScanner(BaseScanner):
    """Scanner for Express.js projects."""

    def can_handle(self, path: str) -> bool:
        """Check if path is an Express project."""
        directory = Path(path)
        if not directory.is_dir():
            directory = directory.parent

        if (directory / "package.json").exists():
            try:
                content = (directory / "package.json").read_text(encoding="utf-8")
                if "express" in content:
                    return True
            except Exception:
                pass
        return False

    def scan(self, path: str, **kwargs) -> RouteManifest:
        """Scan for Express routes."""
        routes = []
        directory = Path(path)

        if not directory.is_dir():
            directory = directory.parent

        # Find JavaScript/TypeScript files to scan
        js_files = list(directory.rglob("*.js")) + list(directory.rglob("*.ts"))

        for js_file in js_files:
            if self._should_skip(js_file):
                continue
            try:
                content = js_file.read_text(encoding="utf-8")
                file_routes = self._extract_routes(content, str(js_file))
                routes.extend(file_routes)
            except Exception:
                continue

        return RouteManifest(
            routes=routes,
            framework="express",
            project_name=directory.name,
            source_mode="scanned",
            detected_at=path,
        )

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped."""
        skip_dirs = ["node_modules", ".git", "dist", "build"]
        for skip_dir in skip_dirs:
            if skip_dir in path.parts:
                return True
        return False

    def _extract_routes(self, content: str, filename: str) -> list[Route]:
        """Extract routes from file content."""
        routes = []

        for method in METHODS:
            # Match app.method(path, handler) or router.method(path, handler)
            pattern = rf"(?:app|router)\.{method}\(['\"](.+?)['\"])"

            for match in re.finditer(pattern, content, re.IGNORECASE):
                path = match.group(1)
                route = Route(
                    method=method.upper(),
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
