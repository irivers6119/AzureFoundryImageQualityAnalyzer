#!/bin/bash

# Build and run script for OpenCV Image Quality Analyzer container

set -e

echo "OpenCV Image Quality Analyzer - Docker Build & Run Script"
echo "=========================================================="

# Configuration
IMAGE_NAME="opencv-image-analyzer"
CONTAINER_NAME="opencv-analyzer"
VERSION="1.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
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

# Function to build the Docker image
build_image() {
    log_info "Building Docker image: ${IMAGE_NAME}:${VERSION}"
    
    if docker build -t "${IMAGE_NAME}:${VERSION}" -t "${IMAGE_NAME}:latest" .; then
        log_success "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Function to run the container
run_container() {
    local mode=${1:-interactive}
    
    log_info "Running container in ${mode} mode"
    
    # Stop existing container if running
    if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
        log_warning "Stopping existing container: ${CONTAINER_NAME}"
        docker stop "${CONTAINER_NAME}" >/dev/null 2>&1
    fi
    
    # Remove existing container
    if docker ps -aq -f name="${CONTAINER_NAME}" | grep -q .; then
        log_warning "Removing existing container: ${CONTAINER_NAME}"
        docker rm "${CONTAINER_NAME}" >/dev/null 2>&1
    fi
    
    # Determine volume mounts
    local current_dir=$(pwd)
    local parent_dir=$(dirname "$current_dir")
    local images_volume="${parent_dir}/images:/app/images:ro"
    local output_volume="${parent_dir}/output:/app/output:rw"
    
    # Check if directories exist
    if [ ! -d "${parent_dir}/images" ]; then
        log_warning "Images directory ${parent_dir}/images not found. Creating empty directory."
        mkdir -p "${parent_dir}/images"
    fi
    
    if [ ! -d "${parent_dir}/output" ]; then
        log_warning "Output directory ${parent_dir}/output not found. Creating directory."
        mkdir -p "${parent_dir}/output"
    fi
    
    # Run container based on mode
    case "${mode}" in
        "interactive")
            log_info "Starting interactive session..."
            docker run -it --rm \
                --name "${CONTAINER_NAME}" \
                -v "${images_volume}" \
                -v "${output_volume}" \
                -e ANALYSIS_PROFILE=general \
                "${IMAGE_NAME}:latest" interactive
            ;;
        "batch")
            log_info "Running batch analysis..."
            docker run --rm \
                --name "${CONTAINER_NAME}" \
                -v "${images_volume}" \
                -v "${output_volume}" \
                -e ANALYSIS_PROFILE=general \
                "${IMAGE_NAME}:latest" batch
            ;;
        "daemon")
            log_info "Starting as daemon..."
            docker run -d \
                --name "${CONTAINER_NAME}" \
                -v "${images_volume}" \
                -v "${output_volume}" \
                -e ANALYSIS_PROFILE=general \
                --restart unless-stopped \
                "${IMAGE_NAME}:latest" interactive
            log_success "Container started as daemon: ${CONTAINER_NAME}"
            log_info "Use 'docker exec -it ${CONTAINER_NAME} bash' to access"
            ;;
        "test")
            log_info "Running system tests..."
            docker run --rm \
                --name "${CONTAINER_NAME}-test" \
                "${IMAGE_NAME}:latest" test
            ;;
        *)
            log_error "Unknown mode: ${mode}"
            show_usage
            exit 1
            ;;
    esac
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build                 Build the Docker image"
    echo "  run [mode]           Run the container"
    echo "  compose              Use docker-compose"
    echo "  clean                Clean up containers and images"
    echo "  logs                 Show container logs"
    echo "  shell                Access container shell"
    echo ""
    echo "Run Modes:"
    echo "  interactive          Start interactive analysis session (default)"
    echo "  batch               Run batch analysis and exit"
    echo "  daemon              Run as background daemon"
    echo "  test                Run system tests"
    echo ""
    echo "Examples:"
    echo "  $0 build                    # Build the image"
    echo "  $0 run interactive          # Interactive session"
    echo "  $0 run batch               # Batch analysis"
    echo "  $0 run daemon              # Background daemon"
    echo "  $0 compose                 # Use docker-compose"
    echo "  $0 clean                   # Clean up"
}

# Function to use docker-compose
run_compose() {
    log_info "Using docker-compose..."
    
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml not found"
        exit 1
    fi
    
    log_info "Building and starting services..."
    docker-compose up --build -d
    
    log_success "Services started. Use 'docker-compose logs -f' to view logs"
    log_info "To stop: docker-compose down"
}

# Function to clean up
cleanup() {
    log_info "Cleaning up containers and images..."
    
    # Stop and remove containers
    docker ps -aq -f name="${CONTAINER_NAME}" | xargs -r docker stop >/dev/null 2>&1
    docker ps -aq -f name="${CONTAINER_NAME}" | xargs -r docker rm >/dev/null 2>&1
    
    # Remove images
    docker images -q "${IMAGE_NAME}" | xargs -r docker rmi >/dev/null 2>&1
    
    # Clean up dangling images
    docker image prune -f >/dev/null 2>&1
    
    log_success "Cleanup completed"
}

# Function to show logs
show_logs() {
    if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
        log_info "Showing logs for ${CONTAINER_NAME}..."
        docker logs -f "${CONTAINER_NAME}"
    else
        log_error "Container ${CONTAINER_NAME} is not running"
        exit 1
    fi
}

# Function to access shell
access_shell() {
    if docker ps -q -f name="${CONTAINER_NAME}" | grep -q .; then
        log_info "Accessing shell in ${CONTAINER_NAME}..."
        docker exec -it "${CONTAINER_NAME}" bash
    else
        log_error "Container ${CONTAINER_NAME} is not running"
        log_info "Starting temporary container with shell access..."
        docker run -it --rm \
            --name "${CONTAINER_NAME}-shell" \
            -v "../images:/app/images:ro" \
            -v "../output:/app/output:rw" \
            "${IMAGE_NAME}:latest" bash
    fi
}

# Main script logic
case "${1:-}" in
    "build")
        build_image
        ;;
    "run")
        run_container "${2:-interactive}"
        ;;
    "compose")
        run_compose
        ;;
    "clean")
        cleanup
        ;;
    "logs")
        show_logs
        ;;
    "shell")
        access_shell
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    "")
        log_info "No command specified. Building image and running interactive mode..."
        build_image
        run_container "interactive"
        ;;
    *)
        log_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
