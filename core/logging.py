"""
Structured logging configuration for the TBCV system.

Goals:
- Provide JSON-structured logs by default (good for log shipping / analysis).
- Avoid hard dependency on `python-json-logger`; gracefully fallback if it's missing.
- Offer simple helpers (get_logger, LoggerMixin, PerformanceLogger, @log_performance).

How to use:
1) Call setup_logging() once in your program's entry point.
2) Get a logger with get_logger("module_or_component_name")
3) Optionally inherit LoggerMixin to auto-wire a structlog logger per class.
4) Use PerformanceLogger or @log_performance to time critical operations.
"""

from __future__ import annotations

import sys
import json
import logging
from logging import Handler
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime

import logging
try:
    import structlog
except ImportError:
    structlog = None


# Import settings from our config module
from .config import get_settings


# =========================
# JSON formatter (fallback)
# =========================
class _FallbackJsonFormatter(logging.Formatter):
    """
    Minimal JSON formatter used when `python-json-logger` is not available.

    Behavior:
    - Emits a single JSON object per log line.
    - Includes timestamp, level, name, message, plus any extra attributes bound
      to the record (e.g., via logger = logger.bind(...) in structlog or logger.xyz=...).

    This is intentionally simple and dependency-free.
    """

    # Keys that logging.LogRecord uses internally; we don't want to duplicate them
    _RESERVED = {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process"
    }

    def format(self, record: logging.LogRecord) -> str:
        # Base payload
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        # Merge extras (anything the LogRecord has that isn't reserved)
        for k, v in record.__dict__.items():
            if k not in self._RESERVED and not k.startswith("_"):
                try:
                    json.dumps(v)  # ensure serializable
                    payload[k] = v
                except TypeError:
                    payload[k] = str(v)

        # Ensure consistent one-line JSON output
        return json.dumps(payload, ensure_ascii=False)


def _build_formatter(fmt_style: str) -> logging.Formatter:
    """
    Create a logging.Formatter instance based on requested style.

    If `fmt_style == 'json'`, we prefer python-json-logger if installed,
    otherwise we fallback to _FallbackJsonFormatter. For any other style,
    we output a standard human-readable format.
    """
    fmt_style = (fmt_style or "json").lower()

    if fmt_style == "json":
        # Try to use python-json-logger if available
        try:
            from pythonjsonlogger import jsonlogger  # type: ignore
            # A lean JSON layout; structlog already adds rich context.
            return jsonlogger.JsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
        except Exception:
            # Fallback if module missing or import fails
            return _FallbackJsonFormatter()

    # Plain text formatter (useful during local dev)
    return logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# =================================
# Structlog processor customization
# =================================
class TBCVProcessor:
    """
    Custom structlog processor for TBCV-specific formatting.

    It runs late in the processor chain to enrich the event dict with:
    - ISO-8601 UTC timestamp (if missing),
    - logger name (as `logger`),
    - system metadata (version, environment, hostname placeholder).
    """

    def __call__(self, logger, name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure a timestamp exists
        event_dict.setdefault("timestamp", datetime.utcnow().isoformat(timespec="milliseconds") + "Z")
        # Attach logger name
        event_dict["logger"] = name

        # Attach basic metadata from settings
        settings = get_settings()
        event_dict["metadata"] = {
            "version": settings.system.version,
            "environment": settings.system.environment,
            # NOTE: consider socket.gethostname() if you want the real host
            "hostname": "localhost",
        }
        return event_dict


# ============================
# Context helpers (std logging)
# ============================
class ContextFilter(logging.Filter):
    """
    Standard logging filter which appends a static context dict to every record.

    Use case:
      handler.addFilter(ContextFilter({"service": "tbcv-api"}))
    """

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}

    def filter(self, record: logging.LogRecord) -> bool:
        for k, v in self.context.items():
            setattr(record, k, v)
        return True


