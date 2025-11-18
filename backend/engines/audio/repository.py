"""
Audio generation database repository.
"""
import json
import logging
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime

from backend.core import (
    Task,
    TaskStatus,
    EngineType,
    DatabaseManager,
    get_db_manager,
)
from .models import AudioResponse, AudioListItem


logger = logging.getLogger(__name__)


class AudioRepository:
    """Repository for audio generation database operations."""

    def __init__(self, db: DatabaseManager = None):
        """Initialize repository with database manager."""
        self.db = db or get_db_manager()

    async def create_task(self, task: Task) -> Task:
        """
        Create a new audio generation task.

        Args:
            task: Task object to create

        Returns:
            Created task
        """
        query = """
            INSERT INTO generation_tasks (
                id, engine, status, provider, provider_task_id,
                user_id, client_id, campaign_id,
                params, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            task.id,
            task.engine if isinstance(task.engine, str) else task.engine.value,
            task.status if isinstance(task.status, str) else task.status.value,
            task.provider,
            task.provider_task_id,
            task.user_id,
            task.client_id,
            task.campaign_id,
            json.dumps(task.params),
            json.dumps(task.metadata),
            task.created_at.isoformat(),
        )

        self.db.execute_query(query, params)
        logger.info(f"Created audio task {task.id} in database")
        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task object or None if not found
        """
        query = """
            SELECT * FROM generation_tasks
            WHERE id = ? AND engine = ?
        """

        row = self.db.execute_query(
            query,
            (task_id, EngineType.AUDIO.value),
            fetch_one=True
        )

        if not row:
            return None

        return self._row_to_task(row)

    async def update_task(
        self,
        task_id: str,
        updates: Dict[str, Any]
    ) -> Task:
        """
        Update task fields.

        Args:
            task_id: Task ID
            updates: Dictionary of fields to update

        Returns:
            Updated task
        """
        # Build dynamic UPDATE query
        set_clauses = []
        params = []

        for key, value in updates.items():
            if key in ['status', 'error', 'result']:
                if key == 'status' and isinstance(value, TaskStatus):
                    value = value.value
                elif key == 'result' and value is not None:
                    value = json.dumps(value)
                elif key == 'error' and value is None:
                    value = None

                set_clauses.append(f"{key} = ?")
                params.append(value)
            elif key in ['started_at', 'completed_at']:
                set_clauses.append(f"{key} = ?")
                params.append(value.isoformat() if value else None)

        if not set_clauses:
            # No valid updates
            return await self.get_task(task_id)

        # Add updated_at
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())

        # Add WHERE clause params
        params.extend([task_id, EngineType.AUDIO.value])

        query = f"""
            UPDATE generation_tasks
            SET {', '.join(set_clauses)}
            WHERE id = ? AND engine = ?
        """

        self.db.execute_query(query, tuple(params))
        logger.info(f"Updated audio task {task_id}")

        return await self.get_task(task_id)

    async def list_tasks(
        self,
        filters: Dict[str, Any]
    ) -> Tuple[List[Task], int]:
        """
        List tasks with filtering and pagination.

        Args:
            filters: Filter parameters (page, page_size, status, user_id, etc.)

        Returns:
            Tuple of (tasks list, total count)
        """
        # Build WHERE clause
        where_clauses = ["engine = ?"]
        params = [EngineType.AUDIO.value]

        if filters.get('status'):
            where_clauses.append("status = ?")
            params.append(filters['status'].value if isinstance(filters['status'], TaskStatus) else filters['status'])

        if filters.get('user_id'):
            where_clauses.append("user_id = ?")
            params.append(filters['user_id'])

        if filters.get('client_id'):
            where_clauses.append("client_id = ?")
            params.append(filters['client_id'])

        if filters.get('campaign_id'):
            where_clauses.append("campaign_id = ?")
            params.append(filters['campaign_id'])

        if filters.get('provider'):
            where_clauses.append("provider = ?")
            params.append(filters['provider'])

        where_clause = " AND ".join(where_clauses)

        # Get total count
        count_query = f"SELECT COUNT(*) as count FROM generation_tasks WHERE {where_clause}"
        count_row = self.db.execute_query(count_query, tuple(params), fetch_one=True)
        total = count_row['count'] if count_row else 0

        # Get paginated results
        page = filters.get('page', 1)
        page_size = filters.get('page_size', 50)
        offset = (page - 1) * page_size

        sort_by = filters.get('sort_by', 'created_at')
        sort_order = filters.get('sort_order', 'desc').upper()

        query = f"""
            SELECT * FROM generation_tasks
            WHERE {where_clause}
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
        """

        rows = self.db.execute_query(
            query,
            tuple(params + [page_size, offset]),
            fetch_all=True
        )

        tasks = [self._row_to_task(row) for row in rows] if rows else []

        return tasks, total

    async def save_audio_result(
        self,
        task_id: str,
        audio_data: Dict[str, Any]
    ) -> AudioResponse:
        """
        Save the final audio result.

        Args:
            task_id: Task ID
            audio_data: Audio result data

        Returns:
            AudioResponse object
        """
        # Get the task to get context
        task = await self.get_task(task_id)

        # Create response object
        return AudioResponse(
            id=task_id,
            created_at=task.created_at,
            updated_at=datetime.now(),
            prompt=task.params.get('prompt'),
            model=task.params.get('model'),
            provider=task.provider,
            url=audio_data.get('url'),
            duration=audio_data.get('duration'),
            file_size=audio_data.get('file_size'),
            format=audio_data.get('format', 'mp3'),
            sample_rate=audio_data.get('sample_rate'),
            channels=audio_data.get('channels'),
            seed=task.params.get('seed'),
            temperature=task.params.get('temperature'),
            user_id=task.user_id,
            client_id=task.client_id,
            campaign_id=task.campaign_id,
            local_path=audio_data.get('local_path'),
        )

    def _row_to_task(self, row: Dict[str, Any]) -> Task:
        """Convert database row to Task object."""
        return Task(
            id=row['id'],
            engine=EngineType(row['engine']),
            status=TaskStatus(row['status']),
            provider=row['provider'],
            provider_task_id=row.get('provider_task_id'),
            user_id=row['user_id'],
            client_id=row.get('client_id'),
            campaign_id=row.get('campaign_id'),
            params=json.loads(row['params']) if row.get('params') else {},
            result=json.loads(row['result']) if row.get('result') else None,
            error=row.get('error'),
            created_at=datetime.fromisoformat(row['created_at']),
            started_at=datetime.fromisoformat(row['started_at']) if row.get('started_at') else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row.get('completed_at') else None,
            metadata=json.loads(row['metadata']) if row.get('metadata') else {},
        )
