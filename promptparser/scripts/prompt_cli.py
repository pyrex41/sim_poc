#!/usr/bin/env python
"""Simple CLI to send a text prompt to the Prompt Parser API."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send a text prompt to the Prompt Parser API and print the creative_direction."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Prompt text to parse (omit to read from stdin).",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("PROMPT_PARSER_BASE_URL", "http://127.0.0.1:8080"),
        help="Base URL of the Prompt Parser API (default: %(default)s).",
    )
    parser.add_argument(
        "--include-cost",
        action="store_true",
        help="Request fallback cost estimates when available.",
    )
    return parser


def read_prompt(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    print("Enter prompt text (end with Ctrl+D / Ctrl+Z):", file=sys.stderr)
    return sys.stdin.read().strip()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    prompt_text = read_prompt(args)
    if not prompt_text:
        parser.error("Prompt text is required (provide as an argument or via stdin).")

    payload: dict[str, Any] = {
        "prompt": {"text": prompt_text},
        "options": {"include_cost_estimate": args.include_cost, "cost_fallback_enabled": True},
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(f"{args.base_url.rstrip('/')}/v1/parse", json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        print(f"[prompt-cli] Request failed: {exc}", file=sys.stderr)
        return 1

    data = response.json()
    creative_direction = data.get("creative_direction")
    if not creative_direction:
        print(json.dumps(data, indent=2))
        return 0

    print(json.dumps(creative_direction, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

