"""
Comprehensive tests for the research agent.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from app.agents.research import research_agent
from app.agents.tools import rag_query, places_api, init_mock_vector_store, add_to_mock_vector_store
from app.tests.test_config import mock_redis, mock_llm


class TestResearchAgent:
    """Test suite for research agent functionality."""

    def test_research_agent_initialization(self):
        """Test research agent initialization."""
        assert research_agent is not None
        assert research_agent["name"] == "research"
        assert research_agent["description"] == "Researches attractions and user preferences"
        assert callable(research_agent["function"])

    def test_rag_query_initialization(self):
        """Test RAG query function initialization."""
        # Test that rag_query is callable
        assert callable(rag_query)
        
        # Test with mock tool context
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = rag_query(mock_context, "test query")
        assert isinstance(result, dict)
        assert "results" in result

    def test_rag_query_with_mock_vector_store(self):
        """Test RAG query with mock vector store."""
        # Initialize mock vector store
        init_mock_vector_store(dimension=768)
        
        # Add some mock data
        mock_embedding = np.random.rand(768).astype(np.float32)
        mock_payload = {
            "text": "Paris is a beautiful city with many attractions",
            "metadata": {"city": "Paris", "type": "attraction"}
        }
        add_to_mock_vector_store(mock_embedding, mock_payload)
        
        # Test query
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = rag_query(mock_context, "Paris attractions")
        assert isinstance(result, dict)
        assert "results" in result

    def test_places_api_mock_implementation(self):
        """Test places API mock implementation."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = places_api(mock_context, "Paris", "restaurants")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "name" in result[0]
        assert "rating" in result[0]
        assert "place_id" in result[0]

    def test_places_api_different_locations(self):
        """Test places API with different locations and queries."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        test_cases = [
            ("Paris", "restaurants"),
            ("Tokyo", "hotels"),
            ("New York", "museums"),
            ("London", "shopping")
        ]
        
        for location, query in test_cases:
            result = places_api(mock_context, location, query)
            assert isinstance(result, list)
            assert len(result) > 0
            assert location in result[0]["name"]

    def test_rag_query_empty_vector_store(self):
        """Test RAG query with empty vector store."""
        # Reset vector store
        init_mock_vector_store(dimension=768)
        
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = rag_query(mock_context, "test query")
        assert isinstance(result, dict)
        assert "results" in result
        assert isinstance(result["results"], list)

    def test_rag_query_multiple_embeddings(self):
        """Test RAG query with multiple embeddings in vector store."""
        # Initialize and populate vector store
        init_mock_vector_store(dimension=768)
        
        # Add multiple mock embeddings
        for i in range(5):
            mock_embedding = np.random.rand(768).astype(np.float32)
            mock_payload = {
                "text": f"Test document {i}",
                "metadata": {"id": i, "type": "test"}
            }
            add_to_mock_vector_store(mock_embedding, mock_payload)
        
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = rag_query(mock_context, "test query")
        assert isinstance(result, dict)
        assert "results" in result
        assert isinstance(result["results"], list)

    def test_research_agent_function_execution(self):
        """Test research agent function execution."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = research_agent["function"](mock_context)
        assert isinstance(result, dict)
        assert "results" in result

    def test_rag_query_different_query_types(self):
        """Test RAG query with different types of queries."""
        init_mock_vector_store(dimension=768)
        
        # Add diverse mock data
        test_data = [
            ("Paris attractions", {"city": "Paris", "type": "attraction"}),
            ("Tokyo restaurants", {"city": "Tokyo", "type": "restaurant"}),
            ("London hotels", {"city": "London", "type": "hotel"}),
            ("New York museums", {"city": "New York", "type": "museum"})
        ]
        
        for text, metadata in test_data:
            mock_embedding = np.random.rand(768).astype(np.float32)
            mock_payload = {"text": text, "metadata": metadata}
            add_to_mock_vector_store(mock_embedding, mock_payload)
        
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test different query types
        queries = [
            "What to see in Paris?",
            "Best restaurants in Tokyo",
            "Where to stay in London?",
            "Museums in New York"
        ]
        
        for query in queries:
            result = rag_query(mock_context, query)
            assert isinstance(result, dict)
            assert "results" in result

    def test_places_api_error_handling(self):
        """Test places API error handling."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test with empty location
        result = places_api(mock_context, "", "restaurants")
        assert isinstance(result, list)
        
        # Test with empty query
        result = places_api(mock_context, "Paris", "")
        assert isinstance(result, list)

    def test_vector_store_operations(self):
        """Test vector store operations."""
        # Test initialization
        init_mock_vector_store(dimension=768)
        
        # Test adding embeddings
        mock_embedding = np.random.rand(768).astype(np.float32)
        mock_payload = {"text": "Test document", "metadata": {"type": "test"}}
        
        # This should not raise an exception
        add_to_mock_vector_store(mock_embedding, mock_payload)
        
        # Test querying
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = rag_query(mock_context, "test query")
        assert isinstance(result, dict)

    def test_research_agent_metadata(self):
        """Test research agent metadata and structure."""
        assert "name" in research_agent
        assert "description" in research_agent
        assert "function" in research_agent
        
        assert research_agent["name"] == "research"
        assert isinstance(research_agent["description"], str)
        assert callable(research_agent["function"])

    @pytest.mark.asyncio
    async def test_research_agent_integration(self):
        """Test research agent integration with other components."""
        # Test that the research agent can be used in orchestrator context
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test research function
        result = research_agent["function"](mock_context)
        assert isinstance(result, dict)
        
        # Test that result has expected structure
        assert "results" in result or "answer" in result

    def test_rag_query_performance(self):
        """Test RAG query performance with larger dataset."""
        # Initialize with larger dataset
        init_mock_vector_store(dimension=768)
        
        # Add many embeddings
        for i in range(100):
            mock_embedding = np.random.rand(768).astype(np.float32)
            mock_payload = {
                "text": f"Document {i}",
                "metadata": {"id": i, "type": "document"}
            }
            add_to_mock_vector_store(mock_embedding, mock_payload)
        
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test query performance
        import time
        start_time = time.time()
        result = rag_query(mock_context, "test query")
        end_time = time.time()
        
        assert isinstance(result, dict)
        assert end_time - start_time < 1.0  # Should complete within 1 second
