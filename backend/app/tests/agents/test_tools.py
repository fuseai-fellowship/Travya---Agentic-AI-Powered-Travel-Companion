import pytest
from unittest.mock import patch, MagicMock
from app.agents.tools import (
    rag_query, places_api, amadeus_flight_search, stripe_payment, weather_api,
    init_mock_vector_store, add_to_mock_vector_store
)
from google.adk.tools.tool_context import ToolContext
import numpy as np
import faiss

@pytest.fixture(autouse=True)
def setup_mock_vector_store():
    """Ensure mock_vector_store is reset for each test."""
    init_mock_vector_store()  # Initialize with default dimension
    yield
    # Cleanup after test

def test_init_mock_vector_store():
    """Test mock vector store initialization."""
    init_mock_vector_store(dimension=10)
    # The global variables are not directly accessible, but we can test the function works
    assert True  # Function should not raise an exception

def test_add_to_mock_vector_store():
    """Test adding to mock vector store."""
    embedding = [0.1] * 768
    payload = {"data": "test"}
    add_to_mock_vector_store(embedding, payload)
    # Function should not raise an exception
    assert True

def test_rag_query():
    """Test RAG query functionality."""
    add_to_mock_vector_store([0.1]*768, {"item": "beach"})
    add_to_mock_vector_store([0.9]*768, {"item": "mountain"})
    
    tool_context = MagicMock(spec=ToolContext)
    query = "beach vacation"
    
    with patch('numpy.random.rand', return_value=np.array([0.1]*768)) as mock_rand:
        results = rag_query(tool_context, query)
        assert "results" in results
        assert isinstance(results["results"], list)

def test_places_api():
    """Test Places API functionality."""
    tool_context = MagicMock(spec=ToolContext)
    location = "Paris"
    query = "Eiffel Tower"
    results = places_api(tool_context, location, query)
    
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["name"] == f"Mock {query} in {location}"

def test_amadeus_flight_search():
    """Test Amadeus flight search functionality."""
    tool_context = MagicMock(spec=ToolContext)
    origin = "NYC"
    destination = "LAX"
    date = "2024-12-25"
    results = amadeus_flight_search(tool_context, origin, destination, date)
    
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["id"] == "mock_flight_id"

def test_stripe_payment():
    """Test Stripe payment functionality."""
    tool_context = MagicMock(spec=ToolContext)
    amount = 100.50
    description = "Test payment"
    result = stripe_payment(tool_context, amount, description)
    
    assert isinstance(result, dict)
    assert result["payment_id"] == "mock_payment_id"
    assert result["status"] == "succeeded"

def test_weather_api():
    """Test weather API functionality."""
    tool_context = MagicMock(spec=ToolContext)
    location = "London"
    date = "2024-07-10"
    result = weather_api(tool_context, location, date)
    
    assert isinstance(result, dict)
    assert result["forecast"] == "Sunny, 75°F"

def test_tools_integration():
    """Test tools integration workflow."""
    tool_context = MagicMock(spec=ToolContext)
    
    # Test research workflow
    research_results = rag_query(tool_context, "Paris attractions")
    assert "results" in research_results
    
    places_results = places_api(tool_context, "Paris", "museums")
    assert len(places_results) > 0
    
    # Test booking workflow
    flights = amadeus_flight_search(tool_context, "NYC", "LAX", "2024-08-15")
    assert len(flights) > 0
    
    payment = stripe_payment(tool_context, 500.0, "Flight booking")
    assert payment["status"] == "succeeded"
    
    # Test weather check
    weather = weather_api(tool_context, "LAX", "2024-08-15")
    assert "forecast" in weather

def test_error_handling():
    """Test error handling in tools."""
    tool_context = MagicMock(spec=ToolContext)
    
    # Test with invalid inputs
    try:
        places_api(tool_context, "", "")
        assert True  # Should handle empty inputs gracefully
    except Exception:
        assert False  # Should not raise exceptions
    
    try:
        amadeus_flight_search(tool_context, "", "", "")
        assert True  # Should handle empty inputs gracefully
    except Exception:
        assert False  # Should not raise exceptions
