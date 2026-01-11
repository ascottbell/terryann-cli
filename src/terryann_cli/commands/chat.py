"""Chat command - interactive conversation mode."""

import asyncio
import uuid

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from terryann_cli.client import GatewayClient
from terryann_cli.config import load_config

console = Console()


async def chat_loop(client: GatewayClient, session_id: str):
    """Run the interactive chat loop."""
    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if user_input.lower() in ("exit", "quit"):
            console.print("[dim]Goodbye![/dim]")
            break

        if not user_input.strip():
            continue

        try:
            with console.status("[dim]TerryAnn is thinking...[/dim]", spinner="dots"):
                result = await client.send_message(session_id, user_input)

            response_text = result.get("response", "No response received.")
            console.print(
                Panel(
                    response_text,
                    title="[bold magenta]TerryAnn[/bold magenta]",
                    border_style="magenta",
                    padding=(0, 1),
                )
            )

        except httpx.ConnectError:
            console.print(
                "[red]Error: Cannot connect to gateway. Check your connection.[/red]"
            )
        except httpx.TimeoutException:
            console.print(
                "[red]Error: Request timed out. The gateway may be busy.[/red]"
            )
        except httpx.HTTPStatusError as e:
            console.print(f"[red]Error: Gateway returned {e.response.status_code}[/red]")


def chat():
    """Start interactive conversation with TerryAnn."""
    config = load_config()
    client = GatewayClient(config)
    session_id = str(uuid.uuid4())

    console.print(
        Panel(
            "[bold]Welcome to TerryAnn[/bold]\n"
            "Medicare Journey Intelligence Assistant\n\n"
            f"[dim]Session:[/dim] {session_id[:8]}...\n"
            f"[dim]Gateway:[/dim] {config.gateway_url}\n\n"
            "[dim]Type 'exit' or 'quit' to end the conversation.[/dim]",
            title="TerryAnn Chat",
            border_style="blue",
        )
    )

    try:
        asyncio.run(chat_loop(client, session_id))
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")

    raise typer.Exit(code=0)
