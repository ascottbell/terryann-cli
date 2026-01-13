"""TerryAnn CLI - Main entry point."""

import typer

from terryann_cli import __version__
from terryann_cli.commands.auth import login, logout, whoami
from terryann_cli.commands.chat import chat
from terryann_cli.commands.journeys import list_journeys, show_journey
from terryann_cli.commands.status import status

app = typer.Typer(
    name="terryann",
    help="CLI for TerryAnn Medicare Journey Intelligence Platform",
)


def version_callback(value: bool):
    if value:
        print(f"terryann-cli {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    """TerryAnn CLI - Medicare Journey Intelligence Platform.

    Run without arguments to start an interactive chat session.
    """
    # If no subcommand provided, launch chat by default
    if ctx.invoked_subcommand is None:
        chat()


app.command()(status)
app.command()(chat)
app.command()(login)
app.command()(logout)
app.command()(whoami)

# Journeys subcommand group
journeys_app = typer.Typer(help="Manage journeys")
journeys_app.command("list")(list_journeys)
journeys_app.command("show")(show_journey)
app.add_typer(journeys_app, name="journeys")


if __name__ == "__main__":
    app()
