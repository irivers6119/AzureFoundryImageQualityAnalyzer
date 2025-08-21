#!/usr/bin/env python3
"""
FastAPI service for OpenCV Image Quality Analyzer.
Provides REST API endpoints for image quality analysis.
"""

import io
import json
import logging
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
import uvicorn

try:
    from opencv_image_quality_analyzer import OpenCVImageQualityAnalyzer
except ImportError:
    from .opencv_image_quality_analyzer import OpenCVImageQualityAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OpenCV Image Quality Analyzer API",
    description="REST API for analyzing image quality using OpenCV algorithms",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for web applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global analyzer instance
analyzer = None
executor = ThreadPoolExecutor(max_workers=4)

# Pydantic models for API responses
class AnalysisResult(BaseModel):
    file_name: str
    file_extension: str
    file_size_bytes: int
    analysis_timestamp: str
    Lighting_and_Exposure: float = Field(..., ge=0, le=10)
    Angle_and_Composition: float = Field(..., ge=0, le=10)
    Clarity_and_Resolution: float = Field(..., ge=0, le=10)
    Detail_Visibility: float = Field(..., ge=0, le=10)
    Background_and_Distractions: float = Field(..., ge=0, le=10)
    Overall_Score: float = Field(..., ge=0, le=10)
    Decision: str = Field(..., pattern="^(Keep|Retake)$")
    detailed_metrics: Dict[str, float]
    processing_time_seconds: float

class BatchAnalysisResult(BaseModel):
    request_id: str
    total_images: int
    successful_analyses: int
    failed_analyses: int
    batch_timestamp: str
    results: List[AnalysisResult]
    errors: List[Dict[str, str]]

class HealthStatus(BaseModel):
    status: str
    timestamp: str
    opencv_version: str
    api_version: str
    available_profiles: List[str]

class AnalysisRequest(BaseModel):
    profile: Optional[str] = Field(default="general", pattern="^(general|document|portrait)$")
    return_detailed_metrics: Optional[bool] = True
    max_dimension: Optional[int] = Field(default=None, ge=100, le=4096)


