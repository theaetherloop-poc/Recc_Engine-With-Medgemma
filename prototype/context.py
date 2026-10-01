"""Shared patient context for the prototype.

run.py computes the patient context ONCE (by running the existing rule-based
preprocessing) and stores it here. The CrewAI tools read from this module-level
holder instead of taking constructor args — simplest robust pattern for a
prototype.
"""
from typing import Any, Dict, Optional

# Populated by run.py before the agent kicks off.
CTX: Dict[str, Any] = {}


def set_context(ctx: Dict[str, Any]) -> None:
    global CTX
    CTX = ctx


def get(key: str, default: Optional[Any] = None) -> Any:
    return CTX.get(key, default)
