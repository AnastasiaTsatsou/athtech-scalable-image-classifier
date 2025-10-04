"""
Prometheus metrics collection for the image classifier service
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import Response
import time
import logging

logger = logging.getLogger(__name__)

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# Image classification metrics
CLASSIFICATION_COUNT = Counter(
    "image_classifications_total",
    "Total image classifications performed",
    ["model_name", "status"],
)

CLASSIFICATION_DURATION = Histogram(
    "image_classification_duration_seconds",
    "Image classification duration in seconds",
    ["model_name"],
)

CLASSIFICATION_CONFIDENCE = Histogram(
    "image_classification_confidence",
    "Confidence score of image classifications",
    ["model_name"],
)

# Model metrics
MODEL_LOAD_TIME = Gauge(
    "model_load_time_seconds", "Time taken to load the model"
)

MODEL_INFO = Info("model_info", "Information about the loaded model")

# System metrics
ACTIVE_CONNECTIONS = Gauge(
    "active_connections", "Number of active connections"
)

MEMORY_USAGE = Gauge("memory_usage_bytes", "Memory usage in bytes")

# Custom metrics for our service
PREDICTION_TOP_K = Histogram(
    "prediction_top_k",
    "Distribution of top_k values requested",
    buckets=[1, 3, 5, 10, 20, 50, 100],
)

IMAGE_SIZE = Histogram(
    "image_size_bytes",
    "Size of uploaded images in bytes",
    buckets=[
        1024,
        10240,
        102400,
        1048576,
        10485760,
        104857600,
    ],  # 1KB to 100MB
)


class MetricsCollector:
    """Metrics collector for the image classifier service"""

    def __init__(self):
        self.start_time = time.time()

    def record_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """Record HTTP request metrics"""
        REQUEST_COUNT.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()

        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(
            duration
        )

    def record_classification(
        self,
        model_name: str,
        duration: float,
        confidence: float,
        status: str = "success",
    ):
        """Record image classification metrics"""
        CLASSIFICATION_COUNT.labels(model_name=model_name, status=status).inc()

        CLASSIFICATION_DURATION.labels(model_name=model_name).observe(duration)

        CLASSIFICATION_CONFIDENCE.labels(model_name=model_name).observe(
            confidence
        )

    def record_model_info(
        self, model_name: str, device: str, num_classes: int, framework: str
    ):
        """Record model information"""
        MODEL_INFO.info(
            {
                "model_name": model_name,
                "device": device,
                "num_classes": str(num_classes),
                "framework": framework,
            }
        )

    def record_model_load_time(self, load_time: float):
        """Record model loading time"""
        MODEL_LOAD_TIME.set(load_time)

    def record_prediction_params(self, top_k: int, image_size: int):
        """Record prediction parameters"""
        PREDICTION_TOP_K.observe(top_k)
        IMAGE_SIZE.observe(image_size)

    def get_metrics_response(self) -> Response:
        """Get Prometheus metrics response"""
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)


# Global metrics collector instance
metrics_collector = MetricsCollector()
