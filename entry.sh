#!/bin/bash

# ========================================
# Anchor Insight AI - Project Setup Script
# ========================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="Anchor Insight AI"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_VERSION="3.13"
VENV_NAME="anchor-insight-venv"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    print_status "Checking Python version..."
    
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python ${PYTHON_VERSION} or later."
        exit 1
    fi
    
    CURRENT_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    print_status "Found Python version: $CURRENT_VERSION"
    
    # Extract major and minor version
    MAJOR=$(echo $CURRENT_VERSION | cut -d'.' -f1)
    MINOR=$(echo $CURRENT_VERSION | cut -d'.' -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
        print_error "Python 3.9+ is required. Current version: $CURRENT_VERSION"
        exit 1
    fi
    
    print_success "Python version is compatible"
}

# Function to install pipenv if not exists
install_pipenv() {
    if ! command_exists pipenv; then
        print_status "Installing pipenv..."
        
        # Check if we're on macOS and brew is available
        if [[ "$OSTYPE" == "darwin"* ]] && command_exists brew; then
            print_status "Using Homebrew to install pipenv..."
            brew install pipenv
        elif command_exists pipx; then
            print_status "Using pipx to install pipenv..."
            pipx install pipenv
        else
            # Try with --user flag first
            print_status "Attempting to install pipenv with --user flag..."
            if ! $PYTHON_CMD -m pip install --user pipenv; then
                print_warning "Failed to install with --user flag. Trying with --break-system-packages..."
                $PYTHON_CMD -m pip install --break-system-packages --user pipenv
            fi
        fi
        
        # Verify installation
        if command_exists pipenv; then
            print_success "Pipenv installed successfully"
        else
            print_error "Failed to install pipenv. Please install it manually:"
            print_error "  macOS: brew install pipenv"
            print_error "  Other: pip install --user pipenv"
            exit 1
        fi
    else
        print_success "Pipenv is already installed"
    fi
}

# Function to setup virtual environment and install dependencies
setup_environment() {
    print_status "Setting up virtual environment and installing dependencies..."
    
    cd "$PROJECT_DIR"
    
    # Remove existing Pipfile.lock if it has no dependencies
    if [ -f "Pipfile.lock" ]; then
        if grep -q '"default": {}' Pipfile.lock && grep -q '"develop": {}' Pipfile.lock; then
            print_status "Removing empty Pipfile.lock..."
            rm Pipfile.lock
        fi
    fi
    
    # Install dependencies
    print_status "Installing project dependencies..."
    pipenv install
    
    print_success "Virtual environment and dependencies installed"
}

# Function to create .env file
setup_env_file() {
    print_status "Setting up environment variables..."
    
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        cat > "$PROJECT_DIR/.env" << EOF
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Model Configuration
MODEL_ID=gpt-4o-mini

# File Processing Configuration
MAX_FILE_SIZE_MB=10

# Network Configuration
URL_TIMEOUT_SECONDS=30
MAX_RETRIES=3
RETRY_DELAY_SECONDS=2

# Service URLs (default values)
FOCUS_TIME_SERVICE_URL=http://localhost:8001
FOCUS_SCORE_SERVICE_URL=http://localhost:8002

# Logging Configuration
LOG_LEVEL=INFO
EOF
        print_success "Created .env file with default configuration"
        print_warning "Please update the OPENAI_API_KEY in .env file before running the services"
    else
        print_success ".env file already exists"
    fi
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    cd "$PROJECT_DIR"
    
    # Check if virtual environment is working
    if pipenv run python --version >/dev/null 2>&1; then
        VENV_PYTHON_VERSION=$(pipenv run python --version 2>&1)
        print_success "Virtual environment is working: $VENV_PYTHON_VERSION"
    else
        print_error "Virtual environment setup failed"
        exit 1
    fi
    
    # Check if required packages are installed
    print_status "Checking installed packages..."
    pipenv run python -c "import fastapi, uvicorn, openai, dotenv, pydantic_settings, httpx" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_success "All required packages are installed"
    else
        print_error "Some required packages are missing"
        exit 1
    fi
}

