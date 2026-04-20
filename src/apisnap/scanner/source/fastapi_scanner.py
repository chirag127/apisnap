"""FastAPI scanner."""

import re
from pathlib import Path
from apisnap.schema import RouteManifest, Route, Param
from apisnap.scanner.base import BaseScanner


METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]


class FastAPIScanner(BaseScanner):
    """Scanner for FastAPI projects."""

    def can_handle(self, path: str) -> bool:
        """Check if path is a FastAPI project."""
        directory = Path(path)
        if not directory.is_dir():
            directory = directory.parent

        for pattern in ["main.py", "app.py", "application.py"]:
            if (directory / pattern).exists():
                try:
                    content = (directory / pattern).read_text(encoding="utf-8")
                    if (
                        "fastapi" in content.lower()
                        or "@app.get" in content
                        or "@router." in content
                    ):
                        return True
                except Exception:
                    continue
        return False

    def scan(self, path: str, **kwargs) -> RouteManifest:
        """Scan for FastAPI routes."""
        routes = []
        directory = Path(path)

        if not directory.is_dir():
            directory = directory.parent

        # Find Python files to scan
        python_files = list(directory.rglob("*.py"))

        for py_file in python_files:
            if self._should_skip(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                file_routes = self._extract_routes(content, str(py_file))
                routes.extend(file_routes)
            except Exception:
                continue

        return RouteManifest(
            routes=routes,
            framework="fastapi",
            project_name=directory.name,
            source_mode="scanned",
            detected_at=path,
        )

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped."""
        skip_dirs = ["__pycache__", ".git", "venv", "env", ".venv", "node_modules"]
        for skip_dir in skip_dirs:
            if skip_dir in path.parts:
                return True
        return False

    def _extract_routes(self, content: str, filename: str) -> list[Route]:
        """Extract routes from file content."""
        routes = []

        for line in content.split("\n"):
            stripped = line.strip()

            for method in METHODS:
                method_lower = method.lower()

                pattern = rf'@(?:app|router)\.{method_lower}\("([^"]+)"\)'
                match = re.match(pattern, stripped)
                if match:
                    path = match.group(1)
                    route = Route(
                        method=method,
                        path=path,
                        source="scanned",
                        confidence=0.9,
                    )
                    params = self._extract_params(path)
                    route.params = params
                    routes.append(route)
                    continue

                pattern = rf"@(?:\bapp\b|\brouter\b)\.{method_lower}\('([^']+)'\)"
                match = re.match(pattern, stripped)
                if match:
                    path = match.group(1)
                    route = Route(
                        method=method,
                        path=path,
                        source="scanned",
                        confidence=0.9,
                    )
                    params = self._extract_params(path)
                    route.params = params
                    routes.append(route)
                    continue

                pattern = rf'@(?:api_router|APIRouter)\.{method_lower}\("([^"]+)"\)'
                match = re.match(pattern, stripped)
                if match:
                    path = match.group(1)
                    route = Route(
                        method=method,
                        path=path,
                        source="scanned",
                        confidence=0.9,
                    )
                    params = self._extract_params(path)
                    route.params = params
                    routes.append(route)
                    continue

                pattern = rf"@(?:api_router|APIRouter)\.{method_lower}\('([^']+)'\)"
                match = re.match(pattern, stripped)
                if match:
                    path = match.group(1)
                    route = Route(
                        method=method,
                        path=path,
                        source="scanned",
                        confidence=0.9,
                    )
                    params = self._extract_params(path)
                    route.params = params
                    routes.append(route)

        return routes

    def _extract_params(self, path: str) -> list[Param]:
        """Extract parameters from path."""
        params = []

        # Match {param} or <param> patterns
        param_pattern = r"\{(\w+)\}"
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
