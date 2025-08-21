#!/usr/bin/env python3
"""
Verification script for LocalStack setup.

This script verifies that all AWS resources were created successfully
and are functioning properly in LocalStack.
"""

import os
import json
import boto3
import requests
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Configuration
LOCALSTACK_ENDPOINT = os.getenv('AWS_ENDPOINT_URL', 'http://localhost:4566')
REGION = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
BUCKET_NAME = os.getenv('TEST_BUCKET_NAME', 'opencv-test-images')
TABLE_NAME = os.getenv('TEST_TABLE_NAME', 'opencv-test-results')
FUNCTION_NAME = 'opencv-analyzer'

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
        'iam': boto3.client('iam', **config)
    }

def verify_localstack_health():
    """Verify LocalStack is running and healthy."""
    print("🔍 Checking LocalStack health...")
    
    try:
        response = requests.get(f"{LOCALSTACK_ENDPOINT}/health")
        health = response.json()
        
        services = health.get('services', {})
        print(f"✅ LocalStack is healthy")
        print(f"   Available services: {list(services.keys())}")
        
        # Check specific services we need
        required_services = ['s3', 'dynamodb', 'lambda', 'apigateway', 'iam']
        for service in required_services:
            status = services.get(service, 'not available')
            if status == 'available':
                print(f"   ✅ {service}: {status}")
            else:
                print(f"   ❌ {service}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ LocalStack health check failed: {e}")
        return False

def verify_s3_bucket(s3_client):
    """Verify S3 bucket exists and is configured correctly."""
    print(f"🪣 Verifying S3 bucket: {BUCKET_NAME}")
    
    try:
        # Check if bucket exists
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        print(f"   ✅ Bucket exists")
        
        # Check versioning
        versioning = s3_client.get_bucket_versioning(Bucket=BUCKET_NAME)
        if versioning.get('Status') == 'Enabled':
            print(f"   ✅ Versioning enabled")
        else:
            print(f"   ⚠️ Versioning not enabled")
        
        # Check CORS
        try:
            cors = s3_client.get_bucket_cors(Bucket=BUCKET_NAME)
            print(f"   ✅ CORS configured")
        except ClientError:
            print(f"   ⚠️ CORS not configured")
        
        # Check lifecycle
        try:
            lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=BUCKET_NAME)
            rules = lifecycle.get('Rules', [])
            print(f"   ✅ Lifecycle configured ({len(rules)} rules)")
        except ClientError:
            print(f"   ⚠️ Lifecycle not configured")
        
        # Test upload
        test_key = 'test-verification.txt'
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=test_key,
            Body=b'LocalStack verification test'
        )
        print(f"   ✅ Test upload successful")
        
        # Clean up test object
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=test_key)
        
        return True
        
    except Exception as e:
        print(f"   ❌ S3 verification failed: {e}")
        return False

def verify_dynamodb_table(dynamodb_client):
    """Verify DynamoDB table exists and is configured correctly."""
    print(f"🗄️ Verifying DynamoDB table: {TABLE_NAME}")
    
    try:
        # Check if table exists
        response = dynamodb_client.describe_table(TableName=TABLE_NAME)
        table = response['Table']
        
        print(f"   ✅ Table exists")
        print(f"   Status: {table['TableStatus']}")
        print(f"   Billing mode: {table.get('BillingModeSummary', {}).get('BillingMode', 'Unknown')}")
        
        # Check TTL
        try:
            ttl_response = dynamodb_client.describe_time_to_live(TableName=TABLE_NAME)
            ttl_status = ttl_response['TimeToLiveDescription']['TimeToLiveStatus']
            print(f"   ✅ TTL status: {ttl_status}")
        except ClientError:
            print(f"   ⚠️ TTL not configured")
        
        # Test write/read
        test_item = {
            'analysis_id': {'S': 'test-verification'},
            'timestamp': {'S': '2025-01-01T00:00:00Z'},
            'test_data': {'S': 'LocalStack verification'}
        }
        
        dynamodb_client.put_item(TableName=TABLE_NAME, Item=test_item)
        print(f"   ✅ Test write successful")
        
        response = dynamodb_client.get_item(
            TableName=TABLE_NAME,
            Key={'analysis_id': {'S': 'test-verification'}}
        )
        
        if 'Item' in response:
            print(f"   ✅ Test read successful")
        else:
            print(f"   ❌ Test read failed")
        
        # Clean up test item
        dynamodb_client.delete_item(
            TableName=TABLE_NAME,
            Key={'analysis_id': {'S': 'test-verification'}}
        )
        
        return True
        
    except Exception as e:
        print(f"   ❌ DynamoDB verification failed: {e}")
        return False

