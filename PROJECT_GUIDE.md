# Travya - AI-Powered Travel Companion

A comprehensive travel planning and booking platform powered by AI agents, built with FastAPI backend and React frontend.

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (recommended)
- **Node.js** 18+ (for local development)
- **Python** 3.11+ (for local development)
- **Git**

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd travya
   ```

2. **Set up environment variables**
   ```bash
   cp backend/env.example backend/.env
   # Edit backend/.env with your configuration
   ```

3. **Start the application**
   ```bash
   docker compose up -d --build
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Local Development

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   source .venv/bin/activate
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Start the backend**
   ```bash
   fastapi run app/main.py --reload
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the frontend**
   ```bash
   npm run dev
   ```

## 🏗️ Project Structure

```
travya/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/         # AI agent implementations
│   │   ├── api/           # REST API endpoints
│   │   ├── core/          # Core configuration and utilities
│   │   ├── services/      # Business logic services
│   │   └── tests/         # Backend tests
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── routes/        # Application routes
│   │   ├── contexts/      # React contexts
│   │   └── hooks/         # Custom hooks
│   ├── Dockerfile
│   └── package.json
├── docs/                   # Documentation
├── scripts/               # Build and deployment scripts
└── docker-compose.yml     # Docker Compose configuration
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
# Database
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=travya
POSTGRES_PASSWORD=changethis
POSTGRES_DB=travya

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# External APIs
OPENAI_API_KEY=your-openai-key
GOOGLE_AI_API_KEY=your-google-ai-key
AMADEUS_API_KEY=your-amadeus-key
GOOGLE_MAPS_API_KEY=your-google-maps-key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

#### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
```

## 🧪 Testing

### Backend Tests
```bash
# Run all backend tests
cd backend
pytest

# Run specific test categories
pytest tests/agents/
pytest tests/api/
pytest tests/core/
```

### Frontend Tests
```bash
# Run frontend tests
cd frontend
npm test

# Run E2E tests with Playwright
npx playwright test
```

### Integration Tests
```bash
# Run integration tests
docker compose exec backend pytest tests/integration/
```

## 📚 Documentation

### Module Documentation
- [Backend Agents](../backend/app/agents/README.md)
- [Backend API](../backend/app/api/README.md)
- [Backend Core](../backend/app/core/README.md)
- [Backend Services](../backend/app/services/README.md)
- [Frontend Components](../frontend/src/components/README.md)
- [Frontend Routes](../frontend/src/routes/README.md)
- [Frontend Contexts](../frontend/src/contexts/README.md)

### System Documentation
- [System Design](../docs/system-design.md)
- [Architecture](../docs/architecture.md)
- [Deployment](../docs/deployment/README.md)
- [Database](../docs/database/README.md)

## 🚀 Deployment

### Production Deployment

1. **Set up production environment**
   ```bash
   # Configure production environment variables
   cp .env.production .env
   ```

2. **Build and deploy**
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

3. **Set up reverse proxy (optional)**
   ```bash
   # Configure Traefik for HTTPS
   docker compose -f docker-compose.traefik.yml up -d
   ```

### Environment-Specific Configurations

- **Development**: `docker-compose.yml` + `docker-compose.override.yml`
- **Production**: `docker-compose.yml` + `docker-compose.prod.yml`
- **Traefik**: `docker-compose.traefik.yml`

## 🔍 Development

### Backend Development

1. **Start development server**
   ```bash
   cd backend
   fastapi run app/main.py --reload
   ```

2. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

3. **Generate new migration**
   ```bash
   alembic revision --autogenerate -m "Description"
   ```

### Frontend Development

1. **Start development server**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Generate API client**
   ```bash
   npm run generate-client
   ```

3. **Build for production**
   ```bash
   npm run build
   ```

### Code Quality

```bash
# Backend linting and formatting
cd backend
black .
isort .
flake8 .

# Frontend linting and formatting
cd frontend
npm run lint
npm run format
```

## 🐛 Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check PostgreSQL is running
   - Verify database credentials in .env
   - Run database migrations

2. **API connection errors**
   - Check backend is running on port 8000
   - Verify CORS settings
   - Check API key configurations

3. **Frontend build errors**
   - Clear node_modules and reinstall
   - Check Node.js version compatibility
   - Verify environment variables

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=debug

# Start with debug mode
docker compose up --build
```

## 📊 Monitoring

### Health Checks
- Backend: http://localhost:8000/api/v1/health
- Frontend: http://localhost:5173/health

### Logs
```bash
# View application logs
docker compose logs -f backend
docker compose logs -f frontend

# View specific service logs
docker compose logs -f postgres
docker compose logs -f redis
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   npm test
   pytest
   ```
5. **Commit your changes**
   ```bash
   git commit -m "Add your feature"
   ```
6. **Push to the branch**
   ```bash
   git push origin feature/your-feature
   ```
7. **Create a Pull Request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the [docs](../docs/) directory
- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions

## 🔄 Updates

### Updating Dependencies

```bash
# Backend
cd backend
uv sync --upgrade

# Frontend
cd frontend
npm update
```

### Database Updates

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Update description"
```
