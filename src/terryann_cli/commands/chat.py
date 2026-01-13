"""Chat command - interactive conversation mode."""

import asyncio
import getpass
import random
import uuid

import httpx
import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from terryann_cli import auth
from terryann_cli.client import GatewayClient
from terryann_cli.config import load_config
from terryann_cli.splash import print_splash, SUGGESTIONS
from terryann_cli.spinner import run_with_rotating_status

console = Console()

# Menu commands
MENU_COMMANDS = {
    "/help": "Show help from terryann.ai",
    "/faq": "Show FAQ from terryann.ai",
    "/new": "Start a new session",
    "/clear": "Clear the screen",
    "/whoami": "Show current user",
    "/logout": "Log out and exit",
    "/exit": "Exit TerryAnn",
}


def _show_menu():
    """Display the command menu."""
    menu_text = "[bold]Available Commands[/bold]\n\n"
    for cmd, desc in MENU_COMMANDS.items():
        menu_text += f"  [cyan]{cmd:<10}[/cyan] {desc}\n"
    menu_text += "\n[dim]Or just type your message to chat with TerryAnn[/dim]"

    console.print(
        Panel(
            menu_text,
            title="[bold cyan]Menu[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        )
    )


async def _fetch_help_content(page: str = "help") -> str | None:
    """Fetch help content from terryann.ai with CLI surface filter."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://terryann.ai/{page}?surface=cli")
            response.raise_for_status()

            # Extract text content from HTML (basic extraction)
            html = response.text

            # Try to extract main content - look for common patterns
            import re

            # Remove script and style tags
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

            # Extract title
            title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else "TerryAnn Help"

            # Extract main/article content or body
            main_match = re.search(r'<main[^>]*>(.*?)</main>', html, flags=re.DOTALL | re.IGNORECASE)
            if not main_match:
                main_match = re.search(r'<article[^>]*>(.*?)</article>', html, flags=re.DOTALL | re.IGNORECASE)
            if not main_match:
                main_match = re.search(r'<body[^>]*>(.*?)</body>', html, flags=re.DOTALL | re.IGNORECASE)

            content = main_match.group(1) if main_match else html

            # Convert common HTML to Rich markup format
            content = re.sub(r'<h1[^>]*>([^<]+)</h1>', r'\n[bold]\1[/bold]\n', content, flags=re.IGNORECASE)
            content = re.sub(r'<h2[^>]*>([^<]+)</h2>', r'\n[bold cyan]\1[/bold cyan]\n', content, flags=re.IGNORECASE)
            content = re.sub(r'<h3[^>]*>([^<]+)</h3>', r'\n[cyan]\1[/cyan]\n', content, flags=re.IGNORECASE)
            content = re.sub(r'<p[^>]*>', '\n', content, flags=re.IGNORECASE)
            content = re.sub(r'</p>', '\n', content, flags=re.IGNORECASE)
            content = re.sub(r'<br\s*/?>', '\n', content, flags=re.IGNORECASE)
            content = re.sub(r'<li[^>]*>', '  • ', content, flags=re.IGNORECASE)
            content = re.sub(r'</li>', '\n', content, flags=re.IGNORECASE)
            content = re.sub(r'<strong>([^<]+)</strong>', r'[bold]\1[/bold]', content, flags=re.IGNORECASE)
            content = re.sub(r'<b>([^<]+)</b>', r'[bold]\1[/bold]', content, flags=re.IGNORECASE)
            content = re.sub(r'<em>([^<]+)</em>', r'[italic]\1[/italic]', content, flags=re.IGNORECASE)
            content = re.sub(r'<code[^>]*>([^<]+)</code>', r'[cyan]\1[/cyan]', content, flags=re.IGNORECASE)
            # Convert links to Rich clickable format: [link=URL]text[/link]
            content = re.sub(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', r'[link=\1]\2[/link]', content, flags=re.IGNORECASE)

            # Remove remaining HTML tags
            content = re.sub(r'<[^>]+>', '', content)

            # Clean up whitespace
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            content = content.strip()

            # Decode HTML entities
            import html as html_module
            content = html_module.unescape(content)

            return content

    except Exception as e:
        return None


def _show_help_fallback():
    """Show fallback help when online help is unavailable."""
    help_text = """[bold]TerryAnn CLI Help[/bold]

TerryAnn is your Medicare journey intelligence agent.

[bold cyan]Getting Started[/bold cyan]
Just describe what you want to create:
  • "Create an AEP journey for Miami"
  • "Build a retention campaign for rural Texas"
  • "Design a T65 journey for Phoenix seniors"

[bold cyan]What TerryAnn Does[/bold cyan]
  • Analyzes market data from 15+ sources
  • Generates optimized multi-channel journeys
  • Provides data-backed recommendations

[bold cyan]Commands[/bold cyan]
Type / to see all available commands.

[bold cyan]More Help[/bold cyan]
Visit [bold]terryann.ai/help[/bold] for detailed documentation."""

    console.print(
        Panel(
            help_text,
            title="[bold cyan]Help[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        )
    )


# Rotating acknowledgment messages
ACKNOWLEDGMENTS = [
    "On it...",
    "Let me think about that...",
    "Working on it...",
    "Give me a moment...",
    "Pulling that together...",
    "Crunching the numbers...",
    "Looking into that...",
    "One sec...",
]


async def get_user_input_async(session: PromptSession) -> str | None:
    """Get user input with placeholder text (async version)."""
    # Pick a random suggestion for placeholder
    suggestion = random.choice(SUGGESTIONS)
    placeholder = f"Ask me to {suggestion.lower()}..."

    try:
        # Add spacing before prompt so it doesn't sit at terminal bottom
        console.print()
        console.print()
        console.print()

        # Print thin rule above prompt
        console.print(Rule(style="dim"))

        # Use prompt_toolkit async prompt
        user_input = await session.prompt_async(
            HTML('<ansicyan><b>)</b></ansicyan> '),
            placeholder=HTML(f'<style fg="#707070">{placeholder}</style>'),
        )

        # Print thin rule below prompt
        console.print(Rule(style="dim"))

        return user_input
    except (KeyboardInterrupt, EOFError):
        return None


async def chat_loop(client: GatewayClient, session_id: str, user: auth.AuthUser):
    """Run the interactive chat loop."""
    # Create prompt session for async input
    prompt_session = PromptSession()
    current_session_id = session_id

    while True:
        user_input = await get_user_input_async(prompt_session)
        if user_input is None:
            console.print("\n[dim]Goodbye![/dim]")
            break

        input_lower = user_input.lower().strip()

        # Handle menu command
        if input_lower in ("/", "/?"):
            _show_menu()
            continue

        # Handle help/faq commands - fetch from terryann.ai
        if input_lower in ("/help", "/faq"):
            page = "faq" if input_lower == "/faq" else "help"
            title = "FAQ" if page == "faq" else "Help"
            console.print(f"[dim]Fetching {title.lower()}...[/dim]")
            help_content = await _fetch_help_content(page)
            if help_content:
                console.print(
                    Panel(
                        help_content,
                        title=f"[bold cyan]TerryAnn {title}[/bold cyan]",
                        border_style="cyan",
                        padding=(0, 1),
                    )
                )
            else:
                _show_help_fallback()
            continue

        if input_lower in ("/exit", "/quit", "exit", "quit"):
            console.print("[dim]Goodbye![/dim]")
            break

        if input_lower == "/new":
            current_session_id = str(uuid.uuid4())
            console.print(f"[green]Started new session:[/green] [dim]{current_session_id[:8]}[/dim]")
            continue

        if input_lower == "/clear":
            console.clear()
            print_splash(console, current_session_id, user_email=user.email)
            continue

        if input_lower == "/whoami":
            name_display = f" ({user.first_name})" if user.first_name else ""
            console.print(f"[cyan]Logged in as:[/cyan] {user.email}{name_display}")
            continue

        if input_lower == "/logout":
            auth.logout()
            console.print("[dim]Logged out. Goodbye![/dim]")
            break

        if not user_input.strip():
            continue

        # Check for unrecognized slash commands
        if input_lower.startswith("/"):
            console.print(f"[yellow]Unknown command:[/yellow] {user_input}")
            console.print("[dim]Type / to see available commands[/dim]")
            continue

        try:
            # Brief acknowledgment before processing
            ack = random.choice(ACKNOWLEDGMENTS)
            console.print(f"[dim]{ack}[/dim]\n")

            # Use rotating branded status messages while waiting
            result = await run_with_rotating_status(
                console,
                client.send_message(current_session_id, user_input),
                message=user_input,
            )

            response_text = result.get("response", "No response received.")

            # Check for pending_action (journey creation that needs direct backend call)
            metadata = result.get("metadata", {})
            pending_action = metadata.get("pending_action")

            if pending_action and pending_action.get("type") == "create_journey":
                # Show TerryAnn's "brb" message first
                console.print(
                    Panel(
                        response_text,
                        title="[bold magenta]TerryAnn[/bold magenta]",
                        border_style="magenta",
                        padding=(0, 1),
                    )
                )

                # Now create the journey directly (bypasses gateway timeout)
                params = pending_action.get("params", {})
                console.print()

                try:
                    journey_result = await run_with_rotating_status(
                        console,
                        client.create_journey_direct(params),
                        message="Building journey...",
                    )

                    # Format journey summary
                    journey_id = journey_result.get("id", "unknown")
                    nodes = journey_result.get("nodes", [])
                    touchpoints = [n for n in nodes if n.get("type") == "touchpoint"]

                    # Format touchpoint list
                    touchpoint_list = "\n".join(
                        f"- **Day {tp.get('data', {}).get('day', 0)}:** "
                        f"{tp.get('data', {}).get('label', 'Touchpoint')} "
                        f"({tp.get('data', {}).get('channel', 'email').title()})"
                        for tp in touchpoints[:6]
                    )
                    if len(touchpoints) > 6:
                        touchpoint_list += f"\n- ... and {len(touchpoints) - 6} more"

                    journey_summary = (
                        f"**Journey Created:** `{journey_id}`\n\n"
                        f"**Target:** {params.get('location_description') or ', '.join(params.get('zip_codes', []))}\n"
                        f"**Campaign:** {params.get('campaign_type', '').replace('_', ' ').title()}\n\n"
                        f"**Touchpoints:**\n{touchpoint_list}\n\n"
                        f"You can now ask 'what if' questions like:\n"
                        f"- \"What if we add a mailer on day 3?\"\n"
                        f"- \"What if we remove the phone call?\""
                    )

                    console.print(
                        Panel(
                            journey_summary,
                            title="[bold green]Journey Ready[/bold green]",
                            border_style="green",
                            padding=(0, 1),
                        )
                    )
                except Exception as e:
                    console.print(f"[red]Error creating journey: {e}[/red]")
            else:
                # Normal response - just show it
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


def _prompt_login() -> auth.AuthUser | None:
    """Prompt user to log in with a friendly message."""
    console.print()
    console.print(
        Panel(
            "Hi! I'm TerryAnn, your Medicare journey intelligence agent.\n\n"
            "To get started, please sign in with your TerryAnn account.\n"
            "This lets me save your journeys so you can access them\n"
            "at [bold]terryann.ai[/bold] for review and refinement.",
            title="[bold magenta]Welcome to TerryAnn[/bold magenta]",
            border_style="magenta",
        )
    )
    console.print()

    # Prompt for credentials
    try:
        email = typer.prompt("Email")
        password = getpass.getpass("Password: ")

        console.print("[dim]Signing in...[/dim]")
        user = auth.login(email, password)

        greeting = f"Welcome {user.first_name}!" if user.first_name else "Welcome!"
        console.print(f"\n[green][bold]{greeting}[/bold][/green] Let's build some journeys.\n")

        return user

    except KeyboardInterrupt:
        console.print("\n[dim]Maybe next time![/dim]")
        return None
    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            console.print("\n[red]Invalid email or password. Please try again.[/red]")
        elif "Email not confirmed" in error_msg:
            console.print("\n[red]Please verify your email before signing in.[/red]")
        else:
            console.print(f"\n[red]Sign in failed: {error_msg}[/red]")
        return None


def chat():
    """Start interactive conversation with TerryAnn."""
    config = load_config()

    # Require authentication
    user = auth.get_current_user()
    if not user:
        user = _prompt_login()
        if not user:
            raise typer.Exit(code=0)

    client = GatewayClient(config, auth_token=user.access_token)
    session_id = str(uuid.uuid4())

    # Display splash screen with ASCII logo
    print_splash(console, session_id, user_email=user.email)

    try:
        asyncio.run(chat_loop(client, session_id, user))
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye![/dim]")

    raise typer.Exit(code=0)
