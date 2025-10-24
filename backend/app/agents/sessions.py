# Session management with Redis and Memory

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from google.adk.sessions import InMemorySessionService
from redis import Redis
from app.core.config import settings

redis = Redis.from_url(settings.REDIS_URL)

class MemoryManager:
    """Manages conversation memory and context for AI agents."""
    
    def __init__(self):
        self.redis = redis
    
    def store_conversation_memory(self, user_id: str, session_id: str, memory: Dict[str, Any]):
        """Store conversation memory in Redis."""
        key = f"memory:{user_id}:{session_id}"
        self.redis.setex(key, 86400, json.dumps(memory))  # 24-hour TTL
    
    def get_conversation_memory(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conversation memory from Redis."""
        key = f"memory:{user_id}:{session_id}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    def store_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Store user travel preferences."""
        key = f"preferences:{user_id}"
        self.redis.setex(key, 2592000, json.dumps(preferences))  # 30-day TTL
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user travel preferences."""
        key = f"preferences:{user_id}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    def store_trip_context(self, user_id: str, trip_id: str, context: Dict[str, Any]):
        """Store trip-specific context."""
        key = f"trip_context:{user_id}:{trip_id}"
        self.redis.setex(key, 604800, json.dumps(context))  # 7-day TTL
    
    def get_trip_context(self, user_id: str, trip_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve trip-specific context."""
        key = f"trip_context:{user_id}:{trip_id}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None

class RedisSessionService(InMemorySessionService):
    """Enhanced session service with Redis persistence and memory management."""
    
    def __init__(self):
        super().__init__()
        self.redis = redis
        self.memory_manager = MemoryManager()
    
    def create_session(self, app_name: str, user_id: str, session_id: str):
        """Create a new session with Redis persistence."""
        super().create_session(app_name, user_id, session_id)
        
        # Store session metadata
        session_data = {
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id
        }
        
        self.redis.setex(
            f"session:{app_name}:{user_id}:{session_id}", 
            3600,  # 1-hour TTL
            json.dumps(session_data)
        )
        
        # Initialize memory for this session
        self.memory_manager.store_conversation_memory(user_id, session_id, {
            "conversation_history": [],
            "user_intent": None,
            "current_context": {},
            "suggestions_given": []
        })

    def get_session(self, app_name: str, user_id: str, session_id: str):
        """Get session with Redis persistence."""
        session_key = f"session:{app_name}:{user_id}:{session_id}"
        if self.redis.get(session_key):
            # Update last activity
            session_data = json.loads(self.redis.get(session_key))
            session_data["last_activity"] = datetime.utcnow().isoformat()
            self.redis.setex(session_key, 3600, json.dumps(session_data))
            
            return super().get_session(app_name, user_id, session_id)
        return None
    
    def update_session_memory(self, user_id: str, session_id: str, memory_update: Dict[str, Any]):
        """Update session memory with new information."""
        current_memory = self.memory_manager.get_conversation_memory(user_id, session_id) or {}
        current_memory.update(memory_update)
        self.memory_manager.store_conversation_memory(user_id, session_id, current_memory)
    
    def get_session_memory(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current session memory."""
        return self.memory_manager.get_conversation_memory(user_id, session_id)
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (called periodically)."""
        # Redis TTL handles this automatically, but we can add custom cleanup logic here
        pass

# Global instances
memory_manager = MemoryManager()
session_service = RedisSessionService()