@app.on_event("startup")
async def startup_event():
    """Initialize the analyzer on startup."""
    global analyzer, startup_time
    try:
        analyzer = OpenCVImageQualityAnalyzer(profile="general")
        startup_time = datetime.now()
        logger.info("OpenCV Image Quality Analyzer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
        raise


def analyze_single_image_data(analyzer_instance, img, filename):
    """Analyze image data directly without file I/O."""
    file_ext = Path(filename).suffix or '.jpg'
    file_name = Path(filename).stem
    
    # Perform the analysis
    result = {
        'file_name': file_name,
        'file_extension': file_ext,
        'Lighting_and_Exposure': float(analyzer_instance.analyze_brightness(img)),
        'Angle_and_Composition': float(analyzer_instance.analyze_contrast(img)), 
        'Clarity_and_Resolution': float(analyzer_instance.analyze_sharpness(img)),
        'Detail_Visibility': float(analyzer_instance.analyze_noise(img)),
        'Background_and_Distractions': 10.0 - float(analyzer_instance.analyze_noise(img)),  # Inverted noise
        'detailed_metrics': {
            'brightness': float(analyzer_instance.analyze_brightness(img)),
            'contrast': float(analyzer_instance.analyze_contrast(img)),
            'sharpness': float(analyzer_instance.analyze_sharpness(img)),
            'noise': float(analyzer_instance.analyze_noise(img)),
            'exposure': float(analyzer_instance.analyze_exposure(img)),
            'edge_quality': float(analyzer_instance.analyze_edge_quality(img))
        }
    }
    
    # Calculate overall score
    scores = [
        result['Lighting_and_Exposure'],
        result['Angle_and_Composition'], 
        result['Clarity_and_Resolution'],
        result['Detail_Visibility'],
        result['Background_and_Distractions']
    ]
    result['Overall_Score'] = float(sum(scores) / len(scores))
    result['Decision'] = "Keep" if result['Overall_Score'] > 7.0 else "Retake"
    
    return result


def process_image(image_data: bytes, filename: str, params: AnalysisRequest) -> AnalysisResult:
    """Process a single image and return analysis results."""
    start_time = datetime.now()
    
    try:
        # Convert bytes to OpenCV image
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Could not decode image")
        
        # Resize if max_dimension is specified
        if params.max_dimension:
            h, w = img.shape[:2]
            if max(h, w) > params.max_dimension:
                scale = params.max_dimension / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Update analyzer profile if needed
        global analyzer
        if analyzer.profile != params.profile:
            analyzer = OpenCVImageQualityAnalyzer(profile=params.profile)
        
        # Perform analysis
        result = analyze_single_image_data(analyzer, img, filename)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create API response
        return AnalysisResult(
            file_name=result['file_name'],
            file_extension=result['file_extension'],
            file_size_bytes=len(image_data),
            analysis_timestamp=datetime.now().isoformat(),
            Lighting_and_Exposure=result['Lighting_and_Exposure'],
            Angle_and_Composition=result['Angle_and_Composition'],
            Clarity_and_Resolution=result['Clarity_and_Resolution'],
            Detail_Visibility=result['Detail_Visibility'],
            Background_and_Distractions=result['Background_and_Distractions'],
            Overall_Score=result['Overall_Score'],
            Decision=result['Decision'],
            detailed_metrics=result.get('detailed_metrics', {}),
            processing_time_seconds=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error processing image {filename}: {e}")
        raise HTTPException(status_code=400, detail=f"Image processing failed: {str(e)}")


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        opencv_version=cv2.__version__,
        api_version="1.0.0",
        available_profiles=["general", "document", "portrait"]
    )


@app.post("/analyze", response_model=AnalysisResult)
async def analyze_single_image(
    image: UploadFile = File(...),
    profile: str = Query(default="general", regex="^(general|document|portrait)$"),
    return_detailed_metrics: bool = Query(default=True),
    max_dimension: Optional[int] = Query(default=None, ge=100, le=4096)
):
    """
    Analyze a single image for quality metrics.
    
    - **image**: Image file to analyze (JPG, PNG, BMP, TIFF)
    - **profile**: Analysis profile (general, document, portrait)
    - **return_detailed_metrics**: Include detailed metric breakdown
    - **max_dimension**: Maximum image dimension for processing (optional)
    """
    
    # Validate file type
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read image data
    image_data = await image.read()
    
    if len(image_data) == 0:
        raise HTTPException(status_code=400, detail="Empty image file")
    
    # Create analysis parameters
    params = AnalysisRequest(
        profile=profile,
        return_detailed_metrics=return_detailed_metrics,
        max_dimension=max_dimension
    )
    
    # Process image in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor, 
        process_image, 
        image_data, 
        image.filename or "unknown.jpg", 
        params
    )
    
    return result


@app.post("/analyze/batch", response_model=BatchAnalysisResult)
async def analyze_batch_images(
    images: List[UploadFile] = File(...),
    profile: str = Query(default="general", regex="^(general|document|portrait)$"),
    return_detailed_metrics: bool = Query(default=True),
    max_dimension: Optional[int] = Query(default=None, ge=100, le=4096)
):
    """
    Analyze multiple images in batch.
    
    - **images**: List of image files to analyze
    - **profile**: Analysis profile for all images
    - **return_detailed_metrics**: Include detailed metrics for all images
    - **max_dimension**: Maximum image dimension for processing (optional)
    """
    
    if len(images) == 0:
        raise HTTPException(status_code=400, detail="No images provided")
    
    if len(images) > 50:  # Limit batch size
        raise HTTPException(status_code=400, detail="Batch size limited to 50 images")
    
    request_id = str(uuid.uuid4())
    results = []
    errors = []
    
    # Create analysis parameters
    params = AnalysisRequest(
        profile=profile,
        return_detailed_metrics=return_detailed_metrics,
        max_dimension=max_dimension
    )
    
    # Process each image
    for image in images:
        try:
            # Validate file type
            if not image.content_type or not image.content_type.startswith('image/'):
                errors.append({
                    "filename": image.filename or "unknown",
                    "error": "Invalid file type - must be an image"
                })
                continue
            
            # Read image data
            image_data = await image.read()
            
            if len(image_data) == 0:
                errors.append({
                    "filename": image.filename or "unknown",
                    "error": "Empty image file"
                })
                continue
            
            # Process image in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                process_image,
                image_data,
                image.filename or "unknown.jpg",
                params
            )
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing {image.filename}: {e}")
            errors.append({
                "filename": image.filename or "unknown",
                "error": str(e)
            })
    
    return BatchAnalysisResult(
        request_id=request_id,
        total_images=len(images),
        successful_analyses=len(results),
        failed_analyses=len(errors),
        batch_timestamp=datetime.now().isoformat(),
        results=results,
        errors=errors
    )


