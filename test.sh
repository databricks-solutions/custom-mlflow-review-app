#!/bin/bash
# Test runner script for the MLflow Review App

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[TEST] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[PASS] $1${NC}"
}

log_error() {
    echo -e "${RED}[FAIL] $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

# Configuration
PYTHON_CMD="uv run python"
PYTEST_CMD="uv run pytest"
TEST_TIMEOUT=300 # 5 minutes

# Test categories
run_backend_tests=true
run_integration_tests=false
run_frontend_tests=false
run_quality_checks=true
verbose=false

# Parse command line arguments
while (( "$#" )); do
  case "$1" in
    --backend)
      run_backend_tests=true
      run_integration_tests=false
      run_frontend_tests=false
      run_quality_checks=false
      shift
      ;;
    --integration)
      run_backend_tests=false
      run_integration_tests=true
      run_frontend_tests=false
      run_quality_checks=false
      shift
      ;;
    --frontend)
      run_backend_tests=false
      run_integration_tests=false
      run_frontend_tests=true
      run_quality_checks=false
      shift
      ;;
    --quality)
      run_backend_tests=false
      run_integration_tests=false
      run_frontend_tests=false
      run_quality_checks=true
      shift
      ;;
    --all)
      run_backend_tests=true
      run_integration_tests=true
      run_frontend_tests=true
      run_quality_checks=true
      shift
      ;;
    -v|--verbose)
      verbose=true
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --backend         Run only backend pytest tests"
      echo "  --integration     Run only integration tests"
      echo "  --frontend        Run only frontend tests"
      echo "  --quality         Run only code quality checks"
      echo "  --all             Run all test categories"
      echo "  -v, --verbose     Verbose output"
      echo "  -h, --help        Show this help message"
      echo ""
      echo "Default: runs backend tests and quality checks"
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Set pytest options
PYTEST_OPTS="--tb=short --maxfail=5"
if [ "$verbose" = true ]; then
    PYTEST_OPTS="$PYTEST_OPTS -v"
fi

log "Starting MLflow Review App test suite..."
log "Configuration:"
log "  Backend tests: $run_backend_tests"
log "  Integration tests: $run_integration_tests"
log "  Frontend tests: $run_frontend_tests"
log "  Quality checks: $run_quality_checks"
log "  Verbose: $verbose"

# Track test results
total_tests=0
passed_tests=0
failed_tests=0

# Function to run a test category
run_test_category() {
    local category="$1"
    local command="$2"
    local description="$3"
    
    log "Running $description..."
    
    if eval timeout $TEST_TIMEOUT $command; then
        log_success "$description completed successfully"
        ((passed_tests++))
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then
            log_error "$description timed out after ${TEST_TIMEOUT}s"
        else
            log_error "$description failed with exit code $exit_code"
        fi
        ((failed_tests++))
    fi
    
    ((total_tests++))
}

# Backend Tests
if [ "$run_backend_tests" = true ]; then
    log "=== Backend Tests ==="
    
    # Check if pytest is available
    if ! command -v uv >/dev/null 2>&1; then
        log_error "uv is not installed. Please run ./setup.sh first."
        exit 1
    fi
    
    # Create test database/setup if needed
    log "Setting up test environment..."
    
    # Run unit tests - look in tests directory first, then for *_test.py files
    if [ -d "tests" ]; then
        run_test_category "backend" "$PYTEST_CMD $PYTEST_OPTS tests/" "Backend unit tests"
    else
        test_files=$(find . -name "*_test.py" -not -path "./client/*" -not -path "./.venv/*" -not -path "./venv/*" -not -path "./integration_tests/*")
        
        if [ -n "$test_files" ]; then
            run_test_category "backend" "$PYTEST_CMD $PYTEST_OPTS $test_files" "Backend unit tests"
        else
            log_warning "No tests directory or *_test.py files found. Skipping backend tests."
        fi
    fi
fi

