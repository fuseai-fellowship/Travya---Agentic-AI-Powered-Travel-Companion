import json
from app.core.llm import call_llm
from app.core.config import settings

PROMPT_TEMPLATE = """
You are a world-class travel planner AI.
Given the user's travel goal, produce a structured 5-day itinerary in JSON.
User goal: "{goal}"
"""

def plan_trip(goal: str) -> dict:
    try:
        prompt = PROMPT_TEMPLATE.format(goal=goal)
        response = call_llm(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_output": response, "error": "invalid_json"}
    except Exception as e:
        return {"error": str(e)}

# Create planner agent instance
planner_agent = {
    "name": "planner",
    "description": "Creates detailed travel itineraries",
    "function": plan_trip
}

# Also create the proper Agent instance for production
if settings.ENVIRONMENT != "local":
    from google.adk.agents import Agent
    from google.adk.models.lite_llm import LiteLlm
    
    planner_agent = Agent(
        name="planner",
        model=LiteLlm(settings.GEMINI_MODEL),
        description="Creates detailed travel itineraries",
        instruction="Generate comprehensive travel itineraries based on research data and user preferences.",
        tools=[]  # Planner uses LLM directly
    )
