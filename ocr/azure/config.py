"""
Environment configuration loader for Azure OCR project.

This module loads environment variables from the parent project's .env file
to use the same Azure Computer Vision credentials across the entire project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def load_project_environment():
    """
    Load environment variables from the main project .env file.
    
    This ensures the Azure OCR module uses the same credentials as the main project.
    """
    # Get the main project directory (two levels up from this file)
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    main_env_file = project_root / ".env"
    
    if main_env_file.exists():
        load_dotenv(main_env_file)
        print(f"Loaded environment from: {main_env_file}")
        return True
    else:
        # Fallback to local .env file
        local_env_file = current_file.parent / ".env"
        if local_env_file.exists():
            load_dotenv(local_env_file)
            print(f"Loaded environment from: {local_env_file}")
            return True
        else:
            print("Warning: No .env file found")
            return False


def get_azure_credentials():
    """
    Get Azure Computer Vision credentials from environment variables.
    
    Returns:
        tuple: (endpoint, key) or (None, None) if not found
    """
    endpoint = os.getenv('AZURE_COMPUTER_VISION_ENDPOINT')
    key = os.getenv('AZURE_COMPUTER_VISION_KEY')
    
    return endpoint, key


def validate_azure_credentials():
    """
    Validate that Azure Computer Vision credentials are available.
    
    Returns:
        bool: True if credentials are valid, False otherwise
    """
    endpoint, key = get_azure_credentials()
    
    if not endpoint:
        print("Error: AZURE_COMPUTER_VISION_ENDPOINT not found in environment")
        return False
    
    if not key:
        print("Error: AZURE_COMPUTER_VISION_KEY not found in environment")
        return False
    
    # Basic validation
    if not endpoint.startswith('https://'):
        print("Error: AZURE_COMPUTER_VISION_ENDPOINT should start with https://")
        return False
    
    if len(key) < 32:
        print("Error: AZURE_COMPUTER_VISION_KEY appears to be too short")
        return False
    
    return True


# Auto-load environment when module is imported
load_project_environment()
