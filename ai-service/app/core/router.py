"""
MemoraAI - Core Router
Adaptive query routing based on query classification.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class QueryType(Enum):
    """Query classification types for adaptive routing."""
    CONVERSATIONAL = "conversational"
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    MEMORY_RELATED = "memory_related"
    MIXED = "mixed"


@dataclass
class RoutingDecision:
    """Routing decision with strategy and metadata."""
    query_type: QueryType
    strategy: str
    requires_retrieval: bool
    requires_memory: bool
    confidence: float
    reasoning: str


class QueryClassifier:
    """Classify queries to determine retrieval strategy."""

    CONVERSATIONAL_PATTERNS = [
        r"^(hi|hello|hey|howdy)",
        r"^(thanks?|thank you|appreciate)",
        r"^(bye|goodbye|see you)",
        r"^(okay|ok|sure|yes|no|yeah|yep)",
        r"what('s| is) up",
        r"(how are|how('s| is) it|how('s| is) everything)",
        r"(can|could) you (help|assist)",
        r"(just|just wanted to) (say|ask|check)",
        r"(no problem|sure thing|sounds good)",
    ]

    FACTUAL_PATTERNS = [
        r"^(what is|what are|what's|what were)",
        r"^(who is|who are|who was|who were|who's)",
        r"^(where is|where are|where was|where were)",
        r"^(when did|when is|when was|when will)",
        r"^(how many|how much|how long|how far)",
        r"^(define|definition of)",
        r"^(explain|tell me about)",
        r"^(list|give me)",
        r"(is there|are there|does exist)",
    ]

    ANALYTICAL_PATTERNS = [
        r"^(analyze|analysis)",
        r"^(compare|contrast)",
        r"^(evaluate|assessment)",
        r"^(why|how does|relationship between)",
        r"(advantages?|disadvantages?)",
        r"(pros and cons)",
        r"(differences?|similarities?)",
        r"(causes?|effects?|impact)",
        r"(synthesize|summary|conclusion)",
    ]

    MEMORY_PATTERNS = [
        r"(remember|stored|learned)",
        r"(previously|earlier|before|beforehand)",
        r"(yesterday|last week|last time)",
        r"(my|your) (preferences?|interests?|facts?)",
        r"(told you|told me|said earlier)",
        r"(based on|according to)",
        r"(we discussed|we talked about)",
    ]

    def classify(self, query: str) -> tuple[QueryType, float]:
        """
        Classify query type with confidence score.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (QueryType, confidence)
        """
        query_lower = query.lower().strip()

        conversational_score = self._score_patterns(query_lower, self.CONVERSATIONAL_PATTERNS)
        factual_score = self._score_patterns(query_lower, self.FACTUAL_PATTERNS)
        analytical_score = self._score_patterns(query_lower, self.ANALYTICAL_PATTERNS)
        memory_score = self._score_patterns(query_lower, self.MEMORY_PATTERNS)

        scores = {
            QueryType.CONVERSATIONAL: conversational_score,
            QueryType.FACTUAL: factual_score,
            QueryType.ANALYTICAL: analytical_score,
            QueryType.MEMORY_RELATED: memory_score,
        }

        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]

        if max_score < 0.3:
            max_type = QueryType.FACTUAL
            max_score = 0.5

        logger.debug(
            "query_classified",
            query=query[:50],
            type=max_type.value,
            confidence=max_score,
        )

        return max_type, max_score

    def _score_patterns(self, query: str, patterns: list[str]) -> float:
        """Score query against patterns."""
        import re
        score = 0.0
        for pattern in patterns:
            if re.search(pattern, query):
                score += 0.25
        return min(score, 1.0)


class AdaptiveRouter:
    """
    Adaptive query router determining retrieval strategy.
    
    Decisions:
    - Conversational: Direct LLM response
    - Factual: Retrieval + generation
    - Analytical: Multi-hop retrieval
    - Memory-related: Memory search + generation
    """

    def __init__(self):
        self.classifier = QueryClassifier()

    def route(self, query: str, user_context: Optional[dict] = None) -> RoutingDecision:
        """
        Determine routing strategy for query.
        
        Args:
            query: User query
            user_context: Optional user context for memory decisions
            
        Returns:
            RoutingDecision with strategy
        """
        query_type, confidence = self.classifier.classify(query)

        requires_retrieval = query_type in [
            QueryType.FACTUAL,
            QueryType.ANALYTICAL,
        ]

        requires_memory = query_type == QueryType.MEMORY_RELATED

        strategy_map = {
            QueryType.CONVERSATIONAL: "direct_generation",
            QueryType.FACTUAL: "retrieval_augmented",
            QueryType.ANALYTICAL: "multi_hop_retrieval",
            QueryType.MEMORY_RELATED: "memory_retrieval",
            QueryType.MIXED: "hybrid_strategy",
        }

        strategy = strategy_map.get(query_type, "retrieval_augmented")

        reasoning_map = {
            QueryType.CONVERSATIONAL: "Query appears conversational, direct response sufficient",
            QueryType.FACTUAL: "Query requires factual information, retrieval recommended",
            QueryType.ANALYTICAL: "Query requires analysis, multi-hop retrieval needed",
            QueryType.MEMORY_RELATED: "Query references memory, memory search required",
        }

        decision = RoutingDecision(
            query_type=query_type,
            strategy=strategy,
            requires_retrieval=requires_retrieval,
            requires_memory=requires_memory,
            confidence=confidence,
            reasoning=reasoning_map.get(query_type, "Default retrieval strategy"),
        )

        logger.info(
            "routing_decision_made",
            query=query[:50],
            strategy=strategy,
            requires_retrieval=requires_retrieval,
            confidence=confidence,
        )

        return decision


class RouterManager:
    """Manage multiple routers for different domains."""

    def __init__(self):
        self.default_router = AdaptiveRouter()
        self.domain_routers = {}

    def add_domain_router(self, domain: str, router: AdaptiveRouter) -> None:
        """Add a domain-specific router."""
        self.domain_routers[domain] = router
        logger.info("domain_router_added", domain=domain)

    def get_router(self, domain: str = None) -> AdaptiveRouter:
        """Get router for domain or default."""
        return self.domain_routers.get(domain, self.default_router)

    def route_query(
        self,
        query: str,
        domain: str = None,
        user_context: dict = None,
    ) -> RoutingDecision:
        """Route query using appropriate router."""
        router = self.get_router(domain)
        return router.route(query, user_context)


router = AdaptiveRouter()
router_manager = RouterManager()
classifier = QueryClassifier()