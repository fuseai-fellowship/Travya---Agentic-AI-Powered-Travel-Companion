# import uuid
# import logging
# from typing import Any, List, Optional
# from datetime import date, datetime, timedelta

# from fastapi import APIRouter, Depends, HTTPException
# from pydantic import BaseModel
# from sqlmodel import Session

# logger = logging.getLogger(__name__)

# from app.api.deps import CurrentUser, SessionDep
# from app.models import (
#     Trip, TripCreate, Itinerary, ItineraryCreate, Booking, BookingCreate,
#     Conversation, ConversationCreate, ConversationMessage, ConversationMessageCreate
# )
# from app.agents.orchestrator import plan_trip_with_agents
# from app.services.external_apis import travel_api_service
# from app.core.llm import call_llm
# from app import crud

# router = APIRouter(prefix="/ai-travel", tags=["ai-travel"])

# # Request/Response Models
# class TripPlanningRequest(BaseModel):
#     destination: str
#     start_date: date
#     end_date: date
#     budget: Optional[float] = None
#     trip_type: str = "leisure"
#     interests: List[str] = []
#     travelers: int = 1
#     accommodation_preference: Optional[str] = None
#     transportation_preference: Optional[str] = None


# class TripPlanningResponse(BaseModel):
#     status: str
#     trip_id: Optional[uuid.UUID] = None
#     research: dict
#     itinerary: dict
#     bookings: dict
#     trip_summary: dict
#     message: Optional[str] = None


# class ChatRequest(BaseModel):
#     message: str
#     conversation_id: Optional[uuid.UUID] = None
#     trip_id: Optional[uuid.UUID] = None


# class ChatResponse(BaseModel):
#     response: str
#     conversation_id: uuid.UUID
#     suggestions: Optional[List[dict]] = None


# # Public chat endpoint for testing
# @router.post("/chat-public", response_model=ChatResponse)
# async def chat_with_ai_public(request: ChatRequest) -> Any:
#     """Public chat endpoint for testing without authentication."""
#     try:
#         # Generate AI response using LLM directly
#         ai_response = call_llm(f"User asks: {request.message}. Provide helpful travel advice.")
        
#         suggestions = [
#             {"type": "destination", "text": "Find destinations", "action": "search_destinations"},
#             {"type": "itinerary", "text": "Plan itinerary", "action": "plan_itinerary"},
#             {"type": "booking", "text": "Find bookings", "action": "search_bookings"}
#         ]
        
#         return ChatResponse(
#             response=ai_response,
#             conversation_id=uuid.uuid4(),
#             suggestions=suggestions
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# @router.post("/plan-trip", response_model=TripPlanningResponse)
# async def plan_trip_with_ai(
#     *, session: SessionDep, current_user: CurrentUser, request: TripPlanningRequest
# ) -> Any:
#     """Plan a complete trip using AI agents."""
    
#     try:
#         # Calculate duration
#         duration = (request.end_date - request.start_date).days
        
#         # Prepare trip request for agents
#         trip_request = {
#             "destination": request.destination,
#             "start_date": request.start_date.isoformat(),
#             "end_date": request.end_date.isoformat(),
#             "duration": duration,
#             "budget": request.budget,
#             "trip_type": request.trip_type,
#             "interests": request.interests,
#             "travelers": request.travelers,
#             "accommodation_preference": request.accommodation_preference,
#             "transportation_preference": request.transportation_preference
#         }
        
#         # Generate session ID
#         session_id = f"trip_plan_{uuid.uuid4().hex[:8]}"
        
#         # Use AI agents to plan the trip
#         ai_response = await plan_trip_with_agents(
#             user_id=str(current_user.id),
#             session_id=session_id,
#             trip_request=trip_request,
#             db=session
#         )
        
#         if ai_response.get("status") == "error":
#             raise HTTPException(status_code=500, detail=ai_response.get("message", "AI planning failed"))
        
#         # Create trip in database
#         trip_data = TripCreate(
#             title=f"Trip to {request.destination}",
#             description=f"AI-planned {request.trip_type} trip to {request.destination}",
#             destination=request.destination,
#             start_date=request.start_date,
#             end_date=request.end_date,
#             budget=request.budget,
#             trip_type=request.trip_type
#         )
        
