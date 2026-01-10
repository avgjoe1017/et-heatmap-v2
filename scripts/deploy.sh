#!/bin/bash
# Production deployment script for ET Heatmap

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.production"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

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

    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file not found: $ENV_FILE"
        log_info "Please create .env.production with required variables."
        exit 1
    fi

    log_info "✓ All prerequisites met"
}

backup_database() {
    log_info "Creating database backup before deployment..."

    if docker-compose -f docker-compose.prod.yml ps | grep -q "et-heatmap-postgres-prod"; then
        docker-compose -f docker-compose.prod.yml exec -T postgres \
            pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" > "backups/pre-deploy-$(date +%Y%m%d_%H%M%S).sql"
        log_info "✓ Database backup created"
    else
        log_warn "Database container not running, skipping backup"
    fi
}

pull_images() {
    log_info "Pulling latest images..."
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml pull
    log_info "✓ Images pulled"
}

build_images() {
    log_info "Building Docker images..."
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml build --no-cache
    log_info "✓ Images built"
}

stop_services() {
    log_info "Stopping running services..."
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml down
    log_info "✓ Services stopped"
}

start_services() {
    log_info "Starting services..."
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.prod.yml up -d
    log_info "✓ Services started"
}

run_migrations() {
    log_info "Running database migrations..."
    cd "$PROJECT_DIR"

    # Wait for database to be ready
    sleep 10

    # Run migrations
    docker-compose -f docker-compose.prod.yml exec -T backend \
        alembic upgrade head

    log_info "✓ Migrations completed"
}

health_check() {
    log_info "Running health checks..."
    cd "$PROJECT_DIR"

    # Wait for services to start
    sleep 15

    # Check backend health
    if docker-compose -f docker-compose.prod.yml exec -T backend \
        curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_info "✓ Backend is healthy"
    else
        log_error "Backend health check failed"
        return 1
    fi

    # Check frontend via nginx
    if curl -f http://localhost/health > /dev/null 2>&1; then
        log_info "✓ Frontend is healthy"
    else
        log_error "Frontend health check failed"
        return 1
    fi

    log_info "✓ All health checks passed"
}

cleanup_old_images() {
    log_info "Cleaning up old Docker images..."
    docker image prune -f
    log_info "✓ Cleanup completed"
}

# Main deployment flow
main() {
    log_info "Starting ET Heatmap deployment..."
    log_info "Environment: Production"
    log_info "Date: $(date)"

    check_prerequisites
    backup_database
    stop_services
    build_images
    start_services
    run_migrations
    health_check

    if [ $? -eq 0 ]; then
        log_info "✓ Deployment completed successfully!"
        log_info "Application is available at: https://your-domain.com"
        cleanup_old_images
    else
        log_error "Deployment failed. Rolling back..."
        docker-compose -f docker-compose.prod.yml down
        exit 1
    fi
}

# Run main function
main "$@"
