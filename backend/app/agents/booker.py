# Booker agent (Amadeus/Stripe)

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .tools import amadeus_flight_search, stripe_payment
from app.core.config import settings

# Create booker agent instance
booker_agent = {
    "name": "booker",
    "description": "Handles bookings and payments",
    "function": amadeus_flight_search
}

# Also create the proper Agent instance for production
if settings.ENVIRONMENT != "local":
    from google.adk.agents import Agent
    from google.adk.models.lite_llm import LiteLlm
    from .tools import amadeus_flight_search, stripe_payment
    
    booker_agent = Agent(
        name="booker",
        model=LiteLlm(settings.GEMINI_MODEL),
        description="Handles bookings and payments via Amadeus and Stripe.",
        instruction="Execute bookings and payments if approved by user.",
        tools=[amadeus_flight_search, stripe_payment]
    )