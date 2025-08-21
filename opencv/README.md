# OpenCV Image Quality Analyzer

A computer vision-based replacement for AI-driven image quality analysis using OpenCV algorithms.

## Overview

This implementation replaces the Azure OpenAI GPT-4o image quality analyzer with a local, cost-effective OpenCV-based solution that provides:

- **Local processing** - No external API calls or data transmission
- **Cost efficiency** - No token usage or API costs
- **Consistent results** - Deterministic algorithmic analysis
- **Fast performance** - Optimized computer vision algorithms
- **Privacy protection** - All processing happens locally

## Features

### Quality Metrics Analyzed

1. **Brightness** - Overall image lightness using pixel intensity analysis
2. **Contrast** - Dynamic range assessment using standard deviation
3. **Sharpness** - Blur detection using Laplacian variance and Sobel gradients
4. **Noise** - Visual noise assessment using bilateral filtering
5. **Exposure** - Over/under exposure detection using histogram analysis
6. **Edge Quality** - Detail preservation using Canny edge detection

### Analysis Profiles

- **General** - Balanced weighting for typical photos
- **Document** - Optimized for text and document clarity
- **Portrait** - Tuned for portrait photography with emphasis on noise reduction

### Output Compatibility

Maintains the same JSON output format as the original AI system:

```json
{
    "file_name": "image",
    "file_extension": "jpg",
    "Lighting_and_Exposure": 7.5,
    "Angle_and_Composition": 8.0,
    "Clarity_and_Resolution": 6.8,
    "Detail_Visibility": 7.2,
    "Background_and_Distractions": 8.5,
    "Overall_Score": 7.6,
    "Decision": "Keep"
}
```

## Installation

1. **Install dependencies:**
   ```bash
   cd opencv
   python setup.py
   ```

2. **Or manually install packages:**
   ```bash
   pip install opencv-python>=4.8.0 numpy>=1.21.0 matplotlib>=3.5.0 scikit-image>=0.19.0 pillow>=9.0.0
   ```

## Usage

### Interactive Session (Recommended)

```bash
python opencv_analysis_session.py
```

**Available commands:**
- `analyze` - Analyze all images in the images folder
- `analyze <filename>` - Analyze a specific image
- `profile <name>` - Change analysis profile (general/document/portrait)
- `save` - Save current results to output folder
- `report` - Show detailed analysis report
- `summary` - Show quick summary statistics
- `exit` - End session

### Direct Analysis

```bash
python opencv_image_quality_analyzer.py
```

### API Service Usage

For containerized API service deployments, use HTTP requests to analyze images:

#### Single Image Analysis

**Base64 Image Data:**
```json
{
    "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "profile": "general"
}
```

**S3 Object Reference:**
```json
{
    "s3_key": "uploads/image-001.jpg",
    "profile": "document"
}
```

**Image URL:**
```json
{
    "image_url": "https://example.com/image.jpg",
    "profile": "portrait"
}
```

#### Batch Image Analysis

```json
{
    "images": [
        {
            "s3_key": "uploads/batch-001.jpg",
            "profile": "general"
        },
        {
            "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
            "profile": "document"
        },
        {
            "image_url": "https://example.com/photo.jpg",
            "profile": "portrait"
        }
    ],
    "batch_id": "batch-2025-001"
}
```

#### Response Format

**Single Analysis Response:**
```json
{
    "analysis_id": "uuid-12345",
    "timestamp": "2025-08-20T10:30:00Z",
    "profile": "general",
    "filename": "image.jpg",
    "file_extension": "jpg",
    "Lighting_and_Exposure": 7.5,
    "Angle_and_Composition": 8.0,
    "Clarity_and_Resolution": 6.8,
    "Detail_Visibility": 7.2,
    "Background_and_Distractions": 8.5,
    "Overall_Score": 7.6,
    "Decision": "Keep",
    "processing_time": 2.34,
    "image_dimensions": {
        "width": 1920,
        "height": 1080
    }
}
```

