import pytest
from unittest.mock import patch, MagicMock
from app.agents.research import research_agent
from app.agents.tools import rag_query, places_api
from google.adk.tools.tool_context import ToolContext

def test_research_agent_definition():
    """Test research agent definition."""
    assert research_agent["name"] == "research"
    assert "Researches attractions and user preferences" in research_agent["description"]
    assert callable(research_agent["function"])

def test_rag_query_tool():
    """Test RAG query tool functionality."""
    # First initialize and add some data to the mock vector store
    from app.agents.tools import init_mock_vector_store, add_to_mock_vector_store
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

def test_research_agent_function_call():
    """Test research agent function call."""
    # First initialize and add some data to the mock vector store
    from app.agents.tools import init_mock_vector_store, add_to_mock_vector_store
    init_mock_vector_store()
    add_to_mock_vector_store([0.1]*768, {"name": "Eiffel Tower", "type": "attraction"})
    
    tool_context = MagicMock(spec=ToolContext)
    result = research_agent["function"](tool_context, "Paris attractions")
    
    assert "results" in result
    assert isinstance(result["results"], list)
