#!/bin/bash

# Financial Data Collector Docker Setup Script
# This script sets up the Docker environment for the Financial Data Collector

set -e

echo "🚀 Setting up Financial Data Collector Docker Environment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data logs cache config monitoring/grafana/dashboards monitoring/grafana/datasources nginx/ssl notebooks

# Set proper permissions
print_status "Setting directory permissions..."



# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cp env.example .env
    print_warning "Please update .env file with your configuration values"
fi

# Create SSL certificates for HTTPS (self-signed for development)
if [ ! -f nginx/ssl/cert.pem ]; then
    print_status "Creating self-signed SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    
    
fi

# Build Docker images
print_status "Building Docker images..."
docker-compose build

# Start services
print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U fdc_user -d fdc_db > /dev/null 2>&1; then
    print_status "✅ PostgreSQL is ready"
else
    print_error "❌ PostgreSQL is not ready"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_status "✅ Redis is ready"
else
    print_error "❌ Redis is not ready"
fi

# Check application
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "✅ Application is ready"
else
    print_warning "⚠️  Application may not be ready yet"
fi

# Display service URLs
echo ""
print_status "🎉 Setup complete! Services are available at:"
echo "  📊 Application: http://localhost:8000"
echo "  🗄️  PostgreSQL: localhost:5432"
echo "  🔴 Redis: localhost:6379"
echo "  📈 Prometheus: http://localhost:9090"
echo "  📊 Grafana: http://localhost:3000 (admin/admin)"
echo "  🐳 pgAdmin: http://localhost:5050 (admin@fdc.local/admin)"
echo "  📊 Redis Commander: http://localhost:8081"
echo "  📓 Jupyter: http://localhost:8888 (token: dev_token_123)"

echo ""
print_status "Useful commands:"
echo "  📋 View logs: docker-compose logs -f"
echo "  🔄 Restart: docker-compose restart"
echo "  🛑 Stop: docker-compose down"
echo "  🧹 Clean: docker-compose down -v --remove-orphans"

echo ""
print_warning "Remember to update your .env file with actual API keys and configuration values!"
