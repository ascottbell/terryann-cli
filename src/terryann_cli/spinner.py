"""Rotating status spinner with TerryAnn branded messages."""

import asyncio
from typing import Any, Coroutine

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from terryann_cli.action_words import (
    MessageContext,
    detect_context,
    get_action_words_for_context,
)

# TerryAnn brand colors
CORAL = "#c4785a"
BLUE = "#b8d4e3"
DIM = "#888888"


class RotatingStatus:
    """
    A status spinner that rotates through branded action words.

    Uses Rich's Live display with a spinner and rotating message text.
    """

    def __init__(
        self,
        console: Console,
        context: MessageContext = MessageContext.GENERAL,
        interval: float = 2.5,
    ):
        """
        Initialize the rotating status.

        Args:
            console: Rich console to display on
            context: Context for action word selection
            interval: Seconds between message changes
        """
        self.console = console
        self.context = context
        self.interval = interval
        self.words = get_action_words_for_context(context)
        self.word_index = 0
        self._stop_event = asyncio.Event()

    def _get_renderable(self) -> Text:
        """Build the current spinner + message renderable."""
        word = self.words[self.word_index % len(self.words)]
        text = Text()
        text.append("  ")
        text.append(f"{word}...", style=DIM)
        return text

    async def _rotate_words(self, live: Live) -> None:
        """Background task to rotate words."""
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.interval,
                )
            except asyncio.TimeoutError:
                # Timeout means we should rotate
                self.word_index += 1
                live.update(self._get_renderable())

    async def run_with_status(
        self,
        coro: Coroutine[Any, Any, Any],
    ) -> Any:
        """
        Run a coroutine while displaying the rotating status.

        Args:
            coro: The coroutine to run (e.g., API call)

        Returns:
            The result of the coroutine
        """
        self._stop_event.clear()
        self.word_index = 0

        # Use Rich's Live display with spinner
        spinner = Spinner("dots", text=self._get_renderable(), style=CORAL)

        with Live(
            spinner,
            console=self.console,
            refresh_per_second=10,
            transient=True,
        ) as live:
            # Create rotation task
            rotate_task = asyncio.create_task(self._rotate_words_with_spinner(live, spinner))

            try:
                # Run the actual work
                result = await coro
                return result
            finally:
                # Stop rotation
                self._stop_event.set()
                rotate_task.cancel()
                try:
                    await rotate_task
                except asyncio.CancelledError:
                    pass

    async def _rotate_words_with_spinner(self, live: Live, spinner: Spinner) -> None:
        """Background task to rotate words with spinner."""
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.interval,
                )
            except asyncio.TimeoutError:
                # Timeout means we should rotate
                self.word_index += 1
                word = self.words[self.word_index % len(self.words)]
                spinner.update(text=Text(f"  {word}...", style=DIM))
                live.update(spinner)


async def run_with_rotating_status(
    console: Console,
    coro: Coroutine[Any, Any, Any],
    message: str = "",
) -> Any:
    """
    Convenience function to run a coroutine with rotating status.

    Args:
        console: Rich console
        coro: Coroutine to run
        message: User message for context detection

    Returns:
        Result of the coroutine
    """
    context = detect_context(message) if message else MessageContext.GENERAL
    spinner = RotatingStatus(console, context=context)
    return await spinner.run_with_status(coro)
