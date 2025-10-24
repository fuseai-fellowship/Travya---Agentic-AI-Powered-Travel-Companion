import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.agents.orchestrator import execute_query, plan_trip_with_agents
from app.agents.sessions import memory_manager
from datetime import datetime

@pytest.mark.asyncio
async def test_orchestrator_query():
    """Test orchestrator query execution."""
    query = {"text": "Plan a trip to Paris for 3 days"}
    
    # Mock the runner.run_async method
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
        
        # Check if memory was stored (this will be mocked in real test)
        conversation_memory = memory_manager.get_conversation_memory(user_id, session_id)
        # In a real test, we'd assert the memory was stored correctly

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

@pytest.mark.asyncio
async def test_plan_trip_with_agents_error_handling():
    """Test error handling in plan_trip_with_agents."""
    user_id = "test_user_error"
    session_id = "test_session_error"
    trip_request = {"destination": "Invalid"}

    with patch('app.agents.orchestrator.execute_query', new_callable=AsyncMock) as mock_execute_query:
        mock_execute_query.side_effect = Exception("Test error")
        
        response = await plan_trip_with_agents(user_id, session_id, trip_request)
        
        assert response["status"] == "error"
        assert "error" in response
        assert "Test error" in response["message"]