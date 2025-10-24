"""
Event emitter for agent activity streaming.
This module provides a way to emit events from agents to SSE streams.
"""
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Global dictionary to store agent event queues for each session
agent_event_queues: Dict[str, asyncio.Queue] = {}

async def emit_agent_event(session_id: str, event_data: dict):
    """
    Emit an event to the SSE stream for a session.
    
    Args:
        session_id: The session ID to emit the event to
        event_data: Dictionary containing event data with keys:
            - agent_type: Type of agent (research, planner, booker, orchestrator)
            - agent_name: Name of the agent
            - event_type: Type of event (start, thinking, tool_call, result, complete, error)
            - message: Human-readable message
            - data: Optional additional data
            - confidence: Optional confidence score (0-1)
    """
    if session_id in agent_event_queues:
        try:
            await agent_event_queues[session_id].put(event_data)
            logger.info(f"📤 Emitted {event_data.get('event_type')} event for {event_data.get('agent_type')} in session {session_id}")
        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
    else:
        # Queue doesn't exist yet, this is expected for early events
        logger.debug(f"No queue for session {session_id}, event not emitted: {event_data.get('event_type')}")

def register_session(session_id: str, queue: asyncio.Queue):
    """Register a new session with its event queue."""
    agent_event_queues[session_id] = queue
    logger.info(f"📝 Registered session {session_id} for event streaming")

def unregister_session(session_id: str):
    """Unregister a session and cleanup its event queue."""
    if session_id in agent_event_queues:
        del agent_event_queues[session_id]
        logger.info(f"🗑️ Unregistered session {session_id}")

