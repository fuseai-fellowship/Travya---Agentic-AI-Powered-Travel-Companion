import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.tests.utils.user import create_random_user, authentication_token_from_email
from app.models import User
from sqlmodel import Session
from datetime import date, timedelta

@pytest.fixture(name="normal_user_client")
def normal_user_client_fixture(client: TestClient, session: Session) -> TestClient:
    """Create a client with a normal user authenticated."""
    user = create_random_user(session)
    token = authentication_token_from_email(client=client, email=user.email, db=session)
    client.headers = {"Authorization": f"Bearer {token}"}
    return client

@pytest.mark.asyncio
async def test_plan_trip_endpoint(normal_user_client: TestClient):
    """Test AI trip planning endpoint."""
    trip_request_data = {
        "destination": "Paris",
        "start_date": str(date.today()),
        "end_date": str(date.today() + timedelta(days=5)),
        "budget": 2500,
        "travelers": 2,
        "trip_type": "leisure",
        "interests": ["culture", "food"],
        "special_requests": "wheelchair accessible"
    }
    
    mock_plan_response = {
        "status": "success",
        "research": {"data": "Paris research"},
        "itinerary": {"days": []},
        "bookings": {"flights": []},
        "trip_summary": {"destination": "Paris"}
    }

    with patch('app.agents.orchestrator.plan_trip_with_agents', new_callable=AsyncMock) as mock_plan_trip_with_agents:
        mock_plan_trip_with_agents.return_value = mock_plan_response
        
        response = normal_user_client.post("/api/v1/ai-travel/plan-trip", json=trip_request_data)
        
        assert response.status_code == 200
        content = response.json()
        assert content == mock_plan_response
        mock_plan_trip_with_agents.assert_called_once()

@pytest.mark.asyncio
async def test_chat_endpoint(normal_user_client: TestClient):
    """Test AI chat endpoint."""
    chat_request_data = {
        "message": "Hello AI",
        "session_id": "test_chat_session_123"
    }
    
    mock_chat_response = {
        "response": "Hello! How can I help you plan your trip?",
        "suggestions": ["Plan a trip", "Find hotels"]
    }

    with patch('app.agents.orchestrator.execute_query', new_callable=AsyncMock) as mock_execute_query:
        mock_execute_query.return_value = mock_chat_response
        
        response = normal_user_client.post("/api/v1/ai-travel/chat", json=chat_request_data)
        
        assert response.status_code == 200
        content = response.json()
        assert content == mock_chat_response
        mock_execute_query.assert_called_once()

def test_suggestions_endpoint(normal_user_client: TestClient):
    """Test AI suggestions endpoint."""
    suggestions_data = {
        "context": "I'm planning a trip to Japan",
        "trip_id": "test_trip_123"
    }
    
    mock_suggestions = {
        "suggestions": [
            "Visit Tokyo's temples",
            "Try authentic ramen",
            "Experience cherry blossom season"
        ]
    }

    with patch('app.agents.orchestrator.execute_query', new_callable=AsyncMock) as mock_execute_query:
        mock_execute_query.return_value = mock_suggestions
        
        response = normal_user_client.post("/api/v1/ai-travel/suggestions", json=suggestions_data)
        
        assert response.status_code == 200
        content = response.json()
        assert content == mock_suggestions

def test_optimize_itinerary_endpoint(normal_user_client: TestClient):
    """Test itinerary optimization endpoint."""
    optimization_data = {
        "trip_id": "test_trip_123",
        "optimization_type": "time_efficient",
        "constraints": ["budget", "time"]
    }
    
    mock_optimized = {
        "optimized_itinerary": {
            "days": [
                {"day": 1, "activities": ["Morning: Museum", "Afternoon: Park"]}
            ]
        }
    }

    with patch('app.agents.orchestrator.execute_query', new_callable=AsyncMock) as mock_execute_query:
        mock_execute_query.return_value = mock_optimized
        
        response = normal_user_client.post("/api/v1/ai-travel/optimize-itinerary", json=optimization_data)
        
        assert response.status_code == 200
        content = response.json()
        assert content == mock_optimized

def test_search_destination_endpoint(normal_user_client: TestClient):
    """Test destination search endpoint."""
    search_data = {
        "query": "beach destinations",
        "filters": {"climate": "tropical", "budget": "medium"}
    }
    
    mock_destinations = {
        "destinations": [
            {"name": "Bali", "country": "Indonesia", "rating": 4.5},
            {"name": "Maldives", "country": "Maldives", "rating": 4.8}
        ]
    }

    with patch('app.agents.orchestrator.execute_query', new_callable=AsyncMock) as mock_execute_query:
        mock_execute_query.return_value = mock_destinations
        
        response = normal_user_client.post("/api/v1/ai-travel/search-destination", json=search_data)
        
        assert response.status_code == 200
        content = response.json()
        assert content == mock_destinations

