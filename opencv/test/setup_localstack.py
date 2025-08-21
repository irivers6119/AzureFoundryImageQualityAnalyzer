#!/usr/bin/env python3
"""
LocalStack Setup Script for OpenCV Image Quality Analyzer

This script initializes all AWS resources in LocalStack for local testing:
- S3 bucket with lifecycle policies
- DynamoDB table with TTL
- Lambda function with OpenCV layer
- API Gateway with endpoints
- IAM roles and policies
"""

import os
import json
import time
import zipfile
import boto3
from pathlib import Path
import requests
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
LOCALSTACK_ENDPOINT = os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')
REGION = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
BUCKET_NAME = os.getenv('TEST_BUCKET_NAME', 'opencv-test-images')
TABLE_NAME = os.getenv('TEST_TABLE_NAME', 'opencv-test-results')
API_NAME = os.getenv('TEST_API_NAME', 'opencv-test-api')
FUNCTION_NAME = 'opencv-analyzer'

def wait_for_localstack():
    """Wait for LocalStack to be ready."""
    print("🔄 Waiting for LocalStack to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{LOCALSTACK_ENDPOINT}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ LocalStack is ready! Services: {list(health.get('services', {}).keys())}")
                return True
        except requests.exceptions.ConnectionError:
            pass
        
        print(f"   Waiting... ({i+1}/{max_retries})")
        time.sleep(2)
    
    raise Exception("❌ LocalStack failed to start")

def create_aws_clients():
    """Create AWS clients pointing to LocalStack."""
    config = {
        'endpoint_url': LOCALSTACK_ENDPOINT,
        'region_name': REGION,
        'aws_access_key_id': 'test',
        'aws_secret_access_key': 'test'
    }
    
    return {
        's3': boto3.client('s3', **config),
        'dynamodb': boto3.client('dynamodb', **config),
        'lambda': boto3.client('lambda', **config),
        'apigateway': boto3.client('apigateway', **config),
        'iam': boto3.client('iam', **config),
        'logs': boto3.client('logs', **config)
    }

def create_s3_bucket(s3_client):
    """Create S3 bucket with lifecycle policies."""
    print(f"🪣 Creating S3 bucket: {BUCKET_NAME}")
    
    try:
        # Create bucket
        if REGION == 'us-east-1':
            s3_client.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3_client.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={'LocationConstraint': REGION}
            )
        
        # Enable versioning
        s3_client.put_bucket_versioning(
            Bucket=BUCKET_NAME,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        
        # Set CORS configuration
        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': ['ETag'],
                    'MaxAgeSeconds': 3000
                }
            ]
        }
        s3_client.put_bucket_cors(Bucket=BUCKET_NAME, CORSConfiguration=cors_configuration)
        
        # Set lifecycle configuration (1-day retention)
        lifecycle_configuration = {
            'Rules': [
                {
                    'ID': 'delete_uploads_after_1_day',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'uploads/'},
                    'Expiration': {'Days': 1},
                    'AbortIncompleteMultipartUpload': {'DaysAfterInitiation': 1}
                },
                {
                    'ID': 'delete_old_versions',
                    'Status': 'Enabled',
                    'NoncurrentVersionExpiration': {'NoncurrentDays': 1}
                }
            ]
        }
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=BUCKET_NAME,
            LifecycleConfiguration=lifecycle_configuration
        )
        
        print(f"✅ S3 bucket {BUCKET_NAME} created successfully")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print(f"✅ S3 bucket {BUCKET_NAME} already exists")
        else:
            raise

def create_dynamodb_table(dynamodb_client):
    """Create DynamoDB table with TTL."""
    print(f"🗄️ Creating DynamoDB table: {TABLE_NAME}")
    
    try:
        # Create table
        dynamodb_client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': 'analysis_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'analysis_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Wait for table to be active
        waiter = dynamodb_client.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        
        # Enable TTL
        dynamodb_client.update_time_to_live(
            TableName=TABLE_NAME,
            TimeToLiveSpecification={
                'AttributeName': 'ttl',
                'Enabled': True
            }
        )
        
        print(f"✅ DynamoDB table {TABLE_NAME} created successfully")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"✅ DynamoDB table {TABLE_NAME} already exists")
        else:
            raise

