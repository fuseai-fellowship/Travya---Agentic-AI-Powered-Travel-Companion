## Sequence Diagram: Multi-Modal Query Flow

```mermaid
sequenceDiagram
    participant User as User (React Frontend)
    participant Gateway as API Gateway
    participant CoreAPI as Core API Service
    participant Orchestrator as ADK Orchestrator
    participant Research as Research Agent
    participant Planner as Planner Agent
    participant Booker as Booker Agent
    participant Adapter as Adapter Agent
    participant DB as Data Layer (AlloyDB/Vector/Redis)
    participant External as External APIs
    participant Monitoring as Ops (Monitoring/Logging)

    User->>Gateway: Multi-Modal Query (Text/Image/Voice)
    Gateway->>CoreAPI: Auth & Route (/v1/agent/query)
    CoreAPI->>Orchestrator: Invoke (gRPC with Context)
    Orchestrator->>Research: A2A Delegate (RAG Fetch)
    Research->>DB: Query Embeddings (Vector Search)
    Research->>External: Tool Call (Places/Amadeus)
    Research-->>Orchestrator: Data Response
    Orchestrator->>Planner: A2A Delegate (Reasoning)
    Planner->>Orchestrator: Structured Itinerary
    alt If Booking Needed
        Orchestrator->>Booker: A2A Delegate (Actions)
        Booker->>External: Book/Confirm (e.g., Stripe)
        Booker-->>Orchestrator: Booking ID
    end
    Orchestrator-->>CoreAPI: Synthesized JSON
    CoreAPI-->>Gateway: Response
    Gateway-->>User: Render Itinerary + Images
    Note over User,Monitoring: Parallel Logging/Traces for SLOs

    loop Real-Time Adaptation
        External->>Pub/Sub: Event (e.g., Delay Webhook)
        Pub/Sub->>Adapter: Trigger
        Adapter->>Orchestrator: Re-Delegate (Re-Plan)
        Orchestrator->>User: Notify (WebSocket/FCM)
    end
    Monitoring->>All: Monitor SLOs/Alerts
