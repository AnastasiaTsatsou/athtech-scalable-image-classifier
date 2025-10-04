"""
FastAPI middleware for automatic metrics collection
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.monitoring.metrics import metrics_collector

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically collect HTTP request metrics"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Extract metrics
        method = request.method
        endpoint = self._get_endpoint_name(request)
        status_code = response.status_code

        # Record metrics
        metrics_collector.record_request(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration=duration,
        )

        logger.debug(
            f"Recorded metrics: {method} {endpoint} {status_code} "
            f"{duration:.3f}s"
        )

        return response

    def _get_endpoint_name(self, request: Request) -> str:
        """Extract endpoint name from request path"""
        path = request.url.path

        # Normalize path for metrics
        if path.startswith("/api/v1/"):
            # API endpoints
            if "/classify" in path:
                return "classify"
            elif "/health" in path:
                return "health"
            elif "/model/info" in path:
                return "model_info"
            else:
                return "api_other"
        elif path == "/":
            return "root"
        elif path == "/docs":
            return "docs"
        elif path == "/redoc":
            return "redoc"
        elif path == "/metrics":
            return "metrics"
        else:
            return "unknown"
