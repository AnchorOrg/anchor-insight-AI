#!/bin/bash

# This script sets up the Anchor-Insight-AI project dependencies.
# Assumes Python 3.12+ and pipenv are already installed.

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
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

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macOS"
    elif [[ -f /proc/version ]] && grep -qi microsoft /proc/version; then
        OS="WSL"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="Linux"
    else
        OS="Unknown"
    fi
    print_info "Detected OS: $OS"
}

# Quick environment check
check_environment() {
    print_info "Checking environment..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        print_success "Python $PYTHON_VERSION found"
        
        # Update Pipfile if using Python 3.12
        if [[ "$PYTHON_VERSION" == "3.12" ]] && [[ -f "Pipfile" ]]; then
            if grep -q 'python_version = "3.13"' Pipfile; then
                print_info "Updating Pipfile to match Python 3.12..."
                sed -i 's/python_version = "3.13"/python_version = "3.12"/' Pipfile
                print_success "Pipfile updated"
            fi
        fi
    else
        print_error "Python 3 not found. Please install Python 3.12+"
        exit 1
    fi
    
    # Check pipenv
    if command -v pipenv &> /dev/null; then
        print_success "pipenv found: $(pipenv --version)"
    else
        print_error "pipenv not found. Please install pipenv first:"
        print_info "  sudo apt install pipenv  # or"
        print_info "  pip install --user pipenv"
        exit 1
    fi
    
    # Check if Pipfile exists
    if [[ ! -f "Pipfile" ]]; then
        print_error "Pipfile not found in current directory."
        print_info "Please run this script from the project root directory."
        exit 1
    fi
}

# Install system dependencies for packages like opencv-python
install_system_dependencies() {
    if [[ "$OS" == "WSL" ]] || [[ "$OS" == "Linux" ]]; then
        print_info "Checking system dependencies for OpenCV and other packages..."
        
        # Get Ubuntu version
        UBUNTU_VERSION=$(lsb_release -rs 2>/dev/null || echo "unknown")
        print_info "Ubuntu version: $UBUNTU_VERSION"
        
        # Base required packages (common across versions)
        required_packages=(
            "libglib2.0-0"
            "libsm6"
            "libxext6"
            "libxrender-dev"
            "libgomp1"
            "libglib2.0-dev"
            "libgtk-3-0"
            "libgstreamer1.0-0"
            "libgstreamer-plugins-base1.0-0"
        )
        
        # Add version-specific packages
        if [[ "$UBUNTU_VERSION" == "24.04" ]] || [[ "$UBUNTU_VERSION" > "24" ]]; then
            # Ubuntu 24.04+ uses libgl1 instead of libgl1-mesa-glx
            required_packages+=("libgl1")
            required_packages+=("libgl1-mesa-dri")
        else
            # Older Ubuntu versions
            required_packages+=("libgl1-mesa-glx")
        fi
        
        packages_to_install=""
        missing_packages=()
        
        for pkg in "${required_packages[@]}"; do
            if ! dpkg -l 2>/dev/null | grep -q "^ii  $pkg"; then
                # Check if package exists in repository
                if apt-cache show "$pkg" &>/dev/null; then
                    packages_to_install="$packages_to_install $pkg"
                    missing_packages+=("$pkg")
                else
                    print_warning "Package $pkg not found in repository, skipping..."
                fi
            fi
        done
        
        if [[ -n "$packages_to_install" ]]; then
            print_info "Installing missing system dependencies: ${missing_packages[*]}"
            sudo apt-get update
            if sudo apt-get install -y $packages_to_install; then
                print_success "System dependencies installed"
            else
                print_warning "Some packages failed to install, but continuing..."
            fi
        else
            print_success "All system dependencies are already installed"
        fi
        
        # Install additional Python dev packages if needed
        if ! dpkg -l | grep -q "python3-dev"; then
            print_info "Installing Python development packages..."
            sudo apt-get install -y python3-dev python3-distutils || true
        fi
        
    elif [[ "$OS" == "macOS" ]]; then
        # macOS usually has required dependencies
        if ! xcode-select -p &> /dev/null; then
            print_warning "Xcode Command Line Tools not installed."
            print_info "Installing Xcode Command Line Tools..."
            xcode-select --install
        else
            print_success "Xcode Command Line Tools found"
        fi
    fi
}

