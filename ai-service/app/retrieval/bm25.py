"""
MemoraAI - BM25 Search
PostgreSQL Full-Text Search for keyword-based retrieval.
"""

from typing import Optional
from dataclasses import dataclass
import structlog
import json

from db.connection import db, fts_search
from app.config import config

logger = structlog.get_logger(__name__)


@dataclass
class BM25Result:
    """BM25 search result."""
    id: int
    content: str
    metadata: dict
    rank: int
    score: float
    headline: str = ""
    source: str = ""


class BM25Searcher:
    """
    BM25-style keyword search using PostgreSQL Full-Text Search.
    
    Features:
    - tsvector/tsrank for BM25-like scoring
    - Configurable ranking
    - Headline extraction for preview
    - Fast exact keyword matching
    """

    def __init__(self):
        self.k1 = config.retrieval.bm25_k1
        self.b = config.retrieval.bm25_b

    async def search(
        self,
        query: str,
        table: str = "chunks",
        top_k: int = 10,
        search_column: str = "content",
        language: str = "english",
    ) -> list[BM25Result]:
        """
        Perform BM25-style full-text search.
        
        Args:
            query: Search query string
            table: Table to search
            top_k: Number of results
            search_column: Column to search (default: content)
            language: Text search language
            
        Returns:
            List of BM25Result sorted by relevance
        """
        if not query or not query.strip():
            logger.warning("empty_query_for_bm25")
            return []

        logger.info(
            "bm25_search_started",
            query=query[:100],
            table=table,
            top_k=top_k,
        )

        import time
        from app.observability.metrics import retrieval_metrics

        start_time = time.perf_counter()
        try:
            results = await fts_search.search(
                table=table,
                query=query,
                top_k=top_k,
                search_column=search_column,
            )

            bm25_results = []
            for rank, row in enumerate(results, 1):
                meta = row["metadata"]
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        meta = {}
                if not isinstance(meta, dict):
                    meta = {}

                bm25_results.append(
                    BM25Result(
                        id=row["id"],
                        content=row["content"],
                        metadata=meta,
                        rank=rank,
                        score=row["bm25_score"],
                        headline=row.get("headline", ""),
                        source=meta.get("source", ""),
                    )
                )

            duration_ms = (time.perf_counter() - start_time) * 1000.0
            retrieval_metrics.record_search("bm25", duration_ms, len(bm25_results))

            logger.info(
                "bm25_search_completed",
                query=query[:100],
                results_found=len(bm25_results),
            )

            return bm25_results

        except Exception as e:
            retrieval_metrics.record_failure("bm25_search", type(e).__name__)
            logger.error("bm25_search_failed", error=str(e), query=query[:100])
            raise

    async def search_with_filters(
        self,
        query: str,
        table: str = "chunks",
        filters: dict = None,
        top_k: int = 10,
    ) -> list[BM25Result]:
        """
        Search with additional filters.
        
        Args:
            query: Search query
            table: Table to search
            filters: Dict of column:value filters
            top_k: Number of results
            
        Returns:
            List of BM25Result
        """
        filters = filters or {}

        try:
            async with db.acquire() as conn:
                conditions = [f"to_tsvector('{filters.get('language', 'english')}', content) @@ plainto_tsquery('{filters.get('language', 'english')}', $1)"]
                params = [query]
                
                param_index = 2
                for column, value in filters.items():
                    if column not in ("language",):
                        conditions.append(f"{column} = ${param_index}")
                        params.append(value)
                        param_index += 1

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                sql_query = f"""
                    SELECT 
                        id,
                        content,
                        metadata,
                        ts_rank(to_tsvector('{filters.get('language', 'english')}', content), plainto_tsquery('{filters.get('language', 'english')}', $1)) AS rank,
                        ts_headline('{filters.get('language', 'english')}', content, plainto_tsquery('{filters.get('language', 'english')}', $1)) AS headline
                    FROM {table}
                    WHERE {where_clause}
                    AND to_tsvector('{filters.get('language', 'english')}', content) @@ plainto_tsquery('{filters.get('language', 'english')}', $1)
                    ORDER BY rank DESC
                    LIMIT $2
                """

                results = await conn.fetch(sql_query, *params, top_k)

                bm25_results = []
                for rank, row in enumerate(results, 1):
                    meta = row["metadata"]
                    if isinstance(meta, str):
                        try:
                            meta = json.loads(meta)
                        except Exception:
                            meta = {}
                    if not isinstance(meta, dict):
                        meta = {}

                    bm25_results.append(
                        BM25Result(
                            id=row["id"],
                            content=row["content"],
                            metadata=meta,
                            rank=rank,
                            score=row["rank"],
                            headline=row.get("headline", ""),
                            source=meta.get("source", ""),
                        )
                    )

                return bm25_results

        except Exception as e:
            logger.error("bm25_search_with_filters_failed", error=str(e))
            raise

    async def expand_query(self, query: str) -> list[str]:
        """
        Expand query with synonyms and variations.
        
        Args:
            query: Original query
            
        Returns:
            List of query variations
        """
        words = query.split()
        expanded = [query]
        
        common_synonyms = {
            "ai": ["artificial intelligence", "machine learning", "ml"],
            "ml": ["machine learning", "ai"],
            "db": ["database"],
            "api": ["application programming interface"],
            "dev": ["development", "developer"],
        }
        
        for word in words:
            word_lower = word.lower()
            if word_lower in common_synonyms:
                for syn in common_synonyms[word_lower]:
                    expanded.append(query.replace(word, syn))
                    expanded.append(f"{query} {syn}")

        return list(set(expanded))[:5]


class BM25Scorer:
    """
    BM25 scoring utilities for custom implementations.
    """

    @staticmethod
    def calculate_bm25_score(
        term_freq: float,
        doc_len: float,
        avg_doc_len: float,
        doc_freq: float,
        total_docs: float,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> float:
        """
        Calculate BM25 score for a single term.
        
        Args:
            term_freq: Term frequency in document
            doc_len: Document length
            avg_doc_len: Average document length
            doc_freq: Document frequency (number of docs containing term)
            total_docs: Total number of documents
            k1: Term frequency saturation parameter
            b: Length normalization parameter
            
        Returns:
            BM25 score
        """
        idf = max(0, (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))
        idf = 1 + idf if idf > 0 else 0

        numerator = term_freq * (k1 + 1)
        denominator = term_freq + k1 * (1 - b + b * (doc_len / avg_doc_len))

        score = idf * (numerator / denominator)
        return score

    @staticmethod
    def normalize_scores(scores: list[float], method: str = "min_max") -> list[float]:
        """
        Normalize BM25 scores.
        
        Args:
            scores: List of BM25 scores
            method: Normalization method ('min_max' or 'z_score')
            
        Returns:
            Normalized scores
        """
        if not scores:
            return []

        if method == "min_max":
            min_s = min(scores)
            max_s = max(scores)
            if max_s == min_s:
                return [1.0] * len(scores)
            return [(s - min_s) / (max_s - min_s) for s in scores]
        
        elif method == "z_score":
            import statistics
            mean = statistics.mean(scores)
            stdev = statistics.stdev(scores) if len(scores) > 1 else 1
            if stdev == 0:
                return [1.0] * len(scores)
            return [(s - mean) / stdev for s in scores]

        return scores


bm25_searcher = BM25Searcher()
bm25_scorer = BM25Scorer()