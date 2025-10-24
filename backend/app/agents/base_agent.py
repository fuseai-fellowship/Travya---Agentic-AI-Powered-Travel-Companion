"""
Base Agent Class for Travya AI System

This module provides a unified base class for all agents in the system,
ensuring consistent behavior, communication, and state management.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncio
import json
import uuid
from enum import Enum

class AgentState(Enum):
    """Agent execution states"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"

class AgentMessage:
    """Standard message format for agent communication"""
    
    def __init__(self, 
                 sender: str, 
                 recipient: str, 
                 message_type: str, 
                 content: Any, 
                 message_id: Optional[str] = None,
                 timestamp: Optional[datetime] = None):
        self.id = message_id or str(uuid.uuid4())
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.status = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        msg = cls(
            sender=data["sender"],
            recipient=data["recipient"],
            message_type=data["message_type"],
            content=data["content"],
            message_id=data["id"]
        )
        msg.timestamp = datetime.fromisoformat(data["timestamp"])
        msg.status = data["status"]
        return msg

class AgentResponse:
    """Standard response format for agent operations"""
    
    def __init__(self, 
                 success: bool, 
                 data: Any = None, 
                 error: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

class BaseAgent(ABC):
    """Base class for all agents in the Travya system"""
    
    def __init__(self, 
                 name: str, 
                 description: str,
                 capabilities: List[str],
                 dependencies: Optional[List[str]] = None):
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.dependencies = dependencies or []
        self.state = AgentState.IDLE
        self.message_queue: List[AgentMessage] = []
        self.response_history: List[AgentResponse] = []
        self.context: Dict[str, Any] = {}
        self.metrics = {
            "requests_processed": 0,
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "last_activity": None
        }
    
    @abstractmethod
    async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
        """Process a request and return a response"""
        pass
    
    @abstractmethod
    async def validate_request(self, request: Dict[str, Any]) -> bool:
        """Validate if this agent can handle the request"""
        pass
    
    async def send_message(self, recipient: str, message_type: str, content: Any) -> str:
        """Send a message to another agent"""
        message = AgentMessage(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            content=content
        )
        self.message_queue.append(message)
        return message.id
    
    async def receive_message(self) -> Optional[AgentMessage]:
        """Receive the next message from the queue"""
        if self.message_queue:
            return self.message_queue.pop(0)
        return None
    
    async def handle_message(self, message: AgentMessage) -> AgentResponse:
        """Handle an incoming message"""
        try:
            self.state = AgentState.PROCESSING
            start_time = datetime.utcnow()
            
            # Validate the request
            if not await self.validate_request(message.content):
                return AgentResponse(
                    success=False,
                    error=f"Agent {self.name} cannot handle this request type"
                )
            
            # Process the request
            response = await self.process_request(message.content)
            
            # Update metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_metrics(response.success, processing_time)
            
            self.state = AgentState.COMPLETED
            return response
            
        except Exception as e:
            self.state = AgentState.ERROR
            return AgentResponse(
                success=False,
                error=f"Error processing request: {str(e)}"
            )
    
    def _update_metrics(self, success: bool, processing_time: float):
        """Update agent metrics"""
        self.metrics["requests_processed"] += 1
        self.metrics["last_activity"] = datetime.utcnow().isoformat()
        
        # Update success rate
        total_requests = self.metrics["requests_processed"]
        current_success_rate = self.metrics["success_rate"]
        new_success_rate = ((current_success_rate * (total_requests - 1)) + (1 if success else 0)) / total_requests
        self.metrics["success_rate"] = new_success_rate
        
        # Update average response time
        current_avg_time = self.metrics["average_response_time"]
        new_avg_time = ((current_avg_time * (total_requests - 1)) + processing_time) / total_requests
        self.metrics["average_response_time"] = new_avg_time
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "capabilities": self.capabilities,
            "metrics": self.metrics,
            "context": self.context,
            "queue_size": len(self.message_queue)
        }
    
    def reset(self):
        """Reset agent to initial state"""
        self.state = AgentState.IDLE
        self.message_queue.clear()
        self.response_history.clear()
        self.context.clear()
        self.metrics = {
            "requests_processed": 0,
            "success_rate": 0.0,
            "average_response_time": 0.0,
            "last_activity": None
        }

class AgentRegistry:
    """Registry for managing all agents in the system"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_bus: List[AgentMessage] = []
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent in the system"""
        self.agents[agent.name] = agent
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name"""
        return self.agents.get(name)
    
    async def route_message(self, message: AgentMessage) -> bool:
        """Route a message to the appropriate agent"""
        agent = self.get_agent(message.recipient)
        if agent:
            response = await agent.handle_message(message)
            # Store response for tracking
            agent.response_history.append(response)
            return response.success
        return False
    
    async def broadcast_message(self, sender: str, message_type: str, content: Any) -> List[AgentResponse]:
        """Broadcast a message to all agents"""
        responses = []
        for agent_name in self.agents:
            if agent_name != sender:
                message = AgentMessage(sender, agent_name, message_type, content)
                response = await self.route_message(message)
                responses.append(response)
        return responses
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all agents in the system"""
        return {
            "total_agents": len(self.agents),
            "agents": {name: agent.get_status() for name, agent in self.agents.items()},
            "message_bus_size": len(self.message_bus)
        }

# Global agent registry
agent_registry = AgentRegistry()
