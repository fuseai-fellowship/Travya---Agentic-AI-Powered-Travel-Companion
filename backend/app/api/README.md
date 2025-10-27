# Backend API Module - Request Flow

This document describes how HTTP requests flow through the Travya backend API.

## API Architecture

```
HTTP Request → FastAPI Router → Endpoint Function → Agent/Service → Database
                                                           ↓
                                                    Response Flow ←
```

## Core API Structure

### Main API Router (`backend/app/api/main.py`)

All API routes are registered here:

```python
api_router = APIRouter()
api_router.include_router(login.router)        # /api/v1/login/*
api_router.include_router(users.router)         # /api/v1/users/*
api_router.include_router(items.router)        # /api/v1/items/*
api_router.include_router(travel.router)        # /api/v1/travel/*
api_router.include_router(ai_travel.router)     # /api/v1/ai-travel/*
api_router.include_router(conversations.router)# /api/v1/conversations/*
api_router.include_router(agents.router)       # /api/v1/agents/*
```

## Request Flow Examples

### 1. Trip Planning Request

**User Journey:**
```
Frontend: plan-trip.tsx
  ↓ User fills form and clicks "Plan Trip"
  ↓ POST /api/v1/ai-travel/plan-trip
  ↓ {
      "destination": "Paris",
      "start_date": "2024-06-01",
      "end_date": "2024-06-07",
      "budget": 2000,
      "trip_type": "leisure"
    }
```

**Backend Flow:**

```python
# 1. Request arrives at endpoint
@router.post("/plan-trip", response_model=TripPlanningResponse)
async def plan_trip_with_ai(
    *, session: SessionDep, current_user: CurrentUser, request: TripPlanningRequest
):
    # 2. Validation
    if not request.destination:
        raise HTTPException(status_code=400, detail="Destination required")
    
    # 3. Prepare trip request for agents
    trip_request = {
        "destination": request.destination,
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "duration": (request.end_date - request.start_date).days,
        "budget": request.budget,
        "trip_type": request.trip_type,
        "interests": request.interests
    }
    
    # 4. Generate session ID
    session_id = f"trip_plan_{uuid.uuid4().hex[:8]}"
    
    # 5. Call agent orchestrator
    ai_response = await plan_trip_with_agents(
        user_id=str(current_user.id),
        session_id=session_id,
        trip_request=trip_request,
        db=session
    )
    
    # 6. Extract itinerary data
    itinerary_data = ai_response.get("itinerary", {})
    
    # 7. Create Trip in database
    trip_data = TripCreate(
        title=f"Trip to {request.destination}",
        description=f"AI-planned {request.trip_type} trip",
        destination=request.destination,
        start_date=request.start_date,
        end_date=request.end_date,
        budget=request.budget,
        ai_itinerary_data=json.dumps(itinerary_data)
    )
    
    trip = Trip.model_validate(trip_data, update={"owner_id": current_user.id})
    session.add(trip)
    session.commit()
    
    # 8. Return response
    return TripPlanningResponse(
        status="success",
        trip_id=trip.id,
        research=ai_response.get("research", {}),
        itinerary=itinerary_data,
        bookings=ai_response.get("bookings", {})
    )
```

**Agent Orchestration:**
```python
# backend/app/agents/orchestrator.py
async def plan_trip_with_agents(user_id, session_id, trip_request, db):
    # 1. Initialize orchestrator
    orchestrator = ImprovedOrchestrator()
    
    # 2. Execute agent workflow
    # Workflow: ["research", "planner", "booker"]
    
    results = []
    for agent_name in ["research", "planner", "booker"]:
        agent = agent_registry.get_agent(agent_name)
        result = await agent.process_request({
            "type": agent_name,
            "query": f"Plan trip to {trip_request['destination']}",
            "context": trip_request
        })
        results.append(result)
    
    # 3. Synthesize results
    synthesized = {
        "research": results[0].data,
        "itinerary": results[1].data,
        "bookings": results[2].data if len(results) > 2 else {}
    }
    
    return {"status": "success", **synthesized}
```

### 2. AI Chat Request

**User Journey:**
```
Frontend: chat.tsx
  ↓ User types message and presses Enter
  ↓ POST /api/v1/conversations/send
  ↓ {
      "message": "What's the weather in Paris?",
      "conversation_id": "conv-123"
    }
```

**Backend Flow:**

```python
# backend/app/api/routes/conversations.py
@router.post("/send")
async def send_message(
    *, session: SessionDep, current_user: CurrentUser, message: ChatMessageCreate
):
    # 1. Get or create conversation
    conversation = await crud.get_or_create_conversation(
        session=session,
        conversation_id=message.conversation_id,
        user_id=current_user.id
    )
    
    # 2. Save user message
    user_msg = ConversationMessageCreate(
        message=message.message,
        sender="user"
    )
    crud.create_conversation_message(session, conversation.id, user_msg)
    
    # 3. Process with RAG system
    from app.services.vector_rag import VectorTravelRAGService
    async with VectorTravelRAGService() as rag:
        # Retrieve relevant context
        context = await rag.query(message.message, user_id=current_user.id)
        
        # Generate AI response
        ai_response = await rag.generate_response(
            user_query=message.message,
            context=context,
            conversation_history=conversation.messages
        )
    
    # 4. Save AI message
    ai_msg = ConversationMessageCreate(
        message=ai_response,
        sender="assistant"
    )
    crud.create_conversation_message(session, conversation.id, ai_msg)
    
    # 5. Return response
    return {
        "message": ai_response,
        "conversation_id": conversation.id
    }
```

