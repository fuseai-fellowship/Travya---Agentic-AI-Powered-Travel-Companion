"""
Itinerary Parser Service
Uses Google AI Studio to extract places from travel itineraries
"""

import os
import json
import aiohttp
from typing import List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExtractedPlace:
    """Represents a place extracted from an itinerary"""
    name: str
    type: str  # 'city', 'landmark', 'natural_spot'
    caption: str
    search_query: str

class ItineraryParserService:
    """Service for parsing itineraries and extracting places using Google AI Studio"""
    
    def __init__(self):
        self.google_ai_api_key = os.getenv('GOOGLE_AI_STUDIO_API_KEY')
        self.google_ai_api_key_fallback = os.getenv('GOOGLE_AI_STUDIO_API_KEY_FALLBACK')
        if not self.google_ai_api_key:
            logger.warning("Google AI Studio API key not found")
        if not self.google_ai_api_key_fallback:
            logger.warning("Google AI Studio fallback API key not found")
    
    async def extract_places_from_itinerary(self, itinerary_text: str, trip_url: str = None) -> List[ExtractedPlace]:
        """
        Extract places from itinerary text using Google AI Studio with chunking for long itineraries
        
        Args:
            itinerary_text: The itinerary text to parse
            trip_url: Optional trip URL for context
            
        Returns:
            List of ExtractedPlace objects
        """
        if not self.google_ai_api_key and not self.google_ai_api_key_fallback:
            logger.error("Google AI Studio API keys not configured")
            return []
        
        try:
            # First try direct extraction from structured data
            logger.info(f"Starting extraction for itinerary text (length: {len(itinerary_text)})")
            direct_places = self._extract_places_directly(itinerary_text)
            if direct_places:
                logger.info(f"Direct extraction found {len(direct_places)} places: {[p.name for p in direct_places]}")
                prioritized_places = self._prioritize_places(direct_places)
                return prioritized_places
            
            # For long itineraries, use chunking strategy
            if len(itinerary_text) > 2000:
                logger.info("Long itinerary detected, using chunking strategy")
                return await self._extract_places_with_chunking(itinerary_text, trip_url)
            
            # Fallback to single LLM extraction for shorter itineraries
            logger.info("Using single LLM extraction for shorter itinerary")
            prompt = self._create_extraction_prompt(itinerary_text, trip_url)
            response = await self._call_google_ai_studio(prompt)
            places = self._parse_llm_response(response)
            prioritized_places = self._prioritize_places(places)
            
            return prioritized_places
            
        except Exception as e:
            logger.error(f"Error extracting places from itinerary: {e}")
            return []
    
    async def _extract_places_with_chunking(self, itinerary_text: str, trip_url: str = None) -> List[ExtractedPlace]:
        """Extract places using chunking strategy for long itineraries"""
        try:
            # Parse the JSON to extract days
            itinerary_data = json.loads(itinerary_text)
            
            if 'itinerary' not in itinerary_data or 'itinerary' not in itinerary_data['itinerary'] or 'days' not in itinerary_data['itinerary']['itinerary']:
                logger.warning("No days found in itinerary data, falling back to single extraction")
                return await self._extract_places_single_chunk(itinerary_text, trip_url)
            
            days = itinerary_data['itinerary']['itinerary']['days']
            logger.info(f"Found {len(days)} days in itinerary, processing with chunking")
            
            all_places = []
            
            # Process each day as a separate chunk
            for i, day in enumerate(days):
                try:
                    # Create a focused chunk for this day
                    day_chunk = self._create_day_chunk(day, i + 1)
                    
                    # Extract places from this day
                    day_places = await self._extract_places_from_chunk(day_chunk, f"Day {i + 1}")
                    
                    if day_places:
                        logger.info(f"Day {i + 1} extracted {len(day_places)} places: {[p.name for p in day_places]}")
                        all_places.extend(day_places)
                    else:
                        logger.warning(f"No places found in Day {i + 1}")
                        
                except Exception as e:
                    logger.error(f"Error processing Day {i + 1}: {e}")
                    continue
            
            # Remove duplicates and prioritize
            unique_places = self._remove_duplicate_places(all_places)
            prioritized_places = self._prioritize_places(unique_places)
            
            logger.info(f"Chunking strategy found {len(prioritized_places)} unique places from {len(days)} days")
            return prioritized_places
            
        except Exception as e:
            logger.error(f"Error in chunking strategy: {e}")
            # Fallback to single chunk extraction
            return await self._extract_places_single_chunk(itinerary_text, trip_url)
    
    def _create_day_chunk(self, day_data: dict, day_number: int) -> str:
        """Create a focused chunk for a single day"""
        chunk_parts = [f"Day {day_number}:"]
        
        # Add theme if available
        if 'theme' in day_data:
            chunk_parts.append(f"Theme: {day_data['theme']}")
        
        # Add activities
        if 'activities' in day_data:
            chunk_parts.append("Activities:")
            for activity in day_data['activities']:
                activity_text = f"- {activity.get('time', '')} {activity.get('activity', '')}"
                if 'location' in activity:
                    activity_text += f" at {activity['location']}"
                if 'description' in activity:
                    activity_text += f" - {activity['description']}"
                chunk_parts.append(activity_text)
        
        # Add meals
        if 'meals' in day_data:
            chunk_parts.append("Meals:")
            for meal in day_data['meals']:
                meal_text = f"- {meal.get('time', '')} {meal.get('type', '')}"
                if 'restaurant' in meal:
                    meal_text += f" at {meal['restaurant']}"
                chunk_parts.append(meal_text)
        
        # Add transportation
        if 'transportation' in day_data:
            chunk_parts.append("Transportation:")
            for transport in day_data['transportation']:
                transport_text = f"- {transport.get('method', '')} from {transport.get('from', '')} to {transport.get('to', '')}"
                chunk_parts.append(transport_text)
        
        return "\n".join(chunk_parts)
    
    async def _extract_places_from_chunk(self, chunk_text: str, chunk_name: str) -> List[ExtractedPlace]:
        """Extract places from a single chunk"""
        try:
            prompt = self._create_chunk_extraction_prompt(chunk_text, chunk_name)
            response = await self._call_google_ai_studio(prompt)
            places = self._parse_llm_response(response)
            return places
        except Exception as e:
            logger.error(f"Error extracting places from {chunk_name}: {e}")
            return []
    
    async def _extract_places_single_chunk(self, itinerary_text: str, trip_url: str = None) -> List[ExtractedPlace]:
        """Fallback to single chunk extraction"""
        try:
            prompt = self._create_extraction_prompt(itinerary_text, trip_url)
            response = await self._call_google_ai_studio(prompt)
            places = self._parse_llm_response(response)
            prioritized_places = self._prioritize_places(places)
            return prioritized_places
        except Exception as e:
            logger.error(f"Error in single chunk extraction: {e}")
            return []
    
    def _create_chunk_extraction_prompt(self, chunk_text: str, chunk_name: str) -> str:
        """Create a prompt for extracting places from a single chunk"""
        return f"""You are a travel expert. Extract EVERY SINGLE place, location, landmark, city, village, natural feature, restaurant, hotel, viewpoint, and attraction mentioned in this {chunk_name}.

{chunk_name} Details:
{chunk_text}

IMPORTANT: Extract ALL places mentioned in this {chunk_name}. Look for:
- Every city, town, village mentioned
- Every natural feature (mountains, rivers, lakes, valleys)
- Every landmark, temple, stupa, viewpoint, museum
- Every restaurant, hotel, guesthouse mentioned
- Every transportation hub (bus park, airport, station)
- Every specific location (viewpoints, trails, markets)

Return JSON array with name, type, caption, search_query for each place.
Types: city, landmark, natural_spot, mountain, lake, temple, village, viewpoint, market, restaurant, hotel, airport, station, river, valley, trail, guesthouse, museum, stupa, pagoda.

Be thorough and extract every place mentioned in this {chunk_name}."""
    
    def _remove_duplicate_places(self, places: List[ExtractedPlace]) -> List[ExtractedPlace]:
        """Remove duplicate places based on name similarity"""
        unique_places = []
        seen_names = set()
        
        for place in places:
            # Normalize name for comparison
            normalized_name = place.name.lower().strip()
            
            # Check if we've seen a similar name
            is_duplicate = False
            for seen_name in seen_names:
                if (normalized_name in seen_name or seen_name in normalized_name or 
                    normalized_name == seen_name):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_places.append(place)
                seen_names.add(normalized_name)
        
        return unique_places

    def _extract_places_directly(self, itinerary_text: str) -> List[ExtractedPlace]:
        """Extract places directly from structured itinerary data"""
        try:
            logger.info(f"Attempting direct extraction from itinerary text (length: {len(itinerary_text)})")
            # Parse the JSON itinerary data
            itinerary_data = json.loads(itinerary_text)
            logger.info(f"Successfully parsed JSON, looking for places...")
            
            places = []
            
            # Extract from overview
            if 'itinerary' in itinerary_data and 'itinerary' in itinerary_data['itinerary'] and 'overview' in itinerary_data['itinerary']['itinerary']:
                overview = itinerary_data['itinerary']['itinerary']['overview']
                if 'destination' in overview:
                    destination = overview['destination']
                    places.append(ExtractedPlace(
                        name=destination,
                        type='natural_spot',
                        caption=f"Main destination: {destination}",
                        search_query=destination
                    ))
            
            # Extract from days and activities
            if 'itinerary' in itinerary_data and 'itinerary' in itinerary_data['itinerary'] and 'days' in itinerary_data['itinerary']['itinerary']:
                for day in itinerary_data['itinerary']['itinerary']['days']:
                    # Extract from activities
                    if 'activities' in day:
                        for activity in day['activities']:
                            if 'location' in activity:
                                location = activity['location']
                                if location and location not in [p.name for p in places]:
                                    # Determine place type based on location name
                                    place_type = self._determine_place_type(location, activity.get('activity', ''))
                                    places.append(ExtractedPlace(
                                        name=location,
                                        type=place_type,
                                        caption=f"Location: {location}",
                                        search_query=location
                                    ))
                    
                    # Extract from meals
                    if 'meals' in day:
                        for meal in day['meals']:
                            if 'restaurant' in meal:
                                restaurant = meal['restaurant']
                                if restaurant and restaurant not in [p.name for p in places]:
                                    places.append(ExtractedPlace(
                                        name=restaurant,
                                        type='restaurant',
                                        caption=f"Restaurant: {restaurant}",
                                        search_query=restaurant
                                    ))
                    
                    # Extract from transportation
                    if 'transportation' in day:
                        for transport in day['transportation']:
                            if 'from' in transport and transport['from'] not in [p.name for p in places]:
                                places.append(ExtractedPlace(
                                    name=transport['from'],
                                    type='station',
                                    caption=f"Transport hub: {transport['from']}",
                                    search_query=transport['from']
                                ))
                            if 'to' in transport and transport['to'] not in [p.name for p in places]:
                                places.append(ExtractedPlace(
                                    name=transport['to'],
                                    type='station',
                                    caption=f"Transport hub: {transport['to']}",
                                    search_query=transport['to']
                                ))
            
            logger.info(f"Direct extraction found {len(places)} places: {[p.name for p in places]}")
            if len(places) == 0:
                logger.warning("No places found in direct extraction, this might indicate an issue with the JSON structure")
            return places
            
        except Exception as e:
            logger.error(f"Error in direct extraction: {e}")
            return []
    
    def _determine_place_type(self, location: str, activity: str) -> str:
        """Determine place type based on location name and activity"""
        location_lower = location.lower()
        activity_lower = activity.lower()
        
        # Natural features
        if any(word in location_lower for word in ['mountain', 'peak', 'range', 'circuit', 'trek', 'trail']):
            return 'mountain'
        if any(word in location_lower for word in ['lake', 'river', 'khola', 'valley']):
            return 'natural_spot'
        
        # Villages and settlements
        if any(word in location_lower for word in ['village', 'village', 'settlement']):
            return 'village'
        
        # Cities and towns
        if any(word in location_lower for word in ['pokhara', 'kathmandu', 'city', 'town']):
            return 'city'
        
        # Transportation hubs
        if any(word in location_lower for word in ['bus', 'park', 'station', 'airport', 'terminal']):
            return 'station'
        
        # Restaurants and hotels
        if any(word in activity_lower for word in ['restaurant', 'hotel', 'guesthouse', 'dining']):
            return 'restaurant'
        
        # Default to landmark
        return 'landmark'

    def _create_extraction_prompt(self, itinerary_text: str, trip_url: str = None) -> str:
        """Create a prompt for the LLM to extract places"""
        # Truncate the itinerary text to avoid token limits
        max_length = 2000  # Increased to 2000 characters to capture more details
        if len(itinerary_text) > max_length:
            itinerary_text = itinerary_text[:max_length] + "..."
        
        return f"""You are a travel expert. Extract EVERY SINGLE place, location, landmark, city, village, natural feature, restaurant, hotel, viewpoint, and attraction mentioned in this itinerary. Be extremely thorough and comprehensive.

Itinerary: {itinerary_text}

IMPORTANT: Extract at least 8-12 different places. Look for:
- Every city, town, village mentioned (Pokhara, Ghandruk, Nayapul, Birethanti, etc.)
- Every natural feature (Annapurna range, Modi Khola river, mountains, lakes, valleys)
- Every landmark, temple, stupa, viewpoint, museum
- Every restaurant, hotel, guesthouse mentioned
- Every transportation hub (bus park, airport, station)
- Every specific location (viewpoints, trails, markets)

Return JSON array with name, type, caption, search_query for each place.
Types: city, landmark, natural_spot, mountain, lake, temple, village, viewpoint, market, restaurant, hotel, airport, station, river, valley, trail, guesthouse, museum, stupa, pagoda.

Extract places like:
- Pokhara (city)
- Ghandruk (village) 
- Nayapul (village)
- Birethanti (village)
- Annapurna range (mountain)
- Modi Khola (river)
- Tourist Bus Park (station)
- Lakeside (area)
- Gurung Museum (museum)
- ACAP office (landmark)
- Any guesthouse, restaurant, viewpoint mentioned

Return at least 8-12 places in the JSON array."""
    
    async def _call_google_ai_studio(self, prompt: str) -> str:
        """Call Google AI Studio API with fallback support"""
        # Try primary API key first
        try:
            return await self._make_api_call(prompt, self.google_ai_api_key, "primary")
        except Exception as e:
            logger.warning(f"Primary API key failed: {e}")
            
            # Try fallback API key if available
            if self.google_ai_api_key_fallback:
                logger.info("Trying fallback API key...")
                try:
                    return await self._make_api_call(prompt, self.google_ai_api_key_fallback, "fallback")
                except Exception as fallback_error:
                    logger.error(f"Fallback API key also failed: {fallback_error}")
                    raise Exception(f"Both primary and fallback API keys failed. Primary: {e}, Fallback: {fallback_error}")
            else:
                raise e
    
    async def _make_api_call(self, prompt: str, api_key: str, key_type: str) -> str:
        """Make API call with specific key"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "topK": 1,
                "topP": 0.8,
                "maxOutputTokens": 1024
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Google AI Studio API error ({key_type} key): {response.status}")
                
                data = await response.json()
                logger.info(f"Google AI Studio API response ({key_type} key): {json.dumps(data, indent=2)}")
                
                # Extract the generated text
                if 'candidates' in data and len(data['candidates']) > 0:
                    candidate = data['candidates'][0]
                    if 'finishReason' in candidate:
                        logger.info(f"Finish reason ({key_type} key): {candidate['finishReason']}")
                    
                    if 'content' in candidate:
                        content = candidate['content']
                        if 'parts' in content and len(content['parts']) > 0:
                            return content['parts'][0]['text']
                    else:
                        logger.warning(f"No content in candidate ({key_type} key)")
                else:
                    logger.warning(f"No candidates in response ({key_type} key)")
                
                raise Exception(f"No content generated by Google AI Studio ({key_type} key)")
    
    def _parse_llm_response(self, response: str) -> List[ExtractedPlace]:
        """Parse the LLM response and extract places"""
        try:
            # Clean the response to extract JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            places_data = json.loads(response)
            
            places = []
            for place_data in places_data:
                place = ExtractedPlace(
                    name=place_data.get('name', ''),
                    type=place_data.get('type', 'landmark'),
                    caption=place_data.get('caption', ''),
                    search_query=place_data.get('search_query', place_data.get('name', ''))
                )
                places.append(place)
            
            return places
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM response as JSON: {e}")
            logger.error(f"Response was: {response}")
            return []
        except Exception as e:
            logger.error(f"Error parsing places from LLM response: {e}")
            return []
    
    def _prioritize_places(self, places: List[ExtractedPlace]) -> List[ExtractedPlace]:
        """Prioritize places based on photogenic potential"""
        # Define priority weights for different types
        type_weights = {
            'landmark': 4,
            'mountain': 4,
            'natural_spot': 3,
            'temple': 3,
            'viewpoint': 3,
            'village': 2,
            'city': 2,
            'lake': 2,
            'market': 1,
            'restaurant': 1,
            'hotel': 1,
            'airport': 1,
            'station': 1,
            'river': 2,
            'valley': 2,
            'trail': 2,
            'guesthouse': 1,
            'museum': 3,
            'stupa': 3,
            'pagoda': 3
        }
        
        # Define keywords that indicate photogenic places
        photogenic_keywords = [
            'temple', 'stupa', 'pagoda', 'monument', 'palace', 'castle',
            'lake', 'mountain', 'beach', 'waterfall', 'valley', 'canyon',
            'garden', 'park', 'square', 'market', 'bridge', 'tower',
            'cathedral', 'mosque', 'church', 'monastery', 'fort', 'ruins',
            'viewpoint', 'summit', 'peak', 'range', 'valley', 'river',
            'village', 'settlement', 'heritage', 'cultural', 'traditional',
            'circuit', 'trek', 'trail', 'national park', 'reserve', 'sanctuary'
        ]
        
        def calculate_score(place: ExtractedPlace) -> int:
            score = type_weights.get(place.type, 1)
            
            # Add bonus for photogenic keywords
            name_lower = place.name.lower()
            caption_lower = place.caption.lower()
            
            for keyword in photogenic_keywords:
                if keyword in name_lower or keyword in caption_lower:
                    score += 2
                    break
            
            return score
        
        # Sort by score (highest first) and limit to top 15 (increased from 10)
        prioritized = sorted(places, key=calculate_score, reverse=True)
        return prioritized[:15]

# Global service instance
itinerary_parser_service = ItineraryParserService()
