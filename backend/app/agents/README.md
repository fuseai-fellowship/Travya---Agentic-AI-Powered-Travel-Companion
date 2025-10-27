# AI Agents Module - Implementation Flow

This document describes the multi-agent system used in Travya for intelligent travel planning, research, and booking.

## Architecture Overview

The agent system follows a **multi-agent coordination pattern** where specialized agents handle different aspects of travel planning:

```
┌─────────────────────────────────────────────────────────┐
│                   Orchestrator Agent                    │
│              (Coordinates all other agents)              │
└─────────────┬───────────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│Research│ │Planner│ │Booker │
│ Agent │ │ Agent │ │ Agent │
└───────┘ └───────┘ └───────┘
```

## Code Flow: How Agents Work Together

### 1. Agent Invocation Flow

When a user requests trip planning, here's how the code flows:

```
frontend/src/routes/_layout/plan-trip.tsx
  ↓ User submits trip planning form
  ↓ POST /api/v1/travel/plan
  
backend/app/api/routes/ai_travel.py
  ↓ plan_trip_with_ai() endpoint receives request
  ↓ Validates request (destination, dates, budget)
  ↓ Prepares trip_request dictionary
  ↓ Calls plan_trip_with_agents() from orchestrator
  
backend/app/agents/orchestrator.py
  ↓ plan_trip_with_agents() function
  ↓ Initializes orchestrator agent
  ↓ Creates session context
  ↓ Delegates to specialized agents in sequence:
    1. Research Agent → Gather information
    2. Planner Agent → Create itinerary
    3. Booker Agent → Handle bookings
  
backend/app/agents/[agent].py
  ↓ Each agent processes its task
  ↓ Returns results to orchestrator
  ↓ Orchestrator synthesizes final response
  
backend/app/api/routes/ai_travel.py
  ↓ Receives orchestrated response
  ↓ Creates Trip record in database
  ↓ Saves itinerary data
  ↓ Returns comprehensive trip plan
```

### 2. Individual Agent Implementation

#### Research Agent (`improved_research_agent.py`)

**Purpose**: Gather information about destinations, attractions, weather, and travel conditions.

**Code Flow:**
```python
# 1. Agent receives request
async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
    destination = request.get("destination")
    
    # 2. Query RAG system for knowledge base information
    knowledge_results = await self._query_rag_system(destination)
    
    # 3. Call external APIs (Google Places, Weather)
    weather_data = await self._get_weather(destination)
    places_data = await self._get_places(destination)
    
    # 4. Synthesize research results
    results = {
        "knowledge": knowledge_results,
        "weather": weather_data,
        "attractions": places_data
    }
    
    # 5. Return structured response
    return AgentResponse(
        success=True,
        data=results,
        confidence=0.85
    )
```

**Tools Used:**
- `rag_system.py` - Vector database for knowledge retrieval
- `tools.py` - Google Places API, Weather API
- `external_apis.py` - External service integrations

#### Planner Agent (`improved_planner_agent.py`)

**Purpose**: Create detailed itineraries based on research and user preferences.

**Code Flow:**
```python
# 1. Agent receives research data and user preferences
async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
    research_data = request.get("research_data")
    user_prefs = request.get("context", {})
    
    # 2. Generate itinerary using LLM
    itinerary_prompt = self._build_itinerary_prompt(
        research_data, 
        user_prefs
    )
    
    itinerary = await self._call_llm(itinerary_prompt)
    
    # 3. Structure itinerary (days, activities, timing)
    structured_itinerary = self._structure_itinerary(itinerary)
    
    # 4. Add enhancements (packing lists, tips)
    enhanced = self._add_enhancements(structured_itinerary)
    
    # 5. Return complete itinerary
    return AgentResponse(
        success=True,
        data={"itinerary": enhanced},
        confidence=0.90
    )
```

**LLM Integration:**
- Uses `app/core/llm.py` for OpenAI/Google AI calls
- Structured JSON output for reliability
- Validates output format

#### Booker Agent (`improved_booker_agent.py`)

**Purpose**: Handle flight searches, hotel bookings, and payment processing.

**Code Flow:**
```python
# 1. Agent receives booking request
async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
    booking_type = request.get("type")  # "flight" or "hotel"
    
    # 2. Search for available options
    if booking_type == "flight":
        results = await self._search_flights(request)
    elif booking_type == "hotel":
        results = await self._search_hotels(request)
    
    # 3. Create booking intent (payment)
    payment_intent = await self._create_payment_intent(results)
    
    # 4. Confirm booking
    booking = await self._confirm_booking(payment_intent)
    
    # 5. Return booking confirmation
    return AgentResponse(
        success=True,
        data={"booking": booking},
        confidence=0.80
    )
```

**External Integrations:**
- Amadeus API for flight search
- Stripe for payment processing
- Booking.com API for hotels

### 3. Orchestrator Coordination

The orchestrator (`improved_orchestrator.py`) coordinates agents using a **workflow-based approach**:

