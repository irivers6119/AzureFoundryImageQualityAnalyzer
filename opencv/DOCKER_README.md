# Docker Containerization Guide
# OpenCV Image Quality Analyzer

This guide provides comprehensive instructions for containerizing and deploying the OpenCV Image Quality Analyzer using Docker.

## 🐳 Container Overview

The OpenCV Image Quality Analyzer has been fully containerized with the following features:

- **Lightweight container** based on Python 3.11 slim image
- **Multi-mode operation** (interactive, batch, daemon, test)
- **Volume mounting** for images and output directories
- **Health checks** and proper error handling
- **Non-root user** for security
- **Flexible configuration** via environment variables

## 📁 Container Files

```
opencv/
├── Dockerfile              # Main container definition
├── Dockerfile.web          # Optional web interface container
├── docker-compose.yml      # Multi-service orchestration
├── entrypoint.sh           # Container entry point script
├── docker-build.sh        # Build and run automation script
├── .dockerignore          # Files to exclude from build
├── requirements.txt       # Python dependencies
├── web-requirements.txt   # Web interface dependencies
└── DOCKER_README.md       # This documentation
```

## 🚀 Quick Start

### Option 1: Using the Build Script (Recommended)

```bash
# Build and run interactively (one command)
./docker-build.sh

# Or specify the mode explicitly
./docker-build.sh run interactive
```

### Option 2: Using Docker Commands Directly

```bash
# Build the image
docker build -t opencv-image-analyzer .

# Run interactively
docker run -it --rm \
  -v ../images:/app/images:ro \
  -v ../output:/app/output:rw \
  opencv-image-analyzer interactive
```

### Option 3: Using Docker Compose

```bash
# Start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

## 🎯 Container Modes

### 1. Interactive Mode (Default)
Provides a chat-like interface for image analysis:

```bash
./docker-build.sh run interactive
# or
docker run -it --rm \
  -v ../images:/app/images:ro \
  -v ../output:/app/output:rw \
  opencv-image-analyzer interactive
```

**Available commands in interactive mode:**
- `analyze` - Analyze all images
- `analyze <filename>` - Analyze specific image
- `profile <name>` - Change analysis profile
- `save` - Save results
- `report` - Show detailed report
- `summary` - Quick statistics
- `exit` - End session

### 2. Batch Mode
Analyzes all images and exits:

```bash
./docker-build.sh run batch
# or
docker run --rm \
  -v ../images:/app/images:ro \
  -v ../output:/app/output:rw \
  opencv-image-analyzer batch
```

### 3. Daemon Mode
Runs as a background service:

```bash
./docker-build.sh run daemon
# or
docker run -d --name opencv-analyzer \
  -v ../images:/app/images:ro \
  -v ../output:/app/output:rw \
  --restart unless-stopped \
  opencv-image-analyzer interactive
```

### 4. Test Mode
Runs system diagnostics:

```bash
./docker-build.sh run test
# or
docker run --rm opencv-image-analyzer test
```

### 5. Single Image Analysis
Analyze a specific image:

```bash
docker run --rm \
  -v ../images:/app/images:ro \
  -v ../output:/app/output:rw \
  opencv-image-analyzer analyze "image.jpg"
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANALYSIS_PROFILE` | `general` | Analysis profile (general/document/portrait) |
| `MAX_WORKERS` | `auto` | Number of parallel workers |
| `LOG_LEVEL` | `INFO` | Logging level |

### Volume Mounts

| Host Path | Container Path | Mode | Purpose |
|-----------|----------------|------|---------|
| `../images` | `/app/images` | `ro` | Input images directory |
| `../output` | `/app/output` | `rw` | Results output directory |
| `./config` | `/app/config` | `ro` | Configuration files (optional) |

### Custom Configuration Example

```bash
docker run -it --rm \
  -v ../images:/app/images:ro \
  -v ../output:/app/output:rw \
  -e ANALYSIS_PROFILE=document \
  -e MAX_WORKERS=8 \
  -e LOG_LEVEL=DEBUG \
  opencv-image-analyzer interactive
```

## 🛠️ Build Script Usage

The `docker-build.sh` script provides a comprehensive interface:

```bash
# Build the Docker image
./docker-build.sh build

# Run in different modes
./docker-build.sh run interactive  # Interactive session
./docker-build.sh run batch       # Batch analysis
./docker-build.sh run daemon      # Background daemon
./docker-build.sh run test        # System tests

# Docker Compose operations
./docker-build.sh compose         # Start with docker-compose

# Utility operations
./docker-build.sh logs           # Show container logs
./docker-build.sh shell          # Access container shell
./docker-build.sh clean          # Clean up containers/images

# Help
./docker-build.sh help           # Show usage information
```

## 📊 Docker Compose Services

The `docker-compose.yml` defines multiple services:

### Main Analyzer Service
```yaml
services:
  opencv-analyzer:
    build: .
    volumes:
      - ../images:/app/images:ro
      - ../output:/app/output:rw
    environment:
      - ANALYSIS_PROFILE=general
      - MAX_WORKERS=4
```

### Optional Web Interface Service
```yaml
  opencv-analyzer-web:
    build:
      dockerfile: Dockerfile.web
    ports:
      - "8080:8000"
    profiles:
      - web  # Enable with: docker-compose --profile web up
