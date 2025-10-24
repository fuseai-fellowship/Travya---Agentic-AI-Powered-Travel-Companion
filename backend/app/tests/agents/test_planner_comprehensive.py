"""
Comprehensive tests for the planner agent.
"""
import pytest
from unittest.mock import Mock, patch
import json

from app.agents.planner import plan_trip, planner_agent
from app.tests.test_config import mock_llm


class TestPlannerAgent:
    """Test suite for planner agent functionality."""

    def test_planner_agent_initialization(self):
        """Test planner agent initialization."""
        assert planner_agent is not None
        assert planner_agent["name"] == "planner"
        assert planner_agent["description"] == "Creates detailed travel itineraries"
        assert callable(planner_agent["function"])

    @patch('app.agents.planner.call_llm')
    def test_plan_trip_success(self, mock_call_llm):
        """Test successful trip planning."""
        # Mock LLM response
        mock_itinerary = {
            "destination": "Paris",
            "duration_days": 3,
            "budget_category": "medium",
            "days": [
                {
                    "day": 1,
                    "theme": "Culture",
                    "places": ["Eiffel Tower", "Louvre Museum"],
                    "estimated_cost_usd": 150
                },
                {
                    "day": 2,
                    "theme": "Food",
                    "places": ["Local restaurants", "Food markets"],
                    "estimated_cost_usd": 100
                },
                {
                    "day": 3,
                    "theme": "Nature",
                    "places": ["Seine River", "Luxembourg Gardens"],
                    "estimated_cost_usd": 80
                }
            ],
            "total_estimated_cost": 330
        }
        
        mock_call_llm.return_value = json.dumps(mock_itinerary)
        
        goal = "Plan a 3-day trip to Paris focusing on culture and food"
        result = plan_trip(goal)
        
        assert isinstance(result, dict)
        assert result["destination"] == "Paris"
        assert result["duration_days"] == 3
        assert len(result["days"]) == 3
        assert result["total_estimated_cost"] == 330

    @patch('app.agents.planner.call_llm')
    def test_plan_trip_invalid_json(self, mock_call_llm):
        """Test trip planning with invalid JSON response."""
        # Mock LLM response with invalid JSON
        mock_call_llm.return_value = "This is not valid JSON"
        
        goal = "Plan a trip to Paris"
        result = plan_trip(goal)
        
        assert isinstance(result, dict)
        assert "raw_output" in result
        assert "error" in result
        assert result["error"] == "invalid_json"

    @patch('app.agents.planner.call_llm')
    def test_plan_trip_different_destinations(self, mock_call_llm):
        """Test trip planning for different destinations."""
        destinations = ["Tokyo", "London", "New York", "Rome", "Barcelona"]
        
        for destination in destinations:
            mock_itinerary = {
                "destination": destination,
                "duration_days": 5,
                "budget_category": "luxury",
                "days": [
                    {
                        "day": 1,
                        "theme": "Arrival",
                        "places": [f"Airport to {destination}"],
                        "estimated_cost_usd": 50
                    }
                ],
                "total_estimated_cost": 1000
            }
            
            mock_call_llm.return_value = json.dumps(mock_itinerary)
            
            goal = f"Plan a luxury trip to {destination}"
            result = plan_trip(goal)
            
            assert isinstance(result, dict)
            assert result["destination"] == destination
            assert result["budget_category"] == "luxury"

    @patch('app.agents.planner.call_llm')
    def test_plan_trip_different_durations(self, mock_call_llm):
        """Test trip planning for different durations."""
        durations = [1, 3, 7, 14, 30]
        
        for duration in durations:
            mock_itinerary = {
                "destination": "Paris",
                "duration_days": duration,
                "budget_category": "medium",
                "days": [
                    {
                        "day": i + 1,
                        "theme": f"Day {i + 1}",
                        "places": [f"Activity {i + 1}"],
                        "estimated_cost_usd": 100
                    } for i in range(duration)
                ],
                "total_estimated_cost": duration * 100
            }
            
            mock_call_llm.return_value = json.dumps(mock_itinerary)
            
            goal = f"Plan a {duration}-day trip to Paris"
            result = plan_trip(goal)
            
            assert isinstance(result, dict)
            assert result["duration_days"] == duration
            assert len(result["days"]) == duration

    @patch('app.agents.planner.call_llm')
    def test_plan_trip_different_budgets(self, mock_call_llm):
        """Test trip planning for different budget categories."""
        budget_categories = ["budget", "medium", "luxury"]
        
        for budget in budget_categories:
            mock_itinerary = {
                "destination": "Paris",
                "duration_days": 3,
                "budget_category": budget,
                "days": [
                    {
                        "day": 1,
                        "theme": "Sightseeing",
                        "places": ["Main attractions"],
                        "estimated_cost_usd": 100 if budget == "budget" else 200 if budget == "medium" else 500
                    }
                ],
                "total_estimated_cost": 300 if budget == "budget" else 600 if budget == "medium" else 1500
            }
            
            mock_call_llm.return_value = json.dumps(mock_itinerary)
            
            goal = f"Plan a {budget} trip to Paris"
            result = plan_trip(goal)
            
            assert isinstance(result, dict)
            assert result["budget_category"] == budget

    def test_planner_agent_function_execution(self):
        """Test planner agent function execution."""
        with patch('app.agents.planner.call_llm') as mock_call_llm:
            mock_itinerary = {
                "destination": "Test City",
                "duration_days": 2,
                "budget_category": "medium",
                "days": [],
                "total_estimated_cost": 200
            }
            mock_call_llm.return_value = json.dumps(mock_itinerary)
            
            result = planner_agent["function"]("Test goal")
            assert isinstance(result, dict)
            assert result["destination"] == "Test City"

    @patch('app.agents.planner.call_llm')
    def test_plan_trip_complex_itinerary(self, mock_call_llm):
        """Test trip planning with complex itinerary."""
        complex_itinerary = {
            "destination": "Europe",
            "duration_days": 14,
            "budget_category": "luxury",
            "days": [
                {
                    "day": 1,
                    "theme": "Arrival in Paris",
                    "places": ["Charles de Gaulle Airport", "Hotel check-in", "Eiffel Tower"],
                    "estimated_cost_usd": 300
                },
                {
                    "day": 2,
                    "theme": "Paris Culture",
                    "places": ["Louvre Museum", "Notre-Dame", "Seine River cruise"],
                    "estimated_cost_usd": 250
                },
                {
                    "day": 7,
                    "theme": "Travel to Rome",
                    "places": ["Flight to Rome", "Colosseum", "Roman Forum"],
                    "estimated_cost_usd": 400
                },
                {
                    "day": 14,
                    "theme": "Departure",
                    "places": ["Final shopping", "Airport transfer"],
                    "estimated_cost_usd": 150
                }
            ],
            "total_estimated_cost": 5000
        }
        
        mock_call_llm.return_value = json.dumps(complex_itinerary)
        
        goal = "Plan a 2-week luxury European tour"
        result = plan_trip(goal)
        
        assert isinstance(result, dict)
        assert result["destination"] == "Europe"
        assert result["duration_days"] == 14
        assert len(result["days"]) == 4  # Only specific days mentioned
        assert result["total_estimated_cost"] == 5000

    @patch('app.agents.planner.call_llm')
    def test_plan_trip_empty_goal(self, mock_call_llm):
        """Test trip planning with empty goal."""
        mock_itinerary = {
            "destination": "Unknown",
            "duration_days": 1,
            "budget_category": "budget",
            "days": [],
            "total_estimated_cost": 0
        }
        
        mock_call_llm.return_value = json.dumps(mock_itinerary)
        
        result = plan_trip("")
        assert isinstance(result, dict)

    @patch('app.agents.planner.call_llm')
    def test_plan_trip_special_characters(self, mock_call_llm):
        """Test trip planning with special characters in goal."""
        mock_itinerary = {
            "destination": "São Paulo",
            "duration_days": 3,
            "budget_category": "medium",
            "days": [
                {
                    "day": 1,
                    "theme": "Arrival",
                    "places": ["São Paulo Airport", "Hotel check-in"],
                    "estimated_cost_usd": 100
                }
            ],
            "total_estimated_cost": 500
        }
        
        mock_call_llm.return_value = json.dumps(mock_itinerary)
        
        goal = "Plan a trip to São Paulo, Brazil 🇧🇷"
        result = plan_trip(goal)
        
        assert isinstance(result, dict)
        assert result["destination"] == "São Paulo"

    def test_planner_agent_metadata(self):
        """Test planner agent metadata and structure."""
        assert "name" in planner_agent
        assert "description" in planner_agent
        assert "function" in planner_agent
        
        assert planner_agent["name"] == "planner"
        assert isinstance(planner_agent["description"], str)
        assert callable(planner_agent["function"])

    @patch('app.agents.planner.call_llm')
    def test_plan_trip_error_handling(self, mock_call_llm):
        """Test trip planning error handling."""
        # Test with LLM returning None
        mock_call_llm.return_value = None
        result = plan_trip("Test goal")
        assert isinstance(result, dict)
        assert "error" in result

    @patch('app.agents.planner.call_llm')
    def test_plan_trip_malformed_json(self, mock_call_llm):
        """Test trip planning with malformed JSON."""
        # Test with malformed JSON
        mock_call_llm.return_value = '{"destination": "Paris", "days": [{"day": 1}]'  # Missing closing brace
        
        result = plan_trip("Test goal")
        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "invalid_json"

    @pytest.mark.asyncio
    async def test_planner_agent_integration(self):
        """Test planner agent integration with other components."""
        with patch('app.agents.planner.call_llm') as mock_call_llm:
            mock_itinerary = {
                "destination": "Integration Test City",
                "duration_days": 1,
                "budget_category": "medium",
                "days": [],
                "total_estimated_cost": 100
            }
            mock_call_llm.return_value = json.dumps(mock_itinerary)
            
            # Test that the planner agent can be used in orchestrator context
            result = planner_agent["function"]("Integration test goal")
            assert isinstance(result, dict)
            assert "destination" in result
