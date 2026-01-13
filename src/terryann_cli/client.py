"""HTTP client for TerryAnn Gateway."""

from typing import Any, Optional

import httpx

from terryann_cli.config import Config

# Backend URL for direct calls (bypasses gateway for long-running operations)
BACKEND_URL = "https://synthwell-prototype-production.up.railway.app"


class GatewayClient:
    """Async HTTP client for TerryAnn Gateway."""

    def __init__(self, config: Config, auth_token: Optional[str] = None):
        self.config = config
        self.base_url = config.gateway_url.rstrip("/")
        self.auth_token = auth_token

    def _get_headers(self) -> dict:
        """Build request headers including auth if available."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def health_check(self) -> dict:
        """Check gateway health status."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/health",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            return response.json()

    async def send_message(
        self, session_id: str, message: str, surface: str = "cli"
    ) -> dict:
        """Send a message to the gateway.

        Args:
            session_id: Conversation session ID
            message: User message text
            surface: Client surface identifier (default: "cli")

        Returns:
            Gateway response dict
        """
        async with httpx.AsyncClient(timeout=180.0) as client:  # 3 min for full pipeline
            response = await client.post(
                f"{self.base_url}/gateway/message",
                headers=self._get_headers(),
                json={"session_id": session_id, "message": message, "surface": surface},
            )
            response.raise_for_status()
            return response.json()

    async def create_journey_direct(self, params: dict[str, Any]) -> dict:
        """Create a journey by calling the backend directly.

        This bypasses the gateway to avoid Railway timeout issues on long-running
        journey creation (~90 seconds).

        Args:
            params: Journey creation params including:
                - zip_codes: List of ZIP codes (optional if locations provided)
                - locations: List of location dicts with type, value, cluster_id (optional)
                - campaign_type: Campaign type (e.g., "aep_acquisition")
                - name: Journey name
                - user_id: User ID for ownership
                - created_from: Source identifier

        Returns:
            Journey creation response with nodes, edges, market_profile, etc.
        """
        # Build request body
        body: dict[str, Any] = {
            "campaign_type": params.get("campaign_type", "aep_acquisition"),
            "name": params.get("name", "New Journey"),
            "user_id": params.get("user_id"),
            "created_from": params.get("created_from", "cli"),
        }

        # Use locations if provided (for state/archetype targeting)
        if params.get("locations"):
            body["locations"] = params["locations"]
        elif params.get("zip_codes"):
            body["zip_codes"] = params["zip_codes"]

        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout
            response = await client.post(
                f"{BACKEND_URL}/journey/flowchart/create-v2",
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                json=body,
            )
            response.raise_for_status()
            return response.json()
