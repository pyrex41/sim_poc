from app.services.parsers.text_parser import (
    ParsedPrompt,
    extract_aesthetic_keywords,
    extract_duration,
    extract_platform,
    parse_text_prompt,
)


def test_extract_duration_seconds():
    assert extract_duration("30 sec video") == 30


def test_extract_duration_minutes():
    assert extract_duration("1 minute ad") == 60


def test_extract_platform():
    assert extract_platform("Instagram Reels spot") == "instagram"
    assert extract_platform("unknown platform") is None


def test_parse_text_prompt_fields():
    parsed = parse_text_prompt("30 second Instagram ad for luxury watches")
    assert parsed.duration == 30
    assert parsed.platform == "instagram"
    assert "luxury" in parsed.aesthetic_keywords


def test_extract_aesthetic_keywords():
    assert extract_aesthetic_keywords("bold energetic modern ad") == ["bold", "energetic", "modern"]
