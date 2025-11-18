"""Repository for video analysis tasks."""
from backend.core.repository import BaseRepository


class VideoAnalysisRepository(BaseRepository):
    """Repository for video analysis operations."""

    def __init__(self, db_path: str):
        super().__init__(db_path, task_type="video_analysis")
