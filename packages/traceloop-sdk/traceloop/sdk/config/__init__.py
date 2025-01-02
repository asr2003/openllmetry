import os


def is_tracing_enabled() -> bool:
    return (os.getenv("TRACELOOP_TRACING_ENABLED") or "true").lower() == "true"


def is_content_tracing_enabled() -> bool:
    return (os.getenv("TRACELOOP_TRACE_CONTENT") or "true").lower() == "true"


def is_metrics_enabled() -> bool:
    return (os.getenv("TRACELOOP_METRICS_ENABLED") or "true").lower() == "true"


def is_logging_enabled() -> bool:
    return (os.getenv("TRACELOOP_LOGGING_ENABLED") or "false").lower() == "true"

def use_legacy_attributes() -> bool:
    """
    Determines whether the SDK should use legacy attributes for tracing and metrics.
    Defaults to True if the environment variable is not set.
    """
    return (os.getenv("TRACELOOP_USE_LEGACY_ATTRIBUTES") or "true").lower() == "true"