### 3. Travel Notes (Items) Request

**User Journey:**
```
Frontend: items.tsx
  ↓ User clicks "Add Note"
  ↓ User fills form with title and description
  ↓ POST /api/v1/items/
  ↓ {
      "title": "Don't forget passport",
      "description": "Check passport validity before trip"
    }
```

**Backend Flow:**

```python
# backend/app/api/routes/items.py
@router.post("/")
def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    # 1. Validate input
    if not item_in.title:
        raise HTTPException(status_code=400, detail="Title required")
    
    # 2. Create item record
    item = Item.model_validate(item_in, update={"owner_id": current_user.id})
    
    # 3. Save to database
    session.add(item)
    session.commit()
    session.refresh(item)
    
    # 4. Return created item
    return item
```

### 4. Map Parser Request

**User Journey:**
```
Frontend: MapParserComponent.tsx
  ↓ User uploads map image
  ↓ POST /api/v1/map-parser/parse
  ↓ MultipartFormData with image file
```

**Backend Flow:**

```python
# backend/app/api/routes/map_parser.py
@router.post("/parse")
async def parse_itinerary(
    request: ParseItineraryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Get uploaded image
    image_file = await request.file.read()
    
    # 2. Process image with OCR and CV
    from app.services.map_parser import MapParserService
    
    parser = MapParserService()
    locations = await parser.process_image(image_file)
    
    # 3. Geocode locations
    geocoded = []
    for loc in locations:
        coordinates = await geocode_location(loc["name"])
        geocoded.append({
            "name": loc["name"],
            "lat": coordinates["lat"],
            "lng": coordinates["lng"],
            "type": loc.get("type", "unknown")
        })
    
    # 4. Return geocoded locations
    return {
        "locations": geocoded,
        "map_url": f"/api/v1/files/{saved_image_id}"
    }
```

## Authentication Flow

All API endpoints (except public ones) require JWT authentication:

```python
# backend/app/api/deps.py
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # 1. Decode JWT token
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # 2. Extract user ID
    user_id: str = payload.get("sub")
    
    # 3. Get user from database
    user = session.get(User, user_id)
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # 4. Return current user
    return user

# Usage in endpoints
@router.get("/trips")
def read_trips(
    session: SessionDep,
    current_user: CurrentUser = Depends(get_current_user)
):
    # current_user is automatically injected
    ...
```

## Error Handling

```python
try:
    result = await some_operation()
except ValidationError as e:
    raise HTTPException(status_code=422, detail=str(e))
except NotFoundError as e:
    raise HTTPException(status_code=404, detail=str(e))
except ExternalAPIError as e:
    logger.error(f"External API error: {e}")
    raise HTTPException(
        status_code=503,
        detail="Service temporarily unavailable"
    )
```

## Response Format

All responses follow a consistent structure:

```python
# Success response
{
    "status": "success",
    "data": {...},
    "message": "Operation completed successfully"
}

# Error response
{
    "status": "error",
    "detail": "Error message",
    "code": "ERROR_CODE"
}
```

## Database Transactions

```python
try:
    # Start transaction
    session.begin()
    
    # Perform operations
    session.add(new_trip)
    session.add(new_itinerary)
    
    # Commit
    session.commit()
    
except Exception as e:
    # Rollback on error
    session.rollback()
    raise HTTPException(
        status_code=500,
        detail=f"Database error: {str(e)}"
    )
```

## Caching Strategy

```python
# Cache for frequently accessed data
@cache(ttl=3600)
async def get_popular_destinations(session: SessionDep):
    # Expensive query cached for 1 hour
    return session.query(Destination).filter_by(popular=True).all()
```

## Testing

```python
# Test API endpoint
def test_plan_trip(client, auth_headers):
    response = client.post(
        "/api/v1/ai-travel/plan-trip",
        json={"destination": "Paris", "start_date": "2024-06-01", "end_date": "2024-06-07"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "trip_id" in response.json()
```

## Environment-Based Routing

```python
# Local environment: Include private endpoints
if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)  # /admin, /debug, etc.

# Production: Exclude private endpoints
else:
    pass  # Private endpoints not available
```

## Key API Modules

- `ai_travel.py` - AI-powered trip planning endpoints
- `travel.py` - Standard trip management endpoints
- `conversations.py` - AI chat endpoints
- `items.py` - Travel notes endpoints
- `map_parser.py` - Map parsing endpoints
- `photo_gallery.py` - Photo gallery endpoints
- `agents.py` - Direct agent query endpoints
