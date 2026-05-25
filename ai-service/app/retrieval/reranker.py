"""
MemoraAI - Cross-Encoder Reranker
Transformer-based reranking for improved retrieval precision.
"""

from typing import Optional
from dataclasses import dataclass
import structlog

from app.config import config

logger = structlog.get_logger(__name__)


@dataclass
class RerankResult:
    """Result from reranking."""
    index: int
    score: float
    content: str
    metadata: dict


class CrossEncoderReranker:
    """
    Cross-encoder reranking using sentence-transformers.
    
    Model: cross-encoder/ms-marco-MiniLM-L-6-v2
    
    Features:
    - Semantic relevance scoring
    - Query-document pair scoring
    - Configurable top-k selection
    - GPU acceleration support
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.settings.RERANKER_MODEL
        self._model = None
        self._tokenizer = None
        self._device = None

    def _load_model(self) -> None:
        """Lazy load the cross-encoder model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import CrossEncoder
            import torch

            logger.info("loading_reranker_model", model=self.model_name)

            self._model = CrossEncoder(self.model_name, max_length=512)
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._model.model.to(self._device)

            logger.info("reranker_model_loaded", device=self._device)

        except ImportError as e:
            logger.error("sentence_transformers_not_installed", error=str(e))
            raise
        except Exception as e:
            logger.error("reranker_model_load_failed", error=str(e))
            raise

    async def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 5,
    ) -> list[RerankResult]:
        """
        Rerank documents based on query relevance.
        
        Args:
            query: Search query
            documents: List of document dicts with 'content' and 'metadata'
            top_k: Number of top results to return
            
        Returns:
            List of RerankResult sorted by relevance score
        """
        if not documents:
            logger.warning("rerank_empty_documents")
            return []

        self._load_model()

        logger.info(
            "reranking_started",
            query=query[:50],
            document_count=len(documents),
            top_k=top_k,
        )

        try:
            doc_texts = [doc.get("content", "") for doc in documents]
            pairs = [(query, text) for text in doc_texts]

            scores = self._model.predict(pairs, show_progress_bar=False)

            if isinstance(scores, list):
                scores = scores
            else:
                scores = scores.tolist()

            results = []
            for idx, (doc, score) in enumerate(zip(documents, scores)):
                results.append(
                    RerankResult(
                        index=idx,
                        score=float(score),
                        content=doc.get("content", ""),
                        metadata=doc.get("metadata", {}),
                    )
                )

            results.sort(key=lambda x: x.score, reverse=True)
            top_results = results[:top_k]

            logger.info(
                "reranking_completed",
                query=query[:50],
                original_count=len(documents),
                returned_count=len(top_results),
            )

            return top_results

        except Exception as e:
            logger.error("reranking_failed", error=str(e))
            raise

    async def rerank_with_metadata(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 5,
        include_scores: bool = True,
    ) -> list[dict]:
        """
        Rerank and return documents with metadata.
        
        Args:
            query: Search query
            documents: List of documents
            top_k: Number of results
            include_scores: Include rerank scores in results
            
        Returns:
            List of dicts with reranked documents and scores
        """
        results = await self.rerank(query, documents, top_k)

        reranked = []
        for result in results:
            doc = {
                "content": result.content,
                "metadata": result.metadata,
                "rerank_score": result.score if include_scores else None,
                "original_index": result.index,
            }
            reranked.append(doc)

        return reranked

    def get_scores_batch(
        self,
        queries: list[str],
        documents: list[str],
    ) -> list[list[float]]:
        """
        Get relevance scores for multiple query-document pairs.
        
        Args:
            queries: List of queries
            documents: List of documents
            
        Returns:
            Matrix of scores [query_idx][doc_idx]
        """
        self._load_model()

        pairs = [(q, d) for q in queries for d in documents]
        scores = self._model.predict(pairs)

        if hasattr(scores, 'tolist'):
            scores = scores.tolist()

        matrix = []
        for i, query in enumerate(queries):
            query_scores = scores[i * len(documents): (i + 1) * len(documents)]
            matrix.append(query_scores)

        return matrix

    def clear_cache(self) -> None:
        """Clear model cache to free memory."""
        if self._model:
            import torch
            if hasattr(self._model, 'model'):
                del self._model.model
            self._model = None
            self._tokenizer = None
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("reranker_cache_cleared")


class RerankingPipeline:
    """
    Complete reranking pipeline with fallback handling.
    """

    def __init__(self):
        self.reranker = CrossEncoderReranker()
        self.use_reranking = True

    async def rerank_results(
        self,
        query: str,
        results: list[dict],
        top_k: int = 5,
        use_reranking: bool = True,
    ) -> list[dict]:
        """
        Rerank retrieval results with optional fallback.
        
        Args:
            query: Search query
            results: Raw retrieval results
            top_k: Number of results to return
            use_reranking: Whether to use reranking
            
        Returns:
            Reranked results
        """
        if not use_reranking or not results:
            logger.info("reranking_skipped", reason="disabled_or_empty")
            return results[:top_k]

        try:
            reranked = await self.reranker.rerank_with_metadata(
                query=query,
                documents=results,
                top_k=top_k,
            )
            return reranked

        except Exception as e:
            logger.warning("reranking_failed_using_raw_results", error=str(e))
            return results[:top_k]

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable reranking."""
        self.use_reranking = enabled
        logger.info("reranking_toggled", enabled=enabled)


reranker = CrossEncoderReranker()
reranking_pipeline = RerankingPipeline()