"""
Main FastAPI application for Scalable Image Classifier
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.api.endpoints import router
from app.monitoring.middleware import MetricsMiddleware
from app.monitoring.metrics import metrics_collector
from app.logging.config import setup_logging, get_logger
from app.logging.middleware import LoggingMiddleware

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Configure structured logging
log_level = os.getenv("LOG_LEVEL", "INFO")
log_format = os.getenv("LOG_FORMAT", "json")
setup_logging(log_level=log_level, log_format=log_format)

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Scalable Image Classifier",
    description=(
        "A scalable image classification service using pretrained models"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware (first)
app.add_middleware(LoggingMiddleware)

# Add metrics middleware
app.add_middleware(MetricsMiddleware)

# Include API routes
app.include_router(router, prefix="/api/v1")


# Add root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Scalable Image Classifier API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/v1/health",
            "classify": "/api/v1/classify",
            "model_info": "/api/v1/model/info",
            "docs": "/docs",
            "metrics": "/metrics",
        },
    }


# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    """
    return metrics_collector.get_metrics_response()


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