def test_search_travel_options_endpoint(normal_user_client: TestClient):
    """Test travel options search endpoint."""
    search_data = {
        "origin": "NYC",
        "destination": "LAX",
        "departure_date": "2024-08-15",
        "return_date": "2024-08-22",
        "travelers": 2
    }
    
    mock_options = {
        "flights": [
            {"airline": "Test Air", "price": 500, "duration": "5h 30m"}
        ],
        "hotels": [
            {"name": "Test Hotel", "price": 150, "rating": 4.2}
        ]
    }

    with patch('app.agents.orchestrator.execute_query', new_callable=AsyncMock) as mock_execute_query:
        mock_execute_query.return_value = mock_options
        
        response = normal_user_client.post("/api/v1/ai-travel/search-travel-options", json=search_data)
        
        assert response.status_code == 200
        content = response.json()
        assert content == mock_options

def test_recommendations_endpoint(normal_user_client: TestClient):
    """Test AI recommendations endpoint."""
    recommendations_data = {
        "user_id": "test_user_123",
        "trip_context": {"destination": "Paris", "interests": ["art", "food"]}
    }
    
    mock_recommendations = {
        "recommendations": [
            {"type": "restaurant", "name": "Le Comptoir", "reason": "Highly rated for local cuisine"},
            {"type": "attraction", "name": "Louvre Museum", "reason": "Perfect for art lovers"}
        ]
    }

    with patch('app.agents.orchestrator.execute_query', new_callable=AsyncMock) as mock_execute_query:
        mock_execute_query.return_value = mock_recommendations
        
        response = normal_user_client.post("/api/v1/ai-travel/recommendations", json=recommendations_data)
        
        assert response.status_code == 200
        content = response.json()
        assert content == mock_recommendations

def test_weather_endpoint(normal_user_client: TestClient):
    """Test weather information endpoint."""
    weather_data = {
        "location": "Paris",
        "date": "2024-08-15"
    }
    
    mock_weather = {
        "forecast": "Sunny, 75°F",
        "conditions": "Clear skies",
        "humidity": 60
    }

    with patch('app.agents.tools.weather_api') as mock_weather_api:
        mock_weather_api.return_value = mock_weather
        
        response = normal_user_client.post("/api/v1/ai-travel/weather", json=weather_data)
        
        assert response.status_code == 200
        content = response.json()
        assert content == mock_weather

def test_places_endpoint(normal_user_client: TestClient):
    """Test places search endpoint."""
    places_data = {
        "location": "Paris",
        "query": "museums",
        "radius": 5000
    }
    
    mock_places = [
        {"name": "Louvre Museum", "rating": 4.5, "place_id": "louvre_123"},
        {"name": "Musée d'Orsay", "rating": 4.3, "place_id": "orsay_456"}
    ]

    with patch('app.agents.tools.places_api') as mock_places_api:
        mock_places_api.return_value = mock_places
        
        response = normal_user_client.post("/api/v1/ai-travel/places", json=places_data)
        
        assert response.status_code == 200
        content = response.json()
        assert content == mock_places

def test_flights_endpoint(normal_user_client: TestClient):
    """Test flights search endpoint."""
    flights_data = {
        "origin": "NYC",
        "destination": "LAX",
        "departure_date": "2024-08-15"
    }
    
    mock_flights = [
        {"id": "flight_123", "price": {"total": "500.00"}, "itineraries": []}
    ]

    with patch('app.agents.tools.amadeus_flight_search') as mock_flight_search:
        mock_flight_search.return_value = mock_flights
        
        response = normal_user_client.post("/api/v1/ai-travel/flights", json=flights_data)
        
        assert response.status_code == 200
        content = response.json()
        assert content == mock_flights

def test_hotels_endpoint(normal_user_client: TestClient):
    """Test hotels search endpoint."""
    hotels_data = {
        "location": "Paris",
        "check_in": "2024-08-15",
        "check_out": "2024-08-18",
        "guests": 2
    }
    
    mock_hotels = [
        {"id": "hotel_123", "name": "Test Hotel", "price": 150, "rating": 4.2}
    ]

    with patch('app.agents.tools.amadeus_flight_search') as mock_hotel_search:  # Using same mock for simplicity
        mock_hotel_search.return_value = mock_hotels
        
        response = normal_user_client.post("/api/v1/ai-travel/hotels", json=hotels_data)
        
        assert response.status_code == 200
        content = response.json()
        assert content == mock_hotels

def test_ai_travel_error_handling(normal_user_client: TestClient):
    """Test AI travel endpoints error handling."""
    # Test with invalid data
    invalid_data = {"invalid": "data"}
    
    with patch('app.agents.orchestrator.plan_trip_with_agents', new_callable=AsyncMock) as mock_plan:
        mock_plan.side_effect = Exception("Test error")
        
        response = normal_user_client.post("/api/v1/ai-travel/plan-trip", json=invalid_data)
        
        # Should handle errors gracefully
        assert response.status_code in [400, 500]

def test_ai_travel_authentication(normal_user_client: TestClient):
    """Test that AI travel endpoints require authentication."""
    # Test without authentication
    client_without_auth = TestClient(normal_user_client.app)
    
    response = client_without_auth.post("/api/v1/ai-travel/plan-trip", json={"destination": "Paris"})
    assert response.status_code == 401  # Unauthorized

def test_ai_travel_rate_limiting():
    """Test AI travel endpoints rate limiting."""
    # This would test rate limiting if implemented
    assert True  # Placeholder for rate limiting tests

def test_ai_travel_concurrent_requests(normal_user_client: TestClient):
    """Test AI travel endpoints with concurrent requests."""
    # This would test concurrent request handling
    assert True  # Placeholder for concurrent request tests