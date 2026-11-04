# Request Processing Flow - Mermaid Diagram

## Basic Flow Diagram

```mermaid
flowchart TD
    A[User Request<br/>Frontend: plan-trip.tsx] --> B[API Endpoint<br/>POST /api/v1/ai-travel/plan-trip]
    B --> C[FastAPI Router<br/>ai_travel.py]
    C --> D[Orchestrator Agent<br/>ImprovedOrchestrator]
    
    D --> E[Research Agent<br/>Data Gathering]
    D --> F[Planner Agent<br/>Itinerary Creation]
    D --> G[Booker Agent<br/>Booking Handling]
    
    E --> H[External APIs<br/>Google Places, Weather]
    E --> I[RAG System<br/>Vector Database]
    
    F --> J[LLM Processing<br/>OpenAI/Google AI]
    
    G --> K[Amadeus API<br/>Flight Search]
    G --> L[Stripe API<br/>Payment Processing]
    
    E --> M[Response Synthesis]
    F --> M
    G --> M
    
    M --> N[Database Storage<br/>PostgreSQL]
    N --> O[Response to Frontend<br/>Trip Planning Response]
    O --> A
    
    style A fill:#007aff,stroke:#0051d5,color:#fff
    style B fill:#10b981,stroke:#059669,color:#fff
    style D fill:#f59e0b,stroke:#d97706,color:#fff
    style E fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style F fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style G fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style N fill:#ef4444,stroke:#dc2626,color:#fff
    style O fill:#007aff,stroke:#0051d5,color:#fff
```

## Detailed Flow with Components

```mermaid
flowchart TB
    subgraph Frontend["Frontend Layer (React)"]
        A[User Interface<br/>plan-trip.tsx]
        A1[Form Submission]
        A2[API Client Call<br/>TravelService.planTrip]
        A --> A1
        A1 --> A2
    end
    
    subgraph Backend["Backend Layer (FastAPI)"]
        B[API Endpoint<br/>plan_trip_with_ai]
        B1[Request Validation]
        B2[Session Creation]
        B --> B1
        B1 --> B2
        
        subgraph Agents["AI Agent System"]
            C[Orchestrator Agent<br/>ImprovedOrchestrator]
            
            subgraph Specialized["Specialized Agents"]
                D[Research Agent<br/>improved_research_agent.py]
                E[Planner Agent<br/>improved_planner_agent.py]
                F[Booker Agent<br/>improved_booker_agent.py]
            end
            
            C --> D
            C --> E
            C --> F
            
            subgraph ResearchFlow["Research Flow"]
                D --> D1[RAG Query<br/>vector_rag.py]
                D --> D2[Google Places API]
                D --> D3[Weather API]
                D1 --> D4[Knowledge Retrieval]
                D2 --> D4
                D3 --> D4
            end
            
            subgraph PlannerFlow["Planner Flow"]
                E --> E1[LLM Call<br/>app/core/llm.py]
                E1 --> E2[Itinerary Generation]
                E2 --> E3[Activity Scheduling]
                E3 --> E4[Budget Optimization]
            end
            
            subgraph BookerFlow["Booker Flow"]
                F --> F1[Amadeus API<br/>Flight Search]
                F --> F2[Stripe API<br/>Payment Intent]
                F1 --> F3[Booking Creation]
                F2 --> F3
            end
            
            D4 --> G[Response Synthesis]
            E4 --> G
            F3 --> G
        end
        
        B2 --> C
        
        subgraph Database["Data Layer"]
            H[SQLModel ORM<br/>crud.py]
            I[(PostgreSQL<br/>Trip Storage)]
            J[(Redis<br/>Cache & Sessions)]
            
            G --> H
            H --> I
            H --> J
        end
        
        K[Response Object<br/>TripPlanningResponse]
        H --> K
    end
    
    A2 -->|HTTP POST Request| B
    K -->|JSON Response| A2
    A2 -->|Update UI| A
    
    style A fill:#007aff,stroke:#0051d5,color:#fff
    style C fill:#f59e0b,stroke:#d97706,color:#fff
    style D fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style E fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style F fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style I fill:#ef4444,stroke:#dc2626,color:#fff
    style J fill:#ef4444,stroke:#dc2626,color:#fff
    style G fill:#10b981,stroke:#059669,color:#fff
```