def create_iam_role(iam_client):
    """Create IAM role for Lambda function."""
    print("🔐 Creating IAM role for Lambda")
    
    role_name = f"{FUNCTION_NAME}-role"
    
    # Trust policy for Lambda
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        # Create role
        iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for OpenCV Image Quality Analyzer Lambda function"
        )
        
        # Attach basic execution policy
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        # Create and attach custom policy
        custom_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{BUCKET_NAME}",
                        f"arn:aws:s3:::{BUCKET_NAME}/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem"
                    ],
                    "Resource": f"arn:aws:dynamodb:{REGION}:000000000000:table/{TABLE_NAME}"
                }
            ]
        }
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{FUNCTION_NAME}-policy",
            PolicyDocument=json.dumps(custom_policy)
        )
        
        print(f"✅ IAM role {role_name} created successfully")
        return f"arn:aws:iam::000000000000:role/{role_name}"
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            print(f"✅ IAM role {role_name} already exists")
            return f"arn:aws:iam::000000000000:role/{role_name}"
        else:
            raise

def create_lambda_function_zip():
    """Create Lambda function deployment package."""
    print("📦 Creating Lambda function deployment package")
    
    lambda_dir = Path(__file__).parent / 'lambda'
    zip_path = lambda_dir / 'function.zip'
    
    # Ensure lambda directory exists
    lambda_dir.mkdir(exist_ok=True)
    
    # Create lambda function if it doesn't exist
    lambda_function_path = lambda_dir / 'lambda_function.py'
    if not lambda_function_path.exists():
        # Copy from parent directory or create a minimal version
        lambda_code = '''
import json
import boto3
import base64
import cv2
import numpy as np
from datetime import datetime, timedelta
import os
import uuid

def lambda_handler(event, context):
    """
    Test Lambda handler for OpenCV Image Quality Analysis
    """
    print(f"Received event: {json.dumps(event)}")
    
    # Basic response for testing
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Lambda function is working!',
            'timestamp': datetime.utcnow().isoformat(),
            'event': event.get('httpMethod', 'direct-invoke')
        })
    }
'''
        lambda_function_path.write_text(lambda_code)
    
    # Create requirements.txt for Lambda
    requirements_path = lambda_dir / 'requirements.txt'
    if not requirements_path.exists():
        requirements_content = '''
boto3==1.34.144
opencv-python-headless==4.8.1.78
numpy==1.24.3
Pillow==10.0.0
'''
        requirements_path.write_text(requirements_content)
    
    # Create ZIP file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(lambda_function_path, 'lambda_function.py')
        if requirements_path.exists():
            zf.write(requirements_path, 'requirements.txt')
    
    print(f"✅ Lambda deployment package created: {zip_path}")
    return zip_path

def create_lambda_function(lambda_client, role_arn):
    """Create Lambda function."""
    print(f"🚀 Creating Lambda function: {FUNCTION_NAME}")
    
    zip_path = create_lambda_function_zip()
    
    try:
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        # Create Lambda function
        response = lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='OpenCV Image Quality Analyzer for LocalStack testing',
            Timeout=900,  # 15 minutes
            MemorySize=3008,  # Maximum memory
            Environment={
                'Variables': {
                    'S3_BUCKET': BUCKET_NAME,
                    'RESULTS_TABLE': TABLE_NAME,
                    'AWS_DEFAULT_REGION': REGION
                }
            }
        )
        
        print(f"✅ Lambda function {FUNCTION_NAME} created successfully")
        return response['FunctionArn']
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print(f"✅ Lambda function {FUNCTION_NAME} already exists")
            # Update function code
            with open(zip_path, 'rb') as f:
                zip_content = f.read()
            
            lambda_client.update_function_code(
                FunctionName=FUNCTION_NAME,
                ZipFile=zip_content
            )
            print(f"✅ Lambda function {FUNCTION_NAME} code updated")
            
            # Get function ARN
            response = lambda_client.get_function(FunctionName=FUNCTION_NAME)
            return response['Configuration']['FunctionArn']
        else:
            raise

