# AI Agents Module

## Overview

The AI Agents module implements a multi-agent system using Google's Agent Development Kit (ADK) to provide intelligent travel planning and assistance. The system consists of specialized agents that work together to deliver comprehensive travel solutions.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Orchestrator   │────│  Research Agent │────│  Planner Agent  │
│     Agent       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         └──────────────│  Booker Agent   │────│  Adapter Agent  │
                        │                 │    │                 │
                        └─────────────────┘    └─────────────────┘
```

## Agent Descriptions

### 1. Orchestrator Agent
**File**: `backend/app/agents/orchestrator.py`

The main coordinator that manages the workflow between all agents.

**Responsibilities**:
- Route user queries to appropriate agents
- Coordinate multi-agent workflows
- Synthesize responses from multiple agents
- Manage conversation memory and context

**Key Functions**:
- `execute_query()`: Process user queries and delegate to agents
- `plan_trip_with_agents()`: Coordinate complete trip planning workflow

### 2. Research Agent
**File**: `backend/app/agents/research.py`

Gathers destination information and user preferences using RAG and external APIs.

**Responsibilities**:
- Query knowledge base for destination information
- Search for attractions and points of interest
- Gather user preferences and requirements
- Provide contextual recommendations

**Key Functions**:
- `rag_query()`: Search knowledge base using vector similarity
- `places_api()`: Query Google Places API for attractions

### 3. Planner Agent
**File**: `backend/app/agents/planner.py`

Creates detailed itineraries and travel schedules.

**Responsibilities**:
- Generate structured travel itineraries
- Optimize schedules based on constraints
- Balance activities and rest time
- Consider user preferences and budget

**Key Functions**:
- `plan_trip()`: Generate JSON-structured itinerary
- Error handling for invalid responses

### 4. Booker Agent
**File**: `backend/app/agents/booker.py`

Handles flight, hotel, and activity bookings.

**Responsibilities**:
- Search for flights and hotels
- Process payments via Stripe
- Manage booking confirmations
- Handle booking modifications

**Key Functions**:
- `amadeus_flight_search()`: Search flights via Amadeus API
- `stripe_payment()`: Process payments securely

### 5. Adapter Agent
**File**: `backend/app/agents/adapter.py`

Provides real-time plan adaptation based on events and changes.

**Responsibilities**:
- Monitor for travel disruptions
- Adapt plans based on real-time events
- Handle flight delays and cancellations
- Suggest alternative arrangements

**Key Functions**:
- `callback()`: Handle Pub/Sub events
- `start_adapter()`: Initialize real-time monitoring

## Tools and Utilities

### External API Tools
**File**: `backend/app/agents/tools.py`

Provides integration with external services:

- **Google Maps API**: Places search and geocoding
- **Amadeus API**: Flight and hotel search
- **Stripe API**: Payment processing
- **Weather API**: Weather forecasts
- **RAG System**: Vector-based knowledge retrieval

### Session Management
**File**: `backend/app/agents/sessions.py`

Manages conversation memory and user context:

- **MemoryManager**: Stores conversation history and preferences
- **RedisSessionService**: Persistent session management
- **Context Storage**: Trip-specific context and state

## Configuration

### Environment Variables

```bash
# AI Model Configuration
GEMINI_MODEL=gemini-2.0-flash-001
ENVIRONMENT=local

# External API Keys
GOOGLE_MAPS_API_KEY=your_google_maps_key
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
STRIPE_SECRET_KEY=your_stripe_secret_key

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

### Agent Configuration
**File**: `backend/app/agents/config.py`

Centralized configuration for all agents with environment-specific settings.

## Usage Examples

### Basic Query Processing

```python
from app.agents.orchestrator import execute_query

# Process a user query
response = await execute_query(
    user_id="user123",
    session_id="session456",
    query={"text": "Plan a trip to Paris for 3 days"}
)
```

### Complete Trip Planning

```python
from app.agents.orchestrator import plan_trip_with_agents

# Plan a complete trip
trip_request = {
    "destination": "Tokyo",
    "start_date": "2024-08-15",
    "end_date": "2024-08-20",
    "budget": 3000,
    "travelers": 2,
    "trip_type": "leisure",
    "interests": ["culture", "food", "technology"]
}

response = await plan_trip_with_agents(
    user_id="user123",
    session_id="session456",
    trip_request=trip_request
)
```

### Memory Management

```python
from app.agents.sessions import memory_manager

# Store conversation memory
memory_manager.store_conversation_memory(
    user_id="user123",
    session_id="session456",
    memory={"preferences": ["museums", "restaurants"]}
)

# Retrieve user preferences
preferences = memory_manager.get_user_preferences("user123")
```

## Testing

### Running Agent Tests

```bash
# Run all agent tests
python -m pytest app/tests/agents/ -v

# Run specific agent tests
python -m pytest app/tests/agents/test_research.py -v
python -m pytest app/tests/agents/test_planner.py -v
python -m pytest app/tests/agents/test_booker.py -v
python -m pytest app/tests/agents/test_adapter.py -v
python -m pytest app/tests/agents/test_tools.py -v
```

### Test Coverage

The agent tests cover:
- Individual agent functionality
- Agent interactions and workflows
- Error handling and edge cases
- Memory management operations
- External API integrations (mocked)

## Development Guidelines

### Adding New Agents

1. Create agent file in `backend/app/agents/`
2. Define agent with proper name, description, and tools
3. Add to orchestrator's sub-agents list
4. Create comprehensive tests
5. Update documentation

### Adding New Tools

1. Define tool function in `backend/app/agents/tools.py`
2. Add proper error handling
3. Include mock implementation for testing
4. Update agent configurations
5. Add tests for the new tool

### Memory Management

- Use `MemoryManager` for persistent storage
- Store conversation context appropriately
- Implement proper TTL for different data types
- Handle Redis connection errors gracefully

## Troubleshooting

### Common Issues

1. **Agent Validation Errors**: Ensure agents are properly defined with required fields
2. **Memory Connection Issues**: Check Redis connection and configuration
3. **External API Failures**: Verify API keys and network connectivity
4. **Mock Agent Issues**: Ensure proper mock implementations for local testing

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check agent status:

```python
from app.agents.orchestrator import orchestrator
print(f"Orchestrator sub-agents: {len(orchestrator.sub_agents)}")
```

## Performance Considerations

- **Memory Usage**: Monitor Redis memory usage for conversation storage
- **API Rate Limits**: Implement proper rate limiting for external APIs
- **Agent Response Time**: Use async operations for better performance
- **Caching**: Cache frequently accessed data to reduce API calls

## Security

- **API Keys**: Store sensitive keys in environment variables
- **User Data**: Encrypt sensitive user information
- **Session Security**: Use secure session tokens
- **Input Validation**: Validate all user inputs before processing
