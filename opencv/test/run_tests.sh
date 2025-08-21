#!/bin/bash

# run_tests.sh - Test execution script for LocalStack testing environment
# 
# This script provides various test execution modes for the OpenCV Image Quality Analyzer
# LocalStack testing environment. It handles LocalStack startup, test execution,
# and cleanup operations.

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_ENV_FILE="$SCRIPT_DIR/.env"
LOCALSTACK_COMPOSE_FILE="$SCRIPT_DIR/docker-compose.localstack.yml"
REQUIREMENTS_FILE="$SCRIPT_DIR/test-requirements.txt"

# Default values
DEFAULT_LOCALSTACK_HOST="localhost"
DEFAULT_LOCALSTACK_PORT="4566"
DEFAULT_TEST_TIMEOUT="300"
DEFAULT_PARALLEL_WORKERS="4"

# Print usage information
usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  setup           Set up LocalStack environment and dependencies"
    echo "  start           Start LocalStack services"
    echo "  stop            Stop LocalStack services"
    echo "  test            Run tests (default command)"
    echo "  clean           Clean up test environment"
    echo "  logs            Show LocalStack logs"
    echo "  status          Check LocalStack status"
    echo "  shell           Open interactive shell with test environment"
    echo
    echo "Test Options:"
    echo "  -m, --marker MARKER     Run tests with specific marker (e.g., s3, lambda, integration)"
    echo "  -k, --keyword KEYWORD   Run tests matching keyword pattern"
    echo "  -v, --verbose          Run tests with verbose output"
    echo "  -s, --capture=no       Don't capture output (show print statements)"
    echo "  -x, --exitfirst        Stop on first failure"
    echo "  --parallel WORKERS     Run tests in parallel (default: $DEFAULT_PARALLEL_WORKERS)"
    echo "  --timeout SECONDS      Test timeout in seconds (default: $DEFAULT_TEST_TIMEOUT)"
    echo "  --no-localstack        Run tests without starting LocalStack"
    echo "  --coverage             Generate coverage report"
    echo "  --html-report          Generate HTML test report"
    echo
    echo "Environment Options:"
    echo "  --host HOST            LocalStack host (default: $DEFAULT_LOCALSTACK_HOST)"
    echo "  --port PORT            LocalStack port (default: $DEFAULT_LOCALSTACK_PORT)"
    echo "  --profile PROFILE      AWS profile to use"
    echo
    echo "Examples:"
    echo "  $0 setup                              # Set up test environment"
    echo "  $0 test -m s3                         # Run only S3 tests"
    echo "  $0 test -m \"s3 or lambda\" -v        # Run S3 or Lambda tests with verbose output"
    echo "  $0 test -k \"multipart\" --coverage   # Run multipart tests with coverage"
    echo "  $0 test --parallel 8 --timeout 600   # Run with 8 workers and 10min timeout"
    echo "  $0 test --no-localstack              # Run tests against external AWS/LocalStack"
}

# Print colored status message
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] ${message}${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "$BLUE" "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command_exists docker; then
        missing_deps+=("docker")
    fi
    
    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_status "$RED" "Missing required dependencies: ${missing_deps[*]}"
        echo "Please install the missing dependencies and try again."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        print_status "$RED" "Docker daemon is not running"
        echo "Please start Docker Desktop or Docker daemon and try again."
        exit 1
    fi
    
    print_status "$GREEN" "Prerequisites check passed"
}

# Setup test environment
setup_environment() {
    print_status "$BLUE" "Setting up test environment..."
    
    check_prerequisites
    
    # Create .env file if it doesn't exist
    if [ ! -f "$TEST_ENV_FILE" ]; then
        print_status "$YELLOW" "Creating .env file from template..."
        if [ -f "$SCRIPT_DIR/.env.example" ]; then
            cp "$SCRIPT_DIR/.env.example" "$TEST_ENV_FILE"
        else
            cat > "$TEST_ENV_FILE" << EOF
# LocalStack Configuration
LOCALSTACK_HOST=localhost
LOCALSTACK_PORT=4566
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test

# Test Configuration
TEST_BUCKET_NAME=image-quality-test-bucket
TEST_TABLE_NAME=image-analysis-results-test
TEST_FUNCTION_NAME=opencv-image-analyzer-test
TEST_API_NAME=opencv-image-analyzer-api-test

# Debug Options
DEBUG=0
PYTEST_VERBOSITY=1
EOF
        fi
        print_status "$GREEN" "Created .env file"
    fi
    
    # Install Python dependencies
    print_status "$BLUE" "Installing Python test dependencies..."
    if [ -f "$REQUIREMENTS_FILE" ]; then
        python3 -m pip install -r "$REQUIREMENTS_FILE" --quiet
        print_status "$GREEN" "Dependencies installed"
    else
        print_status "$YELLOW" "No test-requirements.txt found, skipping dependency installation"
    fi
    
    print_status "$GREEN" "Environment setup completed"
}

