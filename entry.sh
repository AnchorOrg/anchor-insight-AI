#!/bin/bash
# ========================================
# Anchor Insight AI - Docker Setup Script
# ========================================
# Easy deployment with Docker containerization
# Supports both local development and production deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} Anchor Insight AI - Docker Setup${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_status "Docker and Docker Compose are available"
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f ".env.template" ]; then
            cp .env.template .env
            print_status ".env file created from template"
            print_warning "Please configure your .env file with appropriate values before running the application"
        else
            print_error ".env.template file not found!"
            exit 1
        fi
    else
        print_status ".env file found"
    fi
}

# Function to build Docker image
build_image() {
    print_status "Building Docker image..."
    docker build -t anchor-insight-ai .
    print_status "Docker image built successfully"
}

# Function to run in production mode
run_production() {
    print_header
    check_docker
    check_env_file
    
    print_status "Starting Anchor Insight AI in production mode..." # TODO: the env info should come from the .env -> APP_ENV 
    docker-compose up --build -d
    
    print_status "Application is starting up..."
    print_status "Waiting for health check..."
    
    # Wait for application to be ready
    sleep 10
    
    echo ""
    print_status "🚀 Anchor Insight AI is now running!"
    echo -e "   📍 API URL: ${GREEN}http://localhost:8000${NC}"
    echo -e "   📖 API Docs: ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "   🏥 Health Check: ${GREEN}http://localhost:8000/health${NC}"
    echo ""
    echo -e "To view logs: ${BLUE}docker-compose logs -f${NC}"
    echo -e "To stop: ${BLUE}docker-compose down${NC}"
}

# Function to run in development mode
run_development() {
    print_header
    check_docker
    check_env_file
    
    print_status "Starting Anchor Insight AI in development mode..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
}

# Function to stop the application
stop_application() {
    print_status "Stopping Anchor Insight AI..."
    docker-compose down
    print_status "Application stopped"
}

# Function to show logs
show_logs() {
    docker-compose logs -f
}

# Function to show status
show_status() {
    print_status "Checking application status..."
    docker-compose ps
    echo ""
    
    # Check if container is running and healthy
    if docker-compose ps | grep -q "Up"; then
        print_status "✅ Application is running"
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_status "✅ Health check passed"
        else
            print_warning "⚠️  Health check failed - application may still be starting"
        fi
    else
        print_warning "❌ Application is not running"
    fi
}

# Function to clean up Docker resources
cleanup() {
    print_status "Cleaning up Docker resources..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    print_status "Cleanup completed"
}

# Function to show help
show_help() {
    print_header
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start, run          Start the application in production mode (default)"
    echo "  dev, development    Start the application in development mode with live reload"
    echo "  stop               Stop the running application"
    echo "  logs               Show application logs"
    echo "  status             Show application status and health"
    echo "  build              Build Docker image only"
    echo "  cleanup            Stop application and clean up Docker resources"
    echo "  help, -h, --help   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Start in production mode"
    echo "  $0 start           # Start in production mode"
    echo "  $0 dev             # Start in development mode"
    echo "  $0 status          # Check if application is running"
    echo "  $0 logs            # View application logs"
    echo "  $0 stop            # Stop the application"
    echo ""
}

# Main script logic
case "${1:-start}" in
    "start"|"run"|"")
        run_production
        ;;
    "dev"|"development")
        run_development
        ;;
    "stop")
        stop_application
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "build")
        check_docker
        build_image
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

