"""Journeys command - list and manage journeys."""

import asyncio
from datetime import datetime

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from terryann_cli.config import load_config

console = Console()

# Channel icons for visual display
CHANNEL_ICONS = {
    "MAIL": "[blue]📬[/blue]",
    "PHONE": "[green]📞[/green]",
    "PHONE_OUTBOUND": "[green]📞[/green]",
    "PHONE_INBOUND": "[cyan]📲[/cyan]",
    "EMAIL": "[yellow]📧[/yellow]",
    "SMS": "[magenta]💬[/magenta]",
    "AGENT_VISIT": "[red]🏠[/red]",
    "PORTAL": "[white]🌐[/white]",
}

NODE_TYPE_ICONS = {
    "entry": "[green]▶[/green]",
    "touchpoint": "[cyan]●[/cyan]",
    "wait": "[yellow]⏳[/yellow]",
    "decision": "[magenta]◆[/magenta]",
    "status": "[blue]◉[/blue]",
    "exit": "[red]■[/red]",
}


def _parse_datetime(dt_str: str) -> datetime:
    """Parse ISO datetime string."""
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def _format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time (e.g., '2 hours ago')."""
    now = datetime.now(dt.tzinfo)
    delta = now - dt

    if delta.days > 0:
        return f"{delta.days}d ago"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours}h ago"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes}m ago"
    else:
        return "just now"


async def _fetch_journeys(gateway_url: str, limit: int = 20) -> dict:
    """Fetch journeys from gateway."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{gateway_url}/gateway/journeys",
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json()