def verify_lambda_function(lambda_client):
    """Verify Lambda function exists and is configured correctly."""
    print(f"🚀 Verifying Lambda function: {FUNCTION_NAME}")
    
    try:
        # Check if function exists
        response = lambda_client.get_function(FunctionName=FUNCTION_NAME)
        config = response['Configuration']
        
        print(f"   ✅ Function exists")
        print(f"   Runtime: {config['Runtime']}")
        print(f"   Memory: {config['MemorySize']} MB")
        print(f"   Timeout: {config['Timeout']} seconds")
        
        # Check environment variables
        env_vars = config.get('Environment', {}).get('Variables', {})
        required_vars = ['S3_BUCKET', 'RESULTS_TABLE']
        
        for var in required_vars:
            if var in env_vars:
                print(f"   ✅ Environment variable {var}: {env_vars[var]}")
            else:
                print(f"   ❌ Missing environment variable: {var}")
        
        # Test invoke
        test_payload = {
            'httpMethod': 'GET',
            'path': '/health',
            'body': None
        }
        
        invoke_response = lambda_client.invoke(
            FunctionName=FUNCTION_NAME,
            Payload=json.dumps(test_payload)
        )
        
        response_payload = json.loads(invoke_response['Payload'].read())
        
        if invoke_response['StatusCode'] == 200:
            print(f"   ✅ Test invocation successful")
            print(f"   Response: {response_payload.get('statusCode', 'unknown')}")
        else:
            print(f"   ❌ Test invocation failed: {response_payload}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Lambda verification failed: {e}")
        return False

def verify_api_gateway(apigateway_client):
    """Verify API Gateway exists and is configured correctly."""
    print(f"🌐 Verifying API Gateway")
    
    try:
        # Find our API
        apis = apigateway_client.get_rest_apis()
        our_api = None
        
        for api in apis['items']:
            if 'opencv' in api['name'].lower():
                our_api = api
                break
        
        if not our_api:
            print(f"   ❌ API Gateway not found")
            return False
        
        api_id = our_api['id']
        print(f"   ✅ API Gateway found: {our_api['name']} ({api_id})")
        
        # Check resources
        resources = apigateway_client.get_resources(restApiId=api_id)
        resource_paths = [r['path'] for r in resources['items']]
        print(f"   Resources: {resource_paths}")
        
        # Check deployments
        deployments = apigateway_client.get_deployments(restApiId=api_id)
        if deployments['items']:
            print(f"   ✅ Deployments: {len(deployments['items'])}")
        else:
            print(f"   ⚠️ No deployments found")
        
        # Test API endpoint
        api_url = f"{LOCALSTACK_ENDPOINT}/restapis/{api_id}/test/_user_request_/health"
        
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                print(f"   ✅ API endpoint test successful")
            else:
                print(f"   ⚠️ API endpoint returned status: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️ API endpoint test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API Gateway verification failed: {e}")
        return False

def verify_iam_roles(iam_client):
    """Verify IAM roles exist."""
    print(f"🔐 Verifying IAM roles")
    
    try:
        role_name = f"{FUNCTION_NAME}-role"
        
        # Check if role exists
        role = iam_client.get_role(RoleName=role_name)
        print(f"   ✅ Role exists: {role_name}")
        
        # Check attached policies
        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
        for policy in attached_policies['AttachedPolicies']:
            print(f"   ✅ Attached policy: {policy['PolicyName']}")
        
        # Check inline policies
        inline_policies = iam_client.list_role_policies(RoleName=role_name)
        for policy_name in inline_policies['PolicyNames']:
            print(f"   ✅ Inline policy: {policy_name}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ IAM verification failed: {e}")
        return False

def main():
    """Main verification function."""
    print("🔍 Verifying LocalStack setup for OpenCV Image Quality Analyzer")
    print("=" * 70)
    
    all_good = True
    
    # Check LocalStack health
    if not verify_localstack_health():
        all_good = False
    
    print()
    
    # Create AWS clients
    try:
        clients = create_aws_clients()
    except Exception as e:
        print(f"❌ Failed to create AWS clients: {e}")
        return False
    
    # Verify each service
    verifications = [
        (verify_s3_bucket, clients['s3']),
        (verify_dynamodb_table, clients['dynamodb']),
        (verify_lambda_function, clients['lambda']),
        (verify_api_gateway, clients['apigateway']),
        (verify_iam_roles, clients['iam'])
    ]
    
    for verify_func, client in verifications:
        try:
            if not verify_func(client):
                all_good = False
        except Exception as e:
            print(f"❌ Verification error: {e}")
            all_good = False
        print()
    
    print("=" * 70)
    if all_good:
        print("🎉 All verifications passed! LocalStack setup is working correctly.")
        print("\n📋 Next steps:")
        print("1. Copy test images to test_images/ directory")
        print("2. Run tests: python -m pytest tests/ -v")
        print("3. Access API at: http://localhost:4566/restapis/{api_id}/test/_user_request_/")
    else:
        print("❌ Some verifications failed. Please check the setup and try again.")
        print("\n🔧 Troubleshooting:")
        print("1. Ensure LocalStack is running: docker-compose -f docker-compose.localstack.yml ps")
        print("2. Check LocalStack logs: docker logs localstack-opencv-test")
        print("3. Re-run setup: python setup_localstack.py")
    
    print("=" * 70)
    
    return all_good

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
