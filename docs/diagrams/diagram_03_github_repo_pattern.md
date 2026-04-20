# The GitHub-as-Database Serverless API Pattern

This diagram explains the popular "GitHub-as-database" pattern that apisnap specially supports.

## Mermaid Diagram

```mermaid
flowchart TB
    subgraph External["External Data Source"]
        A["External API<br/>(weather, prices, sports)"]
    end

    subgraph Workflow["GitHub Actions"]
        B["Workflow<br/>schedule: cron"]
        C["Fetch Data<br/>Python script"]
        D["Commit JSON<br/>GitHub API"]
    end

    subgraph Repo["GitHub Repository"]
        E["data/chords.json"]
        F["data/prices.json"]
        G["public/items.json"]
    end

    subgraph Serving["Public Serving"]
        H["GitHub Pages<br/>user.github.io"]
        I["Cloudflare Pages<br/>repo.pages.dev"]
        J["Custom Domain<br/>api.example.com"]
    end

    A -->|"HTTP"| C
    C -->|"write"| D
    D -->|"commit"| E
    D -->|"commit"| F
    D -->|"commit"| G
    E --> H
    F --> I
    G --> J
```

## Explanation

The GitHub-as-database pattern creates free serverless APIs:

1. **External API** fetches data from any external source
2. **Cron-based workflow** runs on schedule (e.g., every 6 hours)
3. **Python/Node script** fetches and transforms data
4. **Commits JSON** files directly to the repository
5. **GitHub/Cloudflare Pages** serves the JSON publicly

This creates a zero-cost, zero-maintenance JSON API!

## apisnap Detection

When apisnap scans a GitHub repo, it:
- Finds workflow files → extracts cron schedule
- Finds JSON data files → infers schema
- Detects public URL → generates tests