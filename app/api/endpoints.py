"""
FastAPI endpoints for image classification service
"""

import time
import logging
import os
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from PIL import Image
import io

from app.api.schemas import (
    ClassificationResponse,
    HealthResponse,
    PredictionResponse,
)
from app.middleware.cache import image_cache_key, get_cached_result, set_cached_result

try:
    from app.models.image_classifier import ImageClassifier
except ImportError:
    from app.models.mock_classifier import (  # type: ignore
        MockImageClassifier as ImageClassifier,
    )

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Global classifier instances
classifier = None


def get_classifier() -> ImageClassifier:
    """Get or initialize the PyTorch classifier instance"""
    global classifier
    if classifier is None:
        model_name = os.getenv("MODEL_NAME", "resnet50")
        logger.info(f"Loading {model_name} model...")
        classifier = ImageClassifier(model_name=model_name)
        logger.info(f"✅ {model_name} loaded successfully")
    return classifier


# Pre-load the model at startup
logger.info("Pre-loading ResNet50 model...")
try:
    get_classifier()
    logger.info("✅ Model pre-loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to pre-load model: {e}")


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
        
        # Add size validation early (10MB limit)
        if len(image_data) > 10_000_000:
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Check cache first
        cache_key = image_cache_key(image_data, top_k)
        cached_result = get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Cache hit for image classification")
            # For cache hits, set processing time to 0
            cached_result['processing_time_ms'] = 0.0
            return ClassificationResponse(**cached_result)
        
        image = Image.open(io.BytesIO(image_data))

        # Validate image
        if image.size[0] == 0 or image.size[1] == 0:
            raise HTTPException(
                status_code=400, detail="Invalid image dimensions"
            )
        
        # Resize large images before processing (optimize for speed)
        if image.size[0] > 1024 or image.size[1] > 1024:
            image.thumbnail((1024, 1024), Image.Resampling.BILINEAR)

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

        response = ClassificationResponse(
            predictions=prediction_responses,
            model_info=clf.get_model_info(),
            processing_time_ms=processing_time,
        )
        
        # Cache the result
        set_cached_result(cache_key, response.dict())
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Classification failed: {str(e)}"
        )


@router.post("/classify-batch")
async def classify_batch(
    files: List[UploadFile] = File(..., description="Multiple image files to classify"),
    top_k: int = Form(5, description="Number of top predictions to return", ge=1, le=10),
):
    """
    Classify multiple images in batch (more efficient for multiple images)
    
    Args:
        files: List of image files
        top_k: Number of top predictions to return
        
    Returns:
        List of classification results
    """
    start_time = time.time()
    
    try:
        if len(files) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Maximum 10 images per batch")
        
        # Get classifier
        clf = get_classifier()
        
        results = []
        
        # Process images in batch
        for i, file in enumerate(files):
            try:
                # Validate file type
                if not file.content_type or not file.content_type.startswith("image/"):
                    results.append({
                        "file_index": i,
                        "filename": file.filename,
                        "error": "File must be an image"
                    })
                    continue
                
                # Read and process image
                image_data = await file.read()
                
                # Size validation
                if len(image_data) > 10_000_000:
                    results.append({
                        "file_index": i,
                        "filename": file.filename,
                        "error": "Image too large (max 10MB)"
                    })
                    continue
                
                image = Image.open(io.BytesIO(image_data))
                
                # Validate image
                if image.size[0] == 0 or image.size[1] == 0:
                    results.append({
                        "file_index": i,
                        "filename": file.filename,
                        "error": "Invalid image dimensions"
                    })
                    continue
                
                # Resize large images
                if image.size[0] > 1024 or image.size[1] > 1024:
                    image.thumbnail((1024, 1024), Image.Resampling.BILINEAR)
                
                # Make prediction
                predictions = clf.predict(image, top_k=top_k)
                
                # Format response
                prediction_responses = [
                    PredictionResponse(
                        class_name=str(pred["class_name"]),
                        probability=float(pred["probability"]),
                        class_id=int(pred["class_id"]),
                    )
                    for pred in predictions
                ]
                
                results.append({
                    "file_index": i,
                    "filename": file.filename,
                    "predictions": prediction_responses,
                    "model_info": clf.get_model_info(),
                })
                
            except Exception as e:
                results.append({
                    "file_index": i,
                    "filename": file.filename,
                    "error": str(e)
                })
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "results": results,
            "total_files": len(files),
            "successful_files": len([r for r in results if "error" not in r]),
            "processing_time_ms": processing_time,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch classification failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Batch classification failed: {str(e)}"
        )


@router.get("/model/info")
async def get_model_info():
    """
    Get information about the currently loaded model
    """
    try:
        clf = get_classifier()
        return clf.get_model_info()
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get model info: {str(e)}"
        )
