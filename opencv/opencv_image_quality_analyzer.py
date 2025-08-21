import cv2
import numpy as np
import os
import json
import datetime
from pathlib import Path
import concurrent.futures
import multiprocessing
from typing import Dict, List, Tuple, Optional


class OpenCVImageQualityAnalyzer:
    """
    OpenCV-based image quality analyzer that replaces AI-based analysis with computer vision algorithms.
    
    This class evaluates image quality using multiple metrics:
    - Brightness: Overall lightness of the image
    - Contrast: Dynamic range and tonal separation
    - Sharpness: Edge clarity and detail preservation
    - Noise: Visual noise and grain assessment
    - Exposure: Over/under exposure detection
    - Edge Quality: Detail visibility and preservation
    
    The analyzer produces scores compatible with the original AI-based system.
    """
    
    def __init__(self, profile: str = 'general'):
        """
        Initialize the analyzer with quality thresholds and weight profiles.
        
        Args:
            profile: Quality assessment profile ('general', 'document', 'portrait')
        """
        self.quality_thresholds = {
            'excellent': 8.5,
            'good': 7.0,
            'acceptable': 6.0,
            'poor': 4.0,
            'unacceptable': 0.0
        }
        
        self.weight_profiles = {
            'general': {
                'brightness': 0.15,
                'contrast': 0.20,
                'sharpness': 0.25,
                'noise': 0.15,
                'exposure': 0.15,
                'edge_quality': 0.10
            },
            'document': {
                'brightness': 0.10,
                'contrast': 0.25,
                'sharpness': 0.40,
                'noise': 0.05,
                'exposure': 0.15,
                'edge_quality': 0.05
            },
            'portrait': {
                'brightness': 0.15,
                'contrast': 0.10,
                'sharpness': 0.25,
                'noise': 0.25,
                'exposure': 0.20,
                'edge_quality': 0.05
            }
        }
        
        self.current_profile = profile
        self.weights = self.weight_profiles.get(profile, self.weight_profiles['general'])
        
        # Processing settings
        self.max_image_size = (1920, 1080)  # Resize large images for faster processing
        self.supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
        
    def _resize_image_if_needed(self, image: np.ndarray) -> np.ndarray:
        """Resize image if it's larger than max_image_size to improve processing speed."""
        h, w = image.shape[:2]
        max_w, max_h = self.max_image_size
        
        if w > max_w or h > max_h:
            # Calculate scaling factor
            scale = min(max_w / w, max_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        return image
    
    def analyze_brightness(self, image: np.ndarray) -> float:
        """
        Analyze image brightness using average pixel intensity.
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            Brightness score (0-10)
        """
        if len(image.shape) == 3:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Calculate average brightness
        brightness = np.mean(gray)
        
        # Optimal brightness is around 127.5 (middle of 0-255 range)
        # Score decreases as brightness deviates from optimal
        deviation = abs(brightness - 127.5) / 127.5
        brightness_score = max(10 - (deviation * 10), 0)
        
        return min(brightness_score, 10.0)
    
    def analyze_contrast(self, image: np.ndarray) -> float:
        """
        Analyze image contrast using standard deviation of pixel intensities.
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            Contrast score (0-10)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Calculate contrast using standard deviation
        contrast = np.std(gray)
        
        # Normalize to 0-10 scale (good contrast is typically > 50)
        contrast_score = min(contrast / 64.0 * 10, 10.0)
        
        return contrast_score
    
    def analyze_sharpness(self, image: np.ndarray) -> float:
        """
        Analyze image sharpness using Laplacian variance method.
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            Sharpness score (0-10)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Calculate Laplacian variance (higher = sharper)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Also use Sobel gradient for additional sharpness assessment
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        sobel_mean = np.mean(sobel_magnitude)
        
        # Combine both metrics
        combined_sharpness = (laplacian_var / 500.0) * 0.7 + (sobel_mean / 100.0) * 0.3
        sharpness_score = min(combined_sharpness * 10, 10.0)
        
        return sharpness_score
    
    def analyze_noise(self, image: np.ndarray) -> float:
        """
        Analyze image noise using bilateral filter comparison.
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            Noise score (0-10, higher means less noise)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply bilateral filter to remove noise while preserving edges
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # Calculate difference (noise level)
        noise_level = cv2.norm(gray, denoised, cv2.NORM_L2) / (gray.shape[0] * gray.shape[1])
        
        # Convert to 0-10 scale (lower noise = higher score)
        noise_score = max(10 - (noise_level / 10.0), 0)
        
        return min(noise_score, 10.0)
    
    def analyze_exposure(self, image: np.ndarray) -> float:
        """
        Analyze image exposure using histogram analysis.
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            Exposure score (0-10)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        total_pixels = gray.size
        
        # Check for underexposure (too many dark pixels)
        underexposed = np.sum(hist[0:16]) / total_pixels
        
        # Check for overexposure (too many bright pixels)
        overexposed = np.sum(hist[240:256]) / total_pixels
        
        # Good exposure should have minimal clipping
        exposure_problems = (underexposed + overexposed) * 100
        exposure_score = max(10 - exposure_problems, 0)
        
        return min(exposure_score, 10.0)
    
    def analyze_edge_quality(self, image: np.ndarray) -> float:
        """
        Analyze edge quality and detail preservation using Canny edge detection.
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            Edge quality score (0-10)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply Gaussian blur to reduce noise before edge detection
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Detect edges using Canny
        edges = cv2.Canny(blurred, 50, 150)
        
        # Calculate edge density
        edge_density = cv2.countNonZero(edges) / edges.size
        
        # Convert to 0-10 scale
        edge_score = min(edge_density * 100, 10.0)
        
        return edge_score
    
    def analyze_single_image(self, image_path: str) -> Dict:
        """
        Analyze a single image and return quality metrics.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing quality metrics and overall assessment
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Resize if needed for faster processing
            image = self._resize_image_if_needed(image)
            
            # Extract file information
            file_path = Path(image_path)
            file_name = file_path.stem
            file_extension = file_path.suffix[1:]  # Remove the dot
            
            # Calculate individual metrics
            metrics = {
                'brightness': float(self.analyze_brightness(image)),
                'contrast': float(self.analyze_contrast(image)),
                'sharpness': float(self.analyze_sharpness(image)),
                'noise': float(self.analyze_noise(image)),
                'exposure': float(self.analyze_exposure(image)),
                'edge_quality': float(self.analyze_edge_quality(image))
            }
            
            # Calculate weighted overall score
            overall_score = float(sum(
                metrics[metric] * self.weights[metric] 
                for metric in metrics
            ))
            
            # Map to original AI system format for compatibility
            result = {
                "file_name": file_name,
                "file_extension": file_extension,
                "Lighting_and_Exposure": round((metrics['brightness'] + metrics['exposure']) / 2, 1),
                "Angle_and_Composition": round((metrics['edge_quality'] + metrics['contrast']) / 2, 1),
                "Clarity_and_Resolution": round((metrics['sharpness'] + metrics['edge_quality']) / 2, 1),
                "Detail_Visibility": round((metrics['contrast'] + metrics['sharpness']) / 2, 1),
                "Background_and_Distractions": round(metrics['noise'], 1),
                "Overall_Score": round(overall_score, 1),
                "Decision": "Keep" if overall_score > 7.0 else "Retake",
                # Additional detailed metrics for analysis
                "detailed_metrics": {
                    "brightness": round(metrics['brightness'], 2),
                    "contrast": round(metrics['contrast'], 2),
                    "sharpness": round(metrics['sharpness'], 2),
                    "noise": round(metrics['noise'], 2),
                    "exposure": round(metrics['exposure'], 2),
                    "edge_quality": round(metrics['edge_quality'], 2)
                }
            }
            
            return result
            
        except Exception as e:
            return {
                "file_name": Path(image_path).stem,
                "file_extension": Path(image_path).suffix[1:] if Path(image_path).suffix else "unknown",
                "error": str(e),
                "Overall_Score": 0.0,
                "Decision": "Error"
            }
    
    def analyze_batch(self, images_directory: str, max_workers: Optional[int] = None) -> List[Dict]:
        """
        Analyze all images in a directory using parallel processing.
        
        Args:
            images_directory: Path to directory containing images
            max_workers: Maximum number of worker threads (None for auto)
            
        Returns:
            List of analysis results for each image
        """
        # Find all image files
        image_files = []
        images_path = Path(images_directory)
        
        if not images_path.exists():
            raise FileNotFoundError(f"Images directory not found: {images_directory}")
        
        for ext in self.supported_formats:
            image_files.extend(images_path.glob(f"*{ext}"))
            image_files.extend(images_path.glob(f"*{ext.upper()}"))
        
        if not image_files:
            print(f"No supported image files found in {images_directory}")
            return []
        
        print(f"Found {len(image_files)} images to analyze...")
        
        # Set up parallel processing
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), len(image_files))
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(self.analyze_single_image, str(img_path)): img_path 
                for img_path in image_files
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_path):
                img_path = future_to_path[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"Analyzed: {img_path.name} - Score: {result.get('Overall_Score', 'Error')}")
                except Exception as e:
                    print(f"Error analyzing {img_path}: {e}")
                    results.append({
                        "file_name": img_path.stem,
                        "file_extension": img_path.suffix[1:],
                        "error": str(e),
                        "Overall_Score": 0.0,
                        "Decision": "Error"
                    })
        
        return results
    
    def save_results(self, results: List[Dict], output_directory: str) -> str:
        """
        Save analysis results to JSON file in the output directory.
        
        Args:
            results: List of analysis results
            output_directory: Directory to save results
            
        Returns:
            Path to saved file
        """
        # Create output directory if it doesn't exist
        output_path = Path(output_directory)
        output_path.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        now = datetime.datetime.now()
        filename = f"{now.strftime('%Y%m%d %H-%M-%S')} OpenCV Analysis Results.json"
        file_path = output_path / filename
        
        # Prepare data for saving
        output_data = {
            "analysis_timestamp": now.isoformat(),
            "analyzer_version": "OpenCV 1.0",
            "profile_used": self.current_profile,
            "total_images": len(results),
            "summary": self._generate_summary(results),
            "results": results
        }
        
        # Save to file
        try:
            with open(file_path, 'w') as f:
                json.dump(output_data, f, indent=4)
            print(f"Results saved to: {file_path}")
            return str(file_path)
        except Exception as e:
            print(f"Error saving results: {e}")
            raise
    
    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Generate summary statistics from analysis results."""
        if not results:
            return {}
        
        valid_results = [r for r in results if 'Overall_Score' in r and isinstance(r['Overall_Score'], (int, float))]
        
        if not valid_results:
            return {"error": "No valid results to summarize"}
        
        scores = [r['Overall_Score'] for r in valid_results]
        keep_count = sum(1 for r in valid_results if r.get('Decision') == 'Keep')
        
        return {
            "total_analyzed": len(valid_results),
            "average_score": round(np.mean(scores), 2),
            "median_score": round(np.median(scores), 2),
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
            "keep_recommendations": keep_count,
            "retake_recommendations": len(valid_results) - keep_count,
            "keep_percentage": round((keep_count / len(valid_results)) * 100, 1)
        }
    
    def generate_detailed_report(self, results: List[Dict]) -> str:
        """
        Generate a detailed text report of the analysis.
        
        Args:
            results: List of analysis results
            
        Returns:
            Formatted report string
        """
        if not results:
            return "No results to report."
        
        summary = self._generate_summary(results)
        
        report = []
        report.append("=" * 60)
        report.append("OpenCV IMAGE QUALITY ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Analysis Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Profile Used: {self.current_profile}")
        report.append(f"Total Images Analyzed: {summary.get('total_analyzed', 0)}")
        report.append("")
        
        if 'error' not in summary:
            report.append("SUMMARY STATISTICS:")
            report.append("-" * 20)
            report.append(f"Average Score: {summary['average_score']}")
            report.append(f"Median Score: {summary['median_score']}")
            report.append(f"Score Range: {summary['min_score']} - {summary['max_score']}")
            report.append(f"Keep Recommendations: {summary['keep_recommendations']} ({summary['keep_percentage']}%)")
            report.append(f"Retake Recommendations: {summary['retake_recommendations']}")
            report.append("")
        
        report.append("INDIVIDUAL RESULTS:")
        report.append("-" * 20)
        
        # Sort results by overall score (descending)
        valid_results = [r for r in results if 'Overall_Score' in r and isinstance(r['Overall_Score'], (int, float))]
        valid_results.sort(key=lambda x: x['Overall_Score'], reverse=True)
        
        for result in valid_results:
            score = result['Overall_Score']
            decision = result.get('Decision', 'Unknown')
            filename = f"{result['file_name']}.{result['file_extension']}"
            
            report.append(f"{filename:<40} Score: {score:>5.1f} Decision: {decision}")
        
        # Add error results if any
        error_results = [r for r in results if 'error' in r]
        if error_results:
            report.append("")
            report.append("ERRORS:")
            report.append("-" * 20)
            for result in error_results:
                filename = f"{result['file_name']}.{result['file_extension']}"
                error = result['error']
                report.append(f"{filename}: {error}")
        
        return "\n".join(report)


def main():
    """Main function for command-line usage."""
    # Set up paths relative to the opencv folder or use absolute paths in container
    container_mode = os.environ.get('CONTAINER_MODE', 'false').lower() == 'true'
    
    if container_mode:
        # Running in container
        images_dir = Path("/app/images")
        output_dir = Path("/app/output")
    else:
        # Running on host
        current_dir = Path(__file__).parent.parent
        images_dir = current_dir / "images"
        output_dir = current_dir / "output"
    
    print("OpenCV Image Quality Analyzer")
    print("=" * 40)
    print(f"Images directory: {images_dir}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Initialize analyzer
    analyzer = OpenCVImageQualityAnalyzer(profile='general')
    
    try:
        # Analyze all images
        results = analyzer.analyze_batch(str(images_dir))
        
        if results:
            # Save results
            saved_file = analyzer.save_results(results, str(output_dir))
            
            # Generate and print detailed report
            report = analyzer.generate_detailed_report(results)
            print(report)
            
            # Also save report as text file
            report_path = output_dir / f"{datetime.datetime.now().strftime('%Y%m%d %H-%M-%S')} OpenCV Analysis Report.txt"
            with open(report_path, 'w') as f:
                f.write(report)
            print(f"\nDetailed report saved to: {report_path}")
            
        else:
            print("No images found or analyzed.")
            
    except Exception as e:
        print(f"Error during analysis: {e}")


if __name__ == "__main__":
    main()
