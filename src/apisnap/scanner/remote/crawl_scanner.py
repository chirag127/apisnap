"""Crawl scanner for deployed URLs."""

import re
from pathlib import Path
import httpx

from apisnap.schema import RouteManifest, Route
from apisnap.scanner.base import BaseScanner


# Common API paths to probe
COMMON_PATHS = [
    "/openapi.json",
    "/swagger.json",
    "/api-docs",
    "/api/v1/openapi.json",
    "/_routes",
    "/docs/openapi.yaml",
    "/api/swagger.json",
    "/api/openapi",
    "/api/v1/users",
    "/api/v1/products",
    "/api/v1/orders",
    "/api/auth/login",
    "/api/me",
    "/health",
    "/status",
    "/api/health",
    "/api/status",
    "/users",
    "/products",
    "/orders",
    "/auth",
    "/login",
    "/account",
    "/profile",
    "/data",
    "/v1/data",
    "/api/data",
    "/feed",
    "/posts",
    "/articles",
    "/news",
    "/items",
    "/resources",
]


class CrawlScanner(BaseScanner):
    """Scanner for deployed web apps."""

    def __init__(self):
        self.http_client = httpx.Client(timeout=30.0)

    def can_handle(self, path: str) -> bool:
        """Check if path is a deployed URL."""
        return path.startswith(("http://", "https://"))

    def scan(self, path: str, **kwargs) -> RouteManifest:
        """Scan a deployed URL."""
        base_url = path.rstrip("/")

        # Try to find OpenAPI spec
        spec = self._try_find_spec(base_url)

        if spec:
            from apisnap.scanner.remote.openapi_scanner import OpenAPIScanner

            scanner = OpenAPIScanner()
            return scanner.scan(spec)

        # Probe common paths
        routes = self._probe_common_paths(base_url)

        return RouteManifest(
            routes=routes,
            base_url=base_url,
            source_mode="crawled",
            detected_at=path,
        )

    def _try_find_spec(self, base_url: str) -> str:
        """Try to find OpenAPI spec."""
        candidates = [
            f"{base_url}/openapi.json",
            f"{base_url}/swagger.json",
            f"{base_url}/api-docs",
            f"{base_url}/api/v1/openapi.json",
            f"{base_url}/docs/openapi.yaml",
        ]

        for url in candidates:
            try:
                response = self.http_client.head(url)
                if response.status_code == 200:
                    return url
            except Exception:
                continue

        return ""

    def _probe_common_paths(self, base_url: str) -> list[Route]:
        """Probe common API paths."""
        routes = []
        probed_paths = set()

        # Probe common paths
        for path in COMMON_PATHS:
            url = f"{base_url}{path}"
            try:
                response = self.http_client.head(url)
                if response.status_code in [
                    200,
                    405,
                ]:  # 405 means method not allowed, but endpoint exists
                    # Get actual method
                    methods = self._probe_methods(url)
                    for method in methods:
                        if path not in probed_paths:
                            probed_paths.add(path)
                            route = Route(
                                method=method,
                                path=path,
                                auth_required=False,
                                source="crawled",
                                confidence=0.6,
                            )
                            routes.append(route)
            except Exception:
                continue

        return routes

    def _probe_methods(self, url: str) -> list[str]:
        """Probe allowed HTTP methods."""
        methods = []

        for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            try:
                response = self.http_client.request(method, url)
                if response.status_code != 405:
                    methods.append(method)
            except Exception:
                continue

        if not methods:
            methods = ["GET"]  # Default

        return methods
