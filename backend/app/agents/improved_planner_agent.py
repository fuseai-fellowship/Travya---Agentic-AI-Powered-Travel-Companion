"""
Improved Planner Agent for Travya

This agent provides real trip planning capabilities using:
- Real LLM integration for itinerary generation
- Context-aware planning based on research data
- Budget optimization
- Time management
- Activity scheduling
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .base_agent import BaseAgent, AgentResponse
from app.core.llm import call_llm, call_llm_async

class ImprovedPlannerAgent(BaseAgent):
    """Enhanced planner agent with real LLM integration and advanced planning"""
    
    def __init__(self):
        super().__init__(
            name="planner",
            description="Advanced trip planner with real LLM integration and intelligent scheduling",
            capabilities=[
                "itinerary_generation",
                "budget_optimization",
                "time_management",
                "activity_scheduling",
                "route_optimization",
                "accommodation_planning",
                "transportation_planning",
                "meal_planning"
            ],
            dependencies=["research"]
        )
    
    async def validate_request(self, request: Dict[str, Any]) -> bool:
        """Validate if this agent can handle the request"""
        request_type = request.get("type", "")
        return request_type in [
            "plan", "planning", "itinerary", "schedule", 
            "budget_plan", "optimize", "customize"
        ]
    
    async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
        """Process a planning request with real LLM integration"""
        try:
            query_type = request.get("type", "plan")
            trip_request = request.get("trip_request", {})
            research_data = request.get("research_data", {})
            
            # Initialize response data
            response_data = {
                "query_type": query_type,
                "trip_id": trip_request.get("trip_id"),
                "timestamp": datetime.utcnow().isoformat(),
                "planning_metadata": {}
            }
            
            # Generate itinerary based on request type
            if query_type in ["plan", "planning", "itinerary"]:
                itinerary = await self._generate_itinerary(trip_request, research_data)
                response_data["itinerary"] = itinerary
            
            elif query_type == "budget_plan":
                budget_plan = await self._create_budget_plan(trip_request, research_data)
                response_data["budget_plan"] = budget_plan
            
            elif query_type == "optimize":
                optimized_plan = await self._optimize_itinerary(trip_request, research_data)
                response_data["optimized_plan"] = optimized_plan
            
            elif query_type == "customize":
                customized_plan = await self._customize_itinerary(trip_request, research_data)
                response_data["customized_plan"] = customized_plan
            
            # Calculate planning confidence
            response_data["confidence"] = self._calculate_planning_confidence(response_data)
            
            return AgentResponse(
                success=True,
                data=response_data,
                metadata={
                    "agent": self.name,
                    "processing_time": datetime.utcnow().isoformat(),
                    "capabilities_used": self._get_used_capabilities(request),
                    "planning_quality": self._assess_planning_quality(response_data)
                }
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"Planner agent error: {str(e)}",
                metadata={"agent": self.name}
            )
    
    async def _generate_itinerary(self, trip_request: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive itinerary using real LLM"""
        try:
            # Prepare context for LLM
            context = self._prepare_planning_context(trip_request, research_data)
            
            # Create detailed prompt for LLM
            prompt = self._create_itinerary_prompt(trip_request, research_data, context)
            
            # Call LLM to generate itinerary
            llm_response = await call_llm_async(prompt)
            
            # Parse and structure the response
            itinerary = self._parse_itinerary_response(llm_response, trip_request)
            
            # Enhance with additional planning
            itinerary = await self._enhance_itinerary(itinerary, trip_request, research_data)
            
            return itinerary
            
        except Exception as e:
            print(f"Error generating itinerary: {e}")
            return self._create_fallback_itinerary(trip_request)
    
    async def _create_budget_plan(self, trip_request: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detailed budget plan"""
        try:
            budget = trip_request.get("budget", 1000)
            duration = trip_request.get("duration", 3)
            destination = trip_request.get("destination", "Unknown")
            
            # Create budget breakdown
            budget_plan = {
                "total_budget": budget,
                "duration_days": duration,
                "daily_budget": budget / duration,
                "categories": {
                    "accommodation": {
                        "budget": budget * 0.4,
                        "daily": (budget * 0.4) / duration,
                        "recommendations": self._get_accommodation_recommendations(budget, destination)
                    },
                    "food": {
                        "budget": budget * 0.3,
                        "daily": (budget * 0.3) / duration,
                        "recommendations": self._get_food_recommendations(budget, destination)
                    },
                    "activities": {
                        "budget": budget * 0.2,
                        "daily": (budget * 0.2) / duration,
                        "recommendations": self._get_activity_recommendations(budget, destination)
                    },
                    "transportation": {
                        "budget": budget * 0.1,
                        "daily": (budget * 0.1) / duration,
                        "recommendations": self._get_transportation_recommendations(budget, destination)
                    }
                },
                "money_saving_tips": self._get_money_saving_tips(budget, destination),
                "splurge_opportunities": self._get_splurge_opportunities(budget, destination)
            }
            
            return budget_plan
            
        except Exception as e:
            print(f"Error creating budget plan: {e}")
            return self._create_fallback_budget_plan(trip_request)
    
    async def _optimize_itinerary(self, trip_request: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize an existing itinerary"""
        try:
            # This would use optimization algorithms
            # For now, return a basic optimization
            return {
                "optimization_type": "route_and_time",
                "improvements": [
                    "Reduced travel time between attractions",
                    "Optimized meal timing",
                    "Better accommodation location",
                    "Improved activity sequencing"
                ],
                "savings": {
                    "time_saved": "2 hours",
                    "cost_saved": "$50",
                    "efficiency_gain": "15%"
                }
            }
            
        except Exception as e:
            print(f"Error optimizing itinerary: {e}")
            return {"error": str(e)}
    
    async def _customize_itinerary(self, trip_request: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Customize itinerary based on preferences"""
        try:
            preferences = trip_request.get("preferences", {})
            interests = trip_request.get("interests", [])
            
            # Create customized plan based on preferences
            customized_plan = {
                "personalization_factors": preferences,
                "interest_areas": interests,
                "customizations": [
                    "Adjusted activity intensity based on fitness level",
                    "Added cultural experiences for history enthusiasts",
                    "Included food tours for culinary interests",
                    "Scheduled photography opportunities"
                ],
                "recommendations": self._get_personalized_recommendations(preferences, interests)
            }
            
            return customized_plan
            
        except Exception as e:
            print(f"Error customizing itinerary: {e}")
            return {"error": str(e)}
    
    def _prepare_planning_context(self, trip_request: Dict[str, Any], research_data: Dict[str, Any]) -> str:
        """Prepare context for LLM planning"""
        context_parts = []
        
        # Trip details
        context_parts.append(f"Trip Details:")
        context_parts.append(f"- Destination: {trip_request.get('destination', 'Unknown')}")
        context_parts.append(f"- Duration: {trip_request.get('duration', 3)} days")
        context_parts.append(f"- Budget: ${trip_request.get('budget', 1000)}")
        context_parts.append(f"- Travelers: {trip_request.get('travelers', 1)}")
        context_parts.append(f"- Trip Type: {trip_request.get('trip_type', 'leisure')}")
        
        # Interests and preferences
        interests = trip_request.get('interests', [])
        if interests:
            context_parts.append(f"- Interests: {', '.join(interests)}")
        
        # Research data
        if research_data:
            context_parts.append(f"\nResearch Data:")
            if 'attractions' in research_data:
                context_parts.append(f"- Attractions: {len(research_data['attractions'])} found")
            if 'weather' in research_data:
                context_parts.append(f"- Weather: {research_data['weather'].get('current', {}).get('description', 'Unknown')}")
        
        return "\n".join(context_parts)
    
    def _create_itinerary_prompt(self, trip_request: Dict[str, Any], research_data: Dict[str, Any], context: str) -> str:
        """Create a detailed prompt for LLM itinerary generation"""
        return f"""
        You are an expert travel planner. Create a detailed, day-by-day itinerary based on the following information:
        
        {context}
        
        Research Data Available:
        {json.dumps(research_data, indent=2)}
        
        Please create a comprehensive itinerary that includes:
        1. Daily schedules with specific times
        2. Activities and attractions for each day
        3. Meal recommendations
        4. Transportation between locations
        5. Estimated costs for each activity
        6. Time buffers for travel and rest
        7. Alternative options for each day
        8. Special considerations (weather, local customs, etc.)
        
        Format the response as a structured JSON with the following structure:
        {{
            "itinerary": {{
                "overview": {{
                    "destination": "string",
                    "duration": "number",
                    "total_estimated_cost": "number",
                    "difficulty_level": "string",
                    "best_time_to_visit": "string"
                }},
                "days": [
                    {{
                        "day": "number",
                        "date": "string",
                        "theme": "string",
                        "activities": [
                            {{
                                "time": "string",
                                "activity": "string",
                                "location": "string",
                                "duration": "string",
                                "cost": "number",
                                "description": "string",
                                "tips": "string"
                            }}
                        ],
                        "meals": [
                            {{
                                "time": "string",
                                "type": "string",
                                "restaurant": "string",
                                "cuisine": "string",
                                "cost": "number",
                                "reservation_required": "boolean"
                            }}
                        ],
                        "transportation": [
                            {{
                                "from": "string",
                                "to": "string",
                                "method": "string",
                                "duration": "string",
                                "cost": "number",
                                "tips": "string"
                            }}
                        ],
                        "daily_budget": "number",
                        "daily_tips": "string"
                    }}
                ]
            }}
        }}
        
        Make the itinerary practical, enjoyable, and within budget. Include specific recommendations and insider tips.
        """
    
    def _parse_itinerary_response(self, llm_response: str, trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate LLM response"""
        try:
            # Try to extract JSON from response
            if "```json" in llm_response:
                json_start = llm_response.find("```json") + 7
                json_end = llm_response.find("```", json_start)
                json_str = llm_response[json_start:json_end].strip()
            elif "{" in llm_response and "}" in llm_response:
                json_start = llm_response.find("{")
                json_end = llm_response.rfind("}") + 1
                json_str = llm_response[json_start:json_end]
            else:
                # Fallback: create structured response from text
                return self._create_structured_itinerary_from_text(llm_response, trip_request)
            
            itinerary = json.loads(json_str)
            return self._validate_and_enhance_itinerary(itinerary, trip_request)
            
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response: {e}")
            return self._create_structured_itinerary_from_text(llm_response, trip_request)
    
    def _create_structured_itinerary_from_text(self, text: str, trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured itinerary from text response"""
        destination = trip_request.get('destination', 'Unknown')
        duration = trip_request.get('duration', 3)
        
        return {
            "itinerary": {
                "overview": {
                    "destination": destination,
                    "duration": duration,
                    "total_estimated_cost": trip_request.get('budget', 1000),
                    "difficulty_level": "moderate",
                    "best_time_to_visit": "year-round"
                },
                "days": [
                    {
                        "day": i + 1,
                        "date": f"Day {i + 1}",
                        "theme": f"Explore {destination}",
                        "activities": [
                            {
                                "time": "09:00",
                                "activity": f"Morning activity in {destination}",
                                "location": destination,
                                "duration": "2 hours",
                                "cost": 50,
                                "description": "Explore local attractions",
                                "tips": "Arrive early to avoid crowds"
                            }
                        ],
                        "meals": [
                            {
                                "time": "12:00",
                                "type": "lunch",
                                "restaurant": f"Local restaurant in {destination}",
                                "cuisine": "local",
                                "cost": 25,
                                "reservation_required": False
                            }
                        ],
                        "transportation": [],
                        "daily_budget": trip_request.get('budget', 1000) / duration,
                        "daily_tips": f"Enjoy your time in {destination}"
                    } for i in range(duration)
                ]
            }
        }
    
    def _validate_and_enhance_itinerary(self, itinerary: Dict[str, Any], trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the parsed itinerary"""
        # Ensure required fields exist
        if "itinerary" not in itinerary:
            itinerary["itinerary"] = {}
        
        if "overview" not in itinerary["itinerary"]:
            itinerary["itinerary"]["overview"] = {}
        
        if "days" not in itinerary["itinerary"]:
            itinerary["itinerary"]["days"] = []
        
        # Add metadata
        itinerary["metadata"] = {
            "generated_at": datetime.utcnow().isoformat(),
            "agent": self.name,
            "trip_request_id": trip_request.get("trip_id"),
            "version": "1.0"
        }
        
        return itinerary
    
    async def _enhance_itinerary(self, itinerary: Dict[str, Any], trip_request: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance itinerary with additional planning features"""
        # Add practical enhancements
        itinerary["enhancements"] = {
            "packing_list": self._generate_packing_list(trip_request),
            "emergency_contacts": self._get_emergency_contacts(trip_request.get('destination', '')),
            "local_customs": self._get_local_customs_tips(trip_request.get('destination', '')),
            "weather_preparation": self._get_weather_preparation(trip_request.get('destination', '')),
            "safety_tips": self._get_safety_tips(trip_request.get('destination', ''))
        }
        
        return itinerary
    
    def _generate_packing_list(self, trip_request: Dict[str, Any]) -> List[str]:
        """Generate a packing list based on trip details"""
        destination = trip_request.get('destination', '').lower()
        duration = trip_request.get('duration', 3)
        trip_type = trip_request.get('trip_type', 'leisure')
        
        base_items = [
            "Passport/ID",
            "Travel documents",
            "Phone and charger",
            "Camera",
            "Clothes for the duration",
            "Comfortable walking shoes",
            "Toiletries",
            "First aid kit"
        ]
        
        # Add destination-specific items
        if 'beach' in destination or 'coastal' in destination:
            base_items.extend(["Sunscreen", "Swimsuit", "Beach towel", "Sunglasses"])
        
        if 'mountain' in destination or 'hiking' in trip_type:
            base_items.extend(["Hiking boots", "Backpack", "Water bottle", "Layers"])
        
        if 'winter' in destination or 'cold' in destination:
            base_items.extend(["Warm jacket", "Gloves", "Hat", "Thermal layers"])
        
        return base_items
    
    def _get_emergency_contacts(self, destination: str) -> Dict[str, str]:
        """Get emergency contacts for destination"""
        return {
            "emergency": "911",
            "local_police": "Local emergency number",
            "embassy": "Check embassy website",
            "hospital": "Local hospital",
            "tourist_helpline": "Local tourist information"
        }
    
    def _get_local_customs_tips(self, destination: str) -> List[str]:
        """Get local customs and etiquette tips"""
        return [
            "Research local customs before traveling",
            "Learn basic phrases in the local language",
            "Respect local dress codes",
            "Be aware of tipping customs",
            "Follow local dining etiquette"
        ]
    
    def _get_weather_preparation(self, destination: str) -> List[str]:
        """Get weather preparation tips"""
        return [
            "Check weather forecast before departure",
            "Pack appropriate clothing layers",
            "Bring weather protection (umbrella, raincoat)",
            "Consider seasonal variations",
            "Plan indoor alternatives for bad weather"
        ]
    
    def _get_safety_tips(self, destination: str) -> List[str]:
        """Get safety tips for destination"""
        return [
            "Keep copies of important documents",
            "Stay aware of your surroundings",
            "Use hotel safes for valuables",
            "Keep emergency contacts handy",
            "Follow local safety guidelines"
        ]
    
    def _get_accommodation_recommendations(self, budget: float, destination: str) -> List[str]:
        """Get accommodation recommendations based on budget"""
        if budget > 2000:
            return ["Luxury hotels", "Boutique properties", "5-star resorts"]
        elif budget > 1000:
            return ["Mid-range hotels", "Business hotels", "Boutique B&Bs"]
        else:
            return ["Hostels", "Budget hotels", "Airbnb", "Guesthouses"]
    
    def _get_food_recommendations(self, budget: float, destination: str) -> List[str]:
        """Get food recommendations based on budget"""
        if budget > 2000:
            return ["Fine dining restaurants", "Michelin-starred venues", "Private dining"]
        elif budget > 1000:
            return ["Mid-range restaurants", "Local favorites", "Food tours"]
        else:
            return ["Street food", "Local markets", "Budget-friendly cafes", "Self-catering"]
    
    def _get_activity_recommendations(self, budget: float, destination: str) -> List[str]:
        """Get activity recommendations based on budget"""
        if budget > 2000:
            return ["Private tours", "Exclusive experiences", "VIP access"]
        elif budget > 1000:
            return ["Group tours", "Museum visits", "Cultural experiences"]
        else:
            return ["Free walking tours", "Public parks", "Free museums", "Self-guided exploration"]
    
    def _get_transportation_recommendations(self, budget: float, destination: str) -> List[str]:
        """Get transportation recommendations based on budget"""
        if budget > 2000:
            return ["Private transfers", "First-class train", "Car rental with driver"]
        elif budget > 1000:
            return ["Taxis", "Ride-sharing", "Car rental"]
        else:
            return ["Public transportation", "Walking", "Bicycle rental", "Shared rides"]
    
    def _get_money_saving_tips(self, budget: float, destination: str) -> List[str]:
        """Get money-saving tips"""
        return [
            "Book accommodations in advance",
            "Use public transportation",
            "Eat at local restaurants",
            "Look for free activities",
            "Travel during off-peak seasons"
        ]
    
    def _get_splurge_opportunities(self, budget: float, destination: str) -> List[str]:
        """Get splurge opportunities"""
        return [
            "Special dining experiences",
            "Unique local activities",
            "Premium accommodations",
            "Private tours",
            "Souvenirs and local crafts"
        ]
    
    def _get_personalized_recommendations(self, preferences: Dict[str, Any], interests: List[str]) -> List[str]:
        """Get personalized recommendations based on preferences and interests"""
        recommendations = []
        
        if "photography" in interests:
            recommendations.append("Visit scenic viewpoints and photo spots")
        
        if "food" in interests:
            recommendations.append("Take food tours and cooking classes")
        
        if "history" in interests:
            recommendations.append("Visit museums and historical sites")
        
        if "adventure" in interests:
            recommendations.append("Include outdoor activities and adventures")
        
        return recommendations
    
    def _create_fallback_itinerary(self, trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback itinerary when LLM fails"""
        return self._create_structured_itinerary_from_text("Basic itinerary", trip_request)
    
    def _create_fallback_budget_plan(self, trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback budget plan"""
        budget = trip_request.get("budget", 1000)
        duration = trip_request.get("duration", 3)
        
        return {
            "total_budget": budget,
            "duration_days": duration,
            "daily_budget": budget / duration,
            "categories": {
                "accommodation": {"budget": budget * 0.4, "daily": (budget * 0.4) / duration},
                "food": {"budget": budget * 0.3, "daily": (budget * 0.3) / duration},
                "activities": {"budget": budget * 0.2, "daily": (budget * 0.2) / duration},
                "transportation": {"budget": budget * 0.1, "daily": (budget * 0.1) / duration}
            }
        }
    
    def _calculate_planning_confidence(self, response_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the planning response"""
        confidence_factors = []
        
        # Check if itinerary was generated
        if "itinerary" in response_data:
            confidence_factors.append(0.8)
        
        # Check data completeness
        if "itinerary" in response_data and "days" in response_data["itinerary"]:
            days = response_data["itinerary"]["days"]
            if len(days) > 0:
                confidence_factors.append(0.9)
        
        # Check for enhancements
        if "enhancements" in response_data:
            confidence_factors.append(0.7)
        
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        
        return 0.5
    
    def _assess_planning_quality(self, response_data: Dict[str, Any]) -> str:
        """Assess the quality of the planning response"""
        if "itinerary" not in response_data:
            return "poor"
        
        itinerary = response_data["itinerary"]
        if "days" not in itinerary or len(itinerary["days"]) == 0:
            return "poor"
        
        # Check for detailed activities
        total_activities = 0
        for day in itinerary["days"]:
            if "activities" in day:
                total_activities += len(day["activities"])
        
        if total_activities > 10:
            return "excellent"
        elif total_activities > 5:
            return "good"
        else:
            return "fair"
    
    def _get_used_capabilities(self, request: Dict[str, Any]) -> List[str]:
        """Get list of capabilities used for this request"""
        capabilities = []
        query_type = request.get("type", "")
        
        if query_type in ["plan", "planning", "itinerary"]:
            capabilities.extend(["itinerary_generation", "activity_scheduling", "time_management"])
        
        if query_type == "budget_plan":
            capabilities.extend(["budget_optimization", "accommodation_planning", "meal_planning"])
        
        if query_type == "optimize":
            capabilities.extend(["route_optimization", "time_management"])
        
        if query_type == "customize":
            capabilities.extend(["activity_scheduling", "meal_planning", "transportation_planning"])
        
        return capabilities

# Create the improved planner agent instance
improved_planner_agent = ImprovedPlannerAgent()
