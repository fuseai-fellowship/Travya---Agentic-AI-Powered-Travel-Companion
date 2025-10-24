# Testing Documentation

## Overview

The Travya application uses a comprehensive testing strategy covering unit tests, integration tests, and end-to-end tests for all components including AI agents, API routes, database operations, and external API integrations.

## Testing Architecture

### Test Structure
```
backend/app/tests/
├── agents/                    # AI agent tests
│   ├── test_orchestrator.py
│   ├── test_research.py
│   ├── test_planner.py
│   ├── test_booker.py
│   ├── test_adapter.py
│   ├── test_tools.py
│   └── test_sessions_comprehensive.py
├── api/                       # API route tests
│   ├── test_travel_routes_comprehensive.py
│   └── test_ai_travel_routes_comprehensive.py
├── services/                  # Service layer tests
│   ├── test_external_apis.py
│   └── test_document_storage.py
├── models/                    # Database model tests
│   └── test_models.py
└── test_config.py            # Test configuration
```

## Test Configuration

### Test Database Setup
**File**: `backend/app/tests/test_config.py`

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import Base

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def session(test_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()
```

### Mock Services
```python
from unittest.mock import AsyncMock, MagicMock, patch
import redis

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock_redis = MagicMock(spec=redis.Redis)
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    return mock_redis

@pytest.fixture
def mock_llm():
    """Mock LLM service."""
    with patch('app.core.llm.call_llm') as mock:
        mock.return_value = "Mock LLM response"
        yield mock

@pytest.fixture
def mock_external_apis():
    """Mock external API services."""
    with patch('app.agents.tools.places_api') as mock_places, \
         patch('app.agents.tools.amadeus_flight_search') as mock_flights, \
         patch('app.agents.tools.stripe_payment') as mock_payment:
        
        mock_places.return_value = [{"name": "Mock Place", "rating": 4.5}]
        mock_flights.return_value = [{"id": "mock_flight", "price": "500.00"}]
        mock_payment.return_value = {"payment_id": "mock_payment", "status": "succeeded"}
        
        yield {
            "places": mock_places,
            "flights": mock_flights,
            "payment": mock_payment
        }
```

## Unit Testing

### AI Agent Tests

#### Orchestrator Agent Tests
**File**: `backend/app/tests/agents/test_orchestrator.py`

```python
import pytest
from unittest.mock import patch, AsyncMock
from app.agents.orchestrator import execute_query, plan_trip_with_agents

@pytest.mark.asyncio
async def test_orchestrator_query():
    """Test orchestrator query execution."""
    query = {"text": "Plan a trip to Paris for 3 days"}
    
    with patch('app.agents.orchestrator.runner.run_async', new_callable=AsyncMock) as mock_run_async:
        mock_run_async.return_value.__aiter__.return_value = [
            AsyncMock(is_final_response=lambda: True, content=AsyncMock(parts=[AsyncMock(text="Mock response")]))
        ]
        
        response = await execute_query(user_id="test_user", session_id="test_session", query=query)
        assert isinstance(response, str)
        assert response == "Mock response"

@pytest.mark.asyncio
async def test_execute_query_stores_memory():
    """Test that execute_query stores conversation memory."""
    user_id = "test_user_mem"
    session_id = "test_session_mem"
    query = {"text": "Test query for memory"}
    
    with patch('app.agents.orchestrator.runner.run_async', new_callable=AsyncMock) as mock_run_async:
        mock_run_async.return_value.__aiter__.return_value = [
            AsyncMock(is_final_response=lambda: True, content=AsyncMock(parts=[AsyncMock(text="Mock response")]))
        ]
        
        response = await execute_query(user_id, session_id, query)
        assert response == "Mock response"
        
        # Verify memory was stored
        conversation_memory = memory_manager.get_conversation_memory(user_id, session_id)
        assert conversation_memory is not None

@pytest.mark.asyncio
async def test_plan_trip_with_agents():
    """Test enhanced trip planning using all agents."""
    user_id = "test_user_trip"
    session_id = "test_session_trip"
    trip_request = {
        "destination": "London",
        "start_date": "2024-07-01",
        "end_date": "2024-07-07",
        "budget": 2000,
        "travelers": 2,
        "trip_type": "leisure",
        "interests": ["history", "food"],
        "special_requests": ""
    }
    
    with patch('app.agents.orchestrator.execute_query', new_callable=AsyncMock) as mock_execute_query:
        mock_execute_query.side_effect = [
            {"research_data": "mock research"},
            {"itinerary": "mock itinerary"},
            {"bookings": "mock bookings"}
        ]
        
        response = await plan_trip_with_agents(user_id, session_id, trip_request)
        
        assert response["status"] == "success"
        assert "research" in response
        assert "itinerary" in response
        assert "bookings" in response
        assert response["trip_summary"]["destination"] == "London"
```

#### Research Agent Tests
**File**: `backend/app/tests/agents/test_research.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from app.agents.research import research_agent
from app.agents.tools import rag_query, places_api, init_mock_vector_store, add_to_mock_vector_store

def test_research_agent_definition():
    """Test research agent definition."""
    assert research_agent["name"] == "research"
    assert "Researches attractions and user preferences" in research_agent["description"]
    assert callable(research_agent["function"])

def test_rag_query_tool():
    """Test RAG query tool functionality."""
    # Initialize mock vector store
    init_mock_vector_store()
    add_to_mock_vector_store([0.1]*768, {"name": "Eiffel Tower", "type": "attraction"})
    
    tool_context = MagicMock(spec=ToolContext)
    result = rag_query(tool_context, "Paris attractions")
    
    assert "results" in result
    assert isinstance(result["results"], list)

def test_places_api_tool():
    """Test Places API tool functionality."""
    tool_context = MagicMock(spec=ToolContext)
    location = "Paris"
    query = "Eiffel Tower"
    
    result = places_api(tool_context, location, query)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert "name" in result[0]
    assert "Mock" in result[0]["name"]  # Mock implementation
```

#### Planner Agent Tests
**File**: `backend/app/tests/agents/test_planner.py`

```python
import pytest
from unittest.mock import patch
from app.agents.planner import plan_trip, planner_agent
import json

def test_planner_agent_definition():
    """Test planner agent definition."""
    assert planner_agent["name"] == "planner"
    assert "Creates detailed travel itineraries" in planner_agent["description"]
    assert planner_agent["function"] == plan_trip

def test_plan_trip_generates_json_itinerary():
    """Test plan_trip generates JSON itinerary."""
    goal = "Plan a 3-day trip to Rome with a focus on history."
    mock_llm_response = json.dumps({
        "destination": "Rome",
        "duration_days": 3,
        "days": [
            {"day": 1, "theme": "Ancient Rome", "places": ["Colosseum", "Roman Forum"]},
            {"day": 2, "theme": "Vatican City", "places": ["St. Peter's Basilica", "Vatican Museums"]},
            {"day": 3, "theme": "Baroque Rome", "places": ["Trevi Fountain", "Pantheon"]}
        ]
    })
    
    with patch('app.agents.planner.call_llm', return_value=mock_llm_response) as mock_call_llm:
        result = plan_trip(goal)
        mock_call_llm.assert_called_once()
        assert isinstance(result, dict)
        assert result["destination"] == "Rome"
        assert len(result["days"]) == 3

def test_plan_trip_handles_invalid_json():
    """Test plan_trip handles invalid JSON response."""
    goal = "Plan a trip with invalid json response."
    mock_llm_response = "This is not valid JSON"
    
    with patch('app.agents.planner.call_llm', return_value=mock_llm_response) as mock_call_llm:
        result = plan_trip(goal)
        mock_call_llm.assert_called_once()
        assert "error" in result
        assert result["error"] == "invalid_json"
        assert result["raw_output"] == mock_llm_response
```

#### Booker Agent Tests
**File**: `backend/app/tests/agents/test_booker.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from app.agents.booker import booker_agent
from app.agents.tools import amadeus_flight_search, stripe_payment

def test_booker_agent_definition():
    """Test booker agent definition."""
    assert booker_agent["name"] == "booker"
    assert "Handles bookings and payments" in booker_agent["description"]
    assert callable(booker_agent["function"])

def test_amadeus_flight_search_tool():
    """Test Amadeus flight search tool."""
    tool_context = MagicMock(spec=ToolContext)
    origin = "NYC"
    destination = "LAX"
    date = "2024-07-01"
    
    result = amadeus_flight_search(tool_context, origin, destination, date)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert "id" in result[0]
    assert "price" in result[0]

def test_stripe_payment_tool():
    """Test Stripe payment tool."""
    tool_context = MagicMock(spec=ToolContext)
    amount = 500.0
    description = "Test payment"
    
    result = stripe_payment(tool_context, amount, description)
    
    assert "payment_id" in result
    assert "status" in result
    assert result["status"] == "succeeded"
```

### API Route Tests

#### Travel Routes Tests
**File**: `backend/app/tests/api/test_travel_routes_comprehensive.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from app.models import User, Trip, Itinerary, Booking
from app.core.config import settings

client = TestClient(app)

@pytest.fixture
def test_user(session):
    """Create test user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest.fixture
def test_trip(session, test_user):
    """Create test trip."""
    trip = Trip(
        title="Test Trip",
        destination="Paris",
        start_date="2024-07-01",
        end_date="2024-07-07",
        budget=2000.0,
        travelers=2,
        trip_type="leisure",
        status="planning",
        user_id=test_user.id
    )
    session.add(trip)
    await session.commit()
    await session.refresh(trip)
    return trip

@pytest.mark.asyncio
async def test_create_trip(session, test_user):
    """Test creating a new trip."""
    trip_data = {
        "title": "New Trip",
        "destination": "London",
        "start_date": "2024-08-01",
        "end_date": "2024-08-07",
        "budget": 1500.0,
        "travelers": 1,
        "trip_type": "business",
        "status": "planning"
    }
    
    response = client.post(
        "/api/v1/trips/",
        json=trip_data,
        headers={"Authorization": f"Bearer {test_user.id}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Trip"
    assert data["destination"] == "London"

@pytest.mark.asyncio
async def test_get_trips(session, test_user, test_trip):
    """Test getting user trips."""
    response = client.get(
        "/api/v1/trips/",
        headers={"Authorization": f"Bearer {test_user.id}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Test Trip"

@pytest.mark.asyncio
async def test_get_trip(session, test_user, test_trip):
    """Test getting specific trip."""
    response = client.get(
        f"/api/v1/trips/{test_trip.id}",
        headers={"Authorization": f"Bearer {test_user.id}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Trip"
    assert data["destination"] == "Paris"
```

#### AI Travel Routes Tests
**File**: `backend/app/tests/api/test_ai_travel_routes_comprehensive.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.api.main import app
from unittest.mock import patch

client = TestClient(app)

@pytest.mark.asyncio
async def test_plan_trip_endpoint():
    """Test AI trip planning endpoint."""
    trip_request = {
        "destination": "Tokyo",
        "start_date": "2024-09-01",
        "end_date": "2024-09-07",
        "budget": 3000,
        "travelers": 2,
        "trip_type": "leisure",
        "interests": ["culture", "food"],
        "special_requests": "Visit temples and try local cuisine"
    }
    
    with patch('app.api.routes.ai_travel.plan_trip_with_agents') as mock_plan:
        mock_plan.return_value = {
            "status": "success",
            "trip_summary": {
                "destination": "Tokyo",
                "duration_days": 6,
                "estimated_cost": 2800
            },
            "itinerary": {
                "days": [
                    {"day": 1, "activities": ["Senso-ji Temple", "Asakusa"]},
                    {"day": 2, "activities": ["Tokyo Skytree", "Shibuya"]}
                ]
            }
        }
        
        response = client.post(
            "/api/v1/ai/plan-trip",
            json=trip_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["trip_summary"]["destination"] == "Tokyo"

@pytest.mark.asyncio
async def test_chat_endpoint():
    """Test AI chat endpoint."""
    chat_request = {
        "message": "What's the weather like in Paris?",
        "context": {"trip_id": "test_trip_id"}
    }
    
    with patch('app.api.routes.ai_travel.execute_query') as mock_chat:
        mock_chat.return_value = "The weather in Paris is currently sunny with 22°C."
        
        response = client.post(
            "/api/v1/ai/chat",
            json=chat_request
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "weather" in data["response"].lower()
        assert "paris" in data["response"].lower()
```

### Service Layer Tests

#### External APIs Tests
**File**: `backend/app/tests/services/test_external_apis.py`

```python
import pytest
from unittest.mock import patch, AsyncMock
from app.services.external_apis import GoogleMapsService, AmadeusService, WeatherService

@pytest.mark.asyncio
async def test_google_maps_search_places():
    """Test Google Maps places search."""
    service = GoogleMapsService()
    
    with patch('app.services.external_apis.gmaps.places_nearby') as mock_search:
        mock_search.return_value = {
            "results": [
                {
                    "name": "Eiffel Tower",
                    "rating": 4.6,
                    "place_id": "ChIJLU7jZClu5kcR4PcOOO4p3I0"
                }
            ]
        }
        
        result = await service.search_places("Paris", "attractions")
        
        assert len(result) == 1
        assert result[0]["name"] == "Eiffel Tower"
        assert result[0]["rating"] == 4.6

@pytest.mark.asyncio
async def test_amadeus_flight_search():
    """Test Amadeus flight search."""
    service = AmadeusService()
    
    with patch('app.services.external_apis.amadeus.shopping.flight_offers_search.get') as mock_search:
        mock_search.return_value.data = [
            {
                "id": "test_flight",
                "price": {"total": "500.00"},
                "itineraries": []
            }
        ]
        
        result = await service.search_flights("NYC", "LAX", "2024-07-01")
        
        assert len(result) == 1
        assert result[0]["id"] == "test_flight"
        assert result[0]["price"]["total"] == "500.00"

@pytest.mark.asyncio
async def test_weather_service():
    """Test weather service."""
    service = WeatherService()
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "name": "Paris",
            "main": {"temp": 22, "humidity": 65},
            "weather": [{"description": "sunny"}],
            "wind": {"speed": 5.2}
        }
        mock_get.return_value = mock_response
        
        result = await service.get_weather("Paris")
        
        assert result["location"] == "Paris"
        assert result["temperature"] == 22
        assert result["description"] == "sunny"
```

## Integration Testing

### Database Integration Tests
```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Trip, Itinerary, Booking

@pytest.mark.asyncio
async def test_trip_creation_flow(session: AsyncSession):
    """Test complete trip creation flow."""
    # Create user
    user = User(
        email="integration@test.com",
        hashed_password="hashed_password",
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # Create trip
    trip = Trip(
        title="Integration Test Trip",
        destination="Barcelona",
        start_date="2024-10-01",
        end_date="2024-10-07",
        budget=2500.0,
        travelers=2,
        trip_type="leisure",
        status="planning",
        user_id=user.id
    )
    session.add(trip)
    await session.commit()
    await session.refresh(trip)
    
    # Create itinerary
    itinerary = Itinerary(
        trip_id=trip.id,
        day=1,
        title="Day 1: Arrival",
        description="Arrive in Barcelona and explore the Gothic Quarter",
        activities=["Check into hotel", "Walk around Gothic Quarter", "Dinner at local restaurant"],
        start_time="10:00",
        end_time="22:00"
    )
    session.add(itinerary)
    await session.commit()
    
    # Create booking
    booking = Booking(
        trip_id=trip.id,
        booking_type="flight",
        title="Flight to Barcelona",
        description="Round-trip flight from NYC to Barcelona",
        amount=800.0,
        currency="USD",
        status="confirmed",
        booking_reference="ABC123"
    )
    session.add(booking)
    await session.commit()
    
    # Verify relationships
    assert trip.user_id == user.id
    assert itinerary.trip_id == trip.id
    assert booking.trip_id == trip.id
    assert len(trip.itineraries) == 1
    assert len(trip.bookings) == 1
```

### API Integration Tests
```python
import pytest
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_complete_trip_planning_flow():
    """Test complete trip planning flow through API."""
    # 1. Create user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    user = response.json()
    
    # 2. Plan trip
    trip_request = {
        "destination": "Rome",
        "start_date": "2024-11-01",
        "end_date": "2024-11-07",
        "budget": 2000,
        "travelers": 2,
        "trip_type": "leisure",
        "interests": ["history", "art"],
        "special_requests": "Visit Vatican and Colosseum"
    }
    
    with patch('app.api.routes.ai_travel.plan_trip_with_agents') as mock_plan:
        mock_plan.return_value = {
            "status": "success",
            "trip_summary": {
                "destination": "Rome",
                "duration_days": 6,
                "estimated_cost": 1800
            },
            "itinerary": {
                "days": [
                    {"day": 1, "activities": ["Arrive in Rome", "Check into hotel"]},
                    {"day": 2, "activities": ["Colosseum", "Roman Forum"]}
                ]
            },
            "bookings": [
                {
                    "type": "flight",
                    "title": "Flight to Rome",
                    "amount": 600
                }
            ]
        }
        
        response = client.post(
            "/api/v1/ai/plan-trip",
            json=trip_request,
            headers={"Authorization": f"Bearer {user['id']}"}
        )
        assert response.status_code == 200
    
    # 3. Get planned trips
    response = client.get(
        "/api/v1/trips/",
        headers={"Authorization": f"Bearer {user['id']}"}
    )
    assert response.status_code == 200
    trips = response.json()
    assert len(trips["items"]) >= 1
```

## Performance Testing

### Load Testing
```python
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

async def load_test_api_endpoint(endpoint: str, num_requests: int = 100):
    """Load test an API endpoint."""
    async def make_request():
        start_time = time.time()
        # Make API request
        response = await client.get(endpoint)
        end_time = time.time()
        return {
            "status_code": response.status_code,
            "response_time": end_time - start_time
        }
    
    # Execute requests concurrently
    tasks = [make_request() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)
    
    # Calculate statistics
    response_times = [r["response_time"] for r in results]
    success_count = sum(1 for r in results if r["status_code"] == 200)
    
    return {
        "total_requests": num_requests,
        "successful_requests": success_count,
        "success_rate": success_count / num_requests,
        "avg_response_time": statistics.mean(response_times),
        "median_response_time": statistics.median(response_times),
        "p95_response_time": statistics.quantiles(response_times, n=20)[18],
        "p99_response_time": statistics.quantiles(response_times, n=100)[98]
    }

# Usage
@pytest.mark.asyncio
async def test_trips_endpoint_performance():
    """Test trips endpoint performance."""
    results = await load_test_api_endpoint("/api/v1/trips/", num_requests=50)
    
    assert results["success_rate"] >= 0.95  # 95% success rate
    assert results["avg_response_time"] < 1.0  # Under 1 second
    assert results["p95_response_time"] < 2.0  # 95% under 2 seconds
```

### Memory Testing
```python
import psutil
import os
import gc

def test_memory_usage():
    """Test memory usage during operations."""
    process = psutil.Process(os.getpid())
    
    # Get initial memory
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Perform memory-intensive operations
    for i in range(1000):
        # Create large objects
        data = {"data": "x" * 1000, "index": i}
        # Process data
        processed = data["data"].upper()
    
    # Force garbage collection
    gc.collect()
    
    # Get final memory
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Assert memory increase is reasonable
    assert memory_increase < 100  # Less than 100MB increase
```

## Test Data Management

### Fixtures
```python
@pytest.fixture
def sample_trip_data():
    """Sample trip data for testing."""
    return {
        "title": "Test Trip",
        "destination": "Paris",
        "start_date": "2024-07-01",
        "end_date": "2024-07-07",
        "budget": 2000.0,
        "travelers": 2,
        "trip_type": "leisure",
        "status": "planning"
    }

@pytest.fixture
def sample_itinerary_data():
    """Sample itinerary data for testing."""
    return {
        "day": 1,
        "title": "Day 1: Arrival",
        "description": "Arrive in Paris and explore the city",
        "activities": ["Check into hotel", "Visit Eiffel Tower", "Dinner at local restaurant"],
        "start_time": "10:00",
        "end_time": "22:00"
    }

@pytest.fixture
def sample_booking_data():
    """Sample booking data for testing."""
    return {
        "booking_type": "flight",
        "title": "Flight to Paris",
        "description": "Round-trip flight from NYC to Paris",
        "amount": 800.0,
        "currency": "USD",
        "status": "confirmed",
        "booking_reference": "ABC123"
    }
```

### Test Data Cleanup
```python
@pytest.fixture(autouse=True)
async def cleanup_test_data(session: AsyncSession):
    """Clean up test data after each test."""
    yield
    
    # Delete all test data
    await session.execute("DELETE FROM bookings WHERE title LIKE 'Test%'")
    await session.execute("DELETE FROM itineraries WHERE title LIKE 'Test%'")
    await session.execute("DELETE FROM trips WHERE title LIKE 'Test%'")
    await session.execute("DELETE FROM users WHERE email LIKE '%test%'")
    await session.commit()
```

## Test Coverage

### Coverage Configuration
```python
# pytest.ini
[tool:pytest]
addopts = --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80
testpaths = app/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### Coverage Reports
```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Continuous Integration

### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -e .
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./backend/coverage.xml
```

## Test Utilities

### Test Helpers
```python
# backend/app/tests/utils.py
import json
from typing import Dict, Any

def assert_response_structure(response_data: Dict[str, Any], expected_fields: list):
    """Assert response has expected structure."""
    for field in expected_fields:
        assert field in response_data, f"Missing field: {field}"

def assert_trip_data(trip_data: Dict[str, Any]):
    """Assert trip data is valid."""
    required_fields = ["title", "destination", "start_date", "end_date", "budget"]
    assert_response_structure(trip_data, required_fields)
    
    assert trip_data["budget"] > 0, "Budget must be positive"
    assert trip_data["start_date"] < trip_data["end_date"], "Start date must be before end date"

def create_test_user_data(email: str = "test@example.com") -> Dict[str, str]:
    """Create test user data."""
    return {
        "email": email,
        "password": "testpassword123",
        "full_name": "Test User"
    }

def create_test_trip_data(destination: str = "Paris") -> Dict[str, Any]:
    """Create test trip data."""
    return {
        "title": f"Test Trip to {destination}",
        "destination": destination,
        "start_date": "2024-07-01",
        "end_date": "2024-07-07",
        "budget": 2000.0,
        "travelers": 2,
        "trip_type": "leisure",
        "status": "planning"
    }
```

## Running Tests

### Command Line
```bash
# Run all tests
pytest

# Run specific test file
pytest app/tests/agents/test_orchestrator.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run with verbose output
pytest -v

# Run specific test
pytest app/tests/agents/test_orchestrator.py::test_orchestrator_query

# Run tests in parallel
pytest -n auto
```

### Docker
```bash
# Run tests in Docker
docker compose exec backend pytest

# Run tests with coverage in Docker
docker compose exec backend pytest --cov=app --cov-report=html

# Run specific test in Docker
docker compose exec backend pytest app/tests/agents/test_orchestrator.py
```

## Best Practices

### Test Organization
1. **One test per behavior**: Each test should verify one specific behavior
2. **Descriptive names**: Test names should clearly describe what is being tested
3. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification
4. **Independent tests**: Tests should not depend on each other
5. **Clean up**: Always clean up test data after tests

### Mocking Guidelines
1. **Mock external dependencies**: Mock external APIs, databases, and services
2. **Mock at boundaries**: Mock at the boundary of your system
3. **Verify interactions**: Assert that mocked methods were called correctly
4. **Use realistic data**: Use realistic mock data that matches production

### Performance Considerations
1. **Parallel execution**: Use parallel test execution when possible
2. **Database transactions**: Use database transactions for test isolation
3. **Resource cleanup**: Clean up resources after tests
4. **Memory management**: Monitor memory usage during tests

### Error Testing
1. **Test error conditions**: Test both success and failure scenarios
2. **Edge cases**: Test boundary conditions and edge cases
3. **Exception handling**: Verify that exceptions are handled correctly
4. **Error messages**: Verify that error messages are informative
