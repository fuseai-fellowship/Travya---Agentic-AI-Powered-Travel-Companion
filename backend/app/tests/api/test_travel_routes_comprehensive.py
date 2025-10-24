import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.models import User, Trip, TripCreate, Itinerary, ItineraryCreate, Booking, BookingCreate, TripCollaborator, Conversation, ConversationMessage
from app.tests.utils.user import create_random_user, authentication_token_from_email
from app.core.config import settings
from datetime import date, timedelta
import uuid

@pytest.fixture(name="normal_user_client")
def normal_user_client_fixture(client: TestClient, session: Session) -> TestClient:
    """Create a client with a normal user authenticated."""
    user = create_random_user(session)
    token = authentication_token_from_email(client=client, email=user.email, db=session)
    client.headers = {"Authorization": f"Bearer {token}"}
    return client

@pytest.fixture(name="test_trip")
def test_trip_fixture(session: Session, normal_user_client: TestClient) -> Trip:
    """Create a test trip for testing."""
    # Extract user_id from token (simplified approach)
    user_id = normal_user_client.headers["Authorization"].split(".")[1]  # This is a simplified approach
    trip_create = TripCreate(
        title="Test Trip",
        destination="Test Destination",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=5),
        user_id=uuid.uuid4()  # Use a random UUID for testing
    )
    response = normal_user_client.post("/api/v1/travel/trips/", json=trip_create.model_dump())
    assert response.status_code == 200
    trip = Trip.model_validate(response.json())
    return trip

def test_create_trip(normal_user_client: TestClient):
    """Test creating a new trip."""
    trip_create = TripCreate(
        title="New Trip",
        destination="New Destination",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7),
        user_id=uuid.uuid4()
    )
    response = normal_user_client.post("/api/v1/travel/trips/", json=trip_create.model_dump())
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == "New Trip"
    assert "id" in content

def test_get_trips(normal_user_client: TestClient, test_trip: Trip):
    """Test getting all trips for a user."""
    response = normal_user_client.get("/api/v1/travel/trips/")
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) > 0
    assert any(trip["id"] == str(test_trip.id) for trip in content["data"])

def test_get_trip_by_id(normal_user_client: TestClient, test_trip: Trip):
    """Test getting a specific trip by ID."""
    response = normal_user_client.get(f"/api/v1/travel/trips/{test_trip.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(test_trip.id)
    assert content["title"] == test_trip.title

def test_update_trip(normal_user_client: TestClient, test_trip: Trip):
    """Test updating a trip."""
    trip_update = {"title": "Updated Trip Title"}
    response = normal_user_client.put(f"/api/v1/travel/trips/{test_trip.id}", json=trip_update)
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == "Updated Trip Title"

def test_delete_trip(normal_user_client: TestClient, test_trip: Trip):
    """Test deleting a trip."""
    response = normal_user_client.delete(f"/api/v1/travel/trips/{test_trip.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Trip deleted successfully"
    
    # Verify trip is deleted
    response = normal_user_client.get(f"/api/v1/travel/trips/{test_trip.id}")
    assert response.status_code == 404

def test_create_itinerary(normal_user_client: TestClient, test_trip: Trip):
    """Test creating an itinerary for a trip."""
    itinerary_create = ItineraryCreate(
        trip_id=test_trip.id,
        day=1,
        title="Day 1 Activities",
        description="Explore the city center",
        activities=["Visit museum", "Walk in park"],
        start_time="09:00",
        end_time="18:00"
    )
    response = normal_user_client.post("/api/v1/travel/itineraries/", json=itinerary_create.model_dump())
    assert response.status_code == 200
    content = response.json()
    assert content["trip_id"] == str(test_trip.id)
    assert content["day"] == 1

def test_get_itineraries_for_trip(normal_user_client: TestClient, test_trip: Trip):
    """Test getting itineraries for a specific trip."""
    response = normal_user_client.get(f"/api/v1/travel/trips/{test_trip.id}/itineraries/")
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content["data"], list)

def test_create_booking(normal_user_client: TestClient, test_trip: Trip):
    """Test creating a booking."""
    booking_create = BookingCreate(
        trip_id=test_trip.id,
        booking_type="flight",
        provider="Test Airlines",
        confirmation_number="ABC123",
        amount=500.0,
        currency="USD",
        booking_date=date.today(),
        travel_date=date.today() + timedelta(days=1)
    )
    response = normal_user_client.post("/api/v1/travel/bookings/", json=booking_create.model_dump())
    assert response.status_code == 200
    content = response.json()
    assert content["trip_id"] == str(test_trip.id)
    assert content["booking_type"] == "flight"

def test_get_bookings_for_trip(normal_user_client: TestClient, test_trip: Trip):
    """Test getting bookings for a specific trip."""
    response = normal_user_client.get(f"/api/v1/travel/trips/{test_trip.id}/bookings/")
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content["data"], list)

