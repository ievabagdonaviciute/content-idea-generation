"""Structured logging with secret redaction.

Any log key whose name looks like it holds a secret (token/key/secret/password) has
its value replaced before the record is emitted, so a stray ``logger.info(**locals())``
cannot leak credentials.
"""

from __future__ import annotations

import logging
import re
from collections.abc import MutableMapping
from typing import Any

import structlog

_SECRET_KEY_PATTERN = re.compile(r"(token|secret|api_key|password|authorization)", re.I)
_REDACTED = "***redacted***"


def _redact_processor(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    for key in list(event_dict.keys()):
        if _SECRET_KEY_PATTERN.search(key):
            event_dict[key] = _REDACTED
    return event_dict


def configure_logging(app_env: str) -> None:
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO if app_env != "development" else logging.DEBUG,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact_processor,
            structlog.processors.JSONRenderer()
            if app_env == "production"
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
