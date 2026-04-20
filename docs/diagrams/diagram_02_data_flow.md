# Data Flow Diagram

This diagram shows how data flows through apisnap from input to generated tests.

## Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW DIAGRAM                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   User       │     │   Scanner    │     │   Schema     │     │   AI         │
│   Input      │────▶│   Detection  │────▶│   Building   │────▶│   Processing │
└──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
                                                                          │
                                                                          ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Test       │     │   File       │     │   Output     │     │   Generated  │
│   Files      │◀────│   Writing    │◀────│   Format     │◀────│   Test Code  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

## Data Processing Stages

1. **User Input**: URL, path, or GitHub repo URL
2. **Scanner Detection**: Select appropriate scanner based on input type
3. **Schema Building**: Extract route information and build RouteManifest
4. **AI Processing**: Two-pass AI strategy (schema refinement + test generation)
5. **Output Format**: Select target test framework
6. **File Writing**: Generate and save test files
7. **Test Files**: Final runnable test code