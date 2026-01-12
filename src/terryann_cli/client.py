"""HTTP client for TerryAnn Gateway."""

import httpx

from terryann_cli.config import Config


class GatewayClient:
    """Async HTTP client for TerryAnn Gateway."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.gateway_url.rstrip("/")

    async def health_check(self) -> dict:
        """Check gateway health status."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.base_url}/health")
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
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/gateway/message",
                json={"session_id": session_id, "message": message, "surface": surface},
            )
            response.raise_for_status()
            return response.json()