```python
class ImprovedOrchestrator(BaseAgent):
    # Workflow definitions
    workflows = {
        "trip_planning": ["research", "planner", "booker"],
        "quick_search": ["research"],
        "itinerary_creation": ["research", "planner"],
        "booking_only": ["booker"],
        "research_only": ["research"]
    }
    
    async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
        # 1. Determine workflow based on request type
        workflow = self._determine_workflow(request_type, request)
        
        # 2. Execute agents in sequence
        results = []
        for agent_name in workflow:
            agent = agent_registry.get_agent(agent_name)
            result = await agent.process_request(request)
            results.append(result)
            
            # Pass results to next agent
            request["previous_results"] = result.data
        
        # 3. Synthesize final response
        synthesized_response = self._synthesize_results(results)
        
        # 4. Return comprehensive response
        return AgentResponse(
            success=True,
            data=synthesized_response,
            confidence=0.85
        )
```

### 4. Session & Memory Management

**Session Context (`sessions.py`)**:
```python
# Maintains conversation context across agent interactions
session_context = {
    "user_id": "user123",
    "session_id": "session456",
    "conversation_history": [...],
    "preferences": {...},
    "current_state": "planning"
}

# Stored in Redis for persistence
await redis.setex(
    f"session:{session_id}", 
    TTL, 
    json.dumps(session_context)
)
```

**Memory System** (`rag_system.py`):
```python
# Vector database for knowledge retrieval
class VectorTravelRAGService:
    async def query(self, user_query: str) -> List[Dict]:
        # 1. Convert query to vector
        query_vector = await self.llm.embed_query(user_query)
        
        # 2. Search similar content
        results = await self.vector_db.similarity_search(
            query_vector,
            top_k=5
        )
        
        # 3. Return relevant knowledge
        return results
```

## Request Flow Example: "Plan a Trip to Paris"

### Step-by-Step Execution

1. **Frontend Request** (`plan-trip.tsx`):
```typescript
const response = await TravelService.planTrip({
  destination: "Paris",
  start_date: "2024-06-01",
  end_date: "2024-06-07",
  budget: 2000,
  trip_type: "leisure",
  interests: ["museums", "food"]
});
```

2. **API Endpoint** (`ai_travel.py`):
```python
@router.post("/plan-trip")
async def plan_trip_with_ai(request: TripPlanningRequest):
    # Calls orchestrator
    ai_response = await plan_trip_with_agents(
        user_id=current_user.id,
        session_id=session_id,
        trip_request={...},
        db=session
    )
```

3. **Orchestrator** (`orchestrator.py`):
```python
async def plan_trip_with_agents(...):
    # 1. Initialize orchestrator
    orchestrator = ImprovedOrchestrator()
    
    # 2. Execute workflow: ["research", "planner", "booker"]
    for agent_name in ["research", "planner", "booker"]:
        result = await agent.process(request)
        request["previous_results"] = result
```

4. **Agent Execution**:
   - **Research**: Queries Google Places for Paris attractions, gets weather
   - **Planner**: Creates day-by-day itinerary with activities
   - **Booker**: Searches flights and hotels (optional)

5. **Database Storage** (`ai_travel.py`):
```python
# Create Trip record
trip = Trip.create(...)
trip.ai_itinerary_data = json.dumps(itinerary)

# Save to PostgreSQL
session.add(trip)
session.commit()
```

6. **Response**:
```json
{
  "status": "success",
  "trip_id": "uuid-123",
  "research": {...},
  "itinerary": [...],
  "bookings": {...}
}
```

## Agent Communication Pattern

Agents communicate using a **message passing system**:

```python
# Agent sends message
message = AgentMessage(
    from_agent="research",
    to_agent="planner",
    type="data",
    data={"attractions": [...], "weather": {...}}
)

# Message is stored in registry
agent_registry.send_message(message)

# Receiving agent processes message
planner_agent.receive_message(message)
```

## Error Handling & Recovery

```python
# Agent with error recovery
try:
    result = await agent.process_request(request)
except ExternalAPIError:
    # Fallback to mock data for development
    result = self._get_mock_data()
except ValidationError:
    # Return structured error
    return AgentResponse(
        success=False,
        error="Invalid request format"
    )
```

## Performance Optimizations

1. **Caching**: Research results cached in Redis
2. **Parallel Execution**: Independent agents run in parallel when possible
3. **Streaming**: Real-time updates via Server-Sent Events
4. **Batch Processing**: Multiple requests processed together

## Testing

```python
# Test individual agent
def test_research_agent():
    agent = ImprovedResearchAgent()
    request = {"destination": "Paris"}
    response = await agent.process_request(request)
    assert response.success == True
    assert "attractions" in response.data
```

## Configuration

Environment variables in `backend/.env`:
```bash
OPENAI_API_KEY=sk-...
GOOGLE_AI_API_KEY=...
AMADEUS_API_KEY=...
GOOGLE_MAPS_API_KEY=...
REDIS_URL=redis://redis:6379/0
```

## Dependencies

- `app/core/llm.py` - LLM interface
- `app/services/vector_rag.py` - RAG system
- `app/services/redis_cache.py` - Caching layer
- `app/services/external_apis.py` - External API clients
