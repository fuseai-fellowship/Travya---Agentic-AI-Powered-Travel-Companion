# Adapter agent (Pub/Sub events)

from google.cloud import pubsub_v1
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .orchestrator import runner
from app.core.config import settings

# Create adapter agent instance
adapter_agent = {
    "name": "adapter",
    "description": "Adapts plans in real-time",
    "function": lambda x: {"answer": "Mock adapter response", "context": []}
}

# Mock Pub/Sub for local testing
def callback(message):
    """Handle Pub/Sub events for real-time adaptations."""
    event = message.data.decode("utf-8")  # e.g., {"type": "delay", "flight_id": "123"}
    # Mock adaptation for local testing
    print(f"Mock adapted plan for event: {event}")
    message.ack()

# Mock subscription for local testing
def start_adapter():
    """Start the adapter agent (mock for local testing)."""
    print("Adapter agent started (mock mode)")
    return True