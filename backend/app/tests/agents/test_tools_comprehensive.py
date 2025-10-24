"""
Comprehensive tests for agent tools.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import faiss

from app.agents.tools import (
    init_mock_vector_store, 
    add_to_mock_vector_store, 
    rag_query, 
    places_api, 
    amadeus_flight_search, 
    stripe_payment,
    weather_api
)
from app.tests.test_config import mock_llm


class TestAgentTools:
    """Test suite for agent tools functionality."""

    def test_init_mock_vector_store(self):
        """Test mock vector store initialization."""
        # Test with default dimension
        init_mock_vector_store()
        
        # Test with custom dimension
        init_mock_vector_store(dimension=512)
        
        # Test with different dimensions
        for dim in [128, 256, 512, 768, 1024]:
            init_mock_vector_store(dimension=dim)

    def test_add_to_mock_vector_store(self):
        """Test adding embeddings to mock vector store."""
        # Initialize vector store
        init_mock_vector_store(dimension=768)
        
        # Test adding single embedding
        embedding = np.random.rand(768).astype(np.float32)
        payload = {"text": "Test document", "metadata": {"type": "test"}}
        
        add_to_mock_vector_store(embedding, payload)
        
        # Test adding multiple embeddings
        for i in range(10):
            embedding = np.random.rand(768).astype(np.float32)
            payload = {"text": f"Document {i}", "metadata": {"id": i}}
            add_to_mock_vector_store(embedding, payload)

    def test_rag_query_basic(self):
        """Test basic RAG query functionality."""
        # Initialize and populate vector store
        init_mock_vector_store(dimension=768)
        
        # Add test data
        for i in range(5):
            embedding = np.random.rand(768).astype(np.float32)
            payload = {
                "text": f"Document {i} about travel",
                "metadata": {"id": i, "topic": "travel"}
            }
            add_to_mock_vector_store(embedding, payload)
        
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = rag_query(mock_context, "travel information")
        assert isinstance(result, dict)
        assert "results" in result
        assert isinstance(result["results"], list)

    def test_rag_query_empty_store(self):
        """Test RAG query with empty vector store."""
        init_mock_vector_store(dimension=768)
        
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = rag_query(mock_context, "test query")
        assert isinstance(result, dict)
        assert "results" in result
        assert isinstance(result["results"], list)

    def test_rag_query_different_queries(self):
        """Test RAG query with different types of queries."""
        init_mock_vector_store(dimension=768)
        
        # Add diverse test data
        test_data = [
            ("Paris attractions", {"city": "Paris", "type": "attraction"}),
            ("Tokyo restaurants", {"city": "Tokyo", "type": "restaurant"}),
            ("London hotels", {"city": "London", "type": "hotel"}),
            ("New York museums", {"city": "New York", "type": "museum"}),
            ("Rome history", {"city": "Rome", "type": "history"})
        ]
        
        for text, metadata in test_data:
            embedding = np.random.rand(768).astype(np.float32)
            payload = {"text": text, "metadata": metadata}
            add_to_mock_vector_store(embedding, payload)
        
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        queries = [
            "What to see in Paris?",
            "Best restaurants in Tokyo",
            "Where to stay in London?",
            "Museums in New York",
            "Historical sites in Rome"
        ]
        
        for query in queries:
            result = rag_query(mock_context, query)
            assert isinstance(result, dict)
            assert "results" in result

    def test_places_api_basic(self):
        """Test basic places API functionality."""
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
        """Test places API with different locations."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        locations = ["Paris", "Tokyo", "London", "New York", "Rome", "Barcelona"]
        query_types = ["restaurants", "hotels", "museums", "attractions", "shopping"]
        
        for location in locations:
            for query_type in query_types:
                result = places_api(mock_context, location, query_type)
                assert isinstance(result, list)
                assert len(result) > 0
                assert location in result[0]["name"]

    def test_amadeus_flight_search_basic(self):
        """Test basic Amadeus flight search functionality."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = amadeus_flight_search(mock_context, "JFK", "LAX", "2024-06-01")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "id" in result[0]
        assert "price" in result[0]
        assert "itineraries" in result[0]

    def test_amadeus_flight_search_different_routes(self):
        """Test Amadeus flight search with different routes."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        routes = [
            ("JFK", "LAX", "2024-06-01"),
            ("LHR", "CDG", "2024-07-15"),
            ("NRT", "ICN", "2024-08-20"),
            ("SYD", "MEL", "2024-09-10")
        ]
        
        for origin, destination, date in routes:
            result = amadeus_flight_search(mock_context, origin, destination, date)
            assert isinstance(result, list)
            assert len(result) > 0

    def test_stripe_payment_basic(self):
        """Test basic Stripe payment functionality."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = stripe_payment(mock_context, 100.50, "Test payment")
        
        assert isinstance(result, dict)
        assert "payment_id" in result
        assert "status" in result
        assert result["status"] == "succeeded"

    def test_stripe_payment_different_amounts(self):
        """Test Stripe payment with different amounts."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        amounts = [10.00, 100.50, 1000.00, 5000.99, 0.01]
        
        for amount in amounts:
            result = stripe_payment(mock_context, amount, f"Payment for ${amount}")
            assert isinstance(result, dict)
            assert "payment_id" in result

    def test_weather_api_basic(self):
        """Test basic weather API functionality."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = weather_api(mock_context, "Paris", "2024-06-01")
        
        assert isinstance(result, dict)
        assert "forecast" in result

    def test_weather_api_different_locations(self):
        """Test weather API with different locations."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        locations = ["Paris", "Tokyo", "London", "New York", "Sydney"]
        dates = ["2024-06-01", "2024-07-15", "2024-08-20", "2024-09-10"]
        
        for location in locations:
            for date in dates:
                result = weather_api(mock_context, location, date)
                assert isinstance(result, dict)
                assert "forecast" in result

    def test_vector_store_performance(self):
        """Test vector store performance with large datasets."""
        import time
        
        # Initialize vector store
        init_mock_vector_store(dimension=768)
        
        # Add many embeddings
        start_time = time.time()
        for i in range(1000):
            embedding = np.random.rand(768).astype(np.float32)
            payload = {"text": f"Document {i}", "metadata": {"id": i}}
            add_to_mock_vector_store(embedding, payload)
        add_time = time.time() - start_time
        
        # Query performance
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        start_time = time.time()
        result = rag_query(mock_context, "test query")
        query_time = time.time() - start_time
        
        assert isinstance(result, dict)
        assert add_time < 5.0  # Should add 1000 embeddings quickly
        assert query_time < 1.0  # Should query quickly

    def test_rag_query_with_similar_embeddings(self):
        """Test RAG query with similar embeddings."""
        init_mock_vector_store(dimension=768)
        
        # Add similar embeddings
        base_embedding = np.random.rand(768).astype(np.float32)
        for i in range(10):
            # Create similar embeddings by adding small noise
            noise = np.random.normal(0, 0.1, 768).astype(np.float32)
            similar_embedding = base_embedding + noise
            payload = {"text": f"Similar document {i}", "metadata": {"similarity": i}}
            add_to_mock_vector_store(similar_embedding, payload)
        
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = rag_query(mock_context, "test query")
        assert isinstance(result, dict)
        assert "results" in result

    def test_tools_error_handling(self):
        """Test tools error handling with invalid inputs."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test with None inputs
        result = places_api(mock_context, None, None)
        assert isinstance(result, list)
        
        result = amadeus_flight_search(mock_context, None, None, None)
        assert isinstance(result, list)
        
        result = stripe_payment(mock_context, None, None)
        assert isinstance(result, dict)
        
        result = weather_api(mock_context, None, None)
        assert isinstance(result, dict)

    def test_rag_query_with_empty_context(self):
        """Test RAG query with empty context."""
        init_mock_vector_store(dimension=768)
        
        # Add some data
        embedding = np.random.rand(768).astype(np.float32)
        payload = {"text": "Test document", "metadata": {"type": "test"}}
        add_to_mock_vector_store(embedding, payload)
        
        # Test with None context
        result = rag_query(None, "test query")
        assert isinstance(result, dict)

    def test_tools_with_unicode_inputs(self):
        """Test tools with Unicode inputs."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test with Unicode strings
        unicode_locations = ["北京", "東京", "Londres", "París", "Roma"]
        unicode_queries = ["餐厅", "ホテル", "museos", "attractions", "ristoranti"]
        
        for location in unicode_locations:
            result = places_api(mock_context, location, "restaurants")
            assert isinstance(result, list)
        
        for query in unicode_queries:
            result = places_api(mock_context, "Paris", query)
            assert isinstance(result, list)

    def test_vector_store_dimension_consistency(self):
        """Test vector store dimension consistency."""
        # Test with different dimensions
        for dim in [128, 256, 512, 768, 1024]:
            init_mock_vector_store(dimension=dim)
            
            # Add embedding with correct dimension
            embedding = np.random.rand(dim).astype(np.float32)
            payload = {"text": f"Document for dim {dim}", "metadata": {"dimension": dim}}
            add_to_mock_vector_store(embedding, payload)
            
            # Query should work
            mock_context = Mock()
            mock_context.user_id = "test_user"
            mock_context.session_id = "test_session"
            
            result = rag_query(mock_context, f"query for dim {dim}")
            assert isinstance(result, dict)

    def test_tools_concurrent_access(self):
        """Test tools with concurrent access simulation."""
        import threading
        import time
        
        results = []
        
        def worker(worker_id):
            mock_context = Mock()
            mock_context.user_id = f"user_{worker_id}"
            mock_context.session_id = f"session_{worker_id}"
            
            # Test different tools
            result1 = places_api(mock_context, f"City_{worker_id}", "restaurants")
            result2 = amadeus_flight_search(mock_context, "JFK", "LAX", "2024-06-01")
            result3 = stripe_payment(mock_context, 100.0, f"Payment_{worker_id}")
            
            results.append((worker_id, result1, result2, result3))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all results
        assert len(results) == 10
        for worker_id, result1, result2, result3 in results:
            assert isinstance(result1, list)
            assert isinstance(result2, list)
            assert isinstance(result3, dict)
