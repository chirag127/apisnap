"""RestAssured writer."""

from pathlib import Path

from apisnap.schema import RouteManifest, Route
from apisnap.writers.base_writer import BaseWriter


class RestAssuredWriter(BaseWriter):
    """Writer for RestAssured (Java) format."""

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

        code = f'''package com.example.api.tests;

import io.restassured.RestAssured;
import io.restassured.response.Response;
import org.testng.annotations.Test;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

public class {self._class_name(route.path)} {{

    static {{
        RestAssured.baseURI = "{base_url}";
    }}

    @Test
    public void testHappyPath() {{
        given()
            .contentType("application/json")
        .when()
            .{route.method.lower()}({repr(route.path)})
        .then()
            .statusCode(anyOf(is(200), is(201)))
            .contentType(containsString("application/json"));
    }}

    @Test
    public void testSchemaValidation() {{
        Response response = given()
            .contentType("application/json")
        .when()
            .{route.method.lower()}({repr(route.path)});
        
        if (response.getStatusCode() == 200) {{
            // Schema validation
            response.then().body("$", notNullValue());
        }}
    }}

    @Test
    public void testEmptyResponse() {{
        given()
            .contentType("application/json")
        .when()
            .{route.method.lower()}({repr(route.path)})
        .then()
            .body(notNullValue());
    }}

    @Test
    public void testContentType() {{
        given()
            .contentType("application/json")
        .when()
            .{route.method.lower()}({repr(route.path)})
        .then()
            .contentType(containsString("application/json"));
    }}

    @Test
    public void testNotFound() {{
        given()
            .contentType("application/json")
        .when()
            .{route.method.lower()}({repr(route.path + "_invalid")})
        .then()
            .statusCode(anyOf(is(404), is(400)));
    }}
}}
'''
        return code

    def _class_name(self, path: str) -> str:
        """Convert path to class name."""
        name = path.strip("/").replace("/", "_").replace("-", "_").title()
        return name or "RouteTest"

    def _get_filename(self, route: Route, index: int) -> str:
        """Get filename for a route."""
        name = self._class_name(route.path)
        if not name:
            name = f"RouteTest{index}"
        return f"{name}.java"
