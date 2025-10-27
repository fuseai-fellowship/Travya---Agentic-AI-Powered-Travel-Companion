"""
Travya Map Parser v2 - Backend LLM for processing large multi-day travel itineraries
and producing day-wise, geo-enriched map data for visualization.
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)

class TravyaMapParser:
    """
    Intelligent parser for large travel itineraries that converts raw content
    into structured geo-enriched map data for Travya's dynamic travel map UI.
    """
    
    def __init__(self):
        self.nominatim_base_url = "https://nominatim.openstreetmap.org/search"
        self.elevation_base_url = "https://api.open-meteo.com/v1/elevation"
        self.max_chunk_days = 2
        self.max_tokens_per_chunk = 4000
    
    async def parse_itinerary(self, itinerary_data: Dict[str, Any], chat_id: str, trip_id: str = None, db_session = None) -> Dict[str, Any]:
        """
        Main entry point for parsing itineraries.
        
        Args:
            itinerary_data: Raw itinerary JSON data
            chat_id: Unique chat identifier
            
        Returns:
            Structured map data ready for frontend visualization
        """
        try:
            logger.info(f"Starting itinerary parsing for chat {chat_id}")
            
            # Extract days from itinerary
            days = self._extract_days(itinerary_data)
            
            if not days:
                return self._create_empty_response(chat_id)
            
            # Determine if chunking is needed
            if len(days) <= self.max_chunk_days:
                # Process directly
                map_data = await self._process_chunk(days, chunk_id=1)
            else:
                # Chunk and process
                chunks = self._create_chunks(days)
                map_data = await self._process_chunks(chunks)
            
            # Generate summary text
            summary_text = self._generate_summary_text(days)
            
            # Create final response
            response = {
                "chatId": chat_id,
                "content_type": "text/markdown",
                "text": summary_text,
                "map_data": map_data
            }
            
            # Save to database if trip_id and db_session are provided
            if trip_id and db_session:
                try:
                    import json
                    from sqlmodel import select
                    from app.models import Trip
                    
                    # Convert response to JSON string
                    map_data_json = json.dumps(response)
                    
                    # Update trip with map data
                    statement = select(Trip).where(Trip.id == trip_id)
                    trip = db_session.exec(statement).first()
                    if trip:
                        trip.map_data = map_data_json
                        db_session.add(trip)
                        db_session.commit()
                        logger.info(f"Saved map data to database for trip {trip_id}")
                    else:
                        logger.warning(f"Trip {trip_id} not found for map data storage")
                        
                except Exception as db_error:
                    logger.error(f"Error saving map data to database: {str(db_error)}")
                    # Don't fail the whole operation if DB save fails
            
            logger.info(f"Successfully parsed itinerary with {len(map_data)} locations")
            return response
            
        except Exception as e:
            logger.error(f"Error parsing itinerary: {str(e)}")
            return self._create_error_response(chat_id, str(e))
    
    def _extract_days(self, itinerary_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract days array from itinerary data."""
        try:
            # Navigate through the nested structure
            itinerary = itinerary_data.get("itinerary", {})
            if isinstance(itinerary, dict):
                itinerary = itinerary.get("itinerary", itinerary)
            
            days = itinerary.get("days", [])
            if not isinstance(days, list):
                logger.warning("No valid days array found in itinerary")
                return []
            
            logger.info(f"Extracted {len(days)} days from itinerary")
            return days
            
        except Exception as e:
            logger.error(f"Error extracting days: {str(e)}")
            return []
    
    def _create_chunks(self, days: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Split days into chunks for processing."""
        chunks = []
        for i in range(0, len(days), self.max_chunk_days):
            chunk = days[i:i + self.max_chunk_days]
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks from {len(days)} days")
        return chunks
    
    async def _process_chunks(self, chunks: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Process multiple chunks and merge results."""
        all_map_data = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i + 1}/{len(chunks)}")
            chunk_data = await self._process_chunk(chunk, chunk_id=i + 1)
            all_map_data.extend(chunk_data)
        
        # Deduplicate and sort by day
        return self._deduplicate_and_sort(all_map_data)
    
    async def _process_chunk(self, days: List[Dict[str, Any]], chunk_id: int) -> List[Dict[str, Any]]:
        """Process a single chunk of days."""
        map_data = []
        
        for day_data in days:
            day_number = day_data.get("day", 0)
            logger.info(f"Processing day {day_number}")
            
            # Extract locations from activities
            activities = day_data.get("activities", [])
            for activity in activities:
                location_data = await self._process_activity(activity, day_number)
                if location_data:
                    map_data.append(location_data)
            
            # Extract locations from transportation
            transportation = day_data.get("transportation", [])
            for transport in transportation:
                location_data = await self._process_transportation(transport, day_number)
                if location_data:
                    map_data.append(location_data)
            
            # Extract hotel/accommodation
            meals = day_data.get("meals", [])
            for meal in meals:
                if isinstance(meal, dict) and meal.get("hotel"):
                    location_data = await self._process_hotel(meal["hotel"], day_number)
                    if location_data:
                        map_data.append(location_data)
        
        logger.info(f"Chunk {chunk_id} processed with {len(map_data)} locations")
        return map_data
    
    async def _process_activity(self, activity: Dict[str, Any], day: int) -> Optional[Dict[str, Any]]:
        """Process a single activity and extract location data."""
        try:
            location = activity.get("location", "")
            if not location:
                return None
            
            # Clean location string
            location = self._clean_location_string(location)
            
            # Get coordinates
            coords = await self._get_coordinates(location)
            if not coords:
                return None
            
            # Get elevation
            elevation = await self._get_elevation(coords["lat"], coords["lng"])
            
            return {
                "day": day,
                "name": location,
                "lat": coords["lat"],
                "lng": coords["lng"],
                "description": activity.get("activity", ""),
                "time": activity.get("time", ""),
                "elevation": elevation
            }
            
        except Exception as e:
            logger.error(f"Error processing activity: {str(e)}")
            return None
    
    async def _process_transportation(self, transport: Dict[str, Any], day: int) -> Optional[Dict[str, Any]]:
        """Process transportation data and extract location."""
        try:
            # Extract location from transportation
            location = transport.get("location", "") or transport.get("from", "") or transport.get("to", "")
            if not location:
                return None
            
            location = self._clean_location_string(location)
            coords = await self._get_coordinates(location)
            if not coords:
                return None
            
            elevation = await self._get_elevation(coords["lat"], coords["lng"])
            
            return {
                "day": day,
                "name": location,
                "lat": coords["lat"],
                "lng": coords["lng"],
                "description": f"Transportation: {transport.get('method', '')}",
                "time": transport.get("time", ""),
                "elevation": elevation
            }
            
        except Exception as e:
            logger.error(f"Error processing transportation: {str(e)}")
            return None
    
    async def _process_hotel(self, hotel: str, day: int) -> Optional[Dict[str, Any]]:
        """Process hotel/accommodation data."""
        try:
            if not hotel:
                return None
            
            location = self._clean_location_string(hotel)
            coords = await self._get_coordinates(location)
            if not coords:
                return None
            
            elevation = await self._get_elevation(coords["lat"], coords["lng"])
            
            return {
                "day": day,
                "name": location,
                "lat": coords["lat"],
                "lng": coords["lng"],
                "description": "Accommodation",
                "hotel": hotel,
                "elevation": elevation
            }
            
        except Exception as e:
            logger.error(f"Error processing hotel: {str(e)}")
            return None
    
    def _clean_location_string(self, location: str) -> str:
        """
        Clean and extract the most specific location name from a location string.
        Prioritizes specific place names over generic terms.
        """
        if not location:
            return ""
        
        # Remove common generic terms that cause incorrect geocoding
        generic_terms = [
            "bus park", "bus station", "airport", "hotel", "restaurant", 
            "guesthouse", "viewpoint", "local restaurant", "guesthouse restaurant",
            "tourist bus", "taxi", "trek", "breakfast", "lunch", "dinner",
            "check-in", "rest and relax", "explore", "sunset photography",
            "sunrise viewing", "lakeside stroll", "takeoff point", "dock",
            "area", "near", "around", "vicinity", "region", "zone"
        ]
        
        location_lower = location.lower()
        
        # Extract specific place names (usually capitalized or in parentheses)
        import re
        
        # Look for place names in parentheses first
        parentheses_match = re.search(r'\(([^)]+)\)', location)
        if parentheses_match:
            place_name = parentheses_match.group(1).strip()
            # If it's a specific place name (not generic), use it
            if not any(term in place_name.lower() for term in generic_terms):
                return place_name
        
        # Look for specific place names BEFORE parentheses (e.g., "Sarangkot (takeoff point)")
        before_parentheses = location.split('(')[0].strip()
        if before_parentheses and before_parentheses != location:
            # This means there were parentheses, so use the part before them
            words = before_parentheses.split()
            specific_words = []
            
            for word in words:
                word_clean = word.strip('.,()').lower()
                # Skip generic terms
                if word_clean not in generic_terms and len(word_clean) > 2:
                    specific_words.append(word.strip('.,()'))
            
            if specific_words:
                cleaned = ' '.join(specific_words)
                return cleaned
        
        # Look for specific place names (capitalized words)
        words = location.split()
        specific_words = []
        
        for word in words:
            word_clean = word.strip('.,()').lower()
            # Skip generic terms
            if word_clean not in generic_terms and len(word_clean) > 2:
                specific_words.append(word.strip('.,()'))
        
        if specific_words:
            # Join specific words, prioritizing longer names
            cleaned = ' '.join(specific_words)
            return cleaned
        
        # Fallback: return original location
        return location.strip()
    
    async def _get_coordinates(self, location: str) -> Optional[Dict[str, float]]:
        """Get coordinates for a location using Nominatim API."""
        try:
            if not location:
                return None
            
            # Add country context for better geocoding accuracy
            search_query = f"{location}, Nepal"
            
            async with httpx.AsyncClient() as client:
                params = {
                    "q": search_query,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1
                }
                
                response = await client.get(self.nominatim_base_url, params=params, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                if data and len(data) > 0:
                    result = data[0]
                    return {
                        "lat": float(result["lat"]),
                        "lng": float(result["lon"])
                    }
                
                logger.warning(f"No coordinates found for location: {location}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting coordinates for {location}: {str(e)}")
            return None
    
    async def _get_elevation(self, lat: float, lng: float) -> Optional[str]:
        """Get elevation for coordinates using Open-Meteo API."""
        try:
            async with httpx.AsyncClient() as client:
                params = {
                    "latitude": lat,
                    "longitude": lng
                }
                
                response = await client.get(self.elevation_base_url, params=params, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                if "elevation" in data and data["elevation"]:
                    elevation_m = data["elevation"][0]
                    return f"{elevation_m:.0f}m"
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting elevation for {lat}, {lng}: {str(e)}")
            return None
    
    def _deduplicate_and_sort(self, map_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and sort by day."""
        seen = set()
        unique_data = []
        
        for item in map_data:
            # Create a key for deduplication
            key = (item["day"], item["name"], item["lat"], item["lng"])
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        
        # Sort by day
        unique_data.sort(key=lambda x: x["day"])
        
        logger.info(f"Deduplicated from {len(map_data)} to {len(unique_data)} locations")
        return unique_data
    
    def _generate_summary_text(self, days: List[Dict[str, Any]]) -> str:
        """Generate markdown summary text for the itinerary."""
        if not days:
            return "No itinerary data available."
        
        summary_parts = []
        
        for day_data in days:
            day_number = day_data.get("day", 0)
            summary_parts.append(f"### Day {day_number}")
            
            # Add activities
            activities = day_data.get("activities", [])
            for activity in activities:
                time = activity.get("time", "")
                activity_desc = activity.get("activity", "")
                location = activity.get("location", "")
                
                if activity_desc:
                    line = f"- {time} {activity_desc}" if time else f"- {activity_desc}"
                    if location:
                        line += f" ({location})"
                    summary_parts.append(line)
            
            # Add meals/hotels
            meals = day_data.get("meals", [])
            for meal in meals:
                if isinstance(meal, dict) and meal.get("hotel"):
                    summary_parts.append(f"- **Stay:** {meal['hotel']}")
                    break
            
            summary_parts.append("")  # Empty line between days
        
        return "\n".join(summary_parts)
    
    def _create_empty_response(self, chat_id: str) -> Dict[str, Any]:
        """Create response for empty itinerary."""
        return {
            "chatId": chat_id,
            "content_type": "text/markdown",
            "text": "No itinerary data found to parse.",
            "map_data": []
        }
    
    def _create_error_response(self, chat_id: str, error_message: str) -> Dict[str, Any]:
        """Create error response."""
        return {
            "chatId": chat_id,
            "content_type": "text/markdown",
            "text": f"Error parsing itinerary: {error_message}",
            "map_data": []
        }


# Global instance
map_parser = TravyaMapParser()