```

## 🔍 Container Management

### View Running Containers
```bash
docker ps -f name=opencv-analyzer
```

### View Container Logs
```bash
docker logs -f opencv-analyzer
```

### Access Container Shell
```bash
docker exec -it opencv-analyzer bash
```

### Stop Container
```bash
docker stop opencv-analyzer
```

### Remove Container
```bash
docker rm opencv-analyzer
```

## 🏥 Health Monitoring

The container includes health checks:

```bash
# Check container health
docker inspect opencv-analyzer --format='{{.State.Health.Status}}'

# View health check logs
docker inspect opencv-analyzer --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
```

Health check tests:
- OpenCV import and functionality
- Basic image processing capabilities
- File system access to mounted volumes

## 📈 Performance Optimization

### Resource Limits
```bash
docker run --rm \
  --memory=2g \
  --cpus=4 \
  -v ../images:/app/images:ro \
  -v ../output:/app/output:rw \
  opencv-image-analyzer batch
```

### Multi-Stage Builds
The Dockerfile uses multi-stage builds to minimize image size:
- Base stage: System dependencies and Python packages
- Final stage: Application code and configuration

### Caching Optimization
- Requirements installed before code copy for better cache utilization
- `.dockerignore` excludes unnecessary files
- Layer ordering optimized for cache efficiency

## 🔐 Security Features

### Non-Root User
Container runs as `opencv_user` (UID 1000) for security:

```dockerfile
RUN useradd -m -u 1000 opencv_user && \
    chown -R opencv_user:opencv_user /app
USER opencv_user
```

### Read-Only Images Mount
Images directory mounted as read-only:

```bash
-v ../images:/app/images:ro
```

### Minimal Attack Surface
- Based on slim Python image
- Only essential system packages installed
- No unnecessary services running

## 🐛 Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   ```bash
   # Fix file permissions
   sudo chown -R $(id -u):$(id -g) ../output
   ```

2. **Images Not Found**
   ```bash
   # Verify image directory exists and has content
   ls -la ../images/
   ```

3. **Container Won't Start**
   ```bash
   # Check Docker daemon
   docker version
   
   # View build logs
   docker build --no-cache -t opencv-image-analyzer .
   ```

4. **Out of Memory Errors**
   ```bash
   # Increase memory limit
   docker run --memory=4g ...
   ```

### Debug Mode

Run container with debug output:

```bash
docker run -it --rm \
  -v ../images:/app/images:ro \
  -v ../output:/app/output:rw \
  -e LOG_LEVEL=DEBUG \
  opencv-image-analyzer test
```

### Container Logs

View detailed logs:

```bash
# Real-time logs
docker logs -f opencv-analyzer

# Last 100 lines
docker logs --tail 100 opencv-analyzer

# Logs since specific time
docker logs --since 2025-08-20T10:00:00 opencv-analyzer
```

## 🚀 Deployment Scenarios

### Development Environment
```bash
# Quick development testing
./docker-build.sh run interactive
```

### CI/CD Pipeline
```bash
# Automated testing
docker run --rm \
  -v $PWD/test-images:/app/images:ro \
  -v $PWD/test-output:/app/output:rw \
  opencv-image-analyzer batch
```

### Production Deployment
```bash
# Production daemon with restart policy
docker run -d \
  --name opencv-analyzer-prod \
  --restart always \
  --memory=4g \
  --cpus=8 \
  -v /data/images:/app/images:ro \
  -v /data/output:/app/output:rw \
  -e ANALYSIS_PROFILE=general \
  -e MAX_WORKERS=8 \
  opencv-image-analyzer interactive
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opencv-analyzer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: opencv-analyzer
  template:
    metadata:
      labels:
        app: opencv-analyzer
    spec:
      containers:
      - name: opencv-analyzer
        image: opencv-image-analyzer:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "2"
          limits:
            memory: "4Gi"
            cpu: "4"
        volumeMounts:
        - name: images-volume
          mountPath: /app/images
          readOnly: true
        - name: output-volume
          mountPath: /app/output
        env:
        - name: ANALYSIS_PROFILE
          value: "general"
        - name: MAX_WORKERS
          value: "4"
      volumes:
      - name: images-volume
        persistentVolumeClaim:
          claimName: images-pvc
      - name: output-volume
        persistentVolumeClaim:
          claimName: output-pvc
```

## 📦 Image Registry

### Tag and Push to Registry
```bash
# Tag for registry
docker tag opencv-image-analyzer:latest your-registry.com/opencv-image-analyzer:1.0

# Push to registry
docker push your-registry.com/opencv-image-analyzer:1.0
```

### Pull and Run from Registry
```bash
# Pull from registry
docker pull your-registry.com/opencv-image-analyzer:1.0

# Run from registry
docker run -it --rm \
  -v ../images:/app/images:ro \
  -v ../output:/app/output:rw \
  your-registry.com/opencv-image-analyzer:1.0 interactive
```

## 🎯 Benefits of Containerization

✅ **Consistency** - Same environment across development, testing, and production
✅ **Portability** - Runs anywhere Docker is available
✅ **Isolation** - No conflicts with host system dependencies
✅ **Scalability** - Easy horizontal scaling with orchestration
✅ **Version Control** - Immutable, versioned deployments
✅ **Resource Management** - Controlled resource allocation
✅ **Easy Deployment** - Single command deployment
✅ **Rollback Capability** - Easy version rollback

The containerized OpenCV Image Quality Analyzer provides a robust, scalable, and maintainable solution for image quality analysis in any environment.
