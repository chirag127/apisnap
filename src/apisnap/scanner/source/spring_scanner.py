"""Spring Boot scanner."""

import re
from pathlib import Path
from apisnap.schema import RouteManifest, Route, Param
from apisnap.scanner.base import BaseScanner


class SpringScanner(BaseScanner):
    """Scanner for Spring Boot projects."""

    def can_handle(self, path: str) -> bool:
        """Check if path is a Spring Boot project."""
        directory = Path(path)
        if not directory.is_dir():
            directory = directory.parent

        # Check for pom.xml or build.gradle
        if (directory / "pom.xml").exists() or (directory / "build.gradle").exists():
            return True

        # Check for Java files with Spring annotations
        java_files = list(directory.rglob("*.java"))
        for java_file in java_files[:5]:
            try:
                content = java_file.read_text(encoding="utf-8")
                if "@RestController" in content or "@GetMapping" in content:
                    return True
            except Exception:
                continue

        return False

    def scan(self, path: str, **kwargs) -> RouteManifest:
        """Scan for Spring Boot routes."""
        routes = []
        directory = Path(path)

        if not directory.is_dir():
            directory = directory.parent

        # Find Java files to scan
        java_files = list(directory.rglob("*.java"))

        for java_file in java_files:
            if self._should_skip(java_file):
                continue
            try:
                content = java_file.read_text(encoding="utf-8")
                file_routes = self._extract_routes(content)
                routes.extend(file_routes)
            except Exception:
                continue

        return RouteManifest(
            routes=routes,
            framework="spring",
            project_name=directory.name,
            source_mode="scanned",
            detected_at=path,
        )

    def _should_skip(self, path: Path) -> bool:
        """Check if file should be skipped."""
        skip_dirs = ["target", ".git", "node_modules"]
        for skip_dir in skip_dirs:
            if skip_dir in path.parts:
                return True
        return False

    def _extract_routes(self, content: str) -> list[Route]:
        """Extract routes from Java content."""
        routes = []

        # Match @GetMapping, @PostMapping, @PutMapping, @DeleteMapping, @PatchMapping
        patterns = [
            (r"@GetMapping\((.+?)\)", "GET"),
            (r"@PostMapping\((.+?)\)", "POST"),
            (r"@PutMapping\((.+?)\)", "PUT"),
            (r"@DeleteMapping\((.+?)\)", "DELETE"),
            (r"@PatchMapping\((.+?)\)", "PATCH"),
            (r"@RequestMapping\((.+?)\)", "GET"),
        ]

        for line in content.split("\n"):
            stripped = line.strip()

            for pattern, method in patterns:
                match = re.match(pattern, stripped)
                if match:
                    args = match.group(1)

                    # Extract path from annotation args
                    path = self._extract_path_from_args(args)

                    if path:
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

    def _extract_path_from_args(self, args: str) -> str:
        """Extract path from annotation arguments."""
        # Remove quotes and whitespace
        args = args.strip()

        # Check for value or path argument
        value_match = re.search(r'(?:value|path)\s*=\s*["\'](.+?)["\']', args)
        if value_match:
            return value_match.group(1)

        # Just path string
        if args.startswith('"') or args.startswith("'"):
            return args.strip("\"'")

        return ""

    def _extract_params(self, path: str) -> list[Param]:
        """Extract parameters from path."""
        params = []

        # Match {param} patterns
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
