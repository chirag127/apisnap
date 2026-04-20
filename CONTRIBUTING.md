# Contributing to apisnap

Thank you for your interest in contributing to apisnap! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip or uv for package management

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/chirag127/apisnap.git
cd apisnap

# Install with uv (recommended)
uv venv
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_github_repo_scanner.py -v

# Run with coverage
pytest tests/ --cov=apisnap --cov-report=html
```

## Adding a New Scanner

Scanners discover API endpoints from different sources.

### Step 1: Create the Scanner

Create `src/apisnap/scanner/source/myframework_scanner.py`:

```python
from pathlib import Path
from apisnap.schema import RouteManifest, Route
from apisnap.scanner.base import BaseScanner


class MyFrameworkScanner(BaseScanner):
    """Scanner for MyFramework projects."""

    def can_handle(self, path: str) -> bool:
        """Check if path contains MyFramework files."""
        directory = Path(path)
        if not directory.is_dir():
            directory = directory.parent
        
        # Check for framework-specific files
        return (directory / "myframework.json").exists() or \
               (directory / "framework.config").exists()

    def scan(self, path: str, **kwargs) -> RouteManifest:
        """Scan for MyFramework routes."""
        routes = []
        directory = Path(path)
        
        if not directory.is_dir():
            directory = directory.parent
        
        # Find and parse route definitions
        for py_file in directory.rglob("*.py"):
            if self._should_skip(py_file):
                continue
            
            content = py_file.read_text(encoding="utf-8")
            file_routes = self._extract_routes(content)
            routes.extend(file_routes)
        
        return RouteManifest(
            routes=routes,
            framework="myframework",
            project_name=directory.name,
            source_mode="scanned",
            detected_at=path,
        )

    def _should_skip(self, path: Path) -> bool:
        """Skip test and cache directories."""
        skip_dirs = ["__pycache__", ".git", "venv", "env"]
        return any(skip in path.parts for skip in skip_dirs)

    def _extract_routes(self, content: str) -> list[Route]:
        """Extract routes from file content."""
        routes = []
        # Implement your parsing logic here
        # Use regex to find route definitions
        return routes
```

### Step 2: Register the Scanner

Add it to the detector in `src/apisnap/scanner/detector.py`:

```python
from apisnap.scanner.source.myframework_scanner import MyFrameworkScanner

SCANNERS = [
    # ... existing scanners
    MyFrameworkScanner,
]
```

## Adding a New Writer

Writers generate test code in different formats.

### Step 1: Create the Writer

Create `src/apisnap/writers/myformat_writer.py`:

```python
import json
from pathlib import Path
from apisnap.schema import RouteManifest, Route
from apisnap.writers.base_writer import BaseWriter


class MyFormatWriter(BaseWriter):
    """Writer for MyFormat."""

    def write(self, manifest: RouteManifest, output_dir: str) -> dict:
        """Write tests to files."""
        results = {}
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, route in enumerate(manifest.routes):
            test_code = self._generate_route_test(route)
            filename = self._get_filename(route, i)
            results[filename] = test_code
            (output_path / filename).write_text(test_code)
        
        return results

    def write_file(self, manifest: RouteManifest, output_path: str) -> str:
        """Write tests to a single file."""
        all_tests = []
        
        for route in manifest.routes:
            test_code = self._generate_route_test(route)
            all_tests.append(test_code)
        
        return "\n\n".join(all_tests)

    def _generate_route_test(self, route: Route) -> str:
        """Generate test code for a route."""
        # Implement your test generation logic
        return f"# Test for {route.path}"

    def _get_filename(self, route: Route, index: int) -> str:
        """Get filename for a route."""
        name = route.path.strip("/").replace("/", "-")
        return f"test-{name}.ext"
```

### Step 2: Register the Writer

Add it to the writers package in `src/apisnap/writers/__init__.py`:

```python
from apisnap.writers.myformat_writer import MyFormatWriter

FORMAT_WRITERS = {
    # ... existing writers
    "myformat": MyFormatWriter,
}
```

## Code Style

- Use **Black** for formatting
- Use **type hints** for all function signatures
- Use **docstrings** for classes and complex functions
- Keep lines under 100 characters
- Follow existing naming conventions

### Running Linting

```bash
# Format with Black
black src/ tests/

# Check with ruff
ruff check src/ tests/

# Type check with mypy
mypy src/
```

## Testing Guidelines

- Write tests for every new feature
- Keep tests focused and isolated
- Use descriptive test names
- Follow the existing test patterns

### Test File Structure

```python
"""Tests for feature X."""

import pytest
from apisnap.module import ClassName


class TestClassName:
    """Tests for ClassName."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        result = ClassName().method()
        assert result is not None

    def test_edge_case(self):
        """Test edge case handling."""
        with pytest.raises(ValueError):
            ClassName().invalid_method()
```

## Commit Guidelines

- Use clear, descriptive commit messages
- Keep commits focused and atomic
- Reference issues in commit messages (e.g., "Fixes #123")

## Submitting Changes

1. Create a branch for your feature
2. Make your changes
3. Run tests locally
4. Push your branch
5. Open a pull request

## Getting Help

- Open an issue for bugs or feature requests
- Check the README for documentation
- Review existing issues before opening a new one

---

Thank you for contributing!