"""TerryAnn CLI - Main entry point."""

import typer

from terryann_cli import __version__
from terryann_cli.commands.chat import chat
from terryann_cli.commands.status import status

app = typer.Typer(
    name="terryann",
    help="CLI for TerryAnn Medicare Journey Intelligence Platform",
    no_args_is_help=True,
)


def version_callback(value: bool):
    if value:
        print(f"terryann-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    """TerryAnn CLI - Medicare Journey Intelligence Platform."""
    pass


app.command()(status)
app.command()(chat)


if __name__ == "__main__":
    app()
