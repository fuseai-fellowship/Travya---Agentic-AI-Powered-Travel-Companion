import pytest
from unittest.mock import patch, MagicMock
from app.agents.adapter import adapter_agent, callback, start_adapter
from google.cloud.pubsub_v1.subscriber.message import Message as PubsubMessage

def test_adapter_agent_definition():
    """Test adapter agent definition."""
    assert adapter_agent["name"] == "adapter"
    assert "Adapts plans in real-time" in adapter_agent["description"]
    assert callable(adapter_agent["function"])

def test_adapter_agent_mock_function():
    """Test adapter agent mock function."""
    mock_response = adapter_agent["function"]("some input")
    assert mock_response == {"answer": "Mock adapter response", "context": []}

def test_mock_callback():
    """Test mock callback function."""
    mock_message_data = b'{"type": "delay", "flight_id": "123"}'
    mock_message = MagicMock(spec=PubsubMessage)
    mock_message.data = mock_message_data
    
    with patch('builtins.print') as mock_print:
        callback(mock_message)
        mock_print.assert_called_once_with(f"Mock adapted plan for event: {mock_message_data.decode('utf-8')}")
        mock_message.ack.assert_called_once()

def test_start_adapter():
    """Test start adapter function."""
    with patch('builtins.print') as mock_print:
        result = start_adapter()
        mock_print.assert_called_once_with("Adapter agent started (mock mode)")
        assert result is True

def test_adapter_event_handling():
    """Test adapter event handling scenarios."""
    # Test delay event
    delay_event = b'{"type": "delay", "flight_id": "123", "delay_minutes": 30}'
    mock_message = MagicMock(spec=PubsubMessage)
    mock_message.data = delay_event
    
    with patch('builtins.print') as mock_print:
        callback(mock_message)
        mock_print.assert_called_once()
        mock_message.ack.assert_called_once()
    
    # Test cancellation event
    cancel_event = b'{"type": "cancellation", "booking_id": "456"}'
    mock_message2 = MagicMock(spec=PubsubMessage)
    mock_message2.data = cancel_event
    
    with patch('builtins.print') as mock_print:
        callback(mock_message2)
        mock_print.assert_called_once()
        mock_message2.ack.assert_called_once()

def test_adapter_integration():
    """Test adapter integration with orchestrator."""
    # Test that adapter can be started
    result = start_adapter()
    assert result is True
    
    # Test that adapter function works
    response = adapter_agent["function"]("test input")
    assert isinstance(response, dict)
    assert "answer" in response
    assert "context" in response