# Start LocalStack services
start_localstack() {
    print_status "$BLUE" "Starting LocalStack services..."
    
    if ! docker-compose -f "$LOCALSTACK_COMPOSE_FILE" ps | grep -q "Up"; then
        docker-compose -f "$LOCALSTACK_COMPOSE_FILE" up -d
        
        # Wait for LocalStack to be ready
        print_status "$BLUE" "Waiting for LocalStack to be ready..."
        local max_attempts=60
        local attempt=0
        
        while [ $attempt -lt $max_attempts ]; do
            if curl -s "http://${DEFAULT_LOCALSTACK_HOST}:${DEFAULT_LOCALSTACK_PORT}/health" >/dev/null 2>&1; then
                print_status "$GREEN" "LocalStack is ready"
                break
            fi
            
            attempt=$((attempt + 1))
            if [ $((attempt % 10)) -eq 0 ]; then
                print_status "$YELLOW" "Still waiting for LocalStack... (${attempt}/${max_attempts})"
            fi
            sleep 1
        done
        
        if [ $attempt -eq $max_attempts ]; then
            print_status "$RED" "LocalStack failed to start within timeout"
            exit 1
        fi
        
        # Initialize LocalStack resources
        print_status "$BLUE" "Initializing LocalStack resources..."
        python3 "$SCRIPT_DIR/setup_localstack.py"
        print_status "$GREEN" "LocalStack initialization completed"
        
    else
        print_status "$YELLOW" "LocalStack is already running"
    fi
}

# Stop LocalStack services
stop_localstack() {
    print_status "$BLUE" "Stopping LocalStack services..."
    docker-compose -f "$LOCALSTACK_COMPOSE_FILE" down
    print_status "$GREEN" "LocalStack services stopped"
}

# Show LocalStack logs
show_logs() {
    print_status "$BLUE" "Showing LocalStack logs..."
    docker-compose -f "$LOCALSTACK_COMPOSE_FILE" logs -f
}

# Check LocalStack status
check_status() {
    print_status "$BLUE" "Checking LocalStack status..."
    
    if docker-compose -f "$LOCALSTACK_COMPOSE_FILE" ps | grep -q "Up"; then
        print_status "$GREEN" "LocalStack is running"
        
        # Check health endpoint
        if curl -s "http://${DEFAULT_LOCALSTACK_HOST}:${DEFAULT_LOCALSTACK_PORT}/health" >/dev/null 2>&1; then
            print_status "$GREEN" "LocalStack health check passed"
            
            # Show service status
            echo
            echo "Service Status:"
            curl -s "http://${DEFAULT_LOCALSTACK_HOST}:${DEFAULT_LOCALSTACK_PORT}/health" | python3 -m json.tool 2>/dev/null || echo "Could not retrieve service status"
        else
            print_status "$YELLOW" "LocalStack is running but health check failed"
        fi
        
        # Show running containers
        echo
        echo "Running Containers:"
        docker-compose -f "$LOCALSTACK_COMPOSE_FILE" ps
        
    else
        print_status "$RED" "LocalStack is not running"
        exit 1
    fi
}

# Clean up test environment
clean_environment() {
    print_status "$BLUE" "Cleaning up test environment..."
    
    # Stop LocalStack
    stop_localstack
    
    # Remove test artifacts
    rm -rf "$SCRIPT_DIR/.pytest_cache" 2>/dev/null || true
    rm -rf "$SCRIPT_DIR/__pycache__" 2>/dev/null || true
    rm -rf "$SCRIPT_DIR/tests/__pycache__" 2>/dev/null || true
    rm -f "$SCRIPT_DIR/.coverage" 2>/dev/null || true
    rm -rf "$SCRIPT_DIR/htmlcov" 2>/dev/null || true
    rm -rf "$SCRIPT_DIR/test-reports" 2>/dev/null || true
    
    print_status "$GREEN" "Cleanup completed"
}

# Open interactive shell
open_shell() {
    print_status "$BLUE" "Opening interactive shell with test environment..."
    
    # Source environment variables
    if [ -f "$TEST_ENV_FILE" ]; then
        set -a
        source "$TEST_ENV_FILE"
        set +a
    fi
    
    echo "Test environment variables loaded."
    echo "LocalStack endpoint: http://${LOCALSTACK_HOST:-$DEFAULT_LOCALSTACK_HOST}:${LOCALSTACK_PORT:-$DEFAULT_LOCALSTACK_PORT}"
    echo "Available test modules: s3_operations, lambda_functions, dynamodb_operations, api_gateway, integration"
    echo
    echo "Example commands:"
    echo "  python3 -m pytest tests/test_s3_operations.py -v"
    echo "  python3 setup_localstack.py"
    echo "  python3 verify_setup.py"
    echo
    
    # Start new shell with environment
    exec "$SHELL"
}

