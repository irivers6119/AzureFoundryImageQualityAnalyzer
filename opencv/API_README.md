# 🚀 OpenCV Image Quality Analyzer API

A containerized REST API service for analyzing image quality using OpenCV algorithms. This service provides HTTP endpoints for both single image and batch analysis, returning detailed quality metrics in JSON format.

## 📋 **Quick Start**

### **1. Start the API Service**
```bash
# Using Docker build script (recommended)
./docker-build.sh api

# Or using Docker Compose
docker-compose -f docker-compose-api.yml up opencv-api

# Or manual Docker run
docker run -d \
  --name opencv-api-server \
  -p 8000:8000 \
  -v "$(pwd)/../images:/app/images:ro" \
  -v "$(pwd)/../output:/app/output:rw" \
  opencv-image-analyzer:latest api
```

### **2. Test the API**
```bash
# Health check
curl http://localhost:8000/health

# Upload and analyze an image
curl -X POST \
  -F "image=@sample.jpg" \
  -F "profile=general" \
  http://localhost:8000/analyze
```

### **3. View Documentation**
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🔧 **API Endpoints**

### **Health & Information**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health status |
| `/stats` | GET | Service statistics and metrics |
| `/profiles` | GET | Available analysis profiles |
| `/` | GET | API information and usage |

### **Image Analysis**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Analyze a single image |
| `/analyze/batch` | POST | Analyze multiple images |
| `/analyze/url` | POST | Analyze image from URL |

---

## 📊 **Usage Examples**

### **Single Image Analysis**

```bash
# Basic analysis
curl -X POST \
  -F "image=@photo.jpg" \
  http://localhost:8000/analyze

# With specific profile
curl -X POST \
  -F "image=@document.png" \
  -F "profile=document" \
  http://localhost:8000/analyze

# With size limit
curl -X POST \
  -F "image=@large_photo.jpg" \
  -F "profile=portrait" \
  -F "max_dimension=1024" \
  http://localhost:8000/analyze
```

**Response:**
```json
{
  "file_name": "photo",
  "file_extension": ".jpg",
  "file_size_bytes": 245760,
  "analysis_timestamp": "2025-08-20T22:30:00.123456",
  "Lighting_and_Exposure": 8.5,
  "Angle_and_Composition": 7.2,
  "Clarity_and_Resolution": 9.1,
  "Detail_Visibility": 8.8,
  "Background_and_Distractions": 7.5,
  "Overall_Score": 8.2,
  "Decision": "Keep",
  "detailed_metrics": {
    "brightness": 8.5,
    "contrast": 7.2,
    "sharpness": 9.1,
    "noise": 8.8,
    "exposure": 8.3,
    "edge_quality": 8.9
  },
  "processing_time_seconds": 0.245
}
```

### **Batch Analysis**

```bash
# Multiple images
curl -X POST \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.jpg" \
  -F "images=@photo3.jpg" \
  -F "profile=general" \
  http://localhost:8000/analyze/batch
```

**Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_images": 3,
  "successful_analyses": 3,
  "failed_analyses": 0,
  "batch_timestamp": "2025-08-20T22:30:00.123456",
  "results": [
    {
      "file_name": "photo1",
      "Overall_Score": 8.2,
      "Decision": "Keep",
      ...
    },
    {
      "file_name": "photo2", 
      "Overall_Score": 6.5,
      "Decision": "Retake",
      ...
    }
  ],
  "errors": []
}
```

### **URL Analysis**

```bash
# Analyze image from URL
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "profile": "general",
    "max_dimension": 1024
  }' \
  http://localhost:8000/analyze/url
```

### **Python Client**

```python
import requests

# Single image
with open('photo.jpg', 'rb') as f:
    files = {'image': f}
    data = {'profile': 'general'}
    response = requests.post('http://localhost:8000/analyze', files=files, data=data)
    result = response.json()
    print(f"Score: {result['Overall_Score']}, Decision: {result['Decision']}")

# Batch processing
files = [
    ('images', open('photo1.jpg', 'rb')),
    ('images', open('photo2.jpg', 'rb'))
]
response = requests.post('http://localhost:8000/analyze/batch', files=files)
batch_result = response.json()
print(f"Processed: {batch_result['successful_analyses']}/{batch_result['total_images']}")
```

### **JavaScript/Web**

```javascript
// HTML form upload
const formData = new FormData();
formData.append('image', fileInput.files[0]);
formData.append('profile', 'general');

