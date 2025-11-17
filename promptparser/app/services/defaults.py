"""Smart defaults for creative direction."""

from __future__ import annotations

from typing import Any, Dict

PLATFORM_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "instagram": {
        "aspect_ratio": "9:16",
        "duration": 30,
        "fps": 30,
        "pacing": "moderate",
        "cuts_per_minute": 12,
    },
    "tiktok": {
        "aspect_ratio": "9:16",
        "duration": 15,
        "fps": 30,
        "pacing": "fast",
        "cuts_per_minute": 20,
    },
    "youtube": {
        "aspect_ratio": "16:9",
        "duration": 30,
        "fps": 30,
        "pacing": "moderate",
        "cuts_per_minute": 10,
    },
}

CATEGORY_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "luxury": {
        "pacing": "slow",
        "transition_style": "dissolve",
        "lighting_style": "dramatic_soft",
        "music_genre": "classical",
    },
    "tech": {
        "pacing": "dynamic",
        "transition_style": "cut",
        "lighting_style": "clean_studio",
        "music_genre": "electronic",
    },
    "fitness": {
        "pacing": "fast",
        "transition_style": "cut",
        "lighting_style": "high_contrast",
        "music_genre": "edm",
    },
}


def detect_category(parsed_prompt: dict) -> str | None:
    product = (parsed_prompt.get("product") or "").lower()
    keywords = parsed_prompt.get("aesthetic_keywords", [])
    if "luxury" in keywords or "luxury" in product:
        return "luxury"
    if any(k in product for k in ["tech", "app", "software"]):
        return "tech"
    if any(k in product for k in ["fitness", "gym", "athletic"]):
        return "fitness"
    return None


def apply_smart_defaults(parsed_prompt: dict) -> Dict[str, Any]:
    platform = parsed_prompt.get("platform")
    platform_defaults = PLATFORM_DEFAULTS.get(platform or "", {})
    category = detect_category(parsed_prompt)
    category_defaults = CATEGORY_DEFAULTS.get(category or "", {})

    defaults = {
        "technical_specs": {
            "duration": parsed_prompt.get("duration") or platform_defaults.get("duration", 30),
            "aspect_ratio": platform_defaults.get("aspect_ratio", "9:16"),
            "platform": platform or "instagram",
            "fps": platform_defaults.get("fps", 30),
        },
        "pacing": {
            "overall": category_defaults.get("pacing", platform_defaults.get("pacing", "moderate")),
            "cuts_per_minute": platform_defaults.get("cuts_per_minute", 12),
            "transition_style": category_defaults.get("transition_style", "cut"),
        },
        "audio_direction": {
            "music_genre": category_defaults.get("music_genre", "electronic"),
        },
        "metadata": {
            "defaults_used": [],
        },
    }

    for section, values in defaults.items():
        if section == "metadata":
            continue
        for key, value in values.items():
            if parsed_prompt.get(section, {}).get(key) is None:
                defaults["metadata"]["defaults_used"].append(f"{section}.{key}")

    defaults["category"] = category
    return defaults
