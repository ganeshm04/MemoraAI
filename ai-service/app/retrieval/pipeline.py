"""
MemoraAI - Retrieval Pipeline
Unified retrieval pipeline combining vector search, BM25, RRF fusion, and reranking.
"""

from typing import Optional
from dataclasses import dataclass, field
from enum import Enum
import structlog

from app.config import config
from app.retrieval.vector_search import vector_searcher, VectorSearcher, SearchResult
from app.retrieval.bm25 import bm25_searcher, BM25Searcher, BM25Result
from app.retrieval.fusion import rrf_fusion, ReciprocalRankFusion, FusedResult, score_normalizer
from app.retrieval.reranker import reranking_pipeline, RerankingPipeline
from app.embeddings.embedder import embedder

logger = structlog.get_logger(__name__)


class QueryType(Enum):
    """Query classification types."""
    CONVERSATIONAL = "conversational"
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    MEMORY_RELATED = "memory_related"


@dataclass
class RetrievalResult:
    """Complete retrieval result with all metadata."""
    id: int
    content: str
    metadata: dict
    fused_score: float
    vector_score: float = 0.0
    bm25_score: float = 0.0
    rerank_score: float = 0.0
    vector_rank: int = 0
    bm25_rank: int = 0
    source: str = ""
    chunk_index: int = 0


@dataclass
class PipelineConfig:
    """Configuration for the retrieval pipeline."""
    top_k_initial: int = 10
    top_k_final: int = 5
    use_reranking: bool = True
    use_bm25: bool = True
    use_vector: bool = True
    similarity_threshold: float = 0.7
    rrf_k: int = 60
    weights: dict = field(default_factory=lambda: {"vector": 0.5, "bm25": 0.5})


