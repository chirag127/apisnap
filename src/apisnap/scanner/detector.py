"""Scanner detector and factory."""

import re
from pathlib import Path
from typing import Optional

from apisnap.schema import RouteManifest
from apisnap.scanner.base import BaseScanner
from apisnap.scanner.source.fastapi_scanner import FastAPIScanner
from apisnap.scanner.source.flask_scanner import FlaskScanner
from apisnap.scanner.source.django_scanner import DjangoScanner
from apisnap.scanner.source.express_scanner import ExpressScanner
from apisnap.scanner.source.spring_scanner import SpringScanner
from apisnap.scanner.source.gin_scanner import GinScanner
from apisnap.scanner.source.rails_scanner import RailsScanner
from apisnap.scanner.remote.openapi_scanner import OpenAPIScanner
from apisnap.scanner.remote.json_scanner import JSONScanner
from apisnap.scanner.remote.crawl_scanner import CrawlScanner
from apisnap.scanner.remote.github_repo_scanner import GitHubRepoScanner


# All available scanners
SCANNERS: list[type[BaseScanner]] = [
    # Remote scanners (checked first for URLs)
    GitHubRepoScanner,
    OpenAPIScanner,
    JSONScanner,
    CrawlScanner,
    # Local source scanners
    FastAPIScanner,
    FlaskScanner,
    DjangoScanner,
    ExpressScanner,
    SpringScanner,
    GinScanner,
    RailsScanner,
]


def detect_scanner(
    path: str, force_mode: Optional[str] = None
) -> Optional[BaseScanner]:
    """Detect which scanner to use for a given path.

    Args:
        path: Path to scan (directory or URL)
        force_mode: Force a specific discovery mode

    Returns:
        Appropriate scanner instance or None
    """
    if force_mode:
        return _get_scanner_by_mode(force_mode)

    # Check if it's a URL
    if _is_url(path):
        return _detect_url_scanner(path)

    # Check if it's a local directory
    return _detect_local_scanner(path)


def _is_url(path: str) -> bool:
    """Check if path is a URL."""
    return path.startswith(("http://", "https://", "github.com"))


def _detect_url_scanner(url: str) -> Optional[BaseScanner]:
    """Detect scanner for a URL."""
    # Check for GitHub repo URL
    if "github.com" in url or "github.com" in url:
        return GitHubRepoScanner()

    # Check for OpenAPI/JSON endpoints
    if "openapi" in url.lower() or "swagger" in url.lower():
        return OpenAPIScanner()

    # Try to detect from content-type header
    # This is done at scan time

    # Default to crawl scanner
    return CrawlScanner()


def _detect_local_scanner(path: str) -> Optional[BaseScanner]:
    """Detect scanner for a local directory."""
    directory = Path(path)
    if not directory.is_dir():
        directory = directory.parent

    # Check for FastAPI
    if _has_fastapi_files(directory):
        return FastAPIScanner()

    # Check for Flask
    if _has_flask_files(directory):
        return FlaskScanner()

    # Check for Django
    if _has_django_files(directory):
        return DjangoScanner()

    # Check for Express
    if _has_express_files(directory):
        return ExpressScanner()

    # Check for Spring Boot
    if _has_spring_files(directory):
        return SpringScanner()

    # Check for Gin
    if _has_gin_files(directory):
        return GinScanner()

    # Check for Rails
    if _has_rails_files(directory):
        return RailsScanner()

    return None


def _has_fastapi_files(directory: Path) -> bool:
    """Check for FastAPI project files."""
    patterns = ["main.py", "app.py", "application.py"]
    for pattern in patterns:
        if (directory / pattern).exists():
            content = (directory / pattern).read_text()
            if (
                "fastapi" in content.lower()
                or "@app.get" in content
                or "@router." in content
            ):
                return True
    return False


def _has_flask_files(directory: Path) -> bool:
    """Check for Flask project files."""
    patterns = ["main.py", "app.py", "application.py"]
    for pattern in patterns:
        if (directory / pattern).exists():
            content = (directory / pattern).read_text()
            if "from flask import" in content or "Flask(" in content:
                return True
    return False


def _has_django_files(directory: Path) -> bool:
    """Check for Django project files."""
    return (directory / "settings.py").exists() or (directory / "manage.py").exists()


def _has_express_files(directory: Path) -> bool:
    """Check for Express project files."""
    if (directory / "package.json").exists():
        content = (directory / "package.json").read_text()
        if "express" in content:
            return True
    return False


def _has_spring_files(directory: Path) -> bool:
    """Check for Spring Boot project files."""
    patterns = ["pom.xml", "build.gradle"]
    for pattern in patterns:
        if (directory / pattern).exists():
            return True
    java_files = list(directory.rglob("*.java"))
    for java_file in java_files[:5]:
        content = java_file.read_text()
        if "@RestController" in content or "@GetMapping" in content:
            return True
    return False


def _has_gin_files(directory: Path) -> bool:
    """Check for Gin project files."""
    go_files = list(directory.rglob("*.go"))
    for go_file in go_files[:5]:
        content = go_file.read_text()
        if "gin := gin.New()" in content or "r.GET(" in content or "r.POST(" in content:
            return True
    return False


def _has_rails_files(directory: Path) -> bool:
    """Check for Rails project files."""
    return (directory / "config" / "routes.rb").exists() or (
        directory / "Gemfile"
    ).exists()


def _get_scanner_by_mode(mode: str) -> Optional[BaseScanner]:
    """Get scanner by mode name."""
    mode_map = {
        "source": FastAPIScanner,
        "openapi": OpenAPIScanner,
        "json": JSONScanner,
        "crawl": CrawlScanner,
        "github": GitHubRepoScanner,
        "fastapi": FastAPIScanner,
        "flask": FlaskScanner,
        "django": DjangoScanner,
        "express": ExpressScanner,
        "spring": SpringScanner,
        "gin": GinScanner,
        "rails": RailsScanner,
    }
    scanner_class = mode_map.get(mode.lower())
    if scanner_class:
        return scanner_class()
    return None


def detect_and_scan(path: str, **kwargs) -> RouteManifest:
    """Detect scanner and scan the path.

    Args:
        path: Path to scan (directory or URL)
        **kwargs: Additional options

    Returns:
        RouteManifest with discovered routes
    """
    scanner = detect_scanner(path, kwargs.get("mode"))
    if scanner:
        return scanner.scan(path, **kwargs)

    # Fallback: try each scanner
    for scanner_class in SCANNERS:
        scanner = scanner_class()
        try:
            if scanner.can_handle(path):
                return scanner.scan(path, **kwargs)
        except Exception:
            continue

    # Return empty manifest
    return RouteManifest(source_mode="unknown", detected_at=path)
