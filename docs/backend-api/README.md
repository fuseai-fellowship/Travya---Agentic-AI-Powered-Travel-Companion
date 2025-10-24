# Backend API Documentation

## Overview

The Backend API is built with FastAPI and provides comprehensive travel planning and management services. It includes authentication, AI-powered trip planning, travel management, and external API integrations.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│  API Routes     │────│  AI Agents      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         └──────────────│  Database       │────│  External APIs  │
                        │  (PostgreSQL)   │    │                 │
                        └─────────────────┘    └─────────────────┘
```

## API Structure

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Core Modules

### 1. Authentication & Users
**Files**: `backend/app/api/routes/login.py`, `backend/app/api/routes/users.py`

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login/access-token` | User login |
| POST | `/users/signup` | User registration |
| GET | `/users/me` | Get current user |
| PUT | `/users/me` | Update current user |
| POST | `/users/me/password` | Change password |

#### Example Usage

```python
# Login
response = requests.post(
    "http://localhost:8000/api/v1/login/access-token",
    data={"username": "user@example.com", "password": "password"}
)
token = response.json()["access_token"]

# Get current user
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    "http://localhost:8000/api/v1/users/me",
    headers=headers
)
```

### 2. AI Travel Planning
**File**: `backend/app/api/routes/ai_travel.py`

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai-travel/plan-trip` | Plan a complete trip |
| POST | `/ai-travel/chat` | AI chat assistance |
| POST | `/ai-travel/suggestions` | Get AI suggestions |
| POST | `/ai-travel/optimize-itinerary` | Optimize existing itinerary |
| GET | `/ai-travel/weather/{destination}` | Get weather info |
| GET | `/ai-travel/places/{destination}` | Search places |
| POST | `/ai-travel/search-travel-options` | Search flights/hotels |

#### Example Usage

```python
# Plan a trip
trip_data = {
    "destination": "Paris",
    "start_date": "2024-08-15",
    "end_date": "2024-08-20",
    "budget": 2500,
    "travelers": 2,
    "trip_type": "leisure",
    "interests": ["culture", "food"],
    "special_requests": "wheelchair accessible"
}

response = requests.post(
    "http://localhost:8000/api/v1/ai-travel/plan-trip",
    json=trip_data,
    headers=headers
)
```

### 3. Travel Management
**File**: `backend/app/api/routes/travel.py`

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/travel/trips` | Get user trips |
| POST | `/travel/trips` | Create new trip |
| GET | `/travel/trips/{trip_id}` | Get trip details |
| PUT | `/travel/trips/{trip_id}` | Update trip |
| DELETE | `/travel/trips/{trip_id}` | Delete trip |
| GET | `/travel/trips/{trip_id}/itineraries` | Get trip itineraries |
| POST | `/travel/trips/{trip_id}/itineraries` | Create itinerary |
| GET | `/travel/trips/{trip_id}/bookings` | Get trip bookings |
| POST | `/travel/trips/{trip_id}/bookings` | Create booking |

#### Example Usage

```python
# Create a trip
trip_data = {
    "title": "Paris Adventure",
    "destination": "Paris, France",
    "start_date": "2024-08-15",
    "end_date": "2024-08-20",
    "budget": 2500,
    "description": "A wonderful trip to Paris"
}

response = requests.post(
    "http://localhost:8000/api/v1/travel/trips",
    json=trip_data,
    headers=headers
)
trip_id = response.json()["id"]

# Add itinerary
itinerary_data = {
    "trip_id": trip_id,
    "day": 1,
    "title": "Day 1: Arrival and City Tour",
    "description": "Explore the city center",
    "activities": ["Visit Eiffel Tower", "Walk along Champs-Élysées"],
    "start_time": "09:00",
    "end_time": "18:00"
}

response = requests.post(
    "http://localhost:8000/api/v1/travel/itineraries",
    json=itinerary_data,
    headers=headers
)
```

### 4. Document Management
**File**: `backend/app/api/routes/documents.py`

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/upload` | Upload document |
| GET | `/documents/{document_id}` | Get document info |
| GET | `/documents/{document_id}/download` | Download document |
| GET | `/documents/trip/{trip_id}` | Get trip documents |
| POST | `/documents/trip/{trip_id}/upload` | Upload trip document |

### 5. Agent Management
**File**: `backend/app/api/routes/agents.py`

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents/query` | Execute agent query |
| POST | `/agents/sessions` | Create agent session |
| GET | `/agents/sessions/{session_id}` | Get session info |
| POST | `/agents/index/populate` | Populate knowledge index |