class RetrievalPipeline:
    """
    Unified retrieval pipeline with hybrid search and reranking.
    
    Pipeline:
    1. Query classification (adaptive routing)
    2. Vector search (pgvector)
    3. BM25 search (PostgreSQL FTS)
    4. RRF fusion
    5. Cross-encoder reranking
    6. Return top-k results
    """

    def __init__(self, pipeline_config: Optional[PipelineConfig] = None):
        from app.config import config as app_config
        self.config = pipeline_config or PipelineConfig(
            top_k_initial=app_config.vector.top_k,
            top_k_final=app_config.vector.top_k_reranked,
            use_reranking=True,
            similarity_threshold=app_config.vector.similarity_threshold,
            rrf_k=app_config.retrieval.rrf_k,
        )
        self.vector_searcher = VectorSearcher()
        self.bm25_searcher = BM25Searcher()
        self.fusion = ReciprocalRankFusion()
        self.reranking = reranking_pipeline

    async def search(
        self,
        query: str,
        query_type: QueryType = None,
        top_k: int = None,
        use_reranking: bool = None,
    ) -> list[RetrievalResult]:
        """
        Perform hybrid retrieval with fusion and reranking.
        
        Args:
            query: Search query
            query_type: Optional query type classification
            top_k: Number of final results (default from config)
            use_reranking: Whether to use reranking
            
        Returns:
            List of RetrievalResult sorted by relevance
        """
        top_k = top_k or self.config.top_k_final
        use_reranking = use_reranking if use_reranking is not None else self.config.use_reranking

        logger.info(
            "retrieval_pipeline_started",
            query=query[:100],
            query_type=query_type.value if query_type else "auto",
            top_k=top_k,
        )

        try:
            if query_type == QueryType.CONVERSATIONAL:
                logger.info("query_classified_conversational_skipping_retrieval")
                return []

            vector_results = []
            bm25_results = []

            if self.config.use_vector:
                vector_results = await self._vector_search(query)
                logger.info("vector_search_completed", results=len(vector_results))

            if self.config.use_bm25:
                bm25_results = await self._bm25_search(query)
                logger.info("bm25_search_completed", results=len(bm25_results))

            fused_results = await self._fuse_results(vector_results, bm25_results)
            logger.info("fusion_completed", results=len(fused_results))

            if use_reranking and fused_results:
                fused_results = await self._rerank_results(query, fused_results)

            final_results = fused_results[:top_k]

            retrieval_results = []
            for rank, result in enumerate(final_results, 1):
                retrieval_results.append(
                    RetrievalResult(
                        id=result.id,
                        content=result.content,
                        metadata=result.metadata,
                        fused_score=result.fused_score,
                        vector_score=getattr(result, "vector_score", 0),
                        bm25_score=getattr(result, "bm25_score", 0),
                        rerank_score=getattr(result, "rerank_score", 0),
                        vector_rank=getattr(result, "vector_rank", 0),
                        bm25_rank=getattr(result, "bm25_rank", 0),
                        source=result.source,
                        chunk_index=result.metadata.get("chunk_index", 0),
                    )
                )

            logger.info(
                "retrieval_pipeline_completed",
                query=query[:50],
                final_results=len(retrieval_results),
            )

            return retrieval_results

        except Exception as e:
            logger.error("retrieval_pipeline_failed", error=str(e))
            raise

    async def _vector_search(self, query: str) -> list[SearchResult]:
        """Perform vector similarity search."""
        try:
            query_vector = await embedder.embed_query(query)
            results = await self.vector_searcher.search(
                query_vector=query_vector,
                top_k=self.config.top_k_initial,
            )
            return results
        except Exception as e:
            logger.error("vector_search_in_pipeline_failed", error=str(e))
            return []

    async def _bm25_search(self, query: str) -> list[BM25Result]:
        """Perform BM25 keyword search."""
        try:
            results = await self.bm25_searcher.search(
                query=query,
                top_k=self.config.top_k_initial,
            )
            return results
        except Exception as e:
            logger.error("bm25_search_in_pipeline_failed", error=str(e))
            return []

    async def _fuse_results(
        self,
        vector_results: list[SearchResult],
        bm25_results: list[BM25Result],
    ) -> list[FusedResult]:
        """Fuse vector and BM25 results using RRF."""
        import time
        from app.observability.metrics import retrieval_metrics

        start_time = time.perf_counter()

        if not vector_results and not bm25_results:
            return []

        if not vector_results:
            fused = [FusedResult(
                id=r.id,
                content=r.content,
                metadata=r.metadata,
                fused_score=r.score,
                bm25_rank=r.rank,
                source=r.source,
            ) for r in bm25_results]
        elif not bm25_results:
            fused = [FusedResult(
                id=r.id,
                content=r.content,
                metadata=r.metadata,
                fused_score=r.score,
                vector_rank=r.rank,
                source=r.source,
            ) for r in vector_results]
        else:
            fused = self.fusion.fuse(
                vector_results=vector_results,
                bm25_results=bm25_results,
                k=self.config.rrf_k,
            )

            for result in fused:
                for vr in vector_results:
                    if vr.id == result.id:
                        result.vector_score = vr.score
                        result.vector_rank = vr.rank
                        break
                for br in bm25_results:
                    if br.id == result.id:
                        result.bm25_score = br.score
                        result.bm25_rank = br.rank
                        break

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        retrieval_metrics.record_fusion(duration_ms, len(vector_results) + len(bm25_results), len(fused))

        return fused

    async def _rerank_results(
        self,
        query: str,
        results: list[FusedResult],
    ) -> list[FusedResult]:
        """Rerank fused results using cross-encoder."""
        import time
        from app.observability.metrics import retrieval_metrics

        start_time = time.perf_counter()
        try:
            docs = [{
                "content": r.content,
                "metadata": r.metadata,
            } for r in results]

            reranked = await self.reranking.rerank_results(
                query=query,
                results=docs,
                top_k=len(results),
            )

            for idx, rerank_result in enumerate(reranked):
                original_idx = rerank_result.get("original_index", idx)
                if original_idx < len(results):
                    results[original_idx].rerank_score = rerank_result.get("rerank_score", 0)

            results.sort(key=lambda x: x.rerank_score if x.rerank_score > 0 else x.fused_score, reverse=True)
            
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            retrieval_metrics.record_rerank(duration_ms, len(results), len(results))

            return results

        except Exception as e:
            retrieval_metrics.record_failure("rerank", type(e).__name__)
            logger.warning("reranking_in_pipeline_failed", error=str(e))
            return results

    def update_config(self, **kwargs) -> None:
        """Update pipeline configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        logger.info("pipeline_config_updated", updates=kwargs)


class AdaptiveRetrieval:
    """Adaptive retrieval that adjusts based on query type."""

    def __init__(self):
        self.pipeline = RetrievalPipeline()

    async def search(
        self,
        query: str,
        query_type: QueryType = None,
        user_context: dict = None,
    ) -> list[RetrievalResult]:
        """
        Perform adaptive retrieval based on query type.
        
        Args:
            query: Search query
            query_type: Classified query type
            user_context: User context for memory-based queries
            
        Returns:
            List of RetrievalResult
        """
        query_type = query_type or self._classify_query(query)

        logger.info(
            "adaptive_retrieval_started",
            query=query[:50],
            query_type=query_type.value,
        )

        if query_type == QueryType.CONVERSATIONAL:
            logger.info("skipping_retrieval_conversational_query")
            return []

        if query_type == QueryType.MEMORY_RELATED:
            logger.info("memory_related_query_handling")
            return await self._handle_memory_query(query, user_context)

        return await self.pipeline.search(
            query=query,
            query_type=query_type,
        )

    def _classify_query(self, query: str) -> QueryType:
        """Classify query type based on content."""
        query_lower = query.lower()

        memory_keywords = ["remember", "past", "yesterday", "before", "earlier", "previous", "stored", "learned"]
        for keyword in memory_keywords:
            if keyword in query_lower:
                return QueryType.MEMORY_RELATED

        factual_keywords = ["what is", "who is", "where is", "when did", "how many", "define", "explain"]
        for keyword in factual_keywords:
            if keyword in query_lower:
                return QueryType.FACTUAL

        analytical_keywords = ["analyze", "compare", "contrast", "evaluate", "why", "how does", "relationship"]
        for keyword in analytical_keywords:
            if keyword in query_lower:
                return QueryType.ANALYTICAL

        return QueryType.FACTUAL

    async def _handle_memory_query(
        self,
        query: str,
        user_context: dict = None,
    ) -> list[RetrievalResult]:
        """Handle memory-related queries."""
        logger.info("handling_memory_query")
        return []


retrieval_pipeline = RetrievalPipeline()
adaptive_retrieval = AdaptiveRetrieval()