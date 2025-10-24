# Deployment Documentation

## Overview

The Travya application is designed for containerized deployment using Docker and Docker Compose, with support for both development and production environments. The application consists of a React frontend, FastAPI backend, PostgreSQL database, and Redis cache.

## Architecture

### System Components
- **Frontend**: React application with Vite build system
- **Backend**: FastAPI Python application with AI agents
- **Database**: PostgreSQL with SQLModel ORM
- **Cache**: Redis for session management and caching
- **Reverse Proxy**: Nginx for production deployments

### Container Structure
```
travya/
├── frontend/          # React frontend
├── backend/           # FastAPI backend
├── nginx/             # Nginx configuration
├── docker-compose.yml # Development environment
├── docker-compose.prod.yml # Production environment
└── Dockerfile.*       # Individual service Dockerfiles
```

## Development Environment

### Prerequisites
- Docker Desktop
- Docker Compose
- Git

### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd travya

# Start development environment
docker compose up -d

# View logs
docker compose logs -f

# Stop environment
docker compose down
```

### Development Services
**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/travya
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=local
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=travya
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## Production Environment

### Production Configuration
**File**: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
    environment:
      - VITE_API_URL=https://api.travya.com
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY}
      - GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}
      - AMADEUS_CLIENT_ID=${AMADEUS_CLIENT_ID}
      - AMADEUS_CLIENT_SECRET=${AMADEUS_CLIENT_SECRET}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Environment Variables
**File**: `.env.production`

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/travya_prod
POSTGRES_DB=travya_prod
POSTGRES_USER=travya_user
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# External APIs
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key

# Weather API
WEATHER_API_KEY=your_weather_api_key

# AI Services
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-pro

# Monitoring
SENTRY_DSN=your_sentry_dsn
```

## Docker Configuration

### Frontend Dockerfile
**File**: `frontend/Dockerfile`

```dockerfile
# Development
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**File**: `frontend/Dockerfile.prod`

```dockerfile
# Production
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Backend Dockerfile
**File**: `backend/Dockerfile`

```dockerfile
# Development
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install -e .

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**File**: `backend/Dockerfile.prod`

```dockerfile
# Production
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install -e . --no-cache-dir

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Nginx Configuration

### Development Nginx
**File**: `nginx/nginx.dev.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:5173;
    }

    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Production Nginx
**File**: `nginx/nginx.conf`

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    upstream frontend {
        server frontend:80;
    }

    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name travya.com www.travya.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name travya.com www.travya.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Auth endpoints with stricter rate limiting
        location /api/v1/auth/ {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location /static/ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## Database Management

### Migrations
```bash
# Create migration
docker compose exec backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker compose exec backend alembic upgrade head

# Rollback migration
docker compose exec backend alembic downgrade -1

# Check migration status
docker compose exec backend alembic current
```

### Database Backup
```bash
# Backup database
docker compose exec postgres pg_dump -U postgres travya > backup.sql

# Restore database
docker compose exec -T postgres psql -U postgres travya < backup.sql
```

### Database Initialization
```bash
# Initialize database with sample data
docker compose exec backend python -m app.initial_data
```

## Monitoring and Logging

### Health Checks
**File**: `backend/app/health.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.core.config import settings
import redis
import httpx

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}

@router.get("/health/detailed")
async def detailed_health_check(session: AsyncSession = Depends(get_session)):
    """Detailed health check with dependencies."""
    health_status = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "services": {}
    }
    
    # Check database
    try:
        await session.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check external APIs
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://maps.googleapis.com/maps/api/place/textsearch/json", timeout=5.0)
            if response.status_code == 200:
                health_status["services"]["google_maps"] = "healthy"
            else:
                health_status["services"]["google_maps"] = f"unhealthy: {response.status_code}"
    except Exception as e:
        health_status["services"]["google_maps"] = f"unhealthy: {str(e)}"
    
    return health_status
```

### Logging Configuration
**File**: `backend/app/core/logging.py`

```python
import logging
import sys
from app.core.config import settings

