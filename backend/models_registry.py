"""
Model Registry for Replicate Models

This registry allows easy addition of any Replicate model across different categories.
Each model can have its own input schema and output formats.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ModelCategory(str, Enum):
    """High-level model categories."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    UTILITIES = "utilities"
    PROMPT = "prompt"
    VIDEO_ANALYSIS = "video_analysis"  # Video to text (captioning, description)


@dataclass
class ModelConfig:
    """Configuration for a Replicate model."""

    # Basic info
    identifier: str  # e.g., "black-forest-labs/flux-schnell"
    version: Optional[str] = None  # Specific version hash (optional, uses latest if None)
    category: ModelCategory = ModelCategory.IMAGE

    # Metadata
    name: str = ""
    description: str = ""

    # Input schema hints (for validation and UI generation)
    required_inputs: List[str] = None
    optional_inputs: List[str] = None
    input_schema: Dict[str, Any] = None  # Full schema if available

    # Output info
    output_type: str = "url"  # url, urls, json, etc.

    def __post_init__(self):
        if self.required_inputs is None:
            self.required_inputs = []
        if self.optional_inputs is None:
            self.optional_inputs = []
        if self.input_schema is None:
            self.input_schema = {}


class ModelRegistry:
    """Central registry for all Replicate models."""

    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self._load_default_models()

    def _load_default_models(self):
        """Load default model configurations."""

        # ==================== IMAGE MODELS ====================
        self.register(ModelConfig(
            identifier="black-forest-labs/flux-schnell",
            version="c846a69991daf4c0e5d016514849d14ee5b2e6846ce6b9d6f21369e564cfe51e",
            category=ModelCategory.IMAGE,
            name="Flux Schnell",
            description="Fast high-quality image generation",
            required_inputs=["prompt"],
            optional_inputs=["aspect_ratio", "num_outputs", "seed", "go_fast", "megapixels", "output_format", "output_quality"],
        ))

        self.register(ModelConfig(
            identifier="black-forest-labs/flux-pro",
            category=ModelCategory.IMAGE,
            name="Flux Pro",
            description="Professional image generation with more control",
            required_inputs=["prompt"],
            optional_inputs=["aspect_ratio", "num_outputs", "seed", "guidance", "steps", "interval"],
        ))

        self.register(ModelConfig(
            identifier="stability-ai/sdxl",
            category=ModelCategory.IMAGE,
            name="Stable Diffusion XL",
            description="Open source image generation",
            required_inputs=["prompt"],
            optional_inputs=["negative_prompt", "width", "height", "num_outputs", "guidance_scale", "num_inference_steps", "seed"],
        ))

        # ==================== VIDEO MODELS ====================
        self.register(ModelConfig(
            identifier="minimax/video-01",
            category=ModelCategory.VIDEO,
            name="MiniMax Video-01",
            description="Text or image to video generation",
            required_inputs=["prompt"],
            optional_inputs=["first_frame_image", "prompt_optimizer"],
        ))

        self.register(ModelConfig(
            identifier="luma/ray",
            category=ModelCategory.VIDEO,
            name="Luma Ray",
            description="High-quality text/image to video",
            required_inputs=["prompt"],
            optional_inputs=["image", "loop", "duration"],
        ))

        self.register(ModelConfig(
            identifier="fofr/skyreels-2",
            category=ModelCategory.VIDEO,
            name="SkyReels 2",
            description="Stitch images into video",
            required_inputs=["images"],
            optional_inputs=["fps", "duration"],
        ))

        # ==================== AUDIO MODELS ====================
        self.register(ModelConfig(
            identifier="meta/musicgen",
            category=ModelCategory.AUDIO,
            name="MusicGen",
            description="Generate music from text prompts",
            required_inputs=["prompt"],
            optional_inputs=["model_version", "duration", "temperature", "top_k", "top_p", "seed"],
        ))

        self.register(ModelConfig(
            identifier="suno-ai/bark",
            category=ModelCategory.AUDIO,
            name="Bark",
            description="Text to speech and sound effects",
            required_inputs=["prompt"],
            optional_inputs=["text_temp", "waveform_temp"],
        ))

        # ==================== UTILITIES ====================
        self.register(ModelConfig(
            identifier="philz1337x/clarity-upscaler",
            category=ModelCategory.UTILITIES,
            name="Clarity Upscaler",
            description="AI image upscaling and enhancement",
            required_inputs=["image"],
            optional_inputs=["scale", "dynamic", "sharpen", "creativity", "resemblance", "sd_model"],
        ))

        self.register(ModelConfig(
            identifier="cjwbw/rembg",
            category=ModelCategory.UTILITIES,
            name="Background Removal",
            description="Remove background from images",
            required_inputs=["image"],
            optional_inputs=["model", "return_mask"],
        ))

        self.register(ModelConfig(
            identifier="tencentarc/gfpgan",
            category=ModelCategory.UTILITIES,
            name="Face Restoration",
            description="Restore and enhance faces in images",
            required_inputs=["image"],
            optional_inputs=["scale", "version"],
        ))

        # ==================== VIDEO ANALYSIS (VIDEO TO TEXT) ====================
        self.register(ModelConfig(
            identifier="lucataco/qwen2-vl-7b-instruct",
            category=ModelCategory.VIDEO_ANALYSIS,
            name="Qwen2-VL 7B",
            description="Visual understanding and video captioning",
            required_inputs=["video"],
            optional_inputs=["prompt", "max_tokens", "temperature", "top_p"],
            output_type="text",
        ))

        self.register(ModelConfig(
            identifier="shreejalmaharjan-27/tiktok-short-captions",
            category=ModelCategory.VIDEO_ANALYSIS,
            name="TikTok Captions",
            description="Generate TikTok-style captions with Whisper",
            required_inputs=["video"],
            optional_inputs=["font", "fontsize", "color"],
            output_type="video_with_captions",
        ))

        self.register(ModelConfig(
            identifier="fictions-ai/autocaption",
            category=ModelCategory.VIDEO_ANALYSIS,
            name="Auto Caption",
            description="Automatically add captions to video",
            required_inputs=["video"],
            optional_inputs=["font", "font_size", "font_color", "stroke_width"],
            output_type="video_with_captions",
        ))

        self.register(ModelConfig(
            identifier="chenxwh/cogvlm2-video",
            category=ModelCategory.VIDEO_ANALYSIS,
            name="CogVLM2 Video",
            description="Vision-language model for video analysis",
            required_inputs=["video"],
            optional_inputs=["prompt", "num_beams", "max_new_tokens", "temperature"],
            output_type="text",
        ))

        self.register(ModelConfig(
            identifier="lucataco/apollo-7b",
            category=ModelCategory.VIDEO_ANALYSIS,
            name="Apollo 7B",
            description="Advanced video understanding for complex scenes",
            required_inputs=["video"],
            optional_inputs=["prompt", "max_tokens", "temperature"],
            output_type="text",
        ))

    def register(self, model: ModelConfig, alias: Optional[str] = None):
        """
        Register a model in the registry.

        Args:
            model: ModelConfig to register
            alias: Optional short alias (e.g., "flux" for "black-forest-labs/flux-schnell")
        """
        # Store by full identifier
        self.models[model.identifier] = model

        # Store by alias if provided
        if alias:
            self.models[alias] = model

        # Auto-create alias from last part of identifier
        if "/" in model.identifier:
            short_name = model.identifier.split("/")[-1]
            if short_name not in self.models:
                self.models[short_name] = model

    def get(self, model_id: str) -> Optional[ModelConfig]:
        """Get model config by ID or alias."""
        return self.models.get(model_id)

    def list_by_category(self, category: ModelCategory) -> List[ModelConfig]:
        """List all models in a category."""
        seen = set()
        result = []
        for model in self.models.values():
            if model.category == category and model.identifier not in seen:
                seen.add(model.identifier)
                result.append(model)
        return result

    def list_all(self) -> List[ModelConfig]:
        """List all unique models."""
        seen = set()
        result = []
        for model in self.models.values():
            if model.identifier not in seen:
                seen.add(model.identifier)
                result.append(model)
        return result

    def add_custom_model(
        self,
        identifier: str,
        category: ModelCategory,
        name: str = "",
        description: str = "",
        version: Optional[str] = None,
        required_inputs: List[str] = None,
        optional_inputs: List[str] = None,
        alias: Optional[str] = None
    ):
        """
        Easily add a custom model at runtime.

        Example:
            registry.add_custom_model(
                identifier="someuser/cool-model",
                category=ModelCategory.IMAGE,
                name="Cool Model",
                required_inputs=["prompt"],
                optional_inputs=["style", "strength"],
                alias="cool"
            )
        """
        model = ModelConfig(
            identifier=identifier,
            version=version,
            category=category,
            name=name or identifier,
            description=description,
            required_inputs=required_inputs or [],
            optional_inputs=optional_inputs or [],
        )
        self.register(model, alias=alias)


# Global registry instance
_registry = None


def get_model_registry() -> ModelRegistry:
    """Get the global model registry instance."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
