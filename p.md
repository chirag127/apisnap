You are an expert Python developer, CLI tool architect, open-source maintainer, and technical writer. Your task is to build a complete, production-ready Python package called "apisnap" from scratch — including all source code, all documentation, all diagrams, all configuration files, and PyPI publishing setup. Do not skip any file. Do not summarize. Write every file completely.

---

## WHAT APISNAP DOES

apisnap is a CLI tool that automatically generates API test cases using AI. A developer runs it inside or pointed at any project, and it:

1. Discovers all API endpoints from the project
2. Builds a structured route manifest (method, path, params, auth, request/response shape)
3. Sends that manifest to the Cerebras AI API (model: qwen-3-235b-a22b-instruct-2507)
4. Receives fully-written test cases in the target framework
5. Writes those test cases as runnable files into a /tests folder

The AI model used is Cerebras qwen-3-235b-a22b-instruct-2507 via the Cerebras OpenAI-compatible API at https://api.cerebras.ai/v1

---

## SUPPORTED INPUT MODES

apisnap must support all of the following input modes. Each mode produces the same internal RouteManifest format before passing to the AI.

### Mode 1 — Local source code scan
Run inside a project directory. Auto-detect the framework from files present.
- Python: FastAPI (scan for @app.get, @router.post, APIRouter patterns), Flask, Django REST Framework
- Node.js / TypeScript: Express (app.get, router.post, app.use patterns), Fastify, Hapi
- Java: Spring Boot (@GetMapping, @PostMapping, @RestController annotations)
- Go: Gin (r.GET, r.POST), Echo
- Ruby: Rails (routes.rb parsing)

Command: apisnap scan
Command: apisnap scan ./src/routes

### Mode 2 — Remote OpenAPI / Swagger JSON URL
Point at any URL that returns an OpenAPI 3.x or Swagger 2.x spec.

Command: apisnap scan --url https://api.example.com/openapi.json
Command: apisnap scan --url https://api.example.com/swagger.json

### Mode 3 — Raw JSON endpoint URL
Point at any live JSON endpoint with no spec. The AI infers the schema from the response shape.

Command: apisnap scan --url https://api.example.com/api/v1/products

### Mode 4 — Deployed URL (Cloudflare Pages, GitHub Pages, Vercel, Netlify, Railway)
Point at a deployed web app URL. apisnap will:
1. Check Content-Type header
2. Probe common spec paths: /openapi.json, /swagger.json, /api-docs, /api/v1/openapi.json, /_routes, /docs/openapi.yaml
3. If no spec found, download and scan JavaScript bundles for fetch(), axios.get(), $.ajax() calls with string literal URLs
4. If still no routes found, probe a curated list of 60 common REST patterns: /api/users, /api/auth/login, /health, /api/v1/products, /api/v1/orders, /api/me, /status, etc.

Command: apisnap scan --url https://myapp.pages.dev
Command: apisnap scan --url https://myapp.pages.dev --crawl

### Mode 5 — GitHub repository URL (THE MOST IMPORTANT MODE — READ CAREFULLY)
This mode handles a very specific and important pattern: repos that use GitHub as a serverless database.

The pattern works like this:
- A GitHub Actions workflow runs on a cron schedule (e.g. every 6 hours)
- The workflow fetches data from an external upstream API (e.g. a guitar chords API, a weather API, a prices API, a sports scores API)
- The workflow commits that fetched data as .json files directly into the repository (e.g. /data/chords.json, /data/products.json)
- Those JSON files are then exposed publicly via:
  - GitHub raw URL: https://raw.githubusercontent.com/user/repo/main/data/chords.json
  - GitHub Pages URL: https://user.github.io/repo/data/chords.json
  - Cloudflare Pages URL: https://repo.pages.dev/data/chords.json (if connected)
- This creates a completely free, serverless, zero-maintenance JSON API
- The repo itself IS the API — no server, no backend, no cost

When apisnap receives a GitHub repo URL, it must:

Step 1 — Clone or fetch the repo tree via GitHub API (no auth required for public repos)
  GET https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1