def setup_logging():
    """Setup application logging."""
    log_level = logging.INFO if settings.ENVIRONMENT == "production" else logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log") if settings.ENVIRONMENT == "production" else logging.NullHandler()
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
```

### Prometheus Metrics
**File**: `backend/app/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Metrics
api_requests_total = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration', ['method', 'endpoint'])
active_connections = Gauge('active_connections', 'Active database connections')
memory_usage = Gauge('memory_usage_bytes', 'Memory usage in bytes')

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")
```

## Security

### SSL/TLS Configuration
```bash
# Generate self-signed certificate for development
openssl req -x509 -newkey rsa:4096 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365 -nodes

# For production, use Let's Encrypt
certbot certonly --webroot -w /var/www/html -d travya.com
```

### Security Headers
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://travya.com", "https://www.travya.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["travya.com", "www.travya.com", "localhost"]
)
```

### Environment Security
```bash
# Secure environment file
chmod 600 .env.production

# Use secrets management
docker secret create db_password ./secrets/db_password.txt
docker secret create jwt_secret ./secrets/jwt_secret.txt
```

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  backend:
    deploy:
      replicas: 3
    environment:
      - WORKER_PROCESSES=4

  nginx:
    depends_on:
      - backend
    # Load balancing configuration
```

### Load Balancer Configuration
```nginx
upstream backend {
    least_conn;
    server backend_1:8000;
    server backend_2:8000;
    server backend_3:8000;
}
```

### Database Scaling
```yaml
# Read replicas
services:
  postgres_read:
    image: postgres:15
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    command: postgres -c hot_standby=on
    depends_on:
      - postgres
```

## Deployment Scripts

### Deploy Script
**File**: `scripts/deploy.sh`

```bash
#!/bin/bash

set -e

echo "Starting deployment..."

# Pull latest code
git pull origin main

# Build and start services
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Run migrations
echo "Running database migrations..."
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Health check
echo "Performing health check..."
curl -f http://localhost/health || exit 1

echo "Deployment completed successfully!"
```

### Rollback Script
**File**: `scripts/rollback.sh`

```bash
#!/bin/bash

set -e

echo "Starting rollback..."

# Get previous commit
PREVIOUS_COMMIT=$(git log --oneline -n 2 | tail -1 | cut -d' ' -f1)

# Checkout previous commit
git checkout $PREVIOUS_COMMIT

# Rebuild and restart
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

echo "Rollback completed!"
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database status
docker compose exec postgres pg_isready -U postgres

# Check database logs
docker compose logs postgres

# Reset database
docker compose down -v
docker compose up -d
```

#### Redis Connection Issues
```bash
# Check Redis status
docker compose exec redis redis-cli ping

# Check Redis logs
docker compose logs redis

# Clear Redis cache
docker compose exec redis redis-cli FLUSHALL
```

#### Frontend Build Issues
```bash
# Clear node modules
docker compose exec frontend rm -rf node_modules
docker compose exec frontend npm install

# Rebuild frontend
docker compose build frontend --no-cache
```

#### Backend Import Issues
```bash
# Check Python path
docker compose exec backend python -c "import sys; print(sys.path)"

# Reinstall dependencies
docker compose exec backend pip install -e . --force-reinstall
```

### Log Analysis
```bash
# View all logs
docker compose logs

# View specific service logs
docker compose logs backend
docker compose logs frontend
docker compose logs postgres

# Follow logs in real-time
docker compose logs -f backend

# View logs with timestamps
docker compose logs -t backend
```

### Performance Monitoring
```bash
# Check container resource usage
docker stats

# Check specific container
docker stats travya_backend_1

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

## Backup and Recovery

### Automated Backup
**File**: `scripts/backup.sh`

```bash
#!/bin/bash

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker compose exec postgres pg_dump -U postgres travya > $BACKUP_DIR/db_backup_$DATE.sql

# Backup Redis
docker compose exec redis redis-cli --rdb $BACKUP_DIR/redis_backup_$DATE.rdb

# Backup application data
tar -czf $BACKUP_DIR/app_data_$DATE.tar.gz ./uploads

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### Recovery
**File**: `scripts/restore.sh`

```bash
#!/bin/bash

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Restoring from backup: $BACKUP_FILE"

# Stop services
docker compose down

# Restore database
docker compose up -d postgres
sleep 10
docker compose exec -T postgres psql -U postgres travya < $BACKUP_FILE

# Start all services
docker compose up -d

echo "Restore completed!"
```
