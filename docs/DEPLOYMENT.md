# DEPLOYMENT GUIDE - MINEDU RAG SYSTEM v1.4.0

## 🚀 DEPLOYMENT OVERVIEW

Guía completa para deploying el sistema RAG MINEDU en diferentes entornos: desarrollo, staging, y producción con CI/CD automatizado.

## 📋 PRE-DEPLOYMENT CHECKLIST

### System Requirements
- **Operating System**: Ubuntu 22.04 LTS (recommended) or similar
- **Memory**: 16GB RAM minimum, 32GB recommended
- **Storage**: 100GB SSD minimum, 500GB recommended
- **CPU**: 8 cores minimum, 16 cores recommended
- **Network**: 1 Gbps connection, static IP

### Software Dependencies
```bash
# Core Dependencies
- Docker 24.0+ with Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)
- PostgreSQL 15+
- Redis 7+
- Nginx (reverse proxy)

# Optional for advanced features
- Elasticsearch (for advanced search)
- Prometheus (monitoring)
- Grafana (dashboards)
```

## 🏗️ INFRASTRUCTURE SETUP

### 1. Docker Environment Setup
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Environment Configuration
```bash
# Create environment file
cp .env.example .env.production

# Configure production variables
vim .env.production
```

**Required Environment Variables:**
```env
# Application
ENVIRONMENT=production
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8001

# Database
DATABASE_URL=postgresql://minedu_user:${DB_PASSWORD}@postgres:5432/minedu_rag
REDIS_URL=redis://redis:6379/0

# Authentication
JWT_SECRET_KEY=${JWT_SECRET}
JWT_EXPIRATION_HOURS=24
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
MICROSOFT_CLIENT_ID=${MICROSOFT_CLIENT_ID}
MICROSOFT_CLIENT_SECRET=${MICROSOFT_CLIENT_SECRET}

# AI APIs
OPENAI_API_KEY=${OPENAI_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}

# Security
RATE_LIMIT_ENABLED=true
AUDIT_LOGGING_ENABLED=true
PII_PROTECTION_ENABLED=true
ALLOWED_ORIGINS=https://rag.minedu.gob.pe,https://minedu.gob.pe

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
LOG_LEVEL=INFO
```

## 🔧 PRODUCTION DEPLOYMENT

### 1. Automated Setup Script
```bash
#!/bin/bash
# setup_enterprise.sh - Enterprise deployment script

set -e

echo "🚀 Starting MINEDU RAG Enterprise Setup..."

# Check requirements
check_requirements() {
    echo "📋 Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose not found."
        exit 1
    fi
    
    # Check available memory
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [ $MEMORY_GB -lt 16 ]; then
        echo "⚠️ Warning: Less than 16GB RAM available (${MEMORY_GB}GB)"
    fi
    
    echo "✅ System requirements check passed"
}

# Setup environment
setup_environment() {
    echo "🔧 Setting up environment..."
    
    # Create data directories
    mkdir -p data/vectorstores
    mkdir -p data/processed
    mkdir -p data/backups
    mkdir -p logs
    
    # Set permissions
    chmod 755 data/
    chmod 755 logs/
    
    # Copy environment files
    if [ ! -f .env.production ]; then
        if [ -f .env.example ]; then
            cp .env.example .env.production
            echo "⚠️ Please edit .env.production with your production values"
        else
            echo "❌ .env.example not found"
            exit 1
        fi
    fi
    
    echo "✅ Environment setup completed"
}

# Initialize database
initialize_database() {
    echo "🗄️ Initializing database..."
    
    # Start database services
    docker-compose up -d postgres redis
    
    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    sleep 10
    
    # Run database migrations
    docker-compose exec backend python -m alembic upgrade head
    
    # Create default admin user (if not exists)
    docker-compose exec backend python scripts/create_admin.py
    
    echo "✅ Database initialization completed"
}

# Deploy services
deploy_services() {
    echo "🚢 Deploying services..."
    
    # Build and start all services
    docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d --build
    
    # Wait for services to be healthy
    echo "Waiting for services to be healthy..."
    sleep 30
    
    # Run health checks
    python scripts/health_check.py
    
    echo "✅ Services deployment completed"
}

# Setup monitoring
setup_monitoring() {
    echo "📊 Setting up monitoring..."
    
    # Start monitoring services
    docker-compose -f docker-compose.monitoring.yml up -d
    
    # Configure Grafana dashboards
    python scripts/setup_grafana_dashboards.py
    
    echo "✅ Monitoring setup completed"
}

# Main execution
main() {
    check_requirements
    setup_environment
    initialize_database
    deploy_services
    setup_monitoring
    
    echo ""
    echo "🎉 MINEDU RAG Enterprise deployment completed successfully!"
    echo ""
    echo "📍 Service URLs:"
    echo "   - API: http://localhost:8001"
    echo "   - Frontend: http://localhost:3000"
    echo "   - Grafana: http://localhost:3001"
    echo "   - Prometheus: http://localhost:9090"
    echo ""
    echo "📚 Next steps:"
    echo "   1. Configure reverse proxy (Nginx)"
    echo "   2. Setup SSL certificates"
    echo "   3. Configure DNS records"
    echo "   4. Run initial tests"
    echo ""
}

# Run main function
main "$@"
```

