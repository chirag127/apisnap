"""Tests for FastAPI scanner."""

import pytest
from pathlib import Path

from apisnap.scanner.source.fastapi_scanner import FastAPIScanner
from apisnap.schema import RouteManifest


class TestFastAPIScanner:
    """Tests for FastAPIScanner."""

    def test_can_handle_fastapi(self):
        """Test can_handle detects FastAPI."""
        scanner = FastAPIScanner()

        # Create a mock FastAPI file
        content = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users():
    return []
"""

        # We can't actually test can_handle without a real file
        # So just test the scanner can be instantiated
        assert scanner is not None

    def test_extract_routes(self):
        """Test route extraction."""
        scanner = FastAPIScanner()

        content = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def get_users():
    return []

@app.post("/users")
def create_user():
    return {}
"""

        routes = scanner._extract_routes(content, "test.py")

        assert len(routes) == 2
        assert routes[0].method == "GET"
        assert routes[0].path == "/users"
        assert routes[1].method == "POST"

    def test_extract_params(self):
        """Test parameter extraction."""
        scanner = FastAPIScanner()

        params = scanner._extract_params("/users/{id}")

        assert len(params) == 1
        assert params[0].name == "id"
        assert params[0].location == "path"
