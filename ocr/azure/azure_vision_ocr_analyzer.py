"""
Azure AI Vision Odometer OCR Analyzer

This module provides OCR analysis of odometer photos using Azure AI Vision Image Analysis 4.0 API.
It processes images from the odometer_photos directory and extracts numerical values from odometers.

Features:
- Azure AI Vision Image Analysis 4.0 API integration
- Multi-service Computer Vision key support
- Batch processing of odometer images
- JSON response with filename, extension, and odometer value
- Error handling and retry logic
- Configurable processing parameters

Author: Azure AI Vision OCR System
Date: August 2025
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import asyncio
from dataclasses import dataclass, asdict

# Azure AI Vision imports
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ServiceRequestError

# Image processing imports
from PIL import Image
import requests
from io import BytesIO

# Environment configuration
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class OdometerResult:
    """Data class for odometer analysis results."""
    filename: str
    file_extension: str
    odometer_value: Optional[int]
    confidence_score: float
    processing_time: float
    error_message: Optional[str]
    metadata: Dict
    timestamp: str


class AzureVisionOdometerAnalyzer:
    """
    Azure AI Vision based odometer OCR analyzer.
    
    Uses Azure Computer Vision Image Analysis 4.0 API to extract
    odometer readings from vehicle dashboard photos.
    """
    
    def __init__(self, endpoint: str = None, key: str = None):
        """
        Initialize the Azure Vision OCR analyzer.
        
        Args:
            endpoint: Azure Computer Vision endpoint URL
            key: Azure Computer Vision subscription key
        """
        # Setup logging
        self._setup_logging()
        
        # Get credentials from environment or parameters
        self.endpoint = endpoint or os.getenv('AZURE_COMPUTER_VISION_ENDPOINT')
        self.key = key or os.getenv('AZURE_COMPUTER_VISION_KEY')
        
        if not self.endpoint or not self.key:
            raise ValueError(
                "Azure Computer Vision endpoint and key must be provided either "
                "as parameters or through environment variables AZURE_COMPUTER_VISION_ENDPOINT "
                "and AZURE_COMPUTER_VISION_KEY"
            )
        
        # Initialize Azure client
        self.credential = AzureKeyCredential(self.key)
        self.client = ImageAnalysisClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        
        # Configuration
        self.max_image_size_mb = int(os.getenv('MAX_IMAGE_SIZE_MB', '4'))
        self.processing_timeout = int(os.getenv('PROCESSING_TIMEOUT_SECONDS', '30'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '5'))
        self.output_directory = Path(os.getenv('OUTPUT_DIRECTORY', '../output'))
        
        # Ensure output directory exists
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Odometer value patterns (1-6 digits)
        self.odometer_patterns = [
            r'\b(\d{1,6})\b',           # Basic 1-6 digit numbers
            r'(\d{1,3}[,\.]\d{3})',     # Numbers with thousands separators
            r'(\d{1,6})\s*(?:miles?|km|kilometers?|mi)', # Numbers followed by units
            r'(?:odometer|odo|mileage)[:=\s]*(\d{1,6})', # Numbers after odometer keywords
            r'(\d{1,6})\s*(?:total|累计)', # Numbers with total/cumulative indicators
        ]
        
        self.logger.info(f"Initialized Azure Vision OCR Analyzer")
        self.logger.info(f"Endpoint: {self.endpoint}")
        self.logger.info(f"Max image size: {self.max_image_size_mb}MB")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = logging.INFO if os.getenv('ENABLE_DETAILED_LOGGING', 'true').lower() == 'true' else logging.WARNING
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('azure_ocr_analyzer.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _validate_image_file(self, file_path: Path) -> bool:
        """
        Validate if the file is a supported image format and size.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Check file existence
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return False
            
            # Check file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_image_size_mb:
                self.logger.error(f"File too large: {file_size_mb:.2f}MB > {self.max_image_size_mb}MB")
                return False
            
            # Check if it's a valid image
            try:
                with Image.open(file_path) as img:
                    img.verify()
                return True
            except Exception as e:
                self.logger.error(f"Invalid image file {file_path}: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error validating file {file_path}: {e}")
            return False
    
    def _extract_odometer_value(self, ocr_text: str) -> Tuple[Optional[int], float]:
        """
        Extract odometer value from OCR text using pattern matching.
        
        Args:
            ocr_text: Raw OCR text from Azure Vision
            
        Returns:
            Tuple of (odometer_value, confidence_score)
        """
        if not ocr_text:
            return None, 0.0
        
        # Clean the text
        text = ocr_text.lower().strip()
        
        # Try each pattern
        potential_values = []
        
        for pattern in self.odometer_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Extract the numeric part
                    value_str = match.group(1)
                    # Remove separators
                    value_str = re.sub(r'[,\.]', '', value_str)
                    value = int(value_str)
                    
                    # Validate range (1-6 digits, reasonable odometer values)
                    if 1 <= value <= 999999:
                        confidence = self._calculate_confidence(match, text)
                        potential_values.append((value, confidence))
                        
                except (ValueError, IndexError):
                    continue
        
        if not potential_values:
            return None, 0.0
        
        # Sort by confidence and return the best match
        potential_values.sort(key=lambda x: x[1], reverse=True)
        return potential_values[0]
    
    def _calculate_confidence(self, match, full_text: str) -> float:
        """
        Calculate confidence score for an odometer value match.
        
        Args:
            match: Regex match object
            full_text: Full OCR text
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Boost confidence for certain keywords nearby
        keywords = ['odometer', 'odo', 'mileage', 'miles', 'km', 'total', 'cumulative']
        context_start = max(0, match.start() - 50)
        context_end = min(len(full_text), match.end() + 50)
        context = full_text[context_start:context_end]
        
        for keyword in keywords:
            if keyword in context:
                confidence += 0.2
                break
        
        # Boost confidence for numbers with appropriate length
        value_str = match.group(1)
        if 3 <= len(value_str) <= 6:  # Typical odometer reading length
            confidence += 0.2
        
        # Reduce confidence for very small numbers (likely not odometer)
        try:
            value = int(re.sub(r'[,\.]', '', value_str))
            if value < 10:
                confidence -= 0.3
            elif value < 100:
                confidence -= 0.1
        except:
            pass
        
        return min(1.0, max(0.0, confidence))
    
    async def analyze_image(self, image_path: Path) -> OdometerResult:
        """
        Analyze a single image for odometer reading.
        
        Args:
            image_path: Path to the odometer image
            
        Returns:
            OdometerResult: Analysis results
        """
        start_time = datetime.now()
        filename = image_path.name
        file_extension = image_path.suffix.lstrip('.')
        
        try:
            # Validate image
            if not self._validate_image_file(image_path):
                return OdometerResult(
                    filename=filename,
                    file_extension=file_extension,
                    odometer_value=None,
                    confidence_score=0.0,
                    processing_time=0.0,
                    error_message="Invalid image file",
                    metadata={},
                    timestamp=start_time.isoformat()
                )
            
            self.logger.info(f"Processing image: {filename}")
            
            # Read image data
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
            
            # Call Azure Vision API
            result = self.client.analyze(
                image_data=image_data,
                visual_features=[VisualFeatures.READ],
                language="en"
            )
            
            # Extract text from OCR results
            ocr_text = ""
            if result.read and result.read.blocks:
                for block in result.read.blocks:
                    for line in block.lines:
                        ocr_text += line.text + " "
            
            self.logger.info(f"OCR Text extracted: {ocr_text[:100]}...")
            
            # Extract odometer value
            odometer_value, confidence = self._extract_odometer_value(ocr_text)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare metadata
            metadata = {
                "ocr_text": ocr_text.strip(),
                "api_version": "4.0",
                "visual_features": ["READ"],
                "language": "en",
                "image_size_bytes": len(image_data)
            }
            
            result = OdometerResult(
                filename=filename,
                file_extension=file_extension,
                odometer_value=odometer_value,
                confidence_score=confidence,
                processing_time=processing_time,
                error_message=None,
                metadata=metadata,
                timestamp=start_time.isoformat()
            )
            
            self.logger.info(f"Completed analysis for {filename}: odometer={odometer_value}, confidence={confidence:.2f}")
            return result
            
        except HttpResponseError as e:
            error_msg = f"Azure Vision API error: {e.message}"
            self.logger.error(error_msg)
            
        except ServiceRequestError as e:
            error_msg = f"Service request error: {str(e)}"
            self.logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
        
        # Return error result
        processing_time = (datetime.now() - start_time).total_seconds()
        return OdometerResult(
            filename=filename,
            file_extension=file_extension,
            odometer_value=None,
            confidence_score=0.0,
            processing_time=processing_time,
            error_message=error_msg,
            metadata={},
            timestamp=start_time.isoformat()
        )
    
    async def analyze_batch(self, image_directory: Path) -> List[OdometerResult]:
        """
        Analyze all images in a directory for odometer readings.
        
        Args:
            image_directory: Directory containing odometer images
            
        Returns:
            List[OdometerResult]: Analysis results for all images
        """
        if not image_directory.exists():
            self.logger.error(f"Directory not found: {image_directory}")
            return []
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_files = [
            f for f in image_directory.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        
        if not image_files:
            self.logger.warning(f"No image files found in {image_directory}")
            return []
        
        self.logger.info(f"Found {len(image_files)} images to process")
        
        # Process images in batches
        results = []
        for i in range(0, len(image_files), self.batch_size):
            batch = image_files[i:i + self.batch_size]
            self.logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(image_files)-1)//self.batch_size + 1}")
            
            # Process batch concurrently
            tasks = [self.analyze_image(image_file) for image_file in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Batch processing error: {result}")
                else:
                    results.append(result)
        
        return results
    
    def save_results(self, results: List[OdometerResult], output_filename: str = None) -> Path:
        """
        Save analysis results to JSON file.
        
        Args:
            results: List of analysis results
            output_filename: Optional custom filename
            
        Returns:
            Path: Path to the saved file
        """
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"odometer_analysis_results_{timestamp}.json"
        
        output_path = self.output_directory / output_filename
        
        # Convert results to serializable format
        serializable_results = [asdict(result) for result in results]
        
        # Add summary statistics
        total_images = len(results)
        successful_extractions = len([r for r in results if r.odometer_value is not None])
        avg_confidence = sum(r.confidence_score for r in results) / total_images if total_images > 0 else 0
        avg_processing_time = sum(r.processing_time for r in results) / total_images if total_images > 0 else 0
        
        output_data = {
            "analysis_summary": {
                "total_images": total_images,
                "successful_extractions": successful_extractions,
                "success_rate": successful_extractions / total_images if total_images > 0 else 0,
                "average_confidence": avg_confidence,
                "average_processing_time": avg_processing_time,
                "timestamp": datetime.now().isoformat()
            },
            "results": serializable_results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Results saved to: {output_path}")
        return output_path
    
    def print_summary(self, results: List[OdometerResult]):
        """
        Print a summary of analysis results.
        
        Args:
            results: List of analysis results
        """
        if not results:
            print("No results to display.")
            return
        
        print("\n" + "="*80)
        print("AZURE AI VISION ODOMETER ANALYSIS SUMMARY")
        print("="*80)
        
        total = len(results)
        successful = len([r for r in results if r.odometer_value is not None])
        
        print(f"Total Images Processed: {total}")
        print(f"Successful Extractions: {successful}")
        print(f"Success Rate: {successful/total*100:.1f}%")
        
        if successful > 0:
            avg_confidence = sum(r.confidence_score for r in results if r.odometer_value is not None) / successful
            print(f"Average Confidence: {avg_confidence:.2f}")
        
        print("\nDetailed Results:")
        print("-" * 80)
        
        for result in results:
            status = "✓" if result.odometer_value is not None else "✗"
            print(f"{status} {result.filename}")
            
            if result.odometer_value is not None:
                print(f"    Odometer: {result.odometer_value:,}")
                print(f"    Confidence: {result.confidence_score:.2f}")
            else:
                print(f"    Error: {result.error_message or 'No odometer value detected'}")
            
            print(f"    Processing Time: {result.processing_time:.2f}s")
            print()


async def main():
    """
    Main function to run the odometer analysis.
    """
    try:
        # Initialize analyzer
        analyzer = AzureVisionOdometerAnalyzer()
        
        # Set up paths
        current_dir = Path(__file__).parent
        odometer_photos_dir = current_dir.parent / "odometer_photos"
        
        print("Azure AI Vision Odometer OCR Analyzer")
        print("=====================================")
        print(f"Processing images from: {odometer_photos_dir}")
        print()
        
        # Analyze all images
        results = await analyzer.analyze_batch(odometer_photos_dir)
        
        # Save results
        output_file = analyzer.save_results(results)
        
        # Print summary
        analyzer.print_summary(results)
        
        print(f"\nDetailed results saved to: {output_file}")
        
        # Print JSON results for each image
        print("\n" + "="*80)
        print("JSON RESULTS FOR EACH IMAGE")
        print("="*80)
        
        for result in results:
            json_result = {
                "filename": result.filename,
                "file_extension": result.file_extension,
                "odometer_value": result.odometer_value,
                "confidence_score": result.confidence_score,
                "metadata": result.metadata
            }
            print(json.dumps(json_result, indent=2))
            print("-" * 40)
            
    except Exception as e:
        print(f"Error running analysis: {e}")
        logging.error(f"Main execution error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
