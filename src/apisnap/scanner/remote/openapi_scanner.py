"""OpenAPI scanner."""

import json
import re
from pathlib import Path
from typing import Optional
import httpx

from apisnap.schema import RouteManifest, Route, Param
from apisnap.scanner.base import BaseScanner


class OpenAPIScanner(BaseScanner):
    """Scanner for OpenAPI/Swagger specs."""

    def __init__(self):
        self.http_client = httpx.Client(timeout=30.0)

    def can_handle(self, path: str) -> bool:
        """Check if path is an OpenAPI URL."""
        url_lower = path.lower()
        return (
            "openapi" in url_lower
            or "swagger" in url_lower
            or url_lower.endswith((".json", ".yaml", ".yml"))
        )

    def scan(self, path: str, **kwargs) -> RouteManifest:
        """Scan an OpenAPI specification."""
        # Fetch the spec
        spec = self._fetch_spec(path)

        if not spec:
            return RouteManifest(
                source_mode="openapi",
                detected_at=path,
            )

        # Determine version
        version = self._detect_version(spec)

        # Extract base URL
        base_url = self._extract_base_url(spec, version)

        # Extract paths
        paths = spec.get("paths", {})

        routes = []
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in [
                    "GET",
                    "POST",
                    "PUT",
                    "DELETE",
                    "PATCH",
                    "OPTIONS",
                    "HEAD",
                ]:
                    route = self._extract_route(
                        path,
                        method.upper(),
                        details,
                        base_url,
                    )
                    routes.append(route)

        return RouteManifest(
            routes=routes,
            base_url=base_url,
            framework="openapi",
            project_name=spec.get("info", {}).get("title"),
            source_mode="openapi",
            detected_at=path,
        )

    def _fetch_spec(self, url: str) -> Optional[dict]:
        """Fetch OpenAPI spec from URL."""
        try:
            response = self.http_client.get(url)
            response.raise_for_status()

            # Try JSON first
            try:
                return response.json()
            except Exception:
                pass

            # Try YAML
            import yaml

            try:
                return yaml.safe_load(response.text)
            except Exception:
                pass

            return None
        except Exception:
            return None

    def _detect_version(self, spec: dict) -> str:
        """Detect OpenAPI version."""
        if "openapi" in spec:
            return spec.get("openapi", "3.0.0")[:3]
        elif "swagger" in spec:
            return "2.0"
        return "3.0"

    def _extract_base_url(self, spec: dict, version: str) -> str:
        """Extract base URL from spec."""
        if version.startswith("3"):
            servers = spec.get("servers", [])
            if servers:
                return servers[0].get("url", "")
        else:
            host = spec.get("host", "")
            if host:
                base_path = spec.get("basePath", "/")
                schemes = spec.get("schemes", ["https"])
                return f"{schemes[0]}://{host}{base_path}"

        return ""

    def _extract_route(
        self,
        path: str,
        method: str,
        details: dict,
        base_url: str,
    ) -> Route:
        """Extract route from path details."""
        # Extract parameters
        params = []
        for param in details.get("parameters", []):
            params.append(
                Param(
                    name=param.get("name", ""),
                    location=param.get("in", "query"),
                    type=param.get("schema", {}).get("type", "string"),
                    required=param.get("required", False),
                    description=param.get("description"),
                    example=str(param.get("example", "")),
                )
            )

        # Extract request body (OpenAPI 3.x)
        body_schema = {}
        if "requestBody" in details:
            content = details["requestBody"].get("content", {})
            if "application/json" in content:
                body_schema = content["application/json"].get("schema", {})

        # Extract response
        response_schema = {}
        responses = details.get("responses", {})
        if "200" in responses:
            response = responses["200"]
            content = response.get("content", {})
            if "application/json" in content:
                response_schema = content["application/json"].get("schema", {})

        # Determine if auth required
        security = details.get("security", [])
        auth_required = len(security) > 0

        auth_type = None
        if auth_required:
            # Check auth type
            if "bearerAuth" in str(security) or "Authorization" in str(security):
                auth_type = "bearer"
            elif "apiKey" in str(security):
                auth_type = "api_key"
            elif "http" in str(security):
                auth_type = "basic"

        return Route(
            method=method,
            path=path,
            params=params,
            body_schema=body_schema,
            response_schema=response_schema,
            auth_required=auth_required,
            auth_type=auth_type,
            tags=details.get("tags", []),
            summary=details.get("summary"),
            source="openapi",
            confidence=1.0,
        )
