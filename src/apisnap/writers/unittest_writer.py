"""Unittest writer."""

from pathlib import Path

from apisnap.schema import RouteManifest, Route
from apisnap.writers.base_writer import BaseWriter


class UnittestWriter(BaseWriter):
    """Writer for unittest format."""

    def write(self, manifest: RouteManifest, output_dir: str) -> dict:
        """Write tests to files."""
        results = {}

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

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

    def _generate_route_test(self, route: Route, manifest: RouteManifest) -> str:
        """Generate test for a route."""
        base_url = manifest.base_url or "http://localhost"
        class_name = self._class_name(route.path)
        props = list(route.response_schema.get("properties", {}).keys())
        props_items = list(route.response_schema.get("properties", {}).items())

        code = (
            '''"""Tests for '''
            + route.path
            + '''."""

import unittest
import requests


class Test'''
            + class_name
            + '''(unittest.TestCase):
    """Tests for '''
            + route.path
            + '''"""
    
    BASE_URL = "'''
            + base_url
            + '''"
    
    def setUp(self):
        """Set up test."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_happy_path(self):
        """Happy path - valid request, assert 200."""
        url = "{0}{1}".format(self.BASE_URL, "'''
            + route.path
            + """")
        response = self.session."""
            + route.method.lower()
            + '''(url)
        self.assertIn(response.status_code, [200, 201])
    
    def test_schema_validation(self):
        """Schema field presence validation."""
        url = "{0}{1}".format(self.BASE_URL, "'''
            + route.path
            + """")
        response = self.session."""
            + route.method.lower()
            + """(url)
        if response.status_code == 200:
            data = response.json()
            expected_fields = """
            + str(props)
            + '''
            for field in expected_fields:
                self.assertIn(field, data)
    
    def test_type_validation(self):
        """Field type validation."""
        url = "{0}{1}".format(self.BASE_URL, "'''
            + route.path
            + """")
        response = self.session."""
            + route.method.lower()
            + """(url)
        if response.status_code == 200:
            data = response.json()
            for field, schema in """
            + str(props_items)
            + ''':
                if field in data:
                    expected_type = schema.get("type", "string")
                    if expected_type == "integer":
                        self.assertIsInstance(data[field], int)
                    elif expected_type == "string":
                        self.assertIsInstance(data[field], str)
    
    def test_empty_response(self):
        """Empty/null response check."""
        url = "{0}{1}".format(self.BASE_URL, "'''
            + route.path
            + """")
        response = self.session."""
            + route.method.lower()
            + '''(url)
        if response.status_code == 200:
            data = response.json()
            self.assertIsNotNone(data)
    
    def test_content_type(self):
        """Content-Type header check."""
        url = "{0}{1}".format(self.BASE_URL, "'''
            + route.path
            + """")
        response = self.session."""
            + route.method.lower()
            + """(url)
        if response.status_code == 200:
            self.assertIn("application/json", response.headers.get("Content-Type", ""))


if __name__ == "__main__":
    unittest.main()
"""
        )
        return code

    def _class_name(self, path: str) -> str:
        """Convert path to class name."""
        name = path.strip("/").replace("/", "_").replace("-", "_").title()
        return name or "Route"

    def _get_filename(self, route: Route, index: int) -> str:
        """Get filename for a route."""
        name = self._class_name(route.path)
        if not name:
            name = "Route{0}".format(index)
        return "test_{0}.py".format(name.lower())
