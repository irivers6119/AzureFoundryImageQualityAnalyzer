#!/bin/bash

# Enhanced Docker build script for OpenCV Image Quality Analyzer
# Supports multiple modes: standard, api, test, clean

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="opencv-image-analyzer"
IMAGE_TAG="latest"
API_IMAGE_NAME="opencv-api-server"
CONTAINER_NAME="opencv-analyzer-container"
API_CONTAINER_NAME="opencv-api-container"

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Default mode
MODE="${1:-interactive}"

# Usage information
show_usage() {
    echo -e "${CYAN}OpenCV Image Quality Analyzer - Docker Build Script${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 [MODE] [OPTIONS]"
    echo ""
    echo -e "${YELLOW}Modes:${NC}"
    echo "  interactive  - Build and run interactive analysis session (default)"
    echo "  batch        - Build and run batch analysis"
    echo "  api          - Build and run REST API service"
    echo "  daemon       - Build and run as background daemon"
    echo "  test         - Build and run system tests"
    echo "  build-only   - Build image without running"
    echo "  clean        - Clean up containers and images"
    echo "  help         - Show this usage information"
    echo ""
    echo -e "${YELLOW}API Mode Options:${NC}"
    echo "  --port PORT  - Set API port (default: 8000)"
    echo "  --workers N  - Set number of API workers (default: 1)"
    echo "  --profile P  - Set analysis profile (default: general)"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 interactive              # Interactive session"
    echo "  $0 batch                    # Batch analysis"
    echo "  $0 api --port 8080          # API server on port 8080"
    echo "  $0 daemon                   # Background daemon"
    echo "  $0 test                     # Run tests"
    echo "  $0 clean                    # Clean up"
}

# Parse command line arguments
API_PORT="8000"
API_WORKERS="1"
ANALYSIS_PROFILE="general"

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            API_PORT="$2"
            shift 2
            ;;
        --workers)
            API_WORKERS="$2"
            shift 2
            ;;
        --profile)
            ANALYSIS_PROFILE="$2"
            shift 2
            ;;
        help|--help|-h)
            show_usage
            exit 0
            ;;
        *)
            if [[ -z "${MODE}" || "${MODE}" == "interactive" ]]; then
                MODE="$1"
            fi
            shift
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Check if required directories exist
check_directories() {
    log_step "Checking directory structure..."
    
    if [[ ! -d "$PARENT_DIR/images" ]]; then
        log_warning "Images directory not found at $PARENT_DIR/images"
        log_info "Creating empty images directory..."
        mkdir -p "$PARENT_DIR/images"
    fi
    
    if [[ ! -d "$PARENT_DIR/output" ]]; then
        log_info "Creating output directory..."
        mkdir -p "$PARENT_DIR/output"
    fi
    
    if [[ ! -d "$SCRIPT_DIR/logs" ]]; then
        log_info "Creating logs directory..."
        mkdir -p "$SCRIPT_DIR/logs"
    fi
    
    IMAGE_COUNT=$(find "$PARENT_DIR/images" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.bmp" -o -iname "*.tiff" \) | wc -l)
    log_info "Found $IMAGE_COUNT images in $PARENT_DIR/images"
}

# Build Docker image
build_image() {
    local build_mode="$1"
    local image_name="$2"
    local dockerfile="${3:-Dockerfile}"
    
    log_step "Building Docker image for $build_mode mode..."
    
    # Check if Dockerfile exists
    if [[ ! -f "$SCRIPT_DIR/$dockerfile" ]]; then
        log_error "Dockerfile not found: $SCRIPT_DIR/$dockerfile"
        exit 1
    fi
    
    # Build the image
    log_info "Building image: $image_name:$IMAGE_TAG"
    if docker build -t "$image_name:$IMAGE_TAG" -f "$dockerfile" "$SCRIPT_DIR"; then
        log_success "Image built successfully: $image_name:$IMAGE_TAG"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Clean up existing containers
cleanup_containers() {
    local container_name="$1"
    
    log_step "Cleaning up existing containers..."
    
    if docker ps -a --format "table {{.Names}}" | grep -q "^$container_name$"; then
        log_info "Stopping and removing existing container: $container_name"
        docker stop "$container_name" >/dev/null 2>&1 || true
        docker rm "$container_name" >/dev/null 2>&1 || true
    fi
}

# Run container based on mode
run_container() {
    local mode="$1"
    local container_name="$2"
    local image_name="$3"
    
    log_step "Starting container in $mode mode..."
    
    # Common volume mounts (using absolute paths)
    COMMON_VOLUMES="-v "$PARENT_DIR/images:/app/images:ro" -v "$PARENT_DIR/output:/app/output:rw" -v "$SCRIPT_DIR/logs:/app/logs:rw""
    
    # Common environment variables
    COMMON_ENV="-e ANALYSIS_PROFILE=$ANALYSIS_PROFILE -e MAX_WORKERS=4 -e LOG_LEVEL=INFO -e CONTAINER_MODE=true"
    
    case "$mode" in
        "interactive")
            log_info "Starting interactive session..."
            eval "docker run -it --rm --name "$container_name" $COMMON_VOLUMES $COMMON_ENV "$image_name:$IMAGE_TAG" interactive"
            ;;
        "batch")
            log_info "Running batch analysis..."
            eval "docker run --rm --name "$container_name" $COMMON_VOLUMES $COMMON_ENV "$image_name:$IMAGE_TAG" batch"
            ;;
        "api")
            log_info "Starting API server on port $API_PORT..."
            eval "docker run -d --name "$container_name" -p "$API_PORT:8000" $COMMON_VOLUMES $COMMON_ENV -e API_HOST=0.0.0.0 -e API_PORT=8000 -e API_WORKERS=$API_WORKERS "$image_name:$IMAGE_TAG" api"
            
            # Wait for API to be ready
            log_info "Waiting for API to be ready..."
            for i in {1..30}; do
                if curl -s "http://localhost:$API_PORT/health" >/dev/null 2>&1; then
                    log_success "API server is ready!"
                    log_info "API Documentation: http://localhost:$API_PORT/docs"
                    log_info "Health Check: http://localhost:$API_PORT/health"
                    log_info "API Stats: http://localhost:$API_PORT/stats"
                    break
                fi
                sleep 1
            done
            
            # Show container logs
            log_info "Container logs:"
            docker logs "$container_name"
            ;;
        "daemon")
            log_info "Starting daemon mode..."
            eval "docker run -d --name "$container_name" $COMMON_VOLUMES $COMMON_ENV "$image_name:$IMAGE_TAG" interactive"
            log_success "Daemon started. Use 'docker exec -it $container_name bash' to access."
            ;;
        "test")
            log_info "Running system tests..."
            eval "docker run --rm --name "$container_name" $COMMON_VOLUMES $COMMON_ENV "$image_name:$IMAGE_TAG" test"
            ;;
        *)
            log_error "Unknown run mode: $mode"
            exit 1
            ;;
    esac
}

