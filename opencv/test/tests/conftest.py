"""
Pytest configuration for OpenCV Image Quality Analyzer LocalStack tests.
"""

import os
import pytest
import boto3
from dotenv import load_dotenv

# Load test environment
load_dotenv()

# Test configuration
LOCALSTACK_ENDPOINT = os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')
REGION = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
BUCKET_NAME = os.getenv('TEST_BUCKET_NAME', 'opencv-test-images')
TABLE_NAME = os.getenv('TEST_TABLE_NAME', 'opencv-test-results')
FUNCTION_NAME = 'opencv-analyzer'

@pytest.fixture(scope="session")
def aws_config():
    """AWS configuration for LocalStack."""
    return {
        'endpoint_url': LOCALSTACK_ENDPOINT,
        'region_name': REGION,
        'aws_access_key_id': 'test',
        'aws_secret_access_key': 'test'
    }

@pytest.fixture(scope="session")
def s3_client(aws_config):
    """S3 client for LocalStack."""
    return boto3.client('s3', **aws_config)

@pytest.fixture(scope="session")
def dynamodb_client(aws_config):
    """DynamoDB client for LocalStack."""
    return boto3.client('dynamodb', **aws_config)

@pytest.fixture(scope="session")
def lambda_client(aws_config):
    """Lambda client for LocalStack."""
    return boto3.client('lambda', **aws_config)

@pytest.fixture(scope="session")
def apigateway_client(aws_config):
    """API Gateway client for LocalStack."""
    return boto3.client('apigateway', **aws_config)

@pytest.fixture(scope="session")
def test_bucket_name():
    """Test S3 bucket name."""
    return BUCKET_NAME

@pytest.fixture(scope="session")
def test_table_name():
    """Test DynamoDB table name."""
    return TABLE_NAME

@pytest.fixture(scope="session")
def test_function_name():
    """Test Lambda function name."""
    return FUNCTION_NAME

@pytest.fixture(scope="function")
def test_image_data():
    """Generate test image data."""
    import numpy as np
    import cv2
    
    # Create a simple test image (100x100 red square)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :] = [0, 0, 255]  # Red color
    
    # Convert to bytes
    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()

@pytest.fixture(scope="function")
def large_test_image_data():
    """Generate large test image data for multipart testing."""
    import numpy as np
    import cv2
    
    # Create a larger test image (2000x2000)
    img = np.zeros((2000, 2000, 3), dtype=np.uint8)
    # Create a gradient pattern
    for i in range(2000):
        for j in range(2000):
            img[i, j] = [i % 256, j % 256, (i + j) % 256]
    
    # Convert to bytes with high quality to ensure large size
    _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return buffer.tobytes()

@pytest.fixture(scope="function")
def cleanup_s3_objects(s3_client, test_bucket_name):
    """Cleanup S3 objects after test."""
    created_objects = []
    
    def add_object(key):
        created_objects.append(key)
    
    yield add_object
    
    # Cleanup
    for obj_key in created_objects:
        try:
            s3_client.delete_object(Bucket=test_bucket_name, Key=obj_key)
        except Exception:
            pass  # Ignore cleanup errors

@pytest.fixture(scope="function")
def cleanup_dynamodb_items(dynamodb_client, test_table_name):
    """Cleanup DynamoDB items after test."""
    created_items = []
    
    def add_item(analysis_id):
        created_items.append(analysis_id)
    
    yield add_item
    
    # Cleanup
    for item_id in created_items:
        try:
            dynamodb_client.delete_item(
                TableName=test_table_name,
                Key={'analysis_id': {'S': item_id}}
            )
        except Exception:
            pass  # Ignore cleanup errors

@pytest.fixture(scope="session", autouse=True)
def ensure_localstack_ready():
    """Ensure LocalStack is ready before running tests."""
    import requests
    import time
    
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{LOCALSTACK_ENDPOINT}/health")
            if response.status_code == 200:
                health = response.json()
                required_services = ['s3', 'dynamodb', 'lambda', 'apigateway']
                available_services = health.get('services', {})
                
                if all(available_services.get(svc) == 'available' for svc in required_services):
                    return  # All services ready
                    
        except requests.exceptions.ConnectionError:
            pass
        
        if i == max_retries - 1:
            pytest.fail("LocalStack is not ready. Please start LocalStack and run setup_localstack.py")
        
        time.sleep(2)

# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "s3: mark test as S3 related")
    config.addinivalue_line("markers", "lambda: mark test as Lambda related")
    config.addinivalue_line("markers", "dynamodb: mark test as DynamoDB related")
    config.addinivalue_line("markers", "apigateway: mark test as API Gateway related")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "multipart: mark test as multipart upload test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
