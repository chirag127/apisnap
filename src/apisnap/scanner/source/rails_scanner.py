"""Rails scanner."""

import re
from pathlib import Path
from apisnap.schema import RouteManifest, Route, Param
from apisnap.scanner.base import BaseScanner


class RailsScanner(BaseScanner):
    """Scanner for Ruby on Rails projects."""

    def can_handle(self, path: str) -> bool:
        """Check if path is a Rails project."""
        directory = Path(path)
        if not directory.is_dir():
            directory = directory.parent

        has_routes = (directory / "config" / "routes.rb").exists()
        has_gemfile = (directory / "Gemfile").exists()

        return has_routes or has_gemfile

    def scan(self, path: str, **kwargs) -> RouteManifest:
        """Scan for Rails routes."""
        routes = []
        directory = Path(path)

        if not directory.is_dir():
            directory = directory.parent

        # Look for config/routes.rb
        routes_file = directory / "config" / "routes.rb"

        if routes_file.exists():
            try:
                content = routes_file.read_text(encoding="utf-8")
                routes = self._extract_routes(content)
            except Exception:
                routes = []

        return RouteManifest(
            routes=routes,
            framework="rails",
            project_name=directory.name,
            source_mode="scanned",
            detected_at=path,
        )

    def _extract_routes(self, content: str) -> list[Route]:
        """Extract routes from routes.rb content."""
        routes = []

        # Match resources :users, resource :session, get '/path' => 'controller#action'
        patterns = [
            (r"resources\s+:(\w+)", "resource"),
            (r"resource\s+:(\w+)", "single"),
            (r"get\s+['\"](.+?)['\"]\s*=>\s*['\"](.+?)#(.+?)['\"]", "get"),
            (r"post\s+['\"](.+?)['\"]\s*=>\s*['\"](.+?)#(.+?)['\"]", "post"),
            (r"put\s+['\"](.+?)['\"]\s*=>\s*['\"](.+?)#(.+?)['\"]", "put"),
            (r"patch\s+['\"](.+?)['\"]\s*=>\s*['\"](.+?)#(.+?)['\"]", "patch"),
            (r"delete\s+['\"](.+?)['\"]\s*=>\s*['\"](.+?)#(.+?)['\"]", "delete"),
        ]

        for line in content.split("\n"):
            stripped = line.strip()

            # Skip comments
            if stripped.startswith("#"):
                continue

            # Match resources
            for pattern, route_type in patterns:
                match = re.match(pattern, stripped)
                if match:
                    if route_type == "resource":
                        controller = match.group(1)
                        paths = [
                            ("GET", f"/{controller}"),
                            ("GET", f"/{controller}/:id"),
                            ("POST", f"/{controller}"),
                            ("GET", f"/{controller}/:id/edit"),
                            ("PUT", f"/{controller}/:id"),
                            ("PATCH", f"/{controller}/:id"),
                            ("DELETE", f"/{controller}/:id"),
                        ]
                        for method, path in paths:
                            route = Route(
                                method=method,
                                path=path,
                                source="scanned",
                                confidence=0.8,
                            )
                            routes.append(route)
                    elif route_type == "single":
                        controller = match.group(1)
                        paths = [
                            ("GET", f"/{controller}"),
                            ("POST", f"/{controller}"),
                            ("GET", f"/{controller}/edit"),
                        ]
                        for method, path in paths:
                            route = Route(
                                method=method,
                                path=path,
                                source="scanned",
                                confidence=0.8,
                            )
                            routes.append(route)
                    else:
                        path = match.group(1)
                        method = match.group(0).split()[0].upper()

                        route = Route(
                            method=method,
                            path=path,
                            source="scanned",
                            confidence=0.85,
                        )
                        routes.append(route)

        return routes
