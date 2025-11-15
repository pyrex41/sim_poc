"""
Genesis Documentation Search - Hybrid FTS5 + Vector RAG

Provides semantic and keyword search over Genesis API documentation.
Uses OpenAI embeddings for vector search and SQLite FTS5 for keyword search.
"""

import sqlite3
import os
import logging
from typing import List, Dict, Optional
import struct
from openai import AsyncOpenAI

try:
    import sqlite_vec
    SQLITE_VEC_PATH = sqlite_vec.loadable_path()
except ImportError:
    SQLITE_VEC_PATH = None

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class GenesisDocsSearch:
    """Hybrid search over Genesis documentation using FTS5 + vector embeddings"""

    def __init__(self, db_path: str = "./backend/DATA/genesis_docs.db"):
        self.db_path = db_path
        self._init_db()
        logger.info(f"Initialized GenesisDocsSearch with db: {db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with vec extension loaded"""
        conn = sqlite3.connect(self.db_path)
        if SQLITE_VEC_PATH:
            try:
                conn.enable_load_extension(True)
                conn.load_extension(SQLITE_VEC_PATH)
            except Exception as e:
                logger.debug(f"Could not load vec extension: {e}")
        return conn

    def _init_db(self):
        """Initialize database with FTS5 and vector tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = self._get_connection()

        if SQLITE_VEC_PATH:
            logger.info(f"Loaded sqlite-vec from {SQLITE_VEC_PATH}")
        else:
            logger.warning("sqlite-vec not installed, vector search will not be available")

        # Create FTS5 table for keyword search
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
                section,
                api_name,
                parameters,
                description,
                example,
                content
            )
        """)

        # Create vector table for semantic search (if vec0 available)
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS docs_vec USING vec0(
                    id INTEGER PRIMARY KEY,
                    embedding FLOAT[1536]
                )
            """)

            # Metadata table for vector results
            conn.execute("""
                CREATE TABLE IF NOT EXISTS docs_vec_meta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    section TEXT,
                    api_name TEXT,
                    content TEXT
                )
            """)
        except Exception as e:
            logger.warning(f"Could not create vector table: {e}")

        conn.commit()
        conn.close()
        logger.info("Database tables initialized")

    async def get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for text"""
        try:
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None

    def _embedding_to_blob(self, embedding: List[float]) -> bytes:
        """Convert embedding list to binary blob for sqlite-vec"""
        return struct.pack(f'{len(embedding)}f', *embedding)

    async def index_section(
        self,
        section: str,
        api_name: str,
        parameters: str,
        description: str,
        example: str
    ):
        """Index a single API documentation section"""
        conn = self._get_connection()

        # Combine all text for full context
        combined_text = f"{section}: {api_name}\n{description}\n{parameters}\n{example}"

        # Insert into FTS5
        conn.execute("""
            INSERT INTO docs_fts (section, api_name, parameters, description, example, content)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (section, api_name, parameters, description, example, combined_text))

        # Get embedding and insert into vector table
        embedding = await self.get_embedding(combined_text)
        if embedding:
            try:
                # Insert metadata first to get ID
                cursor = conn.execute("""
                    INSERT INTO docs_vec_meta (section, api_name, content)
                    VALUES (?, ?, ?)
                """, (section, api_name, combined_text))

                doc_id = cursor.lastrowid

                # Insert embedding
                embedding_blob = self._embedding_to_blob(embedding)
                conn.execute("""
                    INSERT INTO docs_vec (id, embedding)
                    VALUES (?, ?)
                """, (doc_id, embedding_blob))
            except Exception as e:
                logger.warning(f"Could not insert vector: {e}")

        conn.commit()
        conn.close()

    def fts_search(self, query: str, limit: int = 5) -> List[Dict]:
        """FTS5 keyword search"""
        conn = self._get_connection()

        try:
            cursor = conn.execute("""
                SELECT section, api_name, parameters, description, example, content
                FROM docs_fts
                WHERE docs_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))

            results = []
            for row in cursor:
                results.append({
                    "section": row[0],
                    "api_name": row[1],
                    "parameters": row[2],
                    "description": row[3],
                    "example": row[4],
                    "content": row[5],
                    "method": "fts"
                })
        except Exception as e:
            logger.error(f"FTS search error: {e}")
            results = []

        conn.close()
        return results

    async def vector_search(self, query: str, limit: int = 5) -> List[Dict]:
        """Vector similarity search using OpenAI embeddings"""
        # Get query embedding
        query_embedding = await self.get_embedding(query)
        if not query_embedding:
            return []

        if not SQLITE_VEC_PATH:
            logger.warning("sqlite-vec not available, skipping vector search")
            return []

        conn = self._get_connection()

        try:

            query_blob = self._embedding_to_blob(query_embedding)

            cursor = conn.execute("""
                SELECT
                    m.section,
                    m.api_name,
                    m.content,
                    vec_distance_cosine(v.embedding, ?) as distance
                FROM docs_vec v
                JOIN docs_vec_meta m ON v.id = m.id
                ORDER BY distance ASC
                LIMIT ?
            """, (query_blob, limit))

            results = []
            for row in cursor:
                results.append({
                    "section": row[0],
                    "api_name": row[1],
                    "content": row[2],
                    "similarity": 1 - row[3],  # Convert distance to similarity
                    "method": "vector"
                })
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            results = []

        conn.close()
        return results

    async def search(
        self,
        query: str,
        method: str = "hybrid",
        limit: int = 5
    ) -> List[Dict]:
        """
        Search documentation using FTS5, vectors, or both.

        Args:
            query: Search query
            method: "fts", "vector", or "hybrid"
            limit: Maximum results to return

        Returns:
            List of matching documentation entries
        """
        if method == "fts":
            return self.fts_search(query, limit=limit)
        elif method == "vector":
            return await self.vector_search(query, limit=limit)
        else:  # hybrid
            # Get results from both methods
            fts_results = self.fts_search(query, limit=limit // 2 + 1)
            vec_results = await self.vector_search(query, limit=limit // 2 + 1)

            # Combine and deduplicate by api_name
            seen = set()
            combined = []

            # Prioritize FTS results for exact matches
            for result in fts_results:
                key = result.get("api_name", "")
                if key not in seen:
                    seen.add(key)
                    combined.append(result)

            # Add vector results
            for result in vec_results:
                key = result.get("api_name", "")
                if key not in seen and len(combined) < limit:
                    seen.add(key)
                    combined.append(result)

            return combined[:limit]

    def get_stats(self) -> Dict:
        """Get statistics about indexed documentation"""
        conn = self._get_connection()

        stats = {}

        # Count FTS entries
        cursor = conn.execute("SELECT COUNT(*) FROM docs_fts")
        stats["fts_count"] = cursor.fetchone()[0]

        # Count vector entries
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM docs_vec_meta")
            stats["vector_count"] = cursor.fetchone()[0]
        except:
            stats["vector_count"] = 0

        # Get sections
        try:
            cursor = conn.execute("SELECT DISTINCT section FROM docs_fts")
            stats["sections"] = [row[0] for row in cursor]
        except:
            stats["sections"] = []

        conn.close()
        return stats


# Singleton instance
_docs_search = None

def get_docs_search() -> GenesisDocsSearch:
    """Get singleton docs search instance"""
    global _docs_search
    if _docs_search is None:
        _docs_search = GenesisDocsSearch()
    return _docs_search


async def search_genesis_docs(
    query: str,
    method: str = "hybrid",
    limit: int = 5
) -> List[Dict]:
    """
    Convenience function to search Genesis documentation.

    Args:
        query: Search query
        method: "fts", "vector", or "hybrid"
        limit: Maximum results

    Returns:
        List of matching documentation entries
    """
    searcher = get_docs_search()
    return await searcher.search(query, method=method, limit=limit)