# API-specific functions
build_api_image() {
    log_step "Building API-enabled image..."
    
    # Create temporary Dockerfile for API
    cat > "$SCRIPT_DIR/Dockerfile.api" << 'EOF'
# API-enabled Docker image for OpenCV Image Quality Analyzer
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for OpenCV
RUN apt-get update && apt-get install -y 
    libglib2.0-0 
    libsm6 
    libxext6 
    libxrender-dev 
    libgomp1 
    libjpeg-dev 
    libpng-dev 
    libtiff-dev 
    libgfortran5 
    libgl1 
    libglib2.0-0 
    libfontconfig1 
    curl 
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy API requirements
COPY api-requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && 
    pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/images /app/output /app/temp /app/logs

# Copy application code
COPY *.py ./
COPY README.md ./
COPY entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create a non-root user for security
RUN useradd -m -u 1000 opencv_user && 
    chown -R opencv_user:opencv_user /app
USER opencv_user

# Expose port for API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health', timeout=5).raise_for_status()" || exit 1

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Default command - run API mode
CMD ["api"]
EOF
    
    build_image "API" "$API_IMAGE_NAME" "Dockerfile.api"
    
    # Clean up temporary Dockerfile
    rm -f "$SCRIPT_DIR/Dockerfile.api"
}

# Clean up function
clean_all() {
    log_step "Cleaning up containers and images..."
    
    # Stop and remove containers
    for container in "$CONTAINER_NAME" "$API_CONTAINER_NAME"; do
        if docker ps -a --format "table {{.Names}}" | grep -q "^$container$"; then
            log_info "Removing container: $container"
            docker stop "$container" >/dev/null 2>&1 || true
            docker rm "$container" >/dev/null 2>&1 || true
        fi
    done
    
    # Remove images
    for image in "$IMAGE_NAME:$IMAGE_TAG" "$API_IMAGE_NAME:$IMAGE_TAG"; do
        if docker images --format "table {{.Repository}}:{{.Tag}}" | grep -q "^$image$"; then
            log_info "Removing image: $image"
            docker rmi "$image" >/dev/null 2>&1 || true
        fi
    done
    
    # Clean up temporary files
    rm -f "$SCRIPT_DIR/Dockerfile.api"
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    log_info "OpenCV Image Quality Analyzer Docker Manager"
    log_info "Mode: $MODE"
    
    case "$MODE" in
        "help"|"--help"|"-h")
            show_usage
            exit 0
            ;;
        "clean")
            clean_all
            exit 0
            ;;
        "build-only")
            check_docker
            check_directories
            build_image "standard" "$IMAGE_NAME"
            log_success "Build completed. Use '$0 interactive' to run."
            exit 0
            ;;
        "api")
            check_docker
            check_directories
            
            # Check if API requirements exist
            if [[ ! -f "$SCRIPT_DIR/api-requirements.txt" ]]; then
                log_error "API requirements file not found: $SCRIPT_DIR/api-requirements.txt"
                log_info "Please ensure api-requirements.txt exists with FastAPI dependencies"
                exit 1
            fi
            
            build_api_image
            cleanup_containers "$API_CONTAINER_NAME"
            run_container "$MODE" "$API_CONTAINER_NAME" "$API_IMAGE_NAME"
            ;;
        *)
            check_docker
            check_directories
            build_image "standard" "$IMAGE_NAME"
            cleanup_containers "$CONTAINER_NAME"
            run_container "$MODE" "$CONTAINER_NAME" "$IMAGE_NAME"
            ;;
    esac
}

# Show help if no arguments provided
if [[ "${MODE}" == "help" ]]; then
    show_usage
    exit 0
fi

# Run main function
main