# Install project dependencies
install_dependencies() {
    print_info "Installing project dependencies..."
    
    # Set environment variables for better compatibility
    export PIPENV_VENV_IN_PROJECT=1  # Create .venv in project directory
    export PIPENV_TIMEOUT=600        # Timeout for large packages
    export PIPENV_MAX_SUBPROCESS=10  # Limit concurrent operations
    
    # Check if Pipfile.lock exists
    if [[ -f "Pipfile.lock" ]]; then
        print_info "Found Pipfile.lock - installing exact dependency versions..."
        INSTALL_CMD="pipenv install --dev"
    else
        print_info "No Pipfile.lock found - will generate it during installation..."
        INSTALL_CMD="pipenv install --dev"
    fi
    
    print_info "This may take several minutes for large packages (torch, ultralytics, opencv)..."
    
    # Try installation
    if $INSTALL_CMD; then
        print_success "✅ All dependencies installed successfully!"
    else
        print_warning "Installation encountered issues. Trying fallback method..."
        # Fallback: install without lock file verification
        if pipenv install --skip-lock --dev; then
            print_success "✅ Dependencies installed (without lock file)"
        else
            print_error "Installation failed. Please check the error messages above."
            exit 1
        fi
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying key packages..."
    
    pipenv run python -c "
import sys
print(f'Python: {sys.version}')
packages = {
    'fastapi': 'FastAPI',
    'cv2': 'OpenCV',
    'numpy': 'NumPy',
    'torch': 'PyTorch',
    'ultralytics': 'Ultralytics YOLO',
    'openai': 'OpenAI',
    'PIL': 'Pillow'
}
for module, name in packages.items():
    try:
        __import__(module)
        print(f'✓ {name} installed')
    except ImportError:
        print(f'✗ {name} not found')
" || print_warning "Some packages may not be properly installed"
}

# Show usage instructions
show_usage() {
    echo ""
    echo "========================================="
    print_success "🎉 Setup Complete!"
    echo "========================================="
    echo ""
    echo "📦 Installed packages:"
    echo "  • FastAPI - Web framework"
    echo "  • Uvicorn - ASGI server"
    echo "  • OpenAI - AI integration"
    echo "  • OpenCV & Pillow - Image processing"
    echo "  • NumPy - Numerical computing"
    echo "  • Ultralytics - YOLO models"
    echo "  • PyTorch - Deep learning"
    echo ""
    echo "🚀 To run the application:"
    echo ""
    echo "  Option 1 - Using pipenv run:"
    echo "     ${GREEN}pipenv run uvicorn src.app.main:app --host 0.0.0.0 --port 7003 --reload${NC}"
    echo ""
    echo "  Option 2 - Activate shell first:"
    echo "     ${GREEN}pipenv shell${NC}"
    echo "     ${GREEN}uvicorn src.app.main:app --host 0.0.0.0 --port 7003 --reload${NC}"
    echo ""
    echo "📝 API Documentation:"
    echo "  • Swagger UI: http://localhost:7003/docs"
    echo "  • ReDoc: http://localhost:7003/redoc"
    echo ""
    if [[ "$OS" == "WSL" ]]; then
        print_info "WSL: Access from Windows browser at http://localhost:7003"
    fi
    
    # Show virtual environment location
    VENV_PATH=$(pipenv --venv 2>/dev/null || echo "")
    if [[ -n "$VENV_PATH" ]]; then
        print_info "Virtual environment: $VENV_PATH"
    elif [[ -d ".venv" ]]; then
        print_info "Virtual environment: $(pwd)/.venv"
    fi
    
    echo "========================================="
}

# Main execution
main() {
    echo "========================================="
    echo "  Anchor-Insight-AI Setup"
    echo "========================================="
    echo ""
    
    # Step 1: Detect OS
    detect_os
    
    # Step 2: Check environment
    check_environment
    
    # Step 3: Install system dependencies
    install_system_dependencies
    
    # Step 4: Install Python dependencies
    install_dependencies
    
    # Step 5: Verify installation
    verify_installation
    
    # Step 6: Show usage instructions
    show_usage
}

# Run main function
main