from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .tools import rag_query, places_api
from app.core.config import settings

# Create research agent instance
research_agent = {
    "name": "research",
    "description": "Researches attractions and user preferences",
    "function": rag_query
}

# Also create the proper Agent instance for production
if settings.ENVIRONMENT != "local":
    research_agent = Agent(
        name="research",
        model=LiteLlm(settings.GEMINI_MODEL),
        description="Researches attractions and user preferences via mock RAG and Google Places.",
        instruction="Fetch personalized travel data using RAG, then query Places API for attractions.",
        tools=[rag_query, places_api]
    )

if __name__ == "__main__":
    # Test RAG locally
    result = rag_query(ToolContext(), "budget-friendly eco-trips")
    print(result)