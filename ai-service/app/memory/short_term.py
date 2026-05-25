"""
MemoraAI - Short-Term Memory
Conversation window management for active sessions.
"""

from typing import Optional, list
from dataclasses import dataclass, field
from datetime import datetime
import structlog

from db.connection import db
from app.config import config

logger = structlog.get_logger(__name__)


@dataclass
class MemoryEntry:
    """Single memory entry."""
    id: int
    session_id: str
    role: str
    content: str
    token_count: int
    metadata: dict
    created_at: datetime


@dataclass
class ConversationContext:
    """Context for conversation continuation."""
    session_id: str
    messages: list[MemoryEntry]
    recent_topics: list[str] = field(default_factory=list)


class ShortTermMemory:
    """
    Short-term memory management for active conversations.
    
    Features:
    - Session-based conversation storage
    - Token limit enforcement
    - Message retrieval by session
    - Context window management
    """

    def __init__(self, max_entries: int = None):
        self.max_entries = max_entries or config.settings.SHORT_TERM_MEMORY_LIMIT

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        token_count: int = None,
        metadata: dict = None,
    ) -> int:
        """
        Add message to short-term memory.
        
        Args:
            session_id: Unique session identifier
            role: Message role (user, assistant, system)
            content: Message content
            token_count: Token count (auto-calculated if None)
            metadata: Additional metadata
            
        Returns:
            Message ID
        """
        if token_count is None:
            token_count = self._estimate_tokens(content)

        logger.info(
            "stm_message_added",
            session_id=session_id,
            role=role,
            token_count=token_count,
        )

        try:
            query = """
                INSERT INTO short_term_memory (session_id, role, content, token_count, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """
            message_id = await db.fetchval(
                query, session_id, role, content, token_count, metadata or {}
            )

            await self._trim_session(session_id)

            return message_id

        except Exception as e:
            logger.error("stm_message_add_failed", error=str(e))
            raise

    async def get_conversation(
        self,
        session_id: str,
        limit: int = None,
        offset: int = 0,
    ) -> list[MemoryEntry]:
        """
        Get conversation messages for session.
        
        Args:
            session_id: Session identifier
            limit: Maximum messages to return
            offset: Start offset
            
        Returns:
            List of MemoryEntry
        """
        limit = limit or self.max_entries

        try:
            query = """
                SELECT id, session_id, role, content, token_count, metadata, created_at
                FROM short_term_memory
                WHERE session_id = $1
                ORDER BY created_at ASC
                LIMIT $2 OFFSET $3
            """
            rows = await db.fetch(query, session_id, limit, offset)

            entries = [
                MemoryEntry(
                    id=row["id"],
                    session_id=row["session_id"],
                    role=row["role"],
                    content=row["content"],
                    token_count=row["token_count"],
                    metadata=row["metadata"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

            logger.info(
                "stm_conversation_retrieved",
                session_id=session_id,
                message_count=len(entries),
            )

            return entries

        except Exception as e:
            logger.error("stm_conversation_get_failed", error=str(e))
            return []

    async def get_context_window(
        self,
        session_id: str,
        max_tokens: int = 2000,
    ) -> ConversationContext:
        """
        Get context window with token limit.
        
        Args:
            session_id: Session identifier
            max_tokens: Maximum tokens in context
            
        Returns:
            ConversationContext with trimmed messages
        """
        all_messages = await self.get_conversation(session_id, limit=1000)

        context_messages = []
        total_tokens = 0

        for message in reversed(all_messages):
            if total_tokens + message.token_count <= max_tokens:
                context_messages.insert(0, message)
                total_tokens += message.token_count
            else:
                break

        logger.info(
            "stm_context_window_created",
            session_id=session_id,
            message_count=len(context_messages),
            total_tokens=total_tokens,
        )

        return ConversationContext(
            session_id=session_id,
            messages=context_messages,
        )

    async def clear_session(self, session_id: str) -> int:
        """Clear all messages for a session."""
        try:
            query = "DELETE FROM short_term_memory WHERE session_id = $1"
            result = await db.execute(query, session_id)
            logger.info("stm_session_cleared", session_id=session_id)
            return 1
        except Exception as e:
            logger.error("stm_session_clear_failed", error=str(e))
            return 0

    async def _trim_session(self, session_id: str) -> None:
        """Trim session to max entries."""
        try:
            query = """
                DELETE FROM short_term_memory
                WHERE id IN (
                    SELECT id FROM short_term_memory
                    WHERE session_id = $1
                    ORDER BY created_at ASC
                    LIMIT GREATEST(0, (SELECT COUNT(*) FROM short_term_memory WHERE session_id = $1) - $2)
                )
            """
            await db.execute(query, session_id, self.max_entries)
        except Exception as e:
            logger.warning("stm_trim_failed", error=str(e))

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count."""
        words = text.split()
        return int(len(words) * 1.3)

    async def search_session(
        self,
        session_id: str,
        query: str,
        limit: int = 5,
    ) -> list[MemoryEntry]:
        """Search messages in session."""
        try:
            query_sql = """
                SELECT id, session_id, role, content, token_count, metadata, created_at
                FROM short_term_memory
                WHERE session_id = $1
                AND content ILIKE $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            rows = await db.fetch(query_sql, session_id, f"%{query}%", limit)

            return [
                MemoryEntry(
                    id=row["id"],
                    session_id=row["session_id"],
                    role=row["role"],
                    content=row["content"],
                    token_count=row["token_count"],
                    metadata=row["metadata"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]
        except Exception as e:
            logger.error("stm_search_failed", error=str(e))
            return []


short_term_memory = ShortTermMemory()