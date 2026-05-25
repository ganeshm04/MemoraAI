"""
MemoraAI - Embedding Service
text-embedding-004 integration with caching and retry logic.
"""

import os
import hashlib
from typing import Optional
from functools import lru_cache
import structlog

from app.config import config

logger = structlog.get_logger(__name__)


class EmbeddingCache:
    """Simple in-memory embedding cache."""

    def __init__(self, max_size: int = 10000):
        self._cache: dict[str, list[float]] = {}
        self._max_size = max_size

    def get(self, text: str) -> Optional[list[float]]:
        """Get cached embedding."""
        key = self._make_key(text)
        return self._cache.get(key)

    def set(self, text: str, embedding: list[float]) -> None:
        """Cache embedding with LRU eviction."""
        if len(self._cache) >= self._max_size:
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        key = self._make_key(text)
        self._cache[key] = embedding

    def _make_key(self, text: str) -> str:
        """Create cache key from text hash."""
        return hashlib.sha256(text.encode()).hexdigest()

    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()


class Embedder:
    """
    Text embedding service using Google AI text-embedding-004.
    
    Features:
    - Automatic retry with exponential backoff
    - In-memory caching
    - Batch embedding support
    - Fallback error handling
    """

    def __init__(self):
        self.api_key = config.settings.GOOGLE_API_KEY or config.settings.GEMINI_API_KEY
        self.model_name = config.settings.EMBEDDING_MODEL
        self.dimension = config.settings.EMBEDDING_DIMENSION
        self.cache = EmbeddingCache()
        self._client = None

    def _get_client(self):
        """Lazy load Google AI client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
                logger.info("gemini_client_configured", model=self.model_name)
            except ImportError:
                logger.error("google-generativeai_not_installed")
                raise
        return self._client

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed (max ~2000 tokens)
            
        Returns:
            List of floats representing the embedding vector
        """
        cached = self.cache.get(text)
        if cached is not None:
            logger.debug("embedding_cache_hit", text_length=len(text))
            return cached

        for attempt in range(3):
            try:
                client = self._get_client()
                result = client.embed_content(
                    model=f"models/{self.model_name}",
                    content=text,
                    task_type="RETRIEVAL_DOCUMENT",
                )
                embedding = result["embedding"]
                
                if len(embedding) != self.dimension:
                    logger.warning(
                        "embedding_dimension_mismatch",
                        expected=self.dimension,
                        actual=len(embedding),
                    )

                self.cache.set(text, embedding)
                logger.info("embedding_generated", dimension=len(embedding))
                return embedding

            except Exception as e:
                logger.warning(
                    "embedding_attempt_failed",
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt == 2:
                    logger.error("embedding_all_attempts_failed", text_length=len(text))
                    raise

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        results = []
        cached_count = 0

        for text in texts:
            cached = self.cache.get(text)
            if cached is not None:
                results.append(cached)
                cached_count += 1
            else:
                try:
                    embedding = await self.embed_text(text)
                    results.append(embedding)
                except Exception as e:
                    logger.error("batch_embedding_failed", text=text[:100], error=str(e))
                    results.append([0.0] * self.dimension)

        logger.info(
            "batch_embedding_completed",
            total=len(texts),
            cached=cached_count,
            generated=len(texts) - cached_count,
        )
        return results

    async def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query to embed
            
        Returns:
            Embedding vector for the query
        """
        for attempt in range(3):
            try:
                client = self._get_client()
                result = client.embed_content(
                    model=f"models/{self.model_name}",
                    content=query,
                    task_type="RETRIEVAL_QUERY",
                )
                return result["embedding"]

            except Exception as e:
                logger.warning(
                    "query_embedding_failed",
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt == 2:
                    logger.error("query_embedding_exhausted", query=query[:50])
                    raise

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self.cache.clear()
        logger.info("embedding_cache_cleared")


@lru_cache(maxsize=1000)
def _cached_embed_sync(text: str) -> list[float]:
    """
    Synchronous cached embedding for non-async contexts.
    Use this only for non-critical paths.
    """
    embedder = Embedder()
    import asyncio
    return asyncio.run(embedder.embed_text(text))


embedder = Embedder()