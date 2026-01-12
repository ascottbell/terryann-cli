"""TerryAnn branded action words for status messages."""

import random
from enum import Enum

# All TerryAnn action words (from web UI)
ALL_ACTION_WORDS = [
    # Core grounding concepts
    "Grounding",
    "Anchoring",
    "Substantiating",
    "Validating",
    "Fortifying",
    # Building/construction metaphors
    "Building",
    "Constructing",
    "Architecting",
    "Assembling",
    "Crafting",
    # Analysis/reasoning
    "Reasoning",
    "Analyzing",
    "Synthesizing",
    "Connecting",
    "Deducing",
    # Verification/truth-seeking
    "Verifying",
    "Confirming",
    "Corroborating",
    "Authenticating",
    # Strategic/planning
    "Mapping",
    "Charting",
    "Calibrating",
    "Aligning",
    "Optimizing",
]


class MessageContext(str, Enum):
    """Context types for action word selection."""

    JOURNEY = "journey"
    SIMULATION = "simulation"
    OPTIMIZATION = "optimization"
    GENERAL = "general"


# Context-aware word preferences
CONTEXT_WORDS = {
    MessageContext.JOURNEY: [
        "Architecting",
        "Constructing",
        "Mapping",
        "Building",
        "Crafting",
        "Charting",
        "Assembling",
    ],
    MessageContext.SIMULATION: [
        "Analyzing",
        "Synthesizing",
        "Calibrating",
        "Simulating",
        "Modeling",
        "Reasoning",
        "Deducing",
    ],
    MessageContext.OPTIMIZATION: [
        "Optimizing",
        "Aligning",
        "Calibrating",
        "Refining",
        "Tuning",
        "Fortifying",
    ],
    MessageContext.GENERAL: [
        "Reasoning",
        "Connecting",
        "Grounding",
        "Analyzing",
        "Synthesizing",
        "Validating",
        "Anchoring",
    ],
}


def detect_context(message: str) -> MessageContext:
    """
    Detect the context from the user's message.

    Args:
        message: User's input message

    Returns:
        Detected context for action word selection
    """
    message_lower = message.lower()

    # Journey creation keywords
    journey_keywords = [
        "journey",
        "create",
        "build",
        "campaign",
        "touchpoint",
        "design",
        "plan",
    ]
    if any(kw in message_lower for kw in journey_keywords):
        return MessageContext.JOURNEY

    # Simulation keywords
    simulation_keywords = [
        "simulate",
        "simulation",
        "test",
        "run",
        "predict",
        "forecast",
        "model",
    ]
    if any(kw in message_lower for kw in simulation_keywords):
        return MessageContext.SIMULATION

    # Optimization keywords
    optimization_keywords = [
        "optimize",
        "improve",
        "better",
        "enhance",
        "refine",
        "tune",
        "adjust",
    ]
    if any(kw in message_lower for kw in optimization_keywords):
        return MessageContext.OPTIMIZATION

    return MessageContext.GENERAL


def get_action_words_for_context(context: MessageContext) -> list[str]:
    """
    Get shuffled action words appropriate for the context.

    Returns context-specific words first, then general words.

    Args:
        context: The detected message context

    Returns:
        List of action words, shuffled within priority groups
    """
    # Get context-specific words
    preferred = CONTEXT_WORDS.get(context, CONTEXT_WORDS[MessageContext.GENERAL]).copy()
    random.shuffle(preferred)

    # Get remaining words
    remaining = [w for w in ALL_ACTION_WORDS if w not in preferred]
    random.shuffle(remaining)

    return preferred + remaining
