# Travya: AI-Powered Travel Companion

## Overview

Travya is a comprehensive AI-powered travel companion application that provides personalized trip planning, real-time assistance, and collaborative travel management. Built with modern technologies including FastAPI, React, PostgreSQL, Redis, and Google's Agent Development Kit (ADK).

## Architecture

The application follows a microservices architecture with the following key components:

- **Frontend**: React + TypeScript + Vite + Chakra UI
- **Backend**: FastAPI + Python + SQLModel
- **Database**: PostgreSQL with Alembic migrations
- **Cache**: Redis for session management and memory
- **AI Agents**: Multi-agent system using Google ADK
- **External APIs**: Google Maps, Amadeus, Stripe, Weather APIs

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.10+ (for local development)

### Running the Application

```bash
# Clone the repository
git clone <repository-url>
cd travya

# Start all services
docker compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
# Database Admin: http://localhost:8080
```

## Module Documentation

- [AI Agents](./ai-agents/README.md) - Multi-agent AI system
- [Backend API](./backend-api/README.md) - FastAPI backend services
- [Frontend](./frontend/README.md) - React frontend application
- [Database](./database/README.md) - Database schema and models
- [External APIs](./external-apis/README.md) - Third-party integrations
- [Deployment](./deployment/README.md) - Production deployment guide

## Features

### Core Features
- 🤖 **AI-Powered Planning**: Multi-agent system for intelligent trip planning
- 🧠 **Memory & Context**: Persistent conversation memory and user preferences
- 👥 **Collaboration**: Real-time trip sharing and collaboration
- 📱 **Responsive UI**: Modern, mobile-friendly interface
- 🔒 **Authentication**: Secure user authentication and authorization
- 📊 **Analytics**: Trip analytics and insights

### AI Agents
- **Research Agent**: Gathers destination information and user preferences
- **Planner Agent**: Creates detailed itineraries and schedules
- **Booker Agent**: Handles flight, hotel, and activity bookings
- **Adapter Agent**: Real-time plan adaptation based on events

### External Integrations
- **Google Maps**: Location services and places API
- **Amadeus**: Flight and hotel search
- **Stripe**: Payment processing
- **Weather APIs**: Weather forecasts and conditions

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the GitHub repository.
