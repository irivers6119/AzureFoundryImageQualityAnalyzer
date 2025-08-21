# 🚀 OpenCV Image Quality Analyzer API Service Guide

This document explains how to expose the OpenCV Image Quality Analyzer as a REST API service, allowing users to submit images and receive JSON responses with quality analysis results.

## 📋 **Table of Contents**
1. [Quick Start](#quick-start)
2. [Service Architecture](#service-architecture)
3. [API Implementation](#api-implementation)
4. [Docker Configuration](#docker-configuration)
5. [Usage Examples](#usage-examples)
6. [Deployment Options](#deployment-options)
7. [Security Considerations](#security-considerations)
8. [Monitoring & Scaling](#monitoring--scaling)

---

## 🎯 **Quick Start**

### **1. Build the API Service**
```bash
cd /path/to/imagequalityanalyzer/opencv
./docker-build.sh api
```

### **2. Start the API Server**
```bash
docker run -d \
  --name opencv-api-server \
  -p 8000:8000 \
  -v "$(pwd)/../images:/app/images:ro" \
  -v "$(pwd)/../output:/app/output:rw" \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  -e MAX_WORKERS=4 \
  opencv-image-analyzer:latest api
```

### **3. Test the API**
```bash
# Health check
curl http://localhost:8000/health

# Analyze single image
curl -X POST \
  -F "image=@../images/sample.jpg" \
  http://localhost:8000/analyze

# Batch analysis
curl -X POST \
  -F "images=@../images/image1.jpg" \
  -F "images=@../images/image2.jpg" \
  http://localhost:8000/analyze/batch
```

---

## 🏗️ **Service Architecture**

### **Components Overview**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   API Gateway    │    │   File Storage  │
│   (nginx/ALB)   │────│   (Optional)     │────│   (S3/Volume)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Service   │    │   OpenCV Engine  │    │   Results DB    │
│   (FastAPI)     │────│   (Container)    │────│   (Optional)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### **Data Flow**
1. **Client** uploads image(s) via HTTP POST
2. **API Service** validates and processes request
3. **OpenCV Engine** performs quality analysis
4. **Results** returned as JSON response
5. **Optional**: Store results in database/file system

---

## 🔧 **API Implementation**

### **Create FastAPI Service** (`api_service.py`)

First, let's create the FastAPI service that will expose the OpenCV analyzer:

```python
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
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    global analyzer
    try:
        analyzer = OpenCVImageQualityAnalyzer(profile="general")
        logger.info("OpenCV Image Quality Analyzer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
        raise


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
        result = analyzer.analyze_single_image_data(img, filename)
        
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
    if not image.content_type.startswith('image/'):
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
            if not image.content_type.startswith('image/'):
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
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download image: {str(e)}")
    except Exception as e:
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
    import psutil
    import os
    
    return {
        "service": {
            "uptime_seconds": (datetime.now() - startup_time).total_seconds() if 'startup_time' in globals() else 0,
            "opencv_version": cv2.__version__,
            "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
            "api_version": "1.0.0"
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        },
        "analyzer": {
            "current_profile": analyzer.profile if analyzer else None,
            "available_profiles": ["general", "document", "portrait"]
        }
    }


# Track startup time
startup_time = datetime.now()

if __name__ == "__main__":
    import os
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("API_WORKERS", "1"))
    
    # Add the analyze_single_image_data method to the analyzer
    def analyze_single_image_data(self, img, filename):
        """Analyze image data directly without file I/O."""
        file_ext = Path(filename).suffix or '.jpg'
        file_name = Path(filename).stem
        
        # Perform the analysis
        result = {
            'file_name': file_name,
            'file_extension': file_ext,
            'Lighting_and_Exposure': float(self.analyze_brightness(img)),
            'Angle_and_Composition': float(self.analyze_contrast(img)), 
            'Clarity_and_Resolution': float(self.analyze_sharpness(img)),
            'Detail_Visibility': float(self.analyze_noise(img)),
            'Background_and_Distractions': 10.0 - float(self.analyze_noise(img)),  # Inverted noise
            'detailed_metrics': {
                'brightness': float(self.analyze_brightness(img)),
                'contrast': float(self.analyze_contrast(img)),
                'sharpness': float(self.analyze_sharpness(img)),
                'noise': float(self.analyze_noise(img)),
                'exposure': float(self.analyze_exposure(img)),
                'edge_quality': float(self.analyze_edge_quality(img))
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
    
    # Monkey patch the method
    OpenCVImageQualityAnalyzer.analyze_single_image_data = analyze_single_image_data
    
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(
        "api_service:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True
    )
```

---

## 🐳 **Docker Configuration**

### **Update Dockerfile for API Mode**

Add the following to your existing `Dockerfile`:

```dockerfile
# Add FastAPI dependencies to requirements.txt
# fastapi==0.104.1
# uvicorn==0.24.0
# python-multipart==0.0.6
# requests==2.31.0
# psutil==5.9.6

# Copy API service
COPY api_service.py ./

# Expose API port
EXPOSE 8000

# Add API command to entrypoint.sh
```

### **Update entrypoint.sh**

Add this case to your `entrypoint.sh`:

```bash
    "api")
        echo "Starting API service..."
        export API_HOST=${API_HOST:-0.0.0.0}
        export API_PORT=${API_PORT:-8000}
        export API_WORKERS=${API_WORKERS:-1}
        echo "API Configuration:"
        echo "  Host: $API_HOST"
        echo "  Port: $API_PORT"
        echo "  Workers: $API_WORKERS"
        python3 api_service.py
        ;;
```

### **Docker Compose for API Service**

```yaml
version: '3.8'

services:
  opencv-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: opencv-api-server
    ports:
      - "8000:8000"
    volumes:
      - ../images:/app/images:ro
      - ../output:/app/output:rw
      - ./logs:/app/logs:rw
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - API_WORKERS=1
      - ANALYSIS_PROFILE=general
      - MAX_WORKERS=4
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - opencv-net
    command: ["api"]

  # Optional: nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: opencv-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    depends_on:
      - opencv-api
    networks:
      - opencv-net
    profiles:
      - proxy

networks:
  opencv-net:
    driver: bridge
```

---

## 📝 **Usage Examples**

### **1. Single Image Analysis**

```bash
# Using curl
curl -X POST \
  -F "image=@sample.jpg" \
  -F "profile=general" \
  http://localhost:8000/analyze

# Using Python requests
import requests

with open('sample.jpg', 'rb') as f:
    files = {'image': f}
    data = {'profile': 'general'}
    response = requests.post('http://localhost:8000/analyze', files=files, data=data)
    result = response.json()
    print(f"Overall Score: {result['Overall_Score']}")
    print(f"Decision: {result['Decision']}")
```

### **2. Batch Analysis**

```bash
# Multiple images
curl -X POST \
  -F "images=@image1.jpg" \
  -F "images=@image2.jpg" \
  -F "images=@image3.jpg" \
  -F "profile=document" \
  http://localhost:8000/analyze/batch

# Python batch processing
import requests

files = [
    ('images', open('image1.jpg', 'rb')),
    ('images', open('image2.jpg', 'rb')),
    ('images', open('image3.jpg', 'rb'))
]

response = requests.post(
    'http://localhost:8000/analyze/batch',
    files=files,
    data={'profile': 'portrait'}
)

batch_result = response.json()
print(f"Processed: {batch_result['successful_analyses']}/{batch_result['total_images']}")
```

### **3. URL-based Analysis**

```bash
# Analyze image from URL
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/image.jpg", "profile": "general"}' \
  http://localhost:8000/analyze/url
```

### **4. JavaScript/Web Integration**

```javascript
// HTML form submission
async function analyzeImage(formData) {
    const response = await fetch('/analyze', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    return result;
}

// File upload with drag and drop
const dropZone = document.getElementById('dropZone');
dropZone.addEventListener('drop', async (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    
    const formData = new FormData();
    for (let file of files) {
        formData.append('images', file);
    }
    formData.append('profile', 'general');
    
    const response = await fetch('/analyze/batch', {
        method: 'POST',
        body: formData
    });
    
    const results = await response.json();
    displayResults(results);
});
```

---

## 🚀 **Deployment Options**

### **1. Local Development**
```bash
# Development server
python3 api_service.py

# Docker development
docker-compose up opencv-api
```

### **2. Production Deployment**

#### **Docker Swarm**
```yaml
version: '3.8'

services:
  opencv-api:
    image: opencv-image-analyzer:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    ports:
      - "8000:8000"
    networks:
      - opencv-net
    command: ["api"]
```

#### **Kubernetes**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opencv-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: opencv-api
  template:
    metadata:
      labels:
        app: opencv-api
    spec:
      containers:
      - name: opencv-api
        image: opencv-image-analyzer:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_WORKERS
          value: "1"
        - name: MAX_WORKERS
          value: "4"
        resources:
          limits:
            cpu: 2000m
            memory: 2Gi
          requests:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        command: ["./entrypoint.sh", "api"]
---
apiVersion: v1
kind: Service
metadata:
  name: opencv-api-service
spec:
  selector:
    app: opencv-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### **3. Cloud Platforms**

#### **AWS ECS**
```json
{
  "family": "opencv-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "opencv-api",
      "image": "your-registry/opencv-image-analyzer:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "API_HOST", "value": "0.0.0.0"},
        {"name": "API_PORT", "value": "8000"},
        {"name": "API_WORKERS", "value": "1"}
      ],
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      },
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/opencv-api",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### **Azure Container Instances**
```yaml
apiVersion: 2021-03-01
location: westus2
name: opencv-api-group
properties:
  containers:
  - name: opencv-api
    properties:
      image: your-registry/opencv-image-analyzer:latest
      ports:
      - port: 8000
        protocol: TCP
      environmentVariables:
      - name: API_HOST
        value: 0.0.0.0
      - name: API_PORT
        value: 8000
      resources:
        requests:
          cpu: 2.0
          memoryInGb: 2.0
      command: ["./entrypoint.sh", "api"]
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8000
tags:
  environment: production
  service: opencv-api
```

---

## 🔒 **Security Considerations**

### **1. Input Validation**
```python
# File size limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_BATCH_SIZE = 50  # Maximum files per batch
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}

# Image validation
def validate_image(image_data: bytes) -> bool:
    try:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img is not None
    except:
        return False
```

### **2. Rate Limiting**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze_single_image(request: Request, ...):
    # API endpoint code
```

### **3. Authentication**
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/analyze")
async def analyze_single_image(
    token: dict = Depends(verify_token),
    ...
):
    # Protected endpoint
```

### **4. HTTPS/TLS Configuration**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    location / {
        proxy_pass http://opencv-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # File upload size limit
        client_max_body_size 50M;
    }
}
```

---

## 📊 **Monitoring & Scaling**

### **1. Health Checks**
```python
@app.get("/health/deep")
async def deep_health_check():
    """Comprehensive health check."""
    checks = {
        "api": "healthy",
        "opencv": "unknown",
        "memory": "unknown",
        "disk": "unknown"
    }
    
    try:
        # Test OpenCV
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
        checks["opencv"] = "healthy"
    except:
        checks["opencv"] = "unhealthy"
    
    try:
        # Check memory usage
        import psutil
        memory_percent = psutil.virtual_memory().percent
        checks["memory"] = "healthy" if memory_percent < 90 else "warning"
        
        # Check disk space
        disk_percent = psutil.disk_usage('/').percent
        checks["disk"] = "healthy" if disk_percent < 90 else "warning"
    except:
        pass
    
    overall_status = "healthy" if all(
        status == "healthy" for status in checks.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

### **2. Metrics Collection**
```python
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

# Metrics
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
IMAGE_PROCESSING_TIME = Histogram('image_processing_seconds', 'Image processing time')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### **3. Logging Configuration**
```python
import logging
from logging.handlers import RotatingFileHandler
import json

# Structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
            
        return json.dumps(log_entry)

# Configure logging
handler = RotatingFileHandler('/app/logs/api.log', maxBytes=10*1024*1024, backupCount=5)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

### **4. Auto-scaling Configuration**
```yaml
# Kubernetes Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: opencv-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: opencv-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 🎯 **Best Practices**

### **1. Performance Optimization**
- Use async processing for I/O operations
- Implement connection pooling for databases
- Cache frequently accessed data
- Use CDN for static assets
- Optimize image processing with appropriate algorithms

### **2. Error Handling**
- Implement comprehensive error responses
- Log errors with context for debugging
- Provide meaningful error messages to clients
- Use circuit breakers for external dependencies

### **3. Documentation**
- Auto-generate API documentation with FastAPI
- Provide usage examples for all endpoints
- Document error codes and responses
- Include authentication requirements

### **4. Testing**
```python
import pytest
from fastapi.testclient import TestClient
from api_service import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_single_image_analysis():
    with open("test_image.jpg", "rb") as f:
        response = client.post("/analyze", files={"image": f})
    assert response.status_code == 200
    result = response.json()
    assert "Overall_Score" in result
    assert "Decision" in result
```

This comprehensive guide provides everything needed to expose your OpenCV Image Quality Analyzer as a production-ready API service! 🚀
