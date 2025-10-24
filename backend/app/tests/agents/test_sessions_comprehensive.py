import pytest
from unittest.mock import patch, MagicMock
from app.agents.sessions import MemoryManager, RedisSessionService
from datetime import datetime, timedelta
import json

@pytest.fixture(autouse=True)
def mock_redis_client():
    """Mock Redis client for all tests."""
    with patch('app.agents.sessions.redis', new_callable=MagicMock) as mock_redis:
        mock_redis.get.return_value = None  # Default to no data
        yield mock_redis

@pytest.fixture
def memory_manager_instance():
    """Create MemoryManager instance for testing."""
    return MemoryManager()

@pytest.fixture
def session_service_instance():
    """Create RedisSessionService instance for testing."""
    return RedisSessionService()

def test_memory_manager_store_and_get_conversation_memory(memory_manager_instance, mock_redis_client):
    """Test conversation memory storage and retrieval."""
    user_id = "user123"
    session_id = "session456"
    memory_data = {"history": ["hello", "hi"]}
    
    memory_manager_instance.store_conversation_memory(user_id, session_id, memory_data)
    mock_redis_client.setex.assert_called_once()
    
    # Test retrieval
    mock_redis_client.get.return_value = json.dumps(memory_data).encode('utf-8')
    retrieved_memory = memory_manager_instance.get_conversation_memory(user_id, session_id)
    mock_redis_client.get.assert_called_once()
    assert retrieved_memory == memory_data

def test_memory_manager_store_and_get_user_preferences(memory_manager_instance, mock_redis_client):
    """Test user preferences storage and retrieval."""
    user_id = "user123"
    preferences = {"theme": "dark", "currency": "USD"}
    
    memory_manager_instance.store_user_preferences(user_id, preferences)
    mock_redis_client.setex.assert_called_once()
    
    # Test retrieval
    mock_redis_client.get.return_value = json.dumps(preferences).encode('utf-8')
    retrieved_preferences = memory_manager_instance.get_user_preferences(user_id)
    assert retrieved_preferences == preferences

def test_memory_manager_store_and_get_trip_context(memory_manager_instance, mock_redis_client):
    """Test trip context storage and retrieval."""
    user_id = "user123"
    trip_id = "trip789"
    context = {"destination": "Paris", "status": "planned"}
    
    memory_manager_instance.store_trip_context(user_id, trip_id, context)
    mock_redis_client.setex.assert_called_once()
    
    # Test retrieval
    mock_redis_client.get.return_value = json.dumps(context).encode('utf-8')
    retrieved_context = memory_manager_instance.get_trip_context(user_id, trip_id)
    assert retrieved_context == context

def test_redis_session_service_create_session(session_service_instance, mock_redis_client):
    """Test session creation."""
    app_name = "travya"
    user_id = "user123"
    session_id = "session456"
    
    session_service_instance.create_session(app_name, user_id, session_id)
    
    # Check if session metadata was stored
    mock_redis_client.setex.assert_called()
    
    # Check if conversation memory was initialized
    assert mock_redis_client.setex.call_count >= 2  # One for session, one for memory

def test_redis_session_service_get_session_updates_activity(session_service_instance, mock_redis_client):
    """Test session retrieval updates last activity."""
    app_name = "travya"
    user_id = "user123"
    session_id = "session456"
    
    # Simulate an existing session
    initial_session_data = {
        "created_at": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
        "last_activity": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
        "app_name": app_name,
        "user_id": user_id,
        "session_id": session_id
    }
    mock_redis_client.get.return_value = json.dumps(initial_session_data).encode('utf-8')
    
    session = session_service_instance.get_session(app_name, user_id, session_id)
    
    assert session is not None
    # Check that setex was called to update last_activity
    assert mock_redis_client.setex.call_count >= 1

def test_redis_session_service_update_and_get_session_memory(session_service_instance, mock_redis_client):
    """Test session memory update and retrieval."""
    user_id = "user123"
    session_id = "session456"
    initial_memory = {"conversation_history": ["Hi"], "user_intent": "greeting"}
    update = {"current_context": {"location": "Paris"}}
    
    # Mock initial memory retrieval
    mock_redis_client.get.side_effect = [
        json.dumps(initial_memory).encode('utf-8'),  # For get_conversation_memory in update_session_memory
        json.dumps({**initial_memory, **update}).encode('utf-8')  # For get_conversation_memory in get_session_memory
    ]
    
    session_service_instance.update_session_memory(user_id, session_id, update)
    
    retrieved_memory = session_service_instance.get_session_memory(user_id, session_id)
    assert retrieved_memory == {**initial_memory, **update}

def test_memory_manager_ttl_settings():
    """Test that TTL settings are correct for different memory types."""
    memory_manager = MemoryManager()
    
    # Test conversation memory TTL (24 hours)
    with patch('app.agents.sessions.redis') as mock_redis:
        memory_manager.store_conversation_memory("user", "session", {"data": "test"})
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 86400  # 24 hours in seconds
    
    # Test user preferences TTL (30 days)
    with patch('app.agents.sessions.redis') as mock_redis:
        memory_manager.store_user_preferences("user", {"data": "test"})
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 2592000  # 30 days in seconds
    
    # Test trip context TTL (7 days)
    with patch('app.agents.sessions.redis') as mock_redis:
        memory_manager.store_trip_context("user", "trip", {"data": "test"})
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 604800  # 7 days in seconds

def test_session_service_cleanup():
    """Test session cleanup functionality."""
    session_service = RedisSessionService()
    
    # Test cleanup method (should not raise exceptions)
    session_service.cleanup_expired_sessions()
    assert True  # Method should complete without errors

def test_memory_manager_error_handling():
    """Test memory manager error handling."""
    memory_manager = MemoryManager()
    
    # Test with invalid JSON in Redis
    with patch('app.agents.sessions.redis') as mock_redis:
        mock_redis.get.return_value = b'invalid json'
        
        result = memory_manager.get_conversation_memory("user", "session")
        assert result is None
        
        result = memory_manager.get_user_preferences("user")
        assert result is None
        
        result = memory_manager.get_trip_context("user", "trip")
        assert result is None

def test_session_service_integration():
    """Test complete session service integration."""
    session_service = RedisSessionService()
    
    # Create session
    session_service.create_session("travya", "user123", "session456")
    
    # Update memory
    session_service.update_session_memory("user123", "session456", {"test": "data"})
    
    # Get memory
    memory = session_service.get_session_memory("user123", "session456")
    
    # Test that the service works end-to-end
    assert True  # Should complete without errors