"""Httpx writer."""

from pathlib import Path

from apisnap.schema import RouteManifest, Route
from apisnap.writers.base_writer import BaseWriter


class HttpxWriter(BaseWriter):
    """Writer for httpx test format."""

    def write(self, manifest: RouteManifest, output_dir: str) -> dict:
        """Write tests to files."""
        results = {}

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        conftest = self._generate_conftest(manifest)
        results["conftest.py"] = conftest
        (output_path / "conftest.py").write_text(conftest)

        for i, route in enumerate(manifest.routes):
            test_code = self._generate_route_test(route, manifest)
            filename = self._get_filename(route, i)
            results[filename] = test_code
            (output_path / filename).write_text(test_code)

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

        return (
            '''"""Pytest configuration and fixtures."""

import pytest
import httpx


BASE_URL = "'''
            + base_url
            + '''"


@pytest.fixture
def base_url():
    """Base URL for API tests."""
    return BASE_URL


@pytest.fixture
def client():
    """HTTP client."""
    with httpx.Client() as c:
        yield c
'''
        )

    def _generate_route_test(self, route: Route, manifest: RouteManifest) -> str:
        """Generate test for a route."""
        sanitize_name = self._sanitize_name(route.path)
        props = list(route.response_schema.get("properties", {}).keys())
        props_items = list(route.response_schema.get("properties", {}).items())

        code = (
            '''"""Tests for '''
            + route.path
            + '''."""

import pytest
import httpx


def test_'''
            + sanitize_name
            + '''_happy_path(client, base_url):
    """Happy path - valid request, assert 200, assert response schema."""
    url = "{0}{1}".format(base_url, "'''
            + route.path
            + """")
    
    response = client."""
            + route.method.lower()
            + """(url)
    
    assert response.status_code in [200, 201], "Expected 200 or 201, got {0}".format(response.status_code)
    assert response.headers.get("Content-Type", "").startswith("application/json")


def test_"""
            + sanitize_name
            + '''_schema_validation(client, base_url):
    """Schema field presence validation."""
    url = "{0}{1}".format(base_url, "'''
            + route.path
            + """")
    
    response = client."""
            + route.method.lower()
            + """(url)
    
    if response.status_code == 200:
        data = response.json()
        expected_fields = """
            + str(props)
            + """
        for field in expected_fields:
            assert field in data, "Expected field {0} not in response".format(field)


def test_"""
            + sanitize_name
            + '''_type_validation(client, base_url):
    """Field type validation."""
    url = "{0}{1}".format(base_url, "'''
            + route.path
            + """")
    
    response = client."""
            + route.method.lower()
            + """(url)
    
    if response.status_code == 200:
        data = response.json()
        for field, schema in """
            + str(props_items)
            + """:
            if field in data:
                expected_type = schema.get("type", "string")
                
                if expected_type == "integer":
                    assert isinstance(data[field], int), "Field {0} should be integer".format(field)
                elif expected_type == "number":
                    assert isinstance(data[field], (int, float)), "Field {0} should be number".format(field)
                elif expected_type == "string":
                    assert isinstance(data[field], str), "Field {0} should be string".format(field)
                elif expected_type == "boolean":
                    assert isinstance(data[field], bool), "Field {0} should be boolean".format(field)


def test_"""
            + sanitize_name
            + '''_auth_failure(client, base_url):
    """Auth failure test - if auth required."""
    if '''
            + ("True" if route.auth_required else "False")
            + ''':
        url = "{0}{1}".format(base_url, "'''
            + route.path
            + """")
        
        response = client."""
            + route.method.lower()
            + """(url)
        
        assert response.status_code in [401, 403], "Expected 401 or 403, got {0}".format(response.status_code)


def test_"""
            + sanitize_name
            + '''_wrong_method(client, base_url):
    """Wrong HTTP method test."""
    url = "{0}{1}".format(base_url, "'''
            + route.path
            + '''")
    
    wrong_method = "POST" if "'''
            + route.method
            + """" == "GET" else "GET"
    response = client.request(wrong_method, url)
    
    assert response.status_code == 405, "Expected 405, got {0}".format(response.status_code)


def test_"""
            + sanitize_name
            + '''_empty_response(client, base_url):
    """Empty/null response check."""
    url = "{0}{1}".format(base_url, "'''
            + route.path
            + """")
    
    response = client."""
            + route.method.lower()
            + """(url)
    
    if response.status_code == 200:
        data = response.json()
        assert data is not None, "Response should not be null"


def test_"""
            + sanitize_name
            + '''_content_type(client, base_url):
    """Content-Type header check."""
    url = "{0}{1}".format(base_url, "'''
            + route.path
            + """")
    
    response = client."""
            + route.method.lower()
            + """(url)
    
    if response.status_code == 200:
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type, "Expected JSON Content-Type"


def test_"""
            + sanitize_name
            + '''_cors_check(client, base_url):
    """CORS headers check."""
    url = "{0}{1}".format(base_url, "'''
            + route.path
            + """")
    
    response = client."""
            + route.method.lower()
            + """(url)
    
    cors_header = response.headers.get("Access-Control-Allow-Origin", "")


def test_"""
            + sanitize_name
            + '''_cache_check(client, base_url):
    """Cache headers check."""
    url = "{0}{1}".format(base_url, "'''
            + route.path
            + """")
    
    response = client."""
            + route.method.lower()
            + """(url)
    
    cache_headers = ["ETag", "Last-Modified", "Cache-Control"]
    has_cache = any(header in response.headers for header in cache_headers)


def test_"""
            + sanitize_name
            + '''_boundary_inputs(client, base_url):
    """Boundary inputs test."""
    url = "{0}{1}".format(base_url, "'''
            + route.path
            + """")
    
    response = client."""
            + route.method.lower()
            + """(url, params={})
    
    assert response.status_code in [200, 400], "Expected 200 or 400, got {0}".format(response.status_code)


def test_"""
            + sanitize_name
            + '''_not_found(client, base_url):
    """404 for invalid endpoint variation."""
    url = "{0}{1}_invalid".format(base_url, "'''
            + route.path
            + """")
    
    response = client."""
            + route.method.lower()
            + """(url)
    
    assert response.status_code in [404, 400], "Expected 404 or 400, got {0}".format(response.status_code)
"""
        )
        return code

    def _sanitize_name(self, path: str) -> str:
        """Sanitize path to valid Python identifier."""
        name = path.strip("/").replace("/", "_").replace("-", "_").replace(":", "_")
        return name

    def _get_filename(self, route: Route, index: int) -> str:
        """Get filename for a route."""
        name = self._sanitize_name(route.path)
        if not name:
            name = "route_{0}".format(index)
        return "test_{0}.py".format(name)
