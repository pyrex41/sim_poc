"""Prometheus metrics registry."""

from prometheus_client import Counter, Histogram

REQUEST_LATENCY = Histogram(
    "prompt_parser_request_latency_seconds",
    "Request latency",
    ["endpoint"],
)
REQUEST_ERRORS = Counter(
    "prompt_parser_request_errors_total",
    "Total request errors",
    ["endpoint"],
)
CACHE_HITS = Counter("prompt_parser_cache_hits_total", "Total cache hits")
CACHE_MISSES = Counter("prompt_parser_cache_misses_total", "Total cache misses")