#         trip = Trip.model_validate(trip_data, update={"owner_id": current_user.id})
#         session.add(trip)
#         session.commit()
#         session.refresh(trip)
        
#         # Parse AI response and create itineraries and bookings
#         try:
#             import json
#             ai_data = json.loads(ai_response.get("itinerary", "{}"))
            
#             # Create itinerary items from AI response
#             if "days" in ai_data:
#                 for day_data in ai_data["days"]:
#                     itinerary_data = ItineraryCreate(
#                         trip_id=trip.id,
#                         title=day_data.get("theme", f"Day {day_data.get('day', 1)}"),
#                         description=f"Activities: {', '.join(day_data.get('places', []))}",
#                         date=request.start_date + timedelta(days=day_data.get('day', 1) - 1),
#                         location=request.destination,
#                         estimated_cost=day_data.get('estimated_cost_usd', 0)
#                     )
#                     crud.create_itinerary(session=session, itinerary_in=itinerary_data)
#         except Exception as parse_error:
#             # Don't fail the main request if parsing fails
#             print(f"Error parsing AI response: {parse_error}")
#             pass
        
#         return TripPlanningResponse(
#             status="success",
#             trip_id=trip.id,
#             research=ai_response.get("research", {}),
#             itinerary=ai_response.get("itinerary", {}),
#             bookings=ai_response.get("bookings", {}),
#             trip_summary=ai_response.get("trip_summary", {}),
#             message="Trip planned successfully!"
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Trip planning failed: {str(e)}")


# @router.post("/chat", response_model=ChatResponse)
# async def chat_with_ai(
#     *, session: SessionDep, current_user: CurrentUser, request: ChatRequest
# ) -> Any:
#     """Chat with AI about travel planning."""
#     logger.error("="*50)
#     logger.error("CHAT ENDPOINT CALLED")
#     logger.error("="*50)
    
#     try:
#         logger.error(f"DEBUG: Chat request received - message: {request.message}, conversation_id: {request.conversation_id}, user_id: {current_user.id}")
#         # Create or get conversation
#         if request.conversation_id:
#             logger.error(f"DEBUG: Looking for existing conversation: {request.conversation_id}")
#             conversation = crud.get_conversation(session=session, conversation_id=request.conversation_id)
#             if not conversation or conversation.user_id != current_user.id:
#                 raise HTTPException(status_code=404, detail="Conversation not found")
#             logger.error(f"DEBUG: Found existing conversation: {conversation.id}")
#         else:
#             # Create new conversation
#             logger.error("DEBUG: Creating new conversation")
#             conversation_data = ConversationCreate(
#                 title=request.message[:50] + "..." if len(request.message) > 50 else request.message
#             )
#             logger.error(f"DEBUG: Conversation data: {conversation_data}")
#             conversation = crud.create_conversation(
#                 session=session, 
#                 conversation_in=conversation_data, 
#                 user_id=current_user.id
#             )
#             logger.error(f"DEBUG: Created conversation: {conversation.id}")
        
#         # Save user message
#         print("DEBUG: Creating user message")
#         user_message_data = ConversationMessageCreate(
#             conversation_id=conversation.id,
#             content=request.message,
#             sender="user"
#         )
#         crud.create_conversation_message(session=session, message_in=user_message_data)
#         print("DEBUG: User message created")
        
#         # Generate AI response using LLM
#         print("DEBUG: Calling LLM")
#         ai_response = call_llm(f"User asks: {request.message}. Provide helpful travel advice.")
#         print(f"DEBUG: LLM response length: {len(ai_response) if ai_response else 0}")
        
#         # Save AI message
#         print("DEBUG: Creating AI message")
#         ai_message_data = ConversationMessageCreate(
#             conversation_id=conversation.id,
#             content=ai_response,
#             sender="ai"
#         )
#         crud.create_conversation_message(session=session, message_in=ai_message_data)
#         print("DEBUG: AI message created")
        