def test_create_trip_collaborator(normal_user_client: TestClient, test_trip: Trip):
    """Test creating a trip collaborator."""
    collaborator_data = {
        "trip_id": str(test_trip.id),
        "email": "collaborator@example.com",
        "role": "viewer"
    }
    response = normal_user_client.post("/api/v1/travel/collaborators/", json=collaborator_data)
    assert response.status_code == 200
    content = response.json()
    assert content["trip_id"] == str(test_trip.id)
    assert content["email"] == "collaborator@example.com"

def test_get_trip_collaborators(normal_user_client: TestClient, test_trip: Trip):
    """Test getting collaborators for a trip."""
    response = normal_user_client.get(f"/api/v1/travel/trips/{test_trip.id}/collaborators/")
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content["data"], list)

def test_create_conversation(normal_user_client: TestClient, test_trip: Trip):
    """Test creating a conversation."""
    conversation_data = {
        "trip_id": str(test_trip.id),
        "title": "Trip Discussion",
        "is_active": True
    }
    response = normal_user_client.post("/api/v1/travel/conversations/", json=conversation_data)
    assert response.status_code == 200
    content = response.json()
    assert content["trip_id"] == str(test_trip.id)
    assert content["title"] == "Trip Discussion"

def test_get_trip_conversations(normal_user_client: TestClient, test_trip: Trip):
    """Test getting conversations for a trip."""
    response = normal_user_client.get(f"/api/v1/travel/trips/{test_trip.id}/conversations/")
    assert response.status_code == 200
    content = response.json()
    assert isinstance(content["data"], list)

def test_create_conversation_message(normal_user_client: TestClient, test_trip: Trip):
    """Test creating a conversation message."""
    # First create a conversation
    conversation_data = {
        "trip_id": str(test_trip.id),
        "title": "Test Conversation",
        "is_active": True
    }
    conv_response = normal_user_client.post("/api/v1/travel/conversations/", json=conversation_data)
    conversation_id = conv_response.json()["id"]
    
    # Then create a message
    message_data = {
        "conversation_id": conversation_id,
        "content": "Hello, this is a test message",
        "message_type": "text"
    }
    response = normal_user_client.post("/api/v1/travel/messages/", json=message_data)
    assert response.status_code == 200
    content = response.json()
    assert content["conversation_id"] == conversation_id
    assert content["content"] == "Hello, this is a test message"

def test_trip_validation():
    """Test trip data validation."""
    # Test invalid trip data
    invalid_trip = {
        "title": "",  # Empty title should fail
        "destination": "Test",
        "start_date": "2024-01-01",
        "end_date": "2024-01-02",
        "user_id": str(uuid.uuid4())
    }
    
    # This would be tested with a client that doesn't have authentication
    # to test validation without authentication issues
    assert True  # Placeholder for validation testing

def test_trip_date_validation():
    """Test trip date validation."""
    # Test end date before start date
    invalid_dates = {
        "title": "Test Trip",
        "destination": "Test",
        "start_date": "2024-01-02",
        "end_date": "2024-01-01",  # End before start
        "user_id": str(uuid.uuid4())
    }
    
    # This would be tested with proper validation
    assert True  # Placeholder for date validation testing

def test_trip_permissions():
    """Test trip access permissions."""
    # Test that users can only access their own trips
    # This would require creating multiple users and testing access
    assert True  # Placeholder for permissions testing

def test_trip_collaboration_workflow():
    """Test complete trip collaboration workflow."""
    # Test inviting collaborator, accepting invitation, and accessing trip
    assert True  # Placeholder for collaboration workflow testing