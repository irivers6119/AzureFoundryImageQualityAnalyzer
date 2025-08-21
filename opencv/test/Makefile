# Makefile for OpenCV Image Quality Analyzer LocalStack Testing

# Variables
SHELL := /bin/bash
.DEFAULT_GOAL := help

# Project paths
PROJECT_ROOT := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
OPENCV_ROOT := $(shell dirname $(PROJECT_ROOT))
TEST_SCRIPT := $(PROJECT_ROOT)/run_tests.sh

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Help target
.PHONY: help
help: ## Show this help message
	@echo "$(CYAN)OpenCV Image Quality Analyzer - LocalStack Testing$(NC)"
	@echo "======================================================"
	@echo
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(CYAN)  %-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo
	@echo "$(GREEN)Example workflows:$(NC)"
	@echo "$(CYAN)  make setup test$(NC)                 # Setup and run all tests"
	@echo "$(CYAN)  make test-s3$(NC)                    # Run S3 tests only"
	@echo "$(CYAN)  make test-integration$(NC)           # Run integration tests"
	@echo "$(CYAN)  make test-coverage$(NC)              # Run tests with coverage"
	@echo "$(CYAN)  make clean start test-fast$(NC)      # Clean, start, and run fast tests"

# Environment setup
.PHONY: setup
setup: ## Set up the test environment and dependencies
	@echo "$(YELLOW)Setting up test environment...$(NC)"
	@$(TEST_SCRIPT) setup

.PHONY: check-deps
check-deps: ## Check if all dependencies are installed
	@echo "$(YELLOW)Checking dependencies...$(NC)"
	@command -v docker >/dev/null 2>&1 || (echo "$(RED)Docker not found$(NC)" && exit 1)
	@command -v docker-compose >/dev/null 2>&1 || (echo "$(RED)Docker Compose not found$(NC)" && exit 1)
	@command -v python3 >/dev/null 2>&1 || (echo "$(RED)Python 3 not found$(NC)" && exit 1)
	@echo "$(GREEN)All dependencies found$(NC)"

# LocalStack management
.PHONY: start
start: ## Start LocalStack services
	@echo "$(YELLOW)Starting LocalStack...$(NC)"
	@$(TEST_SCRIPT) start

.PHONY: stop
stop: ## Stop LocalStack services
	@echo "$(YELLOW)Stopping LocalStack...$(NC)"
	@$(TEST_SCRIPT) stop

.PHONY: restart
restart: stop start ## Restart LocalStack services
	@echo "$(GREEN)LocalStack restarted$(NC)"

.PHONY: status
status: ## Check LocalStack status
	@$(TEST_SCRIPT) status

.PHONY: logs
logs: ## Show LocalStack logs
	@$(TEST_SCRIPT) logs

# Test execution
.PHONY: test
test: ## Run all tests
	@echo "$(YELLOW)Running all tests...$(NC)"
	@$(TEST_SCRIPT) test

.PHONY: test-fast
test-fast: ## Run tests excluding slow and performance tests
	@echo "$(YELLOW)Running fast tests...$(NC)"
	@$(TEST_SCRIPT) test -m "not slow and not performance"

.PHONY: test-s3
test-s3: ## Run S3 operation tests
	@echo "$(YELLOW)Running S3 tests...$(NC)"
	@$(TEST_SCRIPT) test -m s3

.PHONY: test-lambda
test-lambda: ## Run Lambda function tests
	@echo "$(YELLOW)Running Lambda tests...$(NC)"
	@$(TEST_SCRIPT) test -m lambda_func

.PHONY: test-dynamodb
test-dynamodb: ## Run DynamoDB operation tests
	@echo "$(YELLOW)Running DynamoDB tests...$(NC)"
	@$(TEST_SCRIPT) test -m dynamodb

.PHONY: test-apigateway
test-apigateway: ## Run API Gateway tests
	@echo "$(YELLOW)Running API Gateway tests...$(NC)"
	@$(TEST_SCRIPT) test -m api_gateway

.PHONY: test-integration
test-integration: ## Run integration tests
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@$(TEST_SCRIPT) test -m integration

.PHONY: test-performance
test-performance: ## Run performance tests
	@echo "$(YELLOW)Running performance tests...$(NC)"
	@$(TEST_SCRIPT) test -m performance

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	@$(TEST_SCRIPT) test --coverage

.PHONY: test-html
test-html: ## Run tests with HTML coverage and test reports
	@echo "$(YELLOW)Running tests with HTML reports...$(NC)"
	@$(TEST_SCRIPT) test --coverage --html-report

.PHONY: test-parallel
test-parallel: ## Run tests in parallel (8 workers)
	@echo "$(YELLOW)Running tests in parallel...$(NC)"
	@$(TEST_SCRIPT) test --parallel 8

.PHONY: test-verbose
test-verbose: ## Run tests with verbose output
	@echo "$(YELLOW)Running tests with verbose output...$(NC)"
	@$(TEST_SCRIPT) test -v -s

.PHONY: test-keyword
test-keyword: ## Run tests matching keyword (use KEYWORD=pattern)
	@echo "$(YELLOW)Running tests matching keyword: $(KEYWORD)$(NC)"
	@$(TEST_SCRIPT) test -k "$(KEYWORD)"

# Development and debugging
.PHONY: shell
shell: ## Open interactive shell with test environment
	@echo "$(YELLOW)Opening test environment shell...$(NC)"
	@$(TEST_SCRIPT) shell

