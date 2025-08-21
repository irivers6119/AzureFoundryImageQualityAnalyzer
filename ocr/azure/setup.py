"""
Setup script for Azure AI Vision Odometer OCR Analyzer

This script installs the required dependencies and configures the environment
for the Azure AI Vision Image Analysis 4.0 API odometer OCR project.
"""

import subprocess
import sys
import os
from pathlib import Path


def install_requirements():
    """Install required Python packages."""
    print("Installing required packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ All packages installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing packages: {e}")
        return False
    
    return True


def setup_environment():
    """Setup environment configuration."""
    print("Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        # Copy example to .env
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        
        print("✓ Created .env file from template")
        print("⚠️  Please update .env file with your Azure Computer Vision credentials:")
        print("   - AZURE_COMPUTER_VISION_ENDPOINT")
        print("   - AZURE_COMPUTER_VISION_KEY")
    elif env_file.exists():
        print("✓ Environment file already exists")
    else:
        print("✗ No environment template found")
        return False
    
    return True


def create_output_directory():
    """Create output directory for results."""
    output_dir = Path("../output")
    output_dir.mkdir(parents=True, exist_ok=True)
    print("✓ Output directory created")
    return True


def verify_odometer_photos():
    """Verify odometer photos directory exists."""
    photos_dir = Path("../odometer_photos")
    
    if not photos_dir.exists():
        print("✗ Odometer photos directory not found")
        print(f"   Expected: {photos_dir.absolute()}")
        return False
    
    # Count image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    image_files = [
        f for f in photos_dir.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    print(f"✓ Found {len(image_files)} image files in odometer_photos directory")
    
    if len(image_files) == 0:
        print("⚠️  No image files found to process")
    
    return True


def main():
    """Main setup function."""
    print("Azure AI Vision Odometer OCR Analyzer - Setup")
    print("=" * 50)
    
    success = True
    
    # Install requirements
    if not install_requirements():
        success = False
    
    # Setup environment
    if not setup_environment():
        success = False
    
    # Create directories
    if not create_output_directory():
        success = False
    
    # Verify photos directory
    if not verify_odometer_photos():
        success = False
    
    print("\n" + "=" * 50)
    
    if success:
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update .env file with your Azure Computer Vision credentials")
        print("2. Run the analyzer: python azure_vision_ocr_analyzer.py")
    else:
        print("✗ Setup completed with errors")
        print("Please resolve the issues above before running the analyzer")
    
    return success


if __name__ == "__main__":
    main()
