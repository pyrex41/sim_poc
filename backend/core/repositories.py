"""
Database repositories for client and campaign management.
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from .client_models import Client, ClientCreate, ClientUpdate, Campaign, CampaignCreate, CampaignUpdate
from .exceptions import NotFoundError, ValidationError, DatabaseError


logger = logging.getLogger(__name__)


# ============================================================================
# CLIENT REPOSITORY
# ============================================================================

class ClientRepository:
    """Repository for client data operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize repository with database connection."""
        self.conn = conn

    def create(self, user_id: int, data: ClientCreate) -> Client:
        """
        Create a new client.

        Args:
            user_id: ID of the user creating the client
            data: Client creation data

        Returns:
            Created client

        Raises:
            DatabaseError: If creation fails
        """
        client_id = str(uuid4())
        now = datetime.utcnow()

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO clients (id, user_id, name, description, brand_guidelines, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (client_id, user_id, data.name, data.description, data.brand_guidelines, now, now)
            )
            self.conn.commit()

            return self.get_by_id(client_id, user_id)

        except sqlite3.Error as e:
            logger.error(f"Failed to create client: {e}")
            raise DatabaseError(f"Failed to create client: {e}")

    def get_by_id(self, client_id: str, user_id: int) -> Client:
        """
        Get a client by ID.

        Args:
            client_id: Client ID
            user_id: User ID (for access control)

        Returns:
            Client data

        Raises:
            NotFoundError: If client not found or user doesn't have access
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, name, description, brand_guidelines, created_at, updated_at
                FROM clients
                WHERE id = ? AND user_id = ?
                """,
                (client_id, user_id)
            )
            row = cursor.fetchone()

            if not row:
                raise NotFoundError(f"Client {client_id} not found")

            return self._row_to_client(row)

        except sqlite3.Error as e:
            logger.error(f"Failed to get client {client_id}: {e}")
            raise DatabaseError(f"Failed to get client: {e}")

    def list(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: Optional[str] = None
    ) -> tuple[List[Client], int]:
        """
        List clients for a user.

        Args:
            user_id: User ID
            page: Page number
            page_size: Items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            search: Optional search term for client name

        Returns:
            Tuple of (list of clients, total count)
        """
        try:
            # Build query
            where_clause = "WHERE user_id = ?"
            params = [user_id]

            if search:
                where_clause += " AND name LIKE ?"
                params.append(f"%{search}%")

            # Validate sort parameters
            allowed_sort_fields = {"name", "created_at", "updated_at"}
            if sort_by not in allowed_sort_fields:
                sort_by = "created_at"
            if sort_order.lower() not in {"asc", "desc"}:
                sort_order = "desc"

            # Get total count
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM clients {where_clause}", params)
            total = cursor.fetchone()[0]

            # Get paginated results
            offset = (page - 1) * page_size
            cursor.execute(
                f"""
                SELECT id, user_id, name, description, brand_guidelines, created_at, updated_at
                FROM clients
                {where_clause}
                ORDER BY {sort_by} {sort_order}
                LIMIT ? OFFSET ?
                """,
                params + [page_size, offset]
            )
            rows = cursor.fetchall()

            clients = [self._row_to_client(row) for row in rows]
            return clients, total

        except sqlite3.Error as e:
            logger.error(f"Failed to list clients: {e}")
            raise DatabaseError(f"Failed to list clients: {e}")

    def update(self, client_id: str, user_id: int, data: ClientUpdate) -> Client:
        """
        Update a client.

        Args:
            client_id: Client ID
            user_id: User ID (for access control)
            data: Update data

        Returns:
            Updated client

        Raises:
            NotFoundError: If client not found
        """
        # Verify client exists and user has access
        existing = self.get_by_id(client_id, user_id)

        # Build update query
        updates = []
        params = []

        if data.name is not None:
            updates.append("name = ?")
            params.append(data.name)
        if data.description is not None:
            updates.append("description = ?")
            params.append(data.description)
        if data.brand_guidelines is not None:
            updates.append("brand_guidelines = ?")
            params.append(data.brand_guidelines)

        if not updates:
            return existing  # No changes

        updates.append("updated_at = ?")
        params.append(datetime.utcnow())
        params.extend([client_id, user_id])

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                UPDATE clients
                SET {', '.join(updates)}
                WHERE id = ? AND user_id = ?
                """,
                params
            )
            self.conn.commit()

            return self.get_by_id(client_id, user_id)

        except sqlite3.Error as e:
            logger.error(f"Failed to update client {client_id}: {e}")
            raise DatabaseError(f"Failed to update client: {e}")

    def delete(self, client_id: str, user_id: int) -> None:
        """
        Delete a client.

        Args:
            client_id: Client ID
            user_id: User ID (for access control)

        Raises:
            NotFoundError: If client not found
        """
        # Verify client exists and user has access
        self.get_by_id(client_id, user_id)

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM clients WHERE id = ? AND user_id = ?",
                (client_id, user_id)
            )
            self.conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Failed to delete client {client_id}: {e}")
            raise DatabaseError(f"Failed to delete client: {e}")

    @staticmethod
    def _row_to_client(row: sqlite3.Row) -> Client:
        """Convert database row to Client model."""
        return Client(
            id=row[0],
            user_id=row[1],
            name=row[2],
            description=row[3],
            brand_guidelines=row[4],
            created_at=datetime.fromisoformat(row[5]),
            updated_at=datetime.fromisoformat(row[6])
        )


