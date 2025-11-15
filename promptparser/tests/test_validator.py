from app.services.validator import calculate_confidence, validate_scenes


def test_validate_scenes_warns_on_duration():
    creative_direction = {"technical_specs": {"duration": 30}}
    scenes = [{"scene_number": 1, "purpose": "cta", "duration": 1}]
    warnings = validate_scenes(creative_direction, scenes)
    assert any("timing" in warning.lower() for warning in warnings)


def test_calculate_confidence_changes_with_warnings():
    parsed = {"product": "Coffee", "aesthetic_keywords": ["bold"]}
    scenes = [{"scene_number": 1, "duration": 5, "purpose": "hook"}]
    warnings = []
    confidence = calculate_confidence(parsed, scenes, warnings)
    assert confidence["confidence_score"] > 0.6

    warnings = ["issue"]
    lowered = calculate_confidence(parsed, scenes, warnings)
    assert lowered["confidence_score"] < confidence["confidence_score"]