.PHONY: verify
verify: ## Verify LocalStack setup
	@echo "$(YELLOW)Verifying LocalStack setup...$(NC)"
	@cd $(PROJECT_ROOT) && python3 verify_setup.py

.PHONY: init-localstack
init-localstack: ## Initialize LocalStack resources
	@echo "$(YELLOW)Initializing LocalStack resources...$(NC)"
	@cd $(PROJECT_ROOT) && python3 setup_localstack.py

# Cleanup
.PHONY: clean
clean: ## Clean up test environment and artifacts
	@echo "$(YELLOW)Cleaning up test environment...$(NC)"
	@$(TEST_SCRIPT) clean

.PHONY: clean-cache
clean-cache: ## Clean Python and pytest cache files
	@echo "$(YELLOW)Cleaning cache files...$(NC)"
	@find $(PROJECT_ROOT) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find $(PROJECT_ROOT) -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -f $(PROJECT_ROOT)/.coverage 2>/dev/null || true

.PHONY: clean-reports
clean-reports: ## Clean test and coverage reports
	@echo "$(YELLOW)Cleaning test reports...$(NC)"
	@rm -rf $(PROJECT_ROOT)/htmlcov 2>/dev/null || true
	@rm -rf $(PROJECT_ROOT)/test-reports 2>/dev/null || true
	@rm -f $(PROJECT_ROOT)/test-results.xml 2>/dev/null || true

.PHONY: clean-all
clean-all: clean clean-cache clean-reports ## Clean everything
	@echo "$(GREEN)Complete cleanup finished$(NC)"

# Docker management
.PHONY: docker-build
docker-build: ## Build Docker images (if needed)
	@echo "$(YELLOW)Building Docker images...$(NC)"
	@cd $(PROJECT_ROOT) && docker-compose -f docker-compose.localstack.yml build

.PHONY: docker-pull
docker-pull: ## Pull latest LocalStack Docker images
	@echo "$(YELLOW)Pulling LocalStack images...$(NC)"
	@cd $(PROJECT_ROOT) && docker-compose -f docker-compose.localstack.yml pull

.PHONY: docker-clean
docker-clean: ## Clean Docker resources
	@echo "$(YELLOW)Cleaning Docker resources...$(NC)"
	@docker system prune -f
	@docker volume prune -f

# CI/CD helpers
.PHONY: ci-test
ci-test: setup test-coverage ## Run tests suitable for CI/CD
	@echo "$(GREEN)CI tests completed$(NC)"

.PHONY: ci-test-fast
ci-test-fast: setup test-fast ## Run fast tests for CI/CD
	@echo "$(GREEN)CI fast tests completed$(NC)"

# Development workflows
.PHONY: dev-setup
dev-setup: check-deps setup start verify ## Complete development setup
	@echo "$(GREEN)Development environment ready$(NC)"

.PHONY: dev-test
dev-test: start test-fast ## Quick development test cycle
	@echo "$(GREEN)Development tests completed$(NC)"

.PHONY: dev-integration
dev-integration: start test-integration ## Development integration test
	@echo "$(GREEN)Development integration tests completed$(NC)"

# Quality assurance
.PHONY: qa-full
qa-full: clean setup start test-coverage test-performance ## Full QA test suite
	@echo "$(GREEN)Full QA test suite completed$(NC)"

.PHONY: qa-smoke
qa-smoke: start test-fast verify ## Smoke test suite
	@echo "$(GREEN)Smoke tests completed$(NC)"

# Documentation helpers
.PHONY: show-markers
show-markers: ## Show available pytest markers
	@echo "$(CYAN)Available pytest markers:$(NC)"
	@grep -E "^\s+[a-z_]+:" $(PROJECT_ROOT)/pytest.ini | sed 's/://g' | sed 's/^    /  /'

.PHONY: show-config
show-config: ## Show current configuration
	@echo "$(CYAN)Current configuration:$(NC)"
	@echo "Project root: $(PROJECT_ROOT)"
	@echo "OpenCV root:  $(OPENCV_ROOT)"
	@echo "Test script:  $(TEST_SCRIPT)"
	@if [ -f "$(PROJECT_ROOT)/.env" ]; then \
		echo "$(CYAN)Environment variables:$(NC)"; \
		cat $(PROJECT_ROOT)/.env | grep -v "^#" | grep -v "^$$" | sed 's/^/  /'; \
	else \
		echo "$(YELLOW)No .env file found$(NC)"; \
	fi

# Special targets
.PHONY: all
all: dev-setup test-coverage ## Setup environment and run all tests with coverage
	@echo "$(GREEN)All tasks completed$(NC)"

# Pattern rules for custom test execution
test-%: ## Run specific test file (e.g., make test-s3_operations)
	@echo "$(YELLOW)Running test file: test_$*.py$(NC)"
	@$(TEST_SCRIPT) test tests/test_$*.py -v

# Prevent make from interpreting arguments as targets
%:
	@:

# Declare phony targets
.PHONY: help setup check-deps start stop restart status logs test test-fast test-s3 test-lambda test-dynamodb test-apigateway test-integration test-performance test-coverage test-html test-parallel test-verbose test-keyword shell verify init-localstack clean clean-cache clean-reports clean-all docker-build docker-pull docker-clean ci-test ci-test-fast dev-setup dev-test dev-integration qa-full qa-smoke show-markers show-config all
