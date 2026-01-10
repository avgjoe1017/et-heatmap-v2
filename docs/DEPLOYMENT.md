# Deployment Guide

Complete guide for deploying the ET Heatmap application locally and to production.

---

## Table of Contents

1. [Quick Start (Local Development)](#quick-start-local-development)
2. [Docker Setup](#docker-setup)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployments](#cloud-deployments)
5. [CI/CD Setup](#cicd-setup)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start (Local Development)

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git
- 8GB RAM minimum
- 20GB disk space

### 1. Clone Repository

```bash
git clone https://github.com/your-org/et-heatmap-v2.git
cd et-heatmap-v2
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

Required variables:
- `YOUTUBE_API_KEY` - Get from https://console.cloud.google.com/apis/credentials
- `POSTGRES_PASSWORD` - Set a secure password

### 3. Start Services

```bash
# Using Makefile (recommended)
make setup
make up

# Or using docker-compose directly
docker-compose build
docker-compose up -d
```

### 4. Verify Installation

```bash
# Check service status
make status

# Check health
make health

# View logs
make logs
```

**Access the application:**
- Frontend: http://localhost:80
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

### 5. Run Initial Pipeline

```bash
# Run daily pipeline
make pipeline-run

# Or test with small dataset
make pipeline-test
```

---

## Docker Setup

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Network                          │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Frontend │◄───│  Nginx   │◄───│ Backend  │             │
│  │ (React)  │    │ (Proxy)  │    │ (FastAPI)│             │
│  └──────────┘    └──────────┘    └────┬─────┘             │
│                                        │                    │
│                                        ▼                    │
│                                  ┌──────────┐              │
│                                  │Postgres  │              │
│                                  │          │              │
│                                  └──────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Services

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| backend | et-heatmap-backend | 8000 | FastAPI application |
| frontend | et-heatmap-frontend | 80 | React UI with nginx |
| postgres | et-heatmap-postgres | 5432 | PostgreSQL database |
| redis | et-heatmap-redis | 6379 | Redis cache (optional) |

### Development vs Production

**Development (`docker-compose.yml`):**
- Hot reload enabled
- Source code mounted
- Debug logging
- Exposed ports
- SQLite option available

**Production (`docker-compose.prod.yml`):**
- Optimized builds
- No source mounting
- Production logging
- Internal networking
- PostgreSQL required
- SSL/TLS support
- Health checks
- Resource limits

### Common Commands

```bash
# Build images
make build

# Start services
make up

# Stop services
make down

# Restart services
make restart

# View logs
make logs
make logs-backend
make logs-frontend

# Shell access
make shell-backend
make shell-db

# Database operations
make db-migrate
make db-backup
make db-restore BACKUP_FILE=backups/backup.db.gz

# Run pipeline
make pipeline-run

# Run tests
make test
make test-coverage

# Code quality
make lint
make format

# Cleanup
make clean
```

---

## Production Deployment

### Prerequisites

- Linux server (Ubuntu 22.04 LTS recommended)
- Docker 20.10+
- Docker Compose 2.0+
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)
- 4+ CPU cores
- 16GB+ RAM
- 100GB+ SSD storage

### Option 1: Manual Deployment

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply group changes
```

#### 2. Clone and Configure

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/your-org/et-heatmap-v2.git
cd et-heatmap-v2
sudo chown -R $USER:$USER .

# Create production environment file
cp .env.example .env.production
nano .env.production
```

**Required production variables:**

```bash
# Database (use strong passwords!)
POSTGRES_USER=et_heatmap_prod
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>
POSTGRES_DB=et_heatmap
DATABASE_URL=postgresql://et_heatmap_prod:<PASSWORD>@postgres:5432/et_heatmap

# API Keys
YOUTUBE_API_KEY=<your-youtube-api-key>
REDDIT_CLIENT_ID=<your-reddit-client-id>
REDDIT_CLIENT_SECRET=<your-reddit-secret>
REDDIT_USERNAME=<your-reddit-username>
REDDIT_PASSWORD=<your-reddit-password>

# Sentry (Error Monitoring)
SENTRY_DSN=<your-sentry-dsn>
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=et-heatmap@0.1.0

# Security
REDIS_PASSWORD=<strong-redis-password>

# URLs
CORS_ORIGINS=https://yourdomain.com
VITE_API_URL=https://yourdomain.com

# Backup (optional - S3)
BACKUP_S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=<your-aws-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret>
```

#### 3. SSL Certificate Setup

Using Let's Encrypt (recommended):

```bash
# Install certbot
sudo apt install certbot

# Get certificate (standalone mode)
sudo certbot certonly --standalone -d yourdomain.com

# Certificates will be in /etc/letsencrypt/live/yourdomain.com/
# Copy to project directory
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
sudo chown -R $USER:$USER nginx/ssl
```

#### 4. Update nginx Configuration

Edit `nginx/nginx.prod.conf`:

```nginx
# Replace this line
server_name your-domain.com;

# With your actual domain
server_name yourdomain.com;
```

#### 5. Deploy

```bash
# Run deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Or manually
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

#### 6. Verify Deployment

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Health check
curl https://yourdomain.com/health
```

### Option 2: Automated Deployment Script

```bash
# One-command deployment
./scripts/deploy.sh
```

The script will:
1. Check prerequisites
2. Backup database
3. Build Docker images
4. Stop old services
5. Start new services
6. Run migrations
7. Health checks
8. Cleanup

### SSL Certificate Renewal

Setup auto-renewal with cron:

```bash
# Edit crontab
crontab -e

# Add renewal job (runs daily at 3 AM)
0 3 * * * certbot renew --quiet --post-hook "docker-compose -f /opt/et-heatmap-v2/docker-compose.prod.yml restart nginx"
```

### Systemd Service (Optional)

Create `/etc/systemd/system/et-heatmap.service`:

```ini
[Unit]
Description=ET Heatmap
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/et-heatmap-v2
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable et-heatmap
sudo systemctl start et-heatmap
sudo systemctl status et-heatmap
```

---

## Cloud Deployments

### AWS (Elastic Beanstalk + RDS)

#### 1. Install EB CLI

```bash
pip install awsebcli
```

#### 2. Initialize EB Application

```bash
eb init -p docker et-heatmap-prod --region us-west-2
```

#### 3. Create RDS Database

```bash
eb create et-heatmap-env --database.engine postgres --database.size 20
```

#### 4. Set Environment Variables

```bash
eb setenv YOUTUBE_API_KEY=xxx REDDIT_CLIENT_ID=xxx SENTRY_DSN=xxx
```

#### 5. Deploy

```bash
eb deploy
```

#### 6. Configure SSL

```bash
# Add HTTPS listener in EB console
# Upload SSL certificate
```

### Google Cloud Platform (Cloud Run + Cloud SQL)

#### 1. Setup Cloud SQL

```bash
gcloud sql instances create et-heatmap-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1
```

#### 2. Build and Push Images

```bash
# Backend
gcloud builds submit --tag gcr.io/PROJECT_ID/et-heatmap-backend

# Frontend
gcloud builds submit --tag gcr.io/PROJECT_ID/et-heatmap-frontend ./ui
```

#### 3. Deploy to Cloud Run

```bash
# Backend
gcloud run deploy et-heatmap-backend \
  --image gcr.io/PROJECT_ID/et-heatmap-backend \
  --add-cloudsql-instances PROJECT_ID:us-central1:et-heatmap-db \
  --set-env-vars DATABASE_URL=postgresql://...

# Frontend
gcloud run deploy et-heatmap-frontend \
  --image gcr.io/PROJECT_ID/et-heatmap-frontend
```

### DigitalOcean (App Platform)

#### 1. Create App

- Go to App Platform
- Connect GitHub repository
- Select branch: `main`

#### 2. Configure Services

**Backend:**
- Type: Web Service
- Dockerfile: `Dockerfile`
- Port: 8000
- Health Check: `/health`

**Frontend:**
- Type: Static Site
- Build Command: `npm run build`
- Output Directory: `dist`

**Database:**
- Add PostgreSQL database (managed)

#### 3. Set Environment Variables

Add in App Platform console:
- `DATABASE_URL` (from managed database)
- `YOUTUBE_API_KEY`
- `SENTRY_DSN`
- etc.

#### 4. Deploy

Click "Deploy" - automatic on push to main.

### Kubernetes (K8s)

See `k8s/` directory for manifests:

```bash
# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n et-heatmap

# View logs
kubectl logs -f deployment/backend -n et-heatmap
```

---

## CI/CD Setup

### GitHub Actions

The project includes a complete CI/CD pipeline in `.github/workflows/ci-cd.yml`.

#### Required GitHub Secrets

Set these in your repository settings (Settings → Secrets → Actions):

```
# Docker Hub
DOCKER_USERNAME
DOCKER_PASSWORD

# Deployment
DEPLOY_HOST          # Your server IP/hostname
DEPLOY_USER          # SSH username
DEPLOY_SSH_KEY       # Private SSH key
DEPLOY_URL           # https://yourdomain.com

# Notifications (optional)
SLACK_WEBHOOK_URL    # Slack webhook for notifications
```

#### Pipeline Stages

1. **Test** - Run Python and frontend tests
2. **Lint** - Code quality checks (Black, Ruff, MyPy)
3. **Build** - Build and push Docker images
4. **Security** - Scan for vulnerabilities (Trivy)
5. **Deploy** - Deploy to production (main branch only)

#### Triggering Deployments

```bash
# Automatic deployment on push to main
git push origin main

# Manual trigger via GitHub UI
# Actions → CI/CD Pipeline → Run workflow
```

### GitLab CI/CD

Create `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - pip install -e .
    - pytest tests/

build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - ssh $DEPLOY_USER@$DEPLOY_HOST "cd /opt/et-heatmap-v2 && ./scripts/deploy.sh"
  only:
    - main
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Check all services
curl https://yourdomain.com/health

# Check backend directly
curl http://localhost:8000/health

# Check frontend
curl http://localhost/health
```

### Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# View last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Backups

Automated daily backups are configured in `docker-compose.prod.yml`.

```bash
# Manual backup
docker-compose -f docker-compose.prod.yml exec backup \
  python scripts/backup_database.py --action backup

# List backups
ls -lh backups/

# Restore from backup
docker-compose -f docker-compose.prod.yml exec backup \
  python scripts/backup_database.py --action restore \
  --backup-file backups/et_heatmap_postgres_20240109_030000.sql
```

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
./scripts/deploy.sh

# Or manually
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Resource Monitoring

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Clean up old images
docker image prune -a
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend

# Verify environment variables
docker-compose config

# Restart services
docker-compose restart
```

### Database Connection Issues

```bash
# Check if Postgres is running
docker-compose ps postgres

# Check Postgres logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U et_heatmap -d et_heatmap -c "SELECT 1"

# Verify DATABASE_URL
docker-compose exec backend env | grep DATABASE_URL
```

### Backend API Not Responding

```bash
# Check backend logs
docker-compose logs backend

# Check health endpoint
curl http://localhost:8000/health

# Restart backend
docker-compose restart backend

# Shell into container
docker-compose exec backend /bin/bash
python -c "import requests; print(requests.get('http://localhost:8000/health').text)"
```

### Frontend Not Loading

```bash
# Check nginx logs
docker-compose logs frontend

# Check if nginx is serving files
docker-compose exec frontend ls -la /usr/share/nginx/html

# Verify nginx config
docker-compose exec frontend nginx -t

# Restart frontend
docker-compose restart frontend
```

### Pipeline Failures

```bash
# Check pipeline logs
docker-compose logs scheduler

# Run pipeline manually
docker-compose exec backend python scripts/run_pipeline.py

# Check quota status
docker-compose exec backend python -c "
from src.common.youtube_quota import get_quota_tracker
print(get_quota_tracker().get_status())
"
```

### Out of Disk Space

```bash
# Check disk usage
df -h
docker system df

# Clean up
docker system prune -a --volumes
docker image prune -a
docker volume prune

# Remove old logs
find logs/ -name "*.log" -mtime +30 -delete
```

### Memory Issues

```bash
# Check container memory usage
docker stats

# Set memory limits in docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 4G

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

### SSL Certificate Issues

```bash
# Check certificate expiry
openssl x509 -in nginx/ssl/fullchain.pem -noout -dates

# Renew certificate
sudo certbot renew

# Reload nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## Production Checklist

Before going live:

- [ ] All environment variables configured
- [ ] SSL certificates installed and verified
- [ ] Database backups configured (daily)
- [ ] Sentry error monitoring configured
- [ ] YouTube API quota monitoring enabled
- [ ] Firewall configured (ports 80, 443 open)
- [ ] Domain DNS configured
- [ ] Health checks passing
- [ ] Logs rotation configured
- [ ] Resource limits set
- [ ] Monitoring alerts configured
- [ ] CI/CD pipeline tested
- [ ] Backup restoration tested
- [ ] Load testing completed
- [ ] Security scan completed

---

## Support

For issues or questions:

- **Documentation**: See `docs/` directory
- **GitHub Issues**: https://github.com/your-org/et-heatmap-v2/issues
- **Email**: support@yourdomain.com
