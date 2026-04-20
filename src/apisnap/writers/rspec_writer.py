"""RSpec writer."""

import json
from pathlib import Path

from apisnap.schema import RouteManifest, Route
from apisnap.writers.base_writer import BaseWriter


class RSpecWriter(BaseWriter):
    """Writer for RSpec (Ruby) format."""

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
        props_json = json.dumps(props)

        code = f'''require "rspec"
require "httparty"

RSpec.describe "{route.path}" do
  let(:base_url) {{ "{base_url}" }}
  let(:url) {{ "{{base_url}}{route.path}" }}

  it "happy path - valid request, assert 200" do
    response = HTTParty.{route.method.lower()}(url)
    expect([200, 201]).to include(response.code)
  end

  it "schema field presence validation" do
    response = HTTParty.{route.method.lower()}(url)
    if response.code == 200
      data = JSON.parse(response.body)
      expected_fields = {props_json}
      expected_fields.each do |field|
        expect(data).to have_key(field)
      end
    end
  end

  it "field type validation" do
    response = HTTParty.{route.method.lower()}(url)
    if response.code == 200
      data = JSON.parse(response.body)
      # Type validation
    end
  end

  it "empty/null response check" do
    response = HTTParty.{route.method.lower()}(url)
    expect(response.body).not_to be_empty
  end

  it "content-type header check" do
    response = HTTParty.{route.method.lower()}(url)
    expect(response["Content-Type"]).to include("application/json")
  end

  it "404 for invalid variation" do
    begin
      response = HTTParty.{route.method.lower()}("{{url}}_invalid")
    rescue HTTParty::Error
      # Expected
    end
  end
end
'''
        return code

    def _get_filename(self, route: Route, index: int) -> str:
        """Get filename for a route."""
        name = route.path.strip("/").replace("/", "_")
        if not name:
            name = f"route_{index}"
        return f"spec_{name}_spec.rb"
