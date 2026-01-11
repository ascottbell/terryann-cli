"""Chat command - interactive conversation mode."""

import typer
from rich.console import Console
from rich.panel import Panel

from terryann_cli.config import load_config

console = Console()


def chat():
    """Start interactive conversation with TerryAnn."""
    config = load_config()

    console.print(
        Panel(
            "[yellow]Interactive chat mode is not yet implemented.[/yellow]\n\n"
            f"[dim]Gateway URL:[/dim] {config.gateway_url}\n"
            f"[dim]Endpoint:[/dim] POST /gateway/message\n\n"
            "[dim]This will provide an interactive conversation loop "
            "for Medicare journey intelligence queries.[/dim]",
            title="TerryAnn Chat",
            subtitle="Coming Soon",
            border_style="yellow",
        )
    )
    raise typer.Exit(code=0)
