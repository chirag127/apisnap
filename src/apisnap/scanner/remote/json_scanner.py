"""JSON endpoint scanner."""

import json
from pathlib import Path
from typing import Optional
import httpx

from apisnap.schema import RouteManifest, Route
from apisnap.scanner.base import BaseScanner
from apisnap.scanner.schema_inferrer import SchemaInferrer


class JSONScanner(BaseScanner):
    """Scanner for raw JSON endpoints."""

    def __init__(self):
        self.http_client = httpx.Client(timeout=30.0)
        self.inferrer = SchemaInferrer()

    def can_handle(self, path: str) -> bool:
        """Check if path is a JSON URL."""
        return path.startswith(("http://", "https://"))

    def scan(self, path: str, **kwargs) -> RouteManifest:
        """Scan a JSON endpoint."""
        # Detect if it's a JSON endpoint
        is_json = self._check_if_json(path)

        if not is_json:
            return RouteManifest(
                source_mode="json",
                detected_at=path,
            )

        # Fetch the JSON
        data = self._fetch_json(path)

        if data is None:
            return RouteManifest(
                source_mode="json",
                detected_at=path,
            )

        # Infer schema
        response_schema = self.inferrer.infer(data)

        # Build route
        route = Route(
            method="GET",
            path=path,
            response_schema=response_schema,
            auth_required=False,
            source="inferred",
            confidence=0.7,
            public_url=path,
        )

        return RouteManifest(
            routes=[route],
            base_url=self._extract_base_url(path),
            framework="json",
            source_mode="json",
            detected_at=path,
        )

    def _check_if_json(self, url: str) -> bool:
        """Check if URL returns JSON."""
        try:
            response = self.http_client.head(url)
            content_type = response.headers.get("content-type", "")
            return "json" in content_type.lower()
        except Exception:
            return False

    def _fetch_json(self, url: str) -> Optional[dict]:
        """Fetch JSON from URL."""
        try:
            response = self.http_client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def _extract_base_url(self, url: str) -> str:
        """Extract base URL."""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rsplit('/', 1)[0]}"
