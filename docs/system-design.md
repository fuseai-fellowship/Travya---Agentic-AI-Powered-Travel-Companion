# System Design - Travya Architecture

## High-Level Architecture Overview

Travya follows a **layered architecture** with clear separation between frontend, backend, AI agents, and data layers.

## Complete System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Client Layer"]
        A[React Frontend<br/>TypeScript + Vite] -->|HTTPS/REST API| B[FastAPI Backend<br/>Python 3.11+]
        A -->|Server-Sent Events| B
    end
    
    subgraph APILayer["API Layer"]
        B --> C[Authentication<br/>JWT Token Validation]
        B --> D[Route Handlers<br/>ai_travel.py, travel.py, etc.]
        D --> E[Request Validation<br/>Pydantic Models]
    end
    
    subgraph AgentLayer["AI Agent Layer"]
        E --> F[Orchestrator Agent<br/>ImprovedOrchestrator]
        F --> G[Research Agent<br/>improved_research_agent.py]
        F --> H[Planner Agent<br/>improved_planner_agent.py]
        F --> I[Booker Agent<br/>improved_booker_agent.py]
    end
    
    subgraph ServiceLayer["Service Layer"]
        G --> J[RAG System<br/>vector_rag.py]
        G --> K[Google Places API<br/>External Service]
        G --> L[Weather API<br/>External Service]
        H --> M[LLM Service<br/>core/llm.py]
        I --> N[Amadeus API<br/>Flight Search]
        I --> O[Stripe API<br/>Payment Processing]
    end
    
    subgraph DataLayer["Data Layer"]
        D --> P[(PostgreSQL<br/>SQLModel ORM)]
        J --> Q[FAISS Vector DB<br/>RAG Embeddings]
        D --> R[(Redis<br/>Cache & Sessions)]
        P --> S[Alembic Migrations<br/>Schema Management]
    end
    
    subgraph ExternalLayer["External Services"]
        K & L & N & O --> T[Third-Party APIs<br/>HTTP/REST]
    end
    
    style ClientLayer fill:#007aff,stroke:#0051d5,color:#fff
    style APILayer fill:#10b981,stroke:#059669,color:#fff
    style AgentLayer fill:#f59e0b,stroke:#d97706,color:#fff
    style ServiceLayer fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style DataLayer fill:#ef4444,stroke:#dc2626,color:#fff
    style ExternalLayer fill:#06b6d4,stroke:#0891b2,color:#fff
```

## Detailed Component Architecture

```mermaid
flowchart LR
    subgraph Frontend["Frontend (React)"]
        A1[plan-trip.tsx] --> A2[TravelContext]
        A3[chat.tsx] --> A4[AuthContext]
        A5[items.tsx] --> A6[React Query]
        A2 & A4 & A6 --> A7[API Client<br/>sdk.gen.ts]
    end
    
    subgraph Backend["Backend (FastAPI)"]
        A7 --> B1[API Router<br/>main.py]
        B1 --> B2[ai_travel.py<br/>Trip Planning]
        B1 --> B3[conversations.py<br/>AI Chat]
        B1 --> B4[travel.py<br/>Trip Management]
        B1 --> B5[items.py<br/>Travel Notes]
        B1 --> B6[map_parser.py<br/>Map Processing]
    end
    
    subgraph Agents["AI Agents"]
        B2 --> C1[Orchestrator<br/>orchestrator.py]
        C1 --> C2[Research Agent<br/>improved_research_agent.py]
        C1 --> C3[Planner Agent<br/>improved_planner_agent.py]
        C1 --> C4[Booker Agent<br/>improved_booker_agent.py]
        C1 --> C5[Base Agent<br/>base_agent.py]
    end
    
    subgraph Services["Services"]
        C2 --> D1[Vector RAG<br/>vector_rag.py]
        C2 --> D2[External APIs<br/>Google Places]
        C3 --> D3[LLM<br/>core/llm.py]
        C4 --> D4[Amadeus<br/>Booking API]
        C4 --> D5[Stripe<br/>Payment API]
        D1 --> D6[FAISS<br/>Vector Store]
    end
    
    subgraph Database["Database Layer"]
        B2 & B3 & B4 & B5 --> E1[SQLModel<br/>ORM]
        E1 --> E2[(PostgreSQL<br/>Primary Database)]
        E1 --> E3[(Redis<br/>Cache & Sessions)]
        E2 --> E4[Alembic<br/>Migrations]
    end
    
    style Frontend fill:#007aff,stroke:#0051d5,color:#fff
    style Backend fill:#10b981,stroke:#059669,color:#fff
    style Agents fill:#f59e0b,stroke:#d97706,color:#fff
    style Services fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style Database fill:#ef4444,stroke:#dc2626,color:#fff
