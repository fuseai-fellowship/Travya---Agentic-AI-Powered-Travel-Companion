from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.agents.orchestrator import execute_query
from app.agents.sessions import RedisSessionService
from app.agents.populate_index import populate_index  # Updated import
from app.core.db import get_db


from redis import Redis
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None

class QueryResponse(BaseModel):
    answer: str
    context: list[str] = []

class SessionCreate(BaseModel):
    session_data: dict = {}

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    session_data: dict

# Dependency for Redis
def get_redis():
    return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

# Endpoints
@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session: SessionCreate,
    redis: Redis = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """Create a new agent session."""
    try:
        session_service = RedisSessionService()
        session_id = session_service.create_session("travya", current_user["id"], session.session_data)
        return SessionResponse(session_id=session_id, user_id=current_user["id"], session_data=session.session_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, redis: Redis = Depends(get_redis)):
    """Retrieve an agent session."""
    try:
        session_service = RedisSessionService()
        session_data = session_service.get_session("travya", "user", session_id)  # Use current_user if needed
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        return SessionResponse(**session_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve session: {str(e)}")

@router.post("/index/populate")
async def populate_index_endpoint(db: Session = Depends(get_db)):
    """Populate the mock vector store with user data."""
    try:
        populate_index()  # Call the script function
        return {"message": "Vector store populated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to populate index: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def agent_query(
    query: QueryRequest,
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: dict = Depends(get_current_user)
):
    """Handle multi-modal travel planning query."""
    try:
        session_id = query.session_id or f"default-{current_user['id']}"
        response = await execute_query(current_user["id"], session_id, {"query": query.query}, db)
        try:
            import json
            parsed_response = json.loads(response) if isinstance(response, str) else response
            return QueryResponse(
                answer=parsed_response.get("answer", "No answer provided"),
                context=parsed_response.get("context", [])
            )
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from orchestrator")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")