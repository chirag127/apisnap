"""Tests for OpenAPI scanner."""

import pytest

from apisnap.scanner.remote.openapi_scanner import OpenAPIScanner
from apisnap.schema import RouteManifest


class TestOpenAPIScanner:
    """Tests for OpenAPIScanner."""

    def test_can_handle(self):
        """Test can_handle detects OpenAPI URLs."""
        scanner = OpenAPIScanner()

        assert scanner.can_handle("https://api.example.com/openapi.json") is True
        assert scanner.can_handle("https://api.example.com/swagger.json") is True

    def test_detect_version(self):
        """Test version detection."""
        scanner = OpenAPIScanner()

        spec_v3 = {"openapi": "3.0.0", "paths": {}}
        assert scanner._detect_version(spec_v3) == "3.0"

        spec_2 = {"swagger": "2.0", "paths": {}}
        assert scanner._detect_version(spec_2) == "2.0"

    def test_extract_base_url(self):
        """Test base URL extraction."""
        scanner = OpenAPIScanner()

        spec = {
            "openapi": "3.0.0",
            "servers": [{"url": "https://api.example.com"}],
            "paths": {},
        }

        url = scanner._extract_base_url(spec, "3.0")
        assert url == "https://api.example.com"
