"""
Validation utilities – sanitise and validate all incoming data before
it reaches business logic or the AI service.
"""

import html
import re
import unicodedata
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_MESSAGE_LENGTH = 500          # Characters
MAX_HISTORY_TURNS = 10            # Chat turns kept per session
ALLOWED_LANGUAGES = {"en", "hi"}  # ISO 639-1 codes
_INJECTION_PATTERN = re.compile(
    r"(ignore\s+previous|forget\s+instructions|system\s*prompt|you\s+are\s+now)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public validators
# ---------------------------------------------------------------------------

def sanitize_message(raw: str) -> str:
    """
    Sanitise user input:
    1. Normalise unicode (NFKC).
    2. HTML-escape special characters.
    3. Strip leading/trailing whitespace.
    4. Truncate to MAX_MESSAGE_LENGTH.
    """
    normalised = unicodedata.normalize("NFKC", raw)
    escaped = html.escape(normalised, quote=False)
    stripped = escaped.strip()
    return stripped[:MAX_MESSAGE_LENGTH]


def validate_message(message: str) -> tuple[bool, str]:
    """
    Validate a sanitised user message.

    Returns:
        (is_valid, error_message)
    """
    if not message:
        return False, "Message cannot be empty."
    if len(message) < 2:
        return False, "Message is too short."
    if len(message) > MAX_MESSAGE_LENGTH:
        return False, f"Message exceeds {MAX_MESSAGE_LENGTH} characters."
    if _INJECTION_PATTERN.search(message):
        return False, "Message contains disallowed content."
    return True, ""


def validate_language(lang: str) -> tuple[bool, str]:
    """Validate the requested language code."""
    if lang not in ALLOWED_LANGUAGES:
        return False, f"Language '{lang}' is not supported. Use one of: {', '.join(ALLOWED_LANGUAGES)}."
    return True, ""


def validate_chat_history(history: Any) -> tuple[bool, str]:
    """
    Validate the chat history payload from the client.
    Must be a list of {role, content} dicts, max MAX_HISTORY_TURNS entries.
    """
    if not isinstance(history, list):
        return False, "chat_history must be an array."
    if len(history) > MAX_HISTORY_TURNS:
        return False, f"chat_history exceeds maximum of {MAX_HISTORY_TURNS} turns."
    for turn in history:
        if not isinstance(turn, dict):
            return False, "Each history entry must be an object."
        if turn.get("role") not in ("user", "assistant"):
            return False, "History role must be 'user' or 'assistant'."
        if not isinstance(turn.get("content"), str):
            return False, "History content must be a string."
        if len(turn["content"]) > MAX_MESSAGE_LENGTH:
            return False, "A history entry exceeds maximum length."
    return True, ""
