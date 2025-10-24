"""
Comprehensive tests for the adapter agent.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.agents.adapter import adapter_agent, callback, start_adapter
from app.tests.test_config import mock_llm


class TestAdapterAgent:
    """Test suite for adapter agent functionality."""

    def test_adapter_agent_initialization(self):
        """Test adapter agent initialization."""
        assert adapter_agent is not None
        assert adapter_agent["name"] == "adapter"
        assert adapter_agent["description"] == "Adapts plans in real-time"
        assert callable(adapter_agent["function"])

    def test_adapter_agent_function_execution(self):
        """Test adapter agent function execution."""
        result = adapter_agent["function"]("test input")
        assert isinstance(result, dict)
        assert "answer" in result
        assert "context" in result

    def test_callback_function(self):
        """Test callback function for Pub/Sub events."""
        # Create a mock message
        mock_message = Mock()
        mock_message.data = b'{"type": "delay", "flight_id": "123", "new_time": "14:30"}'
        mock_message.ack = Mock()
        
        # Test callback execution
        callback(mock_message)
        
        # Verify ack was called
        mock_message.ack.assert_called_once()

    def test_callback_with_different_event_types(self):
        """Test callback with different event types."""
        event_types = [
            '{"type": "delay", "flight_id": "123"}',
            '{"type": "cancellation", "booking_id": "456"}',
            '{"type": "weather", "location": "Paris", "condition": "storm"}',
            '{"type": "price_change", "hotel_id": "789", "new_price": 200}',
            '{"type": "availability", "restaurant_id": "101", "slots": 3}'
        ]
        
        for event_data in event_types:
            mock_message = Mock()
            mock_message.data = event_data.encode('utf-8')
            mock_message.ack = Mock()
            
            callback(mock_message)
            mock_message.ack.assert_called_once()

    def test_callback_with_invalid_json(self):
        """Test callback with invalid JSON data."""
        mock_message = Mock()
        mock_message.data = b'Invalid JSON data'
        mock_message.ack = Mock()
        
        # Should not raise exception
        callback(mock_message)
        mock_message.ack.assert_called_once()

    def test_callback_with_empty_data(self):
        """Test callback with empty data."""
        mock_message = Mock()
        mock_message.data = b''
        mock_message.ack = Mock()
        
        callback(mock_message)
        mock_message.ack.assert_called_once()

    def test_start_adapter_function(self):
        """Test start_adapter function."""
        result = start_adapter()
        assert result is True

    def test_adapter_agent_metadata(self):
        """Test adapter agent metadata and structure."""
        assert "name" in adapter_agent
        assert "description" in adapter_agent
        assert "function" in adapter_agent
        
        assert adapter_agent["name"] == "adapter"
        assert isinstance(adapter_agent["description"], str)
        assert callable(adapter_agent["function"])

    def test_callback_with_unicode_data(self):
        """Test callback with Unicode data."""
        unicode_data = '{"type": "delay", "message": "航班延误", "airline": "中国国际航空"}'
        mock_message = Mock()
        mock_message.data = unicode_data.encode('utf-8')
        mock_message.ack = Mock()
        
        callback(mock_message)
        mock_message.ack.assert_called_once()

    def test_callback_with_large_data(self):
        """Test callback with large data payload."""
        large_data = '{"type": "bulk_update", "bookings": ' + str([{"id": i, "status": "confirmed"} for i in range(1000)]) + '}'
        mock_message = Mock()
        mock_message.data = large_data.encode('utf-8')
        mock_message.ack = Mock()
        
        callback(mock_message)
        mock_message.ack.assert_called_once()

    def test_adapter_agent_error_handling(self):
        """Test adapter agent error handling."""
        # Test with various input types
        test_inputs = [
            None,
            "",
            {},
            [],
            123,
            True
        ]
        
        for test_input in test_inputs:
            result = adapter_agent["function"](test_input)
            assert isinstance(result, dict)
            assert "answer" in result

    def test_callback_with_special_characters(self):
        """Test callback with special characters in data."""
        special_data = '{"type": "alert", "message": "Alert! Flight #123 has been delayed by 2+ hours. Please contact +1-800-AIRLINE for assistance."}'
        mock_message = Mock()
        mock_message.data = special_data.encode('utf-8')
        mock_message.ack = Mock()
        
        callback(mock_message)
        mock_message.ack.assert_called_once()

    def test_callback_with_nested_json(self):
        """Test callback with nested JSON data."""
        nested_data = {
            "type": "complex_update",
            "trip": {
                "id": "trip_123",
                "itinerary": {
                    "days": [
                        {
                            "date": "2024-06-01",
                            "activities": [
                                {"name": "Flight to Paris", "time": "09:00"},
                                {"name": "Hotel check-in", "time": "15:00"}
                            ]
                        }
                    ]
                }
            },
            "changes": {
                "flight_delay": {
                    "original_time": "09:00",
                    "new_time": "11:30",
                    "reason": "weather"
                }
            }
        }
        
        import json
        mock_message = Mock()
        mock_message.data = json.dumps(nested_data).encode('utf-8')
        mock_message.ack = Mock()
        
        callback(mock_message)
        mock_message.ack.assert_called_once()

    @pytest.mark.asyncio
    async def test_adapter_agent_integration(self):
        """Test adapter agent integration with other components."""
        # Test that the adapter agent can be used in orchestrator context
        result = adapter_agent["function"]("integration test")
        assert isinstance(result, dict)

    def test_callback_performance(self):
        """Test callback performance with multiple messages."""
        import time
        
        # Test with multiple rapid messages
        start_time = time.time()
        
        for i in range(100):
            mock_message = Mock()
            mock_message.data = f'{{"type": "test", "id": {i}}}'.encode('utf-8')
            mock_message.ack = Mock()
            
            callback(mock_message)
        
        end_time = time.time()
        
        # Should process 100 messages quickly
        assert end_time - start_time < 1.0

    def test_adapter_agent_with_different_contexts(self):
        """Test adapter agent with different context types."""
        contexts = [
            "flight_delay",
            "hotel_cancellation",
            "weather_alert",
            "price_change",
            "availability_update",
            "route_change",
            "equipment_change",
            "crew_change"
        ]
        
        for context in contexts:
            result = adapter_agent["function"](context)
            assert isinstance(result, dict)
            assert "answer" in result

    def test_callback_with_malformed_data(self):
        """Test callback with malformed data."""
        malformed_data_cases = [
            b'{"incomplete": "json"',
            b'{"type": "test", "missing_quote": value}',
            b'{"type": "test", "trailing_comma": "value",}',
            b'{"type": "test", "unclosed_array": [1, 2, 3',
            b'{"type": "test", "unclosed_object": {"key": "value"'
        ]
        
        for malformed_data in malformed_data_cases:
            mock_message = Mock()
            mock_message.data = malformed_data
            mock_message.ack = Mock()
            
            # Should not raise exception
            callback(mock_message)
            mock_message.ack.assert_called_once()

    def test_adapter_agent_resilience(self):
        """Test adapter agent resilience to various inputs."""
        resilience_tests = [
            ("normal_input", "string"),
            ({"key": "value"}, "dict"),
            ([1, 2, 3], "list"),
            (123, "number"),
            (True, "boolean"),
            (None, "none")
        ]
        
        for test_input, input_type in resilience_tests:
            result = adapter_agent["function"](test_input)
            assert isinstance(result, dict)
            assert "answer" in result
            assert "context" in result

    def test_start_adapter_multiple_calls(self):
        """Test start_adapter function with multiple calls."""
        # Should be idempotent
        result1 = start_adapter()
        result2 = start_adapter()
        
        assert result1 is True
        assert result2 is True

    def test_callback_with_binary_data(self):
        """Test callback with binary data."""
        binary_data = b'\x00\x01\x02\x03\x04\x05'
        mock_message = Mock()
        mock_message.data = binary_data
        mock_message.ack = Mock()
        
        # Should handle binary data gracefully
        callback(mock_message)
        mock_message.ack.assert_called_once()
