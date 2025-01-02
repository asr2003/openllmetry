import dataclasses
import json
import logging
import os
import traceback
from opentelemetry import context as context_api
from opentelemetry.instrumentation.langchain.config import Config
from opentelemetry._events import Event, EventLogger
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes as GenAIAttributes
from pydantic import BaseModel

class CallbackFilteredJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, dict):
            if "callbacks" in o:
                del o["callbacks"]
                return o

        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)

        if hasattr(o, "to_json"):
            return o.to_json()

        if isinstance(o, BaseModel) and hasattr(o, "model_dump_json"):
            return o.model_dump_json()

        return super().default(o)


def should_send_prompts():
    return (
        os.getenv("TRACELOOP_TRACE_CONTENT") or "true"
    ).lower() == "true" or context_api.get_value("override_enable_content_tracing")


def dont_throw(func):
    """
    A decorator that wraps the passed in function and logs exceptions instead of throwing them.

    @param func: The function to wrap
    @return: The wrapper function
    """
    # Obtain a logger specific to the function's module
    logger = logging.getLogger(func.__module__)

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.debug(
                "OpenLLMetry failed to trace in %s, error: %s",
                func.__name__,
                traceback.format_exc(),
            )
            if Config.exception_logger:
                Config.exception_logger(e)

    return wrapper

def emit_event(event_logger, name, attributes, body, trace_id, span_id):
    """Helper function to emit an OpenTelemetry event."""
    event_logger.emit(
        Event(
            name=name,
            attributes=attributes,
            body=body,
            trace_id=trace_id,
            span_id=span_id,
        )
    )

def emit_user_message_event(event_logger, message, trace_id, span_id, capture_content):
    """Emit an event for user messages."""
    body = {"role": "user"}
    if capture_content:
        body["content"] = message.get("content")
    emit_event(event_logger, "gen_ai.user.message", {GenAIAttributes.GEN_AI_SYSTEM: "langchain"}, body, trace_id, span_id)

def emit_system_message_event(event_logger, content, trace_id, span_id, capture_content):
    """Emit an event for system messages."""
    body = {"role": "system"}
    if capture_content:
        body["content"] = content
    emit_event(event_logger, "gen_ai.system.message", {GenAIAttributes.GEN_AI_SYSTEM: "langchain"}, body, trace_id, span_id)

def emit_assistant_message_event(event_logger, message, trace_id, span_id, capture_content):
    """Emit an event for assistant messages."""
    body = {"role": "assistant"}
    if capture_content:
        body["content"] = message.get("content")
    emit_event(event_logger, "gen_ai.assistant.message", {GenAIAttributes.GEN_AI_SYSTEM: "langchain"}, body, trace_id, span_id)

def emit_choice_event(event_logger, choice, trace_id, span_id, capture_content):
    """Emit an event for a choice."""
    body = {
        "index": choice.get("index", 0),
        "finish_reason": choice.get("finish_reason", "unknown"),
        "message": {}
    }
    if capture_content:
        body["message"]["content"] = choice.get("content")
    emit_event(event_logger, "gen_ai.choice", {GenAIAttributes.GEN_AI_SYSTEM: "langchain"}, body, trace_id, span_id)