# Run tests
run_tests() {
    local pytest_args=()
    local use_localstack=true
    local generate_coverage=false
    local generate_html_report=false
    local parallel_workers="$DEFAULT_PARALLEL_WORKERS"
    local test_timeout="$DEFAULT_TEST_TIMEOUT"
    
    # Parse test options
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--marker)
                pytest_args+=("-m" "$2")
                shift 2
                ;;
            -k|--keyword)
                pytest_args+=("-k" "$2")
                shift 2
                ;;
            -v|--verbose)
                pytest_args+=("-v")
                shift
                ;;
            -s|--capture=no)
                pytest_args+=("-s")
                shift
                ;;
            -x|--exitfirst)
                pytest_args+=("-x")
                shift
                ;;
            --parallel)
                parallel_workers="$2"
                shift 2
                ;;
            --timeout)
                test_timeout="$2"
                shift 2
                ;;
            --no-localstack)
                use_localstack=false
                shift
                ;;
            --coverage)
                generate_coverage=true
                shift
                ;;
            --html-report)
                generate_html_report=true
                shift
                ;;
            --host)
                DEFAULT_LOCALSTACK_HOST="$2"
                shift 2
                ;;
            --port)
                DEFAULT_LOCALSTACK_PORT="$2"
                shift 2
                ;;
            --profile)
                export AWS_PROFILE="$2"
                shift 2
                ;;
            *)
                pytest_args+=("$1")
                shift
                ;;
        esac
    done
    
    # Setup environment if needed
    if [ ! -f "$TEST_ENV_FILE" ]; then
        setup_environment
    fi
    
    # Start LocalStack if requested
    if [ "$use_localstack" = true ]; then
        start_localstack
    fi
    
    # Source environment variables
    if [ -f "$TEST_ENV_FILE" ]; then
        set -a
        source "$TEST_ENV_FILE"
        set +a
    fi
    
    # Update host/port if provided
    export LOCALSTACK_HOST="$DEFAULT_LOCALSTACK_HOST"
    export LOCALSTACK_PORT="$DEFAULT_LOCALSTACK_PORT"
    
    print_status "$BLUE" "Running tests..."
    
    # Build pytest command
    local pytest_cmd=(python3 -m pytest)
    
    # Add test directory
    pytest_cmd+=("$SCRIPT_DIR/tests")
    
    # Add parallel execution if requested
    if [ "$parallel_workers" -gt 1 ]; then
        pytest_cmd+=("-n" "$parallel_workers")
    fi
    
    # Add timeout
    pytest_cmd+=("--timeout=$test_timeout")
    
    # Add coverage if requested
    if [ "$generate_coverage" = true ]; then
        pytest_cmd+=("--cov=$SCRIPT_DIR" "--cov-report=term-missing")
        if [ "$generate_html_report" = true ]; then
            pytest_cmd+=("--cov-report=html:$SCRIPT_DIR/htmlcov")
        fi
    fi
    
    # Add HTML report if requested
    if [ "$generate_html_report" = true ]; then
        mkdir -p "$SCRIPT_DIR/test-reports"
        pytest_cmd+=("--html=$SCRIPT_DIR/test-reports/report.html" "--self-contained-html")
    fi
    
    # Add JUnit XML for CI
    pytest_cmd+=("--junit-xml=$SCRIPT_DIR/test-results.xml")
    
    # Add user arguments
    pytest_cmd+=("${pytest_args[@]}")
    
    print_status "$BLUE" "Executing: ${pytest_cmd[*]}"
    
    # Run tests
    if "${pytest_cmd[@]}"; then
        print_status "$GREEN" "Tests completed successfully"
        
        if [ "$generate_coverage" = true ]; then
            echo
            print_status "$BLUE" "Coverage report generated"
            if [ "$generate_html_report" = true ]; then
                print_status "$BLUE" "HTML coverage report: $SCRIPT_DIR/htmlcov/index.html"
            fi
        fi
        
        if [ "$generate_html_report" = true ]; then
            print_status "$BLUE" "HTML test report: $SCRIPT_DIR/test-reports/report.html"
        fi
        
    else
        print_status "$RED" "Tests failed"
        exit 1
    fi
}

# Main script logic
main() {
    local command="${1:-test}"
    shift || true
    
    case "$command" in
        setup)
            setup_environment
            ;;
        start)
            start_localstack
            ;;
        stop)
            stop_localstack
            ;;
        test)
            run_tests "$@"
            ;;
        clean)
            clean_environment
            ;;
        logs)
            show_logs
            ;;
        status)
            check_status
            ;;
        shell)
            open_shell
            ;;
        --help|-h|help)
            usage
            ;;
        *)
            echo "Unknown command: $command"
            echo
            usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
