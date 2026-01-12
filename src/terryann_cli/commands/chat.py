"""Chat command - interactive conversation mode."""

import asyncio
import random
import uuid

import httpx
import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from terryann_cli.client import GatewayClient
from terryann_cli.config import load_config
from terryann_cli.splash import print_splash, SUGGESTIONS
from terryann_cli.spinner import run_with_rotating_status

console = Console()


async def get_user_input_async(session: PromptSession) -> str | None:
    """Get user input with placeholder text (async version)."""
    # Pick a random suggestion for placeholder
    suggestion = random.choice(SUGGESTIONS)
    placeholder = f"Ask me to {suggestion.lower()}..."

    try:
        # Print thin rule above prompt
        console.print(Rule(style="dim"))

        # Use prompt_toolkit async prompt
        user_input = await session.prompt_async(
            HTML('<ansicyan><b>)</b></ansicyan> '),
            placeholder=HTML(f'<ansigray>{placeholder}</ansigray>'),
        )

        # Print thin rule below prompt
        console.print(Rule(style="dim"))

        return user_input
    except (KeyboardInterrupt, EOFError):
        return None


async def chat_loop(client: GatewayClient, session_id: str):
    """Run the interactive chat loop."""
    # Create prompt session for async input
    prompt_session = PromptSession()

    while True:
        user_input = await get_user_input_async(prompt_session)
        if user_input is None:
            console.print("\n[dim]Goodbye![/dim]")
            break

        if user_input.lower() in ("exit", "quit"):
            console.print("[dim]Goodbye![/dim]")
            break

        if not user_input.strip():
            continue

        try:
            # Use rotating branded status messages while waiting
            result = await run_with_rotating_status(
                console,
                client.send_message(session_id, user_input),
                message=user_input,
            )

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

    # Display splash screen with ASCII logo
    print_splash(console, session_id)

    try:
        asyncio.run(chat_loop(client, session_id))
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")

    raise typer.Exit(code=0)
