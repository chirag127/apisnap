"""Route manifest dataclasses for apisnap."""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class Param:
    """Represents an API parameter."""

    name: str
    location: str  # "path", "query", "header", "body"
    type: str  # "string", "integer", "boolean", "object", "array"
    required: bool
    description: Optional[str] = None
    example: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "location": self.location,
            "type": self.type,
            "required": self.required,
        }
        if self.description is not None:
            result["description"] = self.description
        if self.example is not None:
            result["example"] = self.example
        return result


@dataclass
class Route:
    """Represents an API route."""

    method: str  # GET, POST, PUT, DELETE, PATCH
    path: str  # /api/v1/users/{id}
    params: list[Param] = field(default_factory=list)
    body_schema: dict = field(default_factory=dict)
    response_schema: dict = field(default_factory=dict)
    auth_required: bool = False
    auth_type: Optional[str] = None  # "bearer", "api_key", "basic", "oauth2"
    tags: list[str] = field(default_factory=list)
    summary: Optional[str] = None
    source: str = (
        "unknown"  # "openapi", "inferred", "crawled", "scanned", "github-data-repo"
    )
    confidence: float = 1.0  # 0.0 to 1.0
    refresh_schedule: Optional[str] = None  # cron expression if applicable
    public_url: Optional[str] = (
        None  # full public URL if serving via GitHub/Cloudflare Pages
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "method": self.method,
            "path": self.path,
            "params": [p.to_dict() for p in self.params],
            "body_schema": self.body_schema,
            "response_schema": self.response_schema,
            "auth_required": self.auth_required,
            "source": self.source,
            "confidence": self.confidence,
        }
        if self.auth_type is not None:
            result["auth_type"] = self.auth_type
        if self.tags:
            result["tags"] = self.tags
        if self.summary is not None:
            result["summary"] = self.summary
        if self.refresh_schedule is not None:
            result["refresh_schedule"] = self.refresh_schedule
        if self.public_url is not None:
            result["public_url"] = self.public_url
        return result


@dataclass
class RouteManifest:
    """Represents a collection of API routes."""

    routes: list[Route] = field(default_factory=list)
    base_url: Optional[str] = None
    framework: Optional[str] = None
    project_name: Optional[str] = None
    source_mode: str = "unknown"
    detected_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "routes": [r.to_dict() for r in self.routes],
            "base_url": self.base_url,
            "framework": self.framework,
            "project_name": self.project_name,
            "source_mode": self.source_mode,
            "detected_at": self.detected_at,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json

        return json.dumps(self.to_dict(), indent=2)