Step 2 — Scan for generator scripts
  Look for files matching these patterns:
  - .github/workflows/*.yml or *.yaml — parse for: cron schedules, curl/fetch/requests calls, output file paths
  - scripts/fetch*.py, scripts/update*.py, scripts/sync*.py, fetch*.js, update*.js
  - Any Python or JS file containing: requests.get(, fetch(, axios.get(, httpx.get(
  - Extract: what URL is being fetched, what the output filename is, what transformation is applied

Step 3 — Scan for committed JSON data files
  Look for: /data/*.json, /public/*.json, /api/*.json, /dist/*.json, /output/*.json, /assets/*.json
  Fetch each JSON file and infer its schema (field names, types, nullable, nested objects, arrays)

Step 4 — Detect the public serving URL
  Check for:
  - GitHub Pages: look for gh-pages branch, or docs/ folder, or pages config in repo settings (via API)
  - Cloudflare Pages: look for wrangler.toml or .cloudflare/ directory
  - Custom domain: look for CNAME file
  Construct the public base URL for the JSON files

Step 5 — Build the RouteManifest
  For each JSON file found, create a route entry:
  - method: GET (all GitHub-as-database APIs are GET-only)
  - path: the public URL path to the JSON file
  - response_schema: inferred from the actual JSON content
  - auth_required: false (public repos = public data)
  - refresh_schedule: extracted from the cron expression in the workflow
  - source: "github-data-repo"
  - confidence: 0.95 (JSON files are the ground truth)

Step 6 — Generate tests
  Tests for this mode must validate:
  - The public URL returns 200
  - Content-Type is application/json
  - Response body matches the inferred schema (all required fields present)
  - Field types match (string is string, number is number, array is array)
  - Nested objects have their expected fields
  - Array items have consistent structure
  - CORS headers present (Access-Control-Allow-Origin)
  - Response is not empty / not null
  - Response caching headers present (Last-Modified or ETag or Cache-Control)

Command: apisnap scan --url https://github.com/username/guitar-chords-repo
Command: apisnap scan --url https://github.com/username/guitar-chords-repo --format pytest

---

## ROUTE MANIFEST INTERNAL FORMAT

Every input mode must produce this exact Python dataclass structure:

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Param:
    name: str
    location: str        # "path", "query", "header", "body"
    type: str            # "string", "integer", "boolean", "object", "array"
    required: bool
    description: Optional[str] = None
    example: Optional[str] = None

@dataclass
class Route:
    method: str                        # GET, POST, PUT, DELETE, PATCH
    path: str                          # /api/v1/users/{id}
    params: list[Param] = field(default_factory=list)
    body_schema: dict = field(default_factory=dict)
    response_schema: dict = field(default_factory=dict)
    auth_required: bool = False
    auth_type: Optional[str] = None    # "bearer", "api_key", "basic", "oauth2"
    tags: list[str] = field(default_factory=list)
    summary: Optional[str] = None
    source: str = "unknown"            # "openapi", "inferred", "crawled", "scanned", "github-data-repo"
    confidence: float = 1.0            # 0.0 to 1.0
    refresh_schedule: Optional[str] = None  # cron expression if applicable
    public_url: Optional[str] = None   # full public URL if serving via GitHub/Cloudflare Pages

@dataclass
class RouteManifest:
    routes: list[Route]
    base_url: Optional[str] = None
    framework: Optional[str] = None
    project_name: Optional[str] = None
    source_mode: str = "unknown"
    detected_at: str = ""
```

---

## AI TEST GENERATION

### Two-pass AI strategy

Pass 1 — Schema refinement (only if confidence < 0.8):
Send the raw extracted data to the AI and ask it to:
- Clean up and normalize the schema
- Identify field types more precisely
- Suggest what the endpoint does based on field names
- Flag any unusual patterns

Pass 2 — Test generation:
Send the cleaned RouteManifest to the AI and instruct it to generate tests.

### Test categories to generate per route

For every route, generate all of the following:
1. Happy path — valid request, assert 200/201, assert response schema matches
2. Schema validation — assert every expected field is present in response
3. Type validation — assert field types are correct (string, integer, boolean, array)
4. Auth test — if auth_required is true, send without token, assert 401 or 403
5. Method not allowed — try wrong HTTP method, assert 405
6. Empty response check — assert response body is not null and not empty
7. Content-Type check — assert response header Content-Type is application/json
8. CORS check — for public APIs, assert Access-Control-Allow-Origin header present
9. Caching check — for GitHub-data-repo type, assert ETag or Cache-Control or Last-Modified present
10. Boundary tests — empty query params, very long strings, special characters in params
11. Negative test — invalid endpoint variation, assert 404

### AI prompt template for Pass 2

Use this exact prompt structure when calling the Cerebras API:

```
You are an API test engineer. Generate complete, runnable test code in {framework} for the following API endpoint.

Endpoint details:
- Method: {method}
- Path: {path}
- Public URL: {public_url}
- Auth required: {auth_required}
- Auth type: {auth_type}
- Response schema: {response_schema}
- Source type: {source}
- Confidence: {confidence}
- Refresh schedule: {refresh_schedule}

Generate tests for ALL of the following categories:
1. Happy path (200 response, full schema present)
2. Schema field presence validation
3. Field type validation
4. Auth failure (if auth required)
5. Wrong HTTP method (405)
6. Empty/null response check
7. Content-Type header check
8. CORS headers check (for public APIs)
9. Cache headers check (for GitHub-data-repo type)
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

Output ONLY the test code. No explanation. No markdown. No code fences.
```

---

## OUTPUT FORMATS

Support these test frameworks via --format flag:

- pytest (default for Python projects)
- unittest (Python)
- jest (JavaScript/TypeScript)
- mocha (JavaScript)
- vitest (JavaScript/TypeScript)
- restassured (Java)
- rspec (Ruby)
- httpx_test (Python, using httpx)

---

## CLI INTERFACE

Use Typer for the CLI. Build the following commands:

### apisnap config
First-time setup. Prompts for and stores the Cerebras API key.
Stores config at: ~/.apisnap/config.toml

```
[cerebras]
api_key = "your-key-here"
model = "qwen-3-235b-a22b-instruct-2507"

[defaults]
output_dir = "./tests"
format = "pytest"
```

Also support: apisnap config --api-key sk-xxxx (non-interactive)
Also support: apisnap config --show (print current config, masking the key)

### apisnap scan
Main command. All options:

```
apisnap scan [PATH] [OPTIONS]

Arguments:
  PATH    Path to scan (default: current directory)

Options:
  --url TEXT          Remote URL to scan (GitHub repo, deployed URL, OpenAPI JSON)
  --format TEXT       Test framework output [pytest|jest|mocha|vitest|unittest|restassured|rspec]
  --output TEXT       Output directory for tests [default: ./tests]
  --framework TEXT    Force a specific framework detection [fastapi|express|django|spring|gin|rails]
  --mode TEXT         Force a discovery mode [source|openapi|json|crawl|github]
  --dry-run           Show discovered routes without generating tests
  --base-url TEXT     Base URL for generated test requests
  --verbose           Show detailed progress
  --no-ai             Only discover routes, print manifest as JSON, skip test generation
```

### apisnap list
Show all discovered routes without generating tests. Pretty-printed table.

### apisnap version
Show version.

---

## PROJECT FILE STRUCTURE

Create every single one of these files. Do not skip any.

```
apisnap/
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
├── LICENSE (MIT)
├── .github/
│   └── workflows/
│       ├── publish.yml          (PyPI publish on tag push)
│       └── test.yml             (run pytest on push/PR)
├── docs/
│   ├── diagrams/
│   │   ├── diagram_01_system_overview.md
│   │   ├── diagram_02_data_flow.md
│   │   ├── diagram_03_github_repo_pattern.md
│   │   ├── diagram_04_cli_modes.md
│   │   ├── diagram_05_ai_pipeline.md
│   │   └── diagram_06_route_manifest.md
│   └── usage.md
├── src/
│   └── apisnap/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── schema.py            (RouteManifest, Route, Param dataclasses)
│       ├── scanner/
│       │   ├── __init__.py
│       │   ├── base.py          (abstract BaseScanner)
│       │   ├── detector.py      (auto-detect which scanner to use)
│       │   ├── source/
│       │   │   ├── __init__.py
│       │   │   ├── fastapi_scanner.py
│       │   │   ├── flask_scanner.py
│       │   │   ├── django_scanner.py
│       │   │   ├── express_scanner.py
│       │   │   ├── spring_scanner.py
│       │   │   ├── gin_scanner.py
│       │   │   └── rails_scanner.py
│       │   ├── remote/
│       │   │   ├── __init__.py
│       │   │   ├── openapi_scanner.py
│       │   │   ├── json_scanner.py
│       │   │   ├── crawl_scanner.py
│       │   │   └── github_repo_scanner.py   (THE KEY FILE — handles git-as-database)
│       │   └── schema_inferrer.py           (infers schema from raw JSON)
│       ├── ai/
│       │   ├── __init__.py
│       │   ├── client.py        (Cerebras API client)
│       │   └── prompts.py       (prompt templates)
│       ├── writers/
│       │   ├── __init__.py
│       │   ├── base_writer.py
│       │   ├── pytest_writer.py
│       │   ├── unittest_writer.py
│       │   ├── jest_writer.py
│       │   ├── mocha_writer.py
│       │   ├── vitest_writer.py
│       │   ├── restassured_writer.py
│       │   ├── rspec_writer.py
│       │   └── httpx_writer.py
│       └── utils/
│           ├── __init__.py
│           ├── http.py          (shared HTTP client with retry logic)
│           └── display.py       (rich terminal output helpers)
└── tests/
    ├── __init__.py
    ├── test_schema.py
    ├── test_detector.py
    ├── test_fastapi_scanner.py
    ├── test_openapi_scanner.py
    ├── test_github_repo_scanner.py
    ├── test_schema_inferrer.py
    ├── test_ai_client.py
    └── fixtures/
        ├── sample_openapi.json
        ├── sample_github_repo_tree.json
        ├── sample_data_file.json
        └── sample_workflow.yml
```

---

## PYPROJECT.TOML — WRITE THIS EXACTLY

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "apisnap"
version = "0.1.0"
description = "AI-powered API test case generator. Point it at any codebase, URL, or GitHub repo and get instant runnable tests."
readme = "README.md"
license = { file = "LICENSE" }
requires-python = ">=3.10"
authors = [
  { name = "Your Name", email = "you@example.com" }
]
keywords = ["api", "testing", "ai", "test-generation", "openapi", "cli", "cerebras"]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Environment :: Console",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Topic :: Software Development :: Testing",
  "Topic :: Utilities",
]
dependencies = [
  "typer>=0.12.0",
  "rich>=13.0.0",
  "httpx>=0.27.0",
  "toml>=0.10.2",
  "pyyaml>=6.0",
  "openai>=1.0.0",
]

[project.scripts]
apisnap = "apisnap.__main__:app"

[project.urls]
Homepage = "https://github.com/yourusername/apisnap"
Repository = "https://github.com/yourusername/apisnap"
Issues = "https://github.com/yourusername/apisnap/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/apisnap"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

---

## README.md — WRITE THIS COMPLETELY

The README must contain all of the following sections in this order:

### Section 1 — Header
Project name, one-line description, PyPI badge, Python version badge, license badge.

### Section 2 — What is apisnap?
Clear explanation of the problem it solves and what it does. Mention the GitHub-as-database serverless API pattern specifically by name. Explain that this is increasingly common for free, zero-server APIs.

### Section 3 — Installation
```bash
# Recommended: use uvx (no install needed)
uvx apisnap scan --url https://github.com/user/repo

# Install with uv
uv add apisnap --dev

# Install with pip
pip install apisnap
```

### Section 4 — Quick start
Step by step from zero to running tests in under 60 seconds.

### Section 5 — Diagram: System overview
Full Mermaid diagram showing the high level flow.
Title: "How apisnap works — system overview"
Must show: all 5 input modes → auto-detector → route manifest → AI engine → test writers → output files

### Section 6 — Diagram: The GitHub-as-database pattern
Full Mermaid diagram showing the serverless API pattern.
Title: "The GitHub-as-database serverless API pattern"
Must show: cron trigger → upstream API fetch → JSON commit to repo → GitHub Pages / Cloudflare Pages → public URL → users

### Section 7 — Diagram: apisnap GitHub repo scanner
Full Mermaid diagram showing what apisnap does when it receives a GitHub URL.
Title: "How apisnap scans a GitHub-as-database repo"
Must show: GitHub URL → tree API fetch → generator script scan + JSON file scan → schema inference → route manifest → AI test generator

### Section 8 — Diagram: CLI modes reference
Full Mermaid diagram showing all CLI commands and their flags.
Title: "apisnap CLI modes and commands"
Must show: apisnap config, apisnap scan (local), apisnap scan --url (OpenAPI), apisnap scan --url (deployed), apisnap scan --url (github), apisnap list, apisnap version

### Section 9 — Diagram: AI test generation pipeline
Full Mermaid diagram showing the two-pass AI strategy.
Title: "AI test generation pipeline"
Must show: route manifest → confidence check → optional pass 1 schema refinement → pass 2 test generation → framework writer → test file

### Section 10 — Diagram: Route manifest structure
Full Mermaid diagram showing the RouteManifest dataclass fields.
Title: "Internal route manifest structure"
Must show: all fields of Route and RouteManifest as a box diagram

### Section 11 — Supported frameworks
Table showing all supported source code frameworks, detection method, and example file.

### Section 12 — Supported test output formats
Table showing all supported output formats (pytest, jest, etc.) and install command.

### Section 13 — GitHub-as-database repos — detailed guide
Full explanation of the pattern, how to structure such a repo, what apisnap detects, example workflow YAML.

### Section 14 — Configuration reference
Full reference for ~/.apisnap/config.toml with all options explained.

### Section 15 — Contributing
How to contribute, how to run tests locally, how to add a new scanner.

### Section 16 — Publishing to PyPI
Step by step: how to build and publish. Explain the GitHub Actions workflow.

### Section 17 — License
MIT license statement.

IMPORTANT: Every Mermaid diagram in the README must be inside a code block using triple backticks. Each diagram must be standalone — do not combine multiple diagrams into one block. Each diagram must be large enough to read clearly at a glance. Minimum width: 60 characters. Use box-drawing characters: ┌─┐└─┘│├─┤┬┴┼ for borders. Use arrows: →, ←, ↓, ↑, ↔ for flow.

---

## DOCS/ DIAGRAM FILES

For each of the 6 files in docs/diagrams/, write a standalone Markdown file containing:
- A level-1 heading with the diagram name
- A one-paragraph explanation of what the diagram shows
- The full Mermaid diagram in a code block
- A bullet list explaining each component in the diagram

---

## GITHUB ACTIONS — publish.yml

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install hatch
      - run: hatch build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

---

## GITHUB ACTIONS — test.yml

```yaml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v
```

---

## KEY IMPLEMENTATION DETAILS

### github_repo_scanner.py — implement completely

This is the most important and unique file. Implement the following logic completely:

```python
class GitHubRepoScanner(BaseScanner):

    def scan(self, url: str) -> RouteManifest:
        # 1. Parse owner/repo from URL
        # 2. Fetch repo tree from GitHub API
        # 3. Find and parse workflow YAML files — extract cron, fetch URLs, output paths
        # 4. Find and fetch JSON data files — infer schema from content
        # 5. Detect GitHub Pages URL or Cloudflare Pages URL
        # 6. Build RouteManifest with one Route per JSON file
        # 7. Return manifest

    def _parse_github_url(self, url: str) -> tuple[str, str]:
        # returns (owner, repo)

    def _fetch_repo_tree(self, owner: str, repo: str) -> list[dict]:
        # calls https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1
        # returns list of {path, type, url} for all files

    def _find_workflow_files(self, tree: list[dict]) -> list[str]:
        # returns paths matching .github/workflows/*.yml

    def _parse_workflow(self, content: str) -> dict:
        # parses YAML, extracts: cron schedule, HTTP fetch calls, output file paths

    def _find_json_data_files(self, tree: list[dict]) -> list[str]:
        # returns paths matching: data/*.json, public/*.json, api/*.json, output/*.json

    def _fetch_file_content(self, owner: str, repo: str, path: str) -> str:
        # fetches raw file content from GitHub API

    def _detect_public_url(self, owner: str, repo: str, tree: list[dict]) -> str:
        # checks for CNAME, gh-pages branch, wrangler.toml
        # returns base URL: https://owner.github.io/repo or https://custom.domain.com

    def _build_route(self, json_path: str, content: str, base_url: str, workflow_info: dict) -> Route:
        # creates Route with inferred schema, public URL, cron schedule
```

### schema_inferrer.py — implement completely

```python
class SchemaInferrer:

    def infer(self, data: any) -> dict:
        # recursively infer JSON schema from a Python object
        # handle: dict, list, str, int, float, bool, None
        # for lists: infer schema of items (merge multiple item schemas)
        # return a JSON Schema compatible dict

    def _infer_object(self, obj: dict) -> dict:
        # infer schema for a dict

    def _infer_array(self, arr: list) -> dict:
        # infer schema for a list
        # merge schemas of first 10 items

    def _infer_type(self, value: any) -> str:
        # return "string", "integer", "number", "boolean", "object", "array", "null"

    def _merge_schemas(self, schemas: list[dict]) -> dict:
        # merge multiple schemas into one (union of fields, types become anyOf if different)
```

### ai/client.py — implement completely

```python
from openai import OpenAI

class CerebraClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.cerebras.ai/v1"
        )
        self.model = "qwen-3-235b-a22b-instruct-2507"

    def generate_tests(self, route: Route, framework: str) -> str:
        # builds prompt from prompts.py
        # calls self.client.chat.completions.create
        # returns raw test code string

    def refine_schema(self, raw_data: dict) -> dict:
        # pass 1: send raw JSON to AI, get back cleaner schema
```

### config.py — implement completely

Store and load config from ~/.apisnap/config.toml. Support:
- get_api_key() → str
- set_api_key(key: str)
- get_default_format() → str
- get_default_output_dir() → str
- show_config() → prints config with masked key

### cli.py — implement completely using Typer

All commands must work. Use Rich for terminal output: progress spinners, colored output, tables for route listing, success/error messages.

---

## TESTS — write these test files completely

### tests/test_github_repo_scanner.py
Mock the GitHub API responses. Test:
- Parsing GitHub URLs to owner/repo
- Detecting JSON data files in repo tree
- Parsing workflow YAML for cron schedules
- Detecting GitHub Pages URL from CNAME file
- Building correct RouteManifest from mocked data

### tests/test_schema_inferrer.py
Test schema inference for:
- Simple flat object: {"name": "John", "age": 30}
- Nested object: {"user": {"id": 1, "email": "a@b.com"}}
- Array of objects: [{"id": 1}, {"id": 2}]
- Mixed types
- Null values
- Empty object
- Empty array

### tests/fixtures/sample_workflow.yml
A real GitHub Actions workflow file that:
- Runs on schedule: cron '0 */6 * * *'
- Uses Python to fetch from an external API
- Commits the result as data/latest.json

