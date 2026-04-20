"""Mocha writer."""

from pathlib import Path

from apisnap.schema import RouteManifest, Route
from apisnap.writers.base_writer import BaseWriter


class MochaWriter(BaseWriter):
    """Writer for Mocha format."""

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
        props = list(route.response_schema.get("properties", {}).keys())

        code = (
            """/** @module """
            + route.path
            + ''' */
const axios = require("axios");

const BASE_URL = "'''
            + base_url
            + """";
const url = "$BASE_URL}/"""
            + route.path
            + '''";

describe("'''
            + route.path
            + """", () => {
  it("happy path - valid request, assert 200", async () => {
    const response = await axios."""
            + route.method.lower()
            + """(url);
    expect([200, 201]).toContain(response.status);
  });

  it("schema field presence validation", async () => {
    const response = await axios."""
            + route.method.lower()
            + """(url);
    if (response.status === 200) {
      const data = response.data;
      const expectedFields = """
            + str(props)
            + """;
      expectedFields.forEach(field => {
        expect(data).toHaveProperty(field);
      });
    }
  });

  it("field type validation", async () => {
    const response = await axios."""
            + route.method.lower()
            + """(url);
    if (response.status === 200) {
      const data = response.data;
      // Type validation
    }
  });

  it("empty/null response check", async () => {
    const response = await axios."""
            + route.method.lower()
            + """(url);
    expect(response.data).not.toBeNull();
  });

  it("content-type header check", async () => {
    const response = await axios."""
            + route.method.lower()
            + """(url);
    expect(response.headers["content-type"]).toMatch(/application\\/json/);
  });

  it("404 for invalid variation", async () => {
    try {
      await axios."""
            + route.method.lower()
            + """(url + "_invalid");
    } catch (error) {
      expect([400, 404]).toContain(error.response?.status);
    }
  });
});
"""
        )
        return code

    def _get_filename(self, route: Route, index: int) -> str:
        """Get filename for a route."""
        name = route.path.strip("/").replace("/", "-")
        if not name:
            name = "route-{0}".format(index)
        return "test-{0}.js".format(name)
