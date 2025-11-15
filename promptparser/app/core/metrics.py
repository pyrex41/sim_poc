"""Prometheus metrics registry."""

from prometheus_client import Counter, Histogram

REQUEST_LATENCY = Histogram("prompt_parser_request_latency_seconds", "Request latency", ["endpoint"])
REQUEST_ERRORS = Counter("prompt_parser_request_errors_total", "Total request errors", ["endpoint"])

