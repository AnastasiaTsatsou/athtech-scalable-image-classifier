"""
FastAPI endpoints for image classification service
"""

import time
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from PIL import Image
import io

from app.api.schemas import (
    ClassificationResponse,
    HealthResponse,
    PredictionResponse,
)

try:
    from app.models.image_classifier import ImageClassifier
except ImportError:
    from app.models.mock_classifier import (  # type: ignore
        MockImageClassifier as ImageClassifier,
    )

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Global model instance
classifier = None


def get_classifier() -> ImageClassifier:
    """Get or initialize the classifier instance"""
    global classifier
    if classifier is None:
        classifier = ImageClassifier()
    return classifier


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    try:
        clf = get_classifier()
        model_info = clf.get_model_info()

        return HealthResponse(
            status="healthy", model_loaded=True, model_info=model_info
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy", model_loaded=False, model_info=None
        )


@router.post("/classify", response_model=ClassificationResponse)
async def classify_image(
    file: UploadFile = File(..., description="Image file to classify"),
    top_k: int = Form(
        5,
        description="Number of top predictions to return",
        ge=1,
        le=10,
    ),
):
    """
    Classify an uploaded image

    Args:
        file: Image file (JPEG, PNG, etc.)
        top_k: Number of top predictions to return (1-10)

    Returns:
        Classification results with predictions and model info
    """
    start_time = time.time()

    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail="File must be an image"
            )

        # Read and process image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))

        # Validate image
        if image.size[0] == 0 or image.size[1] == 0:
            raise HTTPException(
                status_code=400, detail="Invalid image dimensions"
            )

        # Get classifier and make prediction
        clf = get_classifier()
        predictions = clf.predict(image, top_k=top_k)

        # Calculate processing time
        # Convert to milliseconds
        processing_time = (time.time() - start_time) * 1000

        # Format response
        prediction_responses = [
            PredictionResponse(
                class_name=str(pred["class_name"]),
                probability=float(pred["probability"]),
                class_id=int(pred["class_id"]),
            )
            for pred in predictions
        ]

        return ClassificationResponse(
            predictions=prediction_responses,
            model_info=clf.get_model_info(),
            processing_time_ms=processing_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Classification failed: {str(e)}"
        )


@router.get("/model/info")
async def get_model_info():
    """
    Get information about the loaded model
    """
    try:
        clf = get_classifier()
        return clf.get_model_info()
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get model info: {str(e)}"
        )