**Batch Analysis Response:**
```json
{
    "batch_id": "batch-2025-001",
    "timestamp": "2025-08-20T10:30:00Z",
    "total_images": 3,
    "completed": 3,
    "failed": 0,
    "processing_time": 6.82,
    "analyses": [
        {
            "analysis_id": "uuid-12345",
            "filename": "batch-001.jpg",
            "Overall_Score": 7.6,
            "Decision": "Keep"
        },
        {
            "analysis_id": "uuid-12346",
            "filename": "image.jpg",
            "Overall_Score": 8.2,
            "Decision": "Keep"
        },
        {
            "analysis_id": "uuid-12347",
            "filename": "photo.jpg",
            "Overall_Score": 5.1,
            "Decision": "Retake"
        }
    ]
}
```

### Comparison with AI Results

```bash
python comparison_tool.py
```

This tool compares OpenCV results with existing AI analysis results to validate accuracy.

## File Structure

```
opencv/
├── opencv_image_quality_analyzer.py  # Core analysis engine
├── opencv_analysis_session.py        # Interactive session wrapper
├── comparison_tool.py                 # AI vs OpenCV comparison utility
├── setup.py                          # Installation and setup script
├── requirements.txt                   # Python dependencies
└── README.md                         # This file

../images/                            # Input images (shared)
../output/                            # Analysis results (shared)
```

## Algorithm Details

### Brightness Analysis
- Calculates mean pixel intensity
- Optimal brightness around 127.5 (middle of 0-255 range)
- Score decreases with deviation from optimal

### Contrast Analysis
- Uses standard deviation of pixel intensities
- Higher standard deviation indicates better contrast
- Normalized to 0-10 scale

### Sharpness Detection
- **Laplacian Variance**: Higher variance indicates sharper edges
- **Sobel Gradients**: Measures edge magnitude in X and Y directions
- Combined metric provides robust sharpness assessment

### Noise Analysis
- Compares original image with bilateral filtered version
- Bilateral filter removes noise while preserving edges
- Difference indicates noise level

### Exposure Analysis
- Analyzes histogram distribution
- Detects clipping in shadows (underexposure) and highlights (overexposure)
- Penalizes excessive clipping

### Edge Quality
- Uses Canny edge detection to find edges
- Measures edge density as indicator of detail preservation
- Higher edge density suggests better detail retention

## Performance Optimizations

- **Parallel Processing**: Multi-threaded batch analysis
- **Image Resizing**: Automatic resizing of large images for speed
- **Memory Management**: Efficient processing to handle large batches
- **Caching**: Results caching to avoid recomputation

## Validation and Calibration

The system includes tools to validate against the original AI results:

1. **Statistical Comparison**: Mean, median, standard deviation analysis
2. **Decision Agreement**: Percentage of Keep/Retake agreement
3. **Score Correlation**: Analysis of score differences
4. **Individual File Analysis**: Detailed per-image comparison

## Advantages Over AI Approach

✅ **Zero API Costs** - No token usage or external service fees
✅ **Faster Processing** - Local computation is typically faster
✅ **Privacy & Security** - No data leaves your environment
✅ **Reliability** - No dependency on external service availability
✅ **Consistency** - Same input always produces same output
✅ **Offline Capability** - Works without internet connection
✅ **Full Control** - Complete control over analysis parameters

## Customization

### Adjusting Weights

Edit the weight profiles in `opencv_image_quality_analyzer.py`:

```python
self.weight_profiles = {
    'general': {
        'brightness': 0.15,
        'contrast': 0.20,
        'sharpness': 0.25,
        'noise': 0.15,
        'exposure': 0.15,
        'edge_quality': 0.10
    }
}
```

### Tuning Thresholds

Modify quality thresholds for different standards:

```python
self.quality_thresholds = {
    'excellent': 8.5,
    'good': 7.0,
    'acceptable': 6.0,
    'poor': 4.0
}
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Run `python setup.py` to install dependencies
2. **No Images Found**: Ensure images are in the `../images` folder
3. **Permission Errors**: Check write permissions for `../output` folder
4. **Memory Issues**: Large images are automatically resized for processing

### Performance Tuning

- Adjust `max_image_size` in the analyzer for speed vs quality trade-off
- Modify `max_workers` parameter for parallel processing
- Use appropriate analysis profile for your image type

## Support and Development

This implementation provides a robust, cost-effective alternative to AI-based image quality analysis while maintaining compatibility with existing workflows and output formats.

For issues or enhancements, refer to the detailed code comments and docstrings within each module.