# Integration Tests
if [ "$run_integration_tests" = true ]; then
    log "=== Integration Tests ==="
    
    # Check if development server is running
    if ! curl -s http://localhost:8000/health > /dev/null; then
        log_warning "Development server not running on localhost:8000"
        log "Starting development server for integration tests..."
        
        nohup ./watch.sh > /tmp/test-server.log 2>&1 &
        TEST_SERVER_PID=$!
        
        # Wait for server to start
        for i in {1..30}; do
            if curl -s http://localhost:8000/health > /dev/null; then
                log_success "Development server started"
                break
            fi
            sleep 1
        done
        
        if ! curl -s http://localhost:8000/health > /dev/null; then
            log_error "Failed to start development server"
            kill $TEST_SERVER_PID 2>/dev/null || true
            exit 1
        fi
    fi
    
    # Run integration tests - look in integration_tests directory
    if [ -d "integration_tests" ]; then
        run_test_category "integration" "$PYTEST_CMD $PYTEST_OPTS integration_tests/" "Integration tests"
    else
        log_warning "No integration_tests directory found. Skipping integration tests."
    fi
    
    # Cleanup test server if we started it
    if [ ! -z "$TEST_SERVER_PID" ]; then
        kill $TEST_SERVER_PID 2>/dev/null || true
        log "Stopped test development server"
    fi
fi

# Frontend Tests
if [ "$run_frontend_tests" = true ]; then
    log "=== Frontend Tests ==="
    
    cd client
    
    # Check if bun is available
    if ! command -v bun >/dev/null 2>&1; then
        log_error "bun is not installed. Please run ./setup.sh first."
        exit 1
    fi
    
    # Run frontend tests
    if [ -f "package.json" ] && grep -q "test" package.json; then
        run_test_category "frontend" "bun test" "Frontend tests"
    else
        log_warning "No frontend tests configured. Skipping frontend tests."
    fi
    
    cd ..
fi

# Code Quality Checks
if [ "$run_quality_checks" = true ]; then
    log "=== Code Quality Checks ==="
    
    # Python code quality
    log "Checking Python code quality..."
    
    # Ruff linting
    if command -v uv >/dev/null 2>&1; then
        run_test_category "ruff" "uv run ruff check server/ tools/ --output-format=github" "Python linting (ruff)"
        
        # Python formatting check
        run_test_category "ruff-format" "uv run ruff format --check server/ tools/" "Python formatting check"
        
        # Type checking (if available)
        if command -v uv run mypy >/dev/null 2>&1; then
            run_test_category "mypy" "uv run mypy server/ --ignore-missing-imports" "Python type checking"
        fi
    else
        log_warning "uv not available. Skipping Python quality checks."
    fi
    
    # TypeScript code quality (if frontend exists)
    if [ -d "client" ]; then
        log "Checking TypeScript code quality..."
        
        cd client
        
        if [ -f "package.json" ]; then
            # TypeScript checking
            if grep -q "type-check" package.json; then
                run_test_category "tsc" "bun run type-check" "TypeScript type checking"
            fi
            
            # Linting
            if grep -q "lint" package.json; then
                run_test_category "eslint" "bun run lint" "TypeScript linting"
            fi
            
            # Formatting check
            if grep -q "format:check" package.json; then
                run_test_category "prettier" "bun run format:check" "TypeScript formatting check"
            fi
        fi
        
        cd ..
    fi
fi

# Test Summary
log "=== Test Summary ==="
log "Total test categories: $total_tests"
log_success "Passed: $passed_tests"

if [ $failed_tests -gt 0 ]; then
    log_error "Failed: $failed_tests"
    
    echo ""
    log_error "Some tests failed. Please review the output above."
    log "Common fixes:"
    log "  - For linting issues: run ./fix.sh"
    log "  - For failing tests: check test logs and fix implementation"
    log "  - For missing dependencies: run ./setup.sh"
    
    exit 1
else
    log_success "All tests passed! 🎉"
    
    if [ $total_tests -eq 0 ]; then
        log_warning "No tests were run. Consider adding tests to improve code quality."
    fi
fi

log "Test suite completed successfully."