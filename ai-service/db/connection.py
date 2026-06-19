"""
MemoraAI - Database Connection
PostgreSQL connection with pgvector and async support.
"""

import asyncpg
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
import structlog

from app.config import config

logger = structlog.get_logger(__name__)


class DatabaseConnection:
    """Async PostgreSQL connection manager with pgvector support."""

    _instance: Optional["DatabaseConnection"] = None
    _pool: Optional[asyncpg.Pool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._pool = None

    async def connect(self) -> None:
        """Initialize connection pool."""
        if self._pool is not None:
            return

        try:
            self._pool = await asyncpg.create_pool(
                dsn=config.database.url,
                min_size=5,
                max_size=config.database.pool_size,
                command_timeout=config.settings.DB_POOL_TIMEOUT,
            )
            await self.initialize_schema()
            logger.info("database_connected", pool_size=config.database.pool_size)
        except Exception as e:
            logger.error("database_connection_failed", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("database_disconnected")

    @property
    def pool(self) -> asyncpg.Pool:
        """Get connection pool."""
        if self._pool is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._pool

    @asynccontextmanager
    async def acquire(self):
        """Acquire connection from pool."""
        async with self.pool.acquire() as conn:
            yield conn

    async def execute(self, query: str, *args) -> str:
        """Execute query without returning results."""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list:
        """Execute query and return all rows."""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Execute query and return single row."""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Execute query and return single value."""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute_many(self, query: str, values: list[tuple]) -> None:
        """Execute many queries in a transaction."""
        async with self.acquire() as conn:
            await conn.executemany(query, values)

    async def initialize_schema(self) -> None:
        """Initialize database schema from the shared schema.sql."""

        schema_path = Path(__file__).resolve().parents[2] / 'db' / 'schema.sql'
        if not schema_path.exists():
            logger.warning("schema_file_missing", path=str(schema_path))
            return

        schema_sql = schema_path.read_text(encoding='utf-8')
        try:
            async with self.acquire() as conn:
                await conn.execute(schema_sql)
            logger.info("database_schema_initialized", schema_file=str(schema_path))
        except Exception as e:
            logger.warning("schema_initialization_failed", error=str(e), path=str(schema_path))


class VectorStore:
    """pgvector operations for semantic search."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def search_similarity(
        self,
        table: str,
        query_vector: list[float],
        top_k: int = 10,
        threshold: float = 0.0,
        filter_column: Optional[str] = None,
        filter_value: Optional[str] = None,
    ) -> list[dict]:
        """Perform cosine similarity search using pgvector."""
        if table not in ["chunks", "documents"]:
            raise ValueError(f"Invalid table context: {table}")
        if filter_column and filter_column not in ["document_id", "source", "source_type"]:
            raise ValueError(f"Invalid filter column context: {filter_column}")
        try:
            vector_str = f"[{','.join(str(v) for v in query_vector)}]"
            if filter_column and filter_value:
                query = f"""
                    SELECT id, content, metadata, embedding <=> $1::vector AS distance
                    FROM {table}
                    WHERE {filter_column} = $2
                    AND embedding <=> $1::vector < $3
                    ORDER BY embedding <=> $1::vector
                    LIMIT $4
                """
                results = await self.db.fetch(
                    query, vector_str, filter_value, 1 - threshold, top_k
                )
            else:
                query = f"""
                    SELECT id, content, metadata, embedding <=> $1::vector AS distance
                    FROM {table}
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2
                """
                results = await self.db.fetch(query, vector_str, top_k)

            return [
                {
                    "id": row["id"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "distance": row["distance"] if row["distance"] is not None else 1.0,
                    "similarity": 1 - row["distance"] if row["distance"] is not None else 0.0,
                }
                for row in results
            ]
        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            raise

    async def insert_vector(
        self,
        table: str,
        content: str,
        embedding: list[float],
        metadata: dict,
    ) -> int:
        """Insert vector with content and metadata."""
        if table not in ["chunks", "documents"]:
            raise ValueError(f"Invalid table context: {table}")
        vector_str = f"[{','.join(str(v) for v in embedding)}]"
        query = f"""
            INSERT INTO {table} (content, embedding, metadata)
            VALUES ($1, $2::vector, $3)
            RETURNING id
        """
        return await self.db.fetchval(query, content, vector_str, metadata)

    async def batch_insert_vectors(
        self,
        table: str,
        values: list[tuple[str, list[float], dict]],
    ) -> None:
        """Batch insert vectors."""
        if table not in ["chunks", "documents"]:
            raise ValueError(f"Invalid table context: {table}")
        formatted_values = []
        for content, embedding, metadata in values:
            vector_str = f"[{','.join(str(v) for v in embedding)}]"
            formatted_values.append((content, vector_str, metadata))
            
        query = f"""
            INSERT INTO {table} (content, embedding, metadata)
            VALUES ($1, $2::vector, $3)
        """
        await self.db.execute_many(query, formatted_values)


class FullTextSearch:
    """PostgreSQL Full-Text Search operations for BM25."""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    async def search(
        self,
        table: str,
        query: str,
        top_k: int = 10,
        search_column: str = "content",
    ) -> list[dict]:
        """Perform full-text search with ts_rank."""
        if table not in ["chunks", "documents"]:
            raise ValueError(f"Invalid table context: {table}")
        if search_column not in ["content"]:
            raise ValueError(f"Invalid search column context: {search_column}")
        try:
            sql_query = f"""
                SELECT 
                    id,
                    content,
                    metadata,
                    ts_rank(to_tsvector('english', {search_column}), plainto_tsquery('english', $1)) AS rank,
                    ts_headline('english', {search_column}, plainto_tsquery('english', $1)) AS headline
                FROM {table}
                WHERE to_tsvector('english', {search_column}) @@ plainto_tsquery('english', $1)
                ORDER BY rank DESC
                LIMIT $2
            """
            results = await self.db.fetch(sql_query, query, top_k)

            return [
                {
                    "id": row["id"],
                    "content": row["content"],
                    "metadata": row["metadata"],
                    "rank": row["rank"],
                    "headline": row["headline"],
                    "bm25_score": row["rank"],
                }
                for row in results
            ]
        except Exception as e:
            logger.error("fts_search_failed", error=str(e))
            raise

    async def search_with_reranking(
        self,
        table: str,
        query: str,
        top_k: int = 50,
        search_column: str = "content",
    ) -> list[dict]:
        """Extended FTS with more results for reranking."""
        return await self.search(table, query, top_k, search_column)


db = DatabaseConnection()
vector_store = VectorStore(db)
fts_search = FullTextSearch(db)