"""
Monitoring and metrics collection.
"""
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logging import get_logger


class MetricsCollector:
    """
    Collects and tracks system metrics.
    
    Metrics tracked:
    - Order metrics (submitted, filled, rejected)
    - Execution metrics (fill rates, latency)
    - Risk metrics (Greeks, VaR, limits)
    - P&L metrics
    - System health metrics
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.logger = get_logger(__name__)
        self.metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.start_time = datetime.utcnow()
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Increment value
            tags: Optional tags for the metric
        """
        key = self._make_key(name, tags)
        self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge metric.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for the metric
        """
        key = self._make_key(name, tags)
        self.gauges[key] = value
    
    def record_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Record an event with associated data.
        
        Args:
            event_type: Type of event
            data: Event data
            timestamp: Event timestamp (default: now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        event = {
            'timestamp': timestamp.isoformat(),
            **data
        }
        
        self.metrics[event_type].append(event)
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get counter value."""
        key = self._make_key(name, tags)
        return self.counters.get(key, 0)
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get gauge value."""
        key = self._make_key(name, tags)
        return self.gauges.get(key)
    
    def get_events(self, event_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get events of a specific type.
        
        Args:
            event_type: Type of events to retrieve
            limit: Maximum number of events to return (None = all)
        
        Returns:
            List of events
        """
        events = self.metrics.get(event_type, [])
        if limit:
            return events[-limit:]
        return events
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all metrics.
        
        Returns:
            Dictionary with metric summary
        """
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            'uptime_seconds': uptime,
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'event_counts': {k: len(v) for k, v in self.metrics.items()}
        }
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Create a key from name and tags."""
        if not tags:
            return name
        
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()
        self.counters.clear()
        self.gauges.clear()
        self.start_time = datetime.utcnow()
        self.logger.info("Metrics reset")


# Global metrics collector instance
_global_metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return _global_metrics