def list_journeys(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of journeys to show"),
):
    """List recent journeys."""
    config = load_config()

    try:
        data = asyncio.run(_fetch_journeys(config.gateway_url, limit))
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to gateway.[/red]")
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error: Gateway returned {e.response.status_code}[/red]")
        raise typer.Exit(code=1)

    journeys = data.get("journeys", [])

    if not journeys:
        console.print("[dim]No journeys found.[/dim]")
        return

    # Create table
    table = Table(title="Recent Journeys", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Target", style="white")
    table.add_column("Touchpoints", justify="right")
    table.add_column("Created", style="dim")

    for j in journeys:
        journey_id = j["id"][:8]  # Short ID
        status = j.get("status", "draft")

        # Extract target from cohort_config or journey_data
        cohort = j.get("cohort_config", {})
        journey_data = j.get("journey_data", {}) or {}

        target = cohort.get("location", cohort.get("name", "—"))
        if not target or target == "—":
            # Try to get from journey_data
            target = journey_data.get("name", "—")

        # Get touchpoint count
        touchpoints = journey_data.get("touchpoints", [])
        tp_count = str(len(touchpoints)) if touchpoints else "—"

        # Format created time
        created_at = _parse_datetime(j["created_at"])
        created = _format_relative_time(created_at)

        # Color status
        status_display = {
            "draft": "[yellow]draft[/yellow]",
            "simulated": "[blue]simulated[/blue]",
            "approved": "[green]approved[/green]",
            "executing": "[cyan]executing[/cyan]",
        }.get(status, status)

        table.add_row(journey_id, status_display, target, tp_count, created)

    console.print(table)
    console.print(f"\n[dim]Total: {data.get('count', len(journeys))} journeys[/dim]")


async def _fetch_journey(gateway_url: str, journey_id: str) -> dict:
    """Fetch a single journey from gateway."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{gateway_url}/gateway/journeys/{journey_id}")
        response.raise_for_status()
        return response.json()


def _build_journey_tree(journey_data: dict, show_because: bool = True) -> Tree:
    """Build a Rich tree visualization of the journey flow."""
    nodes = journey_data.get("nodes", [])
    edges = journey_data.get("edges", [])

    if not nodes:
        tree = Tree("[dim]No journey flow data[/dim]")
        return tree

    # Build adjacency map from edges
    adjacency: dict[str, list[dict]] = {}
    for edge in edges:
        source = edge.get("source", "")
        if source not in adjacency:
            adjacency[source] = []
        adjacency[source].append(edge)

    # Build node lookup
    node_map = {n.get("id"): n for n in nodes}

    # Find entry node
    entry_node = None
    for n in nodes:
        if n.get("type") == "entry":
            entry_node = n
            break

    if not entry_node:
        tree = Tree("[dim]No entry node found[/dim]")
        return tree

    # Build tree recursively
    tree = Tree(f"{NODE_TYPE_ICONS.get('entry', '▶')} [bold]Journey Start[/bold]")
    visited = set()

    def add_node_to_tree(parent_tree, node_id: str, edge_label: str | None = None):
        if node_id in visited:
            parent_tree.add(f"[dim]↩ (loops to {node_id})[/dim]")
            return
        visited.add(node_id)

        node = node_map.get(node_id)
        if not node:
            return

        node_type = node.get("type", "unknown")
        icon = NODE_TYPE_ICONS.get(node_type, "○")
        label = node.get("label", node_id)

        # Build node display string
        if node_type == "touchpoint":
            channel = node.get("channel", "")
            channel_icon = CHANNEL_ICONS.get(channel, "")
            display = f"{icon} {channel_icon} [bold]{label}[/bold] [dim]({channel})[/dim]"

            # Add "because" evidence if present and enabled
            if show_because:
                because = node.get("because", {})
                if because and because.get("claim"):
                    claim = because.get("claim", "")
                    if len(claim) > 80:
                        display += f"\n      [dim italic]↳ {claim[:80]}...[/dim italic]"
                    else:
                        display += f"\n      [dim italic]↳ {claim}[/dim italic]"
        elif node_type == "wait":
            wait_days = node.get("wait_days")
            wait_until = node.get("wait_until")
            if wait_days:
                display = f"{icon} [yellow]{label}[/yellow] [dim]({wait_days} days)[/dim]"
            elif wait_until:
                display = f"{icon} [yellow]{label}[/yellow] [dim](until {wait_until})[/dim]"
            else:
                display = f"{icon} [yellow]{label}[/yellow]"
        elif node_type == "decision":
            question = node.get("decision_question", "")
            display = f"{icon} [magenta]{label}[/magenta]"
            if question:
                display += f"\n      [dim]? {question}[/dim]"
        elif node_type == "exit":
            display = f"{icon} [red]{label}[/red]"
        elif node_type == "status":
            status_type = node.get("status_type", "")
            color = {"success": "green", "failure": "red", "pending": "yellow"}.get(
                status_type, "blue"
            )
            display = f"{icon} [{color}]{label}[/{color}]"
        else:
            display = f"{icon} {label}"

        # Add edge label if present (Yes/No for decisions)
        if edge_label:
            display = f"[dim]{edge_label}→[/dim] " + display

        branch = parent_tree.add(display)

        # Add children
        child_edges = adjacency.get(node_id, [])
        for edge in child_edges:
            target = edge.get("target")
            label = edge.get("label")  # "Yes", "No", or None
            add_node_to_tree(branch, target, label)

    # Start from entry node's children
    for edge in adjacency.get(entry_node.get("id"), []):
        add_node_to_tree(tree, edge.get("target"))

    return tree


def _display_simulation_results(simulation: dict):
    """Display simulation results in a table."""
    if not simulation:
        return

    console.print("\n[bold]Simulation Results[/bold]")

    # Extract key metrics
    summary = simulation.get("summary", {})
    metrics = simulation.get("metrics", {})

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    if summary.get("total_contacts"):
        table.add_row("Total Contacts", f"{summary['total_contacts']:,}")
    if summary.get("total_conversions"):
        table.add_row("Conversions", f"{summary['total_conversions']:,}")
    if summary.get("conversion_rate"):
        table.add_row("Conversion Rate", f"{summary['conversion_rate']:.1%}")
    if metrics.get("estimated_roi"):
        table.add_row("Estimated ROI", f"{metrics['estimated_roi']:.1f}x")
    if metrics.get("cost_per_conversion"):
        table.add_row("Cost/Conversion", f"${metrics['cost_per_conversion']:.2f}")

    console.print(table)


def show_journey(
    journey_id: str = typer.Argument(..., help="Journey ID (full or short)"),
    brief: bool = typer.Option(False, "--brief", "-b", help="Hide 'because' reasoning statements"),
):
    """Show journey details and visualization."""
    config = load_config()

    try:
        journey = asyncio.run(_fetch_journey(config.gateway_url, journey_id))
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to gateway.[/red]")
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]Journey not found: {journey_id}[/red]")
        else:
            console.print(f"[red]Error: Gateway returned {e.response.status_code}[/red]")
        raise typer.Exit(code=1)

    # Journey header
    status = journey.get("status", "draft")
    status_color = {
        "draft": "yellow",
        "simulated": "blue",
        "approved": "green",
        "executing": "cyan",
    }.get(status, "white")

    created_at = _parse_datetime(journey["created_at"])
    created = _format_relative_time(created_at)

    # Get name from cohort_config or journey_data
    cohort = journey.get("cohort_config", {})
    journey_data = journey.get("journey_data", {}) or {}
    name = journey_data.get("name") or cohort.get("name") or cohort.get("location") or "Unnamed Journey"

    header = f"[bold]{name}[/bold]\n"
    header += f"[dim]ID: {journey['id']}[/dim]\n"
    header += f"Status: [{status_color}]{status}[/{status_color}] • Created: {created}"

    console.print(Panel(header, title="Journey", border_style="blue"))

    # Cohort info if present
    if cohort:
        cohort_info = []
        if cohort.get("location"):
            cohort_info.append(f"Location: {cohort['location']}")
        if cohort.get("zip_codes"):
            zips = cohort["zip_codes"]
            if len(zips) <= 3:
                cohort_info.append(f"ZIP codes: {', '.join(zips)}")
            else:
                cohort_info.append(f"ZIP codes: {', '.join(zips[:3])}... (+{len(zips)-3} more)")
        if cohort.get("campaign_type"):
            cohort_info.append(f"Campaign: {cohort['campaign_type'].replace('_', ' ').title()}")
        if cohort_info:
            console.print(Panel("\n".join(cohort_info), title="Cohort", border_style="dim"))

    # Journey flow visualization
    if journey_data:
        console.print("\n[bold]Journey Flow[/bold]")
        tree = _build_journey_tree(journey_data, show_because=not brief)
        console.print(tree)

        # Show hint when in brief mode
        if brief:
            console.print("\n[dim]Tip: Run without --brief to see data-driven reasoning for each touchpoint[/dim]")

        # Methodology notes if present
        notes = journey_data.get("methodology_notes")
        if notes:
            console.print(f"\n[dim italic]Methodology: {notes}[/dim italic]")

    # Simulation results
    simulation = journey.get("simulation_results")
    if simulation:
        _display_simulation_results(simulation)
