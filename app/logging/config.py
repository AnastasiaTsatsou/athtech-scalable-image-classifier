"""
Structured logging configuration for the image classifier service
"""

import logging
import logging.config
import structlog
import json
import sys
import os
from typing import Any, Dict
from datetime import datetime, timezone
import traceback


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            exc_type, exc_value, exc_tb = record.exc_info
            log_entry["exception"] = {
                "type": exc_type.__name__ if exc_type else "Unknown",
                "message": str(exc_value) if exc_value else "Unknown error",
                "traceback": traceback.format_exception(
                    exc_type, exc_value, exc_tb
                ),
            }

        return json.dumps(log_entry, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """Filter to add context information to log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        # Add request context if available
        if hasattr(record, "request_id"):
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}  # type: ignore
            record.extra_fields["request_id"] = (  # type: ignore
                record.request_id
            )

        if hasattr(record, "user_id"):
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}  # type: ignore
            record.extra_fields["user_id"] = record.user_id  # type: ignore

        if hasattr(record, "model_name"):
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}  # type: ignore
            record.extra_fields["model_name"] = (  # type: ignore
                record.model_name
            )

        if hasattr(record, "endpoint"):
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}  # type: ignore
            record.extra_fields["endpoint"] = record.endpoint  # type: ignore

        if hasattr(record, "response_time"):
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}  # type: ignore
            record.extra_fields["response_time"] = (  # type: ignore
                record.response_time
            )

        if hasattr(record, "status_code"):
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}  # type: ignore
            record.extra_fields["status_code"] = (  # type: ignore
                record.status_code
            )

        if hasattr(record, "image_size"):
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}  # type: ignore
            record.extra_fields["image_size"] = (  # type: ignore
                record.image_size
            )

        if hasattr(record, "confidence"):
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}  # type: ignore
            record.extra_fields["confidence"] = (  # type: ignore
                record.confidence
            )

        if hasattr(record, "top_k"):
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}  # type: ignore
            record.extra_fields["top_k"] = record.top_k  # type: ignore

        return True


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Set up structured logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json, text)
    """
    # Check if running in container (disable file logging)
    is_container = os.path.exists("/.dockerenv") or os.environ.get("CONTAINER") == "true"

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()  # type: ignore
            if log_format == "json"
            else structlog.dev.ConsoleRenderer(),  # type: ignore
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": log_format,
            "filters": ["context"],
            "stream": sys.stdout,
        },
    }
    
    # Add file handler only if not in container
    if not is_container:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": log_format,
            "filters": ["context"],
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }
    
    # Determine which handlers to use
    handler_list = ["console"]
    if not is_container:
        handler_list.append("file")
    
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JSONFormatter,
            },
            "text": {
                "format": (
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "filters": {
            "context": {
                "()": ContextFilter,
            }
        },
        "handlers": handlers,
        "loggers": {
            "app": {
                "level": log_level,
                "handlers": handler_list,
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": handler_list,
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": handler_list,
                "propagate": False,
            },
        },
        "root": {"level": log_level, "handlers": handler_list},
    }

    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with structured logging

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    response_time: float,
    request_id: str | None = None,
) -> None:
    """
    Log HTTP request information

    Args:
        logger: Logger instance
        method: HTTP method
        endpoint: Request endpoint
        status_code: HTTP status code
        response_time: Response time in seconds
        request_id: Optional request ID
    """
    extra = {
        "endpoint": endpoint,
        "status_code": status_code,
        "response_time": response_time,
    }
    if request_id:
        extra["request_id"] = request_id

    logger.info(
        f"{method} {endpoint} - {status_code} - {response_time:.3f}s",
        extra=extra,
    )


def log_classification(
    logger: logging.Logger,
    model_name: str,
    confidence: float,
    processing_time: float,
    top_k: int,
    image_size: int,
    status: str = "success",
) -> None:
    """
    Log image classification information

    Args:
        logger: Logger instance
        model_name: Name of the model used
        confidence: Classification confidence score
        processing_time: Processing time in seconds
        top_k: Number of top predictions
        image_size: Size of the input image in bytes
        status: Classification status (success/error)
    """
    extra = {
        "model_name": model_name,
        "confidence": confidence,
        "processing_time": processing_time,
        "top_k": top_k,
        "image_size": image_size,
        "status": status,
    }

    logger.info(
        f"Image classification - {model_name} - {confidence:.3f} - "
        f"{processing_time:.3f}s",
        extra=extra,
    )


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Dict[str, Any] | None = None,
) -> None:
    """
    Log error information with context

    Args:
        logger: Logger instance
        error: Exception object
        context: Additional context information
    """
    extra = context or {}
    extra["error_type"] = type(error).__name__
    extra["error_message"] = str(error)

    logger.error(f"Error occurred: {error}", extra=extra, exc_info=True)
