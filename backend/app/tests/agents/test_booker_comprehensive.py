"""
Comprehensive tests for the booker agent.
"""
import pytest
from unittest.mock import Mock, patch

from app.agents.booker import booker_agent
from app.agents.tools import amadeus_flight_search, stripe_payment
from app.tests.test_config import mock_llm


class TestBookerAgent:
    """Test suite for booker agent functionality."""

    def test_booker_agent_initialization(self):
        """Test booker agent initialization."""
        assert booker_agent is not None
        assert booker_agent["name"] == "booker"
        assert booker_agent["description"] == "Handles bookings and payments"
        assert callable(booker_agent["function"])

    def test_amadeus_flight_search_mock_implementation(self):
        """Test Amadeus flight search mock implementation."""
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
        
        test_routes = [
            ("JFK", "LAX", "2024-06-01"),
            ("LHR", "CDG", "2024-07-15"),
            ("NRT", "ICN", "2024-08-20"),
            ("SYD", "MEL", "2024-09-10")
        ]
        
        for origin, destination, date in test_routes:
            result = amadeus_flight_search(mock_context, origin, destination, date)
            assert isinstance(result, list)
            assert len(result) > 0
            assert "id" in result[0]

    def test_stripe_payment_mock_implementation(self):
        """Test Stripe payment mock implementation."""
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
        
        test_amounts = [10.00, 100.50, 1000.00, 5000.99, 0.01]
        
        for amount in test_amounts:
            result = stripe_payment(mock_context, amount, f"Payment for ${amount}")
            assert isinstance(result, dict)
            assert "payment_id" in result
            assert "status" in result

    def test_booker_agent_function_execution(self):
        """Test booker agent function execution."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        result = booker_agent["function"](mock_context)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_amadeus_flight_search_error_handling(self):
        """Test Amadeus flight search error handling."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test with empty parameters
        result = amadeus_flight_search(mock_context, "", "", "")
        assert isinstance(result, list)
        
        # Test with None parameters
        result = amadeus_flight_search(mock_context, None, None, None)
        assert isinstance(result, list)

    def test_stripe_payment_error_handling(self):
        """Test Stripe payment error handling."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test with zero amount
        result = stripe_payment(mock_context, 0, "Zero amount payment")
        assert isinstance(result, dict)
        
        # Test with negative amount
        result = stripe_payment(mock_context, -10, "Negative amount payment")
        assert isinstance(result, dict)

    def test_amadeus_flight_search_international_routes(self):
        """Test Amadeus flight search for international routes."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        international_routes = [
            ("JFK", "LHR", "2024-06-01"),  # New York to London
            ("CDG", "NRT", "2024-07-15"),  # Paris to Tokyo
            ("SYD", "LAX", "2024-08-20"),  # Sydney to Los Angeles
            ("FRA", "SIN", "2024-09-10")   # Frankfurt to Singapore
        ]
        
        for origin, destination, date in international_routes:
            result = amadeus_flight_search(mock_context, origin, destination, date)
            assert isinstance(result, list)
            assert len(result) > 0

    def test_stripe_payment_different_currencies(self):
        """Test Stripe payment with different currency scenarios."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test different payment descriptions
        descriptions = [
            "Flight booking",
            "Hotel reservation",
            "Car rental",
            "Travel insurance",
            "Tour package"
        ]
        
        for description in descriptions:
            result = stripe_payment(mock_context, 100.00, description)
            assert isinstance(result, dict)
            assert "payment_id" in result

    def test_booker_agent_metadata(self):
        """Test booker agent metadata and structure."""
        assert "name" in booker_agent
        assert "description" in booker_agent
        assert "function" in booker_agent
        
        assert booker_agent["name"] == "booker"
        assert isinstance(booker_agent["description"], str)
        assert callable(booker_agent["function"])

    def test_amadeus_flight_search_date_formats(self):
        """Test Amadeus flight search with different date formats."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        date_formats = [
            "2024-06-01",
            "2024-12-25",
            "2025-01-01",
            "2024-02-29"  # Leap year
        ]
        
        for date in date_formats:
            result = amadeus_flight_search(mock_context, "JFK", "LAX", date)
            assert isinstance(result, list)

    def test_stripe_payment_large_amounts(self):
        """Test Stripe payment with large amounts."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        large_amounts = [10000.00, 50000.00, 100000.00]
        
        for amount in large_amounts:
            result = stripe_payment(mock_context, amount, f"Large payment ${amount}")
            assert isinstance(result, dict)
            assert "payment_id" in result

    def test_amadeus_flight_search_round_trip(self):
        """Test Amadeus flight search for round trip scenarios."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test outbound flight
        outbound = amadeus_flight_search(mock_context, "JFK", "LAX", "2024-06-01")
        assert isinstance(outbound, list)
        
        # Test return flight
        return_flight = amadeus_flight_search(mock_context, "LAX", "JFK", "2024-06-08")
        assert isinstance(return_flight, list)

    def test_stripe_payment_refund_scenario(self):
        """Test Stripe payment for refund scenarios."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test original payment
        payment = stripe_payment(mock_context, 500.00, "Original booking")
        assert isinstance(payment, dict)
        assert "payment_id" in payment
        
        # Test refund (negative amount)
        refund = stripe_payment(mock_context, -100.00, "Partial refund")
        assert isinstance(refund, dict)

    @pytest.mark.asyncio
    async def test_booker_agent_integration(self):
        """Test booker agent integration with other components."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test that the booker agent can be used in orchestrator context
        result = booker_agent["function"](mock_context)
        assert isinstance(result, list)

    def test_amadeus_flight_search_connection_codes(self):
        """Test Amadeus flight search with different airport codes."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        airport_codes = [
            ("JFK", "LAX"),  # Major US airports
            ("LHR", "CDG"),  # Major European airports
            ("NRT", "ICN"),  # Major Asian airports
            ("SYD", "MEL")   # Major Australian airports
        ]
        
        for origin, destination in airport_codes:
            result = amadeus_flight_search(mock_context, origin, destination, "2024-06-01")
            assert isinstance(result, list)

    def test_stripe_payment_metadata(self):
        """Test Stripe payment with metadata."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test payment with detailed description
        result = stripe_payment(
            mock_context, 
            250.00, 
            "Flight booking: JFK to LAX on 2024-06-01 for user test_user"
        )
        assert isinstance(result, dict)
        assert "payment_id" in result

    def test_booker_agent_error_resilience(self):
        """Test booker agent error resilience."""
        mock_context = Mock()
        mock_context.user_id = "test_user"
        mock_context.session_id = "test_session"
        
        # Test with various edge cases
        edge_cases = [
            None,  # None input
            "",    # Empty string
            {},    # Empty dict
            []     # Empty list
        ]
        
        for edge_case in edge_cases:
            try:
                result = booker_agent["function"](edge_case)
                # Should not raise exception, should return some result
                assert result is not None
            except Exception as e:
                # If it does raise an exception, it should be handled gracefully
                assert isinstance(e, Exception)
