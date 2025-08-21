# LocalStack Testing for OpenCV Image Quality Analyzer

This folder contains a complete LocalStack setup for testing the AWS implementation locally without deploying to actual AWS services.

## 🚀 **Quick Start**

### **Prerequisites**
- Docker Desktop installed and running
- Python 3.11+ 
- AWS CLI (optional, for easier testing)

### **1. Setup Environment**
```bash
# Copy environment configuration
cp .env.example .env

# Create test images directory
mkdir -p test_images
mkdir -p volume  # LocalStack data persistence

# Install testing dependencies
pip install -r test-requirements.txt
```

### **2. Start LocalStack**
```bash
# Start LocalStack with all AWS services
docker-compose -f docker-compose.localstack.yml up -d

# Check if services are running
curl http://localhost:4566/health

# Optional: Start with Web UI (requires LocalStack Pro)
docker-compose -f docker-compose.localstack.yml --profile web-ui up -d
```

### **3. Initialize AWS Resources**
```bash
# Run setup script to create S3, DynamoDB, Lambda, API Gateway
python setup_localstack.py

# Verify resources were created
python verify_setup.py
```

### **4. Run Tests**

#### Using the Test Runner Script (Recommended)
```bash
# Setup and run all tests
./run_tests.sh setup
./run_tests.sh test

# Run specific test categories  
./run_tests.sh test -m s3                    # S3 tests only
./run_tests.sh test -m "lambda_func"         # Lambda tests only
./run_tests.sh test -m "integration"         # Integration tests only

# Run with verbose output and coverage
./run_tests.sh test -v -s --coverage --html-report
```

#### Using Make Commands
```bash
# Setup and run all tests
make setup
make test

# Run specific test categories
make test-s3                                 # S3 tests only
make test-lambda                             # Lambda tests only
make test-integration                        # Integration tests only

# Development workflows
make dev-setup                               # Complete setup for development
make dev-test                                # Quick development test cycle
make test-coverage                           # Tests with coverage report

# Show all available targets
make help
```

#### Direct Pytest Commands
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_s3_operations.py -v
python -m pytest tests/test_lambda_functions.py -v
python -m pytest tests/test_integration.py -v
```

## 📁 **Directory Structure**

```
test/
├── docker-compose.localstack.yml   # LocalStack container setup
├── .env.example                    # Environment configuration template
├── test-requirements.txt           # Python testing dependencies
├── setup_localstack.py            # Initialize AWS resources in LocalStack
├── verify_setup.py                # Verify LocalStack setup
├── lambda/                         # Lambda function code for testing
│   ├── lambda_function.py          # Main Lambda function
│   ├── requirements.txt            # Lambda dependencies
│   └── opencv_analyzer.py          # OpenCV analysis module
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── test_s3_operations.py       # S3 bucket and upload tests
│   ├── test_lambda_functions.py    # Lambda function tests
│   ├── test_multipart_upload.py    # Multipart upload tests
│   ├── test_dynamodb.py            # DynamoDB operations tests
│   ├── test_api_gateway.py         # API Gateway tests
│   └── test_integration.py         # End-to-end integration tests
├── test_images/                    # Sample images for testing
├── utils/                          # Testing utilities
│   ├── __init__.py
│   ├── aws_client.py               # LocalStack AWS client wrapper
│   ├── test_data.py                # Test data generators
│   └── assertions.py               # Custom test assertions
└── volume/                         # LocalStack data persistence
```

## 🧪 **Available Tests**

### **S3 Operations**
- Bucket creation and configuration
- Standard file uploads
- Multipart uploads for large files
- Presigned URL generation
- Lifecycle policy validation

### **Lambda Functions**
- Function deployment and configuration
- Image analysis processing
- Error handling
- Memory and timeout limits
- Environment variable configuration

### **DynamoDB**
- Table creation and configuration
- Results storage and retrieval
- TTL (Time To Live) functionality
- Query and scan operations

### **API Gateway**
- REST API creation
- Endpoint configuration
- Lambda integration
- CORS configuration
- Request/response validation

### **Integration Tests**
- End-to-end image upload and analysis
- Multipart upload workflow
- Error scenarios and recovery
- Performance testing

## 🔧 **Configuration**

### **LocalStack Services**
The setup includes these AWS services:
- **S3**: Image storage and presigned URLs
- **Lambda**: Image analysis functions
- **DynamoDB**: Results storage
- **API Gateway**: REST API endpoints
- **CloudWatch**: Logging and monitoring
- **IAM**: Roles and permissions
- **STS**: Security token service

### **Environment Variables**
Key configuration options in `.env`:
- `DEBUG`: Enable/disable debug logging
- `PERSISTENCE`: Keep data between restarts
- `LAMBDA_EXECUTOR`: Lambda execution method
- `TEST_BUCKET_NAME`: S3 bucket for testing
- `TEST_TABLE_NAME`: DynamoDB table for testing

## 🚨 **Troubleshooting**

### **Common Issues**

#### **LocalStack won't start**
```bash
# Check Docker is running
docker ps

