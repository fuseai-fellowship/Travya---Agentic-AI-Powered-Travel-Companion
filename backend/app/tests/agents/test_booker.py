import pytest
from unittest.mock import patch, MagicMock
from app.agents.booker import booker_agent
from app.agents.tools import amadeus_flight_search, stripe_payment
from google.adk.tools.tool_context import ToolContext

def test_booker_agent_definition():
    """Test booker agent definition."""
    assert booker_agent["name"] == "booker"
    assert "Handles bookings and payments" in booker_agent["description"]
    assert callable(booker_agent["function"])

def test_amadeus_flight_search_tool():
    """Test Amadeus flight search tool functionality."""
    tool_context = MagicMock(spec=ToolContext)
    origin = "NYC"
    destination = "LAX"
    date = "2024-08-15"
    
    result = amadeus_flight_search(tool_context, origin, destination, date)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert "id" in result[0]
    assert "price" in result[0]

def test_stripe_payment_tool():
    """Test Stripe payment tool functionality."""
    tool_context = MagicMock(spec=ToolContext)
    amount = 100.50
    description = "Test payment"
    
    result = stripe_payment(tool_context, amount, description)
    
    assert isinstance(result, dict)
    assert "payment_id" in result
    assert "status" in result
    assert result["status"] == "succeeded"

def test_booker_agent_function_call():
    """Test booker agent function call."""
    tool_context = MagicMock(spec=ToolContext)
    origin = "NYC"
    destination = "LAX"
    date = "2024-08-15"
    
    result = booker_agent["function"](tool_context, origin, destination, date)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert "id" in result[0]

def test_booking_workflow():
    """Test complete booking workflow."""
    tool_context = MagicMock(spec=ToolContext)
    
    # Search for flights
    flights = amadeus_flight_search(tool_context, "NYC", "LAX", "2024-08-15")
    assert len(flights) > 0
    
    # Process payment
    payment = stripe_payment(tool_context, 500.0, "Flight booking")
    assert payment["status"] == "succeeded"
    
    # Verify booking completion
    assert "payment_id" in payment
    assert "mock_flight_id" in flights[0]["id"]