# ======================
# Top-level configuration
# ======================
def setup_logging() -> None:
    """
    Configure both structlog and stdlib logging.

    Steps:
    1) Ensure log directory exists.
    2) Configure structlog processors (JSON renderer at the end).
    3) Configure stdlib logging root logger, file + console handlers, formatters.
    4) Tweak chatter from common libraries (uvicorn/fastapi/sqlalchemy).
    """
    settings = get_settings()

    # 1) Ensure log directory exists (if file logging is configured)
    log_file_path = Path(settings.log_file_path) if getattr(settings, "log_file_path", None) else None
    if log_file_path:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # 2) Structlog configuration (only if structlog is available)
    if structlog:
        structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,             # honor stdlib log levels
            structlog.stdlib.add_logger_name,             # add `logger`
            structlog.stdlib.add_log_level,               # add `level`
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),     # stack as string if present
            structlog.processors.format_exc_info,         # exc_info to string
            TBCVProcessor(),                              # our custom enrichment
            structlog.processors.JSONRenderer(),          # final JSON serialization
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        # If structlog is not available, just use stdlib logging
        pass

    # 3) Stdlib logging root config: no handlers here; we attach explicit handlers below
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), handlers=[])

    # Choose formatter based on settings.log_format ("json" by default)
    formatter = _build_formatter(getattr(settings, "log_format", "json"))

    # File handler with rotation (if file path configured)
    if log_file_path:
        file_handler: Handler = RotatingFileHandler(
            filename=str(log_file_path),
            maxBytes=int(settings.log_max_file_size_mb) * 1024 * 1024,
            backupCount=int(settings.log_backup_count),
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    # 4) Quiet noisy libraries to sensible defaults
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


# ======================
# Convenience interfaces
# ======================
class LoggerWrapper:
    """Fallback logger wrapper for compatibility with structlog-style calls."""
    def __init__(self, logger):
        self.logger = logger
        self._context = {}

    def bind(self, **kwargs):
        self._context.update(kwargs)
        return self

    def _merge_msg(self, msg):
        if self._context:
            ctx = " ".join(f"{k}={v}" for k, v in self._context.items())
            return f"{msg} {ctx}"
        return msg

    def info(self, msg, **kwargs):
        self.logger.info(self._merge_msg(msg))

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(self._merge_msg(msg), *args, **kwargs)

    def warning(self, msg, **kwargs):
        self.logger.warning(self._merge_msg(msg))

    def error(self, msg, **kwargs):
        self.logger.error(self._merge_msg(msg))

    def critical(self, msg, **kwargs):
        self.logger.critical(self._merge_msg(msg))

    def exception(self, msg, *args, **kwargs):
        self.logger.exception(self._merge_msg(msg), *args, **kwargs)

# file: tbcv/core/logging.py
def get_logger(name: str = "tbcv", context: Optional[Dict[str, Any]] = None):
    """
    Return a structlog logger if available, otherwise a fallback stdlib wrapper.
    Optionally bind an initial context dict (safe for backward compatibility).
    """
    if structlog:
        logger = structlog.get_logger(name)
        if context:
            logger = logger.bind(**context)
        return logger
    else:
        wrapper = LoggerWrapper(logging.getLogger(name))
        if context:
            wrapper.bind(**context)
        return wrapper




class LoggerMixin:
    """
    Mixin that gives any class a `logger` property and simple context management.

    Usage:
        class MyAgent(LoggerMixin):
            def __init__(self):
                super().__init__()
                self.set_log_context(agent="orchestrator")

            def run(self):
                self.logger.info("Running")  # carries bound context
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # Allow cooperative multiple inheritance
        self._logger: Optional[structlog.BoundLogger] = None
        self._log_context: Dict[str, Any] = {}

    @property
    def logger(self) -> structlog.BoundLogger:
        """Return a structlog logger bound to this class' name and current context."""
        if self._logger is None:
            class_name = self.__class__.__name__
            self._logger = get_logger(f"tbcv.{class_name.lower()}", self._log_context)
        return self._logger

    def set_log_context(self, **kwargs) -> None:
        """Merge key/value context and rebind the logger so future logs include it."""
        self._log_context.update(kwargs)
        # Recreate logger with new context
        self._logger = None

    def clear_log_context(self) -> None:
        """Remove all bound context and rebind the logger."""
        self._log_context.clear()
        self._logger = None


class PerformanceLogger:
    """
    Context manager that logs start/completion and wall-clock duration in ms.

    Usage:
        with PerformanceLogger(get_logger("tbcv.workflow"), "validate_content") as perf:
            # ... do work ...
            perf.add_context(files=3, issues=0)

    If an exception occurs, it logs an error with duration and exception metadata.
    """

    def __init__(self, logger: structlog.BoundLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time: Optional[datetime] = None
        self.context: Dict[str, Any] = {}

    def __enter__(self) -> "PerformanceLogger":
        self.start_time = datetime.utcnow()
        self.logger.info(
            f"Starting {self.operation}",
            operation=self.operation,
            started_at=self.start_time.isoformat(timespec="milliseconds"),
        )
        return self

    def __exit__(self, exc_type, exc_val, _exc_tb) -> None:
        end_time = datetime.utcnow()
        duration_ms = (end_time - (self.start_time or end_time)).total_seconds() * 1000.0

        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation}",
                operation=self.operation,
                duration_ms=round(duration_ms, 2),
                completed_at=end_time.isoformat(timespec="milliseconds"),
                **self.context,
            )
        else:
            self.logger.error(
                f"Failed {self.operation}",
                operation=self.operation,
                duration_ms=round(duration_ms, 2),
                error_type=getattr(exc_type, "__name__", str(exc_type)),
                error_message=str(exc_val),
                **self.context,
            )

    def add_context(self, **kwargs) -> None:
        """Attach additional structured fields to the eventual completion/error log."""
        self.context.update(kwargs)


def log_performance(operation: str) -> Callable:
    """
    Decorator that logs the duration of a function call using PerformanceLogger.

    Example:
        @log_performance("detect_plugins")
        def detect(...):
            ...

    It tries to reuse `self.logger` when decorating methods; otherwise
    it creates a module-level logger based on the function's module name.
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # If used on a method, prefer the class' logger
            if args and hasattr(args[0], "logger"):
                logger = args[0].logger  # type: ignore[attr-defined]
            else:
                logger = get_logger(func.__module__)
            with PerformanceLogger(logger, operation):
                return func(*args, **kwargs)

        # Preserve original metadata for debuggability
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__qualname__ = getattr(func, "__qualname__", func.__name__)
        return wrapper

    return decorator


# Create a module-level logger for quick logging in this module
logger = get_logger(__name__)


if __name__ == "__main__":
    # Self-test: exercise the logging pipeline with/without python-json-logger present.
    setup_logging()

    test_logger = get_logger("tbcv.test", {"component": "logging_selftest"})
    test_logger.info("Test message", test_field="test_value")
    test_logger.warning("Test warning", warning_code="W001")
    test_logger.error("Test error", error_code="E001", details={"key": "value"})

    @log_performance("test_operation")
    def test_function():
        import time
        time.sleep(0.1)
        return "success"

    result = test_function()
    print(f"Function result: {result}")
