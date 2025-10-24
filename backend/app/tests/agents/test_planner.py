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

def test_plan_trip_handles_llm_error():
    """Test plan_trip handles LLM errors."""
    goal = "Plan a trip that causes LLM error."
    
    with patch('app.agents.planner.call_llm', side_effect=Exception("LLM Error")) as mock_call_llm:
        result = plan_trip(goal)
        mock_call_llm.assert_called_once()
        assert "error" in result
        assert "LLM Error" in result["error"]

def test_planner_agent_function_call():
    """Test planner agent function call."""
    goal = "Plan a weekend trip to Barcelona"
    
    with patch('app.agents.planner.call_llm', return_value='{"destination": "Barcelona", "days": []}') as mock_call_llm:
        result = planner_agent["function"](goal)
        mock_call_llm.assert_called_once()
        assert isinstance(result, dict)
