"""
Base classes for Luigi campaign pipeline tasks.

Provides common functionality for all pipeline tasks including:
- State management in database
- Async operation support
- Error handling and logging
"""

import luigi
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class CampaignStateTarget(luigi.Target):
    """
    Custom Target that stores task completion state in database.

    This allows Luigi to track which tasks have completed and supports
    resuming from failures.
    """

    def __init__(self, job_id: int, task_name: str):
        self.job_id = job_id
        self.task_name = task_name

    def exists(self) -> bool:
        """Check if this task has already completed."""
        from ..database import get_db

        with get_db() as conn:
            row = conn.execute(
                """
                SELECT 1 FROM luigi_task_state
                WHERE job_id = ? AND task_name = ?
                AND status = 'completed'
                """,
                (self.job_id, self.task_name),
            ).fetchone()

            return row is not None

    def mark_complete(self, output_data: Optional[Dict[str, Any]] = None):
        """Mark this task as completed."""
        from ..database import get_db

        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO luigi_task_state
                (task_id, job_id, task_name, status, output_data, completed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    f"{self.job_id}_{self.task_name}",
                    self.job_id,
                    self.task_name,
                    "completed",
                    json.dumps(output_data) if output_data else None,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

    def get_output_data(self) -> Optional[Dict[str, Any]]:
        """Retrieve output data from completed task."""
        from ..database import get_db

        with get_db() as conn:
            row = conn.execute(
                """
                SELECT output_data FROM luigi_task_state
                WHERE job_id = ? AND task_name = ?
                AND status = 'completed'
                """,
                (self.job_id, self.task_name),
            ).fetchone()

            if row and row["output_data"]:
                return json.loads(row["output_data"])
            return None


class CampaignPipelineTask(luigi.Task):
    """
    Base class for all campaign pipeline tasks.

    Provides common parameters and helper methods for pipeline tasks.
    """

    job_id = luigi.IntParameter(description="Parent job ID")
    campaign_id = luigi.Parameter(description="Campaign ID")

    def output(self):
        """
        Return the Target that marks this task's completion.

        Override this in subclasses if you need custom Target behavior.
        """
        return CampaignStateTarget(self.job_id, self.__class__.__name__)

    def get_output_data(self) -> Optional[Dict[str, Any]]:
        """Get output data from this task if it's already completed."""
        target = self.output()
        if isinstance(target, CampaignStateTarget):
            return target.get_output_data()
        return None

    def mark_complete(self, output_data: Optional[Dict[str, Any]] = None):
        """Mark this task as completed with optional output data."""
        target = self.output()
        if isinstance(target, CampaignStateTarget):
            target.mark_complete(output_data)

    def update_job_status(self, status: str, **metadata):
        """Update the main job status in database."""
        from ..database import update_video_status

        update_video_status(self.job_id, status, metadata=metadata)
        logger.info(f"Updated job {self.job_id} status to: {status}")

    def log_task_start(self):
        """Log when task starts."""
        from ..database import get_db

        task_id = f"{self.job_id}_{self.__class__.__name__}"

        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO luigi_task_state
                (task_id, job_id, task_name, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    self.job_id,
                    self.__class__.__name__,
                    "running",
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

        logger.info(f"Started task: {self.__class__.__name__} for job {self.job_id}")

    def log_task_failure(self, error: Exception):
        """Log when task fails."""
        from ..database import get_db

        task_id = f"{self.job_id}_{self.__class__.__name__}"

        with get_db() as conn:
            conn.execute(
                """
                UPDATE luigi_task_state
                SET status = ?, output_data = ?
                WHERE task_id = ?
                """,
                (
                    "failed",
                    json.dumps({"error": str(error)}),
                    task_id,
                ),
            )
            conn.commit()

        logger.error(
            f"Task {self.__class__.__name__} failed for job {self.job_id}: {error}"
        )

    def on_failure(self, exception):
        """Called when task fails."""
        self.log_task_failure(exception)
        super().on_failure(exception)


class AsyncCampaignTask(CampaignPipelineTask):
    """
    Base class for tasks that need to run async operations.

    Wraps async operations to work with Luigi's synchronous execution model.
    """

    def run(self):
        """
        Luigi's synchronous run method.

        This calls the async_run method and waits for it to complete.
        """
        import asyncio

        self.log_task_start()

        try:
            # Run the async operation
            result = asyncio.run(self.async_run())

            # Mark as complete
            self.mark_complete(result)

        except Exception as e:
            self.log_task_failure(e)
            raise

    async def async_run(self) -> Optional[Dict[str, Any]]:
        """
        Override this method in subclasses to implement async logic.

        Returns:
            Optional dict with output data to be stored
        """
        raise NotImplementedError("Subclasses must implement async_run()")
