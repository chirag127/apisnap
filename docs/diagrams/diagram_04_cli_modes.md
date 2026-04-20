# CLI Modes Reference

This diagram shows all apisnap CLI commands and their options.

## Mermaid Diagram

```mermaid
flowchart TD
    subgraph Config["apisnap config"]
        C1["--api-key KEY"]
        C2["--show"]
        C3["--format FORMAT"]
        C4["--output-dir DIR"]
    end

    subgraph Scan["apisnap scan"]
        S1["PATH"]
        S2["--url URL"]
        S3["--format FORMAT"]
        S4["--output DIR"]
        S5["--framework FMW"]
        S6["--mode MODE"]
        S7["--dry-run"]
        S8["--base-url URL"]
        S9["--verbose"]
        S10["--no-ai"]
    end

    subgraph List["apisnap list"]
        L1["PATH"]
    end

    subgraph Version["apisnap version"]
        V1[...]
    end

    Scan --> S1
    Scan --> S2
    Scan --> S3
    Scan --> S4
    Scan --> S5
    Scan --> S6
    Scan --> S7
    Scan --> S8
    Scan --> S9
    Scan --> S10
```

## CLI Input Modes

| Mode | Command | Description |
|------|---------|-------------|
| Local | `apisnap scan ./src` | Scan local codebase |
| OpenAPI | `apisnap scan --url https://api.example.com/openapi.json` | Parse OpenAPI spec |
| JSON | `apisnap scan --url https://api.example.com/data.json` | Infer from JSON endpoint |
| Deployed | `apisnap scan --url https://myapp.pages.dev` | Crawl deployed app |
| GitHub | `apisnap scan --url https://github.com/user/repo` | Scan GitHub-as-database |

## Supported Frameworks

- **Source**: FastAPI, Flask, Django, Express, Spring, Gin, Rails
- **Output**: pytest, unittest, jest, mocha, vitest, restassured, rspec, httpx