#         # Update conversation with last message
#         print("DEBUG: Updating conversation")
#         conversation.last_message = ai_response[:100]
#         conversation.updated_at = datetime.utcnow()
#         session.add(conversation)
#         session.commit()
#         print("DEBUG: Conversation updated")
        
#         suggestions = [
#             {"type": "destination", "text": "Find destinations", "action": "search_destinations"},
#             {"type": "itinerary", "text": "Plan itinerary", "action": "plan_itinerary"},
#             {"type": "booking", "text": "Find bookings", "action": "search_bookings"}
#         ]
        
#         print("DEBUG: Creating response")
#         response = ChatResponse(
#             response=ai_response,
#             conversation_id=conversation.id,
#             suggestions=suggestions
#         )
#         print(f"DEBUG: Response created - conversation_id: {response.conversation_id}")
#         return response
        
#     except Exception as e:
#         import traceback
#         error_details = traceback.format_exc()
#         print(f"DEBUG: Chat error: {str(e)}")
#         print(f"DEBUG: Full traceback: {error_details}")
#         raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# @router.get("/suggestions/{trip_id}")
# async def get_ai_suggestions(
#     session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID
# ) -> Any:
#     """Get AI-powered suggestions for a trip."""
    
#     # Check trip access
#     trip = session.get(Trip, trip_id)
#     if not trip:
#         raise HTTPException(status_code=404, detail="Trip not found")
    
#     if trip.owner_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     # TODO: Use AI to generate personalized suggestions based on trip data
#     suggestions = {
#         "destinations": [
#             {"name": "Local Attractions", "description": "Popular spots near your destination"},
#             {"name": "Hidden Gems", "description": "Lesser-known but amazing places"}
#         ],
#         "activities": [
#             {"name": "Cultural Experiences", "description": "Museums, historical sites, local culture"},
#             {"name": "Outdoor Adventures", "description": "Hiking, beaches, nature activities"}
#         ],
#         "dining": [
#             {"name": "Local Cuisine", "description": "Authentic local restaurants"},
#             {"name": "Fine Dining", "description": "Upscale dining experiences"}
#         ],
#         "accommodation": [
#             {"name": "Hotels", "description": "Traditional hotel options"},
#             {"name": "Unique Stays", "description": "Boutique hotels, B&Bs, unique accommodations"}
#         ]
#     }
    
#     return {"suggestions": suggestions}


# @router.post("/optimize-itinerary/{trip_id}")
# async def optimize_itinerary_with_ai(
#     session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID
# ) -> Any:
#     """Use AI to optimize an existing trip itinerary."""
    
#     # Check trip access
#     trip = session.get(Trip, trip_id)
#     if not trip:
#         raise HTTPException(status_code=404, detail="Trip not found")
    
#     if trip.owner_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not enough permissions")
    
#     # TODO: Get existing itineraries and use AI to optimize them
#     # This would involve:
#     # 1. Fetching current itineraries
#     # 2. Using AI to analyze and optimize the schedule
#     # 3. Suggesting improvements for timing, logistics, etc.
    
#     optimization_result = {
#         "status": "success",
#         "improvements": [
#             "Optimized travel times between locations",
#             "Added buffer time for popular attractions",
#             "Suggested alternative routes to avoid crowds"
#         ],
#         "estimated_savings": {
#             "time": "2 hours saved per day",
#             "cost": "15% reduction in transportation costs"
#         }
#     }
    
#     return optimization_result


# # ===== EXTERNAL API INTEGRATION ENDPOINTS =====

# @router.get("/search-destination/{destination}")
# async def search_destination(
#     destination: str,
#     current_user: CurrentUser
# ) -> Any:
#     """Search for comprehensive destination information."""
    
#     try:
#         destination_info = await travel_api_service.search_destination_info(destination)
#         return destination_info
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Destination search failed: {str(e)}")


# @router.get("/search-travel-options")
# async def search_travel_options(
#     origin: str,
#     destination: str,
#     departure_date: date,
#     return_date: Optional[date] = None,
#     travelers: int = 1,
#     current_user: CurrentUser = None
# ) -> Any:
#     """Search for flights and destination information."""
    
#     try:
#         travel_options = await travel_api_service.search_travel_options(
#             origin, destination, departure_date, return_date, travelers
#         )
#         return travel_options
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Travel search failed: {str(e)}")


