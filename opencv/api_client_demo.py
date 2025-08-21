#!/usr/bin/env python3
"""
Test client for OpenCV Image Quality Analyzer API.
Demonstrates how to use the API endpoints.
"""

import json
import os
import requests
import time
from pathlib import Path
from typing import List, Dict

class OpenCVAPIClient:
    """Client for interacting with the OpenCV Image Quality Analyzer API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict:
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_profiles(self) -> Dict:
        """Get available analysis profiles."""
        response = self.session.get(f"{self.base_url}/profiles")
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict:
        """Get service statistics."""
        response = self.session.get(f"{self.base_url}/stats")
        response.raise_for_status()
        return response.json()
    
    def analyze_single_image(
        self, 
        image_path: str, 
        profile: str = "general",
        max_dimension: int = None
    ) -> Dict:
        """
        Analyze a single image.
        
        Args:
            image_path: Path to the image file
            profile: Analysis profile (general, document, portrait)
            max_dimension: Maximum image dimension for processing
            
        Returns:
            Analysis result dictionary
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'profile': profile}
            if max_dimension:
                data['max_dimension'] = max_dimension
            
            response = self.session.post(
                f"{self.base_url}/analyze",
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()
    
    def analyze_batch_images(
        self, 
        image_paths: List[str], 
        profile: str = "general",
        max_dimension: int = None
    ) -> Dict:
        """
        Analyze multiple images in batch.
        
        Args:
            image_paths: List of paths to image files
            profile: Analysis profile for all images
            max_dimension: Maximum image dimension for processing
            
        Returns:
            Batch analysis result dictionary
        """
        files = []
        try:
            for path in image_paths:
                if not os.path.exists(path):
                    print(f"Warning: Image file not found: {path}")
                    continue
                files.append(('images', open(path, 'rb')))
            
            if not files:
                raise ValueError("No valid image files found")
            
            data = {'profile': profile}
            if max_dimension:
                data['max_dimension'] = max_dimension
            
            response = self.session.post(
                f"{self.base_url}/analyze/batch",
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()
        
        finally:
            # Close all file handles
            for _, file_handle in files:
                file_handle.close()
    
    def analyze_image_url(
        self, 
        image_url: str, 
        profile: str = "general",
        max_dimension: int = None
    ) -> Dict:
        """
        Analyze an image from a URL.
        
        Args:
            image_url: URL of the image to analyze
            profile: Analysis profile
            max_dimension: Maximum image dimension for processing
            
        Returns:
            Analysis result dictionary
        """
        data = {
            'image_url': image_url,
            'profile': profile
        }
        if max_dimension:
            data['max_dimension'] = max_dimension
        
        response = self.session.post(
            f"{self.base_url}/analyze/url",
            json=data
        )
        response.raise_for_status()
        return response.json()


def demo_api_usage():
    """Demonstrate API usage with sample images."""
    print("🚀 OpenCV Image Quality Analyzer API Demo")
    print("=" * 50)
    
    # Initialize client
    client = OpenCVAPIClient()
    
    try:
        # Health check
        print("🔍 Checking API health...")
        health = client.health_check()
        print(f"✅ API Status: {health['status']}")
        print(f"📦 OpenCV Version: {health['opencv_version']}")
        print(f"🔧 API Version: {health['api_version']}")
        
        # Get available profiles
        print(f"\n📋 Available profiles:")
        profiles = client.get_profiles()
        for profile in profiles['profiles']:
            print(f"  • {profile['name']}: {profile['description']}")
        
        # Find sample images
        images_dir = Path(__file__).parent.parent / "images"
        if not images_dir.exists():
            print(f"\n❌ Images directory not found: {images_dir}")
            print("Please ensure you have sample images in the ../images directory")
            return
        
        # Get list of image files
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg")) + list(images_dir.glob("*.png"))
        
        if not image_files:
            print(f"\n❌ No image files found in {images_dir}")
            return
        
        print(f"\n📸 Found {len(image_files)} images for testing")
        
        # Test single image analysis
        if image_files:
            test_image = str(image_files[0])
            print(f"\n🔬 Analyzing single image: {Path(test_image).name}")
            
            start_time = time.time()
            result = client.analyze_single_image(test_image, profile="general")
            end_time = time.time()
            
            print(f"✅ Analysis complete in {end_time - start_time:.2f} seconds")
            print(f"📊 Overall Score: {result['Overall_Score']:.1f}/10")
            print(f"🎯 Decision: {result['Decision']}")
            print(f"📏 File Size: {result['file_size_bytes']} bytes")
            print(f"⏱️ Processing Time: {result['processing_time_seconds']:.3f} seconds")
            
            if result.get('detailed_metrics'):
                print("📈 Detailed Metrics:")
                for metric, value in result['detailed_metrics'].items():
                    print(f"  • {metric}: {value:.2f}")
        
        # Test batch analysis (limit to first 3 images for demo)
        batch_images = [str(img) for img in image_files[:3]]
        if len(batch_images) > 1:
            print(f"\n📦 Batch analyzing {len(batch_images)} images...")
            
            start_time = time.time()
            batch_result = client.analyze_batch_images(batch_images, profile="document")
            end_time = time.time()
            
            print(f"✅ Batch analysis complete in {end_time - start_time:.2f} seconds")
            print(f"📊 Results: {batch_result['successful_analyses']}/{batch_result['total_images']} successful")
            
            if batch_result['results']:
                print("📋 Individual Results:")
                for result in batch_result['results']:
                    print(f"  • {result['file_name']}: {result['Overall_Score']:.1f} ({result['Decision']})")
            
            if batch_result['errors']:
                print("❌ Errors:")
                for error in batch_result['errors']:
                    print(f"  • {error['filename']}: {error['error']}")
        
        # Test URL analysis (optional - requires internet)
        print(f"\n🌐 Testing URL analysis (optional)...")
        try:
            url_result = client.analyze_image_url(
                "https://via.placeholder.com/300x200.jpg",
                profile="general"
            )
            print(f"✅ URL analysis successful: {url_result['Overall_Score']:.1f}/10")
        except Exception as e:
            print(f"⚠️ URL analysis skipped: {e}")
        
        # Get service stats
        print(f"\n📊 Service Statistics:")
        stats = client.get_stats()
        service_stats = stats.get('service', {})
        system_stats = stats.get('system', {})
        
        print(f"  • Uptime: {service_stats.get('uptime_seconds', 0):.1f} seconds")
        print(f"  • Python Version: {service_stats.get('python_version', 'Unknown')}")
        
        if 'error' not in system_stats:
            print(f"  • CPU Usage: {system_stats.get('cpu_percent', 0):.1f}%")
            print(f"  • Memory Usage: {system_stats.get('memory_percent', 0):.1f}%")
        
        print(f"\n🎉 API Demo completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server.")
        print("Please ensure the API server is running:")
        print("  docker-compose -f docker-compose-api.yml up opencv-api")
        print("  or")
        print("  python3 api_service.py")
    
    except Exception as e:
        print(f"❌ Error during demo: {e}")


def test_api_endpoints():
    """Test all API endpoints systematically."""
    print("🧪 Testing API Endpoints")
    print("=" * 30)
    
    client = OpenCVAPIClient()
    
    tests = [
        ("Health Check", lambda: client.health_check()),
        ("Get Profiles", lambda: client.get_profiles()),
        ("Get Stats", lambda: client.get_stats()),
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"Testing {test_name}... ", end="")
            result = test_func()
            print("✅ PASS")
        except Exception as e:
            print(f"❌ FAIL: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_api_endpoints()
    else:
        demo_api_usage()
