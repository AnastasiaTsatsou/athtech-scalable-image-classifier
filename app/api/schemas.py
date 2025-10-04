"""
Pydantic schemas for API request/response models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class ModelType(str, Enum):
    """Supported model types"""
    RESNET50 = "resnet50"
    RESNET101 = "resnet101"
    RESNET152 = "resnet152"


class PredictionResponse(BaseModel):
    """Response model for image classification predictions"""
    class_name: str = Field(..., description="Predicted class name")
    probability: float = Field(..., description="Prediction probability", ge=0.0, le=1.0)
    class_id: int = Field(..., description="Class ID")


class ClassificationResponse(BaseModel):
    """Response model for image classification API"""
    predictions: List[PredictionResponse] = Field(..., description="Top predictions")
    model_info: Dict[str, str] = Field(..., description="Model information")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    
    model_config = {"protected_namespaces": ()}


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    status: str = Field(..., description="Service status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    model_info: Optional[Dict[str, str]] = Field(None, description="Model information")
    
    model_config = {"protected_namespaces": ()}


class ErrorResponse(BaseModel):
    """Response model for error cases"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
