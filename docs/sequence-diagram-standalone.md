# Standalone Mermaid Sequence Diagrams

Copy each diagram individually to Mermaid Live Editor.

## 1. Complete Trip Planning Flow (Copy this to Mermaid Live Editor)

```mermaid
sequenceDiagram
    participant User as User Browser
    participant Frontend as React Frontend<br/>plan-trip.tsx
    participant API as FastAPI Endpoint<br/>ai_travel.py
    participant Orch as Orchestrator Agent<br/>ImprovedOrchestrator
    participant Research as Research Agent<br/>improved_research_agent.py
    participant Planner as Planner Agent<br/>improved_planner_agent.py
    participant Booker as Booker Agent<br/>improved_booker_agent.py
    participant RAG as RAG System<br/>vector_rag.py
    participant LLM as LLM Service<br/>core/llm.py
    participant ExtAPI as External APIs<br/>Google Places, Weather
    participant Amadeus as Amadeus API<br/>Flight Search
    participant Stripe as Stripe API<br/>Payment Processing
    participant PostgreSQL as PostgreSQL<br/>Database
    participant Redis as Redis<br/>Cache & Sessions

    User->>Frontend: Fill trip planning form<br/>(destination, dates, budget)
    Frontend->>Frontend: Validate form data
    
    Frontend->>API: POST /api/v1/ai-travel/plan-trip<br/>{destination, start_date, end_date, budget, trip_type}
    
    API->>API: Validate request<br/>(check dates, destination)
    API->>API: Generate session_id<br/>Create trip_request dict
    
    API->>Orch: plan_trip_with_agents<br/>(user_id, session_id, trip_request, db)
    
    Note over Orch: Initialize workflow: research, planner, booker
    
    rect rgb(255, 245, 238)
        Note over Orch,Research: Phase 1: Research
        Orch->>Research: Delegate research task<br/>process_request(trip_request)
        
        Research->>RAG: Query knowledge base<br/>vector_rag.query(destination)
        RAG->>RAG: Embed query<br/>Search FAISS vector DB
        RAG-->>Research: Return relevant knowledge
        
        Research->>ExtAPI: Call Google Places API<br/>Get attractions & locations
        ExtAPI-->>Research: Return places data
        
        Research->>ExtAPI: Get weather data<br/>Weather API for destination
        ExtAPI-->>Research: Return weather forecast
        
        Research->>Research: Synthesize research data<br/>Combine RAG + Places + Weather
        Research-->>Orch: Research results<br/>{knowledge, attractions, weather}
    end
    
    rect rgb(238, 245, 255)
        Note over Orch,Planner: Phase 2: Planning
        Orch->>Planner: Delegate planning task<br/>process_request(trip_request + research_data)
        
        Planner->>LLM: Generate itinerary<br/>call_llm(prompt with research + preferences)
        LLM->>LLM: Process with OpenAI/Google AI<br/>Create structured itinerary
        LLM-->>Planner: Return JSON itinerary<br/>{days, activities, timing, budget}
        
        Planner->>Planner: Structure itinerary<br/>Organize days and activities
        Planner->>Planner: Add enhancements<br/>(packing lists, tips, local customs)
        Planner-->>Orch: Planning results<br/>{itinerary, suggestions}
    end
    
    rect rgb(245, 255, 245)
        Note over Orch,Booker: Phase 3: Booking (Optional)
        alt If booking requested
            Orch->>Booker: Delegate booking task<br/>process_request(flight/hotel requirements)
            
            Booker->>Amadeus: Search flights<br/>origin, destination, dates
            Amadeus-->>Booker: Return flight options
            
            Booker->>Booker: Select best flight<br/>Compare prices & times
            
            Booker->>Stripe: Create payment intent<br/>payment_intent.create(amount)
            Stripe-->>Booker: Return payment intent ID
            
            Booker->>Booker: Confirm booking<br/>Save booking details
            Booker-->>Orch: Booking results<br/>{flight_id, payment_intent, status}
        end
    end
    
    Orch->>Orch: Synthesize all responses<br/>Combine research + itinerary + bookings
    
    Orch->>PostgreSQL: Create Trip record<br/>INSERT INTO trips (...)
    PostgreSQL-->>Orch: Return trip_id
    
    Orch->>PostgreSQL: Save itinerary data<br/>UPDATE trips SET ai_itinerary_data = ...
    PostgreSQL-->>Orch: Confirm saved
    
    Orch->>Redis: Cache trip data<br/>SET trip:{trip_id} {...}
    Redis-->>Orch: Confirm cached
    
    Orch-->>API: Return complete trip plan<br/>{status, trip_id, research, itinerary, bookings}
    
    API->>API: Format TripPlanningResponse<br/>Structure JSON response
    
    API-->>Frontend: HTTP 200<br/>TripPlanningResponse JSON
    
    Frontend->>Frontend: Update TanStack Query cache<br/>Invalidate trips query
    Frontend->>Frontend: Navigate to trip details<br/>/trips/{trip_id}
    Frontend-->>User: Display trip plan<br/>(itinerary, bookings, recommendations)
    
    Note over User,Redis: Trip planning complete!
```

## 2. Simplified Trip Planning Flow (Alternative - Easier to render)

```mermaid
sequenceDiagram
    participant User as User Browser
    participant Frontend as React Frontend
    participant API as FastAPI Endpoint
    participant Orch as Orchestrator Agent
    participant Research as Research Agent
    participant Planner as Planner Agent
    participant Booker as Booker Agent
    participant RAG as RAG System
    participant LLM as LLM Service
    participant ExtAPI as External APIs
    participant DB as PostgreSQL
    participant Redis as Redis

    User->>Frontend: Submit trip planning form
    Frontend->>API: POST /api/v1/ai-travel/plan-trip
    
    API->>API: Validate request
    API->>Orch: plan_trip_with_agents()
    
    Orch->>Research: Delegate research task
    Research->>RAG: Query knowledge base
    RAG-->>Research: Return knowledge
    Research->>ExtAPI: Get Places & Weather
    ExtAPI-->>Research: Return data
    Research-->>Orch: Research results
    
    Orch->>Planner: Delegate planning task
    Planner->>LLM: Generate itinerary
    LLM-->>Planner: Return itinerary
    Planner-->>Orch: Planning results
    
    alt Booking requested
        Orch->>Booker: Delegate booking task
        Booker->>ExtAPI: Search flights
        ExtAPI-->>Booker: Return options
        Booker-->>Orch: Booking results
    end
    
    Orch->>Orch: Synthesize responses
    Orch->>DB: Save Trip record
    Orch->>Redis: Cache results
    DB-->>Orch: trip_id
    
    Orch-->>API: Complete trip plan
    API->>API: Format response
    API-->>Frontend: TripPlanningResponse
    Frontend->>Frontend: Update UI
    Frontend-->>User: Display trip plan
```

