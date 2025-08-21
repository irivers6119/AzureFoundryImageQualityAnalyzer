#!/usr/bin/env python3
"""
Setup script for OpenCV Image Quality Analyzer

This script installs required dependencies and sets up the environment
for the OpenCV-based image quality analysis system.
"""

import subprocess
import sys
import os
from pathlib import Path


def install_requirements():
    """Install required Python packages."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("Error: requirements.txt not found!")
        return False
    
    try:
        print("Installing required packages...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        
        print("✓ All packages installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_directories():
    """Check and create necessary directories."""
    base_path = Path(__file__).parent.parent
    images_dir = base_path / "images"
    output_dir = base_path / "output"
    
    print(f"Checking directories...")
    
    if not images_dir.exists():
        print(f"Warning: Images directory not found at {images_dir}")
        print("Please ensure you have images in the '../images' folder")
    else:
        image_count = len(list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg")) + list(images_dir.glob("*.png")))
        print(f"✓ Images directory found with {image_count} images")
    
    if not output_dir.exists():
        output_dir.mkdir(exist_ok=True)
        print(f"✓ Created output directory at {output_dir}")
    else:
        print(f"✓ Output directory exists at {output_dir}")
    
    return True


def test_opencv_import():
    """Test if OpenCV is properly installed and working."""
    try:
        import cv2
        import numpy as np
        
        print(f"✓ OpenCV version: {cv2.__version__}")
        print(f"✓ NumPy version: {np.__version__}")
        
        # Test basic OpenCV functionality
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        print("✓ OpenCV basic functionality test passed")
        
        return True
        
    except ImportError as e:
        print(f"Error importing OpenCV or NumPy: {e}")
        return False
    except Exception as e:
        print(f"Error testing OpenCV functionality: {e}")
        return False


def main():
    """Main setup function."""
    print("OpenCV Image Quality Analyzer - Setup")
    print("=" * 40)
    
    # Install requirements
    if not install_requirements():
        print("Setup failed during package installation.")
        return 1
    
    # Test imports
    if not test_opencv_import():
        print("Setup failed during OpenCV testing.")
        return 1
    
    # Check directories
    if not check_directories():
        print("Setup failed during directory setup.")
        return 1
    
    print("\n" + "=" * 40)
    print("✓ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Ensure you have images in the '../images' folder")
    print("2. Run the analyzer: python opencv_analysis_session.py")
    print("3. Or run direct analysis: python opencv_image_quality_analyzer.py")
    print("4. Compare with AI results: python comparison_tool.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
