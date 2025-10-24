import time
from datetime import datetime
from google.adk.agents import Agent
from app.core.config import settings
from .sessions import RedisSessionService, memory_manager
from google.adk.runners import Runner
from google.adk.models.lite_llm import LiteLlm
from google.genai import types
from .monitoring import track_agent_request, track_agent_error, track_agent_cost
from .evaluation import evaluate_agent_response, EvaluationType
from .event_emitter import emit_agent_event

# Import improved agents
try:
    from .improved_orchestrator import improved_orchestrator
    from .improved_research_agent import improved_research_agent
    from .improved_planner_agent import improved_planner_agent
    from .improved_booker_agent import improved_booker_agent
    print(f"✅ Improved orchestrator loaded: {improved_orchestrator is not None}")
except Exception as e:
    print(f"❌ Error loading improved orchestrator: {e}")
    improved_orchestrator = None
    improved_research_agent = None
    improved_planner_agent = None
    improved_booker_agent = None

# Import legacy agents for backward compatibility
from .research import research_agent as legacy_research_agent
from .planner import planner_agent as legacy_planner_agent
from .booker import booker_agent as legacy_booker_agent

# LiteLLM model (can keep, will not actually call external model in local test)
model = LiteLlm(settings.GEMINI_MODEL)
session_service = RedisSessionService()
# Create orchestrator with proper agent handling
if settings.ENVIRONMENT == "local":
    # For local development, use mock agents
    from .mock_agents import MockAgent
    orchestrator_agents = [
        MockAgent("research"),
        MockAgent("planner"), 
        MockAgent("booker")
    ]
    orchestrator = None  # No real orchestrator in local mode
    runner = None
else:
    # For production, use real agents
    orchestrator_agents = [research_agent, planner_agent, booker_agent]
    orchestrator = Agent(
        name="orchestrator",
        sub_agents=orchestrator_agents,
        description="Orchestrates travel planning: Research -> Plan -> Book.",
        instruction="""You are the orchestrator agent for Travya, an AI-powered travel companion.
        Your role is to coordinate between different specialized agents to provide comprehensive travel assistance.
        You can delegate tasks to research, planner, and booker agents based on user queries.
        Always provide helpful, accurate, and personalized travel recommendations.
        Use the memory manager to store and retrieve conversation context, user preferences, and trip information.
        Delegate tasks to sub-agents and synthesize JSON response."""
    )
    runner = Runner(agent=orchestrator, app_name="travya", session_service=session_service)