# Check ports aren't in use
lsof -i :4566

# Restart with fresh data
docker-compose -f docker-compose.localstack.yml down -v
docker-compose -f docker-compose.localstack.yml up -d
```

#### **Lambda functions fail to deploy**
```bash
# Check Lambda code directory exists
ls -la lambda/

# Verify Python dependencies
cd lambda && pip install -r requirements.txt

# Check LocalStack logs
docker logs localstack-opencv-test
```

#### **S3 operations fail**
```bash
# Verify S3 service is running
curl http://localhost:4566/health | jq .services.s3

# Test basic S3 operations
aws --endpoint-url=http://localhost:4566 s3 ls
```

#### **Tests fail with connection errors**
```bash
# Verify LocalStack is accessible
curl http://localhost:4566/health

# Check network connectivity
docker network ls | grep opencv-test

# Restart LocalStack
docker-compose -f docker-compose.localstack.yml restart
```

## 📊 **Performance Testing**

### **Load Testing**
```bash
# Run performance tests
python tests/performance/load_test.py

# Test multipart upload performance
python tests/performance/multipart_performance.py

# Memory usage testing
python tests/performance/memory_test.py
```

### **Metrics Collection**
LocalStack provides CloudWatch-compatible metrics for monitoring:
- Lambda execution duration
- S3 operation latency
- DynamoDB read/write capacity
- API Gateway request rates

## 🔍 **Debugging**

### **Enable Debug Logging**
```bash
# Set debug mode in .env
DEBUG=1

# Restart LocalStack
docker-compose -f docker-compose.localstack.yml restart localstack

# View logs
docker logs -f localstack-opencv-test
```

### **Access LocalStack Web UI** (Pro feature)
```bash
# Start with web UI profile
docker-compose -f docker-compose.localstack.yml --profile web-ui up -d

# Access at http://localhost:8080
```

### **Manual Testing**
```bash
# Test Lambda function directly
aws --endpoint-url=http://localhost:4566 lambda invoke \
    --function-name opencv-analyzer \
    --payload '{"test": "data"}' \
    response.json

# Test S3 operations
aws --endpoint-url=http://localhost:4566 s3 cp test_image.jpg s3://opencv-test-images/

# Test DynamoDB
aws --endpoint-url=http://localhost:4566 dynamodb scan \
    --table-name opencv-test-results
```

## 🔄 **CI/CD Integration**

### **GitHub Actions Example**
```yaml
name: LocalStack Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start LocalStack
        run: |
          cd opencv/test
          docker-compose -f docker-compose.localstack.yml up -d
          sleep 30  # Wait for services to start
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd opencv/test
          pip install -r test-requirements.txt
      - name: Initialize LocalStack
        run: |
          cd opencv/test
          python setup_localstack.py
      - name: Run tests
        run: |
          cd opencv/test
          python -m pytest tests/ -v
```

## 🚀 **Next Steps**

1. **Copy environment configuration**: `cp .env.example .env`
2. **Start LocalStack**: `docker-compose -f docker-compose.localstack.yml up -d`
3. **Initialize resources**: `python setup_localstack.py`
4. **Run tests**: `python -m pytest tests/ -v`
5. **Add your own test images** to `test_images/` directory
6. **Customize tests** for your specific use cases

This LocalStack setup provides a complete local AWS environment for developing and testing your OpenCV Image Quality Analyzer without incurring AWS costs! 🎯
