"""
External API integrations for travel services.
Includes Google Maps, Amadeus (flights/hotels), and other travel APIs.
"""

import httpx
import asyncio
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel
import os
from app.core.config import settings


# ===== DATA MODELS =====

class Location(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    place_id: Optional[str] = None
    rating: Optional[float] = None
    price_level: Optional[int] = None
    types: List[str] = []


class Attraction(BaseModel):
    name: str
    description: str
    location: Location
    rating: float
    price_level: int
    opening_hours: Optional[Dict[str, Any]] = None
    photos: List[str] = []
    reviews: List[Dict[str, Any]] = []


class Hotel(BaseModel):
    name: str
    address: str
    location: Location
    rating: float
    price_per_night: float
    currency: str
    amenities: List[str] = []
    photos: List[str] = []
    availability: bool = True


class Flight(BaseModel):
    airline: str
    flight_number: str
    departure: Dict[str, Any]  # airport, time, city
    arrival: Dict[str, Any]    # airport, time, city
    duration: str
    price: float
    currency: str
    stops: int
    aircraft: Optional[str] = None


class Restaurant(BaseModel):
    name: str
    description: str
    location: Location
    rating: float
    price_level: int
    cuisine_types: List[str] = []
    opening_hours: Optional[Dict[str, Any]] = None
    photos: List[str] = []


# ===== GOOGLE MAPS API SERVICE =====

class GoogleMapsService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY", "your_google_maps_api_key")
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_places(
        self, 
        query: str, 
        location: Optional[tuple] = None, 
        radius: int = 50000,
        place_type: Optional[str] = None
    ) -> List[Location]:
        """Search for places using Google Places API."""
        
        params = {
            "key": self.api_key,
            "query": query,
            "fields": "place_id,name,formatted_address,geometry,rating,price_level,types"
        }
        
        if location:
            params["location"] = f"{location[0]},{location[1]}"
            params["radius"] = radius
        
        if place_type:
            params["type"] = place_type
        
        try:
            response = await self.client.get(f"{self.base_url}/place/textsearch/json", params=params)
            response.raise_for_status()
            data = response.json()
            
            places = []
            for result in data.get("results", []):
                place = Location(
                    name=result.get("name", ""),
                    address=result.get("formatted_address", ""),
                    latitude=result["geometry"]["location"]["lat"],
                    longitude=result["geometry"]["location"]["lng"],
                    place_id=result.get("place_id"),
                    rating=result.get("rating"),
                    price_level=result.get("price_level"),
                    types=result.get("types", [])
                )
                places.append(place)
            
            return places
            
        except Exception as e:
            print(f"Google Places API error: {e}")
            return []
    
    async def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a place."""
        
        params = {
            "key": self.api_key,
            "place_id": place_id,
            "fields": "name,formatted_address,geometry,rating,price_level,types,opening_hours,photos,reviews"
        }
        
        try:
            response = await self.client.get(f"{self.base_url}/place/details/json", params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("result")
            
        except Exception as e:
            print(f"Google Places Details API error: {e}")
            return None
    
    async def get_directions(
        self, 
        origin: str, 
        destination: str, 
        mode: str = "driving"
    ) -> Optional[Dict[str, Any]]:
        """Get directions between two points."""
        
        params = {
            "key": self.api_key,
            "origin": origin,
            "destination": destination,
            "mode": mode
        }
        
        try:
            response = await self.client.get(f"{self.base_url}/directions/json", params=params)
            response.raise_for_status()
            data = response.json()
            return data
            
        except Exception as e:
            print(f"Google Directions API error: {e}")
            return None
    
    async def geocode_address(self, address: str) -> Optional[Location]:
        """Convert address to coordinates."""
        
        params = {
            "key": self.api_key,
            "address": address
        }
        
        try:
            response = await self.client.get(f"{self.base_url}/geocode/json", params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                result = data["results"][0]
                return Location(
                    name=result.get("formatted_address", ""),
                    address=result.get("formatted_address", ""),
                    latitude=result["geometry"]["location"]["lat"],
                    longitude=result["geometry"]["location"]["lng"],
                    place_id=result.get("place_id")
                )
            
            return None
            
        except Exception as e:
            print(f"Google Geocoding API error: {e}")
            return None


# ===== AMADEUS API SERVICE =====

class AmadeusService:
    def __init__(self):
        self.api_key = os.getenv("AMADEUS_API_KEY", "your_amadeus_api_key")
        self.api_secret = os.getenv("AMADEUS_API_SECRET", "your_amadeus_api_secret")
        self.base_url = "https://test.api.amadeus.com"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
    
    async def _get_access_token(self) -> str:
        """Get access token for Amadeus API."""
        
        if self.access_token:
            return self.access_token
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }
        
        try:
            response = await self.client.post(f"{self.base_url}/v1/security/oauth2/token", data=data)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data["access_token"]
            return self.access_token
            
        except Exception as e:
            print(f"Amadeus token error: {e}")
            raise
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: Optional[date] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0
    ) -> List[Flight]:
        """Search for flights using Amadeus API."""
        
        try:
            token = await self._get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            params = {
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDate": departure_date.isoformat(),
                "adults": adults,
                "children": children,
                "infants": infants,
                "max": 10
            }
            
            if return_date:
                params["returnDate"] = return_date.isoformat()
            
            response = await self.client.get(f"{self.base_url}/v2/shopping/flight-offers", 
                                           headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            flights = []
            for offer in data.get("data", []):
                for itinerary in offer.get("itineraries", []):
                    segments = itinerary.get("segments", [])
                    if segments:
                        first_segment = segments[0]
                        last_segment = segments[-1]
                        
                        flight = Flight(
                            airline=first_segment.get("carrierCode", ""),
                            flight_number=first_segment.get("number", ""),
                            departure={
                                "airport": first_segment.get("departure", {}).get("iataCode", ""),
                                "time": first_segment.get("departure", {}).get("at", ""),
                                "city": first_segment.get("departure", {}).get("iataCode", "")
                            },
                            arrival={
                                "airport": last_segment.get("arrival", {}).get("iataCode", ""),
                                "time": last_segment.get("arrival", {}).get("at", ""),
                                "city": last_segment.get("arrival", {}).get("iataCode", "")
                            },
                            duration=itinerary.get("duration", ""),
                            price=float(offer.get("price", {}).get("total", 0)),
                            currency=offer.get("price", {}).get("currency", "USD"),
                            stops=len(segments) - 1,
                            aircraft=first_segment.get("aircraft", {}).get("code", "")
                        )
                        flights.append(flight)
            
            return flights
            
        except Exception as e:
            print(f"Amadeus flights API error: {e}")
            return []
    
    async def search_hotels(
        self,
        city_code: str,
        check_in: date,
        check_out: date,
        adults: int = 1,
        rooms: int = 1
    ) -> List[Hotel]:
        """Search for hotels using Amadeus API."""
        
        try:
            token = await self._get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            params = {
                "cityCode": city_code,
                "checkInDate": check_in.isoformat(),
                "checkOutDate": check_out.isoformat(),
                "adults": adults,
                "roomQuantity": rooms,
                "max": 10
            }
            
            response = await self.client.get(f"{self.base_url}/v1/reference-data/locations/hotels/by-city",
                                           headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            hotels = []
            for hotel_data in data.get("data", []):
                hotel = Hotel(
                    name=hotel_data.get("name", ""),
                    address=hotel_data.get("address", {}).get("lines", [""])[0],
                    location=Location(
                        name=hotel_data.get("name", ""),
                        address=hotel_data.get("address", {}).get("lines", [""])[0],
                        latitude=hotel_data.get("geoCode", {}).get("latitude", 0.0),
                        longitude=hotel_data.get("geoCode", {}).get("longitude", 0.0)
                    ),
                    rating=hotel_data.get("rating", 0.0),
                    price_per_night=0.0,  # Would need separate pricing API
                    currency="USD",
                    amenities=hotel_data.get("amenities", []),
                    photos=hotel_data.get("media", [])
                )
                hotels.append(hotel)
            
            return hotels
            
        except Exception as e:
            print(f"Amadeus hotels API error: {e}")
            return []


# ===== WEATHER API SERVICE =====

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY", "your_openweather_api_key")
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_weather(
        self, 
        latitude: float, 
        longitude: float, 
        date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """Get weather information for a location."""
        
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric"
        }
        
        if date:
            # For historical weather (requires paid plan)
            params["dt"] = int(datetime.combine(date, datetime.min.time()).timestamp())
            endpoint = "onecall/timemachine"
        else:
            endpoint = "weather"
        
        try:
            response = await self.client.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Weather API error: {e}")
            return None
    
    async def get_forecast(
        self, 
        latitude: float, 
        longitude: float, 
        days: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Get weather forecast for a location."""
        
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
            "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
        }
        
        try:
            response = await self.client.get(f"{self.base_url}/forecast", params=params)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Weather forecast API error: {e}")
            return None


