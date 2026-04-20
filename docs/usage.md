# apisnap Usage Guide

## Quick Start

### 1. Install and Configure

```bash
pip install apisnap
apisnap config --api-key YOUR_API_KEY
```

### 2. Generate Tests

```bash
# Scan a GitHub repo (GitHub-as-database pattern)
apisnap scan --url https://github.com/user/repo

# Scan local project
apisnap scan ./src

# Scan OpenAPI URL
apisnap scan --url https://api.example.com/openapi.json
```

### 3. Run Tests

```bash
pytest tests/ -v
```

## Input Modes

### Mode 1: Local Source Code

```bash
apisnap scan ./src
```

Auto-detects frameworks: FastAPI, Flask, Django, Express, Spring, Gin, Rails

### Mode 2: OpenAPI/Swagger

```bash
apisnap scan --url https://api.example.com/openapi.json
```

### Mode 3: Raw JSON Endpoint

```bash
apisnap scan --url https://api.example.com/data.json
```

### Mode 4: Deployed Web App

```bash
apisnap scan --url https://myapp.pages.dev
```

Probes for OpenAPI spec or common REST patterns.

### Mode 5: GitHub Repository (GitHub-as-Database)

```bash
apisnap scan --url https://github.com/user/repo
```

Special mode for GitHub-as-database repos.

## Output Formats

| Format | Flag | Language |
|--------|-----|----------|
| pytest | `--format pytest` | Python |
| unittest | `--format unittest` | Python |
| httpx | `--format httpx_test` | Python |
| jest | `--format jest` | JavaScript |
| mocha | `--format mocha` | JavaScript |
| vitest | `--format vitest` | TypeScript |
| restassured | `--format restassured` | Java |
| rspec | `--format rspec` | Ruby |

## Configuration

Config stored at `~/.apisnap/config.toml`:

```toml
[cerebras]
api_key = "sk-xxx"
model = "gpt-oss-120b"

[defaults]
output_dir = "./tests"
format = "pytest"
```

## Common Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Show routes without generating tests |
| `--verbose` | Show detailed progress |
| `--no-ai` | Print manifest as JSON, skip AI |
| `--output DIR` | Output directory (default: ./tests) |
| `--format FMT` | Test framework (default: pytest) |

## Troubleshooting

### No API key configured
```bash
apisnap config --api-key YOUR_KEY
```

### No routes found
- Check the path or URL is correct
- Try with `--verbose` for details
- Use `--no-ai` to see raw manifest

### Tests failing
- Check the base URL in tests
- Verify the API is accessible
- Adjust tests manually if needed