## Sequence Diagram

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
    participant DB as PostgreSQL
    participant Redis as Redis Cache
    
    User->>Frontend: Fill trip planning form
    Frontend->>API: POST /api/v1/ai-travel/plan-trip
    API->>API: Validate request
    API->>Orch: plan_trip_with_agents()
    
    Orch->>Research: Delegate research task
    Research->>RAG: Query knowledge base
    RAG-->>Research: Return relevant data
    Research->>Research: Call Google Places API
    Research->>Research: Get weather data
    Research-->>Orch: Research results
    
    Orch->>Planner: Delegate planning task
    Planner->>LLM: Generate itinerary
    LLM-->>Planner: Structured itinerary
    Planner-->>Orch: Planning results
    
    Orch->>Booker: Delegate booking task (optional)
    Booker->>Booker: Search flights (Amadeus)
    Booker->>Booker: Process payments (Stripe)
    Booker-->>Orch: Booking results
    
    Orch->>Orch: Synthesize responses
    
    Orch->>DB: Create Trip record
    Orch->>Redis: Cache results
    DB-->>Orch: Trip ID
    
    Orch-->>API: Complete trip plan
    API->>API: Format response
    API-->>Frontend: TripPlanningResponse JSON
    Frontend->>Frontend: Update UI with results
    Frontend-->>User: Display trip plan
```

## Component Interaction Diagram

```mermaid
graph LR
    subgraph "Frontend (React)"
        A[plan-trip.tsx]
        B[TravelService]
        C[QueryClient]
    end
    
    subgraph "Backend API (FastAPI)"
        D[ai_travel.py]
        E[SessionDep]
        F[CurrentUser]
    end
    
    subgraph "AI Agents"
        G[Orchestrator]
        H[Research]
        I[Planner]
        J[Booker]
    end
    
    subgraph "Services"
        K[vector_rag.py]
        L[llm.py]
        M[external_apis.py]
        N[redis_cache.py]
    end
    
    subgraph "Data Storage"
        O[(PostgreSQL)]
        P[(Redis)]
    end
    
    A -->|1. Submit Form| B
    B -->|2. POST Request| D
    D -->|3. Validate| E
    E -->|4. Get User| F
    D -->|5. Call Agent| G
    G -->|6. Delegate| H
    G -->|7. Delegate| I
    G -->|8. Delegate| J
    H -->|9. Query| K
    H -->|10. API Call| M
    I -->|11. LLM Call| L
    J -->|12. API Call| M
    K -->|13. Cache Check| P
    G -->|14. Store Results| O
    G -->|15. Cache Data| P
    D -->|16. Response| B
    B -->|17. Update UI| C
    C -->|18. Render| A
    
    style A fill:#007aff
    style G fill:#f59e0b
    style O fill:#ef4444
    style P fill:#ef4444
```

## Simplified Production Flow

```mermaid
flowchart TD
    Start([User Clicks 'Plan Trip']:::user) --> Validate{Validate Form Data}
    Validate -->|Valid| Send[Send POST Request]:::api
    Validate -->|Invalid| Error[Show Error]:::error
    Error --> Start
    
    Send --> Receive[API Receives Request]:::api
    Receive --> Auth{Authenticate User}
    Auth -->|Unauthorized| Redirect[Redirect to Login]:::error
    Auth -->|Authorized| Orchestrate[Call Orchestrator]:::agent
    
    Orchestrate --> Parallel{Parallel Execution}
    
    Parallel --> Research[Research Agent]:::agent
    Parallel --> Plan[Planner Agent]:::agent
    Parallel --> Book[Booker Agent]:::agent
    
    Research --> RAG[Query RAG System]:::service
    Research --> API1[Call External APIs]:::service
    RAG --> Combine1[Combine Research Data]:::process
    API1 --> Combine1
    
    Plan --> LLM[Call LLM]:::service
    LLM --> Generate[Generate Itinerary]:::process
    
    Book --> Flight[Search Flights]:::service
    Book --> Payment[Process Payment]:::service
    
    Combine1 --> Synthesize[Synthesize Response]:::process
    Generate --> Synthesize
    Flight --> Synthesize
    Payment --> Synthesize
    
    Synthesize --> Save[Save to Database]:::database
    Save --> Cache[Update Cache]:::database
    Cache --> Response[Return Response]:::api
    
    Response --> Display[Display Results]:::frontend
    Display --> End([Trip Created Successfully]:::success)
    
    classDef user fill:#007aff,stroke:#0051d5,color:#fff
    classDef api fill:#10b981,stroke:#059669,color:#fff
    classDef agent fill:#f59e0b,stroke:#d97706,color:#fff
    classDef service fill:#8b5cf6,stroke:#7c3aed,color:#fff
    classDef process fill:#06b6d4,stroke:#0891b2,color:#fff
    classDef database fill:#ef4444,stroke:#dc2626,color:#fff
    classDef error fill:#f87171,stroke:#ef4444,color:#fff
    classDef success fill:#10b981,stroke:#059669,color:#fff
    classDef frontend fill:#007aff,stroke:#0051d5,color:#fff
```

## Usage in Documentation

Copy any of these Mermaid diagrams into your:
- README.md
- Presentation slides (if supported)
- Documentation files
- Project reports

Most markdown viewers (GitHub, GitLab, VS Code with extension) render Mermaid diagrams automatically.

