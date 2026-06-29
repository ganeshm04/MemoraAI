"""
MemoraAI - Embedding Service
Google Gemini Embedding API integration with caching and retry logic.
"""

import hashlib
from typing import Optional
from functools import lru_cache
import structlog
import httpx

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
    Text embedding service using Google Gemini Embedding API.
    
    Available models (confirmed via API):
    - gemini-embedding-001
    - gemini-embedding-2
    
    Features:
    - Automatic retry with fallback models
    - In-memory caching
    - Batch embedding support
    """

    def __init__(self):
        self.model_name = config.settings.EMBEDDING_MODEL
        self.dimension = config.settings.EMBEDDING_DIMENSION
        self.cache = EmbeddingCache()
        self._http_client = None
        self._current_key_idx = 0

    def _get_api_keys(self) -> list[str]:
        """Split and return the list of Google/Gemini API keys configured for embeddings."""
        combined = f"{config.settings.GOOGLE_API_KEY or ''},{config.settings.GEMINI_API_KEY or ''}"
        unique_keys = []
        for k in combined.split(","):
            val = k.strip()
            if val and val not in unique_keys:
                unique_keys.append(val)
        return unique_keys

    def _get_client(self):
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def _call_embedding_api(self, text: str, model: str, api_version: str = "v1", api_key: str = None) -> list[float]:
        """Call Google Gemini Embedding API with the specified key context."""
        client = self._get_client()
        url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model}:embedContent"

        payload = {
            "model": f"models/{model}",
            "content": {
                "parts": [{"text": text}]
            },
        }

        response = await client.post(
            url,
            params={"key": api_key},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["embedding"]["values"]

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        cached = self.cache.get(text)
        if cached is not None:
            logger.debug("embedding_cache_hit", text_length=len(text))
            return cached

        models_to_try = [
            ("gemini-embedding-001", "v1"),
            ("gemini-embedding-2", "v1"),
            ("gemini-embedding-001", "v1beta"),
        ]

        import time
        from app.observability.metrics import generation_metrics

        keys = self._get_api_keys()
        if not keys:
            raise ValueError("No API keys configured for embedding")

        start_time = time.perf_counter()
        last_error = None

        # Iterate over keys starting from self._current_key_idx
        for i in range(len(keys)):
            key_idx = (self._current_key_idx + i) % len(keys)
            current_key = keys[key_idx]

            for attempt, (model_name, api_ver) in enumerate(models_to_try):
                try:
                    embedding = await self._call_embedding_api(text, model_name, api_ver, current_key)

                    if len(embedding) != self.dimension:
                        logger.warning(
                            "embedding_dimension_mismatch",
                            expected=self.dimension,
                            actual=len(embedding),
                        )

                    self.cache.set(text, embedding)
                    
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    generation_metrics.record_embedding(duration_ms, 1)

                    logger.info(
                        "embedding_generated",
                        model=model_name,
                        api=api_ver,
                        dimension=len(embedding),
                        duration_ms=round(duration_ms, 2),
                        key_index=key_idx,
                    )
                    
                    # Rotate to next key index for next request to distribute load evenly
                    self._current_key_idx = (key_idx + 1) % len(keys)
                    return embedding

                except Exception as e:
                    logger.warning(
                        "embedding_attempt_failed",
                        attempt=attempt + 1,
                        model=model_name,
                        key_index=key_idx,
                        error=str(e)[:100],
                    )
                    last_error = e

        logger.error("embedding_all_keys_failed")
        if last_error:
            raise last_error
        raise ValueError("All embedding API keys failed")

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
                    logger.error("batch_embedding_failed", text=text[:100], error=str(e)[:100])
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
        return await self.embed_text(query)

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self.cache.clear()
        logger.info("embedding_cache_cleared")


@lru_cache(maxsize=1000)
def _cached_embed_sync(text: str) -> list[float]:
    """
    Synchronous cached embedding for non-async contexts.
    """
    import asyncio
    embedder = Embedder()
    return asyncio.run(embedder.embed_text(text))


embedder = Embedder()