def create_api_gateway(apigateway_client, lambda_arn):
    """Create API Gateway with Lambda integration."""
    print(f"🌐 Creating API Gateway: {API_NAME}")
    
    try:
        # Create REST API
        api_response = apigateway_client.create_rest_api(
            name=API_NAME,
            description='OpenCV Image Quality Analyzer API for LocalStack testing',
            endpointConfiguration={'types': ['REGIONAL']}
        )
        
        api_id = api_response['id']
        print(f"✅ API Gateway {API_NAME} created with ID: {api_id}")
        
        # Get root resource
        resources = apigateway_client.get_resources(restApiId=api_id)
        root_resource_id = next(r['id'] for r in resources['items'] if r['path'] == '/')
        
        # Create resources and methods
        endpoints = [
            {'path': 'analyze', 'method': 'POST'},
            {'path': 'presign', 'method': 'POST'},
            {'path': 'health', 'method': 'GET'}
        ]
        
        for endpoint in endpoints:
            # Create resource
            resource_response = apigateway_client.create_resource(
                restApiId=api_id,
                parentId=root_resource_id,
                pathPart=endpoint['path']
            )
            resource_id = resource_response['id']
            
            # Create method
            apigateway_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=endpoint['method'],
                authorizationType='NONE'
            )
            
            # Create integration
            apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=endpoint['method'],
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            )
        
        # Deploy API
        deployment = apigateway_client.create_deployment(
            restApiId=api_id,
            stageName='test',
            description='Test deployment for LocalStack'
        )
        
        api_url = f"{LOCALSTACK_ENDPOINT}/restapis/{api_id}/test/_user_request_"
        print(f"✅ API Gateway deployed at: {api_url}")
        
        return api_id, api_url
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConflictException':
            print(f"✅ API Gateway {API_NAME} already exists")
            # Find existing API
            apis = apigateway_client.get_rest_apis()
            for api in apis['items']:
                if api['name'] == API_NAME:
                    api_id = api['id']
                    api_url = f"{LOCALSTACK_ENDPOINT}/restapis/{api_id}/test/_user_request_"
                    return api_id, api_url
        else:
            raise

def create_cloudwatch_log_group(logs_client):
    """Create CloudWatch log group for Lambda function."""
    print("📊 Creating CloudWatch log group")
    
    log_group_name = f"/aws/lambda/{FUNCTION_NAME}"
    
    try:
        logs_client.create_log_group(
            logGroupName=log_group_name,
            retentionInDays=14
        )
        print(f"✅ CloudWatch log group {log_group_name} created")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
            print(f"✅ CloudWatch log group {log_group_name} already exists")
        else:
            raise

def main():
    """Main setup function."""
    print("🚀 Starting LocalStack setup for OpenCV Image Quality Analyzer")
    print("=" * 60)
    
    try:
        # Wait for LocalStack to be ready
        wait_for_localstack()
        
        # Create AWS clients
        clients = create_aws_clients()
        
        # Create resources
        create_s3_bucket(clients['s3'])
        create_dynamodb_table(clients['dynamodb'])
        create_cloudwatch_log_group(clients['logs'])
        
        role_arn = create_iam_role(clients['iam'])
        lambda_arn = create_lambda_function(clients['lambda'], role_arn)
        api_id, api_url = create_api_gateway(clients['apigateway'], lambda_arn)
        
        print("\n" + "=" * 60)
        print("🎉 LocalStack setup completed successfully!")
        print("=" * 60)
        print(f"S3 Bucket: {BUCKET_NAME}")
        print(f"DynamoDB Table: {TABLE_NAME}")
        print(f"Lambda Function: {FUNCTION_NAME}")
        print(f"API Gateway: {api_url}")
        print(f"LocalStack Health: {LOCALSTACK_ENDPOINT}/health")
        print("=" * 60)
        print("\n✅ You can now run tests with: python -m pytest tests/ -v")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()
