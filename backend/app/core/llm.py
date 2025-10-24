import os
import asyncio
from typing import Optional
from app.core.config import settings

# Try to import Google AI Studio client
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False

def _setup_google_ai():
    """Setup Google AI Studio client"""
    if not GOOGLE_AI_AVAILABLE:
        raise ValueError("Google AI Studio client (google-generativeai) is not installed")
    if not settings.GOOGLE_AI_STUDIO_API_KEY:
        raise ValueError("GOOGLE_AI_STUDIO_API_KEY is not set in the environment")
    genai.configure(api_key=settings.GOOGLE_AI_STUDIO_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)

def call_llm(prompt: str) -> str:
    """Call LLM with Google AI Studio API."""
    try:
        model = _setup_google_ai()
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
        raise ValueError("No valid response received from Google AI Studio API")
    except Exception as e:
        raise ValueError(f"Failed to call Google AI Studio API: {str(e)}")

async def call_llm_async(prompt: str) -> str:
    """Async version of LLM call"""
    return call_llm(prompt)

def test_google_ai_connection() -> bool:
    """Test Google AI Studio API connection"""
    try:
        model = _setup_google_ai()
        response = model.generate_content("Hello, this is a test.")
        return response and response.text is not None
    except Exception as e:
        print(f"Google AI Studio connection test failed: {e}")
        return False