```

## Data Flow Architecture

```mermaid
flowchart TB
    Start([User Request]) --> Frontend[React Frontend]
    
    Frontend -->|HTTP POST| API[FastAPI Endpoint]
    API -->|Validate| Auth{JWT Valid?}
    
    Auth -->|No| Error[401 Unauthorized]
    Auth -->|Yes| Route[Route Handler]
    
    Route --> Agent{Agent Needed?}
    
    Agent -->|Yes| Orch[Orchestrator Agent]
    Agent -->|No| CRUD[CRUD Operations]
    
    Orch --> Research[Research Agent]
    Orch --> Planner[Planner Agent]
    Orch --> Booker[Booker Agent]
    
    Research --> RAG[RAG System]
    Research --> Places[Google Places]
    Research --> Weather[Weather API]
    
    Planner --> LLM[LLM Service<br/>OpenAI/Google AI]
    
    Booker --> Amadeus[Amadeus API]
    Booker --> Stripe[Stripe API]
    
    RAG --> Vector[FAISS Vector DB]
    LLM --> Cache{Redis Cache}
    
    Research & Planner & Booker --> Synthesize[Synthesize Response]
    Synthesize --> DB[(PostgreSQL)]
    DB --> Cache
    
    CRUD --> DB
    DB --> Response[Formatted Response]
    Cache --> Response
    Response --> Frontend
    Frontend --> User[Display to User]
    
    style Start fill:#007aff,stroke:#0051d5,color:#fff
    style Frontend fill:#007aff,stroke:#0051d5,color:#fff
    style API fill:#10b981,stroke:#059669,color:#fff
    style Orch fill:#f59e0b,stroke:#d97706,color:#fff
    style Research fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style Planner fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style Booker fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style DB fill:#ef4444,stroke:#dc2626,color:#fff
    style Cache fill:#ef4444,stroke:#dc2626,color:#fff
    style User fill:#007aff,stroke:#0051d5,color:#fff
```

## Technology Stack

### Frontend Layer
```
React 18.2+
├── TypeScript 5.0+
├── TanStack Router (File-based routing)
├── TanStack Query (Data fetching & caching)
├── Chakra UI (Component library)
├── Vite (Build tool)
└── React Hooks (State management)
```

### Backend Layer
```
FastAPI 0.109+
├── Python 3.11+
├── SQLModel (ORM)
├── Pydantic (Validation)
├── Alembic (Migrations)
├── Uvicorn (ASGI server)
└── Python-Jose (JWT)
```

### AI Agent System
```
Multi-Agent Architecture
├── Base Agent (Abstract base class)
├── Orchestrator Agent (Coordination)
├── Research Agent (Information gathering)
├── Planner Agent (Itinerary generation)
└── Booker Agent (Booking operations)
```

### Service Layer
```
Business Logic Services
├── Vector RAG Service (FAISS + Embeddings)
├── LLM Service (OpenAI/Google AI integration)
├── Redis Cache Service (Caching layer)
├── External API Clients (Google Places, Amadeus, Stripe)
└── Document Storage Service
```

### Data Layer
```
Storage & Caching
├── PostgreSQL (Primary database)
│   ├── SQLModel tables (Users, Trips, Items, Conversations)
│   └── Alembic migrations
├── Redis (Cache & Sessions)
│   ├── Session storage
│   ├── Query caching
│   └── Agent state
└── FAISS (Vector database for RAG)
    └── Semantic search
