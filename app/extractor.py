"""
Task extraction module.

Listens to meeting transcript segments and detects actionable items.
Extracted tasks are appended to PENDING_TASKS, which the HTTP endpoints
in app/server.py expose for approval/rejection.

Flow
----
1. ``run_task_extraction(transcript)`` is called from the Realtime pipeline
   whenever a speaker finishes a response.
2. ``_contains_action_keywords`` checks whether the text is worth processing.
3. ``_build_task`` constructs a task dict with a UUID and default status.
4. ``_store_task`` appends the task to ``PENDING_TASKS`` and logs it.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("bridge.extractor")

# ---------------------------------------------------------------------------
# Shared state — imported by server.py endpoints and the Realtime pipeline
# ---------------------------------------------------------------------------

PENDING_TASKS: List[Dict[str, Any]] = []

# ---------------------------------------------------------------------------
# Keyword detection
# ---------------------------------------------------------------------------

#: Words that signal an actionable item in the transcript.
_ACTION_KEYWORDS = {"send", "schedule", "book", "create", "follow up", "remind", "assign"}


def _contains_action_keywords(text: str) -> bool:
    """
    Return True if the transcript contains at least one action keyword.

    Uses a simple lowercase substring check. Swap this out for an embeddings-
    based classifier or regex when you need higher precision.
    """
    lowered = text.lower()
    return any(kw in lowered for kw in _ACTION_KEYWORDS)


# ---------------------------------------------------------------------------
# Task construction
# ---------------------------------------------------------------------------

def _build_task(transcript: str) -> Dict[str, Any]:
    """
    Create a task dict from a raw transcript segment.

    Parameters
    ----------
    transcript:
        The full sentence or turn that triggered extraction.

    Returns
    -------
    dict with keys: id, title, description, status, category.
    """
    return {
        "id": str(uuid.uuid4())[:8],
        "title": f"Action Item: {transcript[:50].strip()}{'...' if len(transcript) > 50 else ''}",
        "description": transcript,
        "status": "pending",
        "category": "ticket",
    }


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def _store_task(task: Dict[str, Any]) -> None:
    """Append task to the global list and emit an info log."""
    PENDING_TASKS.append(task)
    logger.info("Task extracted: [%s] %s", task["id"], task["title"])


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_task_extraction(transcript: str) -> Optional[List[Dict[str, Any]]]:
    """
    Analyse a transcript segment and extract actionable tasks.

    Called by ``RealtimeMeetingBridge._pump_model_events`` whenever a
    response turn completes. Non-blocking — errors are caught so the
    caller's audio pump is never interrupted.

    Parameters
    ----------
    transcript:
        A single completed speaker turn from the meeting.

    Returns
    -------
    List of newly created task dicts, or None if nothing was extracted.

    Notes
    -----
    The current implementation uses keyword matching as a stand-in for LLM
    extraction. To upgrade, replace ``_contains_action_keywords`` with a
    call to GPT-4o (or similar) and ``_build_task`` with whatever structured
    output schema the model returns.
    """
    if not transcript.strip():
        return None

    try:
        if not _contains_action_keywords(transcript):
            return None

        task = _build_task(transcript)
        _store_task(task)
        return [task]

    except Exception as e:
        logger.error("Extraction failed for transcript %r: %s", transcript[:60], e)
        return None
