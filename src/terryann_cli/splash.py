"""ASCII art splash screen for TerryAnn CLI."""

import random

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


def get_logo_lines() -> list[Text]:
    """
    Generate the TerryAnn logo as Rich Text objects.

    Two identical circles touching side by side (blue left, coral right)
    with a smile/bridge underneath connecting at their bottom centers.
    """
    lines = []

    # Line 1: tops of circles (rounded)
    line1 = Text()
    line1.append("  ")
    line1.append("▄████▄", style=BLUE)
    line1.append("▄████▄", style=CORAL)
    lines.append(line1)

    # Line 2: body
    line2 = Text()
    line2.append(" ")
    line2.append("████████", style=BLUE)
    line2.append("████████", style=CORAL)
    lines.append(line2)

    # Line 3: bottoms of circles (rounded)
    line3 = Text()
    line3.append("  ")
    line3.append("▀████▀", style=BLUE)
    line3.append("▀████▀", style=CORAL)
    lines.append(line3)

    # Line 4: smile connecting bottom centers
    line4 = Text()
    line4.append("    ")
    line4.append("╰──────╯", style=DARK)
    lines.append(line4)

    return lines


def print_splash(console: Console, session_id: str) -> None:
    """
    Print the TerryAnn splash screen.

    Args:
        console: Rich console to print to
        session_id: Session ID (first 8 chars shown)
    """
    console.print()

    # Print logo
    for line in get_logo_lines():
        console.print(line)

    console.print()

    # Title and tagline
    title = Text()
    title.append("  TerryAnn", style="bold white")
    console.print(title)

    tagline = Text()
    tagline.append("  Medicare Journey Intelligence", style=DIM)
    console.print(tagline)

    console.print()

    # Separator
    console.print(f"  [dim]{'─' * 30}[/dim]")

    console.print()

    # Session info (version only, no gateway URL)
    console.print(f"  [dim]v{__version__}[/dim]  [dim]│[/dim]  [dim]Session:[/dim] {session_id[:8]}")

    console.print()

    # Usage hints
    console.print("  [dim]Type 'exit' to end  •  Ctrl+C to interrupt[/dim]")
    console.print("  [dim]Type [/dim][dim bold]?[/dim bold][dim] for help[/dim]")

    console.print()

    # Random suggestion
    suggestion = random.choice(SUGGESTIONS)
    console.print(f"  [dim italic]Try: {suggestion}[/dim italic]")

    console.print()
