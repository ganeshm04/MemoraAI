"""
MemoraAI - Vector Search
pgvector similarity search implementation.
"""

from typing import Optional, Literal
from dataclasses import dataclass
import structlog

from db.connection import db, vector_store
from app.config import config

logger = structlog.get_logger(__name__)


@dataclass
class SearchResult:
    """Single search result with metadata."""
    id: int
    content: str
    metadata: dict
    score: float
    rank: int
    source: str = ""


@dataclass
class VectorSearchConfig:
    """Configuration for vector search."""
    top_k: int = 10
    threshold: float = 0.7
    table: str = "chunks"


class VectorSearcher:
    """
    Vector similarity search using pgvector.
    
    Features:
    - Cosine similarity search
    - Configurable top-k results
    - Similarity threshold filtering
    - Metadata filtering
    - Fallback error handling
    """

    def __init__(self, config: Optional[VectorSearchConfig] = None):
        self.config = config or VectorSearchConfig(
            top_k=config.vector.top_k,
            threshold=config.vector.similarity_threshold,
        )

    async def search(
        self,
        query_vector: list[float],
        table: str = None,
        top_k: int = None,
        threshold: float = None,
        filter_column: Optional[str] = None,
        filter_value: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Perform vector similarity search.
        
        Args:
            query_vector: Query embedding vector
            table: Table to search (default: chunks)
            top_k: Number of results (default: from config)
            threshold: Minimum similarity threshold
            filter_column: Column to filter on
            filter_value: Value to filter by
            
        Returns:
            List of SearchResult sorted by similarity
        """
        table = table or self.config.table
        top_k = top_k or self.config.top_k
        threshold = threshold or self.config.threshold

        logger.info(
            "vector_search_started",
            table=table,
            top_k=top_k,
            threshold=threshold,
        )

        try:
            results = await vector_store.search_similarity(
                table=table,
                query_vector=query_vector,
                top_k=top_k,
                threshold=threshold,
                filter_column=filter_column,
                filter_value=filter_value,
            )

            search_results = []
            for rank, row in enumerate(results, 1):
                search_results.append(
                    SearchResult(
                        id=row["id"],
                        content=row["content"],
                        metadata=row["metadata"],
                        score=row["similarity"],
                        rank=rank,
                        source=row["metadata"].get("source", ""),
                    )
                )

            logger.info(
                "vector_search_completed",
                table=table,
                results_found=len(search_results),
            )

            return search_results

        except Exception as e:
            logger.error("vector_search_failed", error=str(e), table=table)
            raise

    async def search_by_text(
        self,
        query_text: str,
        embedder,
        table: str = None,
        top_k: int = None,
    ) -> list[SearchResult]:
        """
        Search by text - embeds query first, then searches.
        
        Args:
            query_text: Text query
            embedder: Embedder instance
            table: Table to search
            top_k: Number of results
            
        Returns:
            List of SearchResult
        """
        logger.info("text_vector_search_started", query=query_text[:50])

        try:
            query_vector = await embedder.embed_query(query_text)
            results = await self.search(
                query_vector=query_vector,
                table=table,
                top_k=top_k,
            )

            logger.info(
                "text_vector_search_completed",
                query=query_text[:50],
                results=len(results),
            )

            return results

        except Exception as e:
            logger.error("text_vector_search_failed", error=str(e))
            raise


@dataclass
class BatchVectorSearchConfig:
    """Configuration for batch vector search."""
    batch_size: int = 100
    parallel_queries: int = 5


class BatchVectorSearcher:
    """Batch vector search for multiple queries."""

    def __init__(self, config: Optional[BatchVectorSearchConfig] = None):
        self.config = config or BatchVectorSearchConfig()

    async def search_batch(
        self,
        queries: list[list[float]],
        vector_searcher: VectorSearcher,
        table: str = "chunks",
        top_k: int = 10,
    ) -> list[list[SearchResult]]:
        """
        Search multiple query vectors in batch.
        
        Args:
            queries: List of query vectors
            vector_searcher: VectorSearcher instance
            table: Table to search
            top_k: Results per query
            
        Returns:
            List of result lists (one per query)
        """
        logger.info("batch_vector_search_started", total_queries=len(queries))

        all_results = []
        
        for i, query_vector in enumerate(queries):
            try:
                results = await vector_searcher.search(
                    query_vector=query_vector,
                    table=table,
                    top_k=top_k,
                )
                all_results.append(results)
            except Exception as e:
                logger.warning("batch_query_failed", index=i, error=str(e))
                all_results.append([])

        logger.info(
            "batch_vector_search_completed",
            total_queries=len(queries),
            successful=sum(1 for r in all_results if r),
        )

        return all_results


vector_searcher = VectorSearcher()
batch_vector_searcher = BatchVectorSearcher()