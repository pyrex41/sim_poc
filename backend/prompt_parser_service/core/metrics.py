"""Metrics registry (no-op for now)."""

# No-op metrics since we're not using Prometheus
class NoOpMetric:
    def __init__(self, *args, **kwargs):
        pass

    def inc(self, *args, **kwargs):
        pass

    def dec(self, *args, **kwargs):
        pass

    def observe(self, *args, **kwargs):
        pass

    def time(self, *args, **kwargs):
        return lambda: None

REQUEST_LATENCY = NoOpMetric()
REQUEST_ERRORS = NoOpMetric()
CACHE_HITS = NoOpMetric()
CACHE_MISSES = NoOpMetric()

