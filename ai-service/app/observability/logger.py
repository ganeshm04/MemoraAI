"""
MemoraAI - Structured Logger
Production-grade logging with structured output.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Optional
from contextvars import ContextVar
import structlog

from app.config import config

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def add_context(key: str, value: Any) -> None:
    """Add context to structured logger."""
    structlog.contextvars.bind_contextvars(**{key: value})


def clear_context() -> None:
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()


class StructuredLogger:
    """
    Structured logging for production observability.
    
    Features:
    - JSON output for machine parsing
    - Context awareness
    - Request/trace IDs
    - Structured metadata
    """

    def __init__(self):
        self._configure_logging()

    def _configure_logging(self) -> None:
        """Configure structlog for production use."""
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, config.settings.LOG_LEVEL.upper(), logging.INFO),
        )

        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]

        if config.settings.LOG_FORMAT == "json":
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())

        structlog.configure(
            processors=processors,
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def bind_request(self, request_id: str) -> None:
        """Bind request ID to context."""
        add_context("request_id", request_id)

    def bind_session(self, session_id: str) -> None:
        """Bind session ID to context."""
        add_context("session_id", session_id)

    def bind_user(self, user_id: str) -> None:
        """Bind user ID to context."""
        add_context("user_id", user_id)


class LogCapture:
    """Capture logs for testing."""

    def __init__(self):
        self.logs = []

    def capture(self, logger, method, event, kwargs):
        self.logs.append({
            "method": method,
            "event": event,
            "kwargs": kwargs,
            "timestamp": datetime.now().isoformat(),
        })

    def clear(self):
        self.logs = []

    def get_events(self, event_name: str = None):
        if event_name:
            return [log for log in self.logs if log["event"] == event_name]
        return self.logs


logger = StructuredLogger()