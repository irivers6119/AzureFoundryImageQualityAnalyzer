# Multi-stage Docker build for OpenCV Image Quality Analyzer
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libgfortran5 \
    libgl1 \
    libglib2.0-0 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/images /app/output /app/temp

# Copy application code
COPY *.py ./
COPY README.md ./
COPY entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create a non-root user for security
RUN useradd -m -u 1000 opencv_user && \
    chown -R opencv_user:opencv_user /app
USER opencv_user

# Expose port for potential web interface
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import cv2, numpy; print('OK')" || exit 1

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Default command - run interactive mode
CMD ["interactive"]