async def execute_query(user_id: str, session_id: str, query: dict, db=None) -> dict:
    """Execute multi-modal query and return synthesized response."""
    start_time = time.time()
    success = True
    
    try:
        # Store conversation memory
        memory_manager.store_conversation_memory(user_id, session_id, {
            "last_query": query,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Use improved orchestrator for better agent coordination
        if improved_orchestrator is not None:
            response = await improved_orchestrator.execute_quick_search(
                query=str(query),
                user_id=user_id,
                session_id=session_id
            )
        else:
            # Fallback to mock response if orchestrator is not available
            response = {
                "error": "Orchestrator not available",
                "message": "Agent system is not properly initialized",
                "query": str(query),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Update session memory with response
        session_service.update_session_memory(user_id, session_id, {
            "last_response": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Track successful request
        response_time = time.time() - start_time
        track_agent_request("orchestrator", response_time, success=True)
        
        # Track cost (mock cost for now)
        track_agent_cost("orchestrator", 0.01, "llm_call")
        
        # Evaluate response quality
        try:
            evaluation = await evaluate_agent_response(
                agent_name="orchestrator",
                query=str(query),
                response=str(response),
                evaluation_type=EvaluationType.LLM_AS_JUDGE
            )
            # Store evaluation in memory
            memory_manager.store_conversation_memory(user_id, session_id, {
                "evaluation": {
                    "score": evaluation.overall_score,
                    "feedback": evaluation.feedback,
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
        except Exception as eval_error:
            # Don't fail the main request if evaluation fails
            pass
        
        return response
        
    except Exception as e:
        success = False
        response_time = time.time() - start_time
        
        # Track failed request
        track_agent_request("orchestrator", response_time, success=False)
        track_agent_error("orchestrator", "execution_error", str(e))
        
        # Store error in memory
        memory_manager.store_conversation_memory(user_id, session_id, {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        raise e


async def plan_trip_with_agents(user_id: str, session_id: str, trip_request: dict, db=None) -> dict:
    """Enhanced trip planning using improved orchestrator with all agents."""
    start_time = time.time()
    
    try:
        # Store trip context in memory
        memory_manager.store_trip_context(user_id, session_id, {
            "trip_request": trip_request,
            "status": "planning",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Emit start event
        await emit_agent_event(session_id, {
            "agent_type": "orchestrator",
            "agent_name": "Travel Planning Orchestrator",
            "event_type": "start",
            "message": f"Starting trip planning for {trip_request.get('destination', 'unknown destination')}",
            "data": {"trip_request": trip_request}
        })
        
        # Use improved orchestrator for comprehensive trip planning
        if improved_orchestrator is not None:
            print(f"✅ Calling improved orchestrator with trip_request: {trip_request}")
            
            # Emit event for research phase
            await emit_agent_event(session_id, {
                "agent_type": "research",
                "agent_name": "Research Agent",
                "event_type": "start",
                "message": f"Researching destination: {trip_request.get('destination', 'unknown')}",
                "data": {}
            })
            
            response = await improved_orchestrator.execute_trip_planning_workflow(
                trip_request=trip_request,
                user_id=user_id,
                session_id=session_id
            )
            print(f"🔍 Orchestrator raw response: {response}")
            print(f"🔍 Response type: {type(response)}")
            print(f"🔍 Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
            
            # Emit completion events for each phase
            if response and isinstance(response, dict):
                detailed_results = response.get("detailed_results", {})
                
                # Research complete
                if "research" in detailed_results:
                    await emit_agent_event(session_id, {
                        "agent_type": "research",
                        "agent_name": "Research Agent",
                        "event_type": "complete",
                        "message": "Research completed - Found destination information and recommendations",
                        "confidence": detailed_results["research"].get("confidence", 0.5)
                    })
                
                # Planning complete
                if "planning" in detailed_results:
                    await emit_agent_event(session_id, {
                        "agent_type": "planner",
                        "agent_name": "Planning Agent",
                        "event_type": "complete",
                        "message": "Itinerary created with daily activities, meals, and transportation",
                        "confidence": detailed_results["planning"].get("confidence", 0.8)
                    })
                
                # Booking complete
                if "booking" in detailed_results:
                    await emit_agent_event(session_id, {
                        "agent_type": "booker",
                        "agent_name": "Booking Agent",
                        "event_type": "complete",
                        "message": "Booking options identified with pricing and availability",
                        "confidence": detailed_results["booking"].get("confidence", 0.9)
                    })
        else:
            print("❌ Improved orchestrator is None!")
            await emit_agent_event(session_id, {
                "agent_type": "orchestrator",
                "agent_name": "Travel Planning Orchestrator",
                "event_type": "error",
                "message": "Orchestrator not available",
                "data": {"error": "Agent system is not properly initialized"}
            })
            
            # Fallback to mock response if orchestrator is not available
            response = {
                "error": "Orchestrator not available",
                "message": "Agent system is not properly initialized",
                "trip_request": trip_request,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Add planning metadata
        if response and isinstance(response, dict):
            response["planning_metadata"] = {
                "user_id": user_id,
                "session_id": session_id,
                "processing_time": time.time() - start_time,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Emit final completion event
        await emit_agent_event(session_id, {
            "agent_type": "orchestrator",
            "agent_name": "Travel Planning Orchestrator",
            "event_type": "complete",
            "message": "Trip planning completed successfully!",
            "confidence": response.get("confidence_score", 0.7)
        })
        
        print(f"📦 Final response being returned: {response}")
        return response
        
    except Exception as e:
        # Track failed trip planning
        response_time = time.time() - start_time
        track_agent_request("trip_planner", response_time, success=False)
        track_agent_error("trip_planner", "trip_planning_error", str(e))
        
        # Store error in memory
        memory_manager.store_trip_context(user_id, session_id, {
            "trip_request": trip_request,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "status": "error",
            "message": f"Trip planning failed: {str(e)}",
            "error": str(e)
        }
