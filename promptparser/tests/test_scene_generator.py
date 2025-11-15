from app.services.scene_generator import generate_scenes


def test_generate_scenes_respects_duration():
    creative_direction = {"technical_specs": {"duration": 30}}
    scenes = generate_scenes(creative_direction)

    assert 3 <= len(scenes) <= 8
    total = sum(scene["duration"] for scene in scenes)
    assert abs(total - 30) < 0.5
    assert scenes[0]["purpose"] == "hook"
    assert scenes[-1]["purpose"] == "cta"
