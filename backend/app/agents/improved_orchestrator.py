"""
Improved Orchestrator for Travya Agent System

This orchestrator provides advanced coordination between agents using:
- Real agent communication and message passing
- Intelligent task delegation and routing
- Context-aware decision making
- Advanced workflow management
- Performance monitoring and optimization
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from .base_agent import BaseAgent, AgentResponse, AgentMessage, AgentRegistry, agent_registry
from .improved_research_agent import improved_research_agent
from .improved_planner_agent import improved_planner_agent
from .improved_booker_agent import improved_booker_agent
from app.core.config import settings

class ImprovedOrchestrator(BaseAgent):
    """Enhanced orchestrator with advanced agent coordination"""
    
    def __init__(self):
        super().__init__(
            name="orchestrator",
            description="Advanced orchestrator for coordinating travel planning agents",
            capabilities=[
                "agent_coordination",
                "workflow_management",
                "task_delegation",
                "context_management",
                "decision_making",
                "performance_optimization",
                "error_recovery",
                "response_synthesis"
            ],
            dependencies=["research", "planner", "booker"]
        )
        
        # Register agents
        self._register_agents()
        
        # Workflow definitions
        self.workflows = {
            "trip_planning": ["research", "planner", "booker"],
            "quick_search": ["research"],
            "itinerary_creation": ["research", "planner"],
            "booking_only": ["booker"],
            "research_only": ["research"]
        }
    
    def _register_agents(self):
        """Register all agents with the orchestrator"""
        agent_registry.register_agent(improved_research_agent)
        agent_registry.register_agent(improved_planner_agent)
        agent_registry.register_agent(improved_booker_agent)
        agent_registry.register_agent(self)
    
    async def validate_request(self, request: Dict[str, Any]) -> bool:
        """Validate if this agent can handle the request"""
        request_type = request.get("type", "")
        return request_type in [
            "trip_planning", "quick_search", "itinerary_creation", 
            "booking_only", "research_only", "orchestrate", "coordinate"
        ]
    
    async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
        """Process a request by orchestrating multiple agents"""
        try:
            request_type = request.get("type", "trip_planning")
            user_query = request.get("query", "")
            context = request.get("context", {})
            
            # Determine workflow
            workflow = self._determine_workflow(request_type, request)
            
            # Execute workflow
            workflow_result = await self._execute_workflow(workflow, request, context)
            
            # Synthesize final response
            final_response = await self._synthesize_response(workflow_result, request)
            
            return AgentResponse(
                success=True,
                data=final_response,
                metadata={
                    "agent": self.name,
                    "workflow_used": workflow,
                    "agents_involved": list(workflow_result.keys()),
                    "processing_time": datetime.utcnow().isoformat(),
                    "orchestration_quality": self._assess_orchestration_quality(workflow_result)
                }
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"Orchestrator error: {str(e)}",
                metadata={"agent": self.name}
            )
    
    def _determine_workflow(self, request_type: str, request: Dict[str, Any]) -> List[str]:
        """Determine the appropriate workflow for the request"""
        if request_type in self.workflows:
            return self.workflows[request_type]
        
        # Dynamic workflow determination based on request content
        query = request.get("query", "").lower()
        
        if any(word in query for word in ["book", "flight", "hotel", "payment"]):
            return ["research", "booker"]
        elif any(word in query for word in ["plan", "itinerary", "schedule"]):
            return ["research", "planner"]
        elif any(word in query for word in ["search", "find", "discover"]):
            return ["research"]
        else:
            return ["research", "planner", "booker"]  # Default full workflow
    
    async def _execute_workflow(self, workflow: List[str], request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow by coordinating multiple agents"""
        workflow_result = {}
        current_context = context.copy()
        
        for agent_name in workflow:
            try:
                # Prepare request for this agent
                agent_request = self._prepare_agent_request(agent_name, request, current_context)
                
                # Get agent and execute request
                agent = agent_registry.get_agent(agent_name)
                if agent:
                    # Send message to agent
                    message = AgentMessage(
                        sender=self.name,
                        recipient=agent_name,
                        message_type="process_request",
                        content=agent_request
                    )
                    
                    # Handle the message
                    response = await agent.handle_message(message)
                    
                    if response.success:
                        workflow_result[agent_name] = response.data
                        # Update context with agent's response
                        current_context = self._update_context(current_context, agent_name, response.data)
                    else:
                        workflow_result[agent_name] = {"error": response.error}
                
                # Add delay between agents for realistic processing
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Error executing workflow step {agent_name}: {e}")
                workflow_result[agent_name] = {"error": str(e)}
        
        return workflow_result
    
    def _prepare_agent_request(self, agent_name: str, original_request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a request for a specific agent"""
        base_request = original_request.copy()
        
        # Add context from previous agents
        if context:
            base_request["context"] = context
        
        # Customize request based on agent
        if agent_name == "research":
            base_request["type"] = "research"
            base_request["query"] = original_request.get("query", "")
        
        elif agent_name == "planner":
            base_request["type"] = "plan"
            base_request["trip_request"] = original_request.get("trip_request", {})
            if "research" in context:
                base_request["research_data"] = context["research"]
        
        elif agent_name == "booker":
            base_request["type"] = "book"
            base_request["booking_request"] = original_request.get("booking_request", {})
            if "planner" in context:
                base_request["itinerary"] = context["planner"]
        
        return base_request
    
    def _update_context(self, current_context: Dict[str, Any], agent_name: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update context with agent's response data"""
        updated_context = current_context.copy()
        updated_context[agent_name] = agent_data
        return updated_context
    
    async def _synthesize_response(self, workflow_result: Dict[str, Any], original_request: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize a final response from workflow results"""
        try:
            # Extract key information from each agent's response
            research_data = workflow_result.get("research", {})
            planner_data = workflow_result.get("planner", {})
            booker_data = workflow_result.get("booker", {})
            
            # Create comprehensive response
            synthesized_response = {
                "orchestration_id": f"orch_{int(datetime.utcnow().timestamp())}",
                "timestamp": datetime.utcnow().isoformat(),
                "workflow_status": "completed",
                "summary": self._create_summary(research_data, planner_data, booker_data),
                "detailed_results": {
                    "research": research_data,
                    "planning": planner_data,
                    "booking": booker_data
                },
                "recommendations": self._generate_recommendations(research_data, planner_data, booker_data),
                "next_steps": self._suggest_next_steps(workflow_result),
                "confidence_score": self._calculate_overall_confidence(workflow_result)
            }
            
            return synthesized_response
            
        except Exception as e:
            print(f"Error synthesizing response: {e}")
            return {
                "error": f"Response synthesis failed: {str(e)}",
                "workflow_result": workflow_result
            }
    
    def _create_summary(self, research_data: Dict[str, Any], planner_data: Dict[str, Any], booker_data: Dict[str, Any]) -> str:
        """Create a summary of the orchestration results"""
        summary_parts = []
        
        if research_data and not research_data.get("error"):
            summary_parts.append("Research completed successfully with destination insights and recommendations.")
        
        if planner_data and not planner_data.get("error"):
            summary_parts.append("Trip planning completed with detailed itinerary and budget breakdown.")
        
        if booker_data and not booker_data.get("error"):
            summary_parts.append("Booking options identified with pricing and availability information.")
        
        if not summary_parts:
            return "Orchestration completed with limited results. Some agents encountered errors."
        
        return " ".join(summary_parts)
    
    def _generate_recommendations(self, research_data: Dict[str, Any], planner_data: Dict[str, Any], booker_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on all agent responses"""
        recommendations = []
        
        # Research-based recommendations
        if research_data and not research_data.get("error"):
            if "attractions" in research_data:
                recommendations.append("Consider visiting the top-rated attractions identified in your research.")
            
            if "weather" in research_data:
                weather = research_data["weather"]
                if weather.get("current", {}).get("description"):
                    recommendations.append(f"Current weather: {weather['current']['description']}. Plan accordingly.")
        
        # Planning-based recommendations
        if planner_data and not planner_data.get("error"):
            if "itinerary" in planner_data:
                itinerary = planner_data["itinerary"]
                if "overview" in itinerary:
                    overview = itinerary["overview"]
                    if overview.get("difficulty_level"):
                        recommendations.append(f"Trip difficulty: {overview['difficulty_level']}. Ensure you're prepared.")
        
        # Booking-based recommendations
        if booker_data and not booker_data.get("error"):
            if "flight_booking" in booker_data:
                flight = booker_data["flight_booking"]
                if flight.get("booking_status") == "confirmed":
                    recommendations.append("Flight booking confirmed. Check your email for confirmation details.")
            
            if "hotel_booking" in booker_data:
                hotel = booker_data["hotel_booking"]
                if hotel.get("booking_status") == "confirmed":
                    recommendations.append("Hotel booking confirmed. Note the check-in and check-out times.")
        
        return recommendations
    
    def _suggest_next_steps(self, workflow_result: Dict[str, Any]) -> List[str]:
        """Suggest next steps based on workflow results"""
        next_steps = []
        
        # Check for errors and suggest recovery
        error_agents = [agent for agent, data in workflow_result.items() if data.get("error")]
        if error_agents:
            next_steps.append(f"Some agents encountered errors: {', '.join(error_agents)}. Consider retrying or using alternative approaches.")
        
        # Suggest based on successful agents
        if "research" in workflow_result and not workflow_result["research"].get("error"):
            next_steps.append("Research phase completed. You can now proceed with detailed planning.")
        
        if "planner" in workflow_result and not workflow_result["planner"].get("error"):
            next_steps.append("Itinerary created. Review the plan and make any necessary adjustments.")
        
        if "booker" in workflow_result and not workflow_result["booker"].get("error"):
            next_steps.append("Booking options available. Review prices and availability before confirming.")
        
        # General next steps
        next_steps.extend([
            "Review all recommendations and make informed decisions",
            "Check travel requirements and documentation",
            "Consider travel insurance for your trip",
            "Set up notifications for any booking confirmations"
        ])
        
        return next_steps
    
    def _calculate_overall_confidence(self, workflow_result: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the orchestration"""
        confidence_scores = []
        
        for agent_name, data in workflow_result.items():
            if not data.get("error"):
                # Extract confidence from agent data
                confidence = data.get("confidence", 0.5)
                confidence_scores.append(confidence)
        
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        
        return 0.3  # Low confidence if all agents failed
    
    def _assess_orchestration_quality(self, workflow_result: Dict[str, Any]) -> str:
        """Assess the quality of the orchestration"""
        successful_agents = sum(1 for data in workflow_result.values() if not data.get("error"))
        total_agents = len(workflow_result)
        
        success_rate = successful_agents / total_agents if total_agents > 0 else 0
        
        if success_rate >= 0.9:
            return "excellent"
        elif success_rate >= 0.7:
            return "good"
        elif success_rate >= 0.5:
            return "fair"
        else:
            return "poor"
    
    async def execute_trip_planning_workflow(self, trip_request: Dict[str, Any], user_id: str, session_id: str) -> Dict[str, Any]:
        """Execute a complete trip planning workflow"""
        try:
            # Prepare orchestration request
            orchestration_request = {
                "type": "trip_planning",
                "query": f"Plan a trip to {trip_request.get('destination', 'unknown destination')}",
                "trip_request": trip_request,
                "context": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Process the request
            response = await self.process_request(orchestration_request)
            
            if response.success:
                return response.data
            else:
                return {
                    "error": response.error,
                    "orchestration_id": f"error_{int(datetime.utcnow().timestamp())}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            return {
                "error": f"Trip planning workflow failed: {str(e)}",
                "orchestration_id": f"error_{int(datetime.utcnow().timestamp())}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def execute_quick_search(self, query: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Execute a quick search workflow"""
        try:
            search_request = {
                "type": "quick_search",
                "query": query,
                "context": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            response = await self.process_request(search_request)
            
            if response.success:
                return response.data
            else:
                return {
                    "error": response.error,
                    "search_id": f"error_{int(datetime.utcnow().timestamp())}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            return {
                "error": f"Quick search failed: {str(e)}",
                "search_id": f"error_{int(datetime.utcnow().timestamp())}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "orchestrator": self.get_status(),
            "registered_agents": agent_registry.get_system_status(),
            "workflows_available": list(self.workflows.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }

# Create the improved orchestrator instance
improved_orchestrator = ImprovedOrchestrator()
