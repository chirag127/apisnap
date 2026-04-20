"""Display utilities for terminal output."""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from apisnap.schema import RouteManifest


console = Console()


def print_spinner(message: str, task_id: str = "spinner"):
    """Create a spinner context."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]Success:[/bold green] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[blue]Info:[/blue] {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_routes(manifest: RouteManifest) -> None:
    """Print routes as a table."""
    if not manifest.routes:
        print_warning("No routes found")
        return

    table = Table(title="Discovered Routes")

    table.add_column("Method", style="cyan")
    table.add_column("Path", style="white")
    table.add_column("Auth", style="yellow")
    table.add_column("Source", style="magenta")
    table.add_column("Confidence", style="green")

    for route in manifest.routes:
        auth = "Yes" if route.auth_required else "No"
        confidence = f"{route.confidence:.0%}"

        table.add_row(
            route.method,
            route.path,
            auth,
            route.source,
            confidence,
        )

    console.print(table)


def print_manifest_json(manifest: RouteManifest) -> None:
    """Print manifest as JSON."""
    import json

    console.print_json(json.dumps(manifest.to_dict()))


def print_header(title: str) -> None:
    """Print a header."""
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print("=" * len(title))


def print_subheader(title: str) -> None:
    """Print a subheader."""
    console.print(f"\n[bold]{title}[/bold]")


def print_dict(data: dict) -> None:
    """Print dictionary as formatted text."""
    for key, value in data.items():
        console.print(f"  [cyan]{key}:[/cyan] {value}")


def print_list(items: list, prefix: str = "- ") -> None:
    """Print list items."""
    for item in items:
        console.print(f"  {prefix}{item}")
