"""
Comprehensive tests for the orchestrator agent.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from app.agents.orchestrator import execute_query, plan_trip_with_agents, orchestrator, runner
from app.tests.test_config import mock_redis, mock_llm, mock_agent


class TestOrchestratorAgent:
    """Test suite for orchestrator agent functionality."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator agent initialization."""
        assert orchestrator is not None
        assert orchestrator.name == "orchestrator"
        assert len(orchestrator.sub_agents) == 3  # research, planner, booker

    @pytest.mark.asyncio
    async def test_execute_query_basic(self, mock_redis):
        """Test basic query execution."""
        with patch('app.agents.orchestrator.memory_manager', mock_redis), \
             patch('app.agents.orchestrator.session_service') as mock_session_service, \
             patch('app.agents.orchestrator.runner') as mock_runner:
            
            # Mock the runner response
            mock_event = Mock()
            mock_event.is_final_response.return_value = True
            mock_event.content.parts = [Mock(text='{"response": "test response"}')]
            
            mock_runner.run_async.return_value = [mock_event]
            mock_session_service.update_session_memory.return_value = None
            
            query = {"text": "Plan a trip to Paris"}
            response = await execute_query("test_user", "test_session", query)
            
            assert isinstance(response, dict)
            assert "response" in response
            assert response["response"] == "test response"

    @pytest.mark.asyncio
    async def test_execute_query_with_memory_storage(self, mock_redis):
        """Test query execution with memory storage."""
        with patch('app.agents.orchestrator.memory_manager', mock_redis), \
             patch('app.agents.orchestrator.session_service') as mock_session_service, \
             patch('app.agents.orchestrator.runner') as mock_runner:
            
            # Mock the runner response
            mock_event = Mock()
            mock_event.is_final_response.return_value = True
            mock_event.content.parts = [Mock(text='{"response": "test response"}')]
            
            mock_runner.run_async.return_value = [mock_event]
            
            query = {"text": "Plan a trip to Paris"}
            response = await execute_query("test_user", "test_session", query)
            
            # Verify memory storage was called
            mock_redis.store_conversation_memory.assert_called_once()
            mock_session_service.update_session_memory.assert_called_once()
            
            assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_plan_trip_with_agents_success(self, mock_redis):
        """Test successful trip planning with all agents."""
        with patch('app.agents.orchestrator.memory_manager', mock_redis), \
             patch('app.agents.orchestrator.execute_query') as mock_execute_query:
            
            # Mock agent responses
            mock_research_response = {"attractions": ["Eiffel Tower", "Louvre"]}
            mock_planning_response = {"itinerary": [{"day": 1, "activities": ["Visit Eiffel Tower"]}]}
            mock_booking_response = {"flights": [{"price": 500, "airline": "Air France"}]}
            
            mock_execute_query.side_effect = [
                mock_research_response,
                mock_planning_response,
                mock_booking_response
            ]
            
            trip_request = {
                "destination": "Paris",
                "start_date": "2024-06-01",
                "end_date": "2024-06-05",
                "budget": 2000,
                "trip_type": "leisure",
                "interests": ["culture", "food"]
            }
            
            response = await plan_trip_with_agents("test_user", "test_session", trip_request)
            
            assert response["status"] == "success"
            assert "research" in response
            assert "itinerary" in response
            assert "bookings" in response
            assert "trip_summary" in response
            assert response["trip_summary"]["destination"] == "Paris"

    @pytest.mark.asyncio
    async def test_plan_trip_with_agents_error_handling(self, mock_redis):
        """Test trip planning error handling."""
        with patch('app.agents.orchestrator.memory_manager', mock_redis), \
             patch('app.agents.orchestrator.execute_query') as mock_execute_query:
            
            # Mock an error in the research phase
            mock_execute_query.side_effect = Exception("Research agent failed")
            
            trip_request = {
                "destination": "Paris",
                "start_date": "2024-06-01",
                "end_date": "2024-06-05",
                "budget": 2000,
                "trip_type": "leisure"
            }
            
            response = await plan_trip_with_agents("test_user", "test_session", trip_request)
            
            assert response["status"] == "error"
            assert "message" in response
            assert "Research agent failed" in response["message"]

    @pytest.mark.asyncio
    async def test_plan_trip_memory_storage(self, mock_redis):
        """Test trip planning with memory storage."""
        with patch('app.agents.orchestrator.memory_manager', mock_redis), \
             patch('app.agents.orchestrator.execute_query') as mock_execute_query:
            
            # Mock successful responses
            mock_execute_query.return_value = {"success": True}
            
            trip_request = {
                "destination": "Paris",
                "start_date": "2024-06-01",
                "end_date": "2024-06-05",
                "budget": 2000,
                "trip_type": "leisure"
            }
            
            response = await plan_trip_with_agents("test_user", "test_session", trip_request)
            
            # Verify memory storage was called for trip context
            assert mock_redis.store_trip_context.call_count >= 2  # Initial and final storage
            assert response["status"] == "success"

    def test_orchestrator_agent_structure(self):
        """Test orchestrator agent structure and configuration."""
        assert hasattr(orchestrator, 'name')
        assert hasattr(orchestrator, 'sub_agents')
        assert hasattr(orchestrator, 'description')
        assert hasattr(orchestrator, 'instruction')
        
        # Check sub-agents
        agent_names = [agent["name"] for agent in orchestrator.sub_agents]
        assert "research" in agent_names
        assert "planner" in agent_names
        assert "booker" in agent_names

    @pytest.mark.asyncio
    async def test_execute_query_with_different_query_types(self, mock_redis):
        """Test execute_query with different types of queries."""
        with patch('app.agents.orchestrator.memory_manager', mock_redis), \
             patch('app.agents.orchestrator.session_service') as mock_session_service, \
             patch('app.agents.orchestrator.runner') as mock_runner:
            
            # Mock the runner response
            mock_event = Mock()
            mock_event.is_final_response.return_value = True
            mock_event.content.parts = [Mock(text='{"response": "test response"}')]
            
            mock_runner.run_async.return_value = [mock_event]
            
            # Test different query types
            query_types = [
                {"type": "research", "destination": "Paris"},
                {"type": "plan", "itinerary": "3 days in Paris"},
                {"type": "book", "flights": "Paris to London"},
                {"text": "General travel question"}
            ]
            
            for query in query_types:
                response = await execute_query("test_user", "test_session", query)
                assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_plan_trip_with_agents_partial_failure(self, mock_redis):
        """Test trip planning with partial agent failures."""
        with patch('app.agents.orchestrator.memory_manager', mock_redis), \
             patch('app.agents.orchestrator.execute_query') as mock_execute_query:
            
            # Mock partial failure - research succeeds, planning fails
            mock_research_response = {"attractions": ["Eiffel Tower"]}
            
            def side_effect(*args, **kwargs):
                if "research" in str(args[2]):
                    return mock_research_response
                else:
                    raise Exception("Planning agent failed")
            
            mock_execute_query.side_effect = side_effect
            
            trip_request = {
                "destination": "Paris",
                "start_date": "2024-06-01",
                "end_date": "2024-06-05",
                "budget": 2000,
                "trip_type": "leisure"
            }
            
            response = await plan_trip_with_agents("test_user", "test_session", trip_request)
            
            assert response["status"] == "error"
            assert "Planning agent failed" in response["message"]

    def test_runner_initialization(self):
        """Test runner initialization."""
        assert runner is not None
        assert hasattr(runner, 'agent')
        assert hasattr(runner, 'app_name')
        assert hasattr(runner, 'session_service')

    @pytest.mark.asyncio
    async def test_execute_query_empty_query(self, mock_redis):
        """Test execute_query with empty query."""
        with patch('app.agents.orchestrator.memory_manager', mock_redis), \
             patch('app.agents.orchestrator.session_service') as mock_session_service, \
             patch('app.agents.orchestrator.runner') as mock_runner:
            
            # Mock the runner response
            mock_event = Mock()
            mock_event.is_final_response.return_value = True
            mock_event.content.parts = [Mock(text='{"response": "empty query response"}')]
            
            mock_runner.run_async.return_value = [mock_event]
            
            query = {}
            response = await execute_query("test_user", "test_session", query)
            
            assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_plan_trip_with_agents_minimal_request(self, mock_redis):
        """Test trip planning with minimal request data."""
        with patch('app.agents.orchestrator.memory_manager', mock_redis), \
             patch('app.agents.orchestrator.execute_query') as mock_execute_query:
            
            # Mock successful responses
            mock_execute_query.return_value = {"success": True}
            
            # Minimal trip request
            trip_request = {
                "destination": "Paris"
            }
            
            response = await plan_trip_with_agents("test_user", "test_session", trip_request)
            
            assert response["status"] == "success"
            assert "trip_summary" in response
