"""
MemoraAI - Episodic Memory
Session summaries and historical interaction understanding.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog

from db.connection import db
from app.config import config

logger = structlog.get_logger(__name__)


@dataclass
class Episode:
    """Single episodic memory entry."""
    id: int
    user_id: str
    session_id: str
    summary: str
    key_topics: list[str]
    important_facts: list[str]
    sentiment: str
    duration_minutes: int
    message_count: int
    created_at: datetime


class EpisodicMemory:
    """
    Episodic memory for session summaries and historical understanding.
    
    Stores:
    - Session summaries
    - Key topics discussed
    - Important facts from sessions
    - Interaction patterns
    """

    async def create_episode(
        self,
        user_id: str,
        session_id: str,
        summary: str,
        key_topics: list[str] = None,
        important_facts: list[str] = None,
        sentiment: str = "neutral",
        duration_minutes: int = 0,
        message_count: int = 0,
    ) -> int:
        """
        Create a new episode memory.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            summary: Session summary
            key_topics: Topics discussed
            important_facts: Key facts from session
            sentiment: Overall sentiment
            duration_minutes: Session duration
            message_count: Number of messages
            
        Returns:
            Episode ID
        """
        logger.info(
            "em_episode_creating",
            user_id=user_id,
            session_id=session_id,
            topics_count=len(key_topics or []),
        )

        try:
            query = """
                INSERT INTO episodic_memory 
                (user_id, session_id, summary, key_topics, important_facts, sentiment, duration_minutes, message_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """
            episode_id = await db.fetchval(
                query,
                user_id,
                session_id,
                summary,
                key_topics or [],
                important_facts or [],
                sentiment,
                duration_minutes,
                message_count,
            )

            from app.observability.metrics import memory_metrics
            memory_metrics.record_memory_operation("write", "episodic", 1)

            return episode_id

        except Exception as e:
            logger.error("em_episode_create_failed", error=str(e))
            raise

    async def get_recent_episodes(
        self,
        user_id: str,
        limit: int = 10,
        days: int = 30,
    ) -> list[Episode]:
        """
        Get recent episodes for user.
        
        Args:
            user_id: User identifier
            limit: Maximum episodes to return
            days: Days to look back
            
        Returns:
            List of Episode
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = """
                SELECT id, user_id, session_id, summary, key_topics, important_facts, 
                       sentiment, duration_minutes, message_count, created_at
                FROM episodic_memory
                WHERE user_id = $1 AND created_at >= $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            rows = await db.fetch(query, user_id, cutoff_date, limit)

            episodes = [
                Episode(
                    id=row["id"],
                    user_id=row["user_id"],
                    session_id=row["session_id"],
                    summary=row["summary"],
                    key_topics=row["key_topics"] or [],
                    important_facts=row["important_facts"] or [],
                    sentiment=row["sentiment"],
                    duration_minutes=row["duration_minutes"],
                    message_count=row["message_count"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

            from app.observability.metrics import memory_metrics
            memory_metrics.record_memory_operation("read", "episodic", len(episodes))

            return episodes

        except Exception as e:
            logger.error("em_recent_episodes_get_failed", error=str(e))
            return []

    async def get_episode(self, episode_id: int) -> Optional[Episode]:
        """Get specific episode by ID."""
        try:
            query = """
                SELECT id, user_id, session_id, summary, key_topics, important_facts,
                       sentiment, duration_minutes, message_count, created_at
                FROM episodic_memory
                WHERE id = $1
            """
            row = await db.fetchrow(query, episode_id)

            if not row:
                return None

            return Episode(
                id=row["id"],
                user_id=row["user_id"],
                session_id=row["session_id"],
                summary=row["summary"],
                key_topics=row["key_topics"] or [],
                important_facts=row["important_facts"] or [],
                sentiment=row["sentiment"],
                duration_minutes=row["duration_minutes"],
                message_count=row["message_count"],
                created_at=row["created_at"],
            )

        except Exception as e:
            logger.error("em_episode_get_failed", error=str(e))
            return None

    async def search_episodes(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> list[Episode]:
        """Search episodes by summary or topics."""
        try:
            query_sql = """
                SELECT id, user_id, session_id, summary, key_topics, important_facts,
                       sentiment, duration_minutes, message_count, created_at
                FROM episodic_memory
                WHERE user_id = $1 
                AND (summary ILIKE $2 OR $3 = ANY(key_topics))
                ORDER BY created_at DESC
                LIMIT $4
            """
            rows = await db.fetch(query_sql, user_id, f"%{query}%", query, limit)

            return [
                Episode(
                    id=row["id"],
                    user_id=row["user_id"],
                    session_id=row["session_id"],
                    summary=row["summary"],
                    key_topics=row["key_topics"] or [],
                    important_facts=row["important_facts"] or [],
                    sentiment=row["sentiment"],
                    duration_minutes=row["duration_minutes"],
                    message_count=row["message_count"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

        except Exception as e:
            logger.error("em_episodes_search_failed", error=str(e))
            return []

    async def get_topic_timeline(
        self,
        user_id: str,
        topic: str,
        limit: int = 20,
    ) -> list[Episode]:
        """Get episodes containing specific topic."""
        try:
            query = """
                SELECT id, user_id, session_id, summary, key_topics, important_facts,
                       sentiment, duration_minutes, message_count, created_at
                FROM episodic_memory
                WHERE user_id = $1 AND $2 = ANY(key_topics)
                ORDER BY created_at DESC
                LIMIT $3
            """
            rows = await db.fetch(query, user_id, topic, limit)

            return [
                Episode(
                    id=row["id"],
                    user_id=row["user_id"],
                    session_id=row["session_id"],
                    summary=row["summary"],
                    key_topics=row["key_topics"] or [],
                    important_facts=row["important_facts"] or [],
                    sentiment=row["sentiment"],
                    duration_minutes=row["duration_minutes"],
                    message_count=row["message_count"],
                    created_at=row["created_at"],
                )
                for row in rows
            ]

        except Exception as e:
            logger.error("em_topic_timeline_failed", error=str(e))
            return []

    async def delete_old_episodes(self, user_id: str, days: int = 90) -> int:
        """Delete episodes older than specified days."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = """
                DELETE FROM episodic_memory
                WHERE user_id = $1 AND created_at < $2
            """
            result = await db.execute(query, user_id, cutoff_date)

            retention = config.settings.EPISODIC_MEMORY_RETENTION
            if retention > 0:
                count_query = "SELECT COUNT(*) FROM episodic_memory WHERE user_id = $1"
                count = await db.fetchval(count_query, user_id)
                
                if count > retention:
                    delete_query = """
                        DELETE FROM episodic_memory
                        WHERE id IN (
                            SELECT id FROM episodic_memory
                            WHERE user_id = $1
                            ORDER BY created_at ASC
                            LIMIT $2
                        )
                    """
                    await db.execute(query, user_id, count - retention)

            logger.info("em_old_episodes_deleted", user_id=user_id, cutoff_days=days)
            return 1

        except Exception as e:
            logger.error("em_old_episodes_delete_failed", error=str(e))
            return 0

    async def get_interaction_stats(self, user_id: str, days: int = 30) -> dict:
        """Get interaction statistics for user."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            query = """
                SELECT 
                    COUNT(*) as total_episodes,
                    SUM(message_count) as total_messages,
                    SUM(duration_minutes) as total_duration,
                    AVG(message_count) as avg_messages,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM episodic_memory
                WHERE user_id = $1 AND created_at >= $2
            """
            row = await db.fetchrow(query, user_id, cutoff_date)

            return {
                "total_episodes": row["total_episodes"] or 0,
                "total_messages": row["total_messages"] or 0,
                "total_duration_minutes": row["total_duration"] or 0,
                "avg_messages_per_session": float(row["avg_messages"] or 0),
                "unique_sessions": row["unique_sessions"] or 0,
            }

        except Exception as e:
            logger.error("em_interaction_stats_failed", error=str(e))
            return {}


episodic_memory = EpisodicMemory()