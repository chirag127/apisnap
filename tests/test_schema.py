"""Tests for schema dataclasses."""

import pytest

from apisnap.schema import Param, Route, RouteManifest


class TestParam:
    """Tests for Param dataclass."""

    def test_param_creation(self):
        """Test creating a Param."""
        param = Param(
            name="id",
            location="path",
            type="integer",
            required=True,
        )

        assert param.name == "id"
        assert param.location == "path"
        assert param.type == "integer"
        assert param.required is True

    def test_param_to_dict(self):
        """Test converting Param to dict."""
        param = Param(
            name="id",
            location="path",
            type="integer",
            required=True,
            description="User ID",
        )

        d = param.to_dict()

        assert d["name"] == "id"
        assert d["location"] == "path"
        assert d["type"] == "integer"
        assert d["required"] is True
        assert d["description"] == "User ID"


class TestRoute:
    """Tests for Route dataclass."""

    def test_route_creation(self):
        """Test creating a Route."""
        route = Route(
            method="GET",
            path="/api/users",
        )

        assert route.method == "GET"
        assert route.path == "/api/users"
        assert route.auth_required is False

    def test_route_with_params(self):
        """Test Route with parameters."""
        params = [
            Param(name="id", location="path", type="integer", required=True),
        ]

        route = Route(
            method="GET",
            path="/api/users/{id}",
            params=params,
        )

        assert len(route.params) == 1
        assert route.params[0].name == "id"

    def test_route_to_dict(self):
        """Test converting Route to dict."""
        route = Route(
            method="GET",
            path="/api/users",
            source="scanned",
            confidence=0.9,
        )

        d = route.to_dict()

        assert d["method"] == "GET"
        assert d["path"] == "/api/users"
        assert d["source"] == "scanned"
        assert d["confidence"] == 0.9


class TestRouteManifest:
    """Tests for RouteManifest dataclass."""

    def test_manifest_creation(self):
        """Test creating a RouteManifest."""
        manifest = RouteManifest()

        assert manifest.routes == []
        assert manifest.source_mode == "unknown"

    def test_manifest_with_routes(self):
        """Test manifest with routes."""
        routes = [
            Route(method="GET", path="/api/users"),
            Route(method="POST", path="/api/users"),
        ]

        manifest = RouteManifest(
            routes=routes,
            framework="fastapi",
        )

        assert len(manifest.routes) == 2
        assert manifest.framework == "fastapi"

    def test_manifest_to_json(self):
        """Test converting manifest to JSON."""
        manifest = RouteManifest(
            routes=[Route(method="GET", path="/api/users")],
            framework="fastapi",
            project_name="myproject",
        )

        json_str = manifest.to_json()

        assert "myproject" in json_str
        assert "GET" in json_str
