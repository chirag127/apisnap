# System Overview Diagram

This diagram shows the high-level architecture of apisnap, from input to output.

## Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APISNAP SYSTEM OVERVIEW                           │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │   Mode 1    │   │   Mode 2    │   │   Mode 3    │   │   Mode 4    │
    │ Local Code  │   │  OpenAPI    │   │  JSON URL   │   │  Deployed   │
    │   Scan      │   │    URL      │   │             │   │     URL     │
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           │                  │                  │                  │
           ▼                  ▼                  ▼                  ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           AUTO-DETECTOR                                    │
    │                    Detects framework & input type                         │
    └─────────────────────────────────┬─────────────────────────────────────────┘
                                      │
                                      ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         ROUTE MANIFEST                                    │
    │         { routes: [ { method, path, params, auth, schema... } ] }       │
    └─────────────────────────────────┬─────────────────────────────────────────┘
                                      │
                                      ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         AI ENGINE (Cerebras)                             │
    │         Two-pass: 1) Schema refinement  2) Test generation              │
    └─────────────────────────────────┬─────────────────────────────────────────┘
                                      │
                                      ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                         TEST WRITERS                                      │
    │    pytest | unittest | jest | mocha | vitest | restassured | rspec     │
    └─────────────────────────────────┬─────────────────────────────────────────┘
                                      │
                                      ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           OUTPUT FILES                                    │
    │                         ./tests/*.py                                     │
    └─────────────────────────────────────────────────────────────────────────┘
```

## Components

- **Mode 1 - Local Code Scan**: Scans local project files for route definitions
- **Mode 2 - OpenAPI URL**: Fetches OpenAPI/Swagger specs from URLs
- **Mode 3 - JSON URL**: Points at raw JSON endpoints
- **Mode 4 - Deployed URL**: Scans deployed web apps
- **Mode 5 - GitHub Repo**: Special mode for GitHub-as-database repos
- **Auto-Detector**: Determines the correct scanner to use
- **Route Manifest**: Internal data structure holding all route information
- **AI Engine**: Uses Cerebras AI to generate tests
- **Test Writers**: Converts route info to framework-specific test code
- **Output Files**: Generated test files in target directory