### tests/fixtures/sample_data_file.json
A realistic JSON file that would be committed by such a workflow (guitar chords, prices, etc.)

---

## IMPORTANT INSTRUCTIONS FOR THE AI AGENT

1. Write EVERY file completely. Do not write "# TODO" or "# implement later" or "pass" anywhere except in abstract base class methods.

2. Every scanner must actually work. Use regex for source code parsing. Use httpx for HTTP requests. Handle errors gracefully with clear error messages.

3. The github_repo_scanner.py is the centerpiece. Spend the most effort here. It must handle:
   - Repos where JSON files are in /data/
   - Repos where JSON files are in /public/
   - Repos with GitHub Pages enabled
   - Repos connected to Cloudflare Pages (detected via wrangler.toml)
   - Repos with custom domains (detected via CNAME)
   - Repos where the generator is a Python script
   - Repos where the generator is a Node.js script
   - Repos where the generator is a shell script with curl

4. The README Mermaid diagrams must be LARGE and CLEAR. Each diagram minimum 60 characters wide. Use real box-drawing characters. Each diagram in its own code block.

5. The pyproject.toml must be correct and the package must be installable via pip install apisnap and runnable via uvx apisnap after publishing to PyPI.

6. Every CLI command must show a loading spinner (use Rich's Progress or Spinner) while working.

7. Error messages must be user-friendly. If the API key is missing, tell the user to run apisnap config. If a URL is unreachable, say so clearly. If no routes found, give suggestions.

8. The --dry-run flag must print a Rich table with columns: Method, Path, Auth, Source, Confidence.

9. Write the complete CONTRIBUTING.md explaining: how to clone, how to install dev dependencies with uv, how to run tests, how to add a new scanner (step by step), how to add a new writer.

10. The LICENSE file must contain the complete MIT license text.

11. After writing all files, write a SETUP.md explaining:
    - How to publish to PyPI for the first time
    - How to configure the GitHub Actions environment secret for PyPI trusted publishing
    - How to tag a release to trigger the publish workflow
    - How to install from PyPI after publishing
    - How to test locally with uvx before publishing

Begin now. Write every file completely in order, one by one. Start with pyproject.toml, then README.md, then all source files, then tests, then docs, then GitHub Actions workflows.
```
