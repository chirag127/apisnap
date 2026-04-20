"""CLI interface for apisnap."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from apisnap import __version__
from apisnap import config
from apisnap.schema import RouteManifest
from apisnap.scanner.detector import detect_and_scan
from apisnap.writers import get_writer
from apisnap.ai.client import CerebrasClient
from apisnap.utils.display import (
    print_error,
    print_success,
    print_info,
    print_routes,
    print_header,
    print_manifest_json,
    print_spinner,
)

app = typer.Typer(
    name="apisnap",
    help="AI-powered API test case generator",
    add_completion=False,
)
console = Console()


@app.command()
def config_cmd(
    api_key: Optional[str] = typer.Option(
        None, "--api-key", help="Set Cerebras API key"
    ),
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    format: Optional[str] = typer.Option(None, "--format", help="Default test format"),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", help="Default output directory"
    ),
):
    """Manage apisnap configuration."""
    if show:
        console.print(config.show_config())
        return

    if api_key:
        config.set_api_key(api_key)
        print_success("API key saved")

    if format:
        config.set_default_format(format)
        print_success(f"Default format set to {format}")

    if output_dir:
        config.set_default_output_dir(output_dir)
        print_success(f"Default output directory set to {output_dir}")

    if not api_key and not show and not format and not output_dir:
        # Interactive setup
        key = typer.prompt("Enter Cerebras API key", hide_input=True)
        if key:
            config.set_api_key(key)
            print_success("API key saved")

        fmt = typer.prompt("Default format (pytest)", default="pytest")
        if fmt:
            config.set_default_format(fmt)

        out = typer.prompt("Default output directory", default="./tests")
        if out:
            config.set_default_output_dir(out)


@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to scan (directory or URL)"),
    url: Optional[str] = typer.Option(None, "--url", help="Remote URL to scan"),
    format: str = typer.Option("pytest", "--format", help="Test framework output"),
    output: str = typer.Option("./tests", "--output", help="Output directory"),
    framework: Optional[str] = typer.Option(
        None, "--framework", help="Force framework"
    ),
    mode: Optional[str] = typer.Option(None, "--mode", help="Discovery mode"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show routes without generating tests"
    ),
    base_url: Optional[str] = typer.Option(
        None, "--base-url", help="Base URL for tests"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Verbose output"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Skip AI test generation"),
):
    """Scan for API endpoints and generate tests."""
    # Use URL if provided
    scan_path = url if url else path

    if verbose:
        print_info(f"Scanning: {scan_path}")

    # Detect and scan
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Scanning for routes...", total=None)

            manifest = detect_and_scan(
                scan_path,
                mode=mode,
                framework=framework,
            )

            progress.update(task, completed=True)

        # Show routes
        if dry_run:
            print_header("Discovered Routes")
            print_routes(manifest)
            return

        # Show as JSON if --no-ai
        if no_ai:
            print_manifest_json(manifest)
            return

        # Generate tests
        print_header("Generating Tests")

        # Check for API key
        api_key = config.get_api_key()
        if not api_key:
            print_error("No API key configured. Run 'apisnap config' first.")
            print_info("Or use --no-ai to see the discovered routes as JSON.")
            return

        # Get writer
        writer = get_writer(format)

        # Generate tests
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating tests...", total=None)

            # Override base_url if provided
            if base_url:
                manifest.base_url = base_url

            # Generate tests
            results = writer.write(manifest, output)

            progress.update(task, completed=True)

        print_success(f"Generated {len(results)} test files in {output}/")

    except Exception as e:
        print_error(f"Failed to scan: {str(e)}")
        if verbose:
            raise
        sys.exit(1)


@app.command()
def list_routes(
    path: str = typer.Argument(".", help="Path to scan"),
):
    """List discovered routes."""
    try:
        manifest = detect_and_scan(path)
        print_routes(manifest)
    except Exception as e:
        print_error(f"Failed to list routes: {str(e)}")
        sys.exit(1)


@app.command()
def version():
    """Show version."""
    console.print(f"apisnap {__version__}")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