fetch('/analyze', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(result => {
    console.log('Score:', result.Overall_Score);
    console.log('Decision:', result.Decision);
});

// Batch upload with drag and drop
const files = Array.from(fileList);
const formData = new FormData();
files.forEach(file => formData.append('images', file));
formData.append('profile', 'document');

fetch('/analyze/batch', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(results => {
    console.log(`Processed: ${results.successful_analyses}/${results.total_images}`);
    results.results.forEach(result => {
        console.log(`${result.file_name}: ${result.Overall_Score} (${result.Decision})`);
    });
});
```

---

## ⚙️ **Configuration**

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `API_WORKERS` | `1` | Number of worker processes |
| `ANALYSIS_PROFILE` | `general` | Default analysis profile |
| `MAX_WORKERS` | `4` | Max concurrent image processing |
| `LOG_LEVEL` | `INFO` | Logging level |

### **Analysis Profiles**

| Profile | Description | Best For |
|---------|-------------|----------|
| `general` | Balanced analysis for most images | Photos, general images |
| `document` | Optimized for text and documents | Scanned docs, text images |
| `portrait` | Optimized for people photography | Portraits, people photos |

### **API Limits**

| Limit | Value | Description |
|-------|-------|-------------|
| Max file size | 10MB | Per image file |
| Batch size | 50 images | Max images per batch request |
| Max dimension | 4096px | Optional image resize limit |
| Request timeout | 30s | Per request timeout |

---

## 🐳 **Deployment**

### **Docker Compose (Recommended)**

```yaml
# docker-compose-api.yml
version: '3.8'

services:
  opencv-api:
    build: .
    container_name: opencv-api-server
    ports:
      - "8000:8000"
    volumes:
      - ../images:/app/images:ro
      - ../output:/app/output:rw
    environment:
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - ANALYSIS_PROFILE=general
    restart: unless-stopped
    command: ["api"]
```

```bash
# Start API service
docker-compose -f docker-compose-api.yml up -d

# View logs
docker-compose -f docker-compose-api.yml logs -f

# Stop service
docker-compose -f docker-compose-api.yml down
```

### **Production Deployment**

#### **With nginx Reverse Proxy**
```bash
# Start with nginx proxy
docker-compose -f docker-compose-api.yml --profile proxy up -d
```

#### **With Monitoring**
```bash
# Start with Prometheus and Grafana
docker-compose -f docker-compose-api.yml --profile monitoring up -d
# Access Grafana: http://localhost:3000 (admin/admin)
# Access Prometheus: http://localhost:9090
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
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
        command: ["./entrypoint.sh", "api"]
```

---

## 🔒 **Security**

### **Input Validation**
- File type validation (image formats only)
- File size limits (10MB max)
- Batch size limits (50 images max)
- Image dimension limits (configurable)

### **Rate Limiting** (Optional)
```python
# Add to api_service.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/analyze")
@limiter.limit("10/minute")  # 10 requests per minute
async def analyze_single_image(request: Request, ...):
    # endpoint code
```

### **Authentication** (Optional)
```python
# Add JWT authentication
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    # Token verification logic
    pass

@app.post("/analyze")
async def analyze_single_image(token: dict = Depends(verify_token), ...):
    # Protected endpoint
```

### **HTTPS/TLS**
Configure nginx or load balancer for SSL/TLS termination:
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    location / {
        proxy_pass http://opencv-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;
    }
}
```

---

## 📊 **Monitoring**

### **Health Checks**
```bash
# Basic health
curl http://localhost:8000/health

# Detailed health with system metrics
curl http://localhost:8000/stats
```

### **Metrics Collection**
The API provides Prometheus-compatible metrics:
```bash
# Metrics endpoint
curl http://localhost:8000/metrics
```

### **Logging**
Structured JSON logs are written to:
- Container logs: `docker logs opencv-api-server`
- File logs: `./logs/api.log` (if volume mounted)

---

## 🧪 **Testing**

### **Automated Testing**
```bash
# Run test client
python3 api_client_demo.py test

# Health check only
curl -f http://localhost:8000/health || echo "API not ready"
```

### **Load Testing**
```bash
# Install Apache Bench
# Ubuntu/Debian: apt-get install apache2-utils
# macOS: brew install apache2

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 http://localhost:8000/health

# Test image upload (requires image file)
ab -n 10 -c 2 -p image.jpg -T multipart/form-data http://localhost:8000/analyze
```

### **Integration Testing**
```python
import pytest
from fastapi.testclient import TestClient
from api_service import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_image_analysis():
    with open("test_image.jpg", "rb") as f:
        response = client.post("/analyze", files={"image": f})
    assert response.status_code == 200
    result = response.json()
    assert "Overall_Score" in result
    assert "Decision" in result
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

| Issue | Solution |
|-------|----------|
| `Connection refused` | Check if container is running: `docker ps` |
| `Import errors` | Ensure all dependencies installed: `pip install -r api-requirements.txt` |
| `Image processing failed` | Check image format and size limits |
| `Container won't start` | Check logs: `docker logs opencv-api-server` |

### **Debug Commands**
```bash
# Check container status
docker ps -a

# View container logs
docker logs opencv-api-server

# Access container shell
docker exec -it opencv-api-server bash

# Test OpenCV inside container
docker exec opencv-api-server python3 -c "import cv2; print(cv2.__version__)"

# Check API dependencies
docker exec opencv-api-server pip list | grep -E "(fastapi|uvicorn|opencv)"
```

### **Performance Optimization**
```bash
# Multiple workers for production
docker run -e API_WORKERS=4 opencv-image-analyzer:latest api

# Limit memory usage
docker run --memory=2g opencv-image-analyzer:latest api

# CPU limits
docker run --cpus=2.0 opencv-image-analyzer:latest api
```

---

## 📚 **API Documentation**

Once the service is running, comprehensive interactive documentation is available:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide:
- Complete endpoint documentation
- Request/response schemas
- Interactive testing interface
- Example requests and responses
- Error code documentation

---

## 🎯 **Best Practices**

### **Production Deployment**
1. Use reverse proxy (nginx) for SSL/TLS
2. Implement rate limiting and authentication
3. Set up monitoring and alerting
4. Use container orchestration (Docker Swarm/Kubernetes)
5. Configure log aggregation

### **Performance**
1. Use multiple API workers for high load
2. Implement caching for repeated analyses
3. Resize large images before processing
4. Use async processing for batch operations
5. Monitor resource usage and scale accordingly

### **Security**
1. Validate all input files
2. Implement file size and type restrictions
3. Use HTTPS in production
4. Add authentication for sensitive deployments
5. Regular security updates

The OpenCV Image Quality Analyzer API provides a robust, scalable solution for automated image quality analysis in production environments! 🚀
