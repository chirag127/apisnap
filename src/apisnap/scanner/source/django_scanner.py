"""Django scanner."""

import re
from pathlib import Path
from apisnap.schema import RouteManifest, Route, Param
from apisnap.scanner.base import BaseScanner


class DjangoScanner(BaseScanner):
    """Scanner for Django REST Framework projects."""

    def can_handle(self, path: str) -> bool:
        """Check if path is a Django project."""
        directory = Path(path)
        if not directory.is_dir():
            directory = directory.parent

        has_settings = (directory / "settings.py").exists()
        has_manage = (directory / "manage.py").exists()

        return has_settings or has_manage

    def scan(self, path: str, **kwargs) -> RouteManifest:
        """Scan for Django routes."""
        routes = []
        directory = Path(path)

        if not directory.is_dir():
            directory = directory.parent

        # Look for urls.py files
        urls_files = list(directory.rglob("urls.py"))

        for urls_file in urls_files:
            if self._should_skip(urls_file):
                continue
            try:
                content = urls_file.read_text(encoding="utf-8")
                file_routes = self._extract_routes(content)
                routes.extend(file_routes)
            except Exception:
                continue

        # Also look for views.py files with @api_view decorators
        views_files = list(directory.rglob("views.py"))

        for views_file in views_files:
            if self._should_skip(views_file):
                continue
            try:
                content = views_file.read_text(encoding="utf-8")
                file_routes = self._extract_from_views(content)
                routes.extend(file_routes)
            except Exception:
                continue

        return RouteManifest(
            routes=routes,
            framework="django",
            project_name=directory.name,
            source_mode="scanned",
            detected_at=path,
        )

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped."""
        skip_dirs = ["__pycache__", ".git", "venv", "env", ".venv"]
        for skip_dir in skip_dirs:
            if skip_dir in path.parts:
                return True
        return False

    def _extract_routes(self, content: str) -> list[Route]:
        """Extract routes from urls.py content."""
        routes = []

        # Match path() or re_path() patterns
        patterns = [
            r"path\(['\"](.+?)['\"]\s*,\s*(?:include\(.+?\)|(.+?)\))",
            r"re_path\(r['\"](.+?)['\"]\s*,\s*(?:include\(.+?\)|(.+?)\))",
        ]

        for line in content.split("\n"):
            stripped = line.strip()

            for pattern in patterns:
                match = re.match(pattern, stripped)
                if match:
                    path = match.group(1)
                    view = match.group(2) if match.lastindex >= 2 else None

                    route = Route(
                        method="GET",
                        path=path,
                        source="scanned",
                        confidence=0.85,
                    )

                    params = self._extract_params(path)
                    route.params = params
                    routes.append(route)

        return routes

    def _extract_from_views(self, content: str) -> list[Route]:
        """Extract routes from views.py content."""
        routes = []

        # Match @api_view(['GET', 'POST', ...])
        pattern = r"@api_view\(\[(.+?)\]\)\s*\ndef\s+(\w+)"

        for match in re.finditer(pattern, content):
            methods_str = match.group(1)
            view_name = match.group(2)

            # Parse methods
            methods = []
            for m in re.finditer(r"['\"](\w+)['\"]", methods_str):
                methods.append(m.group(1).upper())

            # Generate path from view name
            path = f"/{view_name}/"

            for method in methods:
                route = Route(
                    method=method,
                    path=path,
                    source="scanned",
                    confidence=0.8,
                )
                routes.append(route)

        return routes

    def _extract_params(self, path: str) -> list[Param]:
        """Extract parameters from path."""
        params = []

        # Match <slug:name> or <int:name> patterns
        param_pattern = r"<(?:\w+:)?(\w+)>"
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
