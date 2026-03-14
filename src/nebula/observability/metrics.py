from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "nebula_http_requests_total",
    "Total HTTP requests handled by Nebula.",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "nebula_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
)

CACHE_LOOKUPS = Counter(
    "nebula_cache_lookups_total",
    "Total semantic cache lookups.",
    ["result"],
)

COMPLETION_COUNT = Counter(
    "nebula_chat_completions_total",
    "Total completion attempts by provider type.",
    ["provider", "result", "stream"],
)

FALLBACK_COUNT = Counter(
    "nebula_fallback_total",
    "Total fallbacks from local to premium provider.",
    ["reason"],
)

ROUTE_DECISION_COUNT = Counter(
    "nebula_route_decisions_total",
    "Total routing decisions before provider execution.",
    ["target", "reason", "stream"],
)

PROVIDER_LATENCY = Histogram(
    "nebula_provider_duration_seconds",
    "Provider completion latency in seconds.",
    ["provider", "mode", "result"],
)
