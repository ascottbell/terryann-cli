"""Journey creation confirmation UI.

Presents structured selection for campaign type and target location
to ensure clean data before creating a journey.
"""

from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import typer

from terryann_cli.constants import CAMPAIGN_TYPES, NATIONAL_ARCHETYPES, US_STATES

console = Console()


def _select_from_list(
    title: str,
    options: list[tuple],
    show_description: bool = True,
    columns: int = 1,
) -> Optional[tuple]:
    """
    Display a numbered list and let user select an option.

    Args:
        title: Header for the selection
        options: List of tuples (id, label, description) or (id, label)
        show_description: Whether to show description column
        columns: Number of columns for display (1 or 2)

    Returns:
        Selected tuple or None if cancelled
    """
    console.print()
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print()

    if columns == 2 and not show_description:
        # Two-column display for states
        half = (len(options) + 1) // 2
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(width=4)
        table.add_column(width=20)
        table.add_column(width=4)
        table.add_column(width=20)

        for i in range(half):
            left_num = f"[cyan]{i + 1}.[/cyan]"
            left_label = options[i][1]

            if i + half < len(options):
                right_num = f"[cyan]{i + half + 1}.[/cyan]"
                right_label = options[i + half][1]
            else:
                right_num = ""
                right_label = ""

            table.add_row(left_num, left_label, right_num, right_label)

        console.print(table)
    else:
        # Single column with optional descriptions
        for i, opt in enumerate(options):
            num = f"[cyan]{i + 1}.[/cyan]"
            label = opt[1]
            if show_description and len(opt) > 2:
                desc = f"[dim]- {opt[2]}[/dim]"
                console.print(f"  {num} {label} {desc}")
            else:
                console.print(f"  {num} {label}")

    console.print()
    console.print(f"  [dim]0. Cancel[/dim]")
    console.print()

    while True:
        try:
            choice = typer.prompt("Select", default="0")
            choice_num = int(choice)

            if choice_num == 0:
                return None
            elif 1 <= choice_num <= len(options):
                return options[choice_num - 1]
            else:
                console.print("[red]Invalid selection. Try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a number.[/red]")


def _get_zip_codes() -> Optional[list[str]]:
    """Prompt user for ZIP codes."""
    console.print()
    console.print("[bold cyan]Enter ZIP Code(s)[/bold cyan]")
    console.print("[dim]Separate multiple ZIPs with commas (e.g., 10023, 10024, 10025)[/dim]")
    console.print()

    zip_input = typer.prompt("ZIP code(s)", default="")

    if not zip_input.strip():
        return None

    # Parse and validate
    zips = [z.strip() for z in zip_input.split(",")]
    valid_zips = []

    for z in zips:
        if z.isdigit() and len(z) == 5:
            valid_zips.append(z)
        else:
            console.print(f"[yellow]Skipping invalid ZIP: {z}[/yellow]")

    if not valid_zips:
        console.print("[red]No valid ZIP codes entered.[/red]")
        return None

    return valid_zips


def select_campaign_type() -> Optional[tuple[str, str]]:
    """
    Let user select a campaign type.

    Returns:
        Tuple of (campaign_id, campaign_label) or None if cancelled
    """
    result = _select_from_list(
        "Select Campaign Type",
        CAMPAIGN_TYPES,
        show_description=True,
    )

    if result:
        return (result[0], result[1])
    return None


