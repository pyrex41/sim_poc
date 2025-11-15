from app.services.defaults import apply_smart_defaults, detect_category


def test_detect_category_luxury():
    parsed = {"product": "luxury handbags", "aesthetic_keywords": ["luxury"]}
    assert detect_category(parsed) == "luxury"


def test_apply_smart_defaults_uses_platform():
    parsed = {"platform": "instagram", "duration": None}
    defaults = apply_smart_defaults(parsed)

    assert defaults["technical_specs"]["duration"] == 30
    assert defaults["technical_specs"]["aspect_ratio"] == "9:16"
    assert "technical_specs.duration" in defaults["metadata"]["defaults_used"]


def test_apply_smart_defaults_detects_category():
    parsed = {"platform": "youtube", "product": "fitness tracker"}
    defaults = apply_smart_defaults(parsed)
    assert defaults["category"] == "fitness"
    assert defaults["pacing"]["overall"] == "fast"
