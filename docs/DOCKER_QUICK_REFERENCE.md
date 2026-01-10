# Docker Quick Reference

Quick reference guide for Docker commands specific to ET Heatmap.

---

## Development Commands

### Start/Stop Services

```bash
# Start all services
make up
# or
docker-compose up -d

# Stop all services
make down
# or
docker-compose down

# Restart services
make restart
# or
docker-compose restart

# Stop and remove volumes (deletes data!)
docker-compose down -v
```

### View Logs

```bash
# All services
make logs
docker-compose logs -f

# Specific service
make logs-backend
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Follow logs (real-time)
docker-compose logs -f --tail=50 backend
```

### Execute Commands

```bash
# Shell access
make shell-backend
docker-compose exec backend /bin/bash

# Run Python command
docker-compose exec backend python scripts/run_pipeline.py

# Database shell
make shell-db
docker-compose exec postgres psql -U et_heatmap -d et_heatmap

# Redis CLI
docker-compose exec redis redis-cli
```

### Build & Rebuild

```bash
# Build images
make build
docker-compose build

# Rebuild without cache
docker-compose build --no-cache

# Build specific service
docker-compose build backend
```

---

## Production Commands

### Deploy

```bash
# Automated deployment
make prod-deploy
./scripts/deploy.sh

# Manual deployment
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Manage Production Services

```bash
# Start production
make prod-up
docker-compose -f docker-compose.prod.yml up -d

# Stop production
make prod-down
docker-compose -f docker-compose.prod.yml down

# View logs
make prod-logs
docker-compose -f docker-compose.prod.yml logs -f

# Service status
docker-compose -f docker-compose.prod.yml ps

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
```

---

## Database Commands

### Migrations

```bash
# Run migrations
make db-migrate
docker-compose exec backend alembic upgrade head

# Rollback migration
make db-rollback
docker-compose exec backend alembic downgrade -1

# Show migration history
docker-compose exec backend alembic history

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Backups & Restore

```bash
# Create backup
make db-backup
docker-compose exec backend python scripts/backup_database.py --action backup

# List backups
ls -lh backups/

# Restore backup
make db-restore BACKUP_FILE=backups/backup.db.gz
docker-compose exec backend python scripts/backup_database.py \
  --action restore \
  --backup-file backups/et_heatmap_sqlite_20240109_030000.db.gz

# Reset database (WARNING: deletes all data!)
make db-reset
```

### Database Queries

```bash
# Connect to database
docker-compose exec postgres psql -U et_heatmap -d et_heatmap

# Run SQL query
docker-compose exec postgres psql -U et_heatmap -d et_heatmap \
  -c "SELECT COUNT(*) FROM entities;"

# Dump specific table
docker-compose exec postgres pg_dump -U et_heatmap et_heatmap \
  --table=entities > entities_backup.sql
```

---

## Testing Commands

### Run Tests

```bash
# All tests
make test
docker-compose exec backend pytest tests/

# With coverage
make test-coverage
docker-compose exec backend pytest tests/ --cov=src --cov-report=html

# Specific test file
docker-compose exec backend pytest tests/test_pipeline.py

# Verbose mode
docker-compose exec backend pytest tests/ -v -s
```

### Linting & Formatting

```bash
# Check formatting
make lint
docker-compose exec backend black --check src/

# Format code
make format
docker-compose exec backend black src/

# Run ruff
docker-compose exec backend ruff check src/

# Run mypy
docker-compose exec backend mypy src/
```

---

## Pipeline Commands

### Run Pipeline

```bash
# Full daily pipeline
make pipeline-run
docker-compose exec backend python scripts/run_pipeline.py

# Test pipeline
make pipeline-test
docker-compose exec backend python scripts/test_pipeline.py

# Specific pipeline step
docker-compose exec backend python -c "
from src.pipeline.steps.ingest_et_youtube import ingest_et_youtube
from datetime import datetime, timedelta
end = datetime.now()
start = end - timedelta(days=1)
result = ingest_et_youtube(start, end)
print(f'Ingested {len(result)} items')
"
```

---

## Monitoring Commands

### Service Status

```bash
# Check status
make status
docker-compose ps

# Check health
make health
curl http://localhost:8000/health
curl http://localhost/health

# Container stats
docker stats

# Resource usage
docker system df
```

### YouTube Quota

```bash
# Check quota
make quota
docker-compose exec backend python -c "
from src.common.youtube_quota import get_quota_tracker
print(get_quota_tracker().get_status())
"

# View quota file
cat data/youtube_quota.json
```

---

## Cleanup Commands

### Basic Cleanup

```bash
# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune -f

# Remove unused networks
docker network prune -f

# Remove everything (careful!)
make clean
docker system prune -af --volumes
```

### Cleanup Old Images

```bash
# List all images
docker images

# Remove specific image
docker rmi IMAGE_ID

# Remove dangling images
docker image prune

# Remove all unused images
docker image prune -a
```

### Cleanup Logs

```bash
# Find large log files
du -h logs/ | sort -h

# Remove old logs (30+ days)
find logs/ -name "*.log" -mtime +30 -delete

# Truncate log file
> logs/app.log
```

---

## Debugging Commands

### Inspect Containers

```bash
# Container details
docker inspect et-heatmap-backend

# Container IP address
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' et-heatmap-backend

# Environment variables
docker exec et-heatmap-backend env

# Running processes
docker top et-heatmap-backend
```

### Network Debugging

```bash
# List networks
docker network ls

# Inspect network
docker network inspect et-heatmap-v2_et-heatmap-network

# Test connectivity
docker-compose exec backend ping postgres
docker-compose exec backend curl http://frontend:80/health
```

