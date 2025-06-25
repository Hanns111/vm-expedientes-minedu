#!/bin/bash

# AI Search Platform Deployment Script
# Usage: ./deploy.sh [environment]
# Environments: development, production

set -e

ENVIRONMENT=${1:-development}
PROJECT_NAME="ai-search-platform"

echo "🚀 Starting deployment for $PROJECT_NAME in $ENVIRONMENT mode..."

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Node.js (for frontend)
    if ! command -v node &> /dev/null; then
        log_warning "Node.js is not installed. Frontend deployment will be skipped."
    fi
    
    log_success "Prerequisites check completed"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment for $ENVIRONMENT..."
    
    # Copy appropriate environment file
    if [ "$ENVIRONMENT" = "production" ]; then
        if [ ! -f ".env" ]; then
            cp .env.production .env
            log_warning "Copied .env.production to .env. Please update with your actual values."
        fi
    else
        if [ ! -f ".env" ]; then
            echo "ENVIRONMENT=development" > .env
            echo "HOST=0.0.0.0" >> .env
            echo "PORT=8000" >> .env
        fi
    fi
    
    # Create necessary directories
    mkdir -p data/vectorstores data/temp logs
    
    log_success "Environment setup completed"
}

# Build and deploy backend
deploy_backend() {
    log_info "Deploying backend..."
    
    # Build and start services
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose --profile production up -d --build
    else
        docker-compose up -d --build backend
    fi
    
    # Wait for backend to be healthy
    log_info "Waiting for backend to be ready..."
    timeout=60
    counter=0
    
    while [ $counter -lt $timeout ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Backend is healthy!"
            break
        fi
        
        sleep 2
        counter=$((counter + 2))
        
        if [ $counter -ge $timeout ]; then
            log_error "Backend failed to start within $timeout seconds"
            docker-compose logs backend
            exit 1
        fi
    done
    
    log_success "Backend deployment completed"
}

# Deploy frontend
deploy_frontend() {
    if ! command -v node &> /dev/null; then
        log_warning "Skipping frontend deployment - Node.js not available"
        return
    fi
    
    log_info "Deploying frontend..."
    
    cd frontend-new
    
    # Install dependencies
    npm install
    
    # Build frontend
    if [ "$ENVIRONMENT" = "production" ]; then
        npm run build
        log_info "Frontend built for production"
        log_info "Deploy to Vercel:"
        log_info "1. Push code to GitHub"
        log_info "2. Connect repository to Vercel"
        log_info "3. Set NEXT_PUBLIC_API_URL to your backend URL"
        log_info "4. Deploy"
    else
        log_info "Frontend ready for development"
        log_info "Run: cd frontend-new && npm run dev"
    fi
    
    cd ..
    log_success "Frontend deployment completed"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Backend health check
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "Backend health check passed"
    else
        log_error "Backend health check failed"
        return 1
    fi
    
    # Check vectorstores
    if [ -f "data/vectorstores/bm25.pkl" ] && [ -f "data/vectorstores/tfidf.pkl" ] && [ -f "data/vectorstores/transformers.pkl" ]; then
        log_success "Vectorstores are available"
    else
        log_warning "Some vectorstores are missing. Run: python src/data_pipeline/generate_vectorstores.py"
    fi
    
    log_success "Health checks completed"
}

# Show deployment summary
show_summary() {
    log_success "🎉 Deployment completed successfully!"
    echo
    echo "📊 Deployment Summary:"
    echo "├── Environment: $ENVIRONMENT"
    echo "├── Backend: http://localhost:8000"
    echo "├── API Docs: http://localhost:8000/docs"
    echo "├── Health: http://localhost:8000/health"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        echo "└── Frontend: Deploy to Vercel (see instructions above)"
    else
        echo "└── Frontend: cd frontend-new && npm run dev"
    fi
    
    echo
    echo "🔧 Useful Commands:"
    echo "├── View logs: docker-compose logs -f backend"
    echo "├── Stop services: docker-compose down"
    echo "├── Restart: docker-compose restart backend"
    echo "└── Clean rebuild: docker-compose down && docker-compose up -d --build"
    
    if [ -f "test_integration.py" ]; then
        echo
        echo "🧪 Test Integration:"
        echo "└── Run: python test_integration.py"
    fi
}

# Main deployment flow
main() {
    echo "🔍 AI Search Platform Deployment"
    echo "================================"
    
    check_prerequisites
    setup_environment
    deploy_backend
    
    if [ "$ENVIRONMENT" != "production" ]; then
        deploy_frontend
    fi
    
    sleep 5  # Give services time to stabilize
    run_health_checks
    show_summary
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main

log_success "Deployment script completed!"