# Function to display service startup commands
show_startup_commands() {
    print_success "✅ Setup completed successfully!"
    echo
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}     SERVICE STARTUP COMMANDS         ${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo
    echo -e "${GREEN}1. Main API Gateway (Port 8080):${NC}"
    echo "   pipenv run python src/app/main.py"
    echo
    echo -e "${GREEN}2. Focus Score Service (Port 8002):${NC}"
    echo "   pipenv run python src/app/get_focus_score.py"
    echo
    echo -e "${GREEN}3. Focus Time Service (Port 8001):${NC}"
    echo "   pipenv run python src/app/get_focus_time.py"
    echo
    echo -e "${GREEN}4. All services in one command:${NC}"
    echo "   ./entry.sh --start-all"
    echo
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}           IMPORTANT NOTES             ${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo
    echo -e "${YELLOW}• Update your OpenAI API key in .env file${NC}"
    echo -e "${YELLOW}• API Documentation: http://localhost:8080/docs${NC}"
    echo -e "${YELLOW}• Health Check: http://localhost:8080/health${NC}"
    echo
}

# Function to start all services
start_all_services() {
    print_status "Starting all services..."
    
    # Check if .env file has API key configured
    if grep -q "your_openai_api_key_here" "$PROJECT_DIR/.env" 2>/dev/null; then
        print_error "Please configure your OPENAI_API_KEY in .env file first"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # Start services in background
    print_status "Starting Focus Score Service on port 8002..."
    pipenv run python src/app/get_focus_score.py &
    FOCUS_SCORE_PID=$!
    
    sleep 2
    
    print_status "Starting Focus Time Service on port 8001..."
    pipenv run python src/app/get_focus_time.py &
    FOCUS_TIME_PID=$!
    
    sleep 2
    
    print_status "Starting Main API Gateway on port 8080..."
    pipenv run python src/app/main.py &
    MAIN_API_PID=$!
    
    # Create PID file for cleanup
    echo "$FOCUS_SCORE_PID $FOCUS_TIME_PID $MAIN_API_PID" > "$PROJECT_DIR/.service_pids"
    
    print_success "All services started successfully!"
    print_status "Service PIDs saved to .service_pids"
    print_status "Use './entry.sh --stop-all' to stop all services"
    print_status "API Documentation: http://localhost:8080/docs"
    
    # Wait for all background processes
    wait
}

# Function to stop all services
stop_all_services() {
    print_status "Stopping all services..."
    
    if [ -f "$PROJECT_DIR/.service_pids" ]; then
        PIDS=$(cat "$PROJECT_DIR/.service_pids")
        for PID in $PIDS; do
            if kill -0 "$PID" 2>/dev/null; then
                print_status "Stopping service with PID: $PID"
                kill "$PID"
            fi
        done
        rm "$PROJECT_DIR/.service_pids"
        print_success "All services stopped"
    else
        print_warning "No service PID file found. Services may not be running."
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --start-all         Start all services"
    echo "  --stop-all          Stop all services"
    echo "  --verify            Verify installation only"
    echo "  --env-only          Setup .env file only"
    echo
    echo "Default behavior (no options): Complete project setup"
}

# Main execution logic
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}     ${PROJECT_NAME} Setup Script       ${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo
    
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --start-all)
            start_all_services
            exit 0
            ;;
        --stop-all)
            stop_all_services
            exit 0
            ;;
        --verify)
            verify_installation
            exit 0
            ;;
        --env-only)
            setup_env_file
            exit 0
            ;;
        "")
            # Default: Full setup
            check_python_version
            install_pipenv
            setup_environment
            setup_env_file
            verify_installation
            show_startup_commands
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
