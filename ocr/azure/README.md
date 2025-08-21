# Azure AI Vision Odometer OCR Analyzer

A comprehensive OCR solution for extracting odometer readings from vehicle dashboard photos using Azure AI Vision Image Analysis 4.0 API.

## Overview

This project provides automated odometer reading extraction using Azure's Computer Vision Multi-Service API. It processes images from the `odometer_photos` directory and returns structured JSON responses with detected odometer values.

## Features

- **Azure AI Vision 4.0 Integration** - Latest Computer Vision API with advanced OCR capabilities
- **Multi-Service Key Support** - Uses Azure Computer Vision Multi-Service endpoint and key
- **Batch Processing** - Processes multiple images concurrently for efficiency
- **Smart Value Extraction** - Advanced pattern matching for 1-6 digit odometer readings
- **Confidence Scoring** - Provides confidence scores for extracted values
- **Error Handling** - Comprehensive error handling and retry logic
- **JSON Output** - Structured responses with filename, extension, and metadata
- **Async Processing** - Asynchronous processing for better performance

## Installation

### 1. Install Dependencies

```bash
cd ocr/azure
python setup.py
```

Or manually install:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the environment template and update with your Azure credentials:

```bash
cp .env.example .env
```

Edit `.env` file with your Azure Computer Vision credentials:

```env
AZURE_COMPUTER_VISION_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
AZURE_COMPUTER_VISION_KEY=your-32-character-key-here
```

## Usage

### Full Azure Implementation

```bash
python azure_vision_ocr_analyzer.py
```

This will:
- Process all images in `../odometer_photos/`
- Extract odometer values using Azure AI Vision 4.0 API
- Save results to JSON file in `../output/`
- Display detailed analysis summary

### Demo Mode (for testing without Azure credentials)

```bash
python demo_ocr_analyzer.py
```

This provides simulated OCR responses for testing the extraction logic.

## Sample JSON Response

### Single Image Analysis

```json
{
  "filename": "speedometer-image.jpg",
  "file_extension": "jpg",
  "odometer_value": 125847,
  "confidence_score": 0.85,
  "processing_time": 2.34,
  "timestamp": "2025-08-20T10:30:00Z",
  "metadata": {
    "ocr_text": "ODOMETER 125847 MILES TOTAL DISTANCE",
    "api_version": "4.0",
    "visual_features": ["READ"],
    "language": "en",
    "image_size_bytes": 245760,
    "status": "success"
  }
}
```

### Batch Analysis Summary

```json
{
  "analysis_summary": {
    "total_images": 10,
    "successful_extractions": 8,
    "success_rate": 0.8,
    "average_confidence": 0.82,
    "average_processing_time": 2.15,
    "timestamp": "2025-08-20T10:30:00Z"
  },
  "results": [
    {
      "filename": "AdobeStock_304389205_Preview.jpeg",
      "file_extension": "jpeg",
      "odometer_value": 125847,
      "confidence_score": 0.85
    },
    {
      "filename": "speedometer-scoring-high-speed.jpg",
      "file_extension": "jpg",
      "odometer_value": 67823,
      "confidence_score": 0.78
    }
  ]
}
```

## Odometer Value Detection

The system uses sophisticated pattern matching to detect odometer values:

### Supported Patterns

1. **Basic Numbers**: 1-6 digit sequences (e.g., `125847`)
2. **Formatted Numbers**: Numbers with separators (e.g., `125,847` or `125.847`)
3. **Unit Indicators**: Numbers followed by units (e.g., `125847 miles`, `67823 km`)
4. **Keyword Context**: Numbers near odometer keywords (e.g., `ODOMETER: 125847`)
5. **Total Indicators**: Numbers with cumulative context (e.g., `TOTAL 125847`)

### Confidence Scoring

Confidence scores (0.0 to 1.0) are calculated based on:

- **Keyword Proximity**: Higher confidence when odometer-related keywords are nearby
- **Number Length**: Optimal confidence for 3-6 digit numbers (typical odometer range)
- **Context Analysis**: Boost for numbers in appropriate contexts
- **Value Validation**: Ensures numbers are within reasonable odometer ranges (1-999,999)

## File Structure

```
ocr/azure/
├── azure_vision_ocr_analyzer.py  # Main Azure implementation
├── demo_ocr_analyzer.py           # Demo/testing version
├── setup.py                       # Installation script
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
├── .env                          # Your Azure credentials (create this)
└── README.md                     # This file

../odometer_photos/               # Input images directory
../output/                        # Analysis results directory
```

## Azure AI Vision Configuration

### Required Azure Services

1. **Computer Vision Resource** (Multi-Service or Computer Vision specific)
2. **Image Analysis 4.0 API** access
3. **Read API** capability for OCR text extraction

### API Features Used

- **Visual Features**: `READ` for OCR text extraction
- **Language**: English (`en`) for optimal text recognition
- **Image Analysis**: Advanced image understanding capabilities

## Performance Optimizations

- **Async Processing**: Concurrent image processing for batch operations
- **Batch Size Control**: Configurable batch sizes to optimize API usage
- **Image Validation**: Pre-processing validation to avoid unnecessary API calls
- **Error Handling**: Robust error handling with detailed logging
- **Memory Management**: Efficient image handling for large files

## Error Handling

The system handles various error scenarios:

- **Invalid Images**: File format validation and size checks
- **API Errors**: Azure service errors with detailed error messages
- **Network Issues**: Connection timeouts and retry logic
- **Authentication**: Clear messages for credential issues
- **Rate Limiting**: Appropriate handling of API rate limits

## Configuration Options

### Environment Variables

```env
# Required
AZURE_COMPUTER_VISION_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_COMPUTER_VISION_KEY=your-key-here

# Optional
AZURE_REGION=eastus
MAX_IMAGE_SIZE_MB=4
PROCESSING_TIMEOUT_SECONDS=30
BATCH_SIZE=5
OUTPUT_DIRECTORY=../output
ENABLE_DETAILED_LOGGING=true
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify Azure Computer Vision endpoint and key
   - Check that the resource is active and has quota

2. **No Images Found**
   - Ensure `../odometer_photos/` directory exists
   - Verify image files have supported extensions

3. **Import Errors**
   - Run `python setup.py` to install dependencies
   - Ensure Azure AI Vision SDK is installed

4. **No Odometer Values Detected**
   - Check OCR text output in results for debugging
   - Verify images contain clear, readable odometer displays

### Performance Tips

- Use images with clear, well-lit odometer displays
- Ensure text is not too small or blurry
- Crop images to focus on the odometer area for better accuracy
- Use appropriate image formats (JPEG, PNG recommended)

## Azure Costs

### API Usage Costs

- **Read API**: Charged per 1,000 API calls
- **Image Analysis**: Charged per image processed
- **Data Transfer**: Minimal costs for image upload

### Cost Optimization

- Process images in batches
- Use appropriate image sizes (balance quality vs. cost)
- Implement caching for repeated analyses
- Monitor usage through Azure portal

## Support

For issues related to:

- **Azure AI Vision**: Check Azure documentation and service health
- **OCR Accuracy**: Review image quality and preprocessing options
- **API Integration**: Verify credentials and endpoint configuration
- **Performance**: Check network connectivity and batch sizes

## Future Enhancements

- Custom model training for specific odometer types
- Support for multiple languages
- Real-time processing capabilities
- Integration with other Azure Cognitive Services
- Advanced image preprocessing for better accuracy
