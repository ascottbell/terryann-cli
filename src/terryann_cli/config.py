"""Configuration management for TerryAnn CLI."""

import os
import sys
from pathlib import Path
from dataclasses import dataclass

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


DEFAULT_GATEWAY_URL = "https://terryann-core-production.up.railway.app"
CONFIG_DIR = Path.home() / ".terryann"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass
class Config:
    """TerryAnn CLI configuration."""

    gateway_url: str = DEFAULT_GATEWAY_URL


def load_config() -> Config:
    """Load configuration from env var or config file.

    Priority:
    1. TERRYANN_GATEWAY_URL environment variable
    2. ~/.terryann/config.toml
    3. Default value
    """
    gateway_url = DEFAULT_GATEWAY_URL

    # Try config file first
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
            gateway_url = data.get("gateway", {}).get("url", DEFAULT_GATEWAY_URL)

    # Env var takes precedence
    gateway_url = os.environ.get("TERRYANN_GATEWAY_URL", gateway_url)

    return Config(gateway_url=gateway_url)
