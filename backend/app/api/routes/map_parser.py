"""
API routes for Travya Map Parser v2
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.models import User
from app.services.map_parser import map_parser

logger = logging.getLogger(__name__)

router = APIRouter()

class ParseItineraryRequest(BaseModel):
    itinerary_data: Dict[str, Any]
    chat_id: str
    trip_id: Optional[str] = None

@router.post("/parse-itinerary")
async def parse_itinerary(
    request: ParseItineraryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Parse a travel itinerary and convert it to geo-enriched map data.
    
    Args:
        request: Request containing itinerary_data and chat_id
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Structured map data ready for frontend visualization
    """
    try:
        logger.info(f"Received itinerary parsing request for chat {request.chat_id} from user {current_user.id}")
        
        # Validate input
        if not request.itinerary_data:
            raise HTTPException(status_code=400, detail="Itinerary data is required")
        
        if not request.chat_id:
            raise HTTPException(status_code=400, detail="Chat ID is required")
        
        # Parse the itinerary
        result = await map_parser.parse_itinerary(
            request.itinerary_data, 
            request.chat_id,
            trip_id=request.trip_id,
            db_session=db
        )
        
        logger.info(f"Successfully parsed itinerary for chat {request.chat_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing itinerary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint for map parser service."""
    return {"status": "healthy", "service": "map_parser_v2"}