### 2. Docker Compose Production Configuration
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.production
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ./data/vectorstores:/app/data/vectorstores:ro
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend-new
      dockerfile: Dockerfile.production
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://api.rag.minedu.gob.pe
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=minedu_rag
      - POSTGRES_USER=minedu_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--auth-host=md5
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/postgres-init:/docker-entrypoint-initdb.d
    restart: unless-stopped
    command: >
      postgres
      -c shared_preload_libraries=pg_stat_statements
      -c pg_stat_statements.max=10000
      -c pg_stat_statements.track=all
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c work_mem=4MB

  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --appendonly yes
      --appendfsync everysec
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
```

### 3. Nginx Configuration
```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8001;
        keepalive 32;
    }
    
    upstream frontend {
        server frontend:3000;
        keepalive 32;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Frontend
    server {
        listen 80;
        listen 443 ssl http2;
        server_name rag.minedu.gob.pe;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    
    # API Backend
    server {
        listen 80;
        listen 443 ssl http2;
        server_name api.rag.minedu.gob.pe;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        # API Rate limiting
        location /api/ {
            limit_req zone=api burst=10 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS headers
            add_header Access-Control-Allow-Origin https://rag.minedu.gob.pe always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        }
        
        # Login endpoint with stricter limits
        location /api/auth/ {
            limit_req zone=login burst=3 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check (no rate limiting)
        location /health {
            proxy_pass http://backend;
            access_log off;
        }
    }
}
```

## ⚙️ CI/CD PIPELINE

### GitHub Actions Workflow
```yaml
# .github/workflows/ci-cd-enterprise.yml
name: Enterprise CI/CD Pipeline

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Security scan with Bandit
        run: |
          pip install bandit
          bandit -r backend/src -f json -o security-report.json
      
      - name: Dependency vulnerability scan
        run: |
          pip install safety
          safety check --json --output vulnerability-report.json
      
      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: "*-report.json"

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          pytest tests/ -v --cov=src --cov-report=xml --cov-report=term
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: backend/coverage.xml

  build:
    needs: [security-scan, test]
    runs-on: ubuntu-latest
    strategy:
      matrix:
        component: [backend, frontend]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.component }}
          file: ./${{ matrix.component }}/Dockerfile.production
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/${{ matrix.component }}:latest
            ghcr.io/${{ github.repository }}/${{ matrix.component }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/staging'
    environment: staging
    
    steps:
      - name: Deploy to staging
        run: |
          # SSH to staging server and deploy
          echo "Deploying to staging environment..."
          
  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
      - name: Manual approval gate
        uses: trstringer/manual-approval@v1
        with:
          secret: ${{ github.TOKEN }}
          approvers: admin-team
          minimum-approvals: 2
          issue-title: "Deploy to Production"
      
      - name: Deploy to production
        run: |
          # SSH to production server and deploy
          echo "Deploying to production environment..."
```

## 📊 MONITORING & ALERTING

### Prometheus Configuration
```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'minedu-rag-backend'
    static_configs:
      - targets: ['backend:8001']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'minedu-rag-postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'minedu-rag-redis'
    static_configs:
      - targets: ['redis-exporter:9121']

alertmanager:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Alert Rules
```yaml
# prometheus/alert_rules.yml
groups:
  - name: minedu-rag-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests per second"

      - alert: DatabaseDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"

      - alert: LowConfidenceResponses
        expr: avg_over_time(response_confidence[1h]) < 0.5
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "System confidence is low"
```

## 🔄 BACKUP & RECOVERY

### Database Backup Strategy
```bash
#!/bin/bash
# scripts/backup_database.sh

BACKUP_DIR="/data/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/minedu_rag_backup_${DATE}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
docker-compose exec -T postgres pg_dump -U minedu_user minedu_rag > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Encrypt backup
gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
    --s2k-digest-algo SHA512 --s2k-count 65536 --symmetric \
    --output "${BACKUP_FILE}.gz.gpg" "${BACKUP_FILE}.gz"

# Remove unencrypted file
rm "${BACKUP_FILE}.gz"

# Clean old backups (keep last 30 days)
find $BACKUP_DIR -name "*.sql.gz.gpg" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz.gpg"
```

### Recovery Script
```bash
#!/bin/bash
# scripts/restore_from_backup.py

import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

def restore_database(backup_file: str, target_db: str = "minedu_rag"):
    """Restore database from encrypted backup"""
    
    try:
        # Decrypt backup
        logging.info(f"Decrypting backup: {backup_file}")
        subprocess.run([
            "gpg", "--decrypt", backup_file
        ], check=True, stdout=open(f"{backup_file}.decrypted", "wb"))
        
        # Decompress
        logging.info("Decompressing backup...")
        subprocess.run([
            "gunzip", f"{backup_file}.decrypted"
        ], check=True)
        
        # Stop application
        logging.info("Stopping application...")
        subprocess.run(["docker-compose", "stop", "backend"], check=True)
        
        # Drop and recreate database
        logging.info(f"Recreating database: {target_db}")
        subprocess.run([
            "docker-compose", "exec", "-T", "postgres",
            "psql", "-U", "minedu_user", "-c", f"DROP DATABASE IF EXISTS {target_db};"
        ], check=True)
        
        subprocess.run([
            "docker-compose", "exec", "-T", "postgres", 
            "psql", "-U", "minedu_user", "-c", f"CREATE DATABASE {target_db};"
        ], check=True)
        
        # Restore data
        logging.info("Restoring database data...")
        with open(f"{backup_file}.sql", "rb") as f:
            subprocess.run([
                "docker-compose", "exec", "-T", "postgres",
                "psql", "-U", "minedu_user", "-d", target_db
            ], stdin=f, check=True)
        
        # Start application
        logging.info("Starting application...")
        subprocess.run(["docker-compose", "start", "backend"], check=True)
        
        # Cleanup
        Path(f"{backup_file}.decrypted").unlink(missing_ok=True)
        Path(f"{backup_file}.sql").unlink(missing_ok=True)
        
        logging.info("Database restore completed successfully!")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Restore failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python restore_from_backup.py <backup_file.sql.gz.gpg>")
        sys.exit(1)
    
    backup_file = sys.argv[1]
    restore_database(backup_file)
```

## 🔍 HEALTH CHECKS & MAINTENANCE

### Comprehensive Health Check
```python
# scripts/health_check.py
import asyncio
import aiohttp
import asyncpg
import redis
import logging
from typing import Dict, Any

async def check_api_health() -> Dict[str, Any]:
    """Check API endpoint health"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8001/health') as response:
                if response.status == 200:
                    data = await response.json()
                    return {"status": "healthy", "response_time": data.get("response_time")}
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_database_health() -> Dict[str, Any]:
    """Check PostgreSQL health"""
    try:
        conn = await asyncpg.connect(
            "postgresql://minedu_user:password@localhost:5432/minedu_rag"
        )
        
        # Test basic query
        result = await conn.fetchval("SELECT 1")
        
        # Check connection count
        conn_count = await conn.fetchval(
            "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
        )
        
        await conn.close()
        
        return {
            "status": "healthy",
            "active_connections": conn_count,
            "query_test": result == 1
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_redis_health() -> Dict[str, Any]:
    """Check Redis health"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Test ping
        pong = r.ping()
        
        # Get info
        info = r.info()
        memory_usage = info.get('used_memory_human', 'unknown')
        
        return {
            "status": "healthy" if pong else "unhealthy",
            "memory_usage": memory_usage,
            "connected_clients": info.get('connected_clients', 0)
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def main():
    """Run all health checks"""
    print("🔍 Running comprehensive health checks...")
    
    # Run checks in parallel
    api_health, db_health, redis_health = await asyncio.gather(
        check_api_health(),
        check_database_health(), 
        check_redis_health()
    )
    
    # Print results
    print(f"API Health: {api_health}")
    print(f"Database Health: {db_health}")
    print(f"Redis Health: {redis_health}")
    
    # Overall status
    all_healthy = all([
        api_health["status"] == "healthy",
        db_health["status"] == "healthy", 
        redis_health["status"] == "healthy"
    ])
    
    if all_healthy:
        print("✅ All systems healthy!")
        return 0
    else:
        print("❌ Some systems are unhealthy!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
```

## 🔧 MAINTENANCE PROCEDURES

### Scheduled Maintenance Tasks
```bash
# Cron configuration
# /etc/crontab

# Daily backup at 2 AM
0 2 * * * root /opt/minedu-rag/scripts/backup_database.sh

# Weekly log rotation
0 3 * * 0 root /opt/minedu-rag/scripts/rotate_logs.sh

# Monthly security updates
0 4 1 * * root /opt/minedu-rag/scripts/security_updates.sh

# Daily health checks
*/15 * * * * root /opt/minedu-rag/scripts/health_check.py
```

### Update Procedures
```bash
#!/bin/bash
# scripts/update_system.sh

echo "🔄 Starting system update..."

# 1. Backup before update
./scripts/backup_database.sh

# 2. Pull latest images
docker-compose pull

# 3. Graceful shutdown
docker-compose down --timeout 60

# 4. Update configuration if needed
# ./scripts/update_config.sh

# 5. Start with new images
docker-compose up -d

# 6. Run health checks
sleep 30
python scripts/health_check.py

# 7. Verify functionality
python scripts/smoke_tests.py

echo "✅ System update completed!"
```

---
*Deployment Guide - MINEDU RAG System v1.4.0*
*Enterprise-grade deployment for production environments*