# @router.get("/recommendations/{destination}")
# async def get_trip_recommendations(
#     destination: str,
#     trip_type: str = "leisure",
#     interests: Optional[List[str]] = None,
#     budget: Optional[float] = None,
#     current_user: CurrentUser = None
# ) -> Any:
#     """Get personalized trip recommendations for a destination."""
    
#     try:
#         recommendations = await travel_api_service.get_trip_recommendations(
#             destination, trip_type, interests or [], budget
#         )
#         return recommendations
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")


# @router.get("/weather/{destination}")
# async def get_destination_weather(
#     destination: str,
#     current_user: CurrentUser = None
# ) -> Any:
#     """Get weather information for a destination."""
    
#     try:
#         # First get location coordinates
#         location = await travel_api_service.google_maps.geocode_address(destination)
#         if not location:
#             raise HTTPException(status_code=404, detail="Destination not found")
        
#         # Get weather forecast
#         weather_data = await travel_api_service.weather.get_forecast(
#             location.latitude, location.longitude
#         )
        
#         return {
#             "destination": destination,
#             "location": location,
#             "weather": weather_data
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Weather lookup failed: {str(e)}")


# @router.get("/places/{destination}")
# async def search_places(
#     destination: str,
#     place_type: Optional[str] = None,
#     current_user: CurrentUser = None
# ) -> Any:
#     """Search for places (attractions, restaurants, hotels) in a destination."""
    
#     try:
#         # First get location coordinates
#         location = await travel_api_service.google_maps.geocode_address(destination)
#         if not location:
#             raise HTTPException(status_code=404, detail="Destination not found")
        
#         # Search for places
#         places = await travel_api_service.google_maps.search_places(
#             f"{place_type or 'places'} in {destination}",
#             (location.latitude, location.longitude),
#             place_type=place_type
#         )
        
#         return {
#             "destination": destination,
#             "place_type": place_type,
#             "places": places
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Places search failed: {str(e)}")


# @router.get("/flights")
# async def search_flights(
#     origin: str,
#     destination: str,
#     departure_date: date,
#     return_date: Optional[date] = None,
#     adults: int = 1,
#     children: int = 0,
#     infants: int = 0,
#     current_user: CurrentUser = None
# ) -> Any:
#     """Search for flights between two destinations."""
    
#     try:
#         flights = await travel_api_service.amadeus.search_flights(
#             origin, destination, departure_date, return_date, adults, children, infants
#         )
        
#         return {
#             "origin": origin,
#             "destination": destination,
#             "departure_date": departure_date,
#             "return_date": return_date,
#             "flights": flights
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Flight search failed: {str(e)}")


# @router.get("/hotels/{city_code}")
# async def search_hotels(
#     city_code: str,
#     check_in: date,
#     check_out: date,
#     adults: int = 1,
#     rooms: int = 1,
#     current_user: CurrentUser = None
# ) -> Any:
#     """Search for hotels in a city."""
    
#     try:
#         hotels = await travel_api_service.amadeus.search_hotels(
#             city_code, check_in, check_out, adults, rooms
#         )
        
#         return {
#             "city_code": city_code,
#             "check_in": check_in,
#             "check_out": check_out,
#             "hotels": hotels
#         }
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Hotel search failed: {str(e)}")


import uuid
import logging
import json
from typing import Any, List, Optional
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session
import asyncio

logger = logging.getLogger(__name__)

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Trip, TripCreate, Itinerary, ItineraryCreate, Booking, BookingCreate,
    Conversation, ConversationCreate, ConversationMessage, ConversationMessageCreate
)
from app.agents.orchestrator import plan_trip_with_agents
from app.services.external_apis import travel_api_service
from app.core.llm import call_llm
from app import crud

router = APIRouter(prefix="/ai-travel", tags=["ai-travel"])

# Request/Response Models
class TripPlanningRequest(BaseModel):
    destination: str
    start_date: date
    end_date: date
    budget: Optional[float] = None
    trip_type: str = "leisure"
    interests: List[str] = []
    travelers: int = 1
    accommodation_preference: Optional[str] = None
    transportation_preference: Optional[str] = None

