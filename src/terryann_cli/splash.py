"""Splash screen for TerryAnn CLI."""

import base64
import os
import random
import sys
from importlib import resources
from pathlib import Path

from rich.console import Console
from rich.text import Text

from terryann_cli import __version__

# TerryAnn brand colors (from SVG logo)
BLUE = "#b8d4e3"       # Soft blue - left circle
CORAL = "#c4785a"      # Terracotta - right circle
DARK = "#2d2a26"       # Dark brown - smile
DIM = "#666666"        # Dim text

# Rotating suggestion prompts
SUGGESTIONS = [
    "Create an AEP acquisition journey for Miami",
    "What's the difference between a D-SNP and C-SNP?",
    "Explain the Medicare enrollment periods",
    "Build a retention journey for rural Texas",
    "What channels work best for low-income seniors?",
    "Create an OEP winback campaign for Southern California",
    "How should I approach dual-eligible members?",
    "What compliance rules should I know about?",
]


def get_logo_path() -> Path:
    """Get the path to the logo PNG file."""
    try:
        # Python 3.9+ way
        with resources.files("terryann_cli").joinpath("assets/terryann-logo.png") as p:
            return Path(p)
    except (TypeError, AttributeError):
        # Fallback for development
        return Path(__file__).parent / "assets" / "terryann-logo.png"


def is_iterm2() -> bool:
    """Check if running in iTerm2."""
    return os.environ.get("TERM_PROGRAM") == "iTerm.app"


def render_iterm2_image(image_path: Path, width: int = 10) -> bool:
    """
    Render image using iTerm2's native imgcat protocol.

    This renders inline at cursor position (not centered on screen).
    """
    try:
        if not is_iterm2():
            return False

        if not image_path.exists():
            return False

        # Read and encode the image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("ascii")

        # iTerm2 inline image escape sequence
        # OSC 1337 ; File=[args] : base64_data ST
        # Using width in cells, inline=1 means render at cursor position
        osc = f"\033]1337;File=inline=1;width={width}:{image_data}\a"

        # Center the image by adding leading spaces
        # "Medicare Journey Intelligence" is ~30 chars, image is ~10 cells
        # So we want about 10 spaces to center above the text
        sys.stdout.write("          " + osc + "\n")
        sys.stdout.flush()
        return True

    except Exception:
        return False


def get_ascii_logo_lines() -> list[Text]:
    """
    Generate the TerryAnn logo as ASCII art (fallback for basic terminals).

    Two identical circles touching side by side (blue left, coral right)
    with a smile/bridge underneath connecting at their bottom centers.
    """
    lines = []

    # Line 1: tops of circles (rounded)
    line1 = Text()
    line1.append("          ")  # Center padding
    line1.append("▄████▄", style=BLUE)
    line1.append("▄████▄", style=CORAL)
    lines.append(line1)

    # Line 2: body
    line2 = Text()
    line2.append("         ")
    line2.append("████████", style=BLUE)
    line2.append("████████", style=CORAL)
    lines.append(line2)

    # Line 3: bottoms of circles (rounded)
    line3 = Text()
    line3.append("          ")
    line3.append("▀████▀", style=BLUE)
    line3.append("▀████▀", style=CORAL)
    lines.append(line3)

    # Line 4: smile connecting bottom centers
    line4 = Text()
    line4.append("            ")
    line4.append("╰──────╯", style=DARK)
    lines.append(line4)

    return lines


def print_splash(console: Console, session_id: str, user_email: str | None = None) -> None:
    """
    Print the TerryAnn splash screen.

    Clears the terminal first so CLI starts fresh at top of screen.

    Args:
        console: Rich console to print to
        session_id: Session ID (first 8 chars shown)
        user_email: Logged in user email (if authenticated)
    """
    # Clear screen and move cursor to top (like Claude Code)
    console.clear()

    console.print()

    # Try to render actual image, fall back to ASCII art
    logo_path = get_logo_path()
    if not render_iterm2_image(logo_path, width=10):
        for line in get_ascii_logo_lines():
            console.print(line)

    # Title and tagline - centered
    title = Text()
    title.append("          TerryAnn", style="bold white")
    console.print(title)

    tagline = Text()
    tagline.append("  Medicare Journey Intelligence", style=DIM)
    console.print(tagline)

    console.print()

    # Session info and hints on one line
    session_line = f"  [dim]v{__version__}[/dim]  [dim]│[/dim]  [dim]Session:[/dim] {session_id[:8]}"
    if user_email:
        session_line += f"  [dim]│[/dim]  [green]{user_email}[/green]"
    else:
        session_line += "  [dim]│[/dim]  [dim]Not logged in[/dim]"
    session_line += "  [dim]│[/dim]  [dim]/ for menu[/dim]"
    console.print(session_line)

    console.print()
