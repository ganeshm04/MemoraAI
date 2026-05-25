"""
MemoraAI - Long-Term Memory
Persistent user preferences, facts, and interests.
"""

from typing import Optional, list
from dataclasses import dataclass
from datetime import datetime
import structlog

from db.connection import db

logger = structlog.get_logger(__name__)


@dataclass
class UserFact:
    """Persistent user fact or preference."""
    id: int
    user_id: str
    category: str
    key: str
    value: str
    confidence: float
    source: str
    metadata: dict
    created_at: datetime
    updated_at: datetime


class LongTermMemory:
    """
    Long-term memory for persistent user information.
    
    Stores:
    - User preferences
    - Recurring interests
    - Persistent facts
    - Important personal information
    """

    async def store_fact(
        self,
        user_id: str,
        key: str,
        value: str,
        category: str = "general",
        confidence: float = 1.0,
        source: str = "conversation",
        metadata: dict = None,
    ) -> int:
        """
        Store a fact in long-term memory.
        
        Args:
            user_id: User identifier
            key: Fact key (unique per user)
            value: Fact value
            category: Category for organization
            confidence: Confidence score (0-1)
            source: Source of the fact
            metadata: Additional metadata
            
        Returns:
            Fact ID
        """
        logger.info(
            "ltm_fact_storing",
            user_id=user_id,
            key=key,
            category=category,
        )

        try:
            query = """
                INSERT INTO long_term_memory (user_id, category, key, value, confidence, source, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id, key) 
                DO UPDATE SET value = $4, confidence = $5, updated_at = NOW()
                RETURNING id
            """
            fact_id = await db.fetchval(
                query, user_id, category, key, value, confidence, source, metadata or {}
            )
            return fact_id

        except Exception as e:
            logger.error("ltm_fact_store_failed", error=str(e))
            raise

    async def get_fact(self, user_id: str, key: str) -> Optional[UserFact]:
        """Get a specific fact by key."""
        try:
            query = """
                SELECT id, user_id, category, key, value, confidence, source, metadata, created_at, updated_at
                FROM long_term_memory
                WHERE user_id = $1 AND key = $2
            """
            row = await db.fetchrow(query, user_id, key)

            if not row:
                return None

            return UserFact(
                id=row["id"],
                user_id=row["user_id"],
                category=row["category"],
                key=row["key"],
                value=row["value"],
                confidence=row["confidence"],
                source=row["source"],
                metadata=row["metadata"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

        except Exception as e:
            logger.error("ltm_fact_get_failed", error=str(e))
            return None

    async def get_all_facts(self, user_id: str, category: str = None) -> list[UserFact]:
        """Get all facts for a user, optionally filtered by category."""
        try:
            if category:
                query = """
                    SELECT id, user_id, category, key, value, confidence, source, metadata, created_at, updated_at
                    FROM long_term_memory
                    WHERE user_id = $1 AND category = $2
                    ORDER BY updated_at DESC
                """
                rows = await db.fetch(query, user_id, category)
            else:
                query = """
                    SELECT id, user_id, category, key, value, confidence, source, metadata, created_at, updated_at
                    FROM long_term_memory
                    WHERE user_id = $1
                    ORDER BY updated_at DESC
                """
                rows = await db.fetch(query, user_id)

            return [
                UserFact(
                    id=row["id"],
                    user_id=row["user_id"],
                    category=row["category"],
                    key=row["key"],
                    value=row["value"],
                    confidence=row["confidence"],
                    source=row["source"],
                    metadata=row["metadata"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

        except Exception as e:
            logger.error("ltm_facts_get_failed", error=str(e))
            return []

    async def update_fact(
        self,
        user_id: str,
        key: str,
        value: str,
        confidence: float = None,
    ) -> bool:
        """Update an existing fact."""
        try:
            if confidence is not None:
                query = """
                    UPDATE long_term_memory
                    SET value = $3, confidence = $4, updated_at = NOW()
                    WHERE user_id = $1 AND key = $2
                """
                result = await db.execute(query, user_id, key, value, confidence)
            else:
                query = """
                    UPDATE long_term_memory
                    SET value = $3, updated_at = NOW()
                    WHERE user_id = $1 AND key = $2
                """
                result = await db.execute(query, user_id, key, value)

            return result != "UPDATE 0"

        except Exception as e:
            logger.error("ltm_fact_update_failed", error=str(e))
            return False

    async def delete_fact(self, user_id: str, key: str) -> bool:
        """Delete a fact from memory."""
        try:
            query = "DELETE FROM long_term_memory WHERE user_id = $1 AND key = $2"
            result = await db.execute(query, user_id, key)
            return result != "DELETE 0"
        except Exception as e:
            logger.error("ltm_fact_delete_failed", error=str(e))
            return False

    async def search_facts(self, user_id: str, query: str, limit: int = 10) -> list[UserFact]:
        """Search facts by key or value."""
        try:
            query_sql = """
                SELECT id, user_id, category, key, value, confidence, source, metadata, created_at, updated_at
                FROM long_term_memory
                WHERE user_id = $1 AND (key ILIKE $2 OR value ILIKE $2)
                ORDER BY confidence DESC, updated_at DESC
                LIMIT $3
            """
            rows = await db.fetch(query_sql, user_id, f"%{query}%", limit)

            return [
                UserFact(
                    id=row["id"],
                    user_id=row["user_id"],
                    category=row["category"],
                    key=row["key"],
                    value=row["value"],
                    confidence=row["confidence"],
                    source=row["source"],
                    metadata=row["metadata"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

        except Exception as e:
            logger.error("ltm_facts_search_failed", error=str(e))
            return []

    async def get_preferences(self, user_id: str) -> dict:
        """Get user preferences as dictionary."""
        facts = await self.get_all_facts(user_id, category="preference")
        return {fact.key: fact.value for fact in facts if fact.confidence >= 0.5}

    async def store_preference(self, user_id: str, key: str, value: str) -> int:
        """Store a user preference."""
        return await self.store_fact(
            user_id=user_id,
            key=key,
            value=value,
            category="preference",
            confidence=1.0,
            source="learned",
        )


long_term_memory = LongTermMemory()