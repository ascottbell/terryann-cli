"""Logging configuration for TerryAnn CLI."""

import logging
import sys

# Create a logger for the package
logger = logging.getLogger("terryann")

# Track if debug mode is enabled
_debug_enabled = False


def enable_debug():
    """Enable debug logging to stderr."""
    global _debug_enabled
    _debug_enabled = True

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(levelname)s] %(name)s: %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled")


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled."""
    return _debug_enabled
