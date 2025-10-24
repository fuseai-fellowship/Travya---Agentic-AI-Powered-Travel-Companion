# backend/app/agents/mock_agents.py
from google.adk.agents import Agent

class MockToolContext:
    """Mock ToolContext for testing"""
    def __init__(self):
        pass

# Mock sub-agents
class MockAgent(Agent):
    def __init__(self, name):
        super().__init__(
            name=name,
            sub_agents=[],
            description=f"Mock agent for {name}",
            instruction="Return a simple JSON for testing."
        )

    async def run(self, user_id, session_id, message):
        """Return simple mock response."""
        return {"answer": f"Mock response from {self.name}", "context": []}

# Create mock agent instances
research_agent = {
    "name": "research",
    "description": "Mock research agent",
    "function": lambda x: {"answer": "Mock research response", "context": []}
}

planner_agent = {
    "name": "planner",
    "description": "Mock planner agent",
    "function": lambda x: {"answer": "Mock planner response", "context": []}
}

booker_agent = {
    "name": "booker",
    "description": "Mock booker agent",
    "function": lambda x: {"answer": "Mock booker response", "context": []}
}
