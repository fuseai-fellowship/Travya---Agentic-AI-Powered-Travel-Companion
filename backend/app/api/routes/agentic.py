from fastapi import APIRouter, HTTPException
from app.core.llm import call_llm
import asyncio
import json

router = APIRouter(prefix="/agentic", tags=["agentic"])

@router.get("/test")
async def test_agentic():
    """Test endpoint to verify the agentic system is working"""
    try:
        # Simple test using LLM directly
        response = call_llm("Hello! This is a test of the AI system.")
        return {
            "status": "success", 
            "message": "Agentic system is working", 
            "ai_response": response[:200] + "..." if len(response) > 200 else response
        }
    except Exception as e:
        import traceback
        print(f"Error in agentic test: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run")
def run_agentic_query(user_id: str, session_id: str, query: dict):
    try:
        # Use LLM directly for now (synchronous call)
        message = query.get("message", "Hello")
        ai_response = call_llm(f"User query: {message}. Please provide helpful travel advice.")
        
        return {
            "status": "success", 
            "response": {
                "user_id": user_id,
                "session_id": session_id,
                "query": query,
                "ai_response": ai_response,
                "timestamp": "2025-10-12T06:40:00.000000"
            }
        }
    except Exception as e:
        import traceback
        print(f"Error in agentic query: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