# ===== TRAVEL API ORCHESTRATOR =====

class TravelAPIService:
    def __init__(self):
        self.google_maps = GoogleMapsService()
        self.amadeus = AmadeusService()
        self.weather = WeatherService()
    
    async def search_destination_info(self, destination: str) -> Dict[str, Any]:
        """Get comprehensive information about a destination."""
        
        # Get location coordinates
        location = await self.google_maps.geocode_address(destination)
        if not location:
            return {"error": "Location not found"}
        
        # Search for attractions, restaurants, and hotels
        attractions_task = self.google_maps.search_places(
            f"attractions in {destination}", 
            (location.latitude, location.longitude),
            place_type="tourist_attraction"
        )
        
        restaurants_task = self.google_maps.search_places(
            f"restaurants in {destination}", 
            (location.latitude, location.longitude),
            place_type="restaurant"
        )
        
        hotels_task = self.google_maps.search_places(
            f"hotels in {destination}", 
            (location.latitude, location.longitude),
            place_type="lodging"
        )
        
        weather_task = self.weather.get_forecast(location.latitude, location.longitude)
        
        # Wait for all requests to complete
        attractions, restaurants, hotels, weather_data = await asyncio.gather(
            attractions_task, restaurants_task, hotels_task, weather_task
        )
        
        return {
            "location": location,
            "attractions": attractions[:10],  # Top 10 attractions
            "restaurants": restaurants[:10],  # Top 10 restaurants
            "hotels": hotels[:10],           # Top 10 hotels
            "weather": weather_data
        }
    
    async def search_travel_options(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: Optional[date] = None,
        travelers: int = 1
    ) -> Dict[str, Any]:
        """Search for comprehensive travel options."""
        
        # Search flights
        flights = await self.amadeus.search_flights(
            origin, destination, departure_date, return_date, travelers
        )
        
        # Get destination information
        destination_info = await self.search_destination_info(destination)
        
        return {
            "flights": flights,
            "destination_info": destination_info
        }
    
    async def get_trip_recommendations(
        self,
        destination: str,
        trip_type: str = "leisure",
        interests: List[str] = None,
        budget: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get personalized trip recommendations."""
        
        if interests is None:
            interests = []
        
        # Get destination information
        destination_info = await self.search_destination_info(destination)
        
        # Filter attractions based on interests
        filtered_attractions = []
        if destination_info.get("attractions"):
            for attraction in destination_info["attractions"]:
                # Simple interest matching (in real implementation, use ML/NLP)
                if not interests or any(interest.lower() in attraction.name.lower() 
                                     or interest.lower() in " ".join(attraction.types).lower() 
                                     for interest in interests):
                    filtered_attractions.append(attraction)
        
        # Filter restaurants based on budget
        filtered_restaurants = []
        if destination_info.get("restaurants"):
            for restaurant in destination_info["restaurants"]:
                if not budget or not restaurant.price_level or restaurant.price_level <= 2:
                    filtered_restaurants.append(restaurant)
        
        return {
            "destination": destination,
            "trip_type": trip_type,
            "recommended_attractions": filtered_attractions[:5],
            "recommended_restaurants": filtered_restaurants[:5],
            "weather": destination_info.get("weather"),
            "location": destination_info.get("location")
        }


# ===== SERVICE INSTANCE =====

travel_api_service = TravelAPIService()