### File System

```bash
# Copy file from container
docker cp et-heatmap-backend:/app/logs/app.log ./local-app.log

# Copy file to container
docker cp local-config.yaml et-heatmap-backend:/app/config/

# List files in container
docker exec et-heatmap-backend ls -la /app/

# Check disk usage in container
docker exec et-heatmap-backend df -h
```

---

## Performance Commands

### Resource Limits

```bash
# Set memory limit
docker-compose -f docker-compose.prod.yml up -d \
  --scale backend=1 \
  --memory="4g"

# Set CPU limit
docker update --cpus="2" et-heatmap-backend

# View resource limits
docker inspect et-heatmap-backend | grep -A 10 "Memory"
```

### Scaling

```bash
# Scale service (multiple instances)
docker-compose up -d --scale backend=3

# View scaled instances
docker-compose ps
```

---

## Security Commands

### Scan for Vulnerabilities

```bash
# Scan image with Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image et-heatmap-backend:latest

# Scan filesystem
docker run --rm -v $(pwd):/src aquasec/trivy fs /src
```

### Update Base Images

```bash
# Pull latest base images
docker-compose pull

# Rebuild with latest
docker-compose build --pull --no-cache
```

---

## Troubleshooting One-Liners

```bash
# Why won't container start?
docker-compose logs backend --tail=50

# Is database ready?
docker-compose exec postgres pg_isready

# Can backend reach database?
docker-compose exec backend ping postgres

# What's using port 8000?
lsof -i :8000

# Restart everything
docker-compose down && docker-compose up -d

# Force recreate containers
docker-compose up -d --force-recreate

# Remove everything and start fresh
docker-compose down -v && docker-compose build && docker-compose up -d
```

---

## Environment-Specific Commands

### Switch Between Environments

```bash
# Development
export COMPOSE_FILE=docker-compose.yml
docker-compose up -d

# Production
export COMPOSE_FILE=docker-compose.prod.yml
docker-compose up -d

# Multiple compose files
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

### Load Different .env Files

```bash
# Development
docker-compose --env-file .env up -d

# Production
docker-compose --env-file .env.production up -d

# Staging
docker-compose --env-file .env.staging up -d
```

---

## Useful Aliases

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# ET Heatmap aliases
alias eth-up='cd /opt/et-heatmap-v2 && docker-compose up -d'
alias eth-down='cd /opt/et-heatmap-v2 && docker-compose down'
alias eth-logs='cd /opt/et-heatmap-v2 && docker-compose logs -f'
alias eth-shell='cd /opt/et-heatmap-v2 && docker-compose exec backend /bin/bash'
alias eth-db='cd /opt/et-heatmap-v2 && docker-compose exec postgres psql -U et_heatmap -d et_heatmap'
alias eth-pipeline='cd /opt/et-heatmap-v2 && docker-compose exec backend python scripts/run_pipeline.py'
alias eth-status='cd /opt/et-heatmap-v2 && docker-compose ps'
```

---

## Emergency Commands

### Service Not Responding

```bash
# 1. Check if running
docker-compose ps

# 2. Check logs
docker-compose logs backend --tail=100

# 3. Restart service
docker-compose restart backend

# 4. Force recreate
docker-compose up -d --force-recreate backend

# 5. Nuclear option: restart everything
docker-compose down && docker-compose up -d
```

### Out of Disk Space

```bash
# 1. Check disk usage
df -h
docker system df

# 2. Remove stopped containers
docker container prune -f

# 3. Remove unused images
docker image prune -a

# 4. Remove old logs
find logs/ -name "*.log" -mtime +7 -delete

# 5. Remove old backups
find backups/ -name "*.gz" -mtime +30 -delete

# 6. Nuclear option
docker system prune -af --volumes
```

### Database Corrupted

```bash
# 1. Stop services
docker-compose down

# 2. Backup current state (even if corrupted)
cp -r data/ data_backup_$(date +%Y%m%d)/

# 3. Restore from latest backup
docker-compose up -d postgres
make db-restore BACKUP_FILE=backups/latest.sql

# 4. Restart services
docker-compose up -d
```

---

## Pro Tips

1. **Use Makefile**: `make up` is easier than `docker-compose up -d`
2. **Tail logs**: Always use `-f --tail=50` to avoid overwhelming output
3. **Health checks**: Check `/health` endpoints before debugging
4. **Resource monitoring**: Run `docker stats` in another terminal
5. **Clean regularly**: Run `docker system prune` weekly
6. **Backup before changes**: Always backup database before major changes
7. **Test locally first**: Use `docker-compose.yml` before production
8. **Use `.env` files**: Never hardcode secrets in compose files
9. **Version control**: Keep `docker-compose.yml` in git, `.env` in `.gitignore`
10. **Read logs**: Most issues are obvious in logs if you read them

---

## Quick Start Cheat Sheet

```bash
# First time setup
git clone <repo>
cd et-heatmap-v2
cp .env.example .env
nano .env  # Add your API keys
make setup

# Daily development
make up                    # Start services
make logs                  # View logs
make shell-backend         # Shell access
make pipeline-run          # Run pipeline
make test                  # Run tests
make down                  # Stop services

# Production deployment
./scripts/deploy.sh        # Deploy
docker-compose -f docker-compose.prod.yml ps  # Status
docker-compose -f docker-compose.prod.yml logs -f  # Logs

# Emergency
docker-compose restart backend  # Restart service
docker-compose down && docker-compose up -d  # Full restart
make clean                 # Clean everything
```
