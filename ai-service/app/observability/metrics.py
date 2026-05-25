"""
MemoraAI - Metrics
Prometheus metrics for observability.
"""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point."""
    value: float
    timestamp: datetime
    labels: dict


class MetricsCollector:
    """
    Metrics collection for observability.
    
    Tracks:
    - Retrieval latency
    - Rerank scores
    - Token usage
    - Memory usage
    - Error rates
    """

    def __init__(self):
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._timestamps: dict[str, datetime] = {}

    def increment(self, metric: str, value: float = 1.0, labels: dict = None) -> None:
        """Increment a counter metric."""
        key = self._make_key(metric, labels)
        self._counters[key] += value

    def gauge(self, metric: str, value: float, labels: dict = None) -> None:
        """Set a gauge metric."""
        key = self._make_key(metric, labels)
        self._gauges[key] = value
        self._timestamps[key] = datetime.now()

    def histogram(self, metric: str, value: float, labels: dict = None) -> None:
        """Record a histogram value."""
        key = self._make_key(metric, labels)
        self._histograms[key].append(value)

        if len(self._histograms[key]) > 1000:
            self._histograms[key] = self._histograms[key][-1000:]

    def timing(self, metric: str, duration_ms: float, labels: dict = None) -> None:
        """Record timing metric."""
        self.histogram(f"{metric}_duration_ms", duration_ms, labels)

    def _make_key(self, metric: str, labels: dict = None) -> str:
        """Create metric key from name and labels."""
        if not labels:
            return metric
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{metric}{{{label_str}}}"

    def get_counter(self, metric: str, labels: dict = None) -> float:
        """Get counter value."""
        key = self._make_key(metric, labels)
        return self._counters.get(key, 0.0)

    def get_gauge(self, metric: str, labels: dict = None) -> Optional[float]:
        """Get gauge value."""
        key = self._make_key(metric, labels)
        return self._gauges.get(key)

    def get_histogram_stats(self, metric: str, labels: dict = None) -> dict:
        """Get histogram statistics."""
        key = self._make_key(metric, labels)
        values = self._histograms.get(key, [])

        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0, "p50": 0, "p95": 0, "p99": 0}

        sorted_values = sorted(values)
        n = len(sorted_values)

        return {
            "count": n,
            "sum": sum(values),
            "avg": sum(values) / n,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": sorted_values[int(n * 0.5)],
            "p95": sorted_values[int(n * 0.95)] if n > 1 else sorted_values[0],
            "p99": sorted_values[int(n * 0.99)] if n > 1 else sorted_values[0],
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._timestamps.clear()


class RetrievalMetrics:
    """Metrics specific to retrieval operations."""

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def record_search(self, method: str, duration_ms: float, results_count: int) -> None:
        """Record search operation metrics."""
        self.collector.increment("retrieval_search_total", labels={"method": method})
        self.collector.timing("retrieval_search", duration_ms, {"method": method})
        self.collector.histogram("retrieval_results_count", results_count, {"method": method})

    def record_fusion(self, duration_ms: float, input_count: int, output_count: int) -> None:
        """Record fusion operation metrics."""
        self.collector.increment("retrieval_fusion_total")
        self.collector.timing("retrieval_fusion", duration_ms)
        self.collector.histogram("retrieval_fusion_input", input_count)
        self.collector.histogram("retrieval_fusion_output", output_count)

    def record_rerank(self, duration_ms: float, input_count: int, output_count: int) -> None:
        """Record reranking metrics."""
        self.collector.increment("retrieval_rerank_total")
        self.collector.timing("retrieval_rerank", duration_ms)
        self.collector.histogram("retrieval_rerank_input", input_count)
        self.collector.histogram("retrieval_rerank_output", output_count)

    def record_failure(self, operation: str, error_type: str) -> None:
        """Record retrieval failure."""
        self.collector.increment("retrieval_failures_total", labels={"operation": operation, "error_type": error_type})


class GenerationMetrics:
    """Metrics specific to generation operations."""

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def record_generation(
        self,
        duration_ms: float,
        tokens_used: int,
        finish_reason: str,
    ) -> None:
        """Record generation metrics."""
        self.collector.increment("generation_total")
        self.collector.timing("generation", duration_ms)
        self.collector.histogram("generation_tokens_used", tokens_used)
        self.collector.increment("generation_finish_reasons", labels={"reason": finish_reason})

    def record_embedding(self, duration_ms: float, count: int) -> None:
        """Record embedding generation metrics."""
        self.collector.increment("embedding_total")
        self.collector.timing("embedding", duration_ms)
        self.collector.histogram("embedding_batch_size", count)


class MemoryMetrics:
    """Metrics specific to memory operations."""

    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    def record_memory_operation(self, operation: str, memory_type: str, count: int = 1) -> None:
        """Record memory operation."""
        self.collector.increment(f"memory_{operation}_total", labels={"memory_type": memory_type})
        self.collector.histogram(f"memory_{operation}_count", count, {"memory_type": memory_type})


metrics = MetricsCollector()
retrieval_metrics = RetrievalMetrics(metrics)
generation_metrics = GenerationMetrics(metrics)
memory_metrics = MemoryMetrics(metrics)