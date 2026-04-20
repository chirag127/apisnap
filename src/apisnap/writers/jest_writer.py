"""Jest writer."""

import os
from pathlib import Path
import json

from apisnap.schema import RouteManifest, Route
from apisnap.writers.base_writer import BaseWriter


class JestWriter(BaseWriter):
    """Writer for Jest format."""

    def write(self, manifest: RouteManifest, output_dir: str) -> dict:
        """Write tests to files."""
        results = {}

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write tests for each route
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

        code = f'''/** @{{jest}} */
const axios = require("axios");

describe("{route.path}", () => {{
  const BASE_URL = "{base_url}";
  const url = `${{BASE_URL}}{route.path}`;

  test("happy path - valid request, assert 200", async () => {{
    const response = await axios.{route.method.lower()}(url);
    expect([200, 201]).toContain(response.status);
    expect(response.headers["content-type"]).toMatch(/application\\/json/);
  }});

  test("schema field presence validation", async () => {{
    const response = await axios.{route.method.lower()}(url);
    if (response.status === 200) {{
      const data = response.data;
      const expectedFields = {json.dumps(list(route.response_schema.get("properties", {{}}).keys()))};
      expectedFields.forEach(field => {{
        expect(data).toHaveProperty(field);
      }});
    }}
  }});

  test("field type validation", async () => {{
    const response = await axios.{route.method.lower()}(url);
    if (response.status === 200) {{
      const data = response.data;
      const properties = {json.dumps(route.response_schema.get("properties", {{}}))};
      Object.entries(properties).forEach(([field, schema]) => {{
        if (data[field] !== undefined) {{
          const expectedType = schema.type;
          if (expectedType === "integer") {{
            expect(typeof data[field]).toBe("number");
          }} else if (expectedType === "string") {{
            expect(typeof data[field]).toBe("string");
          }} else if (expectedType === "boolean") {{
            expect(typeof data[field]).toBe("boolean");
          }} else if (expectedType === "array") {{
            expect(Array.isArray(data[field])).toBe(true);
          }} else if (expectedType === "object") {{
            expect(typeof data[field]).toBe("object");
          }}
        }}
      }});
    }}
  }});

  test("empty/null response check", async () => {{
    const response = await axios.{route.method.lower()}(url);
    if (response.status === 200) {{
      expect(response.data).not.toBeNull();
      expect(response.data).not.toEqual({{}});
    }}
  }});

  test("content-type header check", async () => {{
    const response = await axios.{route.method.lower()}(url);
    if (response.status === 200) {{
      expect(response.headers["content-type"]).toMatch(/application\\/json/);
    }}
  }});

  test("cors headers check", async () => {{
    const response = await axios.{route.method.lower()}(url);
    // CORS headers are optional
  }});

  test("404 for invalid variation", async () => {{
    try {{
      await axios.{route.method.lower()}(`${{url}}_invalid`);
    }} catch (error) {{
      expect([400, 404]).toContain(error.response?.status);
    }}
  }});
}});
'''
        return code

    def _get_filename(self, route: Route, index: int) -> str:
        """Get filename for a route."""
        name = route.path.strip("/").replace("/", "-").replace(":", "-")
        if not name:
            name = f"route-{index}"
        return f"test-{name}.test.js"


def list(lst):
    """Helper to convert dict_keys to list."""
    return list(lst)
