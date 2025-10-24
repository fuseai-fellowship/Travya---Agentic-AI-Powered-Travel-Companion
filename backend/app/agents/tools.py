# backend/app/agents/tools.py
from google.adk.tools.tool_context import ToolContext
from googlemaps import Client as GoogleMapsClient
from amadeus import Client as AmadeusClient
import stripe
import numpy as np
import faiss
from app.core.config import settings

# Initialize clients
# gmaps = GoogleMapsClient(key=settings.GOOGLE_MAPS_API_KEY)  # Changed to uppercase
amadeus = AmadeusClient(client_id=settings.AMADEUS_CLIENT_ID, client_secret=settings.AMADEUS_CLIENT_SECRET)  # Changed to uppercase
stripe.api_key = settings.STRIPE_SECRET_KEY  # Changed to uppercase

# Mock vector store
mock_vector_store = None
mock_payloads = []

def init_mock_vector_store(dimension=768):
    """Initialize FAISS index for mock vector store."""
    global mock_vector_store, mock_payloads
    mock_vector_store = faiss.IndexFlatL2(dimension)
    mock_payloads = []

def add_to_mock_vector_store(embedding: list[float], payload: dict):
    """Add embedding and payload to mock vector store."""
    global mock_vector_store, mock_payloads
    embedding = np.array([embedding], dtype=np.float32)
    mock_vector_store.add(embedding)
    mock_payloads.append(payload)

def rag_query(tool_context: ToolContext, query: str) -> dict:
    """Mock RAG query using FAISS."""
    global mock_vector_store, mock_payloads
    if mock_vector_store is None:
        init_mock_vector_store()
    
    # If no data in vector store, return empty results
    if mock_vector_store.ntotal == 0:
        return {"results": []}
    
    # Mock embedding generation (replace with Gemini in production)
    query_embedding = np.random.rand(768).astype(np.float32)  # Mock 768-dim embedding
    distances, indices = mock_vector_store.search(np.array([query_embedding]), k=5)
    
    # Handle case where search returns no results
    if len(indices) == 0 or len(indices[0]) == 0:
        return {"results": []}
    
    results = [mock_payloads[i] for i in indices[0] if i < len(mock_payloads)]
    return {"results": results}

def places_api(tool_context: ToolContext, location: str, query: str) -> list:
    """Fetch attractions via Google Places API."""
    # Mock implementation for local testing
    return [{"name": f"Mock {query} in {location}", "rating": 4.5, "place_id": "mock_place_id"}]

def amadeus_flight_search(tool_context: ToolContext, origin: str, destination: str, date: str) -> list:
    """Search flights via Amadeus API."""
    # Mock implementation for local testing
    return [{"id": "mock_flight_id", "price": {"total": "500.00"}, "itineraries": []}]

def stripe_payment(tool_context: ToolContext, amount: float, description: str) -> dict:
    """Process payment via Stripe."""
    # Mock implementation for local testing
    return {"payment_id": "mock_payment_id", "status": "succeeded"}

def weather_api(tool_context: ToolContext, location: str, date: str) -> dict:
    """Fetch weather forecast (placeholder)."""
    return {"forecast": "Sunny, 75°F"}