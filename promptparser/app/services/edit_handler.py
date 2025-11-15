"""Iterative editing helper."""

from __future__ import annotations

import copy
from typing import Any, Dict


def merge_iterative_edit(previous_config: Dict[str, Any], new_prompt: str) -> Dict[str, Any]:
    """Stub: merge user instructions into previous config."""
    config = copy.deepcopy(previous_config)
    notes = config.setdefault("metadata", {}).setdefault("iteration_notes", [])
    notes.append(f"Applied edit: {new_prompt}")
    return config