```

## Component Responsibilities

### Frontend Components

**Routes (`frontend/src/routes/`)**
- `_layout/index.tsx` - Dashboard with trip overview
- `_layout/plan-trip.tsx` - Trip planning interface
- `_layout/chat.tsx` - AI chat interface
- `_layout/items.tsx` - Travel Notes management
- `_layout/trips.tsx` - Trip list and details
- `_layout/settings.tsx` - User settings

**Components (`frontend/src/components/`)**
- `Common/` - Navbar, Sidebar, shared UI
- `Items/` - Travel Notes CRUD components
- `MapParserComponent.tsx` - Map visualization
- `PhotoGallery.tsx` - Photo display
- `ItineraryDisplay.tsx` - Itinerary rendering

**Contexts (`frontend/src/contexts/`)**
- `AuthContext.tsx` - Authentication state
- `TravelContext.tsx` - Travel data management
- `SidebarContext.tsx` - UI state

### Backend Components

**API Routes (`backend/app/api/routes/`)**
- `ai_travel.py` - AI-powered trip planning
- `travel.py` - Standard trip CRUD
- `conversations.py` - AI chat endpoints
- `items.py` - Travel Notes endpoints
- `map_parser.py` - Map parsing
- `photo_gallery.py` - Photo management

**Agents (`backend/app/agents/`)**
- `orchestrator.py` - Agent coordination
- `improved_research_agent.py` - Information research
- `improved_planner_agent.py` - Itinerary planning
- `improved_booker_agent.py` - Booking operations
- `base_agent.py` - Base agent class

**Services (`backend/app/services/`)**
- `vector_rag.py` - RAG implementation with FAISS
- `redis_cache.py` - Caching utilities
- `llm.py` - LLM service wrapper (in core/)
- External API clients

**Models (`backend/app/models.py`)**
- User, Trip, Itinerary, Booking
- Conversation, ConversationMessage
- Item (Travel Notes)
- SQLModel definitions

## Communication Patterns

### Synchronous Communication
- **Frontend ↔ Backend**: REST API (HTTPS)
- **Backend ↔ Database**: SQL queries via SQLModel
- **Agents ↔ Services**: Direct function calls
- **Services ↔ External APIs**: HTTP requests

### Asynchronous Communication
- **Real-time Updates**: Server-Sent Events (SSE)
- **Agent Events**: Redis pub/sub
- **Background Tasks**: Async/await in Python

### Caching Strategy
```
Request Flow with Caching:
1. Check Redis cache
2. If cache miss → Query database
3. Store result in Redis (TTL: 1 hour)
4. Return response
```

## Security Architecture

```
Security Layers:
├── JWT Authentication
│   ├── Token generation on login
│   ├── Token validation on requests
│   └── Token refresh mechanism
├── Password Hashing
│   └── bcrypt with salt
├── CORS Configuration
│   └── Whitelisted origins
└── Input Validation
    └── Pydantic models
```

## Deployment Architecture

```
Production Deployment:
├── Docker Compose
│   ├── Frontend (Nginx)
│   ├── Backend (FastAPI)
│   ├── PostgreSQL
│   └── Redis
├── Environment Configuration
│   ├── .env files
│   └── Secrets management
└── Reverse Proxy
    └── Nginx/Traefik
```

## Scalability Considerations

### Horizontal Scaling
- **Frontend**: Stateless, can scale horizontally
- **Backend**: Stateless API, load balancer ready
- **Database**: PostgreSQL with read replicas
- **Cache**: Redis cluster support

### Performance Optimization
- **Caching**: Redis for frequent queries
- **Database Indexing**: Optimized queries
- **Agent Parallelization**: Concurrent agent execution
- **CDN**: Static asset delivery

## Monitoring & Observability

```
Monitoring Stack:
├── Logging (Python logging)
├── Error Tracking (Exception handlers)
├── Health Checks (/api/v1/health)
└── Performance Metrics
    ├── Request/response times
    ├── Database query times
    └── Agent execution times
```