## Data Models

### Trip Model

```python
class Trip(BaseModel):
    id: UUID
    title: str
    destination: str
    start_date: date
    end_date: date
    budget: Optional[float]
    description: Optional[str]
    status: TripStatus
    trip_type: TripType
    user_id: UUID
    created_at: datetime
    updated_at: datetime
```

### Itinerary Model

```python
class Itinerary(BaseModel):
    id: UUID
    trip_id: UUID
    day: int
    title: str
    description: str
    activities: List[str]
    start_time: str
    end_time: str
    location: Optional[str]
    created_at: datetime
```

### Booking Model

```python
class Booking(BaseModel):
    id: UUID
    trip_id: UUID
    booking_type: str  # "flight", "hotel", "activity"
    provider: str
    confirmation_number: str
    amount: float
    currency: str
    booking_date: date
    travel_date: date
    status: BookingStatus
```

## Error Handling

### Standard Error Responses

```json
{
    "detail": "Error message",
    "error_code": "ERROR_CODE",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common Error Codes

- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Configuration

### Environment Variables

```bash
# Database
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=travya
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs
GOOGLE_MAPS_API_KEY=your-key
AMADEUS_CLIENT_ID=your-id
AMADEUS_CLIENT_SECRET=your-secret
STRIPE_SECRET_KEY=your-key

# Redis
REDIS_URL=redis://localhost:6379/0

# File Storage
DOCUMENT_STORAGE_PATH=/app/uploads
MAX_FILE_SIZE=10485760  # 10MB
```

## Database Schema

### Key Tables

- **users**: User accounts and profiles
- **trips**: Travel plans and itineraries
- **itineraries**: Daily activity schedules
- **bookings**: Flight, hotel, and activity bookings
- **trip_collaborators**: Shared trip access
- **conversations**: AI chat sessions
- **conversation_messages**: Chat message history
- **documents**: File attachments

### Relationships

```
users (1) ──→ (many) trips
trips (1) ──→ (many) itineraries
trips (1) ──→ (many) bookings
trips (1) ──→ (many) trip_collaborators
trips (1) ──→ (many) conversations
conversations (1) ──→ (many) conversation_messages
```

## Testing

### Running Tests

```bash
# All tests
python -m pytest

# Specific module
python -m pytest app/tests/api/routes/

# With coverage
python -m pytest --cov=app --cov-report=html
```

### Test Structure

```
app/tests/
├── api/
│   ├── routes/
│   │   ├── test_login.py
│   │   ├── test_users.py
│   │   ├── test_travel.py
│   │   └── test_ai_travel.py
│   └── test_main.py
├── crud/
│   └── test_user.py
├── agents/
│   ├── test_orchestrator.py
│   ├── test_research.py
│   ├── test_planner.py
│   ├── test_booker.py
│   └── test_adapter.py
└── conftest.py
```

## Development

### Adding New Endpoints

1. Create route file in `app/api/routes/`
2. Define Pydantic models for request/response
3. Implement CRUD operations
4. Add to main router in `app/api/main.py`
5. Create comprehensive tests
6. Update API documentation

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Document all public functions
- Write comprehensive tests
- Use async/await for I/O operations

## Performance

### Optimization Tips

1. **Database Queries**: Use proper indexing and avoid N+1 queries
2. **Caching**: Implement Redis caching for frequently accessed data
3. **Async Operations**: Use async/await for I/O operations
4. **Pagination**: Implement pagination for large datasets
5. **Rate Limiting**: Add rate limiting for external API calls

### Monitoring

- Use FastAPI's built-in metrics
- Monitor database query performance
- Track external API response times
- Monitor memory usage and Redis performance

## Security

### Best Practices

1. **Authentication**: Use JWT tokens with proper expiration
2. **Authorization**: Implement role-based access control
3. **Input Validation**: Validate all inputs using Pydantic
4. **SQL Injection**: Use SQLModel ORM to prevent SQL injection
5. **CORS**: Configure CORS properly for frontend integration
6. **Rate Limiting**: Implement rate limiting to prevent abuse

### Security Headers

```python
# Add security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```
