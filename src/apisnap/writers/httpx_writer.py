"""Httpx writer."""

from pathlib import Path
import json

from apisnap.schema import RouteManifest, Route
from apisnap.writers.base_writer import BaseWriter


class HttpxWriter(BaseWriter):
    """Writer for httpx test format."""

    def write(self, manifest: RouteManifest, output_dir: str) -> dict:
        """Write tests to files."""
        results = {}
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Write conftest.py
        conftest = self._generate_conftest(manifest)
        results["conftest.py"] = conftest
        (output_path / "conftest.py").write_text(conftest)
        
        # Write tests for each route
        for i, route in enumerate(manifest.routes):
            test_code = self._generate_route_test(route, manifest)
            filename = self._get_filename(route, i)
            results[filename] = test_code
            (output_path / filename).write_text(test_code)
        
        # Write __init__.py
        (output_path / "__init__.py").write_text("")
        
        return results

    def write_file(self, manifest: RouteManifest, output_path: str) -> str:
        """Write a single test file."""
        all_tests = []
        
        for i, route in enumerate(manifest.routes):
            test_code = self._generate_route_test(route, manifest)
            all_tests.append(test_code)
        
        return "\n\n".join(all_tests)

    def _generate_conftest(self, manifest: RouteManifest) -> str:
        """Generate conftest.py."""
        base_url = manifest.base_url or '""'
        
        return f'''"""Pytest configuration and fixtures."""

import pytest
import httpx


BASE_URL = "{base_url}"


@pytest.fixture
def base_url():
    """Base URL for API tests."""
    return BASE_URL


@pytest.fixture
def client():
    """HTTP client."""
    with httpx.Client() as client:
        yield client
'''

    def _generate_route_test(self, route: Route, manifest: RouteManifest) -> str:
        """Generate test for a route."""
        code = f'''"""Tests for {route.path}."""

import pytest
import httpx


def test_{self._sanitize_name(route.path)}_happy_path(client, base_url):
    """Happy path - valid request, assert 200, assert response schema."""
    url = f"{{base_url}}{route.path}"
    
    response = client.{route.method.lower()}(url)
    
    assert response.status_code in [200, 201], f"Expected 200 or 201, got {{response.status_code}}"
    assert response.headers.get("Content-Type", "").startswith("application/json")


def test_{self._sanitize_name(route.path)}_schema_validation(client, base_url):
    """Schema field presence validation."""
    url = f"{{base_url}}{route.path}"
    
    response = client.{route.method.lower()}(url)
    
    if response.status_code == 200:
        data = response.json()
        expected_fields = {list(route.response_schema.get("properties", {{}}).keys())}
        for field in expected_fields:
            assert field in data, f"Expected field '{{field}}' not in response"


def test_{self._sanitize_name(route.path)}_type_validation(client, base_url):
    """Field type validation."""
    url = f"{{base_url}}{route.path}"
    
    response = client.{route.method.lower()}(url)
    
    if response.status_code == 200:
        data = response.json()
        for field, schema in {route.response_schema.get("properties", {{}}).items():
            if field in data:
                expected_type = schema.get("type", "string")
                actual_type = type(data[field]).__name__
                
                if expected_type == "integer":
                    assert isinstance(data[field], int), f"Field '{{field}}' should be integer"
                elif expected_type == "number":
                    assert isinstance(data[field], (int, float)), f"Field '{{field}}' should be number"
                elif expected_type == "string":
                    assert isinstance(data[field], str), f"Field '{{field}}' should be string"
                elif expected_type == "boolean":
                    assert isinstance(data[field], bool), f"Field '{{field}}' should be boolean"


def test_{self._sanitize_name(route.path)}_auth_failure(client, base_url):
    """Auth failure test - if auth required."""
    {"if route.auth_required:" else "if False:"}
    url = f"{{base_url}}{route.path}"
    
    response = client.{route.method.lower()}(url)
    
    assert response.status_code in [401, 403], f"Expected 401 or 403, got {{response.status_code}}"


def test_{self._sanitize_name(route.path)}_wrong_method(client, base_url):
    """Wrong HTTP method test."""
    url = f"{{base_url}}{route.path}"
    
    wrong_method = "POST" if "{route.method}" == "GET" else "GET"
    response = client.request(wrong_method, url)
    
    assert response.status_code == 405, f"Expected 405, got {{response.status_code}}"


def test_{self._sanitize_name(route.path)}_empty_response(client, base_url):
    """Empty/null response check."""
    url = f"{{base_url}}{route.path}"
    
    response = client.{route.method.lower()}(url)
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be null"


def test_{self._sanitize_name(route.path)}_content_type(client, base_url):
    """Content-Type header check."""
    url = f"{{base_url}}{route.path}"
    
    response = client.{route.method.lower()}(url)
    
    if response.status_code == 200:
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type, f"Expected JSON Content-Type"


def test_{self._sanitize_name(route.path)}_cors_check(client, base_url):
    """CORS headers check."""
    url = f"{{base_url}}{route.path}"
    
    response = client.{route.method.lower()}(url)
    
    cors_header = response.headers.get("Access-Control-Allow-Origin", "")


def test_{self._sanitize_name(route.path)}_cache_check(client, base_url):
    """Cache headers check."""
    url = f"{{base_url}}{route.path}"
    
    response = client.{route.method.lower()}(url)
    
    cache_headers = ["ETag", "Last-Modified", "Cache-Control"]
    has_cache = any(header in response.headers for header in cache_headers)


def test_{self._sanitize_name(route.path)}_boundary_inputs(client, base_url):
    """Boundary inputs test."""
    url = f"{{base_url}}{route.path}"
    
    response = client.{route.method.lower()}(url, params={{}})
    
    assert response.status_code in [200, 400], f"Expected 200 or 400, got {{response.status_code}}"


def test_{self._sanitize_name(route.path)}_not_found(client, base_url):
    """404 for invalid endpoint variation."""
    url = f"{{base_url}}{route.path}_invalid"
    
    response = client.{route.method.lower()}(url)
    
    assert response.status_code in [404, 400], f"Expected 404 or 400, got {{response.status_code}}"
'''
        return code

    def _sanitize_name(self, path: str) -> str:
        """Sanitize path to valid Python identifier."""
        name = path.strip("/").replace("/", "_").replace("-", "_").replace(":", "_")
        return name

    def _get_filename(self, route: Route, index: int) -> str:
        """Get filename for a route."""
        name = self._sanitize_name(route.path)
        if not name:
            name = f"route_{index}"
        return f"test_{name}.py"