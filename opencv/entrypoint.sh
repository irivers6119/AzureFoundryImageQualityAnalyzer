#!/bin/bash
set -e

# Docker entrypoint script for OpenCV Image Quality Analyzer
echo "Starting OpenCV Image Quality Analyzer..."

# Check if images directory exists and has content
if [ ! -d "/app/images" ]; then
    echo "Warning: Images directory not mounted. Creating empty directory."
    mkdir -p /app/images
fi

# Check if output directory exists
if [ ! -d "/app/output" ]; then
    echo "Warning: Output directory not mounted. Creating empty directory."
    mkdir -p /app/output
fi

# Count images in the directory
IMAGE_COUNT=$(find /app/images -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.bmp" -o -iname "*.tiff" \) | wc -l)
echo "Found $IMAGE_COUNT images to analyze"

# Set default analysis profile if not provided
export ANALYSIS_PROFILE=${ANALYSIS_PROFILE:-general}
export MAX_WORKERS=${MAX_WORKERS:-$(nproc)}
export CONTAINER_MODE=true

echo "Configuration:"
echo "  Analysis Profile: $ANALYSIS_PROFILE"
echo "  Max Workers: $MAX_WORKERS"
echo "  Images Directory: /app/images"
echo "  Output Directory: /app/output"
echo "  Container Mode: $CONTAINER_MODE"

# Parse command line arguments
case "${1:-interactive}" in
    "batch")
        echo "Running batch analysis..."
        python3 opencv_image_quality_analyzer.py
        ;;
    "interactive")
        echo "Starting interactive session..."
        python3 opencv_analysis_session.py
        ;;
    "analyze")
        echo "Running single analysis..."
        if [ -z "$2" ]; then
            echo "Error: Please specify image name for single analysis"
            echo "Usage: docker run ... analyze <image_name>"
            exit 1
        fi
        python3 -c "
from opencv_analysis_session import OpenCVAnalysisSession
session = OpenCVAnalysisSession(profile='$ANALYSIS_PROFILE')
result = session.analyze_single_image('$2')
import json
print(json.dumps(result, indent=2))
"
        ;;
    "compare")
        echo "Running comparison with AI results..."
        python3 comparison_tool.py
        ;;
    "test")
        echo "Running system tests..."
        python3 -c "
import cv2
import numpy as np
from opencv_image_quality_analyzer import OpenCVImageQualityAnalyzer

print('OpenCV version:', cv2.__version__)
print('NumPy version:', np.__version__)

# Test basic functionality
analyzer = OpenCVImageQualityAnalyzer()
print('Analyzer initialized successfully')

# Create a test image
test_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
print('Test image created')

# Test individual metrics
print('Testing metrics...')
print('  Brightness:', analyzer.analyze_brightness(test_img))
print('  Contrast:', analyzer.analyze_contrast(test_img))
print('  Sharpness:', analyzer.analyze_sharpness(test_img))
print('  Noise:', analyzer.analyze_noise(test_img))
print('  Exposure:', analyzer.analyze_exposure(test_img))
print('  Edge Quality:', analyzer.analyze_edge_quality(test_img))
print('All tests passed!')
"
        ;;
    "api")
        echo "Starting API service..."
        export API_HOST=${API_HOST:-0.0.0.0}
        export API_PORT=${API_PORT:-8000}
        export API_WORKERS=${API_WORKERS:-1}
        echo "API Configuration:"
        echo "  Host: $API_HOST"
        echo "  Port: $API_PORT"
        echo "  Workers: $API_WORKERS"
        echo "  Profile: $ANALYSIS_PROFILE"
        python3 api_service.py
        ;;
    "bash"|"sh")
        echo "Starting shell..."
        exec /bin/bash
        ;;
    *)
        echo "Running custom command: $@"
        exec "$@"
        ;;
esac