# ============================================================================
# CAMPAIGN REPOSITORY
# ============================================================================

class CampaignRepository:
    """Repository for campaign data operations."""

    def __init__(self, conn: sqlite3.Connection):
        """Initialize repository with database connection."""
        self.conn = conn

    def create(self, user_id: int, data: CampaignCreate) -> Campaign:
        """
        Create a new campaign.

        Args:
            user_id: ID of the user creating the campaign
            data: Campaign creation data

        Returns:
            Created campaign

        Raises:
            ValidationError: If client doesn't exist
            DatabaseError: If creation fails
        """
        # Verify client exists and user has access
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM clients WHERE id = ? AND user_id = ?",
            (data.client_id, user_id)
        )
        if not cursor.fetchone():
            raise ValidationError(f"Client {data.client_id} not found or access denied")

        campaign_id = str(uuid4())
        now = datetime.utcnow()

        try:
            cursor.execute(
                """
                INSERT INTO campaigns (id, client_id, user_id, name, goal, status, brief, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (campaign_id, data.client_id, user_id, data.name, data.goal, data.status, data.brief, now, now)
            )
            self.conn.commit()

            return self.get_by_id(campaign_id, user_id)

        except sqlite3.Error as e:
            logger.error(f"Failed to create campaign: {e}")
            raise DatabaseError(f"Failed to create campaign: {e}")

    def get_by_id(self, campaign_id: str, user_id: int) -> Campaign:
        """
        Get a campaign by ID.

        Args:
            campaign_id: Campaign ID
            user_id: User ID (for access control)

        Returns:
            Campaign data

        Raises:
            NotFoundError: If campaign not found or user doesn't have access
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT id, client_id, user_id, name, goal, status, brief, created_at, updated_at
                FROM campaigns
                WHERE id = ? AND user_id = ?
                """,
                (campaign_id, user_id)
            )
            row = cursor.fetchone()

            if not row:
                raise NotFoundError(f"Campaign {campaign_id} not found")

            return self._row_to_campaign(row)

        except sqlite3.Error as e:
            logger.error(f"Failed to get campaign {campaign_id}: {e}")
            raise DatabaseError(f"Failed to get campaign: {e}")

    def list(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        client_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Campaign], int]:
        """
        List campaigns for a user.

        Args:
            user_id: User ID
            page: Page number
            page_size: Items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            client_id: Optional filter by client
            status: Optional filter by status
            search: Optional search term for campaign name

        Returns:
            Tuple of (list of campaigns, total count)
        """
        try:
            # Build query
            where_clause = "WHERE user_id = ?"
            params = [user_id]

            if client_id:
                where_clause += " AND client_id = ?"
                params.append(client_id)
            if status:
                where_clause += " AND status = ?"
                params.append(status)
            if search:
                where_clause += " AND name LIKE ?"
                params.append(f"%{search}%")

            # Validate sort parameters
            allowed_sort_fields = {"name", "created_at", "updated_at", "status"}
            if sort_by not in allowed_sort_fields:
                sort_by = "created_at"
            if sort_order.lower() not in {"asc", "desc"}:
                sort_order = "desc"

            # Get total count
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM campaigns {where_clause}", params)
            total = cursor.fetchone()[0]

            # Get paginated results
            offset = (page - 1) * page_size
            cursor.execute(
                f"""
                SELECT id, client_id, user_id, name, goal, status, brief, created_at, updated_at
                FROM campaigns
                {where_clause}
                ORDER BY {sort_by} {sort_order}
                LIMIT ? OFFSET ?
                """,
                params + [page_size, offset]
            )
            rows = cursor.fetchall()

            campaigns = [self._row_to_campaign(row) for row in rows]
            return campaigns, total

        except sqlite3.Error as e:
            logger.error(f"Failed to list campaigns: {e}")
            raise DatabaseError(f"Failed to list campaigns: {e}")

    def update(self, campaign_id: str, user_id: int, data: CampaignUpdate) -> Campaign:
        """
        Update a campaign.

        Args:
            campaign_id: Campaign ID
            user_id: User ID (for access control)
            data: Update data

        Returns:
            Updated campaign

        Raises:
            NotFoundError: If campaign not found
        """
        # Verify campaign exists and user has access
        existing = self.get_by_id(campaign_id, user_id)

        # Build update query
        updates = []
        params = []

        if data.name is not None:
            updates.append("name = ?")
            params.append(data.name)
        if data.goal is not None:
            updates.append("goal = ?")
            params.append(data.goal)
        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status)
        if data.brief is not None:
            updates.append("brief = ?")
            params.append(data.brief)

        if not updates:
            return existing  # No changes

        updates.append("updated_at = ?")
        params.append(datetime.utcnow())
        params.extend([campaign_id, user_id])

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                f"""
                UPDATE campaigns
                SET {', '.join(updates)}
                WHERE id = ? AND user_id = ?
                """,
                params
            )
            self.conn.commit()

            return self.get_by_id(campaign_id, user_id)

        except sqlite3.Error as e:
            logger.error(f"Failed to update campaign {campaign_id}: {e}")
            raise DatabaseError(f"Failed to update campaign: {e}")

    def delete(self, campaign_id: str, user_id: int) -> None:
        """
        Delete a campaign.

        Args:
            campaign_id: Campaign ID
            user_id: User ID (for access control)

        Raises:
            NotFoundError: If campaign not found
        """
        # Verify campaign exists and user has access
        self.get_by_id(campaign_id, user_id)

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM campaigns WHERE id = ? AND user_id = ?",
                (campaign_id, user_id)
            )
            self.conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Failed to delete campaign {campaign_id}: {e}")
            raise DatabaseError(f"Failed to delete campaign: {e}")

    @staticmethod
    def _row_to_campaign(row: sqlite3.Row) -> Campaign:
        """Convert database row to Campaign model."""
        return Campaign(
            id=row[0],
            client_id=row[1],
            user_id=row[2],
            name=row[3],
            goal=row[4],
            status=row[5],
            brief=row[6],
            created_at=datetime.fromisoformat(row[7]),
            updated_at=datetime.fromisoformat(row[8])
        )
