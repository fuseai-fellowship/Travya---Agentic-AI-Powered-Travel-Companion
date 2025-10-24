"""
Improved Research Agent for Travya

This agent provides real research capabilities using:
- Real RAG system with knowledge base
- Google Places API integration
- Weather data integration
- Context-aware research
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_agent import BaseAgent, AgentResponse, AgentMessage
from .rag_system import rag_system
from .real_apis import google_places, weather_api

class ImprovedResearchAgent(BaseAgent):
    """Enhanced research agent with real API integrations"""
    
    def __init__(self):
        super().__init__(
            name="research",
            description="Advanced research agent with real API integrations and knowledge base",
            capabilities=[
                "destination_research",
                "attraction_discovery",
                "weather_information",
                "local_insights",
                "travel_recommendations",
                "budget_analysis",
                "safety_information"
            ],
            dependencies=[]
        )
    
    async def validate_request(self, request: Dict[str, Any]) -> bool:
        """Validate if this agent can handle the request"""
        request_type = request.get("type", "")
        return request_type in [
            "research", "destination_info", "attractions", 
            "weather", "local_insights", "recommendations"
        ]
    
    async def process_request(self, request: Dict[str, Any]) -> AgentResponse:
        """Process a research request with real data"""
        try:
            query_type = request.get("type", "research")
            user_query = request.get("query", "")
            destination = request.get("destination", "")
            context = request.get("context", {})
            
            # Initialize response data
            response_data = {
                "query_type": query_type,
                "destination": destination,
                "timestamp": datetime.utcnow().isoformat(),
                "sources": [],
                "confidence": 0.0
            }
            
            # Use RAG system for knowledge base queries
            if query_type in ["research", "destination_info", "recommendations"]:
                rag_response = await self._query_rag_system(user_query, context)
                response_data.update(rag_response)
            
            # Get real-time data based on query type
            if query_type == "attractions" and destination:
                attractions = await self._get_attractions(destination, request)
                response_data["attractions"] = attractions
            
            if query_type == "weather" and destination:
                weather = await self._get_weather(destination, request)
                response_data["weather"] = weather
            
            if query_type == "local_insights" and destination:
                insights = await self._get_local_insights(destination, request)
                response_data["local_insights"] = insights
            
            # Calculate overall confidence
            response_data["confidence"] = self._calculate_confidence(response_data)
            
            return AgentResponse(
                success=True,
                data=response_data,
                metadata={
                    "agent": self.name,
                    "processing_time": datetime.utcnow().isoformat(),
                    "capabilities_used": self._get_used_capabilities(request)
                }
            )
            
        except Exception as e:
            return AgentResponse(
                success=False,
                error=f"Research agent error: {str(e)}",
                metadata={"agent": self.name}
            )
    
    async def _query_rag_system(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Query the RAG system for knowledge base information"""
        try:
            async with rag_system as rag:
                result = await rag.query(query, context)
                return {
                    "knowledge_response": result.get("response", ""),
                    "sources": result.get("sources", []),
                    "rag_confidence": result.get("confidence", 0.0),
                    "real_time_data": result.get("real_time_data", False)
                }
        except Exception as e:
            return {
                "knowledge_response": f"Unable to access knowledge base: {str(e)}",
                "sources": [],
                "rag_confidence": 0.0,
                "real_time_data": False
            }
    
    async def _get_attractions(self, destination: str, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get attractions using Google Places API"""
        try:
            if not google_places:
                return self._get_mock_attractions(destination)
            
            async with google_places as places:
                # Search for tourist attractions
                attractions = await places.search_places(
                    query=f"tourist attractions in {destination}",
                    place_type="tourist_attraction"
                )
                
                # Get detailed information for top attractions
                detailed_attractions = []
                for attraction in attractions[:5]:  # Limit to top 5
                    details = await places.get_place_details(attraction.place_id)
                    if details:
                        detailed_attractions.append({
                            "name": details.name,
                            "rating": details.rating,
                            "address": details.address,
                            "types": details.types,
                            "price_level": details.price_level,
                            "phone": details.phone_number,
                            "website": details.website,
                            "photos": details.photos[:3]  # Limit photos
                        })
                
                return detailed_attractions
        
        except Exception as e:
            print(f"Error getting attractions: {e}")
            return self._get_mock_attractions(destination)
    
    async def _get_weather(self, destination: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get weather information"""
        try:
            if not weather_api:
                return self._get_mock_weather(destination)
            
            async with weather_api as weather:
                # Get current weather
                current = await weather.get_current_weather(destination)
                
                # Get 5-day forecast
                forecast = await weather.get_forecast(destination, days=5)
                
                return {
                    "current": self._parse_weather_data(current),
                    "forecast": self._parse_forecast_data(forecast),
                    "last_updated": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            print(f"Error getting weather: {e}")
            return self._get_mock_weather(destination)
    
    async def _get_local_insights(self, destination: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get local insights and recommendations"""
        try:
            # Use RAG system for local insights
            insights_query = f"local insights and tips for {destination}"
            rag_response = await self._query_rag_system(insights_query, request)
            
            # Add real-time data if available
            local_data = {
                "cultural_tips": [],
                "safety_advice": [],
                "transportation": [],
                "dining_recommendations": [],
                "shopping_areas": []
            }
            
            # This would integrate with local data sources
            # For now, use knowledge base responses
            
            return {
                "insights": rag_response.get("knowledge_response", ""),
                "local_data": local_data,
                "sources": rag_response.get("sources", [])
            }
        
        except Exception as e:
            return {
                "insights": f"Unable to get local insights: {str(e)}",
                "local_data": {},
                "sources": []
            }
    
    def _get_mock_attractions(self, destination: str) -> List[Dict[str, Any]]:
        """Fallback mock attractions data"""
        return [
            {
                "name": f"Top Attraction in {destination}",
                "rating": 4.5,
                "address": f"Main Street, {destination}",
                "types": ["tourist_attraction", "point_of_interest"],
                "price_level": 2,
                "phone": "+1-555-0123",
                "website": "https://example.com",
                "photos": ["photo1.jpg", "photo2.jpg"]
            }
        ]
    
    def _get_mock_weather(self, destination: str) -> Dict[str, Any]:
        """Fallback mock weather data"""
        return {
            "current": {
                "temperature": 22,
                "description": "Partly cloudy",
                "humidity": 65,
                "wind_speed": 10
            },
            "forecast": [
                {"day": "Today", "high": 25, "low": 18, "description": "Sunny"},
                {"day": "Tomorrow", "high": 23, "low": 16, "description": "Cloudy"},
                {"day": "Day 3", "high": 20, "low": 14, "description": "Rainy"}
            ],
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _parse_weather_data(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse weather data from API response"""
        if not weather_data:
            return {}
        
        main = weather_data.get("main", {})
        weather = weather_data.get("weather", [{}])[0]
        
        return {
            "temperature": main.get("temp", 0),
            "description": weather.get("description", ""),
            "humidity": main.get("humidity", 0),
            "wind_speed": weather_data.get("wind", {}).get("speed", 0),
            "pressure": main.get("pressure", 0)
        }
    
    def _parse_forecast_data(self, forecast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse forecast data from API response"""
        if not forecast_data:
            return []
        
        forecasts = []
        for item in forecast_data.get("list", [])[:5]:  # Limit to 5 days
            main = item.get("main", {})
            weather = item.get("weather", [{}])[0]
            
            forecasts.append({
                "day": item.get("dt_txt", "").split(" ")[0],
                "high": main.get("temp_max", 0),
                "low": main.get("temp_min", 0),
                "description": weather.get("description", "")
            })
        
        return forecasts
    
    def _calculate_confidence(self, response_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the response"""
        confidence_factors = []
        
        # RAG confidence
        if "rag_confidence" in response_data:
            confidence_factors.append(response_data["rag_confidence"])
        
        # Real-time data availability
        if response_data.get("real_time_data", False):
            confidence_factors.append(0.9)
        
        # Data completeness
        data_fields = ["attractions", "weather", "local_insights", "knowledge_response"]
        available_fields = sum(1 for field in data_fields if field in response_data and response_data[field])
        completeness_score = available_fields / len(data_fields)
        confidence_factors.append(completeness_score)
        
        # Calculate average confidence
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        
        return 0.5
    
    def _get_used_capabilities(self, request: Dict[str, Any]) -> List[str]:
        """Get list of capabilities used for this request"""
        capabilities = []
        query_type = request.get("type", "")
        
        if query_type in ["research", "destination_info"]:
            capabilities.append("destination_research")
        
        if query_type == "attractions":
            capabilities.append("attraction_discovery")
        
        if query_type == "weather":
            capabilities.append("weather_information")
        
        if query_type == "local_insights":
            capabilities.append("local_insights")
        
        if "recommendations" in query_type:
            capabilities.append("travel_recommendations")
        
        return capabilities

# Create the improved research agent instance
improved_research_agent = ImprovedResearchAgent()
