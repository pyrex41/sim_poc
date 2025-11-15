"""Text prompt parsing utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


DURATION_PATTERN = re.compile(r"(?P<value>\d+)\s*(seconds?|secs?|s|minutes?|mins?|m)")
PLATFORM_KEYWORDS = {
    "instagram": ["instagram", "reels"],
    "tiktok": ["tiktok"],
    "youtube": ["youtube"],
    "facebook": ["facebook"],
}


@dataclass
class ParsedPrompt:
    duration: Optional[int] = None
    platform: Optional[str] = None
    product: Optional[str] = None
    aesthetic_keywords: List[str] = field(default_factory=list)
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            "duration": self.duration,
            "platform": self.platform,
            "product": self.product,
            "aesthetic_keywords": self.aesthetic_keywords,
        }


def extract_duration(text: str) -> Optional[int]:
    match = DURATION_PATTERN.search(text.lower())
    if not match:
        return None
    value = int(match.group("value"))
    unit = match.group(0)
    if "min" in unit:
        return value * 60
    return value


def extract_platform(text: str) -> Optional[str]:
    lower = text.lower()
    for platform, keywords in PLATFORM_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            return platform
    return None


def extract_product(text: str) -> Optional[str]:
    match = re.search(r"ad for (?P<product>[a-zA-Z\s]+)", text.lower())
    if match:
        product = match.group("product").strip()
        return product.title()
    return None


def extract_aesthetic_keywords(text: str) -> List[str]:
    keywords = []
    for token in re.findall(r"[a-zA-Z]+", text.lower()):
        if token in {"luxury", "energetic", "minimal", "modern", "bold", "calm"}:
            keywords.append(token)
    return keywords


def parse_text_prompt(text: str) -> ParsedPrompt:
    parsed = ParsedPrompt(
        duration=extract_duration(text),
        platform=extract_platform(text),
        product=extract_product(text),
        aesthetic_keywords=extract_aesthetic_keywords(text),
        raw_text=text,
    )
    return parsed
