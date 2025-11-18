"""Replicate provider for video analysis."""
import replicate
from typing import Dict, Any
from backend.core.providers import BaseProvider
from backend.engines.video_analysis.models import VideoAnalysisRequest, VideoAnalysisResponse
from backend.models_registry import get_model_registry


class ReplicateVideoAnalysisProvider(BaseProvider[VideoAnalysisRequest, VideoAnalysisResponse]):
    """Replicate provider for video analysis."""

    def __init__(self, api_key: str):
        self.client = replicate.Client(api_token=api_key)
        self.registry = get_model_registry()

    def _build_input(self, request: VideoAnalysisRequest) -> Dict[str, Any]:
        """Build input dict for Replicate API."""
        input_data = {
            "video": request.video,
        }

        # Add prompt if provided
        if request.prompt:
            input_data["prompt"] = request.prompt

        # Add generation parameters
        if request.max_tokens is not None:
            input_data["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            input_data["temperature"] = request.temperature
        if request.top_p is not None:
            input_data["top_p"] = request.top_p

        # Add caption overlay parameters
        if request.font is not None:
            input_data["font"] = request.font
        if request.font_size is not None:
            input_data["fontsize"] = request.font_size
            input_data["font_size"] = request.font_size  # Different models use different names
        if request.font_color is not None:
            input_data["color"] = request.font_color
            input_data["font_color"] = request.font_color
        if request.stroke_width is not None:
            input_data["stroke_width"] = request.stroke_width

        return input_data

    async def submit(self, request: VideoAnalysisRequest) -> str:
        """Submit video analysis task to Replicate."""
        model_config = self.registry.get(request.model)
        if not model_config:
            raise ValueError(f"Unknown model: {request.model}")

        input_data = self._build_input(request)

        # Use version if available, otherwise use identifier
        model_ref = f"{model_config.identifier}:{model_config.version}" if model_config.version else model_config.identifier

        # Submit prediction
        prediction = self.client.predictions.create(
            model=model_ref if ":" in model_ref else None,
            version=model_config.version if model_config.version and ":" not in model_ref else None,
            input=input_data
        )

        return prediction.id

    async def get_result(self, task_id: str) -> VideoAnalysisResponse:
        """Get video analysis result from Replicate."""
        prediction = self.client.predictions.get(task_id)

        if prediction.status == "succeeded":
            output = prediction.output

            # Handle different output formats
            if isinstance(output, str):
                # Could be text description or video URL
                if output.startswith("http"):
                    return VideoAnalysisResponse(
                        task_id=task_id,
                        status="completed",
                        video_url=output
                    )
                else:
                    return VideoAnalysisResponse(
                        task_id=task_id,
                        status="completed",
                        text=output
                    )
            elif isinstance(output, list) and len(output) > 0:
                # Some models return list
                first_item = output[0]
                if isinstance(first_item, str) and first_item.startswith("http"):
                    return VideoAnalysisResponse(
                        task_id=task_id,
                        status="completed",
                        video_url=first_item
                    )
                else:
                    return VideoAnalysisResponse(
                        task_id=task_id,
                        status="completed",
                        text=str(first_item)
                    )
            elif isinstance(output, dict):
                # Handle dict output
                return VideoAnalysisResponse(
                    task_id=task_id,
                    status="completed",
                    text=output.get("text"),
                    video_url=output.get("video_url") or output.get("url")
                )
            else:
                return VideoAnalysisResponse(
                    task_id=task_id,
                    status="completed",
                    text=str(output)
                )

        elif prediction.status == "failed":
            return VideoAnalysisResponse(
                task_id=task_id,
                status="failed",
                error=prediction.error or "Analysis failed"
            )

        else:
            return VideoAnalysisResponse(
                task_id=task_id,
                status="processing"
            )

    async def cancel(self, task_id: str) -> bool:
        """Cancel video analysis task."""
        try:
            self.client.predictions.cancel(task_id)
            return True
        except Exception:
            return False
