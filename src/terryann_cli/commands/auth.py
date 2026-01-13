"""Authentication commands for TerryAnn CLI."""

import getpass

import typer
from rich.console import Console
from rich.panel import Panel

from terryann_cli import auth

console = Console()


def login(
    email: str = typer.Option(None, "--email", "-e", help="Email address"),
    password: str = typer.Option(None, "--password", "-p", help="Password (will prompt if not provided)"),
):
    """Log in to your TerryAnn account.

    Authenticates with your TerryAnn account to enable journey persistence.
    Your journeys will be saved to your account and available in the web UI.
    """
    # Check if already logged in
    current_user = auth.get_current_user()
    if current_user:
        console.print(
            f"[yellow]Already logged in as {current_user.email}[/yellow]\n"
            "Run [bold]terryann logout[/bold] first to switch accounts."
        )
        raise typer.Exit(code=0)

    # Prompt for email if not provided
    if not email:
        email = typer.prompt("Email")

    # Prompt for password securely if not provided
    if not password:
        password = getpass.getpass("Password: ")

    try:
        console.print("[dim]Authenticating...[/dim]")
        user = auth.login(email, password)

        # Use first name if available, otherwise email
        greeting = f"Welcome {user.first_name}!" if user.first_name else f"Welcome!"

        console.print(
            Panel(
                f"[green][bold]{greeting}[/bold][/green]\n\n"
                "All your journeys created here will also be\n"
                "available for review and refinement at [bold]terryann.ai[/bold]",
                title="[bold green]Authentication Successful[/bold green]",
                border_style="green",
            )
        )

    except Exception as e:
        error_msg = str(e)
        if "Invalid login credentials" in error_msg:
            console.print("[red]Invalid email or password.[/red]")
        elif "Email not confirmed" in error_msg:
            console.print("[red]Please verify your email before logging in.[/red]")
        else:
            console.print(f"[red]Login failed: {error_msg}[/red]")
        raise typer.Exit(code=1)


def logout():
    """Log out of your TerryAnn account.

    Clears stored credentials from this device.
    """
    current_user = auth.get_current_user()
    if not current_user:
        console.print("[yellow]Not currently logged in.[/yellow]")
        raise typer.Exit(code=0)

    email = current_user.email
    auth.logout()

    console.print(f"[green]Logged out from {email}[/green]")


def whoami():
    """Show current logged-in user.

    Displays authentication status and account details.
    """
    user = auth.get_current_user()

    if not user:
        console.print(
            "[yellow]Not logged in.[/yellow]\n"
            "Run [bold]terryann login[/bold] to authenticate."
        )
        raise typer.Exit(code=0)

    console.print(
        Panel(
            f"[bold]{user.email}[/bold]\n"
            f"[dim]User ID: {user.user_id}[/dim]",
            title="[bold cyan]Current User[/bold cyan]",
            border_style="cyan",
        )
    )
