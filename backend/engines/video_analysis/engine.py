"""Video analysis engine."""
from backend.core.engine import BaseGenerationEngine
from backend.engines.video_analysis.models import VideoAnalysisRequest, VideoAnalysisResponse
from backend.engines.video_analysis.repository import VideoAnalysisRepository
from backend.engines.video_analysis.providers.replicate import ReplicateVideoAnalysisProvider


class VideoAnalysisEngine(BaseGenerationEngine[VideoAnalysisRequest, VideoAnalysisResponse]):
    """Engine for video analysis tasks."""

    def __init__(self, db_path: str, replicate_api_key: str):
        repository = VideoAnalysisRepository(db_path)
        provider = ReplicateVideoAnalysisProvider(replicate_api_key)
        super().__init__(repository, provider)
