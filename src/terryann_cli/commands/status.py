"""Status command - gateway health check."""

import asyncio

import httpx
import typer
from rich.console import Console
from rich.panel import Panel

from terryann_cli.client import GatewayClient
from terryann_cli.config import load_config

console = Console()


def status():
    """Check TerryAnn gateway health status."""
    config = load_config()
    client = GatewayClient(config)

    console.print(f"[dim]Checking gateway at {config.gateway_url}...[/dim]")

    try:
        result = asyncio.run(client.health_check())
        console.print(
            Panel(
                f"[green bold]Gateway is healthy[/green bold]\n\n"
                f"[dim]Status:[/dim] {result.get('status', 'unknown')}\n"
                f"[dim]URL:[/dim] {config.gateway_url}",
                title="TerryAnn Gateway",
                border_style="green",
            )
        )
    except httpx.ConnectError:
        console.print(
            Panel(
                f"[red bold]Cannot connect to gateway[/red bold]\n\n"
                f"[dim]URL:[/dim] {config.gateway_url}\n"
                f"[dim]Check that the gateway is running and the URL is correct.[/dim]",
                title="Connection Error",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError as e:
        console.print(
            Panel(
                f"[red bold]Gateway returned error[/red bold]\n\n"
                f"[dim]Status:[/dim] {e.response.status_code}\n"
                f"[dim]URL:[/dim] {config.gateway_url}",
                title="HTTP Error",
                border_style="red",
            )
        )
        raise typer.Exit(code=1)