def select_target_location() -> Optional[dict]:
    """
    Let user select target location (ZIP, State, or National Archetype).

    Returns:
        Dict with location info or None if cancelled:
        - type: "zip", "state", or "archetype"
        - value: ZIP codes list, state code, or archetype ID
        - label: Human-readable description
        - cluster_id: Optional cluster ID for states/archetypes
    """
    # First, select location type
    location_types = [
        ("zip", "ZIP Code(s)", "Enter specific ZIP codes"),
        ("state", "State", "Select a state (will show market clusters)"),
        ("archetype", "National Archetype", "Target a national market segment"),
    ]

    loc_type = _select_from_list(
        "Select Target Location Type",
        location_types,
        show_description=True,
    )

    if not loc_type:
        return None

    location_type_id = loc_type[0]

    if location_type_id == "zip":
        zips = _get_zip_codes()
        if not zips:
            return None
        return {
            "type": "zip",
            "value": zips,
            "label": f"ZIP: {', '.join(zips[:3])}" + (f" +{len(zips)-3} more" if len(zips) > 3 else ""),
            "zip_codes": zips,
        }

    elif location_type_id == "state":
        state = _select_from_list(
            "Select State",
            US_STATES,
            show_description=False,
            columns=2,
        )
        if not state:
            return None

        state_code, state_name = state[0], state[1]

        # TODO: Fetch state clusters from backend and let user select
        # For now, just return the state
        return {
            "type": "state",
            "value": state_code,
            "label": state_name,
            "zip_codes": [],  # Will be resolved by backend
        }

    elif location_type_id == "archetype":
        archetype = _select_from_list(
            "Select National Archetype",
            NATIONAL_ARCHETYPES,
            show_description=True,
        )
        if not archetype:
            return None

        return {
            "type": "archetype",
            "value": archetype[0],
            "label": archetype[1],
            "zip_codes": [],  # Will be resolved by backend
            "cluster_id": archetype[0],
        }

    return None


def confirm_journey_creation() -> Optional[dict]:
    """
    Full journey creation confirmation flow.

    Guides user through campaign type and location selection,
    then confirms before creating.

    Returns:
        Dict with journey params or None if cancelled:
        - campaign_type: Campaign type ID
        - campaign_label: Human-readable campaign type
        - location: Location dict from select_target_location()
    """
    console.print()
    console.print(
        Panel(
            "Let me confirm the details before building your journey.",
            title="[bold magenta]TerryAnn[/bold magenta]",
            border_style="magenta",
        )
    )

    # Step 1: Campaign Type
    campaign = select_campaign_type()
    if not campaign:
        console.print("[dim]Journey creation cancelled.[/dim]")
        return None

    campaign_id, campaign_label = campaign

    # Step 2: Target Location
    location = select_target_location()
    if not location:
        console.print("[dim]Journey creation cancelled.[/dim]")
        return None

    # Step 3: Confirm
    console.print()
    confirm_table = Table(show_header=False, box=box.ROUNDED, border_style="green")
    confirm_table.add_column("Field", style="bold")
    confirm_table.add_column("Value")
    confirm_table.add_row("Campaign", campaign_label)
    confirm_table.add_row("Target", location["label"])

    console.print(Panel(confirm_table, title="[bold green]Confirm Journey[/bold green]", border_style="green"))
    console.print()

    actions = [
        ("create", "Create Journey", "Build the journey now"),
        ("edit", "Edit Selection", "Go back and change selections"),
    ]

    action = _select_from_list("", actions, show_description=False)

    if not action or action[0] == "edit":
        # Recursively restart
        return confirm_journey_creation()

    # Return confirmed params
    return {
        "campaign_type": campaign_id,
        "campaign_label": campaign_label,
        "location": location,
    }


def format_journey_params_for_api(params: dict) -> dict:
    """
    Convert UI params to API-ready format.

    Args:
        params: Dict from confirm_journey_creation()

    Returns:
        Dict ready for create_journey_direct() API call
    """
    location = params["location"]

    api_params = {
        "campaign_type": params["campaign_type"],
        "name": f"{location['label']} {params['campaign_label']} Journey",
        "location_description": location["label"],
    }

    if location["type"] == "zip":
        # Direct ZIP codes
        api_params["zip_codes"] = location["zip_codes"]

    elif location["type"] == "state":
        # Use locations API with state type
        # Backend will resolve state to representative ZIPs
        api_params["locations"] = [{
            "type": "state",
            "value": location["value"],  # State code like "CA"
        }]

    elif location["type"] == "archetype":
        # Use locations API with cluster type for national archetypes
        api_params["locations"] = [{
            "type": "cluster",
            "value": location["value"],  # Archetype ID like "nat_sun_belt_retiree"
        }]

    return api_params
