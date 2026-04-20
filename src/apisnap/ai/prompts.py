"""Prompt templates for AI test generation."""

import json

from apisnap.schema import Route


def get_generate_tests_prompt(route: Route, framework: str) -> str:
    """Get prompt for test generation.

    Args:
        route: Route to generate tests for
        framework: Target test framework

    Returns:
        Formatted prompt string
    """
    # Format response schema
    response_schema_json = json.dumps(route.response_schema, indent=2)

    prompt = f"""You are an API test engineer. Generate complete, runnable test code in {framework} for the following API endpoint.

Endpoint details:
- Method: {route.method}
- Path: {route.path}
- Public URL: {route.public_url or "N/A"}
- Auth required: {route.auth_required}
- Auth type: {route.auth_type or "N/A"}
- Response schema: {response_schema_json}
- Source type: {route.source}
- Confidence: {route.confidence}
- Refresh schedule: {route.refresh_schedule or "N/A"}

Generate tests for ALL of the following categories:
1. Happy path (200 response, full schema present)
2. Schema field presence validation
3. Field type validation
4. Auth failure (if auth required)
5. Wrong HTTP method (405)
6. Empty/null response check
7. Content-Type header check
8. CORS headers check (for public APIs)
9. Cache headers check (for github-data-repo type)
10. Boundary inputs
11. 404 for invalid variation

Rules:
- Write complete, runnable code. No placeholders. No pseudocode.
- Use only standard libraries for the framework plus requests (Python) or axios (JS).
- Each test must have a clear name describing what it tests.
- Add a comment above each test explaining the category it covers.
- The tests must be immediately runnable with zero modification.
- For github-data-repo type, the base URL is the GitHub Pages or Cloudflare Pages URL.
- If confidence is below 0.8, add a comment noting that the schema was inferred and may need manual review.

Output ONLY the test code. No explanation. No markdown. No code fences."""

    return prompt


def get_refine_schema_prompt(raw_data: dict) -> str:
    """Get prompt for schema refinement.

    Args:
        raw_data: Raw JSON data

    Returns:
        Formatted prompt string
    """
    data_json = json.dumps(raw_data, indent=2)

    prompt = f"""Refine and normalize the following JSON schema. Clean up types, identify field types more precisely, and suggest what the data represents based on field names.

Return ONLY valid JSON. No explanation. No markdown.

Data:
{data_json}

Output only the refined JSON schema."""

    return prompt
