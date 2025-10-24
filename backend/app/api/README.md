# API Module

This module contains all the REST API endpoints for the Travya travel companion system. It's built using FastAPI and provides comprehensive API coverage for all system functionality.

## Architecture

The API module follows a modular structure with separate route files for different functional areas:

- **Authentication**: User login, registration, and session management
- **User Management**: User CRUD operations and profile management
- **Travel Services**: Core travel planning and booking functionality
- **AI Agents**: Agent-based travel assistance and recommendations
- **Documents**: File upload and document processing
- **Health**: System health monitoring and status endpoints

## Route Modules

### Authentication (`login.py`)
- User authentication endpoints
- JWT token management
- Password reset functionality
- Session handling

### User Management (`users.py`)
- User registration and profile management
- User CRUD operations
- Admin user management
- User settings and preferences

### Travel Services (`travel.py`, `ai_travel.py`)
- Travel planning endpoints
- Itinerary management
- Booking operations
- Travel recommendations

### AI Agents (`agents.py`, `agentic.py`, `simple_agentic.py`)
- Agent-based travel assistance
- Conversational AI endpoints
- Multi-modal input handling
- Real-time agent interactions

### Documents (`documents.py`)
- File upload and processing
- Document storage management
- Media handling for travel content

### Health & Monitoring (`health.py`, `monitoring.py`)
- System health checks
- Performance monitoring
- Service status endpoints
- Diagnostic information

### Utilities (`utils.py`)
- Common utility endpoints
- Helper functions
- System information
- Configuration endpoints

## API Structure

### Base URL
All API endpoints are prefixed with `/api/v1`

### Authentication
Most endpoints require authentication via JWT tokens in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Response Format
All API responses follow a consistent format:
```json
{
  "data": <response_data>,
  "message": "Success message",
  "status": "success"
}
```

### Error Handling
Errors are returned with appropriate HTTP status codes and error messages:
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

## Key Endpoints

### Authentication
- `POST /api/v1/login/access-token` - User login
- `POST /api/v1/login/test-token` - Token validation
- `POST /api/v1/login/recover-password` - Password recovery
- `POST /api/v1/login/reset-password` - Password reset

### Users
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user
- `GET /api/v1/users/` - List users (admin)
- `POST /api/v1/users/` - Create user (admin)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### Travel Services
- `POST /api/v1/travel/plan` - Plan a trip
- `GET /api/v1/travel/itineraries` - Get user itineraries
- `POST /api/v1/travel/book` - Book travel services
- `GET /api/v1/travel/recommendations` - Get travel recommendations

### AI Agents
- `POST /api/v1/agents/query` - Send query to AI agents
- `POST /api/v1/agents/chat` - Conversational AI interface
- `GET /api/v1/agents/status` - Get agent status
- `POST /api/v1/agents/stream` - Streaming agent responses

## Dependencies

### Core Dependencies
- FastAPI for API framework
- SQLAlchemy for database operations
- Pydantic for data validation
- JWT for authentication

### External Services
- AI/ML services for agent functionality
- External travel APIs (Amadeus, Google Maps, etc.)
- Payment processing APIs
- Email services for notifications

## Configuration

API configuration is managed through environment variables and the core settings system:

```python
# Example configuration
API_V1_STR = "/api/v1"
SECRET_KEY = "your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 8
```

## Testing

The API module includes comprehensive test coverage:

- Unit tests for individual endpoints
- Integration tests for API workflows
- Authentication and authorization tests
- Error handling and edge case testing

## Documentation

API documentation is automatically generated using FastAPI's built-in OpenAPI support:

- Interactive API docs available at `/docs`
- OpenAPI schema at `/openapi.json`
- ReDoc documentation at `/redoc`

## Security

- JWT-based authentication
- CORS configuration
- Input validation and sanitization
- Rate limiting and abuse prevention
- Secure password handling
