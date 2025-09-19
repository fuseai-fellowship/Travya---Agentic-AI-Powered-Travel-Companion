# System Design

## Architecture Flowchart

```mermaid
flowchart TD
    subgraph ClientLayer
        A[React Frontend: Multi-Modal Input Chat/Dashboard] -- HTTPS/WebSockets --> B[API Gateway: Load Balancer + Auth]
    end
    subgraph MicroservicesLayer
        B --> C[Auth Service: JWT/OAuth]
        B --> D[Profile Service: CRUD + Embeddings]
        B --> E[Booking Service: Amadeus/Stripe Sagas]
        B --> F[Core API Service: ADK Proxy]
    end
    subgraph AIAgentLayer
        F -- gRPC/Pub/Sub --> G[ADK Orchestrator Agent: Delegate/Synthesize]
        G -- A2A/MCP --> H[Research Agent: RAG + Places API]
        G -- A2A/MCP --> I[Planner Agent: Gemini Reasoning]
        G -- A2A/MCP --> J[Booker Agent: Action Tools]
        G -- Pub/Sub Triggers --> K[Adapter Agent: Real-Time Adaptation]
    end
    subgraph DataLayer
        D & E -- Queries --> L[AlloyDB PostgreSQL: Users/Trips/Bookings]
        H -- Embed Queries --> M[Vertex AI Vector Search: RAG Index]
        C & F -- Sessions --> N[Redis Cache: TTL/LRU]
        All -- Logs --> O[BigQuery Analytics]
    end
    subgraph External
        H & J -- API Calls --> P[Google Maps/Amadeus/Weather/Stripe]
        A -- Push --> Q[FCM Notifications]
    end
    subgraph OpsLayer
        All -- Traces/Logs --> R[Cloud Monitoring: SLOs/Alerts]
        All -- CI/CD --> S[Cloud Build: Deploy to Cloud Run/GKE]
    end
    style ClientLayer fill:#f9f,stroke:#333
    style MicroservicesLayer fill:#ddf,stroke:#333
    style AIAgentLayer fill:#fdf,stroke:#333
    style DataLayer fill:#dff,stroke:#333
    style External fill:#ffd,stroke:#333
    style OpsLayer fill:#dfd,stroke:#333