@app.post("/analyze/url")
async def analyze_image_from_url(
    image_url: str,
    profile: str = Query(default="general", regex="^(general|document|portrait)$"),
    return_detailed_metrics: bool = Query(default=True),
    max_dimension: Optional[int] = Query(default=None, ge=100, le=4096)
):
    """
    Analyze an image from a URL.
    
    - **image_url**: URL of the image to analyze
    - **profile**: Analysis profile (general, document, portrait)
    - **return_detailed_metrics**: Include detailed metric breakdown
    - **max_dimension**: Maximum image dimension for processing (optional)
    """
    
    try:
        import requests
        
        # Download image
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Validate content type
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="URL does not point to an image")
        
        # Extract filename from URL
        filename = Path(image_url).name or "url_image.jpg"
        
        # Create analysis parameters
        params = AnalysisRequest(
            profile=profile,
            return_detailed_metrics=return_detailed_metrics,
            max_dimension=max_dimension
        )
        
        # Process image
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            process_image,
            response.content,
            filename,
            params
        )
        
        return result
        
    except Exception as e:
        if "requests" in str(e):
            raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/profiles")
async def get_available_profiles():
    """Get available analysis profiles and their descriptions."""
    return {
        "profiles": [
            {
                "name": "general",
                "description": "Balanced analysis suitable for most image types",
                "metrics": ["brightness", "contrast", "sharpness", "noise", "exposure", "edge_quality"]
            },
            {
                "name": "document",
                "description": "Optimized for document and text images",
                "emphasis": ["clarity", "contrast", "text_readability"]
            },
            {
                "name": "portrait",
                "description": "Optimized for portrait and people photography",
                "emphasis": ["lighting", "skin_tones", "focus_quality"]
            }
        ]
    }


@app.get("/stats")
async def get_service_stats():
    """Get service statistics and runtime information."""
    try:
        import psutil
        import os
        
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        system_stats = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_usage_percent": disk.percent,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
    except ImportError:
        system_stats = {"error": "psutil not available"}
    
    return {
        "service": {
            "uptime_seconds": (datetime.now() - startup_time).total_seconds() if 'startup_time' in globals() else 0,
            "opencv_version": cv2.__version__,
            "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
            "api_version": "1.0.0"
        },
        "system": system_stats,
        "analyzer": {
            "current_profile": analyzer.profile if analyzer else None,
            "available_profiles": ["general", "document", "portrait"]
        }
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "OpenCV Image Quality Analyzer API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "analyze_single": "/analyze",
            "analyze_batch": "/analyze/batch",
            "analyze_url": "/analyze/url",
            "profiles": "/profiles",
            "stats": "/stats",
            "docs": "/docs"
        },
        "usage": {
            "single_image": "POST /analyze with multipart/form-data",
            "batch_images": "POST /analyze/batch with multiple files",
            "url_analysis": "POST /analyze/url with JSON body"
        }
    }


# Track startup time
startup_time = datetime.now()

if __name__ == "__main__":
    import os
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "1"))
    
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(
        "api_service:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True
    )
