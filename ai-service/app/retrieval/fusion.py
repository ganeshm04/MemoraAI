"""
MemoraAI - Reciprocal Rank Fusion (RRF)
Hybrid search result fusion using RRF algorithm.
"""

from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict
import structlog

from app.config import config as app_config

logger = structlog.get_logger(__name__)


@dataclass
class FusedResult:
    """Result from RRF fusion."""
    id: int
    content: str
    metadata: dict
    fused_score: float
    vector_rank: int = 0
    bm25_rank: int = 0
    source: str = ""
    rerank_score: float = 0.0


@dataclass
class FusionConfig:
    """Configuration for RRF fusion."""
    k: int = 60
    weights: dict = field(default_factory=lambda: {"vector": 0.5, "bm25": 0.5})


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion for combining search results.
    
    Algorithm:
    RRF_score = Σ 1 / (k + rank_i)
    
    Benefits:
    - Reduces position bias
    - Improves retrieval diversity
    - Better ranking quality
    """

    def __init__(self, config: Optional[FusionConfig] = None):
        self.config = config or FusionConfig(k=app_config.retrieval.rrf_k)
        self.weights = self.config.weights

    def fuse(
        self,
        vector_results: list,
        bm25_results: list,
        k: int = None,
    ) -> list[FusedResult]:
        """
        Fuse vector and BM25 results using RRF.
        
        Args:
            vector_results: Results from vector search
            bm25_results: Results from BM25 search
            k: RRF constant (default from config)
            
        Returns:
            Sorted list of FusedResult
        """
        k = k or self.config.k

        logger.info(
            "fusion_started",
            vector_count=len(vector_results),
            bm25_count=len(bm25_results),
            k=k,
        )

        fused_scores = defaultdict(float)
        result_map = {}

        for rank, result in enumerate(vector_results, 1):
            score = 1.0 / (k + rank)
            fused_scores[result.id] += self.weights.get("vector", 0.5) * score
            result_map[result.id] = result

        for rank, result in enumerate(bm25_results, 1):
            score = 1.0 / (k + rank)
            fused_scores[result.id] += self.weights.get("bm25", 0.5) * score
            result_map[result.id] = result

        fused_results = []
        for doc_id, score in fused_scores.items():
            result = result_map[doc_id]
            fused_results.append(
                FusedResult(
                    id=doc_id,
                    content=getattr(result, "content", ""),
                    metadata=getattr(result, "metadata", {}),
                    fused_score=score,
                    vector_rank=getattr(result, "rank", 0),
                    bm25_rank=getattr(result, "rank", 0),
                    source=getattr(result, "source", ""),
                )
            )

        fused_results.sort(key=lambda x: x.fused_score, reverse=True)

        logger.info(
            "fusion_completed",
            total_fused=len(fused_results),
        )

        return fused_results

    def fuse_with_scores(
        self,
        vector_results: list,
        bm25_results: list,
        vector_scores: list[float],
        bm25_scores: list[float],
        k: int = None,
    ) -> list[FusedResult]:
        """
        Fuse results with pre-computed scores (normalized).
        
        Args:
            vector_results: Vector search results
            bm25_results: BM25 results
            vector_scores: Pre-computed vector similarity scores
            bm25_scores: Pre-computed BM25 scores
            k: RRF constant
            
        Returns:
            List of FusedResult with combined scores
        """
        k = k or self.config.k

        fused_scores = defaultdict(float)
        result_map = {}

        for idx, result in enumerate(vector_results):
            rrf_score = 1.0 / (k + idx + 1)
            combined = (self.weights.get("vector", 0.5) * rrf_score) + \
                      ((1 - self.weights.get("vector", 0.5)) * vector_scores[idx])
            fused_scores[result.id] += combined
            result_map[result.id] = result

        for idx, result in enumerate(bm25_results):
            rrf_score = 1.0 / (k + idx + 1)
            combined = (self.weights.get("bm25", 0.5) * rrf_score) + \
                      ((1 - self.weights.get("bm25", 0.5)) * bm25_scores[idx])
            fused_scores[result.id] += combined
            result_map[result.id] = result

        fused_results = []
        for doc_id, score in fused_scores.items():
            result = result_map[doc_id]
            fused_results.append(
                FusedResult(
                    id=doc_id,
                    content=getattr(result, "content", ""),
                    metadata=getattr(result, "metadata", {}),
                    fused_score=score,
                    source=getattr(result, "source", ""),
                )
            )

        fused_results.sort(key=lambda x: x.fused_score, reverse=True)
        return fused_results

    def fuse_multiple_sources(
        self,
        results_by_source: dict[str, list],
        k: int = None,
    ) -> list[FusedResult]:
        """
        Fuse results from multiple retrieval sources.
        
        Args:
            results_by_source: Dict of {source_name: results_list}
            k: RRF constant
            
        Returns:
            List of FusedResult
        """
        k = k or self.config.k

        fused_scores = defaultdict(float)
        result_map = {}

        for source, results in results_by_source.items():
            weight = self.weights.get(source, 1.0 / len(results_by_source))
            
            for rank, result in enumerate(results, 1):
                score = 1.0 / (k + rank)
                fused_scores[result.id] += weight * score
                result_map[result.id] = result

        fused_results = []
        for doc_id, score in fused_scores.items():
            result = result_map[doc_id]
            fused_results.append(
                FusedResult(
                    id=doc_id,
                    content=getattr(result, "content", ""),
                    metadata=getattr(result, "metadata", {}),
                    fused_score=score,
                    source=getattr(result, "source", ""),
                )
            )

        fused_results.sort(key=lambda x: x.fused_score, reverse=True)
        return fused_results


class ScoreNormalizer:
    """Utility for normalizing scores from different sources."""

    @staticmethod
    def min_max_normalize(scores: list[float]) -> list[float]:
        """Normalize scores to 0-1 range."""
        if not scores:
            return []
        
        min_s, max_s = min(scores), max(scores)
        if max_s == min_s:
            return [1.0] * len(scores)
        
        return [(s - min_s) / (max_s - min_s) for s in scores]

    @staticmethod
    def percentile_normalize(scores: list[float]) -> list[float]:
        """Normalize scores to percentile ranks."""
        if not scores:
            return []
        
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        
        return [sorted_scores.index(s) / n for s in scores]

    @staticmethod
    def rank_normalize(scores: list[float]) -> list[float]:
        """Convert scores to rank-based normalized scores."""
        if not scores:
            return []
        
        indexed_scores = [(s, i) for i, s in enumerate(scores)]
        indexed_scores.sort(key=lambda x: x[0], reverse=True)
        
        result = [0.0] * len(scores)
        for rank, (_, idx) in enumerate(indexed_scores, 1):
            result[idx] = 1.0 / rank
        
        return result


rrf_fusion = ReciprocalRankFusion()
score_normalizer = ScoreNormalizer()