class TripPlanningResponse(BaseModel):
    status: str
    trip_id: Optional[uuid.UUID] = None
    research: dict
    itinerary: dict
    bookings: dict
    trip_summary: dict
    message: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[uuid.UUID] = None
    trip_id: Optional[uuid.UUID] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: uuid.UUID
    suggestions: Optional[List[dict]] = None

# Public chat endpoint for testing
@router.post("/chat-public", response_model=ChatResponse)
async def chat_with_ai_public(request: ChatRequest) -> Any:
    """Public chat endpoint for testing without authentication."""
    try:
        # Generate AI response using LLM directly
        ai_response = call_llm(f"User asks: {request.message}. Provide helpful travel advice.")
        
        suggestions = [
            {"type": "destination", "text": "Find destinations", "action": "search_destinations"},
            {"type": "itinerary", "text": "Plan itinerary", "action": "plan_itinerary"},
            {"type": "booking", "text": "Find bookings", "action": "search_bookings"}
        ]
        
        return ChatResponse(
            response=ai_response,
            conversation_id=uuid.uuid4(),
            suggestions=suggestions
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.post("/plan-trip", response_model=TripPlanningResponse)
async def plan_trip_with_ai(
    *, session: SessionDep, current_user: CurrentUser, request: TripPlanningRequest
) -> Any:
    """Plan a complete trip using AI agents."""
    
    try:
        # Validate request
        if not request.destination or not request.destination.strip():
            raise HTTPException(status_code=400, detail="Destination is required")
        
        if not request.start_date or not request.end_date:
            raise HTTPException(status_code=400, detail="Start and end dates are required")
        
        if request.start_date >= request.end_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        # Calculate duration
        duration = (request.end_date - request.start_date).days
        
        # Prepare trip request for agents
        trip_request = {
            "destination": request.destination,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "duration": duration,
            "budget": request.budget,
            "trip_type": request.trip_type,
            "interests": request.interests,
            "travelers": request.travelers,
            "accommodation_preference": request.accommodation_preference,
            "transportation_preference": request.transportation_preference
        }
        
        logger.info(f"Planning trip request: {trip_request}")
        
        # Generate session ID
        session_id = f"trip_plan_{uuid.uuid4().hex[:8]}"
        
        # Use AI agents to plan the trip
        logger.info(f"Calling plan_trip_with_agents for user {current_user.id}")
        ai_response = await plan_trip_with_agents(
            user_id=str(current_user.id),
            session_id=session_id,
            trip_request=trip_request,
            db=session
        )
        
        logger.info(f"🔍 Full AI response received: {ai_response}")
        logger.info(f"AI response status: {ai_response.get('status')}")
        logger.info(f"AI response keys: {list(ai_response.keys()) if isinstance(ai_response, dict) else 'Not a dict'}")
        
        if ai_response.get("status") == "error":
            logger.error(f"AI planning error: {ai_response.get('message')}")
            raise HTTPException(status_code=500, detail=ai_response.get("message", "AI planning failed"))
        
        # Extract itinerary data before creating trip
        itinerary_data = ai_response.get("itinerary", ai_response.get("detailed_results", {}).get("planning", {}))
        
        # Create trip in database with AI itinerary data
        trip_data = TripCreate(
            title=f"Trip to {request.destination}",
            description=f"AI-planned {request.trip_type} trip to {request.destination}",
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            budget=request.budget,
            trip_type=request.trip_type,
            ai_itinerary_data=json.dumps(itinerary_data) if itinerary_data else None  # Save as JSON string
        )
        
        trip = Trip.model_validate(trip_data, update={"owner_id": current_user.id})
        session.add(trip)
        session.commit()
        session.refresh(trip)
        
        logger.info(f"Trip created with ID: {trip.id}")
        
        # Parse AI response and create itineraries and bookings
        try:
            ai_data = ai_response.get("itinerary", {})
            if isinstance(ai_data, str):
                ai_data = json.loads(ai_data)
            
            # Create itinerary items from AI response
            if "days" in ai_data:
                for day_data in ai_data["days"]:
                    itinerary_data = ItineraryCreate(
                        trip_id=trip.id,
                        title=day_data.get("theme", f"Day {day_data.get('day', 1)}"),
                        description=f"Activities: {', '.join(day_data.get('places', []))}",
                        date=request.start_date + timedelta(days=day_data.get('day', 1) - 1),
                        location=request.destination,
                        estimated_cost=day_data.get('estimated_cost_usd', 0)
                    )
                    crud.create_itinerary(session=session, itinerary_in=itinerary_data)
        except Exception as parse_error:
            # Don't fail the main request if parsing fails
            logger.warning(f"Error parsing AI response: {parse_error}")
            pass
        
        # Extract data from orchestrator response
        research_data = ai_response.get("research", ai_response.get("detailed_results", {}).get("research", {}))
        # itinerary_data already extracted above
        bookings_data = ai_response.get("bookings", ai_response.get("detailed_results", {}).get("booking", {}))
        
        logger.info(f"📊 Extracted research_data: {research_data}")
        logger.info(f"📊 Extracted itinerary_data: {itinerary_data}")
        logger.info(f"📊 Extracted bookings_data: {bookings_data}")
        
        # Construct trip_summary as a proper dictionary
        trip_summary = {
            "summary": ai_response.get("summary", ""),
            "workflow_status": ai_response.get("workflow_status", "completed"),
            "confidence_score": ai_response.get("confidence_score", 0.0),
            "recommendations": ai_response.get("recommendations", []),
            "next_steps": ai_response.get("next_steps", []),
            "orchestration_id": ai_response.get("orchestration_id", ""),
            "timestamp": ai_response.get("timestamp", "")
        }
        
        response = TripPlanningResponse(
            status="success",
            trip_id=trip.id,
            research=research_data,
            itinerary=itinerary_data,
            bookings=bookings_data,
            trip_summary=trip_summary,
            message="Trip planned successfully!"
        )
        
        logger.info(f"🎯 Final response to frontend: {response}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Trip planning failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Trip planning failed: {str(e)}")

# Import event emitter from agents
from app.agents.event_emitter import register_session, unregister_session

@router.get("/agent-stream/{session_id}")
async def stream_agent_events(session_id: str) -> StreamingResponse:
    """Stream agent events for a session using Server-Sent Events (SSE)."""
    
    async def event_generator():
        """Generate SSE events."""
        # Create a queue for this session
        queue = asyncio.Queue()
        register_session(session_id, queue)
        
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'event_type': 'connected', 'message': 'Connected to agent stream'})}\n\n"
            
            # Keep connection alive and stream events
            while True:
                try:
                    # Wait for events with a timeout to send keep-alive
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send keep-alive ping
                    yield f"data: {json.dumps({'event_type': 'ping', 'message': 'keep-alive'})}\n\n"
                except Exception as e:
                    logger.error(f"Error in event generator: {e}")
                    break
        finally:
            # Cleanup when client disconnects
            unregister_session(session_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    *, session: SessionDep, current_user: CurrentUser, request: ChatRequest
) -> Any:
    """Chat with AI about travel planning."""
    logger.error("="*50)
    logger.error("CHAT ENDPOINT CALLED")
    logger.error("="*50)
    
    try:
        logger.error(f"DEBUG: Chat request received - message: {request.message}, conversation_id: {request.conversation_id}, user_id: {current_user.id}")
        # Create or get conversation
        conversation = None
        if request.conversation_id:
            logger.error(f"DEBUG: Looking for existing conversation: {request.conversation_id}")
            conversation = crud.get_conversation(session=session, conversation_id=request.conversation_id)
            if not conversation or conversation.user_id != current_user.id:
                logger.error(f"DEBUG: Conversation {request.conversation_id} not found or does not belong to user {current_user.id}")
                conversation = None  # Treat as new conversation
        
        # Create new conversation if none exists
        if not conversation:
            logger.error("DEBUG: Creating new conversation")
            conversation_data = ConversationCreate(
                title=request.message[:50] + "..." if len(request.message) > 50 else request.message,
                trip_id=request.trip_id
            )
            logger.error(f"DEBUG: Conversation data: {conversation_data}")
            conversation = crud.create_conversation(
                session=session, 
                conversation_in=conversation_data, 
                user_id=current_user.id
            )
            logger.error(f"DEBUG: Created conversation: {conversation.id}")
        
        # Save user message
        logger.error("DEBUG: Creating user message")
        user_message_data = ConversationMessageCreate(
            conversation_id=conversation.id,
            content=request.message,
            sender="user"
        )
        crud.create_conversation_message(session=session, message_in=user_message_data)
        logger.error("DEBUG: User message created")
        
        # Generate AI response using LLM
        logger.error("DEBUG: Calling LLM")
        prompt = f"User asks: {request.message}. Provide a concise, plain-text response with helpful travel advice, avoiding JSON or structured output."
        ai_response = call_llm(prompt)
        logger.info(f"yo actual response ho llm dekhi : {ai_response}")
        logger.error(f"DEBUG: LLM response length: {len(ai_response) if ai_response else 0}")
        
        # Check if response is JSON and convert to text if needed
        try:
            parsed_response = json.loads(ai_response)
            # If JSON, extract a summary
            destination = parsed_response.get("destination", "the destination")
            duration = parsed_response.get("duration_days", "a few days")
            ai_response = f"Consider visiting {destination} for {duration} days. Check local attractions and book accommodations early for the best deals."
            logger.error("DEBUG: Converted JSON response to plain text")
        except json.JSONDecodeError:
            # Response is already plain text
            pass
        
        # Save AI message
        logger.error("DEBUG: Creating AI message")
        ai_message_data = ConversationMessageCreate(
            conversation_id=conversation.id,
            content=ai_response,
            sender="ai"
        )
        crud.create_conversation_message(session=session, message_in=ai_message_data)
        logger.error("DEBUG: AI message created")
        
        # Update conversation with last message
        logger.error("DEBUG: Updating conversation")
        conversation.last_message = ai_response[:100]
        conversation.updated_at = datetime.utcnow()
        session.add(conversation)
        session.commit()
        logger.error("DEBUG: Conversation updated")
        
        suggestions = [
            {"type": "destination", "text": "Find destinations", "action": "search_destinations"},
            {"type": "itinerary", "text": "Plan itinerary", "action": "plan_itinerary"},
            {"type": "booking", "text": "Find bookings", "action": "search_bookings"}
        ]
        
        logger.error("DEBUG: Creating response")
        response = ChatResponse(
            response=ai_response,
            conversation_id=conversation.id,
            suggestions=suggestions
        )
        logger.error(f"DEBUG: Response created - conversation_id: {response.conversation_id}")
        return response
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"DEBUG: Chat error: {str(e)}")
        logger.error(f"DEBUG: Full traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.get("/suggestions/{trip_id}")
async def get_ai_suggestions(
    session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID
) -> Any:
    """Get AI-powered suggestions for a trip."""
    
    # Check trip access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # TODO: Use AI to generate personalized suggestions based on trip data
    suggestions = {
        "destinations": [
            {"name": "Local Attractions", "description": "Popular spots near your destination"},
            {"name": "Hidden Gems", "description": "Lesser-known but amazing places"}
        ],
        "activities": [
            {"name": "Cultural Experiences", "description": "Museums, historical sites, local culture"},
            {"name": "Outdoor Adventures", "description": "Hiking, beaches, nature activities"}
        ],
        "dining": [
            {"name": "Local Cuisine", "description": "Authentic local restaurants"},
            {"name": "Fine Dining", "description": "Upscale dining experiences"}
        ],
        "accommodation": [
            {"name": "Hotels", "description": "Traditional hotel options"},
            {"name": "Unique Stays", "description": "Boutique hotels, B&Bs, unique accommodations"}
        ]
    }
    
    return {"suggestions": suggestions}

@router.post("/optimize-itinerary/{trip_id}")
async def optimize_itinerary_with_ai(
    session: SessionDep, current_user: CurrentUser, trip_id: uuid.UUID
) -> Any:
    """Use AI to optimize an existing trip itinerary."""
    
    # Check trip access
    trip = session.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # TODO: Get existing itineraries and use AI to optimize them
    # This would involve:
    # 1. Fetching current itineraries
    # 2. Using AI to analyze and optimize the schedule
    # 3. Suggesting improvements for timing, logistics, etc.
    
    optimization_result = {
        "status": "success",
        "improvements": [
            "Optimized travel times between locations",
            "Added buffer time for popular attractions",
            "Suggested alternative routes to avoid crowds"
        ],
        "estimated_savings": {
            "time": "2 hours saved per day",
            "cost": "15% reduction in transportation costs"
        }
    }
    
    return optimization_result

# ===== EXTERNAL API INTEGRATION ENDPOINTS =====

@router.get("/search-destination/{destination}")
async def search_destination(
    destination: str,
    current_user: CurrentUser
) -> Any:
    """Search for comprehensive destination information."""
    
    try:
        destination_info = await travel_api_service.search_destination_info(destination)
        return destination_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Destination search failed: {str(e)}")

@router.get("/search-travel-options")
async def search_travel_options(
    origin: str,
    destination: str,
    departure_date: date,
    return_date: Optional[date] = None,
    travelers: int = 1,
    current_user: CurrentUser = None
) -> Any:
    """Search for flights and destination information."""
    
    try:
        travel_options = await travel_api_service.search_travel_options(
            origin, destination, departure_date, return_date, travelers
        )
        return travel_options
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Travel search failed: {str(e)}")

@router.get("/recommendations/{destination}")
async def get_trip_recommendations(
    destination: str,
    trip_type: str = "leisure",
    interests: Optional[List[str]] = None,
    budget: Optional[float] = None,
    current_user: CurrentUser = None
) -> Any:
    """Get personalized trip recommendations for a destination."""
    
    try:
        recommendations = await travel_api_service.get_trip_recommendations(
            destination, trip_type, interests or [], budget
        )
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")

@router.get("/weather/{destination}")
async def get_destination_weather(
    destination: str,
    current_user: CurrentUser = None
) -> Any:
    """Get weather information for a destination."""
    
    try:
        # First get location coordinates
        location = await travel_api_service.google_maps.geocode_address(destination)
        if not location:
            raise HTTPException(status_code=404, detail="Destination not found")
        
        # Get weather forecast
        weather_data = await travel_api_service.weather.get_forecast(
            location.latitude, location.longitude
        )
        
        return {
            "destination": destination,
            "location": location,
            "weather": weather_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather lookup failed: {str(e)}")

@router.get("/places/{destination}")
async def search_places(
    destination: str,
    place_type: Optional[str] = None,
    current_user: CurrentUser = None
) -> Any:
    """Search for places (attractions, restaurants, hotels) in a destination."""
    
    try:
        # First get location coordinates
        location = await travel_api_service.google_maps.geocode_address(destination)
        if not location:
            raise HTTPException(status_code=404, detail="Destination not found")
        
        # Search for places
        places = await travel_api_service.google_maps.search_places(
            f"{place_type or 'places'} in {destination}",
            (location.latitude, location.longitude),
            place_type=place_type
        )
        
        return {
            "destination": destination,
            "place_type": place_type,
            "places": places
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Places search failed: {str(e)}")

@router.get("/flights")
async def search_flights(
    origin: str,
    destination: str,
    departure_date: date,
    return_date: Optional[date] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    current_user: CurrentUser = None
) -> Any:
    """Search for flights between two destinations."""
    
    try:
        flights = await travel_api_service.amadeus.search_flights(
            origin, destination, departure_date, return_date, adults, children, infants
        )
        
        return {
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "return_date": return_date,
            "flights": flights
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flight search failed: {str(e)}")

@router.get("/hotels/{city_code}")
async def search_hotels(
    city_code: str,
    check_in: date,
    check_out: date,
    adults: int = 1,
    rooms: int = 1,
    current_user: CurrentUser = None
) -> Any:
    """Search for hotels in a city."""
    
    try:
        hotels = await travel_api_service.amadeus.search_hotels(
            city_code, check_in, check_out, adults, rooms
        )
        
        return {
            "city_code": city_code,
            "check_in": check_in,
            "check_out": check_out,
            "hotels": hotels
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hotel search failed: {str(e)}")
