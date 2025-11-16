"""Response models."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class SceneVisual(BaseModel):
    shot_type: Optional[str] = None
    subject: Optional[str] = None
    generation_prompt: Optional[str] = None


class Scene(BaseModel):
    id: str
    scene_number: int
    purpose: str
    duration: float
    visual: SceneVisual


class Metadata(BaseModel):
    cache_hit: bool = False
    defaults_used: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    confidence_breakdown: Optional[dict[str, float]] = None
    llm_provider_used: Optional[str] = None
    auto_generated_scene: Optional[dict[str, Any]] = None


class ParseResponse(BaseModel):
    status: str = "success"
    creative_direction: dict[str, Any]
    scenes: List[Scene]
    metadata: Metadata
    cost_estimate: Optional[dict[str, Any]] = None
    extracted_references: Optional[dict[str, Any]] = None
